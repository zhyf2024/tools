"""示例：抓取 themewagon.com/theme-index/，保存页面、资产到本地并重写 URL。

站点结构（纯 HTTP 可见，无需 JS 渲染）::

    /theme-index/                      目录页：按字母列出分类/标签/框架
    /theme-category|tag|framework/...  列表页：主题卡片 + /page/N/ 分页
    /themes/<slug>/                    主题详情页

抓取策略：

- themewagon.com 上**只跟进** ``/theme-tag/``、``/theme-category/``、
  ``/theme-framework/`` 之下的链接（含其 ``/page/N/`` 分页），
  其余路径（``/themes/`` 详情页、``/theme-price/`` 等）一律略过；
- ``parse``        目录页（种子入口）：跟进三类列表；
- ``parse_listing`` 列表页：跟进分页；
- ``parse_preview`` Live preview 演示页（可能在外域）：只保存，不再外扩。

列表页卡片上按钮文案含 “Live preview” 的链接都会跟进（外域也抓，本地测试
不限制 ``allowed_domains``），演示页连同其全部图片/CSS/JS 一起镜像到本地
（``MIRROR_REWRITE_EXTERNAL`` 连跨域 CDN 资源也下载）。

输出：

- 所有抓到的 URL 写入 ``output/themewagon/urls.db``（urls 表，按 url 去重）；
- 页面保存到 ``output/themewagon/mirror/``，图片/CSS/JS（含 CSS 内 url()）一并下载，
  跨域 CDN 资源（``MIRROR_REWRITE_EXTERNAL``）也下载；
- 页面里的 src/href/srcset 改写为指向本地文件的相对路径。

运行方式::

    uv run python examples/themewagon_spider.py
"""

from __future__ import annotations

import itertools
import os
import shutil
import sys
import threading
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from threadspider import Spider, run


