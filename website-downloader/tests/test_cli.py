from __future__ import annotations

import pytest

from website_downloader.cli import (
    load_cookies,
    load_exclude_patterns,
    load_headers,
    load_start_urls,
    parse_args,
    parse_cookie_header,
    parse_header,
    validate_args,
)


def test_parse_cookie_header_accepts_header_syntax() -> None:
    assert parse_cookie_header("session=abc; csrftoken=xyz") == {
        "session": "abc",
        "csrftoken": "xyz",
    }


def test_parse_cookie_header_rejects_invalid_entries() -> None:
    with pytest.raises(ValueError):
        parse_cookie_header("session")


def test_load_cookies_merges_files_and_cli(tmp_path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("filecookie=yes", encoding="utf-8")
    assert load_cookies(["session=abc"], [str(cookie_file)]) == {
        "session": "abc",
        "filecookie": "yes",
    }


def test_validate_args_rejects_invalid_limits() -> None:
    args = parse_args(["--url", "https://example.com", "--threads", "0"])
    with pytest.raises(ValueError):
        validate_args(args)


def test_validate_args_rejects_invalid_page_threads() -> None:
    args = parse_args(["--url", "https://example.com", "--page-threads", "0"])
    with pytest.raises(ValueError):
        validate_args(args)


def test_parse_header_accepts_authorization_header() -> None:
    assert parse_header("Authorization: Bearer token") == ("Authorization", "Bearer token")


def test_load_headers_uses_last_repeated_header() -> None:
    assert load_headers(["X-Test: one", "X-Test: two"]) == {"X-Test": "two"}


def test_headless_alias_enables_flag() -> None:
    args = parse_args(["--url", "https://example.com", "--headless"])
    assert args.headless is True


def test_parse_args_collects_repeated_exclude_patterns() -> None:
    args = parse_args(
        ["--url", "https://example.com", "--exclude", "*/forum/*", "--exclude", "*/drafts/*"]
    )
    assert args.exclude == ["*/forum/*", "*/drafts/*"]


def test_load_exclude_patterns_merges_files_and_cli(tmp_path) -> None:
    pattern_file = tmp_path / "exclude.txt"
    pattern_file.write_text("# comment\n*/forum/*\n\n*/drafts/*\n", encoding="utf-8")
    assert load_exclude_patterns(["*/admin/*"], [str(pattern_file)]) == [
        "*/admin/*",
        "*/forum/*",
        "*/drafts/*",
    ]


def test_parse_args_collects_repeated_urls() -> None:
    args = parse_args(["--url", "https://example.com/a", "--url", "https://example.com/b"])
    assert args.url == ["https://example.com/a", "https://example.com/b"]


def test_load_start_urls_merges_file_and_dedupes(tmp_path) -> None:
    url_file = tmp_path / "urls.txt"
    url_file.write_text(
        "# comment\nhttps://example.com/a\n\nhttps://example.com/c\n",
        encoding="utf-8",
    )
    result = load_start_urls(["https://example.com/a", "https://example.com/b"], str(url_file))
    assert result == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]


def test_load_start_urls_raises_without_any_url() -> None:
    with pytest.raises(ValueError):
        load_start_urls([], None)


def test_validate_args_rejects_negative_max_depth() -> None:
    args = parse_args(["--url", "https://example.com", "--max-depth", "-1"])
    with pytest.raises(ValueError):
        validate_args(args)


def test_validate_args_accepts_zero_max_depth() -> None:
    args = parse_args(["--url", "https://example.com", "--max-depth", "0"])
    validate_args(args)
