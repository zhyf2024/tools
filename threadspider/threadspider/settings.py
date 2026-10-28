"""框架配置：默认值 + 用户覆盖。"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

DEFAULTS: dict[str, Any] = {
    # --- 并发与限速 ---
    "CONCURRENCY": 8,  # 工作线程数
    "CONCURRENCY_PER_HOST": 0,  # 单域名最大并发，0 = 不限制
    "DOWNLOAD_DELAY": 0.0,  # 单域名两次请求之间的最小间隔（秒）
    "DOWNLOAD_TIMEOUT": 30,  # 单次请求超时（秒）

    # --- 请求伪装 ---
    "IMPERSONATE": "chrome",  # TLS 指纹伪装，可传列表随机选取
    "STEALTHY_HEADERS": True,  # 生成真实浏览器请求头
    "DEFAULT_HEADERS": {},  # 追加/覆盖的请求头
    "PROXY": None,  # 全局代理，如 "http://user:pass@host:port"；None = 直连（跟随环境变量）
    "VERIFY_SSL": False,
    "FOLLOW_REDIRECTS": "safe",
    "FETCHER_RETRIES": 1,  # Scrapling 内部尝试次数；1 = 只发一次，重试交给框架

    # --- 框架层重试 ---
    "RETRY_ENABLED": True,
    "RETRY_TIMES": 3,  # 最大重试次数（不含首次）
    "RETRY_HTTP_CODES": (408, 429, 500, 502, 503, 504, 522, 524),
    "RETRY_BACKOFF_BASE": 0.5,  # 退避 = base * 2**(retries-1)，上限 RETRY_BACKOFF_MAX
    "RETRY_BACKOFF_MAX": 60.0,

    # --- 解析器配置（透传给 Scrapling Selector/Response） ---
    "SELECTOR_CONFIG": None,  # 如 {"adaptive": True, "encoding": "shift_jis"}

    # --- 中间件 / Pipeline（字符串用 "module:Class" 形式，也可直接传类或实例） ---
    "MIDDLEWARES": [
        "threadspider.middleware:DefaultHeadersMiddleware",
        "threadspider.middleware:RetryMiddleware",
    ],
    "PIPELINES": [],

    # --- 抓取范围 ---
    "MAX_DEPTH": 0,  # 链接深度限制，0 = 不限制
    "ALLOWED_DOMAINS": None,  # 默认取 spider.allowed_domains
    "ALLOWED_SCHEMES": ("http", "https"),

    # --- 队列与退出 ---
    "ITEM_QUEUE_SIZE": 0,  # 条目队列上限，0 = 无界（有界可产生背压）
    "SHUTDOWN_TIMEOUT": 30,  # 退出时等待在途请求的最长时间（秒）

    # --- 日志与统计 ---
    "LOG_LEVEL": "INFO",
    "LOG_FORMAT": "%(asctime)s [%(threadName)s] %(levelname)s %(name)s: %(message)s",
    "STATS_INTERVAL": 10,  # 运行中每 N 秒打印一次统计，0 = 关闭
}


def _load_object(spec: Any) -> Any:
    """把 ``"module:Class"`` 字符串导入为对象；其余原样返回。"""
    if not isinstance(spec, str):
        return spec
    module_path, sep, name = spec.partition(":")
    if not sep:
        raise ValueError(f"无效的对象引用（应为 'module:Class'）: {spec!r}")
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, name)


class Settings:
    """一个带默认值的字典式配置对象，大小写敏感（键均为大写）。"""

    def __init__(self, values: Mapping[str, Any] | None = None) -> None:
        self._values: dict[str, Any] = dict(DEFAULTS)
        if values:
            self.update(values)

    # -- 基础字典接口 --
    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._values[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._values

    def __iter__(self):
        return iter(self._values)

    def update(self, values: Mapping[str, Any]) -> Settings:
        # 未在 DEFAULTS 中出现的键也会被接受，方便自定义 Pipeline 读取自己的配置
        self._values.update(values)
        return self

    def as_dict(self) -> dict[str, Any]:
        return dict(self._values)

    def copy(self) -> Settings:
        return Settings(self._values)

    # -- 类型化取值 --
    def getint(self, key: str, default: int = 0) -> int:
        value = self.get(key, default)
        return int(value) if value is not None else default

    def getfloat(self, key: str, default: float = 0.0) -> float:
        value = self.get(key, default)
        return float(value) if value is not None else default

    def getbool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, default)
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    def getlist(self, key: str, default: Iterable[Any] | None = None) -> list[Any]:
        value = self.get(key)
        if value is None:
            return list(default or ())
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return list(value)

    # -- 对象解析 --
    def load_objects(self, key: str) -> list[Any]:
        return [_load_object(spec) for spec in self.getlist(key)]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Settings {self._values}>"


__all__ = ["DEFAULTS", "Settings", "_load_object"]
