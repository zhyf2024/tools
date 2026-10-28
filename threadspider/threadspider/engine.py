"""多线程抓取引擎：调度器 + 工作线程池 + 中间件 + Pipeline 的编排者。"""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlsplit

from .downloader import Downloader
from .exceptions import DropItem, Failure, IgnoreRequest
from .log import get_logger, setup_logging
from .middleware import Middleware
from .pipeline import Pipeline, build_pipelines
from .ratelimit import HostLimiter
from .request import Request
from .response import CrawlResponse
from .scheduler import Scheduler
from .settings import Settings, _load_object
from .spider import Spider
from .stats import StatsCollector

logger = get_logger()

_SENTINEL = object()


@dataclass
class CrawlResult:
    """一次抓取的最终结果。"""

    reason: str  # "finished" | "shutdown" | "error"
    stats: dict[str, Any]

    @property
    def completed(self) -> bool:
        """是否为正常完成（而非 Ctrl+C 或错误中断）。"""
        return self.reason == "finished"

    @property
    def items_scraped(self) -> int:
        return int(self.stats.get("items_scraped", 0))

    @property
    def elapsed(self) -> float:
        return float(self.stats.get("elapsed_seconds", 0.0))

    def __str__(self) -> str:
        return (
            f"<CrawlResult reason={self.reason} "
            f"items={self.items_scraped} requests={self.stats.get('requests_scheduled', 0)} "
            f"elapsed={self.elapsed:.1f}s>"
        )


