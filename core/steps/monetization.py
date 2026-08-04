#!/usr/bin/env python3
"""Step: monetisasi & rating iklan."""

from __future__ import annotations

import re

from playwright.sync_api import TimeoutError as PWTimeout

from ..logger import get_logger
from ..selectors import (
    SEL_M10N,
    SEL_M10N_AKTIF,
    SEL_M10N_SELESAI,
    SEL_NEXT,
    SEL_RATING_NONE,
    SEL_RATING_SUBMIT,
)

from ..studio import Studio


def _rating_locked(s: Studio) -> bool:
    try:
        q = s.page.locator("ytpp-self-certification-questionnaire")
        if q.count() == 0:
            return False
        if q.first.get_attribute("disabled") is not None:
            return True
        if q.get_by_text(re.compile(r"dikunci karena Anda telah mengirimkan rating", re.I)).count():
            return True
    except Exception:
        pass
    return False


def monetization(s: Studio) -> None:
     logger = get_logger()
     logger.action("Monetisasi", "Aktif + Rating")
     loc = s.page.locator(SEL_M10N).first
     loc.wait_for(state="visible", timeout=6000)
     loc.click()
     logger.step("Klik Dropdown Monetisasi", indent=2)
     s.wait()
     akt = s.page.get_by_role("radio", name=SEL_M10N_AKTIF, exact=True).first
     akt.wait_for(state="visible", timeout=6000)
     if not akt.is_checked():
         akt.click()
         logger.result("Monetisasi Aktif", success=True)
         s.wait()
         try:
             s.role_click(SEL_M10N_SELESAI)
         except PWTimeout:
             logger.warning("Tombol Selesai Tidak Muncul")
             s.page.keyboard.press("Escape")
             s.wait()
     else:
         logger.info("Monetisasi Sudah Aktif")
         s.page.keyboard.press("Escape")
         s.wait()
     try:
         akt.wait_for(state="hidden", timeout=5000)
     except PWTimeout:
         s.page.keyboard.press("Escape")
         s.wait()
     s.role_click(SEL_NEXT)
     s.wait(2000 / 1000.0)
     if _rating_locked(s):
         logger.info("Rating Sudah Dikirim")
         s.role_click(SEL_NEXT)
         s.shot("05-monetization")
         return
     logger.action("Rating", "Atur Rating Iklan")
     s.text_click(SEL_RATING_NONE)
     try:
         s.role_click(SEL_RATING_SUBMIT)
     except Exception:
         logger.warning("Kirim Rating Gagal")
         sub = s.page.get_by_role("button", name=SEL_RATING_SUBMIT, exact=True).first
         sub.wait_for(state="visible", timeout=6000)
         sub.click(force=True)
         s.wait()
     logger.result("Rating Dikirim", success=True)
     s.role_click(SEL_NEXT)
     s.shot("05-monetization")