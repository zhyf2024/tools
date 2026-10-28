"""Item Pipeline：条目的落盘与后处理，全部在单独的写入线程中执行。"""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
from typing import Any

from .log import get_logger
from .settings import Settings
from .stats import StatsCollector

logger = get_logger("pipeline")

_IDENT_RE = re.compile(r"[^0-9A-Za-z_]+")


def _safe_ident(name: str, fallback: str) -> str:
    cleaned = _IDENT_RE.sub("_", str(name)).strip("_")
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"{fallback}_{cleaned}" if cleaned else fallback
    return cleaned


class Pipeline:
    """Pipeline 基类。注意：所有方法都运行在**同一个**写入线程里。"""

    def __init__(self, settings: Settings, stats: StatsCollector | None = None) -> None:
        self.settings = settings
        self.stats = stats

    def open_spider(self, spider) -> None:
        pass

    def process_item(self, item: Any, spider) -> Any:
        """处理条目；返回值（或原对象）会传给下一个 Pipeline。"""
        return item

    def close_spider(self, spider, reason: str) -> None:
        pass


class ConsolePipeline(Pipeline):
    """把条目打印到日志，方便调试。"""

    def process_item(self, item: Any, spider) -> Any:
        logger.info("item: %s", item)
        return item


class JsonLinesPipeline(Pipeline):
    """追加写入 JSON Lines 文件（每行一个 JSON 对象）。

    相关配置：``JSONL_PATH``（默认 ``items.jsonl``）、
    ``JSONL_FLUSH``（默认 ``True``，每条都落盘）。
    """

    def open_spider(self, spider) -> None:
        self.path = self.settings.get("JSONL_PATH", "items.jsonl")
        self.flush = self.settings.getbool("JSONL_FLUSH", True)
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        self._file = open(self.path, "a", encoding="utf-8")

    def process_item(self, item: Any, spider) -> Any:
        self._file.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
        if self.flush:
            self._file.flush()
        if self.stats:
            self.stats.inc("jsonl_items")
        return item

    def close_spider(self, spider, reason: str) -> None:
        self._file.close()
        logger.info("JSONL 输出: %s", os.path.abspath(self.path))


class CsvPipeline(Pipeline):
    """写入 CSV 文件。字段取 ``CSV_FIELDS``，否则取第一个条目的键。

    相关配置：``CSV_PATH``（默认 ``items.csv``）、``CSV_FIELDS``。
    """

    def open_spider(self, spider) -> None:
        self.path = self.settings.get("CSV_PATH", "items.csv")
        self.fields: list[str] | None = self.settings.getlist("CSV_FIELDS") or None
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        # utf-8-sig 让 Excel 直接打开不乱码
        self._file = open(self.path, "a", encoding="utf-8-sig", newline="")
        self._writer = None
        self._warned_extra = False
        if self.fields:
            self._writer = csv.DictWriter(
                self._file, fieldnames=self.fields, extrasaction="ignore"
            )
            if self._file.tell() == 0:
                self._writer.writeheader()

    def process_item(self, item: Any, spider) -> Any:
        if not isinstance(item, dict):
            item = {"value": item}
        if self._writer is None:
            self.fields = [str(key) for key in item]
            self._writer = csv.DictWriter(
                self._file, fieldnames=self.fields, extrasaction="ignore"
            )
            if self._file.tell() == 0:
                self._writer.writeheader()
        known = set(self.fields or [])
        unknown = [key for key in item if str(key) not in known]
        if unknown and not self._warned_extra:
            logger.warning("CSV 忽略了未声明的字段 %s（仅提示一次）", unknown)
            self._warned_extra = True
        row = {
            str(key): ("" if value is None else value)
            for key, value in item.items()
            if str(key) in known
        }
        self._writer.writerow(row)
        if self.stats:
            self.stats.inc("csv_items")
        return item

    def close_spider(self, spider, reason: str) -> None:
        self._file.close()
        logger.info("CSV 输出: %s", os.path.abspath(self.path))


