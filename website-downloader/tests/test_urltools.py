from __future__ import annotations

from website_downloader.urltools import (
    canonicalize_url,
    is_allowed_external,
    is_blacklisted,
    is_internal,
    normalize_external_domains,
)


def test_canonicalize_url_drops_fragments_and_default_ports() -> None:
    result = canonicalize_url("/docs/page.html#part", "https://EXAMPLE.com:443/base/")
    assert result == "https://example.com/docs/page.html"


def test_is_internal_treats_www_as_same_site() -> None:
    assert is_internal("https://www.example.com/a.css", "example.com")
    assert is_internal("/a.css", "example.com")
    assert not is_internal("https://cdn.example.net/a.css", "example.com")


def test_external_domain_whitelist_accepts_subdomains() -> None:
    domains = normalize_external_domains(["https://cdn.example.com", "assets.test"])
    assert domains == {"cdn.example.com", "assets.test"}
    assert is_allowed_external("https://img.cdn.example.com/a.png", domains)
    assert not is_allowed_external("https://example.org/a.png", domains)


def test_is_blacklisted_matches_path_glob_regardless_of_host() -> None:
    patterns = ["*/forum/*"]
    assert is_blacklisted("https://example.com/forum/thread/1", patterns)
    assert is_blacklisted("/forum/thread/1", patterns)
    assert not is_blacklisted("https://example.com/blog/post", patterns)


def test_is_blacklisted_returns_false_without_patterns() -> None:
    assert not is_blacklisted("https://example.com/forum/thread/1", None)
    assert not is_blacklisted("https://example.com/forum/thread/1", [])
