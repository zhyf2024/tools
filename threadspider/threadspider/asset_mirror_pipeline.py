"""资产镜像 Pipeline：下载页面及所有静态资源，重写 URL 以便离线浏览。

流程（全部在 Pipeline 写入线程内串行执行）：

1. ``process_item`` 收到带 ``url`` 的条目（条目里若已带 ``html`` 则直接使用，
   否则用独立的会话补一次下载）；
2. 用 :class:`_AssetURLCollector`（基于 ``html.parser``）收集页面里的
   ``src/href/srcset/poster`` 等资源地址，逐个下载到镜像目录
   （``<a href>`` 导航与 ``<link rel=canonical/next/...>`` 页面引用不收集
   不下载，收尾时按实际镜像结果统一改写）；
3. 用 :class:`_AssetHTMLRewriter` 把页面里的资源地址改写为指向本地文件的
   相对路径（``<link>`` 引入的 CSS 内部的 ``url()`` 也会一并改写）；
4. 页面与资源的 ``URL -> 本地路径`` 映射记录到 SQLite（``pages`` / ``assets``
   表），天然去重：同一资源只下载一次，重复页面直接跳过。

相关配置：

- ``MIRROR_ROOT``：镜像根目录（默认 ``output/mirror``）
- ``MIRROR_DB``：映射数据库路径（默认 ``output/mirror.db``）
- ``MIRROR_ALLOWED_DOMAINS``：允许镜像的域名，默认取 ``ALLOWED_DOMAINS``
- ``MIRROR_REWRITE_EXTERNAL``：是否连外域资源 URL 也改写（默认 ``False``，
  外域资源本身不下载）
"""

from __future__ import annotations

import contextlib
import os
import re
import sqlite3
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

from scrapling.fetchers import FetcherSession

from .log import get_logger
from .pipeline import Pipeline
from .settings import Settings
from .stats import StatsCollector

logger = get_logger("asset_mirror")

#: HTML 中携带资源地址的常规属性
_URL_ATTRS = ("src", "href", "poster", "data-src", "data-original")

#: ``<link rel=...>`` 中指向 HTML 页面的关系（canonical/分页/协作发现等）：
#: 这些引用的是页面而非静态资源，不作为资源下载（否则会级联下载整站页面、
#: 与条目流程重复抓取甚至覆盖已改写的镜像），统一留给收尾补写按镜像结果改写。
#: 注意不含 ``alternate``——它常指向 RSS/Atom feed 等真实资源。
_PAGE_LINK_RELS = frozenset(
    {
        "canonical",
        "next",
        "prev",
        "first",
        "last",
        "shortlink",
        "amphtml",
        "edituri",
        "hub",
        "pingback",
        "replies",
    }
)

#: 文件没有扩展名时按 Content-Type 补扩展名
_CONTENT_TYPES = {
    # 样式与脚本
    "text/html": ".html",
    "application/xhtml+xml": ".html",
    "text/css": ".css",
    "application/javascript": ".js",
    "text/javascript": ".js",
    "application/x-javascript": ".js",
    "application/json": ".json",
    # 图片
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/avif": ".avif",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    # 字体
    "font/woff2": ".woff2",
    "font/woff": ".woff",
    "font/ttf": ".ttf",
    "font/otf": ".otf",
    "application/font-woff2": ".woff2",
    "application/font-woff": ".woff",
    "application/x-font-woff": ".woff",
    "application/x-font-ttf": ".ttf",
    "application/vnd.ms-fontobject": ".eot",
    # 音视频与文档
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/webm": ".weba",
    "audio/wav": ".wav",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "application/pdf": ".pdf",
    "application/xml": ".xml",
    "text/xml": ".xml",
    "application/rss+xml": ".xml",
    "application/atom+xml": ".xml",
    "application/rdf+xml": ".xml",
    "application/wasm": ".wasm",
    "application/gzip": ".gz",
    "application/zip": ".zip",
}

