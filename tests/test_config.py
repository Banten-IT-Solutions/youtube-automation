#!/usr/bin/env python3
"""Unit test untuk core.config."""

import json
import sys

import pytest

sys.path.insert(0, ".")
from core.config import (
    apply_env_overrides,
    load_config,
    validate_config,
)


def _write(tmp_path, data) -> str:
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def _valid():
    return {
        "studio_url": "https://studio.youtube.com/channel/UC_TEST/videos?filter=is_live",
        "schedule_time": "20:00",
        "schedule_offset_days": 7,
        "timezone": "Asia/Jakarta",
        "thumbnail_dir": "thumbnails",
        "profile_dir": "profile",
        "logs_dir": "logs",
        "pause_between_drafts": False,
        "screenshots": True,
        "headless": False,
        "wait_after_action_ms": 700,
    }


def test_validate_ok():
    validate_config(_valid())


def test_missing_required_raises():
    cfg = _valid()
    cfg.pop("schedule_time")
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_int_key_wrong_type():
    cfg = _valid()
    cfg["schedule_offset_days"] = "7"
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_int_key_negative():
    cfg = _valid()
    cfg["wait_after_action_ms"] = -5
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_boolean_wrong_type():
    cfg = _valid()
    cfg["headless"] = "false"
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_bad_schedule_time():
    cfg = _valid()
    cfg["schedule_time"] = "8pm"
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_missing_timezone():
    cfg = _valid()
    cfg.pop("timezone")
    with pytest.raises(SystemExit):
        validate_config(cfg)


def test_load_config_missing_file_raises(tmp_path):
    with pytest.raises(SystemExit):
        load_config(str(tmp_path / "nope.json"))


def test_load_config_bad_json(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{invalid", encoding="utf-8")
    with pytest.raises(SystemExit):
        load_config(str(p))


def test_load_config_ok(tmp_path):
    p = _write(tmp_path, _valid())
    assert load_config(p)["schedule_time"] == "20:00"


def test_env_override_string(monkeypatch):
    cfg = _valid()
    monkeypatch.setenv("YT_STUDIO_URL", "https://example.com/videos")
    monkeypatch.setenv("YT_TIMEZONE", "UTC")
    out = apply_env_overrides(cfg)
    assert out["studio_url"] == "https://example.com/videos"
    assert out["timezone"] == "UTC"


@pytest.mark.parametrize("val,expected", [
    ("1", True), ("true", True), ("yes", True), ("on", True),
    ("0", False), ("false", False), ("no", False), ("off", False),
])
def test_env_override_bool(monkeypatch, val, expected):
    cfg = _valid()
    monkeypatch.setenv("YT_HEADLESS", val)
    assert apply_env_overrides(cfg)["headless"] is expected


def test_env_override_int(monkeypatch):
    cfg = _valid()
    monkeypatch.setenv("YT_SCHEDULE_OFFSET_DAYS", "7")
    assert apply_env_overrides(cfg)["schedule_offset_days"] == 7


def test_env_override_bool_invalid(monkeypatch):
    cfg = _valid()
    monkeypatch.setenv("YT_HEADLESS", "mungkin")
    with pytest.raises(SystemExit):
        apply_env_overrides(cfg)


def test_env_override_int_invalid(monkeypatch):
    cfg = _valid()
    monkeypatch.setenv("YT_SCHEDULE_OFFSET_DAYS", "abc")
    with pytest.raises(SystemExit):
        apply_env_overrides(cfg)


def test_env_override_ignores_unset(monkeypatch):
    cfg = _valid()
    monkeypatch.delenv("YT_HEADLESS", raising=False)
    assert apply_env_overrides(cfg)["headless"] is False
