#!/usr/bin/env python3
"""Orkestrasi proses satu draft."""

from __future__ import annotations

import datetime as dt

from .logger import get_logger

from .helpers import find_playlist, find_thumbnail
from .schedule import schedule
from .steps.details import advanced_settings, edit_title_desc, upload_thumbnail
from .steps.elements import video_elements
from .steps.monetization import monetization
from .steps.reuse import reuse_details
from .studio import Studio


def process_draft(s: Studio, num: int, prev_fname: str | None, sch: dt.date, cfg: dict) -> None:
      logger = get_logger()
      prev_num = num - 1
      sch_str = sch.strftime(cfg["date_format"])
      playlist = find_playlist(cfg, prev_fname or "")
      thumbnail = find_thumbnail(cfg, num, prev_fname)

      logger.start_draft(num)
      logger.separator()
      logger.action("Konfigurasi Draft", f"Video {prev_num}, Playlist : {playlist or '-'}")
      logger.step(f"Jadwal : {sch_str} {cfg['schedule_time']}", indent=2)
      logger.step(f"Thumbnail : {thumbnail or '(tidak ditemukan)'}", indent=2)
      logger.separator()

      reuse_details(s, prev_fname)
      edit_title_desc(s, num, prev_num)
      upload_thumbnail(s, num, prev_fname)
      advanced_settings(s)
      monetization(s)
      video_elements(s, playlist, cfg)
      schedule(s, sch, cfg["schedule_time"])

      logger.end_draft(num, success=True)