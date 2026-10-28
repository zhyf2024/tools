"""下载器：为每个工作线程维护一个独立的 Scrapling FetcherSession。"""

from __future__ import annotations

import contextlib
import logging
import threading
from typing import Any

from .log import get_logger
from .request import Request
from .settings import Settings
from .stats import StatsCollector

logger = get_logger("downloader")

_HTTP_METHODS = ("get", "post", "put", "delete")

_logging_normalized = False


def _normalize_library_logging() -> None:
    """让 Scrapling 的日志统一走框架的根日志配置。

    Scrapling 在导入时会给自己的 logger 挂一个自带 handler，不处理的话
    每条 ``Fetched ...`` 都会打印两遍（一遍它的格式、一遍框架的格式）。
    这里移除库自带 handler 并恢复 ``NOTSET`` 级别，使其继承框架的
    ``LOG_LEVEL``。
    """
    global _logging_normalized
    if _logging_normalized:
        return
    lib_logger = logging.getLogger("scrapling")
    if lib_logger.handlers:
        lib_logger.handlers.clear()
    lib_logger.propagate = True
    lib_logger.setLevel(logging.NOTSET)
    _logging_normalized = True


class Downloader:
    """基于 ``scrapling.fetchers.FetcherSession`` 的下载器。

    Scrapling 的会话对象并非为多线程设计，因此这里采用
    ``threading.local()``：**每个工作线程独享一个会话**（独立连接池与
    Cookie 空间），线程结束时由该线程自己关闭会话。
    """

    def __init__(self, settings: Settings, stats: StatsCollector) -> None:
        self.settings = settings
        self.stats = stats
        self._local = threading.local()

    # ------------------------------------------------------------------
    def _make_session(self):
        from scrapling.fetchers import FetcherSession

        _normalize_library_logging()
        selector_config = self.settings.get("SELECTOR_CONFIG") or {}
        manager = FetcherSession(
            impersonate=self.settings.get("IMPERSONATE") or "chrome",
            stealthy_headers=self.settings.getbool("STEALTHY_HEADERS", True),
            timeout=self.settings.getfloat("DOWNLOAD_TIMEOUT", 30.0),
            retries=self.settings.getint("FETCHER_RETRIES", 1),
            follow_redirects=self.settings.get("FOLLOW_REDIRECTS", "safe"),
            verify=self.settings.getbool("VERIFY_SSL", True),
            proxy=self.settings.get("PROXY") or None,
            selector_config=dict(selector_config),
        )
        client = manager.__enter__()  # 创建真正的同步会话
        return manager, client

    @property
    def session(self):
        client = getattr(self._local, "client", None)
        if client is None:
            manager, client = self._make_session()
            self._local.manager = manager
            self._local.client = client
            self.stats.inc("sessions_created")
        return client

    def close_session(self) -> None:
        manager = getattr(self._local, "manager", None)
        if manager is not None:
            # 关闭会话失败不应影响抓取结果
            with contextlib.suppress(Exception):  # pragma: no cover
                manager.__exit__(None, None, None)
            self._local.manager = None
            self._local.client = None

    # ------------------------------------------------------------------
    def _build_kwargs(self, request: Request) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if request.headers:
            kwargs["headers"] = request.headers
        if request.params:
            kwargs["params"] = request.params
        if request.data is not None:
            kwargs["data"] = request.data
        if request.json is not None:
            kwargs["json"] = request.json
        if request.cookies:
            kwargs["cookies"] = request.cookies

        timeout = request.timeout if request.timeout is not None else self.settings.get("DOWNLOAD_TIMEOUT")
        kwargs["timeout"] = timeout
        verify = request.verify if request.verify is not None else self.settings.getbool("VERIFY_SSL", True)
        kwargs["verify"] = verify
        kwargs["retries"] = self.settings.getint("FETCHER_RETRIES", 1)

        if request.proxy or self.settings.get("PROXY"):
            kwargs["proxy"] = request.proxy or self.settings.get("PROXY")
        if request.impersonate:
            kwargs["impersonate"] = request.impersonate
        if request.follow_redirects is not None:
            kwargs["follow_redirects"] = request.follow_redirects
        elif "FOLLOW_REDIRECTS" in self.settings:
            kwargs["follow_redirects"] = self.settings.get("FOLLOW_REDIRECTS")

        selector_config = self.settings.get("SELECTOR_CONFIG")
        if selector_config:
            kwargs["selector_config"] = dict(selector_config)
        kwargs.update(request.extra)
        return kwargs

    def fetch(self, request: Request):
        """执行请求，返回 Scrapling 的 ``Response``；失败抛出异常。"""
        method = request.method.lower()
        if method not in _HTTP_METHODS:
            raise ValueError(f"不支持的 HTTP 方法: {request.method}")
        session = self.session
        kwargs = self._build_kwargs(request)
        self.stats.inc("download_attempts")
        return getattr(session, method)(request.url, **kwargs)


__all__ = ["Downloader"]
