"""资产扩展名嗅探的单元测试（threadspider.asset_mirror_pipeline）。"""

from __future__ import annotations

from threadspider.asset_mirror_pipeline import _content_type_of, _is_html, _sniff_extension


class _FakeResp:
    def __init__(self, headers: dict, body: bytes = b""):
        self.headers = headers
        self.body = body


def test_content_type_strips_params_and_case():
    assert _content_type_of(_FakeResp({"Content-Type": "text/css; charset=utf-8"})) == "text/css"
    assert _content_type_of(_FakeResp({"content-type": "IMAGE/PNG"})) == "image/png"
    assert _content_type_of(_FakeResp({})) == ""


def test_content_type_table_maps_common_types():
    assert _sniff_extension(b"", "text/css") == ".css"
    assert _sniff_extension(b"", "image/png") == ".png"
    assert _sniff_extension(b"", "font/woff2") == ".woff2"
    assert _sniff_extension(b"", "video/mp4") == ".mp4"
    assert _sniff_extension(b"", "application/json") == ".json"


def test_magic_bytes_detect_common_formats():
    assert _sniff_extension(b"\x89PNG\r\n\x1a\n\x00\x00") == ".png"
    assert _sniff_extension(b"\xff\xd8\xff\xe0\x00\x10JFIF") == ".jpg"
    assert _sniff_extension(b"GIF89a\x01\x00") == ".gif"
    assert _sniff_extension(b"wOFF\x00\x01\x00\x00") == ".woff"
    assert _sniff_extension(b"wOF2\x00\x01\x00\x00") == ".woff2"
    assert _sniff_extension(b"OTTO\x00\x01") == ".otf"
    assert _sniff_extension(b"%PDF-1.7\n") == ".pdf"
    assert _sniff_extension(b"PK\x03\x04rest") == ".zip"
    assert _sniff_extension(b"\x1f\x8b\x08\x00") == ".gz"
    assert _sniff_extension(b"OggS\x00\x02") == ".ogg"
    assert _sniff_extension(b"ID3\x04\x00") == ".mp3"
    assert _sniff_extension(b"\x1aE\xdf\xa3\x9fB\x86\x81") == ".webm"
    assert _sniff_extension(b"BM\x36\x00") == ".bmp"
    assert _sniff_extension(b"II*\x00\x08\x00") == ".tiff"
    assert _sniff_extension(b"MM\x00*") == ".tiff"
    assert _sniff_extension(b"\x00\x00\x01\x00\x01\x00") == ".ico"


def test_container_formats_use_inner_type():
    # RIFF 容器：第 8-12 字节决定 webp/wav/avi
    assert _sniff_extension(b"RIFF\x24\x00\x00\x00WEBPVP8 ") == ".webp"
    assert _sniff_extension(b"RIFF\x24\x00\x00\x00WAVEfmt ") == ".wav"
    assert _sniff_extension(b"RIFF\x24\x00\x00\x00AVI LIST") == ".avi"
    # ISO-BMFF（mp4 家族）：第 4-8 字节 ftyp
    assert _sniff_extension(b"\x00\x00\x00\x18ftypmp42\x00\x00") == ".mp4"


def test_svg_detected_by_text特征():
    # SVG 无固定魔数，按文本特征识别
    assert _sniff_extension(b'<?xml version="1.0"?><svg xmlns="x"></svg>') == ".svg"
    assert _sniff_extension(b'  <svg viewBox="0 0 1 1"></svg>') == ".svg"
    # 普通 XML（RSS feed 等）按 .xml 落盘，不再兜底成 .bin
    assert _sniff_extension(b'<?xml version="1.0"?><root><item/></root>') == ".xml"
    assert _sniff_extension(b'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"></rss>') == ".xml"
    assert _sniff_extension(b"<feed xmlns=\"http://www.w3.org/2005/Atom\"></feed>") == ".xml"


def test_unknown_bytes_return_none():
    assert _sniff_extension(b"just some random text without structure") is None
    assert _sniff_extension(b"") is None


def test_html_detected_by_content_type_and_sniff():
    # Content-Type 直接声明
    assert _sniff_extension(b"", "text/html") == ".html"
    assert _sniff_extension(b"", "application/xhtml+xml") == ".html"
    # 无/错误 Content-Type 时按文本特征嗅探
    assert _sniff_extension(b"<!DOCTYPE html><html><head></head></html>") == ".html"
    assert _sniff_extension(b'\n<html lang="zh"><body>hi</body></html>') == ".html"
    # SVG 判定优先于 HTML（内联 svg 的 XHTML 不误判……但纯 SVG 必须是 .svg）
    assert _sniff_extension(b'<?xml version="1.0"?><svg xmlns="x"></svg>') == ".svg"


def test_is_html_routing():
    # 声明为 HTML 的响应 → 按页面处理，不落资源扩展名
    assert _is_html(_FakeResp({"content-type": "text/html; charset=utf-8"})) is True
    assert _is_html(_FakeResp({}, b"<!DOCTYPE html><html></html>")) is True
    # 普通资源 → 走资产路径
    assert _is_html(_FakeResp({"content-type": "image/png"})) is False
    assert _is_html(_FakeResp({}, b"\x89PNG\r\n\x1a\n\x00\x00")) is False
    assert _is_html(_FakeResp({})) is False


def test_magic_wins_over_generic_content_type():
    # 服务器误报 application/octet-stream 时靠魔数纠正
    assert _sniff_extension(b"\x89PNG\r\n\x1a\n\x00\x00", "application/octet-stream") == ".png"
