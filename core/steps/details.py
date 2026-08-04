#!/usr/bin/env python3
"""Step: judul & deskripsi, thumbnail, dan pengaturan lanjutan (Details)."""

from __future__ import annotations

import datetime as dt
import os
import re

from playwright.sync_api import TimeoutError as PWTimeout

from ..logger import get_logger
from ..selectors import (
    SEL_AI_NO_NAME,
    SEL_DESC_NAME,
    SEL_NEXT,
    SEL_REC_DATE_BTN,
    SEL_SHOW_MORE,
    SEL_THUMB_INPUT,
    SEL_TITLE_NAME,
)

from ..helpers import _click_schedule_day, find_thumbnail, replace_number, today_str
from ..studio import Studio


def _leading_number(text: str | None) -> int | None:
    m = re.match(r"^\s*(\d{1,4})\b", text or "")
    return int(m.group(1)) if m else None


def edit_title_desc(s: Studio, num: int, prev_num: int) -> None:
     logger = get_logger()
     logger.action("Ubah Judul & Deskripsi", f"{prev_num} → {num}")
     t = s.role_text(SEL_TITLE_NAME, exact=False)
     d = s.role_text(SEL_DESC_NAME, exact=False)
     cur_t = _leading_number(t)
     cur_d = _leading_number(d)
     new_t = replace_number(t, cur_t if cur_t is not None else prev_num, num)
     new_d = replace_number(d, cur_d if cur_d is not None else prev_num, num)
     s.role_fill(SEL_TITLE_NAME, new_t, exact=False)
     s.role_fill(SEL_DESC_NAME, new_d, exact=False)
     logger.result("Judul & Deskripsi Berhasil Diubah", success=True)
     s.shot("02-title-desc")


def upload_thumbnail(s: Studio, num: int, fname: str | None = None) -> None:
    logger = get_logger()
    fp = find_thumbnail(s.cfg, num, fname)
    if not fp:
        logger.warning(f"Thumbnail {num} Tidak Ada")
        return
    logger.action("Upload Thumbnail", os.path.basename(fp))
    try:
        s.page.locator(SEL_THUMB_INPUT).first.set_input_files(fp, timeout=5000)
        s.wait(1500 / 1000.0)
        logger.result("Thumbnail Berhasil Diupload", success=True)
    except Exception as e:
        logger.warning(f"Gagal Upload {e}")
    s.shot("03-thumbnail")


def set_recording_date(s: Studio) -> None:
     logger = get_logger()
     logger.action("Tanggal Perekaman", "Hari Ini")
     btns = s.page.get_by_role("button", name=re.compile(SEL_REC_DATE_BTN))
     target = None
     for i in range(btns.count() - 1, -1, -1):
         try:
             b = btns.nth(i)
             b.wait_for(state="visible", timeout=4000)
             target = b
             break
         except PWTimeout:
             continue
     if target is None:
         logger.warning("Tombol Tanggal Perekaman Tidak Ada")
         return
     target.click()
     s.wait()
     try:
         inp = s.page.locator("ytcp-date-picker input").first
         inp.wait_for(state="visible", timeout=4000)
         inp.fill(dt.date.today().strftime("%d/%m/%Y"))
         inp.press("Enter")
         s.wait()
         try:
             popup = s.page.locator("ytcp-date-picker > tp-yt-paper-dialog").first
             popup.wait_for(state="hidden", timeout=2500)
             logger.result(f"Tanggal Perekaman {today_str()}", success=True)
             return
         except PWTimeout:
             logger.warning("Tanggal Salah")
     except Exception:
         logger.warning(f"Gagal Isi Tanggal")
     day = dt.date.today().day
     if _click_schedule_day(s, day):
         logger.result(f"Tanggal Perekaman Hari {day}", success=True)
         s.wait()
         s.page.keyboard.press("Escape")
         s.wait()
         return
     for label in ["Hari ini", "Today"]:
         try:
             tb = s.page.get_by_role("button", name=label).first
             tb.wait_for(state="visible", timeout=2500)
             tb.click()
             logger.result(f"Tanggal Perekaman {label}", success=True)
             s.wait()
             return
         except PWTimeout:
             continue
     logger.warning("Tanggal Perekaman Gagal")
     s.shot("04-recdate-fail")


def advanced_settings(s: Studio) -> None:
     logger = get_logger()
     logger.action("Pengaturan Lanjutan", "AI Tidak, Tanggal Hari Ini")
     s.click_first(SEL_SHOW_MORE, "Tampilkan setelan lanjutan")
     s.radio_click(SEL_AI_NO_NAME)
     set_recording_date(s)
     s.shot("04-advanced")
     s.role_click(SEL_NEXT)
     logger.result("Pengaturan Lanjutan Selesai", success=True)