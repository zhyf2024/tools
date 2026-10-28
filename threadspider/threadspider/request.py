"""Request 对象与 URL 指纹（去重用）。"""

from __future__ import annotations

import hashlib
import json as _json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

Callback = Callable[..., Any]


class Request:
    """一次待执行的 HTTP 请求。

    ``callback`` 在响应成功后被调用（生成器或普通函数都可），
    ``errback`` 在重试耗尽或不可重试错误发生时被调用，签名
    ``errback(failure: Failure)``。
    """

    __slots__ = (
        "callback",
        "cookies",
        "data",
        "depth",
        "dont_filter",
        "errback",
        "extra",
        "follow_redirects",
        "headers",
        "impersonate",
        "json",
        "meta",
        "method",
        "params",
        "priority",
        "proxy",
        "retries",
        "retry_at",
        "timeout",
        "url",
        "verify",
    )

    def __init__(
        self,
        url: str,
        callback: Callback | None = None,
        *,
        method: str = "GET",
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, Any] | None = None,
        data: Any = None,
        json: Any = None,
        cookies: Mapping[str, Any] | None = None,
        priority: int = 0,
        dont_filter: bool = False,
        meta: Mapping[str, Any] | None = None,
        errback: Callback | None = None,
        timeout: float | None = None,
        proxy: str | None = None,
        impersonate: Any = None,
        verify: bool | None = None,
        follow_redirects: Any = None,
        **extra: Any,
    ) -> None:
        if not isinstance(url, str) or not url:
            raise ValueError("Request.url 必须是非空字符串")
        self.url = url
        self.method = method.upper()
        self.callback = callback
        self.errback = errback
        self.headers = dict(headers) if headers else None
        self.params = dict(params) if params else None
        self.data = data
        self.json = json
        self.cookies = dict(cookies) if cookies else None
        self.priority = priority
        self.dont_filter = dont_filter
        self.meta: dict[str, Any] = dict(meta) if meta else {}
        self.depth = 0
        self.retries = 0
        self.retry_at = 0.0  # 重试等待时间点（time.monotonic），由引擎处理
        self.timeout = timeout
        self.proxy = proxy
        self.impersonate = impersonate
        self.verify = verify
        self.follow_redirects = follow_redirects
        self.extra = dict(extra)  # 其余参数透传给 Scrapling（auth/cert/http3/...）

    # ------------------------------------------------------------------
    @property
    def host(self) -> str:
        return (urlsplit(self.url).hostname or "").lower()

    @property
    def domain(self) -> str:
        """用于 allowed_domains 过滤的 ``domain:port``。"""
        parts = urlsplit(self.url)
        netloc = (parts.hostname or "").lower()
        if parts.port:
            netloc = f"{netloc}:{parts.port}"
        return netloc

    def fingerprint(self) -> str:
        """method + 规范化 URL + 请求体 的 SHA1，用于去重。"""
        parts = urlsplit(self.url)
        query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
        normalized = urlunsplit(
            ((parts.scheme or "http").lower(), (parts.netloc or "").lower(),
             parts.path or "/", query, "")
        )
        if self.json is not None:
            body = _json.dumps(self.json, sort_keys=True, ensure_ascii=False, default=str)
        elif isinstance(self.data, (dict, list, tuple)):
            body = _json.dumps(self.data, sort_keys=True, ensure_ascii=False, default=str)
        elif isinstance(self.data, bytes):
            body = self.data.decode("utf-8", "replace")
        else:
            body = "" if self.data is None else str(self.data)
        raw = f"{self.method}\n{normalized}\n{body}".encode("utf-8", "replace")
        return hashlib.sha1(raw).hexdigest()

    def copy(self, **overrides: Any) -> Request:
        """复制请求，可用 ``**overrides`` 修改任意构造参数。"""
        fields: dict[str, Any] = {
            "url": self.url, "method": self.method, "callback": self.callback,
            "errback": self.errback, "headers": self.headers, "params": self.params,
            "data": self.data, "json": self.json, "cookies": self.cookies,
            "priority": self.priority, "dont_filter": self.dont_filter,
            "meta": self.meta, "timeout": self.timeout, "proxy": self.proxy,
            "impersonate": self.impersonate, "verify": self.verify,
            "follow_redirects": self.follow_redirects,
        }
        fields.update(self.extra)
        state_overrides = {
            key: overrides.pop(key, None)
            for key in ("depth", "retries", "retry_at")
            if key in overrides
        }
        fields.update(overrides)
        new = Request(**fields)
        new.depth = self.depth if state_overrides.get("depth") is None else state_overrides["depth"]
        new.retries = self.retries if state_overrides.get("retries") is None else state_overrides["retries"]
        new.retry_at = 0.0 if state_overrides.get("retry_at") is None else state_overrides["retry_at"]
        return new

    def __repr__(self) -> str:
        return f"<Request {self.method} {self.url} depth={self.depth} retries={self.retries}>"


__all__ = ["Callback", "Request"]
