"""CrawlResponse：包装 Scrapling 的 Response，补充请求上下文。"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import urljoin as _urljoin

from .request import Request


class CrawlResponse:
    """把 Scrapling 返回的 ``Response`` 与产生它的 ``Request`` 绑在一起。

    所有选择器方法（``css``/``xpath``/``get``/``json``/``markdown`` 等）
    都直接透传给底层 Scrapling Response，因此用法与 Scrapling 完全一致。
    """

    __slots__ = ("raw", "request")

    def __init__(self, raw: Any, request: Request) -> None:
        self.raw = raw
        self.request = request

    # -- 常用属性 --
    @property
    def url(self) -> str:
        return getattr(self.raw, "url", None) or self.request.url

    @property
    def status(self) -> int:
        return int(getattr(self.raw, "status", 0) or 0)

    @property
    def meta(self) -> dict[str, Any]:
        return self.request.meta

    @property
    def depth(self) -> int:
        return self.request.depth

    def urljoin(self, url: str) -> str:
        return _urljoin(self.url, url)

    def follow(self, url: str, callback=None, **kwargs: Any) -> Request:
        """构造一个指向 ``url`` 的新请求（自动解析相对链接、深度 +1）。"""
        request = Request(self.urljoin(url), callback=callback, **kwargs)
        request.depth = self.request.depth + 1
        if "headers" not in kwargs:
            request.headers = {"Referer": self.url}
        return request

    def follow_all(self, urls: Iterable[str], callback=None, **kwargs: Any):
        for url in urls:
            yield self.follow(url, callback=callback, **kwargs)

    # -- 透传 --
    def __getattr__(self, name: str) -> Any:
        return getattr(self.raw, name)

    def __repr__(self) -> str:
        return f"<CrawlResponse {self.status} {self.url}>"


__all__ = ["CrawlResponse"]