#: 文件魔数（magic bytes）嗅探表，顺序即优先级；`RIFF/ftyp` 容器需额外校验偏移位
_MAGIC_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
    (b"wOFF", ".woff"),
    (b"wOF2", ".woff2"),
    (b"OTTO", ".otf"),
    (b"\x00\x01\x00\x00\x00", ".ttf"),
    (b"ttcf", ".ttc"),
    (b"\x00\x00\x01\x00", ".ico"),
    (b"BM", ".bmp"),
    (b"II*\x00", ".tiff"),
    (b"MM\x00*", ".tiff"),
    (b"%PDF", ".pdf"),
    (b"PK\x03\x04", ".zip"),
    (b"\x1f\x8b", ".gz"),
    (b"OggS", ".ogg"),
    (b"ID3", ".mp3"),
    (b"\x1a\x45\xdf\xa3", ".webm"),
)

#: RIFF 容器第 8-12 字节的子类型
_RIFF_VARIANTS = {b"WEBP": ".webp", b"WAVE": ".wav", b"AVI ": ".avi"}


def _content_type_of(resp) -> str:
    """从响应头取小写的 Content-Type 主值（不含 charset 等参数）。"""
    headers = resp.headers or {}
    raw = headers.get("content-type") or headers.get("Content-Type") or ""
    return str(raw).split(";")[0].strip().lower()


def _sniff_extension(body: bytes, content_type: str = "") -> str | None:
    """推断资源的真实扩展名：Content-Type → 文件魔数（magic bytes）→ SVG 文本特征。

    返回 ``None`` 表示无法识别，交由调用方做最后兜底。
    """
    ext = _CONTENT_TYPES.get(content_type)
    if ext:
        return ext

    head = body[:512]
    # RIFF/ISO-BMFF 容器需要看内部子类型
    if head.startswith(b"RIFF") and len(head) >= 12:
        return _RIFF_VARIANTS.get(head[8:12])
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return ".mp4"  # mp4/m4a/mov 同族
    for prefix, ext in _MAGIC_SIGNATURES:
        if head.startswith(prefix):
            return ext

    # 纯文本格式没有固定魔数，按内容特征识别（HTML/SVG 标签大小写不敏感）
    stripped = head.lstrip().lower()
    if stripped.startswith((b"<svg", b"<?xml")) and b"<svg" in stripped:
        return ".svg"
    if stripped.startswith((b"<!doctype html", b"<html", b"<?xml")) and b"<html" in stripped:
        return ".html"
    # RSS/Atom 等 XML 文档（如 <link rel="alternate"> 引用的 feed）
    if stripped.startswith((b"<?xml", b"<rss", b"<feed", b"<urlset")):
        return ".xml"
    return None


def _is_html(resp) -> bool:
    """判断响应体是不是 HTML 页面（链接指向的页面不应按普通资源落盘）。"""
    if _content_type_of(resp) in ("text/html", "application/xhtml+xml"):
        return True
    return _sniff_extension(resp.body, "") == ".html"

#: 页面声明的非 UTF-8 字符集，落盘时统一转成 UTF-8 并改写声明
_CHARSET_RE = re.compile(
    r'(<meta[^>]+charset\s*=\s*["\']?)([a-zA-Z0-9_\-]+)',
    re.IGNORECASE,
)
_CSS_URL_RE = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")

#: 属性值里的绝对 URL（收尾补写时用于定位指向其他镜像页的链接）
_ABS_URL_ATTR_RE = re.compile(r'(href|src)="(https?://[^"]+)"')


def _iter_srcset_urls(value: str) -> list[str]:
    """把 ``srcset`` 属性拆成单个 URL 列表（忽略描述性参数如 2x/480w）。"""
    urls: list[str] = []
    for part in value.split(","):
        candidate = part.strip().split()[0] if part.strip() else ""
        if candidate:
            urls.append(candidate)
    return urls


