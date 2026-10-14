from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from website_downloader.rewrite import rewrite_css_text, rewrite_js_text, rewrite_links
from website_downloader.urltools import canonical_netloc


def test_rewrite_css_queues_nested_asset(tmp_path: Path) -> None:
    queued: list[tuple[str, Path]] = []
    rewritten = rewrite_css_text(
        "body { background: url('../img/bg.png'); }",
        "https://example.com/assets/site.css",
        site_root=tmp_path,
        root_netloc="example.com",
        base_dir=tmp_path / "assets",
        download_external_assets=False,
        enqueue_asset=lambda url, path: queued.append((url, path)),
    )

    assert "../img/bg.png" in rewritten
    assert queued == [("https://example.com/img/bg.png", tmp_path / "img" / "bg.png")]


def test_rewrite_css_import_url_form_maps_once(tmp_path: Path) -> None:
    queued: list[str] = []
    rewritten = rewrite_css_text(
        "@import url('/assets/theme.css?v=2');",
        "https://example.com/assets/site.css",
        site_root=tmp_path,
        root_netloc="example.com",
        base_dir=tmp_path / "assets",
        download_external_assets=False,
        enqueue_asset=lambda url, path: queued.append(url),
    )

    assert queued == ["https://example.com/assets/theme.css?v=2"]
    assert '@import "theme-q' in rewritten


def test_rewrite_js_leaves_api_routes_alone(tmp_path: Path) -> None:
    rewritten = rewrite_js_text(
        "const img = '/static/logo.png'; const api = '/api/data';",
        "https://example.com/app.js",
        site_root=tmp_path,
        root_netloc="example.com",
        base_dir=tmp_path,
        download_external_assets=False,
    )

    assert "'static/logo.png'" in rewritten
    assert "'/api/data'" in rewritten


def test_rewrite_srcset_rewrites_extensionless_attachment(tmp_path: Path) -> None:
    soup = BeautifulSoup(
        '<img src="/attachments/228/content" '
        'srcset="/attachments/228/content 1x, /attachments/229/content 2x">',
        "html.parser",
    )
    rewrite_links(
        soup,
        "https://example.com/page/index.html",
        tmp_path,
        tmp_path / "page",
        download_external_assets=False,
    )

    img = soup.find("img")
    # Both the src and every srcset candidate must point at the local copy so
    # offline mirrors and zip exports keep the responsive image working.
    assert img["src"] == "../attachments/228/content"
    assert img["srcset"] == "../attachments/228/content 1x, ../attachments/229/content 2x"


def test_rewrite_links_skips_canonical_and_rewrites_assets(tmp_path: Path) -> None:
    soup = BeautifulSoup(
        """
        <html>
          <head>
            <base href="https://example.com/">
            <link rel="canonical" href="https://example.com/page">
            <link rel="stylesheet" href="/assets/site.css" integrity="abc" crossorigin>
          </head>
          <body><a href="/about">About</a><img src="/img/logo.png"></body>
        </html>
        """,
        "html.parser",
    )
    rewrite_links(
        soup,
        "https://example.com/index.html",
        tmp_path,
        tmp_path,
        download_external_assets=False,
    )

    assert soup.find("base") is None
    assert soup.find("link", rel="canonical")["href"] == "https://example.com/page"
    assert soup.find("link", rel="stylesheet")["href"] == "assets/site.css"
    assert soup.find("a")["href"] == "about.html"
    assert soup.find("img")["src"] == "img/logo.png"


def test_rewrite_external_asset_strips_sri(tmp_path: Path) -> None:
    soup = BeautifulSoup(
        '<script src="https://cdn.example.com/app.js" integrity="abc" crossorigin="anonymous"></script>',
        "html.parser",
    )
    rewrite_links(
        soup,
        "https://example.com/index.html",
        tmp_path,
        tmp_path,
        download_external_assets=True,
        external_domains={"cdn.example.com"},
    )

    script = soup.find("script")
    assert script["src"] == "cdn/cdn.example.com/app.js"
    assert "integrity" not in script.attrs
    assert "crossorigin" not in script.attrs


def test_rewrite_links_keeps_absolute_url_for_excluded_pages(tmp_path: Path) -> None:
    soup = BeautifulSoup(
        '<a href="/forum/thread1">Forum</a><a href="/about">About</a>',
        "html.parser",
    )
    rewrite_links(
        soup,
        "https://example.com/index.html",
        tmp_path,
        tmp_path,
        download_external_assets=False,
        exclude_patterns=["*/forum/*"],
    )

    links = soup.find_all("a")
    # The excluded page was never downloaded, so it must keep pointing at the
    # live URL instead of a local path that doesn't exist.
    assert links[0]["href"] == "https://example.com/forum/thread1"
    assert links[1]["href"] == "about.html"


def test_rewrite_links_preserves_fragment_for_excluded_pages(tmp_path: Path) -> None:
    soup = BeautifulSoup('<a href="/forum/thread#reply-3">Reply</a>', "html.parser")
    rewrite_links(
        soup,
        "https://example.com/index.html",
        tmp_path,
        tmp_path,
        download_external_assets=False,
        exclude_patterns=["*/forum/*"],
    )

    assert soup.find("a")["href"] == "https://example.com/forum/thread#reply-3"


def test_rewrite_links_keeps_local_path_for_downloaded_asset_matching_exclude(
    tmp_path: Path,
) -> None:
    # "*/forum/*" also matches this asset link, but the crawler still
    # downloads it (only pages are excluded), so the local path must be kept.
    soup = BeautifulSoup('<a href="/forum/logo.png">Logo</a>', "html.parser")
    rewrite_links(
        soup,
        "https://example.com/index.html",
        tmp_path,
        tmp_path,
        download_external_assets=False,
        exclude_patterns=["*/forum/*"],
    )

    assert soup.find("a")["href"] == "forum/logo.png"


def test_canonical_netloc_import_keeps_public_api_available() -> None:
    assert canonical_netloc(urlparse("https://EXAMPLE.com:443/a")) == "example.com"
