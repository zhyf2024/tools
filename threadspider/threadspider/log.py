"""框架统一的日志工具。

设计约定：

- 每个模块用 ``get_logger(__name__)`` 拿到以模块全名命名的 logger
  （如 ``threadspider.downloader``），便于按子系统控制日志级别；
- 框架根 logger（``threadspider``）默认挂一个 :class:`logging.NullHandler`，
  作为库被 import 时不会擅自配置日志输出；
- 真正的输出配置只在 :func:`setup_logging` 里发生（由 ``CrawlEngine.run()``
  根据 ``LOG_LEVEL`` / ``LOG_FORMAT`` 设置调用），用户自己配置的 handler
  会被尊重，不会被覆盖。
"""

from __future__ import annotations

import logging
import os
from typing import Any

#: 框架所有日志的根 logger 名
ROOT_LOGGER_NAME = "threadspider"

_DEFAULT_FORMAT = "%(asctime)s [%(threadName)s] %(levelname)s %(name)s: %(message)s"

# 幂等：只挂一次 NullHandler
if not logging.getLogger(ROOT_LOGGER_NAME).handlers:
    logging.getLogger(ROOT_LOGGER_NAME).addHandler(logging.NullHandler())


def get_logger(name: str | None = None) -> logging.Logger:
    """返回框架命名空间下的 logger。

    ``get_logger(__name__)`` 在模块 ``threadspider/downloader.py`` 中调用时
    返回名为 ``threadspider.downloader`` 的 logger；``name`` 为空或不带
    ``threadspider.`` 前缀时自动补前缀，避免日志散落到根 logger。
    """
    if not name:
        return logging.getLogger(ROOT_LOGGER_NAME)
    if name == ROOT_LOGGER_NAME or name.startswith(ROOT_LOGGER_NAME + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")


def _resolve_level(level: Any) -> int:
    if isinstance(level, int):
        return level
    name = str(level).strip().upper()
    return getattr(logging, name, logging.INFO)


def setup_logging(level: Any = "INFO", fmt: str | None = None, *, force: bool = False) -> logging.Logger:
    """配置框架日志（由引擎在启动时调用，也可以在 ``run()`` 之前手动调用）。

    - root logger 没有任何 handler 时用 :func:`logging.basicConfig` 建立控制台输出；
    - root logger 已有 handler（用户自己配置过）时只调整级别，不重复挂 handler；
    - ``force=True`` 则重新配置（丢弃已有 handler）。
    - 始终把 ``scrapling`` 库日志级别抬到 ``WARNING`` 以上，避免刷屏。

    :param level: 级别名（``"DEBUG"`` 等）或数值
    :param fmt: 日志格式；``None`` 用默认格式
    :returns: 配置好的根 logger
    """
    resolved = _resolve_level(level)
    root = logging.getLogger()
    if force or not root.handlers:
        logging.basicConfig(level=resolved, format=fmt or _DEFAULT_FORMAT, force=force)
    else:
        root.setLevel(resolved if root.level == logging.NOTSET else min(root.level, resolved))
    # 库日志跟随框架设置，但至少 WARNING
    logging.getLogger("scrapling").setLevel(max(resolved, logging.WARNING))
    return root


def enable_debug() -> None:
    """快捷方法：把框架所有子系统日志调到 DEBUG（排查问题时用）。"""
    setup_logging("DEBUG")
    for name in (ROOT_LOGGER_NAME, "scrapling", "curl_cffi"):
        logging.getLogger(name).setLevel(logging.DEBUG)


def attach_file_handler(path: str, level: Any = "DEBUG", fmt: str | None = None) -> logging.Handler:
    """给框架根 logger 追加一个文件 handler（线程安全，多线程日志不会串行错乱）。"""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(_resolve_level(level))
    handler.setFormatter(logging.Formatter(fmt or _DEFAULT_FORMAT))
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.addHandler(handler)
    root.setLevel(min(root.level or logging.DEBUG, handler.level))
    return handler


__all__ = [
    "ROOT_LOGGER_NAME",
    "get_logger",
    "setup_logging",
    "enable_debug",
    "attach_file_handler",
]
