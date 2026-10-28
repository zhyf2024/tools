"""下载中间件：请求/响应/异常三个阶段的钩子。"""

from __future__ import annotations

import random
import time
from typing import Any

from .exceptions import IgnoreRequest
from .log import get_logger
from .request import Request
from .settings import Settings
from .stats import StatsCollector

logger = get_logger("middleware")

#: 这些异常属于"代码写错了"，重试没有意义
NON_RETRYABLE_EXCEPTIONS = (ValueError, TypeError, AttributeError, KeyError)


class Middleware:
    """下载中间件基类，所有方法默认直接放行。

    - ``process_request`` 返回 ``None`` 继续处理；返回 ``Request`` 则重新调度；
      返回 Response 则跳过下载（可用来做缓存）；抛 ``IgnoreRequest`` 丢弃请求。
    - ``process_response`` 返回 ``Request`` 则重新调度；返回 Response 继续下一环。
    - ``process_exception`` 返回 ``Request`` 重新调度；返回 Response 视为成功；
      返回 ``None`` 交给下一个中间件。
    """

    def __init__(self, settings: Settings, stats: StatsCollector | None = None) -> None:
        self.settings = settings
        self.stats = stats

    def process_request(self, request: Request, spider) -> Any:
        return None

    def process_response(self, request: Request, response, spider) -> Any:
        return response

    def process_exception(self, request: Request, exception: BaseException, spider) -> Any:
        return None


class DefaultHeadersMiddleware(Middleware):
    """把 ``DEFAULT_HEADERS`` 合并进每个请求（请求自身的头优先级更高）。"""

    def __init__(self, settings: Settings, stats: StatsCollector | None = None) -> None:
        super().__init__(settings, stats)
        self.headers: dict[str, str] = dict(settings.get("DEFAULT_HEADERS") or {})

    def process_request(self, request: Request, spider) -> None:
        if self.headers:
            request.headers = {**self.headers, **(request.headers or {})}


class RetryMiddleware(Middleware):
    """网络异常与可重试状态码的重试逻辑（指数退避 + 抖动）。"""

    def __init__(self, settings: Settings, stats: StatsCollector | None = None) -> None:
        super().__init__(settings, stats)
        self.enabled = settings.getbool("RETRY_ENABLED", True)
        self.retry_times = settings.getint("RETRY_TIMES", 3)
        self.retry_http_codes = {int(code) for code in settings.getlist("RETRY_HTTP_CODES")}
        self.backoff_base = settings.getfloat("RETRY_BACKOFF_BASE", 0.5)
        self.backoff_max = settings.getfloat("RETRY_BACKOFF_MAX", 60.0)

    # ------------------------------------------------------------------
    def process_response(self, request: Request, response, spider) -> Any:
        if not self.enabled:
            return response
        status = int(getattr(response, "status", 0) or 0)
        if status in self.retry_http_codes:
            retried = self.retry(request, spider, reason=f"HTTP {status}")
            if retried is not None:
                return retried
            if self.stats:
                self.stats.inc("retry_exhausted")
            logger.warning("重试次数耗尽，放弃 %s (%s)", request.url, f"HTTP {status}")
        return response

    def process_exception(self, request: Request, exception: BaseException, spider) -> Any:
        if not self.enabled or isinstance(exception, IgnoreRequest):
            return None
        if isinstance(exception, NON_RETRYABLE_EXCEPTIONS):
            logger.debug("不可重试的异常: %r", exception)
            return None
        retried = self.retry(request, spider, reason=repr(exception))
        if retried is not None:
            return retried
        if self.stats:
            self.stats.inc("retry_exhausted")
        logger.warning("重试次数耗尽，放弃 %s (%s)", request.url, repr(exception))
        return None

    # ------------------------------------------------------------------
    def retry(self, request: Request, spider, reason: str) -> Request | None:
        """构造下一次重试请求；次数耗尽返回 ``None``。"""
        if request.retries >= self.retry_times:
            return None
        delay = min(self.backoff_max, self.backoff_base * (2 ** request.retries))
        delay += delay * 0.1 * random.random()  # 退避抖动
        new_request = request.copy(
            retries=request.retries + 1,
            retry_at=time.monotonic() + delay,
        )
        if self.stats:
            self.stats.inc("retries")
        logger.debug(
            "第 %d/%d 次重试 %s (%s)，%.1fs 后执行",
            new_request.retries, self.retry_times, request.url, reason, delay,
        )
        return new_request


__all__ = ["DefaultHeadersMiddleware", "Middleware", "RetryMiddleware"]
