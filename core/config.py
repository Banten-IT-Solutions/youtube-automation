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


def load_config(path: str | None = None) -> dict:
    path = path or os.path.join(BASE, "config.json")
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


_ENV_MAP = {
    "YT_STUDIO_URL": "studio_url",
    "YT_TIMEZONE": "timezone",
    "YT_SCHEDULE_TIME": "schedule_time",
    "YT_SCHEDULE_OFFSET_DAYS": "schedule_offset_days",
    "YT_WAIT_AFTER_ACTION_MS": "wait_after_action_ms",
    "YT_PAUSE_BETWEEN_DRAFTS": "pause_between_drafts",
    "YT_SCREENSHOTS": "screenshots",
    "YT_HEADLESS": "headless",
    "YT_LOGS_DIR": "logs_dir",
    "YT_THUMBNAIL_DIR": "thumbnail_dir",
    "YT_PROFILE_DIR": "profile_dir",
}
_BOOL_ENV = {"YT_PAUSE_BETWEEN_DRAFTS", "YT_SCREENSHOTS", "YT_HEADLESS"}
_INT_ENV = {"YT_SCHEDULE_OFFSET_DAYS", "YT_WAIT_AFTER_ACTION_MS"}


def apply_env_overrides(cfg: dict) -> dict:
    """Timpa key config dari environment (prefix YT_) tanpa menulis ulang config.json."""
    cfg = dict(cfg)
    for env, key in _ENV_MAP.items():
        value = os.environ.get(env)
        if value is None or value == "":
            continue
        if env in _BOOL_ENV:
            v = value.strip().lower()
            if v in {"1", "true", "yes", "on"}:
                cfg[key] = True
            elif v in {"0", "false", "no", "off"}:
                cfg[key] = False
            else:
                raise SystemExit(f"Environment {env} harus boolean (true/false), dapat: {value!r}")
        elif env in _INT_ENV:
            try:
                cfg[key] = int(value)
            except ValueError:
                raise SystemExit(f"Environment {env} harus integer, dapat: {value!r}") from None
        else:
            cfg[key] = value
    return cfg


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