def _build_object(spec: Any, settings: Settings, stats: StatsCollector) -> Any:
    """实例化中间件/Pipeline：兼容字符串引用、类、已实例化对象。"""
    import inspect

    obj = _load_object(spec)
    if not isinstance(obj, type):
        return obj
    try:
        parameters = list(inspect.signature(obj).parameters.values())
    except (TypeError, ValueError):  # pragma: no cover - 内置类型等
        parameters = []
    positional = [
        p for p in parameters
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    required = [p for p in positional if p.default is p.empty]
    max_positional = len(positional)

    if required or max_positional >= 2:
        # 构造器至少需要 (settings[, stats])：优先同时传入 stats
        if max_positional >= 2:
            return obj(settings, stats)
        return obj(settings)
    return obj()


class CrawlEngine:
    """把一个 :class:`Spider` 跑完的多线程引擎。

    线程模型：

    - N 个工作线程：从 :class:`Scheduler` 取请求 → 限速/限并发 → 下载
      （每线程一个独立 ``FetcherSession``）→ 走中间件 → 执行回调；
    - 1 个 Pipeline 写入线程：所有 ``process_item`` 串行执行，
      天然避免 SQLite/文件句柄的并发问题；
    - 主线程：等待调度器清空、处理 Ctrl+C、收尾。
    """

    def __init__(self, spider: Spider, settings: Settings | Mapping[str, Any] | None = None) -> None:
        self.spider = spider
        # 子类自定义 __init__ 且未调用 super() 时，这里兜底补上 logger
        if not getattr(spider, "logger", None):
            spider.logger = get_logger(f"spider.{spider.name or type(spider).__name__}")

        merged = Settings()
        if getattr(spider, "custom_settings", None):
            merged.update(spider.custom_settings)
        if isinstance(settings, Settings):
            merged.update(settings.as_dict())
        elif settings:
            merged.update(settings)
        self.settings = merged

        self.stats = StatsCollector()
        self.logger = logger
        self.stop_event = threading.Event()
        self.scheduler = Scheduler(dupefilter=True)
        self.downloader = Downloader(self.settings, self.stats)
        self.limiter = HostLimiter(
            delay=self.settings.getfloat("DOWNLOAD_DELAY", 0.0),
            concurrency=self.settings.getint("CONCURRENCY_PER_HOST", 0),
            stop_event=self.stop_event,
        )
        self.middlewares: list[Middleware] = [
            _build_object(spec, self.settings, self.stats)
            for spec in self.settings.load_objects("MIDDLEWARES")
        ]
        self.pipelines: list[Pipeline] = build_pipelines(self.settings, self.stats)

        self.allowed_domains: list[str] | None = None
        domains = self.settings.get("ALLOWED_DOMAINS") or getattr(spider, "allowed_domains", None)
        if domains:
            self.allowed_domains = [str(d).lower().lstrip(".") for d in domains]
        self.allowed_schemes = {
            str(s).lower() for s in self.settings.getlist("ALLOWED_SCHEMES", ("http", "https"))
        }
        self.max_depth = self.settings.getint("MAX_DEPTH", 0)

        self.items: queue.Queue = queue.Queue(
            maxsize=self.settings.getint("ITEM_QUEUE_SIZE", 0)
        )
        self._reason = "finished"
        self._pipelines_done = threading.Event()
        self._fatal = False
        self._workers: list[threading.Thread] = []
        self._pipeline_thread: threading.Thread | None = None
        self._reporter_thread: threading.Thread | None = None

    # ==================================================================
    # 生命周期
    # ==================================================================
    def run(self) -> CrawlResult:
        self._setup_logging()
        concurrency = max(1, self.settings.getint("CONCURRENCY", 8))
        self.logger.info(
            "启动爬虫 %r：并发=%d，限速=%ss，单域名并发=%s，Pipeline=%d",
            self.spider.name or type(self.spider).__name__,
            concurrency,
            self.settings.getfloat("DOWNLOAD_DELAY", 0.0) or "无",
            self.settings.getint("CONCURRENCY_PER_HOST", 0) or "无",
            len(self.pipelines),
        )

        self._pipeline_thread = threading.Thread(
            target=self._pipeline_loop, name="pipeline", daemon=True
        )
        self._pipeline_thread.start()
        self._start_reporter()

        reason = "finished"
        try:
            for request in self.spider.start_requests() or ():
                self._schedule(request)
            self.stats.set("start_requests", self.stats.get("requests_scheduled", 0))

            if not self.scheduler.unfinished:
                self.logger.warning(
                    "没有可抓取的请求（start_requests 为空，或全部被域/深度/协议过滤）"
                )

            self._workers = [
                threading.Thread(target=self._worker, name=f"worker-{index}", daemon=True)
                for index in range(concurrency)
            ]
            for thread in self._workers:
                thread.start()

            while True:
                if self.stop_event.is_set():
                    reason = "error" if self._fatal else "shutdown"
                    break
                if self.scheduler.join(timeout=0.5):
                    # 队列恰好清空的同时收到了停止信号，优先按停止处理
                    if self.stop_event.is_set():
                        continue
                    reason = "finished"
                    break
        except KeyboardInterrupt:
            reason = "shutdown"
            self.logger.warning("收到中断信号，正在等待在途请求完成…")
        finally:
            self._shutdown(reason)

        snapshot = self.stats.snapshot()
        snapshot.update(self.scheduler.snapshot())
        self.logger.info(
            "抓取结束（%s）：条目=%d，请求=%d，失败=%d，重试=%d，去重=%d，耗时=%.1fs",
            self._reason,
            snapshot.get("items_scraped", 0),
            snapshot.get("requests_scheduled", 0),
            snapshot.get("requests_failed", 0),
            snapshot.get("retries", 0),
            snapshot.get("filtered", 0),
            snapshot.get("elapsed_seconds", 0.0),
        )
        return CrawlResult(reason=self._reason, stats=snapshot)

    # ------------------------------------------------------------------
    def _shutdown(self, reason: str) -> None:
        self._reason = reason
        self.stop_event.set()

        deadline = time.monotonic() + self.settings.getfloat("SHUTDOWN_TIMEOUT", 30.0)
        for thread in self._workers:
            thread.join(timeout=max(0.05, deadline - time.monotonic()))
        alive = [t.name for t in self._workers if t.is_alive()]
        if alive:
            self.logger.warning("以下工作线程未能在超时内退出: %s", ", ".join(alive))

        self._put_sentinel()  # 关闭 Pipeline 写入线程
        if self._pipeline_thread is not None:
            self._pipeline_thread.join(timeout=max(0.05, deadline - time.monotonic()))

        try:
            self.spider.closed(self._reason)
        except Exception:
            self.logger.exception("Spider.closed() 出错")
            self.stats.inc("spider_close_errors")

    # ==================================================================
    # 工作线程
    # ==================================================================
    def _worker(self) -> None:
        try:
            while not self.stop_event.is_set():
                request = self.scheduler.get(timeout=0.5)
                if request is None:
                    if not self.scheduler.unfinished:
                        break
                    continue
                if not self._handle(request):
                    break
        except Exception:
            self._fatal = True
            self.stop_event.set()
            self.logger.exception("工作线程异常退出")
        finally:
            self.downloader.close_session()

    def _handle(self, request: Request) -> bool:
        """处理一个请求。返回 ``False`` 表示该工作线程应退出。"""
        self.stats.inc("requests_dequeued")
        try:
            # 1) 重试退避等待（可被停止信号打断）
            if request.retry_at and not self._sleep_until(request.retry_at):
                self.stats.inc("dropped_on_shutdown")
                return False
            if self.stop_event.is_set():
                self.stats.inc("dropped_on_shutdown")
                return False

            # 2) 请求阶段中间件
            response: CrawlResponse | None = None
            try:
                for mw in self.middlewares:
                    outcome = mw.process_request(request, self.spider)
                    if outcome is None:
                        continue
                    if isinstance(outcome, Request):
                        self._schedule(outcome, force=True)
                        return True
                    if self._looks_like_response(outcome):
                        response = self._wrap(outcome, request)
                        break
                    raise TypeError(f"process_request 返回了不支持的类型: {type(outcome)!r}")
            except IgnoreRequest:
                self.stats.inc("requests_ignored")
                self.logger.debug("忽略请求 %s", request.url)
                return True
            except Exception as exc:
                handled = self._process_exception(request, exc)
                if handled is None:
                    self._record_failure(request, exc)
                    return True
                if isinstance(handled, Request):
                    self._schedule(handled, force=True)
                    return True
                response = self._wrap(handled, request)

            # 3) 下载（限速 + 单域名并发）
            if response is None:
                host = request.host
                if not self.limiter.acquire(host):
                    self.stats.inc("dropped_on_shutdown")
                    return False
                try:
                    try:
                        raw = self.downloader.fetch(request)
                    finally:
                        self.limiter.release(host)
                except Exception as exc:
                    self.stats.inc("download_errors")
                    handled = self._process_exception(request, exc)
                    if handled is None:
                        self._record_failure(request, exc)
                        return True
                    if isinstance(handled, Request):
                        self._schedule(handled, force=True)
                        return True
                    raw = handled
                response = self._wrap(raw, request)
                self.stats.inc("responses")
                self.stats.inc(f"status/{response.status}")

            # 4) 响应阶段中间件（逆序执行）
            try:
                outcome: Any = response
                for mw in reversed(self.middlewares):
                    outcome = mw.process_response(request, outcome, self.spider)
                    if isinstance(outcome, Request):
                        self._schedule(outcome, force=True)
                        return True
            except Exception as exc:
                handled = self._process_exception(request, exc)
                if handled is None:
                    self._record_failure(request, exc)
                    return True
                if isinstance(handled, Request):
                    self._schedule(handled, force=True)
                    return True
                outcome = handled
            response = self._wrap(outcome, request)

            # 5) 反爬拦截检测与重试
            if self._is_blocked(response) and self._retry_blocked(request):
                return True

            # 6) 执行回调，产出条目与新请求
            return self._deliver(request, response)
        finally:
            self.scheduler.task_done()

    # ==================================================================
    # 调度
    # ==================================================================
    def _schedule(self, request: Request, *, force: bool = False) -> bool:
        scheme = urlsplit(request.url).scheme.lower()
        if scheme not in self.allowed_schemes:
            self.stats.inc("dropped_schemes")
            return False
        if self.max_depth and request.depth > self.max_depth:
            self.stats.inc("dropped_depth")
            return False
        if self.allowed_domains and not self._domain_allowed(request):
            self.stats.inc("dropped_domains")
            self.logger.debug("域名不在白名单内，丢弃: %s", request.url)
            return False

        if self.scheduler.add(request, force=force):
            self.stats.inc("requests_scheduled")
            return True
        self.stats.inc("filtered_duplicates")
        return False

    def _domain_allowed(self, request: Request) -> bool:
        host, domain = request.host, request.domain
        for allowed in self.allowed_domains or ():
            if (
                host == allowed
                or host.endswith("." + allowed)
                or domain == allowed
                or domain.endswith("." + allowed)
            ):
                return True
        return False

    # ==================================================================
    # 结果消费
    # ==================================================================
    def _deliver(self, request: Request, response: CrawlResponse) -> bool:
        callback = request.callback or self.spider.parse
        try:
            result = callback(response)
            self._consume(result, request)
        except Exception as exc:
            self.stats.inc("callback_errors")
            self.logger.exception("回调 %r 处理 %s 时出错", getattr(callback, "__name__", callback), request.url)
            self._call_errback(request, Failure(request, exception=exc))
        return True

    def _consume(self, result: Any, request: Request) -> None:
        if result is None:
            return
        if isinstance(result, Request):
            self._schedule(result)
            return
        if isinstance(result, str):
            follow = Request(
                urljoin(request.url, result),
                callback=request.callback,
                errback=request.errback,
            )
            follow.depth = request.depth + 1
            self._schedule(follow)
            return
        if isinstance(result, dict) or not self._is_iterable(result):
            self.stats.inc("items_scraped")
            self._push_item(result)
            return
        for sub in result:
            self._consume(sub, request)

    @staticmethod
    def _is_iterable(value: Any) -> bool:
        if isinstance(value, (bytes, bytearray)):
            return False
        if hasattr(value, "css") or hasattr(value, "xpath"):  # Selector 类对象不当作可迭代集合
            return False
        return hasattr(value, "__iter__")

    # ==================================================================
    # 中间件协作
    # ==================================================================
    @staticmethod
    def _looks_like_response(value: Any) -> bool:
        return not isinstance(value, Request) and hasattr(value, "status") and hasattr(value, "css")

    @staticmethod
    def _wrap(value: Any, request: Request) -> CrawlResponse:
        return value if isinstance(value, CrawlResponse) else CrawlResponse(value, request)

    def _process_exception(self, request: Request, exc: BaseException):
        for mw in self.middlewares:
            try:
                outcome = mw.process_exception(request, exc, self.spider)
            except Exception:
                self.logger.exception("中间件 %s.process_exception 出错", type(mw).__name__)
                continue
            if outcome is None:
                continue
            if isinstance(outcome, Request) or self._looks_like_response(outcome):
                return outcome
            self.logger.warning(
                "中间件 %s.process_exception 返回了不支持的类型: %r",
                type(mw).__name__, type(outcome),
            )
        return None

    def _record_failure(self, request: Request, exc: BaseException) -> None:
        self.stats.inc("requests_failed")
        self.logger.error("请求最终失败 %s: %r", request.url, exc)
        self._call_errback(request, Failure(request, exception=exc))

    def _call_errback(self, request: Request, failure: Failure) -> None:
        handler = request.errback or getattr(self.spider, "errback", None)
        if handler is None:
            return
        try:
            handler(failure)
        except Exception:
            self.stats.inc("errback_errors")
            self.logger.exception("errback 处理 %s 时出错", request.url)

    # ==================================================================
    # 反爬拦截
    # ==================================================================
    def _is_blocked(self, response: CrawlResponse) -> bool:
        hook = getattr(self.spider, "is_blocked", None)
        if hook is None:
            return False
        # 默认实现直接跳过，避免每个响应都做一次无用调用
        unbound = getattr(type(self.spider), "is_blocked", None)
        if unbound is Spider.is_blocked and "is_blocked" not in vars(self.spider):
            return False
        try:
            return bool(hook(response))
        except Exception:
            self.logger.exception("is_blocked() 出错")
            return False

    def _retry_blocked(self, request: Request) -> bool:
        retries = int(request.meta.get("blocked_retries", 0))
        if retries >= self.settings.getint("RETRY_TIMES", 3):
            self.stats.inc("blocked_exhausted")
            return False
        backoff = self.settings.getfloat("RETRY_BACKOFF_BASE", 0.5)
        delay = min(self.settings.getfloat("RETRY_BACKOFF_MAX", 60.0), backoff * (2 ** retries))
        new_request = request.copy(
            meta={**request.meta, "blocked_retries": retries + 1},
            retry_at=time.monotonic() + delay,
        )
        self.stats.inc("blocked_retries")
        self.logger.info("疑似被拦截，稍后重试 (%d): %s", retries + 1, request.url)
        return self._schedule(new_request, force=True)

    # ==================================================================
    # Pipeline 写入线程
    # ==================================================================
    def _pipeline_loop(self) -> None:
        try:
            for pipeline in self.pipelines:
                pipeline.open_spider(self.spider)
            while True:
                item = self.items.get()
                if item is _SENTINEL:
                    break
                self._dispatch_item(item)
        except Exception:
            self.logger.exception("Pipeline 线程异常")
        finally:
            for pipeline in self.pipelines:
                try:
                    pipeline.close_spider(self.spider, self._reason)
                except Exception:
                    self.logger.exception("关闭 Pipeline %s 出错", type(pipeline).__name__)
            self._pipelines_done.set()

    def _dispatch_item(self, item: Any) -> None:
        for pipeline in self.pipelines:
            try:
                item = pipeline.process_item(item, self.spider)
            except DropItem as exc:
                self.stats.inc("items_dropped")
                self.logger.debug("丢弃条目: %s", exc)
                return
            except Exception:
                self.stats.inc("pipeline_errors")
                self.logger.exception("Pipeline %s 处理条目出错", type(pipeline).__name__)
                return
            if item is None:
                return

    def _push_item(self, item: Any) -> bool:
        deadline: float | None = None
        while True:
            try:
                self.items.put(item, timeout=0.2)
                return True
            except queue.Full:
                if not self.stop_event.is_set():
                    continue
                if deadline is None:
                    deadline = time.monotonic() + 5.0
                if time.monotonic() > deadline:
                    self.stats.inc("items_dropped_on_shutdown")
                    return False

    # ==================================================================
    # 辅助
    # ==================================================================
    def _sleep_until(self, timestamp: float) -> bool:
        while True:
            remaining = timestamp - time.monotonic()
            if remaining <= 0:
                return True
            if self.stop_event.wait(min(0.1, remaining)):
                return False

    def _put_sentinel(self) -> bool:
        """尽量把关闭哨兵放进条目队列（有界队列满时最多等 5 秒）。"""
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            try:
                self.items.put_nowait(_SENTINEL)
                return True
            except queue.Full:
                time.sleep(0.05)
        self.logger.warning("条目队列已满，无法投递关闭哨兵")
        return False

    def _start_reporter(self) -> None:
        interval = self.settings.getfloat("STATS_INTERVAL", 10.0)
        if interval <= 0:
            return

        def report() -> None:
            while not self.stop_event.is_set():
                if self.stop_event.wait(interval):
                    break
                snapshot = self.stats.snapshot()
                snapshot.update(self.scheduler.snapshot())
                self.logger.info(
                    "进度: 队列=%d 处理中=%d 已见=%d 条目=%d 失败=%d 耗时=%.0fs",
                    snapshot.get("queued", 0), snapshot.get("pending", 0),
                    snapshot.get("seen", 0), snapshot.get("items_scraped", 0),
                    snapshot.get("requests_failed", 0), snapshot.get("elapsed_seconds", 0.0),
                )

        self._reporter_thread = threading.Thread(target=report, name="stats", daemon=True)
        self._reporter_thread.start()

    def _setup_logging(self) -> None:
        setup_logging(
            self.settings.get("LOG_LEVEL", "INFO"),
            self.settings.get("LOG_FORMAT"),
        )


__all__ = ["CrawlEngine", "CrawlResult"]
