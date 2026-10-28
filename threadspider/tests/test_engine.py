"""引擎端到端测试：用打桩的下载器跑完整的多线程抓取流程（不依赖网络）。"""

from __future__ import annotations

import json
import sqlite3
import threading

import pytest

from threadspider import (
    CrawlEngine,
    CrawlResponse,
    Failure,
    Request,
    Settings,
    Spider,
    run,
)
from threadspider.downloader import Downloader

# ----------------------------------------------------------------------
# 打桩下载器
# ----------------------------------------------------------------------


class FakeRawResponse:
    """模拟 Scrapling Response 的最小对象。"""

    def __init__(self, url: str, status: int = 200, links=(), text: str = ""):
        self.url = url
        self.status = status
        self.links = list(links)
        self.body = text.encode("utf-8")
        self.headers = {}
        self.cookies = {}
        self.encoding = "utf-8"
        self.history = []
        self.reason = "OK"

    def css(self, _selector):  # 离线测试不应该走到真实解析
        raise AssertionError("离线测试不应调用真实的选择器")


class FakeSite:
    """站点拓扑 + 故障注入。"""

    def __init__(self):
        self.pages = {
            "http://site.test/": ["http://site.test/a", "http://site.test/b"],
            "http://site.test/a": ["http://site.test/a2", "http://site.test/"],  # 含回链（去重）
            "http://site.test/b": ["http://site.test/b2"],
            "http://site.test/a2": [],
            "http://site.test/b2": ["http://site.test/deep"],
            "http://site.test/deep": [],
        }
        self.attempts: dict[str, int] = {}
        self.fail_once: set[str] = {"http://site.test/b"}
        self.always_fail: set[str] = set()
        self.lock = threading.Lock()
        self.concurrent: dict[str, int] = {}
        self.max_concurrent: dict[str, int] = {}
        self.delay = 0.02

    def fetch(self, url: str) -> FakeRawResponse:
        with self.lock:
            self.attempts[url] = self.attempts.get(url, 0) + 1
            attempt = self.attempts[url]
            host = "site.test"
            self.concurrent[host] = self.concurrent.get(host, 0) + 1
            self.max_concurrent[host] = max(
                self.max_concurrent.get(host, 0), self.concurrent[host]
            )
        try:
            if self.delay:
                threading.Event().wait(self.delay)
            if url in self.always_fail or (url in self.fail_once and attempt == 1):
                raise OSError(f"simulated network error for {url}")
            if url not in self.pages:
                return FakeRawResponse(url, status=404, links=[])
            return FakeRawResponse(url, status=200, links=self.pages[url])
        finally:
            with self.lock:
                self.concurrent["site.test"] -= 1


@pytest.fixture()
def fake_site(monkeypatch):
    site = FakeSite()

    def fake_fetch(self: Downloader, request: Request):
        return site.fetch(request.url)

    monkeypatch.setattr(Downloader, "fetch", fake_fetch)
    return site


# ----------------------------------------------------------------------
# 爬虫
# ----------------------------------------------------------------------


class OfflineSpider(Spider):
    name = "offline"
    start_urls = ["http://site.test/"]

    def parse(self, response: CrawlResponse):
        yield {"url": response.url, "depth": response.depth, "status": response.status}
        for link in response.links:
            yield response.follow(link)


def test_full_crawl_terminates_and_covers_site(fake_site, tmp_path):
    jsonl_path = tmp_path / "items.jsonl"
    settings = Settings({
        "CONCURRENCY": 6,
        "STATS_INTERVAL": 0,
        "RETRY_BACKOFF_BASE": 0.01,
        "RETRY_BACKOFF_MAX": 0.05,
        "DOWNLOAD_DELAY": 0,
        "CONCURRENCY_PER_HOST": 0,
        "PIPELINES": ["threadspider.pipeline:JsonLinesPipeline"],
        "JSONL_PATH": str(jsonl_path),
        "LOG_LEVEL": "WARNING",
    })

    result = run(OfflineSpider(), settings)

    assert result.reason == "finished"
    assert result.completed is True
    # 6 个唯一页面全部抓取，且没有陷入死循环
    urls = [json.loads(line)["url"] for line in jsonl_path.read_text("utf-8").splitlines()]
    assert sorted(urls) == sorted(fake_site.pages.keys())
    assert result.stats["responses"] == 6
    # 回链被去重过滤
    assert result.stats["filtered_duplicates"] >= 1
    # 重试机制生效：b 页首次失败后重试成功
    assert result.stats["retries"] >= 1
    assert fake_site.attempts["http://site.test/b"] >= 2
    # 回调深度逐层递增
    depths = {json.loads(line)["url"]: json.loads(line)["depth"] for line in jsonl_path.read_text("utf-8").splitlines()}
    assert depths["http://site.test/"] == 0
    assert depths["http://site.test/a2"] == 2


def test_retry_exhaustion_calls_errback(fake_site, tmp_path):
    fake_site.fail_once.clear()
    fake_site.always_fail = {"http://site.test/b"}

    failures: list[Failure] = []

    class ErrbackSpider(OfflineSpider):
        def errback(self, failure: Failure):
            failures.append(failure)

    settings = Settings({
        "CONCURRENCY": 4,
        "STATS_INTERVAL": 0,
        "RETRY_TIMES": 2,
        "RETRY_BACKOFF_BASE": 0.01,
        "RETRY_BACKOFF_MAX": 0.02,
        "LOG_LEVEL": "ERROR",
    })

    result = run(ErrbackSpider(), settings)

    assert len(failures) == 1
    assert isinstance(failures[0].exception, OSError)
    assert result.stats["requests_failed"] == 1
    assert result.stats["retries"] == 2  # 重试 2 次后放弃
    assert fake_site.attempts["http://site.test/b"] == 3
    assert result.reason == "finished"


