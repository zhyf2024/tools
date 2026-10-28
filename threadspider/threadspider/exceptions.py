"""threadspider 的公共异常类型。"""

from __future__ import annotations


class ThreadSpiderError(Exception):
    """框架内所有异常的基类。"""


class IgnoreRequest(ThreadSpiderError):
    """在中间件中抛出以丢弃当前请求（不会触发重试）。"""


class DropItem(ThreadSpiderError):
    """在 Pipeline 中抛出以丢弃当前条目。"""


class DownloadTimeout(ThreadSpiderError):
    """下载超时（框架层包装）。"""


class RetryableError(ThreadSpiderError):
    """可重试的下载错误（连接失败、DNS 失败等）包装。"""


class Failure:
    """把"哪个请求因何失败"打包，交给 ``Spider.errback()``。

    Attributes:
        request: 失败的 :class:`~threadspider.request.Request`
        exception: 触发失败的异常对象（可为 ``None``）
        response: 若失败来自状态码（如重试耗尽时的 503），则为响应对象
    """

    __slots__ = ("exception", "request", "response")

    def __init__(self, request, exception: BaseException | None = None, response=None) -> None:
        self.request = request
        self.exception = exception
        self.response = response

    @property
    def value(self) -> BaseException | None:
        return self.exception

    def get_traceback(self) -> str:
        if self.exception is None:
            return ""
        import traceback

        return "".join(traceback.format_exception(self.exception))

    def __str__(self) -> str:
        target = self.request.url
        if self.exception is not None:
            return f"<Failure {type(self.exception).__name__} for {target}>"
        return f"<Failure HTTP {getattr(self.response, 'status', '?')} for {target}>"

    __repr__ = __str__
