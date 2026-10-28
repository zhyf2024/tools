"""镜像 Pipeline 的链接收集与收尾补写测试（threadspider.asset_mirror_pipeline）。"""

from __future__ import annotations

import sqlite3

from threadspider.asset_mirror_pipeline import AssetMirrorPipeline
from threadspider.settings import Settings


def _make_pipeline(tmp_path) -> AssetMirrorPipeline:
    settings = Settings(
        {
            "MIRROR_ROOT": str(tmp_path / "mirror"),
            "MIRROR_DB": str(tmp_path / "mirror.db"),
            "MIRROR_REWRITE_EXTERNAL": True,
        }
    )
    return AssetMirrorPipeline(settings)


def test_collect_skips_navigation_and_page_links(tmp_path):
    pipe = _make_pipeline(tmp_path)
    html = """
    <a href="/themes/a/">本站导航</a>
    <a href="https://other.com/x">外站导航</a>
    <link rel="canonical" href="https://site.com/tag/">
    <link rel="next" href="https://site.com/tag/page/2/">
    <link rel="alternate" href="https://site.com/feed/">
    <link rel="stylesheet" href="/css/a.css">
    <img src="/img/a.png">
    <img src="https://cdn.com/b.png">
    """
    urls = set(pipe._collect_asset_urls("https://site.com/tag/", html))
    # 导航链接（含本站）不收集、不下载，留给收尾补写
    assert "https://site.com/themes/a/" not in urls
    assert "https://other.com/x" not in urls
    # 指向页面的 <link>（canonical/分页）不收集，避免重复下载页面
    assert "https://site.com/tag/" not in urls
    assert "https://site.com/tag/page/2/" not in urls
    # feed（alternate）与真实静态资源照常收集
    assert "https://site.com/feed/" in urls
    assert "https://site.com/css/a.css" in urls
    assert "https://site.com/img/a.png" in urls
    assert "https://cdn.com/b.png" in urls


def test_rewrite_cross_page_links_relativizes_saved_pages(tmp_path):
    pipe = _make_pipeline(tmp_path)
    mirror = tmp_path / "mirror" / "site.com"
    listing = mirror / "tag" / "index.html"
    preview = mirror / "preview" / "demo" / "index.html"
    listing.parent.mkdir(parents=True)
    preview.parent.mkdir(parents=True)
    listing.write_text(
        '<a href="https://preview.site.com/demo/">Live preview</a>'
        '<a href="https://preview.site.com/other">Live preview</a>'
        '<a href="https://elsewhere.com/">外站</a>',
        encoding="utf-8",
    )
    preview.write_text("<html>ok</html>", encoding="utf-8")
    other = mirror / "preview" / "other" / "index.html"
    other.parent.mkdir(parents=True)
    other.write_text("<html>ok</html>", encoding="utf-8")

    conn = sqlite3.connect(tmp_path / "mirror.db")
    conn.execute("CREATE TABLE pages (url TEXT PRIMARY KEY, local_path TEXT)")
    conn.executemany(
        "INSERT INTO pages VALUES (?, ?)",
        [
            ("https://site.com/tag/", str(listing)),
            ("https://preview.site.com/demo/", str(preview)),
            # 卡片链接缺尾斜杠，镜像库里是重定向后的带斜杠 URL
            ("https://preview.site.com/other/", str(other)),
        ],
    )
    conn.commit()
    pipe.conn = conn

    pipe._rewrite_cross_page_links()

    content = listing.read_text(encoding="utf-8")
    assert 'href="../preview/demo/index.html"' in content
    # 缺尾斜杠的链接也能匹配到镜像页
    assert 'href="../preview/other/index.html"' in content
    # 未镜像的外站链接保持原样
    assert 'href="https://elsewhere.com/"' in content