def _escape_attr(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;")


class _AssetURLCollector(HTMLParser):
    """收集页面中的资源地址（比正则更可靠，能处理无引号/单引号/换行）。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        #: ``(标签, 属性, 原始 URL, link 的 rel)``,调用方据此区分导航/页面引用与真资源
        self.urls: list[tuple[str, str, str, str]] = []

    def handle_starttag(self, tag, attrs):
        rel = ""
        if tag == "link":
            for name, value in attrs:
                if name == "rel" and value:
                    rel = value.lower()
                    break
        for name, value in attrs:
            if not value:
                continue
            if name in _URL_ATTRS:
                self.urls.append((tag, name, value, rel))
            elif name == "srcset":
                for url in _iter_srcset_urls(value):
                    self.urls.append((tag, "srcset", url, rel))

    handle_startendtag = handle_starttag


class _AssetHTMLRewriter(HTMLParser):
    """HTML 重写器：把资源地址替换为本地相对路径。"""

    def __init__(self, base_url: str, asset_map: dict[str, str], rewrite_external: bool = False):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.asset_map = asset_map
        self.rewrite_external = rewrite_external
        self.parts: list[str] = []

    # -- 标签重建：HTMLParser 会先解码实体/引号，输出时需要重新转义 --
    def handle_starttag(self, tag, attrs):
        rendered = []
        for name, value in attrs:
            if value is None:
                rendered.append(f" {name}")
            elif name in _URL_ATTRS:
                rendered.append(f' {name}="{_escape_attr(self._rewrite_url(value))}"')
            elif name == "srcset":
                rewritten = ", ".join(
                    f"{self._rewrite_url(url)}" + suffix
                    for url, suffix in self._iter_srcset(value)
                )
                rendered.append(f' srcset="{_escape_attr(rewritten)}"')
            else:
                rendered.append(f' {name}="{_escape_attr(value)}"')
        self.parts.append(f"<{tag}{''.join(rendered)}>")

    def handle_startendtag(self, tag, attrs):
        # 自闭合写法（<img/>）不追加多余结束标签
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data):
        self.parts.append(f"<?{data}>")

    def get_html(self) -> str:
        return "".join(self.parts)

    # ------------------------------------------------------------------
    @staticmethod
    def _iter_srcset(value: str):
        for part in value.split(","):
            bits = part.strip().split(None, 1)
            if bits:
                yield bits[0], f" {bits[1]}" if len(bits) > 1 else ""

    def _rewrite_url(self, url: str) -> str:
        url = url.strip()
        if not url or url.startswith(("#", "data:", "javascript:", "mailto:", "tel:")):
            return url
        abs_url = urljoin(self.base_url, url)
        return self.asset_map.get(abs_url, url)


class AssetMirrorPipeline(Pipeline):
    """把页面与静态资源保存到本地镜像目录，并重写页面 URL 指向本地文件。"""

    def __init__(self, settings: Settings, stats: StatsCollector | None = None) -> None:
        super().__init__(settings, stats)
        self.mirror_root = str(settings.get("MIRROR_ROOT", "output/mirror"))
        self.mirror_db = str(settings.get("MIRROR_DB", "output/mirror.db"))
        domains = settings.get("MIRROR_ALLOWED_DOMAINS") or settings.get("ALLOWED_DOMAINS")
        self.allowed_domains: list[str] = [str(d).lower().lstrip(".") for d in (domains or [])]
        self.rewrite_external = settings.getbool("MIRROR_REWRITE_EXTERNAL", False)
        self.timeout = settings.getfloat("DOWNLOAD_TIMEOUT", 30.0)
        self._factory = None
        self._session = None

    # ==================================================================
    # 生命周期
    # ==================================================================
    def open_spider(self, spider) -> None:
        if not self.allowed_domains and spider.allowed_domains:
            self.allowed_domains = [str(d).lower().lstrip(".") for d in spider.allowed_domains]
        os.makedirs(self.mirror_root, exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(self.mirror_db)), exist_ok=True)
        self._factory = FetcherSession(
            impersonate=self.settings.get("IMPERSONATE") or "chrome",
            timeout=self.timeout,
            retries=1,  # 资源失败就跳过，不做重试
        )
        self._session = self._factory.__enter__()
        self.conn = sqlite3.connect(self.mirror_db, check_same_thread=True)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                url TEXT PRIMARY KEY,
                local_path TEXT,
                depth INTEGER,
                title TEXT,
                assets INTEGER DEFAULT 0,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                url TEXT PRIMARY KEY,
                local_path TEXT,
                kind TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
        logger.info(
            "镜像输出: %s (映射库 %s, 允许域名 %s)",
            os.path.abspath(self.mirror_root),
            os.path.abspath(self.mirror_db),
            self.allowed_domains or "全部",
        )

    def close_spider(self, spider, reason: str) -> None:
        if getattr(self, "conn", None) is not None:
            try:
                self._rewrite_cross_page_links()
            except Exception:  # pragma: no cover - 收尾补写失败不影响结果
                logger.exception("收尾改写跨页链接失败")
            self.conn.close()
        if self._factory is not None:
            self._factory.__exit__(None, None, None)
        if self.stats:
            self.stats.inc("mirror_closed")
        logger.info(
            "镜像完成（%s）: 页面=%d, 资源=%d, 跳过=%d, 错误=%d",
            reason,
            self.stats.get("mirror_saved", 0) if self.stats else 0,
            self.stats.get("mirror_assets_downloaded", 0) if self.stats else 0,
            self.stats.get("mirror_skipped", 0) if self.stats else 0,
            self.stats.get("mirror_errors", 0) if self.stats else 0,
        )

    # ==================================================================
    # 条目处理
    # ==================================================================
    def process_item(self, item: Any, spider) -> Any:
        if not isinstance(item, dict):
            return item
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return item
        if not self._domain_allowed(url):
            return item

        page_path = self._page_local_path(url)
        try:
            existing = self.conn.execute(
                "SELECT local_path FROM pages WHERE url = ?", (url,)
            ).fetchone()
            if existing and not item.get("html"):
                # 同一 URL 已镜像过，且本条目没有带来新的 HTML（例如列表页
                # 先以摘要条目出现、抓取后再以完整条目出现时会覆盖保存）
                if self.stats:
                    self.stats.inc("mirror_skipped")
                logger.debug("跳过已镜像页面: %s", url)
                return item

            html = item.get("html")
            if not html:
                resp = self._session.get(url)
                if resp.status >= 400:
                    raise RuntimeError(f"HTTP {resp.status}")
                # Scrapling Response 的 HTML 正文在 html_content（text 是纯文本）
                html = resp.html_content

            asset_map = self._download_assets(url, html, page_path)
            rewritten = self._rewrite_html(url, html, asset_map)
            os.makedirs(os.path.dirname(page_path), exist_ok=True)
            with open(page_path, "w", encoding="utf-8") as fh:
                fh.write(rewritten)

            self.conn.execute(
                "INSERT OR REPLACE INTO pages (url, local_path, depth, title, assets) "
                "VALUES (?, ?, ?, ?, ?)",
                (url, page_path, item.get("depth", 0), item.get("title", ""), len(asset_map)),
            )
            self.conn.commit()

            if self.stats:
                self.stats.inc("mirror_saved")
                self.stats.inc("mirror_assets_downloaded", self._last_new_assets)
            item["saved_path"] = page_path
            item["assets"] = len(asset_map)
            logger.debug("镜像页面 %s -> %s (%d 个资源, 新下载 %d)", url, page_path, len(asset_map), self._last_new_assets)
        except Exception as exc:
            if self.stats:
                self.stats.inc("mirror_errors")
            item["mirror_error"] = str(exc)
            logger.warning("镜像失败 %s: %r", url, exc)

        return item

    # ==================================================================
    # 路径与域名
    # ==================================================================
    def _domain_allowed(self, url: str) -> bool:
        if not self.allowed_domains:
            return True
        host = (urlparse(url).hostname or "").lower()
        return any(host == d or host.endswith("." + d) for d in self.allowed_domains)

    def _page_local_path(self, url: str) -> str:
        parts = urlparse(url)
        path = parts.path or "/"
        if path.endswith("/"):
            path += "index.html"
        if not os.path.splitext(path)[1]:
            path += "/index.html" if path.endswith("/") else ".html"
        safe = re.sub(r"[^0-9A-Za-z_\-./]", "_", path).lstrip("/")
        return os.path.join(self.mirror_root, parts.netloc, safe)

    @staticmethod
    def _posix_relpath(target: str, start: str) -> str:
        """相对路径（HTML 里必须用 ``/``，Windows 的 ``\\`` 会让浏览器解析失败）。"""
        return os.path.relpath(target, start).replace(os.sep, "/")

    def _rewrite_cross_page_links(self) -> None:
        """收尾补写：条目保存顺序不定，处理某页时其他页面（如 Live preview
        演示页）可能尚未落库，其外链无法改写。全部页面入库后统一把指向
        已镜像页面的绝对链接改为相对路径，保证离线可跳转。"""
        rows = self.conn.execute("SELECT url, local_path FROM pages").fetchall()
        page_paths: dict[str, str] = dict(rows)
        changed = 0
        for _, path in rows:
            try:
                with open(path, encoding="utf-8") as fh:
                    html = fh.read()
            except OSError:
                continue

            def _sub(match: re.Match[str], _path: str = path) -> str:
                abs_url = match.group(2)
                target = (
                    page_paths.get(abs_url)
                    # 卡片链接常缺尾斜杠（重定向后才补上），补一次再查
                    or page_paths.get(abs_url.rstrip("/") + "/")
                    or page_paths.get(abs_url.replace("&amp;", "&"))
                )
                if not target:
                    return match.group(0)
                rel = self._posix_relpath(target, os.path.dirname(_path))
                return f'{match.group(1)}="{_escape_attr(rel)}"'

            new_html = _ABS_URL_ATTR_RE.sub(_sub, html)
            if new_html != html:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new_html)
                changed += 1
        if changed:
            logger.info("收尾补写: %d 个页面的跨页链接改为相对路径", changed)

    # ==================================================================
    # 资源下载
    # ==================================================================
    def _collect_asset_urls(self, base_url: str, html: str) -> list[str]:
        """收集页面引用的静态资源绝对 URL（不含导航/页面引用）。

        以下引用指向的是 HTML 页面而非静态资源，一律不收集（不下载也不在
        处理时改写），由 :meth:`_rewrite_cross_page_links` 收尾时按实际镜像
        结果统一改写为相对路径：

        - ``<a href>`` 导航链接（否则一个列表页上百个链接会级联下载整站页面；
          外站链接也保留原始 URL）；
        - ``<link rel=canonical/next/prev/...>`` 等指向页面的关系引用
          （否则每个条目都会把自己的 canonical 当资源重复下载一遍）。
        """
        collector = _AssetURLCollector()
        with contextlib.suppress(Exception):  # pragma: no cover - 极端畸形 HTML
            collector.feed(html)
        page_netloc = urlparse(base_url).netloc
        seen: dict[str, None] = {}
        for tag, attr, candidate, rel in collector.urls:
            candidate = candidate.strip()
            if not candidate or candidate.startswith(("#", "data:", "javascript:", "mailto:", "tel:")):
                continue
            abs_url = urljoin(base_url, candidate)
            parts = urlparse(abs_url)
            if parts.scheme not in ("http", "https"):
                continue
            # 导航链接与指向页面的 <link>：留给收尾补写处理
            if attr == "href" and (
                tag == "a" or (tag == "link" and set(rel.split()) & _PAGE_LINK_RELS)
            ):
                continue
            if not self.rewrite_external and parts.netloc != page_netloc:
                continue
            seen.setdefault(abs_url)
        return list(seen)

    def _download_assets(self, page_url: str, html: str, page_path: str) -> dict[str, str]:
        """下载页面引用的所有资源，返回 ``绝对 URL -> 页面相对路径`` 映射。"""
        asset_map: dict[str, str] = {}
        self._last_new_assets = 0
        page_dir = os.path.dirname(page_path)

        for asset_url in self._collect_asset_urls(page_url, html):
            # 链接指向的页面已镜像过：直接映射到页面文件，不再当资源重复下载
            page_row = self.conn.execute(
                "SELECT local_path FROM pages WHERE url = ?", (asset_url,)
            ).fetchone()
            if page_row:
                asset_map[asset_url] = self._posix_relpath(page_row[0], page_dir)
                continue

            row = self.conn.execute(
                "SELECT local_path FROM assets WHERE url = ?", (asset_url,)
            ).fetchone()
            if row:
                asset_map[asset_url] = self._posix_relpath(row[0], page_dir)
                continue

            try:
                resp = self._session.get(asset_url)
                if resp.status >= 400:
                    logger.debug("资源 HTTP %d，跳过: %s", resp.status, asset_url)
                    continue
                if _is_html(resp):
                    # 收集到的资源实际是 HTML 页面（如 <iframe> 嵌入页、
                    # 非页面关系的 <link>）：按页面路径保存以便本地打开。
                    # 落盘路径用重定向后的最终 URL（如目录型 URL 会补斜杠）
                    final_url = str(getattr(resp, "url", "") or asset_url)
                    local_path = self._page_local_path(final_url)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, "wb") as fh:
                        fh.write(resp.body)
                    kind = "html"
                else:
                    local_path = self._asset_local_path(asset_url, resp)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    body = resp.body
                    if local_path.endswith(".css"):
                        # CSS 不是 HTML，直接解码原始字节（.text/.html_content 会走 HTML 解析）
                        css_text = resp.body.decode(resp.encoding or "utf-8", "replace")
                        body = self._mirror_css_references(asset_url, css_text, local_path).encode("utf-8")
                    with open(local_path, "wb") as fh:
                        fh.write(body)
                    kind = os.path.splitext(local_path)[1].lstrip(".")
                self.conn.execute(
                    "INSERT OR REPLACE INTO assets (url, local_path, kind) VALUES (?, ?, ?)",
                    (asset_url, local_path, kind),
                )
                self.conn.commit()
                self._last_new_assets += 1
                asset_map[asset_url] = self._posix_relpath(local_path, page_dir)
            except Exception as exc:
                logger.debug("资源下载失败，跳过 %s: %r", asset_url, exc)
                continue

        return asset_map

    def _asset_local_path(self, url: str, resp) -> str:
        parts = urlparse(url)
        path = parts.path or "/asset"
        safe = re.sub(r"[^0-9A-Za-z_\-./]", "_", path).lstrip("/")
        if not os.path.splitext(safe)[1]:
            # URL 无扩展名：按 Content-Type/魔数嗅探真实类型；仅无法识别时才 .bin
            ext = _sniff_extension(resp.body, _content_type_of(resp)) or ".bin"
            # 以 / 结尾的 URL 不能拼成 ``dir/.png``（隐藏文件）
            safe += ("index" + ext) if safe.endswith("/") else ext
        return os.path.join(self.mirror_root, parts.netloc, safe)

    def _mirror_css_references(self, css_url: str, css_text: str, css_local_path: str) -> str:
        """下载 CSS 里 ``url()`` 引用的资源，并把 CSS 内容改写为相对路径。"""
        css_dir = os.path.dirname(css_local_path)
        replacements: dict[str, str] = {}

        for match in _CSS_URL_RE.finditer(css_text):
            raw = match.group(2).strip()
            if not raw or raw.startswith(("data:", "#", "//")):
                continue
            abs_url = urljoin(css_url, raw)
            parts = urlparse(abs_url)
            if parts.scheme not in ("http", "https"):
                continue
            if not self.rewrite_external and parts.netloc != urlparse(css_url).netloc:
                continue
            if abs_url in replacements:
                continue
            row = self.conn.execute(
                "SELECT local_path FROM assets WHERE url = ?", (abs_url,)
            ).fetchone()
            if row:
                local_path = row[0]
            else:
                try:
                    resp = self._session.get(abs_url)
                    if resp.status >= 400:
                        continue
                    local_path = self._asset_local_path(abs_url, resp)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, "wb") as fh:
                        fh.write(resp.body)
                    self.conn.execute(
                        "INSERT OR REPLACE INTO assets (url, local_path, kind) VALUES (?, ?, ?)",
                        (abs_url, local_path, os.path.splitext(local_path)[1].lstrip(".")),
                    )
                    self.conn.commit()
                    self._last_new_assets += 1
                except Exception:
                    continue
            replacements[abs_url] = self._posix_relpath(local_path, css_dir)

        def _sub(match: re.Match[str]) -> str:
            quote = match.group(1)
            raw = match.group(2).strip()
            abs_url = urljoin(css_url, raw)
            if abs_url not in replacements:
                return match.group(0)
            return f"url({quote}{replacements[abs_url]}{quote})"

        return _CSS_URL_RE.sub(_sub, css_text)

    # ==================================================================
    # HTML 重写
    # ==================================================================
    def _rewrite_html(self, base_url: str, html: str, asset_map: dict[str, str]) -> str:
        rewriter = _AssetHTMLRewriter(base_url, asset_map, rewrite_external=self.rewrite_external)
        rewriter.feed(html)
        rewritten = rewriter.get_html()
        # 文件按 UTF-8 落盘，页面声明若是其他字符集则同步改写，避免浏览器乱码
        return _CHARSET_RE.sub(lambda m: m.group(1) + "utf-8", rewritten, count=1)


__all__ = ["AssetMirrorPipeline"]
