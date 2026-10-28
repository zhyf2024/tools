"""按域名限速与并发控制。"""

from __future__ import annotations

import contextlib
import random
import threading
import time


class HostLimiter:
    """每个域名一个"时间槽 + 信号量"的组合闸门。

    - 时间槽：同一域名两次请求至少间隔 ``delay`` 秒（含最多 10% 随机抖动）；
    - 信号量：同一域名最多 ``concurrency`` 个并发（0 = 不限制）。

    所有等待都被切成很短的片段，并不断检查 ``stop_event``，
    因此 Ctrl+C 时不会卡在等待里。
    """

    def __init__(
        self,
        delay: float = 0.0,
        concurrency: int = 0,
        stop_event: threading.Event | None = None,
    ) -> None:
        self.delay = max(0.0, float(delay))
        self.concurrency = max(0, int(concurrency))
        self.stop_event = stop_event or threading.Event()
        self._lock = threading.Lock()
        self._semaphores: dict[str, threading.Semaphore] = {}
        self._next_time: dict[str, float] = {}

    # ------------------------------------------------------------------
    def _semaphore(self, host: str) -> threading.Semaphore | None:
        if not self.concurrency:
            return None
        with self._lock:
            sem = self._semaphores.get(host)
            if sem is None:
                sem = threading.Semaphore(self.concurrency)
                self._semaphores[host] = sem
            return sem

    def _wait(self, seconds: float) -> bool:
        """分片睡眠；返回 False 表示收到停止信号。"""
        deadline = seconds
        while deadline > 0:
            if self.stop_event.is_set():
                return False
            step = min(0.1, deadline)
            if self.stop_event.wait(step):
                return False
            deadline -= step
        return not self.stop_event.is_set()

    # ------------------------------------------------------------------
    def acquire(self, host: str) -> bool:
        """请求进入该域名的抓取许可；返回 False 表示已停止。"""
        if self.delay > 0:
            with self._lock:
                now = time.monotonic()
                slot = max(now, self._next_time.get(host, 0.0))
                jitter = random.uniform(0.0, self.delay * 0.1)
                self._next_time[host] = slot + self.delay + jitter
            if slot > now and not self._wait(slot - now):
                return False

        sem = self._semaphore(host)
        if sem is None:
            return not self.stop_event.is_set()
        while True:
            if self.stop_event.is_set():
                return False
            if sem.acquire(timeout=0.1):
                return True

    def release(self, host: str) -> None:
        sem = self._semaphores.get(host)
        if sem is not None:
            with contextlib.suppress(ValueError):  # pragma: no cover - 防御性处理
                sem.release()


__all__ = ["HostLimiter"]
