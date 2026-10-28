"""线程安全的统计收集器。"""

from __future__ import annotations

import threading
import time
from typing import Any


class StatsCollector:
    """所有计数器共享一把锁，工作线程与主线程都可以安全写入。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stats: dict[str, Any] = {}
        self.start_time = time.time()

    def inc(self, key: str, count: int = 1) -> None:
        with self._lock:
            self._stats[key] = self._stats.get(key, 0) + count

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._stats[key] = value

    def get(self, key: str, default: Any = 0) -> Any:
        with self._lock:
            return self._stats.get(key, default)

    def max(self, key: str, value: float) -> None:
        with self._lock:
            if value > self._stats.get(key, 0):
                self._stats[key] = value

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            data = dict(self._stats)
        data["elapsed_seconds"] = round(time.time() - self.start_time, 3)
        return data

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"<StatsCollector {self.snapshot()}>"


__all__ = ["StatsCollector"]
