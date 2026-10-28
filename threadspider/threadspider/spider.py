"""Spider 基类：定义起始请求与解析回调。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .log import get_logger
from .request import Request
from .response import CrawlResponse


class Spider:
    """所有爬虫的基类。

    最小实现只需三样东西::

        class MySpider(Spider):
            name = "my_spider"
            start_urls = ["https://example.com"]

            def parse(self, response):
                yield {"title": response.css("title::text").get("")}

    回调（``parse`` 及你自定义的方法）可以 yield：

    - ``dict`` 或任意对象 → 作为条目交给 Pipeline；
    - ``Request`` → 新的抓取请求；
    - ``str`` → 新的抓取 URL（沿用当前回调）；
    - 列表/生成器 → 递归展开以上类型。
    """

    name: str = ""
    start_urls: list[str] = []
    allowed_domains: list[str] | None = None
    custom_settings: dict[str, Any] = {}

    def __init__(self) -> None:
        self.logger = get_logger(f"spider.{self.name or type(self).__name__}")

    def start_requests(self) -> Iterator[Request]:
        """生成第一批请求，可覆写以实现自定义入口（POST、登录等）。"""
        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response: CrawlResponse):
        """默认解析回调，必须由子类实现。"""
        raise NotImplementedError(f"{type(self).__name__}.parse() 未实现")

    # ------------------------------------------------------------------
    # 可选钩子
    # ------------------------------------------------------------------
    def errback(self, failure: Any) -> None:
        """请求重试耗尽后调用；``failure`` 见 :class:`threadspider.Failure`。"""

    def is_blocked(self, response: CrawlResponse) -> bool:
        """返回 ``True`` 表示该响应疑似被反爬拦截，将按重试策略重新抓取。"""
        return False

    def closed(self, reason: str) -> None:
        """抓取结束（无论正常还是中断）时调用。"""

    # ------------------------------------------------------------------
    def start(self, settings=None):
        """便捷入口：直接运行本爬虫，返回 ``CrawlResult``。"""
        from .engine import CrawlEngine

        return CrawlEngine(self, settings=settings).run()


__all__ = ["Spider"]
