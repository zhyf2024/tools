"""调度器与请求指纹的单元测试（不依赖网络）。"""

from __future__ import annotations

import threading

from threadspider import Request, Scheduler


def test_fingerprint_normalizes_query_order():
    a = Request("https://Example.com/path?b=2&a=1#frag")
    b = Request("https://example.com/path?a=1&b=2")
    c = Request("https://example.com/path?a=1&b=3")
    assert a.fingerprint() == b.fingerprint()
    assert a.fingerprint() != c.fingerprint()


def test_fingerprint_distinguishes_method_and_body():
    get = Request("https://example.com/api", method="GET")
    post = Request("https://example.com/api", method="POST", json={"a": 1})
    post_same = Request("https://example.com/api", method="POST", json={"a": 1})
    post_other = Request("https://example.com/api", method="POST", json={"a": 2})
    assert get.fingerprint() != post.fingerprint()
    assert post.fingerprint() == post_same.fingerprint()
    assert post.fingerprint() != post_other.fingerprint()


def test_scheduler_dedupe_and_pending():
    scheduler = Scheduler()
    first = Request("https://example.com/")
    dup = Request("https://example.com/")
    assert scheduler.add(first) is True
    assert scheduler.add(dup) is False
    assert scheduler.pending == 1
    assert scheduler.add(Request("https://example.com/", dont_filter=True)) is True
    assert scheduler.pending == 2
    scheduler.task_done()
    scheduler.task_done()
    assert scheduler.pending == 0
    assert scheduler.join(timeout=1) is True


def test_scheduler_priority_order():
    scheduler = Scheduler()
    scheduler.add(Request("https://example.com/low", priority=0))
    scheduler.add(Request("https://example.com/high", priority=10))
    scheduler.add(Request("https://example.com/mid", priority=5))
    order = [scheduler.get(timeout=1).url for _ in range(3)]
    assert order == [
        "https://example.com/high",
        "https://example.com/mid",
        "https://example.com/low",
    ]


def test_scheduler_get_returns_none_when_finished():
    scheduler = Scheduler()
    assert scheduler.get(timeout=0.05) is None  # 空队列且 pending == 0
    scheduler.add(Request("https://example.com/"))
    request = scheduler.get(timeout=0.05)
    assert request is not None
    scheduler.task_done()  # 取出的请求处理完毕
    assert scheduler.get(timeout=0.05) is None  # 队列空 + pending 归零


def test_scheduler_thread_safety():
    scheduler = Scheduler(dupefilter=False)
    total = 500

    def producer():
        for index in range(total):
            scheduler.add(Request(f"https://example.com/{index}"))

    threads = [threading.Thread(target=producer) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert scheduler.pending == total * 4
    consumed = 0
    while True:
        request = scheduler.get(timeout=0.2)
        if request is None:
            break
        scheduler.task_done()
        consumed += 1
    assert consumed == total * 4
    assert scheduler.pending == 0
