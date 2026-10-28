# threadspider

基于 [Scrapling](https://github.com/D4Vinci/Scrapling) 的**多线程**网页抓取框架。

Scrapling 自带的 `scrapling.spiders` 是一套 async（协程）框架；`threadspider` 走的是另一条路：
用 **线程池 + 优先级队列** 编排 Scrapling 的同步 `FetcherSession`，提供一套类似 Scrapy 的
同步爬虫 API。适合：

- 更熟悉 `threading` / 多线程、想避开 asyncio 的场景；
- 回调里有阻塞型逻辑（文件处理、同步数据库、调用本地 CLI 等）；
- 想要开箱即用的去重、重试、限速、中间件与 Pipeline。

## 特性

- **多线程抓取引擎**：可配置并发数，线程安全的优先级调度器 + URL 指纹去重 + 未完成请求计数（自然终止，无忙等）
- **每个工作线程独享一个 `FetcherSession`**：独立连接池与 Cookie 空间，避免共享会话的线程安全问题
- **保留 Scrapling 的全部能力**：TLS 指纹伪装（`impersonate`）、真实浏览器头（`stealthy_headers`）、代理、`Selector` 选择器、自适应解析等
- **中间件**：请求/响应/异常三阶段钩子，内置请求头合并与指数退避重试
- **Pipeline**：JSON Lines、CSV、SQLite（可按列去重）、控制台，或自定义；**全部写入在单独的单线程里串行执行**，天然规避 SQLite/文件句柄并发问题
- **限速与限并发**：按域名的时间槽（含抖动）+ 每域名并发信号量
- **范围控制**：`allowed_domains`、`MAX_DEPTH`、`ALLOWED_SCHEMES`
- **健壮收尾**：Ctrl+C 优雅退出（等待在途请求、刷新 Pipeline），统计汇总输出

## 安装

```bash
# uv
uv add "scrapling[fetchers]"

# 或 pip
pip install "scrapling[fetchers]"
```

> `fetchers` extra 会带上 `curl_cffi` 与 `playwright` 等依赖。本框架只使用其中的同步 HTTP
> 能力，**无需下载浏览器二进制**（`playwright install` 可以不执行）。

## 快速开始

```python
from threadspider import Spider, run


class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]

    custom_settings = {
        "CONCURRENCY": 8,           # 8 个工作线程
        "DOWNLOAD_DELAY": 0.1,      # 同域名两次请求至少间隔 0.1s
        "CONCURRENCY_PER_HOST": 4,  # 同域名最多 4 并发
        "PIPELINES": [
            "threadspider.pipeline:JsonLinesPipeline",
            "threadspider.pipeline:SQLitePipeline",
        ],
        "JSONL_PATH": "output/quotes.jsonl",
        "SQLITE_PATH": "output/quotes.db",
        "SQLITE_UNIQUE_KEYS": ["text"],
    }

    def parse(self, response):
        for quote in response.css(".quote"):
            yield {
                "text": quote.css("span.text::text").get(""),
                "author": quote.css("small.author::text").get(""),
                "tags": list(quote.css("div.tags a.tag::text").getall()),
            }

        # 跟进分页：自动解析相对链接、沿用当前回调
        for href in response.css("li.next a::attr(href)").getall():
            yield response.follow(href)


if __name__ == "__main__":
    result = run(QuotesSpider())
    print(result)          # <CrawlResult reason=finished items=100 requests=10 elapsed=4.0s>
    print(result.stats)    # 完整统计字典
```

完整可运行示例见 [`examples/quotes_spider.py`](examples/quotes_spider.py)：

```bash
uv run python examples/quotes_spider.py
```

## 架构

```
                    ┌─────────────────────────────────────────────┐
  Spider.start_requests() / 回调 yield                            │
                    │                                            │
                    ▼                                            │
        ┌───────────────────────┐   指纹去重 / 优先级队列         │
        │  Scheduler（线程安全） │◄──────────────────────┐        │
        └──────────┬────────────┘                       │        │
                   │  N 个工作线程 get()                 │        │
        ┌──────────▼──────────────────────────────┐     │        │
        │ worker-0 … worker-N                     │     │  yield │
        │  1. 等待重试退避                          │     │  Request/str
        │  2. process_request 中间件链              │     │        │
        │  3. HostLimiter（限速 + 每域名并发）       │     │        │
        │  4. FetcherSession.fetch（每线程独享）     │     │        │
        │  5. process_response 中间件链（逆序）       │─────┘        │
        │  6. callback(response) ──► dict ──┐      │              │
        └───────────────────────────────────┼──────┘              │
                                            │  queue.Queue         │
                                  ┌─────────▼──────────┐          │
                                  │ pipeline 写入线程    │          │
                                  │ （单线程串行处理）    │          │
                                  └─────────┬──────────┘          │
                                            ▼                     │
                              JSONL / CSV / SQLite / 自定义        │
```

### 线程模型要点

| 线程 | 数量 | 职责 |
| --- | --- | --- |
| 主线程 | 1 | 等待调度器清空、处理 Ctrl+C、收尾与统计 |
| 工作线程 | `CONCURRENCY` | 取请求 → 中间件 → 下载 → 中间件 → 执行回调、产出条目 |
| Pipeline 线程 | 1 | 串行执行所有 `process_item` / `open_spider` / `close_spider` |
| 统计线程 | 0 或 1 | 每 `STATS_INTERVAL` 秒打印进度 |

1. **为什么每线程一个 `FetcherSession`？** Scrapling 的会话对象（连接池 + Cookie）不是为多线程
   共享设计的。`Downloader` 用 `threading.local()` 给每个工作线程懒创建一个会话，线程退出时自己
   关闭。代价是 **Cookie 不跨线程共享**（同一会话内的连续请求仍共享）；需要全站共享登录态时，
   可用 `start_requests()` 先拿 Cookie 再通过 `Request(headers=..., cookies=...)` 下发。
2. **如何判断抓取结束？** `Scheduler.pending` 在请求入队时 +1、工作线程处理完该请求（回调执行
   完毕）时 -1。回调先产出新请求（pending 再 +1）才减，所以计数不会提前归零；归零即全部完成。
3. **写入为什么是单线程？** SQLite 连接与文件句柄默认不能跨线程使用，统一收到一个 Pipeline 线程，
   既简单又安全；条目队列可设 `ITEM_QUEUE_SIZE` 产生背压。

## 核心概念

### Spider

```python
class MySpider(Spider):
    name = "my_spider"                      # 唯一名字
    start_urls = ["https://example.com"]    # 起始 URL
    allowed_domains = ["example.com"]       # 可选：域名白名单
    custom_settings = {"CONCURRENCY": 4}    # 可选：本爬虫专属配置

    def start_requests(self):               # 可选：自定义入口（POST、登录、API 批量）
        yield Request("https://example.com/login", method="POST",
                      data={"user": "u", "pass": "p"}, callback=self.parse_home)

    def parse(self, response): ...          # 默认回调（必须实现）
    def parse_detail(self, response): ...   # 自定义回调

    # 可选钩子
    def errback(self, failure): ...         # 重试耗尽/回调异常时调用
    def is_blocked(self, response): ...     # 返回 True 视为被反爬拦截，按重试策略重抓
    def closed(self, reason): ...           # 抓取结束时调用（reason: finished/shutdown/error）
```

### 回调里可以 yield 什么

| 类型 | 行为 |
| --- | --- |
| `dict` 或任意对象 | 作为条目交给 Pipeline |
| `Request` | 新的抓取请求 |
| `str` | 新的 URL（自动相对解析，**沿用当前回调**） |
| 列表 / 生成器 | 递归展开以上类型 |
| `None` | 忽略 |

```python
def parse(self, response):
    yield {"title": response.css("h1::text").get("")}          # 条目
    yield response.follow("/next", callback=self.parse_next)   # 跟进（推荐）
    yield response.follow("/detail/1")                         # 沿用当前回调
    yield Request("https://api.example.com/x", callback=self.api, priority=10)
    yield "/page/2"                                            # 纯字符串也可以
```

### Request

```python
Request(
    url,
    callback=None,            # 回调，默认 spider.parse
    errback=None,             # 失败回调，默认 spider.errback
    method="GET",
    headers=None, params=None, data=None, json=None, cookies=None,
    priority=0,               # 数值越大越先执行
    dont_filter=False,        # True 则跳过去重
    meta={},                  # 自定义元数据，response.meta 可读
    timeout=None,             # 覆盖 DOWNLOAD_TIMEOUT
    proxy=None,               # 覆盖全局 PROXY
    impersonate=None,         # 覆盖全局 IMPERSONATE
    verify=None, follow_redirects=None,
    **extra,                  # 其余参数透传 Scrapling：auth/cert/http3/max_redirects/...
)
```

指纹 = `method + 规范化 URL（查询参数排序、去 fragment）+ 请求体`，用于去重；重试请求
由引擎以 `force=True` 重新入队，不会被去重拦下。

### CrawlResponse

包装 Scrapling 的 `Response`，并补充请求上下文：

```python
response.url          # 最终 URL（重定向后）
response.status       # HTTP 状态码
response.meta         # 请求时的 meta
response.depth        # 当前链接深度
response.raw          # 底层 Scrapling Response
response.css(...)     # ↓ 以下全部透传给 Scrapling Response
response.xpath(...) / response.get() / response.json() / response.markdown()
response.body / response.headers / response.cookies / response.encoding

response.urljoin(href)              # 解析相对链接
response.follow(href, callback=...) # 构造跟进请求（自动 Referer、深度 +1）
response.follow_all([...], callback=...)
```

## 配置项

在 `Spider.custom_settings`、`run(spider, settings=...)` 或 `Settings({...})` 中设置；
**未在下表中的键也会被接受**，方便自定义 Pipeline 读取自己的配置（如 `MY_KEY`）。

### 并发与限速

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `CONCURRENCY` | `8` | 工作线程数 |
| `CONCURRENCY_PER_HOST` | `0` | 单域名最大并发，`0` = 不限制 |
| `DOWNLOAD_DELAY` | `0.0` | 单域名两次请求最小间隔（秒，含最多 10% 随机抖动） |
| `DOWNLOAD_TIMEOUT` | `30` | 单次请求超时（秒） |

### 请求伪装

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `IMPERSONATE` | `"chrome"` | TLS 指纹（`chrome`/`firefox`/`safari`/具体版本/列表随机） |
| `STEALTHY_HEADERS` | `True` | 生成真实浏览器请求头 |
| `DEFAULT_HEADERS` | `{}` | 追加到每个请求，请求自身头优先级更高 |
| `PROXY` | `None` | 全局代理，如 `http://user:pass@host:port` |
| `VERIFY_SSL` | `True` | 校验 HTTPS 证书 |
| `FOLLOW_REDIRECTS` | `"safe"` | 传给 Scrapling 的重定向策略 |
| `FETCHER_RETRIES` | `1` | Scrapling 内部尝试次数；`1` = 只发一次，重试交给框架 |
| `SELECTOR_CONFIG` | `None` | 透传给 Scrapling 解析器，如 `{"adaptive": True}` |

### 重试

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `RETRY_ENABLED` | `True` | 是否启用框架层重试 |
| `RETRY_TIMES` | `3` | 最大重试次数（不含首次） |
| `RETRY_HTTP_CODES` | `(408, 429, 500, 502, 503, 504, 522, 524)` | 触发重试的状态码 |
| `RETRY_BACKOFF_BASE` | `0.5` | 退避 = `base * 2**已重试次数`（+10% 抖动） |
| `RETRY_BACKOFF_MAX` | `60.0` | 退避上限（秒） |

网络异常一律按同样策略重试；`ValueError/TypeError/AttributeError/KeyError` 视为代码问题不重试。

### 范围与队列

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `ALLOWED_DOMAINS` | `None` | 域名白名单，缺省取 `spider.allowed_domains` |
| `ALLOWED_SCHEMES` | `("http", "https")` | 允许的协议 |
| `MAX_DEPTH` | `0` | 链接深度限制，`0` = 不限制 |
| `ITEM_QUEUE_SIZE` | `0` | 条目队列上限，`0` = 无界；有界可产生背压 |
| `SHUTDOWN_TIMEOUT` | `30` | 退出时等待在途请求的最长时间（秒） |

### 中间件 / Pipeline / 日志

| 键 | 默认值 | 说明 |
| --- | --- | --- |
| `MIDDLEWARES` | `["threadspider.middleware:DefaultHeadersMiddleware", "threadspider.middleware:RetryMiddleware"]` | 按顺序执行 `process_request`，逆序执行 `process_response` |
| `PIPELINES` | `[]` | 按顺序处理条目 |
| `LOG_LEVEL` | `"INFO"` | `DEBUG/INFO/WARNING/ERROR` |
| `LOG_FORMAT` | 含线程名的时间格式 | 传给 `logging.basicConfig` |
| `STATS_INTERVAL` | `10` | 运行中打印进度的间隔（秒），`0` = 关闭 |

## 中间件

```python
from threadspider import Middleware, Settings, StatsCollector
from threadspider.exceptions import IgnoreRequest


class BlockedHostMiddleware(Middleware):
    """process_request：丢弃广告域名的请求（不重试）。"""

    def process_request(self, request, spider):
        if request.host.endswith(".ads.example.com"):
            raise IgnoreRequest("广告域名")
        return None


class TokenMiddleware(Middleware):
    """process_request：给每个请求补一个查询参数。"""

    def process_request(self, request, spider):
        request.params = {**(request.params or {}), "token": "abc123"}
        return None


# 启用
custom_settings = {
    "MIDDLEWARES": [
        "threadspider.middleware:DefaultHeadersMiddleware",   # process_request 按此顺序
        "my_module:BlockedHostMiddleware",
        "my_module:TokenMiddleware",
        "threadspider.middleware:RetryMiddleware",            # 重试放最后
    ],
    # process_response / process_exception 按**逆序**执行（即 RetryMiddleware 先跑），
    # 与 Scrapy 的中间件顺序约定一致
}
```

钩子约定：

- `process_request(request, spider)` → `None` 继续 / `Request` 重新调度 / Response 跳过下载（可做缓存）/ 抛 `IgnoreRequest` 丢弃
- `process_response(request, response, spider)` → `Response` 继续 / `Request` 重新调度
  （想自定义延迟重试，返回 `request.copy(retry_at=time.monotonic() + seconds)` 即可，引擎会在下载前等待该时间点）
- `process_exception(request, exc, spider)` → `None` 交给下一环 / `Request` 重试 / Response 视为成功

构造器支持 `(settings, stats)`、`(settings)` 或无参，框架按签名自动实例化。

## Pipeline

内置四个（也可全部同时启用，按顺序流经）：

| Pipeline | 相关配置 | 说明 |
| --- | --- | --- |
| `JsonLinesPipeline` | `JSONL_PATH`（`items.jsonl`）、`JSONL_FLUSH`（`True`） | 追加写 JSON Lines |
| `CsvPipeline` | `CSV_PATH`（`items.csv`）、`CSV_FIELDS` | 首个条目决定表头；`utf-8-sig` 编码，Excel 直接可读 |
| `SQLitePipeline` | `SQLITE_PATH`（`items.db`）、`SQLITE_TABLE`（`items`）、`SQLITE_UNIQUE_KEYS`、`SQLITE_COMMIT_EVERY`（`100`） | 字段按需 `ALTER TABLE`；配置唯一键后 `INSERT OR IGNORE` 去重；`dict/list` 自动存 JSON 文本 |
| `ConsolePipeline` | — | 打印条目，调试用 |

自定义 Pipeline：

```python
import json
from threadspider import Pipeline, DropItem


class MinPricePipeline(Pipeline):
    def __init__(self, settings, stats=None):
        super().__init__(settings, stats)
        self.threshold = float(settings.get("MIN_PRICE", 0))

    def open_spider(self, spider):
        self.count = 0

    def process_item(self, item, spider):
        if float(item.get("price", 0)) < self.threshold:
            raise DropItem(f"价格低于阈值: {item}")
        self.count += 1
        return item

    def close_spider(self, spider, reason):
        print("写入", self.count, "条, 结束原因:", reason)


custom_settings = {
    "PIPELINES": ["my_module:MinPricePipeline", "threadspider.pipeline:JsonLinesPipeline"],
    "MIN_PRICE": 9.9,
}
```

注意：所有 Pipeline 方法都运行在**同一个** Pipeline 线程，`open_spider → process_item* → close_spider`
的调用顺序有保证，可以放心持有文件句柄/数据库连接。

## 日志

框架统一使用 Python 标准 `logging`，所有日志都在 `threadspider` 命名空间下：

```
threadspider                 引擎（启动/收尾/进度/致命错误）
threadspider.spider.<name>   爬虫实例（Spider 自带的 self.logger）
threadspider.downloader      下载器
threadspider.middleware      中间件（重试、丢弃）
threadspider.pipeline        内置 Pipeline（JSONL/CSV/SQLite）
threadspider.asset_mirror    资产镜像 Pipeline
```

### 在爬虫里用 self.logger

`Spider` 基类自带 `self.logger`（按爬虫 `name` 命名），回调里可直接使用：

```python
class MySpider(Spider):
    name = "my"

    def parse(self, response):
        if response.status != 200:
            self.logger.warning("非 200 响应: %s", response.url)
        self.logger.debug("解析 %s", response.url)
        yield {...}
```

### 在自定义 Pipeline / 中间件里取 logger

```python
from threadspider import get_logger

class MyPipeline(Pipeline):
    def open_spider(self, spider):
        self.logger = get_logger("pipeline.mine")   # -> threadspider.pipeline.mine
        self.logger.info("就绪")
```

### 配置输出

引擎启动时按 `LOG_LEVEL` / `LOG_FORMAT` 配置根 logger（用户已配置的 handler 会被尊重，
不会重复挂载）。也可以在 `run()` 之前手动控制：

```python
from threadspider import setup_logging, enable_debug, attach_file_handler

setup_logging("INFO")             # 控制台输出（幂等，force=True 强制重建）
enable_debug()                    # 快捷：框架 + scrapling 全部调到 DEBUG
attach_file_handler("crawl.log")  # 追加文件 handler（UTF-8，多线程安全）
```

| 配置键 | 默认值 | 说明 |
| --- | --- | --- |
| `LOG_LEVEL` | `"INFO"` | `DEBUG/INFO/WARNING/ERROR`，同时作用于 `scrapling` 库日志（至少 WARNING） |
| `LOG_FORMAT` | `%(asctime)s [%(threadName)s] %(levelname)s %(name)s: %(message)s` | 默认格式带线程名，多线程日志可追溯 |

框架根 logger 默认挂 `NullHandler`：作为库被 import 时不会擅自向控制台输出任何内容。

## 运行结果与统计

```python
from threadspider import run, CrawlEngine, Settings

result = run(MySpider())                      # 简写
# 等价于
engine = CrawlEngine(MySpider(), Settings({"CONCURRENCY": 4}))
result = engine.run()

result.reason        # "finished" | "shutdown"(Ctrl+C) | "error"
result.completed     # 是否正常完成
result.items_scraped # 抓到的条目数
result.elapsed       # 耗时（秒）
result.stats         # 全部统计
```

常用统计键：

| 类别 | 键 |
| --- | --- |
| 调度 | `requests_scheduled`、`requests_dequeued`、`seen`、`queued`、`pending`、`filtered`（去重数）、`filtered_duplicates` |
| 下载 | `responses`、`status/<code>`、`download_errors`、`sessions_created`、`retries`、`retry_exhausted` |
| 结果 | `items_scraped`、`items_dropped`、`pipeline_errors`、`jsonl_items` / `csv_items` / `sqlite_items` |
| 错误 | `requests_failed`、`callback_errors`、`errback_errors` |
| 过滤 | `dropped_domains`、`dropped_depth`、`dropped_schemes`、`blocked_retries`、`dropped_on_shutdown` |
| 其他 | `elapsed_seconds` |

## 进阶用法

### 代理轮换

```python
from scrapling.fetchers import ProxyRotator

rotator = ProxyRotator(["http://p1:8080", "http://p2:8080"])

# 下载器给每个请求的 kwargs 都支持 Scrapling 的参数，可放进 Request.extra
yield Request("https://example.com", proxy_rotator=rotator)   # 或全局用 "PROXY"
```

### 优先级与去重控制

```python
yield Request(url, priority=100)      # 高优先级先执行
yield Request(url, dont_filter=True)  # 明确允许重复抓取（如轮询接口）
```

### 判断被反爬拦截

```python
class MySpider(Spider):
    def is_blocked(self, response):
        return response.status in (403, 429) or "captcha" in response.css("title::text").get("")

    def parse(self, response):
        ...
```

返回 `True` 的请求会按 `RETRY_TIMES` / 退避策略重抓，统计记在 `blocked_retries`。

### 失败处理（errback）

```python
from threadspider import Failure

def errback(self, failure: Failure):
    self.logger.warning("失败: %s -> %s", failure.request.url, failure.exception)
    print(failure.get_traceback())
```

### 中途停止

- `Ctrl+C`：主线程捕获 `KeyboardInterrupt`，等待在途请求结束、刷新 Pipeline 后退出（`reason="shutdown"`）；
- 编码控制：`engine.stop_event.set()` 可从任何线程触发同样的收尾流程。

## 与 `scrapling.spiders`（内置框架）的对比

| | `threadspider`（本框架） | `scrapling.spiders`（内置） |
| --- | --- | --- |
| 并发模型 | 多线程（`threading`） | asyncio 协程 |
| 回调 | 普通 `def` + `yield` | 必须 `async def` |
| 阻塞型回调逻辑 | 直接写，天然安全 | 需要 `asyncio.to_thread` 包装 |
| 输出 | Pipeline 链（JSONL/CSV/SQLite/自定义，单写入线程） | `ItemList` 导出 + `on_scraped_item` 钩子 |
| 断点续爬/暂停 | 暂不支持 | 支持（`crawldir`） |
| robots.txt | 暂不支持 | 支持 |
| 会话 | 每线程一个 `FetcherSession` | 命名多会话（含浏览器会话） |

两者共用 Scrapling 的解析引擎与伪装能力，可按场景选择。

## 示例与测试

```bash
# 运行示例（会写入 output/quotes.jsonl 与 output/quotes.db）
uv run python examples/quotes_spider.py

# 单元测试（不依赖网络，打桩下载器）
uv run pytest tests -q

# 代码检查
uv run ruff check .
```

## 目录结构

```
threadspider/
├── __init__.py        # 导出与 run()/run_many() 便捷函数
├── settings.py        # 配置默认值与 Settings 对象
├── request.py         # Request 与 URL 指纹
├── response.py        # CrawlResponse（包装 Scrapling Response）
├── scheduler.py       # 线程安全调度器：优先级队列 + 去重 + pending 计数
├── ratelimit.py       # HostLimiter：按域名限速与并发
├── downloader.py       # Downloader：每线程一个 FetcherSession
├── middleware.py       # 中间件基类 + 请求头 + 重试
├── spider.py           # Spider 基类
├── pipeline.py         # Pipeline 基类 + JSONL/CSV/SQLite/控制台
├── asset_mirror_pipeline.py  # 资产镜像：页面/资源落盘 + URL 改写
├── engine.py           # CrawlEngine：线程编排与生命周期
├── log.py              # 统一日志：get_logger/setup_logging/文件 handler
└── stats.py            # 线程安全统计
examples/quotes_spider.py
examples/themewagon_spider.py
tests/                  # 34 个离线测试
```

## 已知限制

- 不支持 robots.txt 解析与断点续爬；
- 同一会话（线程）内的 Cookie 共享，跨线程不共享；
- 只封装了 Scrapling 的同步 HTTP 抓取（`FetcherSession`），浏览器抓取（`StealthyFetcher`）
  未内置——Playwright 会话无法安全跨线程共享，如需 JS 渲染建议直接使用 `scrapling.spiders`
  或自行实现按线程隔离的下载器；
- 单域名队头阻塞：当某域名的请求占满队列时，其他域名的请求会排在其后（可通过
  `CONCURRENCY_PER_HOST`、`DOWNLOAD_DELAY` 调整策略）。

## License

MIT
