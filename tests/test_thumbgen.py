#!/usr/bin/env python3
"""Unit test untuk core.thumbgen."""

import os
import sys

import pytest

sys.path.insert(0, ".")
from core.config import BASE
from core.thumbgen import (
    FONT_PATH,
    TEMPLATES,
    TEMPLATE_DIR,
    fallback_stem,
    generate,
    output_pattern,
)


def test_templates_consistent():
    assert len(TEMPLATES) == 5
    for key, cfg in TEMPLATES.items():
        assert (TEMPLATE_DIR / cfg["image"]).exists(), cfg["image"]
        assert len(cfg["slots"]) == 3


def test_fallback_stem():
    stem = fallback_stem("Tafsir Jalalain")
    assert "PENGAJIAN KITAB" in stem and "Tafsir Jalalain" in stem and stem.endswith("-Thumbnail")


def test_output_pattern_with_existing(tmp_path):
    (tmp_path / "001 PENGAJIAN KITAB TAFSIR JALALAIN - ABUYA UCI CILONGOK-Thumbnail.jpg").write_bytes(b"x")
    (tmp_path / "999 .jpg").write_bytes(b"x")
    pat = output_pattern("TAFSIR JALALAIN", tmp_path)
    assert pat == "{num:03d} PENGAJIAN KITAB TAFSIR JALALAIN - ABUYA UCI CILONGOK-Thumbnail.jpg"


def test_output_pattern_fallback(tmp_path):
    pat = output_pattern("TAFSIR JALALAIN", tmp_path)
    assert pat.startswith("{num:03d}")


def test_generate_invalid_range():
    with pytest.raises(ValueError):
        generate("tafsir-jalalain", 10, 5)


def test_generate_unknown_template():
    with pytest.raises(KeyError):
        generate("unknown-tpl", 1, 2)


def test_generate_writes_files(tmp_path):
    if not os.path.exists(FONT_PATH):
        pytest.skip("Font Fira Sans belum terpasang di sistem ini")
    outdir = tmp_path / "out"
    generate("tafsir-jalalain", 501, 502, outdir=outdir)
    files = sorted(p.name for p in outdir.iterdir())
    assert len(files) == 2
    assert files[0].startswith("501")
    assert files[1].startswith("502")


def test_generate_skip_when_exists(tmp_path):
    if not os.path.exists(FONT_PATH):
        pytest.skip("Font Fira Sans belum terpasang di sistem ini")
    outdir = tmp_path / "out"
    generate("tafsir-jalalain", 610, 610, outdir=outdir)
    before = len(list(outdir.iterdir()))
    generate("tafsir-jalalain", 610, 610, outdir=outdir)
    assert len(list(outdir.iterdir())) == before


def test_base_points_at_project_root():
    assert os.path.isdir(os.path.join(BASE, "core"))