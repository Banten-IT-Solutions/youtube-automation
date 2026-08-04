#!/usr/bin/env python3
"""Konfigurasi aplikasi YouTube Automation."""

from __future__ import annotations

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_WAIT_AFTER_MS = 700
CARD_POSITION = "00:03:00"


def load_config() -> dict:
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def validate_config(cfg: dict) -> None:
    missing = [k for k in ("studio_url", "schedule_time", "schedule_offset_days")
               if not cfg.get(k)]
    if missing:
        raise SystemExit("config.json salah: key {} wajib diisi".format(", ".join(missing)))
    for key in ("thumbnail_dir", "profile_dir", "logs_dir"):
        d = cfg.get(key)
        if d:
            os.makedirs(os.path.join(BASE, d), exist_ok=True)
