"""threadspider：基于 Scrapling 的多线程网页抓取框架。

快速上手::

    from threadspider import Spider, run

    class QuotesSpider(Spider):
        name = "quotes"
        start_urls = ["https://quotes.toscrape.com/"]

        def parse(self, response):
            for quote in response.css(".quote"):
                yield {
                    "text": quote.css("span.text::text").get(""),
                    "author": quote.css("small.author::text").get(""),
                }
            for url in response.css("li.next a::attr(href)").getall():
                yield response.follow(url)

    if __name__ == "__main__":
        run(QuotesSpider())
"""

from __future__ import annotations

from .asset_mirror_pipeline import AssetMirrorPipeline
from .downloader import Downloader
from .engine import CrawlEngine, CrawlResult
from .exceptions import (
    DropItem,
    Failure,
    IgnoreRequest,
    RetryableError,
    ThreadSpiderError,
)
from .log import attach_file_handler, enable_debug, get_logger, setup_logging
from .middleware import DefaultHeadersMiddleware, Middleware, RetryMiddleware
from .pipeline import (
    ConsolePipeline,
    CsvPipeline,
    JsonLinesPipeline,
    Pipeline,
    SQLitePipeline,
)
from .ratelimit import HostLimiter
from .request import Request
from .response import CrawlResponse
from .scheduler import Scheduler
from .settings import Settings
from .spider import Spider
from .stats import StatsCollector

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # 核心
    "Spider",
    "Request",
    "CrawlResponse",
    "CrawlEngine",
    "CrawlResult",
    "Settings",
    "Scheduler",
    "StatsCollector",
    "Downloader",
    "HostLimiter",
    # 中间件
    "Middleware",
    "DefaultHeadersMiddleware",
    "RetryMiddleware",
    # Pipeline
    "Pipeline",
    "ConsolePipeline",
    "JsonLinesPipeline",
    "CsvPipeline",
    "SQLitePipeline",
    "AssetMirrorPipeline",
    # 异常
    "ThreadSpiderError",
    "IgnoreRequest",
    "DropItem",
    "Failure",
    "RetryableError",
    # 日志
    "get_logger",
    "setup_logging",
    "enable_debug",
    "attach_file_handler",
    # 便捷函数
    "run",
    "run_many",
]


def run(spider: Spider, settings=None) -> CrawlResult:
    """运行单个爬虫，返回 :class:`CrawlResult`。"""
    return CrawlEngine(spider, settings=settings).run()


def run_many(spiders, settings=None) -> list[CrawlResult]:
    """依次运行多个爬虫（每个爬虫内部仍是多线程抓取）。"""
    return [run(spider, settings=settings) for spider in spiders]