class ThemewagonSpider(Spider):
    name = "themewagon"
    start_urls = ["https://themewagon.com/theme-index/"]
    #: 本地测试：不限制域名，Live preview 按钮指向外域
    #: （preview.themewagon.com、prium.github.io 等）也要抓
    allowed_domains = None

    #: 演示时限制抓取的页面总数（0 = 不限制；全站约数千页，演示抓几十页即可）
    MAX_PAGES = 0
    #: Live preview 页面单独配额（在跟进按钮时扣减，0 = 不限制）
    MAX_PREVIEWS = 0

    custom_settings = {
        # 并发与限速
        "CONCURRENCY": 4,
        "DOWNLOAD_DELAY": 0.2,
        "CONCURRENCY_PER_HOST": 3,
        # 范围控制
        "MAX_DEPTH": 3,
        # 重试
        "RETRY_TIMES": 3,
        "STATS_INTERVAL": 5,
        "LOG_LEVEL": "INFO",
        # Pipeline：URL 去重存储 + 资产镜像
        "PIPELINES": [
            "threadspider.pipeline:SQLitePipeline",
            "threadspider.asset_mirror_pipeline:AssetMirrorPipeline",
        ],
        "SQLITE_PATH": "output/themewagon/urls.db",
        "SQLITE_TABLE": "urls",
        "SQLITE_UNIQUE_KEYS": ["url"],
        # 资产镜像配置
        "MIRROR_ROOT": "output/themewagon/mirror",
        "MIRROR_DB": "output/themewagon/mirror.db",
        # 不限制域名：preview 站的资源也镜像（含跨域 CDN 资源）
        "MIRROR_REWRITE_EXTERNAL": True,
        # 镜像 Pipeline 串行下载资源较慢，收尾时留足时间排空条目队列
        "SHUTDOWN_TIMEOUT": 1800.0,
    }

    def __init__(self) -> None:
        super().__init__()
        self._counter_lock = threading.Lock()
        self._page_count = itertools.count(1)
        self._preview_count = itertools.count(1)

    # ==================================================================
    # 回调
    # ==================================================================
    def parse(self, response):
        """目录页：保存本页，只跟进三类列表（其余路径略过）。"""
        item = self._page_item(response)
        if item is None:
            return
        yield item

        for href in response.css("a::attr(href)").getall():
            path = urlparse(response.urljoin(href)).path
            if self._is_listing_path(path):
                yield response.follow(href, callback=self.parse_listing)

        yield from self._follow_live_previews(response)

    def parse_listing(self, response):
        """列表页：保存本页，跟进分页（/themes/ 等其他路径一律略过）。"""
        item = self._page_item(response)
        if item is None:
            return
        yield item

        # 分页（最多跟进到第 2 页，控制演示规模）
        for href in response.css("a::attr(href)").getall():
            path = urlparse(response.urljoin(href)).path
            if self._is_listing_path(path) and ("/page/2/" in path or "/page/1/" in path):
                yield response.follow(href, callback=self.parse_listing)

        yield from self._follow_live_previews(response)

    def parse_preview(self, response):
        """Live preview 页面：只保存页面本身，其图片/CSS/JS 由镜像 Pipeline 落盘。"""
        item = self._page_item(response, check_budget=False)
        if item is not None:
            yield item

    # ==================================================================
    # 辅助
    # ==================================================================
    @staticmethod
    def _is_listing_path(path: str) -> bool:
        """themewagon.com 上只跟进这三类前缀，其余路径（详情页/价格页等）略过。"""
        return path.startswith(("/theme-tag/", "/theme-category/", "/theme-framework/"))

    def _follow_live_previews(self, response):
        """找出本页所有 Live preview 按钮并跟进其指向的演示页。"""
        seen: set[str] = set()
        for anchor in response.css("a"):
            text = " ".join(anchor.css("::text").getall()).strip()
            if "live preview" not in text.lower():
                continue
            href = anchor.css("::attr(href)").get("").strip()
            if not href:
                continue
            abs_url = response.urljoin(href)
            if abs_url in seen:
                continue
            seen.add(abs_url)
            if not self._take_preview_budget():
                return  # 配额用完：后续按钮一律不再跟进
            yield response.follow(abs_url, callback=self.parse_preview)

    def _take_preview_budget(self) -> bool:
        """预约一个 Live preview 页面配额（在跟进时扣减，避免超量抓取）。"""
        if self.MAX_PREVIEWS <= 0:
            return True
        with self._counter_lock:
            index = next(self._preview_count)
            if index > self.MAX_PREVIEWS:
                if index == self.MAX_PREVIEWS + 1:  # 只提示一次，避免刷屏
                    self.logger.info("已达到 Live preview 上限 MAX_PREVIEWS=%d，不再跟进", self.MAX_PREVIEWS)
                return False
        return True

    def _budget_left(self) -> bool:
        """页面配额：达到 MAX_PAGES 后不再产出新页面。"""
        if self.MAX_PAGES <= 0:
            return True
        with self._counter_lock:
            index = next(self._page_count)
            if index > self.MAX_PAGES:
                if index == self.MAX_PAGES + 1:  # 只提示一次，避免刷屏
                    self.logger.info("已达到演示上限 MAX_PAGES=%d，不再产出新页面", self.MAX_PAGES)
                return False
        return True

    def _page_item(self, response, check_budget: bool = True) -> dict | None:
        """产出一个带完整 HTML 的条目，Pipeline 用它落盘，避免二次下载。

        ``check_budget=False`` 用于 Live preview 页面——其配额已在跟进按钮时扣减。
        """
        if check_budget and not self._budget_left():
            return None
        headers = response.request.headers or {}
        return {
            "url": response.url,
            "title": response.css("title::text").get("").strip(),
            "depth": response.depth,
            "source": headers.get("Referer", headers.get("referer", "")),
            # Scrapling 的 Response 正文在 html_content（text 只是纯文本）；
            # 交给 AssetMirrorPipeline 保存并重写 URL
            "html": response.raw.html_content,
        }


if __name__ == "__main__":
    # 清空上次运行的输出
    output_dir = "output/themewagon"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    result = run(ThemewagonSpider())
    print()
    print("结果:", result)
    print("条目数:", result.items_scraped)
    print("调度请求:", result.stats.get("requests_scheduled", 0))
    print("下载响应:", result.stats.get("responses", 0))
    print("失败请求:", result.stats.get("requests_failed", 0))
    print("去重过滤:", result.stats.get("filtered", 0))
    print("镜像页面:", result.stats.get("mirror_saved", 0))
    print("镜像资源:", result.stats.get("mirror_assets_downloaded", 0))
    print("耗时(秒):", result.elapsed)