def test_allowed_domains_filters_outsiders(fake_site):
    class RestrictedSpider(OfflineSpider):
        allowed_domains = ["other.test"]

    settings = Settings({"STATS_INTERVAL": 0, "LOG_LEVEL": "ERROR"})
    result = run(RestrictedSpider(), settings)

    assert result.stats.get("dropped_domains", 0) >= 1
    assert result.stats.get("responses", 0) == 0
    assert result.reason == "finished"


def test_max_depth_limits_crawl(fake_site):
    class DeepSpider(OfflineSpider):
        pass

    settings = Settings({"STATS_INTERVAL": 0, "MAX_DEPTH": 1, "LOG_LEVEL": "ERROR"})
    result = run(DeepSpider(), settings)

    assert result.stats.get("dropped_depth", 0) >= 1
    assert result.stats["responses"] == 3  # /, /a, /b 深度 0/1
    assert result.reason == "finished"


def test_sqlite_pipeline_dedupes_items(fake_site, tmp_path):
    db_path = tmp_path / "items.db"

    class DupSpider(OfflineSpider):
        def parse(self, response):
            yield {"url": response.url}
            yield {"url": response.url}  # 同页重复产出
            for link in response.links:
                yield response.follow(link)

    settings = Settings({
        "STATS_INTERVAL": 0,
        "LOG_LEVEL": "ERROR",
        "PIPELINES": ["threadspider.pipeline:SQLitePipeline"],
        "SQLITE_PATH": str(db_path),
        "SQLITE_TABLE": "pages",
        "SQLITE_UNIQUE_KEYS": ["url"],
    })

    result = run(DupSpider(), settings)
    assert result.stats["items_scraped"] == 12  # 6 页 × 2

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute('SELECT COUNT(*) FROM pages').fetchone()[0]
    conn.close()
    assert rows == 6  # 唯一键去重生效


def test_csv_pipeline_writes_header_and_rows(fake_site, tmp_path):
    csv_path = tmp_path / "items.csv"
    settings = Settings({
        "STATS_INTERVAL": 0,
        "LOG_LEVEL": "ERROR",
        "PIPELINES": ["threadspider.pipeline:CsvPipeline"],
        "CSV_PATH": str(csv_path),
    })
    run(OfflineSpider(), settings)

    lines = csv_path.read_text("utf-8-sig").splitlines()
    assert lines[0] == "url,depth,status"  # 字段来自第一个条目
    assert len(lines) == 1 + 6  # 表头 + 6 个页面


def test_stop_event_interrupts_crawl_gracefully(fake_site, tmp_path):
    """外部设置 stop_event 后应尽快收尾，且已抓到的条目不丢。"""
    import time as _time

    jsonl_path = tmp_path / "items.jsonl"
    fake_site.delay = 0.3  # 让抓取过程足够长，便于中途停止
    engine = CrawlEngine(OfflineSpider(), Settings({
        "STATS_INTERVAL": 0,
        "LOG_LEVEL": "ERROR",
        "CONCURRENCY": 4,
        "PIPELINES": ["threadspider.pipeline:JsonLinesPipeline"],
        "JSONL_PATH": str(jsonl_path),
    }))

    results: list = []
    thread = threading.Thread(target=lambda: results.append(engine.run()))
    thread.start()
    _time.sleep(0.6)  # 首页此时应已完成
    engine.stop_event.set()
    thread.join(timeout=30)

    assert not thread.is_alive()
    assert results and results[0].reason == "shutdown"
    assert jsonl_path.exists()  # Pipeline 已正常打开并关闭
    if jsonl_path.exists():
        assert len(jsonl_path.read_text("utf-8").splitlines()) >= 1


def test_per_host_concurrency_is_respected(fake_site):
    settings = Settings({
        "STATS_INTERVAL": 0,
        "CONCURRENCY": 8,
        "CONCURRENCY_PER_HOST": 2,
        "DOWNLOAD_DELAY": 0,
        "LOG_LEVEL": "ERROR",
    })
    run(OfflineSpider(), settings)
    assert fake_site.max_concurrent["site.test"] <= 2


def test_download_delay_enforces_spacing(fake_site):
    fake_site.delay = 0
    timestamps: list[float] = []
    lock = threading.Lock()

    original = FakeSite.fetch

    def timed_fetch(site_self, url):
        import time as _time

        started = _time.monotonic()
        result = original(site_self, url)
        with lock:
            timestamps.append(started)
        return result

    FakeSite.fetch = timed_fetch
    try:
        settings = Settings({
            "STATS_INTERVAL": 0,
            "CONCURRENCY": 4,
            "DOWNLOAD_DELAY": 0.05,
            "CONCURRENCY_PER_HOST": 1,
            "LOG_LEVEL": "ERROR",
        })
        run(OfflineSpider(), settings)
    finally:
        FakeSite.fetch = original

    assert len(timestamps) == 6
    gaps = [b - a for a, b in zip(sorted(timestamps), sorted(timestamps)[1:], strict=False)]
    assert min(gaps) >= 0.04  # 至少接近 0.05s 的间隔（留一点计时容差）
