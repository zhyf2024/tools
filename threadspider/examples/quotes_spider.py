"""示例：多线程抓取 quotes.toscrape.com，结果同时写入 SQLite 与 JSONL。

运行方式::

    uv run python examples/quotes_spider.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from threadspider import Spider, run

Spider_Name = "themewagon"

class QuotesSpider(Spider):

    start_urls = ["https://themewagon.com/theme-index/"]

    custom_settings = {
        # 并发与限速
        "CONCURRENCY": 4,  # 8 个工作线程
        "DOWNLOAD_DELAY": 0.1,  # 同一域名两次请求至少间隔 0.1s
        "CONCURRENCY_PER_HOST": 4,  # 单域名最多 4 个并发
        # 输出
        "PIPELINES": [
            "threadspider.pipeline:SQLitePipeline",
        ],
        "SQLITE_PATH": f"output/{Spider_Name}.db",
        "SQLITE_TABLE": f"{Spider_Name}",
        "SQLITE_UNIQUE_KEYS": ["url"],  # 按名言文本去重
        # 其他
        "MAX_DEPTH": 10,
        "RETRY_TIMES": 3,
        "STATS_INTERVAL": 5,  # 每 5 秒打印一次进度
        "LOG_LEVEL": "INFO",
    }

    def parse(self, response):
        """列表页：提取条目 + 跟进分页链接。"""
        for quote in response.css(".grid-template-columns"):
            yield {
                "url": quote.css("li a::attr(href)").get(""),
            }

        for href in response.css("li.next a::attr(href)").getall():
            yield response.follow(href)  # 沿用当前回调 parse

        # 顺带跟进本页前 2 个标签页，演示多回调分发
        for href in response.css("div.tags-box a.tag::attr(href)").getall()[:2]:
            yield response.follow(href, callback=self.parse_tag)

    def parse_tag(self, response):
        """标签页：只记录标题，不再继续跟进。"""
        yield {"tag": response.css("h3::text").get("").strip(), "page": response.url}


if __name__ == "__main__":
    # 清空上次运行的输出，便于对比
    for path in [f"output/{Spider_Name}.db"]:
        if os.path.exists(path):
            os.remove(path)

    result = run(QuotesSpider())
    print()
    print("结果:", result)
    print("条目数:", result.items_scraped)
    print("调度请求:", result.stats.get("requests_scheduled", 0))
    print("下载响应:", result.stats.get("responses", 0))
    print("失败请求:", result.stats.get("requests_failed", 0))
    print("重试次数:", result.stats.get("retries", 0))
    print("去重过滤:", result.stats.get("filtered", 0))
    print("耗时(秒):", result.elapsed)
