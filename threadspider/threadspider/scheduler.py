"""调度器：优先级队列 + URL 去重 + 未完成请求计数（线程安全）。"""

from __future__ import annotations

import heapq
import itertools
import threading
from collections.abc import Iterable

from .request import Request


class Scheduler:
    """线程安全的抓取队列。

    - 基于 ``heapq`` 的优先级队列（数值越大越先出队，同优先级 FIFO）；
    - 基于指纹的去重集合（``dont_filter=True`` 的请求可重复入队）；
    - ``pending`` 计数用于判断抓取何时结束：入队时 +1，工作线程处理完
      调用 ``task_done()`` 时 -1，计数归零即全部完成。
    """

    def __init__(self, dupefilter: bool = True) -> None:
        self._cv = threading.Condition()
        self._heap: list[tuple[int, int, Request]] = []
        self._counter = itertools.count()
        self._seen: set[str] = set()
        self._pending = 0
        self._dupefilter = dupefilter
        self.dropped_duplicates = 0

    # ------------------------------------------------------------------
    def add(self, request: Request, *, force: bool = False) -> bool:
        """入队一个请求；被去重过滤时返回 False。"""
        with self._cv:
            if self._dupefilter and not force and not request.dont_filter:
                fingerprint = request.fingerprint()
                if fingerprint in self._seen:
                    self.dropped_duplicates += 1
                    return False
                self._seen.add(fingerprint)
            elif self._dupefilter and request.dont_filter:
                pass  # 不记录也不检查
            elif self._dupefilter and force:
                self._seen.add(request.fingerprint())

            heapq.heappush(
                self._heap, (-int(request.priority), next(self._counter), request)
            )
            self._pending += 1
            self._cv.notify_all()
            return True

    def add_many(self, requests: Iterable[Request]) -> int:
        return sum(1 for request in requests if self.add(request))

    # ------------------------------------------------------------------
    def get(self, timeout: float = 0.5) -> Request | None:
        """取出优先级最高的请求；超时或已全部完成时返回 ``None``。"""
        with self._cv:
            ready = self._cv.wait_for(
                lambda: bool(self._heap) or self._pending == 0,
                timeout=timeout,
            )
            if not ready or not self._heap:
                return None
            _, _, request = heapq.heappop(self._heap)
            return request

    def task_done(self) -> None:
        """标记一个已取出的请求处理完毕。"""
        with self._cv:
            self._pending = max(0, self._pending - 1)
            self._cv.notify_all()

    def join(self, timeout: float | None = None) -> bool:
        """等待所有已入队请求处理完毕，返回是否已完成。"""
        with self._cv:
            return self._cv.wait_for(lambda: self._pending == 0, timeout=timeout)

    # ------------------------------------------------------------------
    @property
    def pending(self) -> int:
        with self._cv:
            return self._pending

    @property
    def queued(self) -> int:
        with self._cv:
            return len(self._heap)

    @property
    def seen(self) -> int:
        with self._cv:
            return len(self._seen)

    @property
    def filtered(self) -> int:
        with self._cv:
            return self.dropped_duplicates

    @property
    def unfinished(self) -> bool:
        """队列中还有请求，或有请求正在被处理。"""
        with self._cv:
            return bool(self._heap) or self._pending > 0

    def snapshot(self) -> dict[str, int]:
        with self._cv:
            return {
                "queued": len(self._heap),
                "pending": self._pending,
                "seen": len(self._seen),
                "filtered": self.dropped_duplicates,
            }


__all__ = ["Scheduler"]
