"""日志工具的单元测试（threadspider.log）。"""

from __future__ import annotations

import logging

from threadspider.log import (
    ROOT_LOGGER_NAME,
    attach_file_handler,
    enable_debug,
    get_logger,
    setup_logging,
)


def test_get_logger_prefixes_names():
    assert get_logger("downloader").name == "threadspider.downloader"
    # 已带前缀不重复添加
    assert get_logger("threadspider.pipeline").name == "threadspider.pipeline"
    # 空名字返回根 logger
    assert get_logger().name == ROOT_LOGGER_NAME


def test_root_logger_has_null_handler():
    """作为库被 import 时不应擅自输出日志。"""
    root = logging.getLogger(ROOT_LOGGER_NAME)
    assert any(isinstance(h, logging.NullHandler) for h in root.handlers)


def test_setup_logging_configures_root():
    setup_logging("WARNING", force=True)
    root = logging.getLogger()
    assert root.level == logging.WARNING
    # 至少有一个非 Null 的输出 handler
    assert any(not isinstance(h, logging.NullHandler) for h in root.handlers)
    # setup_logging 幂等：重复调用不叠加 handler
    count = len(root.handlers)
    setup_logging("WARNING", force=True)
    assert len(root.handlers) == count


def test_setup_logging_accepts_int_level():
    setup_logging(logging.ERROR, force=True)
    assert logging.getLogger().level == logging.ERROR


def test_spider_has_logger():
    from threadspider import Spider

    class MySpider(Spider):
        name = "my"

    assert MySpider().logger.name == "threadspider.spider.my"

    # 未设置 name 时用类名
    assert Spider().logger.name == "threadspider.spider.Spider"


def test_engine_backfills_missing_logger():
    """子类自定义 __init__ 未调用 super() 时，引擎兜底补 logger。"""
    from threadspider import CrawlEngine, Spider

    class NoInitSpider(Spider):
        name = "noinit"

        def __init__(self):  # 故意不调用 super().__init__()
            pass

    spider = NoInitSpider()
    assert not hasattr(spider, "logger")
    engine = CrawlEngine(spider, {"STATS_INTERVAL": 0})
    assert engine.spider.logger.name == "threadspider.spider.noinit"


def test_attach_file_handler_writes(tmp_path):
    log_path = tmp_path / "crawl.log"
    handler = attach_file_handler(str(log_path))
    try:
        get_logger("test.file").info("hello-日志")
        for h in logging.getLogger(ROOT_LOGGER_NAME).handlers:
            h.flush()
        content = log_path.read_text(encoding="utf-8")
        assert "hello-日志" in content
    finally:
        logging.getLogger(ROOT_LOGGER_NAME).removeHandler(handler)
        handler.close()


def test_enable_debug_sets_levels():
    try:
        enable_debug()
        # 子 logger 保持 NOTSET（level=0）向下继承，验证有效级别
        assert get_logger("downloader").getEffectiveLevel() == logging.DEBUG
    finally:
        setup_logging("WARNING", force=True)