class SQLitePipeline(Pipeline):
    """写入 SQLite 数据库，可按指定列自动去重。

    相关配置：

    - ``SQLITE_PATH``（默认 ``items.db``）
    - ``SQLITE_TABLE``（默认 ``items``）
    - ``SQLITE_UNIQUE_KEYS``（如 ``["url"]``，配置后按该列 ``INSERT OR IGNORE`` 去重）
    - ``SQLITE_COMMIT_EVERY``（默认 100，每 N 条提交一次）
    """

    def open_spider(self, spider) -> None:
        self.path = self.settings.get("SQLITE_PATH", "items.db")
        self.table = _safe_ident(self.settings.get("SQLITE_TABLE", "items"), "items")
        self.unique_keys = [
            _safe_ident(key, "col")
            for key in self.settings.getlist("SQLITE_UNIQUE_KEYS")
        ]
        self.commit_every = max(1, self.settings.getint("SQLITE_COMMIT_EVERY", 100))
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=True)
        self._columns: set[str] = set()
        self._pending = 0
        self._loaded_columns()
        logger.info(
            "SQLite 输出: %s (表 %s%s)",
            os.path.abspath(self.path), self.table,
            f", 去重键 {self.unique_keys}" if self.unique_keys else "",
        )

    # ------------------------------------------------------------------
    def _loaded_columns(self) -> None:
        cursor = self._conn.execute(f'PRAGMA table_info("{self.table}")')
        rows = cursor.fetchall()
        if not rows:
            self._conn.execute(f'CREATE TABLE IF NOT EXISTS "{self.table}" ("_id" INTEGER PRIMARY KEY AUTOINCREMENT)')
        self._columns = {row[1] for row in rows}

    @staticmethod
    def _column_type(value: Any) -> str:
        if isinstance(value, bool):
            return "INTEGER"
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, float):
            return "REAL"
        if isinstance(value, (dict, list, tuple)):
            return "TEXT"  # 以 JSON 文本存储
        return "TEXT"

    @staticmethod
    def _dump(value: Any) -> Any:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False, default=str)
        return value

    def _ensure_columns(self, item: dict) -> list[str]:
        columns: list[str] = []
        for key in item:
            col = _safe_ident(key, "col")
            if col not in self._columns:
                self._conn.execute(
                    f'ALTER TABLE "{self.table}" ADD COLUMN "{col}" {self._column_type(item[key])}'
                )
                self._columns.add(col)
            columns.append(col)
        return columns

    def _ensure_unique_index(self) -> None:
        if not self.unique_keys or not self._columns:
            return
        cols = [key for key in self.unique_keys if key in self._columns]
        if len(cols) != len(self.unique_keys):
            return  # 唯一键尚未全部出现，等后续条目补齐
        names = ", ".join(f'"{col}"' for col in cols)
        self._conn.execute(
            f'CREATE UNIQUE INDEX IF NOT EXISTS "ux_{self.table}" ON "{self.table}" ({names})'
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    def process_item(self, item: Any, spider) -> Any:
        if not isinstance(item, dict):
            item = {"value": item}
        cols = self._ensure_columns(item)
        self._ensure_unique_index()

        col_names = ", ".join(f'"{col}"' for col in cols)
        placeholders = ", ".join("?" for _ in cols)
        verb = "INSERT OR IGNORE" if self.unique_keys else "INSERT"
        values = [self._dump(item[key]) for key in item]
        self._conn.execute(
            f'{verb} INTO "{self.table}" ({col_names}) VALUES ({placeholders})',
            values,
        )
        self._pending += 1
        if self._pending >= self.commit_every:
            self._conn.commit()
            self._pending = 0
        if self.stats:
            self.stats.inc("sqlite_items")
        return item

    def close_spider(self, spider, reason: str) -> None:
        self._conn.commit()
        self._conn.close()
        logger.info("SQLite 输出完成: %s", os.path.abspath(self.path))


def build_pipelines(settings: Settings, stats: StatsCollector) -> list[Pipeline]:
    """按 ``PIPELINES`` 配置实例化 Pipeline（兼容类 / 实例 / 字符串引用）。"""
    pipelines: list[Pipeline] = []
    for spec in settings.load_objects("PIPELINES"):
        if isinstance(spec, type):
            try:
                obj = spec(settings, stats)
            except TypeError:
                obj = spec(settings)
        else:
            obj = spec
        pipelines.append(obj)
    return pipelines


__all__ = [
    "ConsolePipeline",
    "CsvPipeline",
    "JsonLinesPipeline",
    "Pipeline",
    "SQLitePipeline",
    "build_pipelines",
]
