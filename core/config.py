#!/usr/bin/env python3
"""Konfigurasi aplikasi YouTube Automation."""

from __future__ import annotations

import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_WAIT_AFTER_MS = 700
CARD_POSITION = "00:03:00"

_REQUIRED = ("studio_url", "schedule_time", "schedule_offset_days")
_BOOLEAN_KEYS = ("pause_between_drafts", "screenshots", "headless")
_INT_KEYS = {"schedule_offset_days", "wait_after_action_ms"}
_TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


def load_config() -> dict:
    path = os.path.join(BASE, "config.json")
    if not os.path.exists(path):
        raise SystemExit(
            "config.json tidak ditemukan. Salin dari template:\n"
            f"    cp {os.path.join(BASE, 'config.example.json')} {path}"
        )
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(f"config.json rusak (JSON tidak valid) di baris {e.lineno}: {e.msg}") from e


def validate_config(cfg: dict) -> None:
    missing = [k for k in _REQUIRED if not cfg.get(k)]
    if missing:
        raise SystemExit("config.json salah: key {} wajib diisi".format(", ".join(missing)))

    for key in _INT_KEYS:
        val = cfg.get(key)
        if val is not None and (not isinstance(val, int) or val < 0):
            raise SystemExit(f"config.json salah: '{key}' harus integer >= 0")

    for key in _BOOLEAN_KEYS:
        val = cfg.get(key)
        if val is not None and not isinstance(val, bool):
            raise SystemExit(f"config.json salah: '{key}' harus boolean (true/false)")

    st = cfg.get("schedule_time")
    if not _TIME_RE.match(st or ""):
        raise SystemExit(f"config.json salah: 'schedule_time' harus HH:MM (misal '20:00'), dapat: {st!r}")

    if not cfg.get("timezone"):
        raise SystemExit("config.json salah: 'timezone' wajib diisi (misal 'Asia/Jakarta')")

    for key in ("thumbnail_dir", "profile_dir", "logs_dir"):
        d = cfg.get(key)
        if d:
            os.makedirs(os.path.join(BASE, d), exist_ok=True)