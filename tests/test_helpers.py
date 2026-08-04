#!/usr/bin/env python3
"""Unit test untuk core.helpers (fungsi murni tanpa browser)."""

import sys

sys.path.insert(0, ".")
from core.helpers import (
    find_playlist,
    find_thumbnail,
    parse_studio_date,
    replace_number,
    scheduled_url,
    today_str,
)


def test_today_str_format():
    s = today_str()
    parts = s.split("/")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_parse_studio_date_valid():
    assert parse_studio_date("12 Agu 2026") == __import__("datetime").date(2026, 8, 12)


def test_parse_studio_date_unknown_month():
    assert parse_studio_date("12 FOO 2026") is None


def test_parse_studio_date_garbage():
    assert parse_studio_date("N/A") is None
    assert parse_studio_date(None) is None


def test_parse_studio_date_invalid_day():
    assert parse_studio_date("32 Des 2026") is None


def test_replace_number():
    assert replace_number("PENGAJIAN KITAB 12 - Judul", 12, 13) == "PENGAJIAN KITAB 13 - Judul"
    assert replace_number("Judul tanpa angka", 5, 6) == "Judul tanpa angka"


def test_replace_number_ignores_digit_inside_word():
    assert replace_number("KITAB 012 - Judul", 12, 13) == "KITAB 012 - Judul"


def test_find_thumbnail_by_prefix_and_series(tmp_path):
    (tmp_path / "413 catatan.txt").write_bytes(b"x")
    (tmp_path / "413 PENGAJIAN KITAB MINHAJUT THOLIBIN - ABUYA UCI CILONGOK.jpg").write_bytes(b"x")
    cfg = {"thumbnail_dir": str(tmp_path)}
    hit = find_thumbnail(cfg, 413, "413 Pengajian.mp4")
    assert hit and "MINHAJUT" in hit


def test_find_thumbnail_fallback_glob(tmp_path):
    (tmp_path / "414 abc.jpg").write_bytes(b"x")
    cfg = {"thumbnail_dir": str(tmp_path)}
    assert find_thumbnail(cfg, 414) == str(tmp_path / "414 abc.jpg")


def test_find_thumbnail_missing_dir():
    assert find_thumbnail({"thumbnail_dir": "/no/such/dir"}, 1) is None


def test_find_playlist():
    cfg = {"playlist_keywords": {"Tafsir Jalalain": ["tafsir jalalain"], "Sirrul Asror": ["sirrul asror"]}}
    assert find_playlist(cfg, "PENGAJIAN KITAB TAFSIR JALALAIN - EP 1") == "Tafsir Jalalain"
    assert find_playlist(cfg, "Judul bebas") is None


def test_scheduled_url_contains_filters():
    url = scheduled_url({"studio_url": "https://studio.youtube.com/channel/UCX/videos"}, series="Tafsir Jalalain")
    assert "HAS_SCHEDULE" in url
    assert "Tafsir" in url
    assert "/upload?" in url
