#!/usr/bin/env python3
"""Step: buka editor dan salin detail dari video sebelumnya."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, TimeoutError as PWTimeout

from ..logger import get_logger
from ..selectors import (
    SEL_EDIT_BTN,
    SEL_EDIT_DRAFT_BTN,
    SEL_REUSE_BTN,
    SEL_REUSE_OPTION,
)

from ..studio import StepError, Studio


def open_editor(s: Studio, row: Locator) -> None:
     logger = get_logger()
     logger.action("Buka Editor", "Tombol Ubah Draft")
     for sel in SEL_EDIT_DRAFT_BTN:
         try:
             loc = row.locator(sel).first
             loc.wait_for(state="visible", timeout=5000)
             loc.click()
             s.wait(1500 / 1000.0)
             logger.result(f"Draft")
             break
         except Exception:
             continue
     else:
         s.click_first(SEL_EDIT_BTN, "Detail")
     s.shot("00-editor")


def _find_card_by_text(s: Studio, cards: Locator, target_normalized: str) -> tuple[Locator | None, str | None]:
     for i in range(cards.count()):
         try:
             t = cards.nth(i).inner_text(timeout=1500).strip()
             t_normalized = re.sub(r'\s+', ' ', t.lower())
             if t_normalized == target_normalized or target_normalized in t_normalized:
                 return cards.nth(i), t
         except PWTimeout:
             continue
     return None, None


def _search_reuse_dialog(s: Studio, target: str) -> tuple[Locator | None, str | None]:
     logger = get_logger()
     logger.step("Cari di search box", indent=2)
     search_input = None
     for sel in ["input#search-yours", "ytcp-video-pick-dialog input[placeholder*='Telusuri']", "ytcp-video-pick-dialog input"]:
         try:
             inp = s.page.locator(sel).first
             inp.wait_for(state="visible", timeout=2000)
             search_input = inp
             logger.step(f"Search input found: {sel}", indent=3)
             break
         except Exception:
             continue

     if not search_input:
         return None, None

     try:
         search_input.click(force=True)
         s.wait(200 / 1000.0)
         search_input.click(force=True)
         s.wait(200 / 1000.0)
         search_input.fill("")
         s.wait(200 / 1000.0)
         search_input.type(target, delay=30)
         s.wait(500 / 1000.0)
         search_input.press("Enter")
         s.wait(500 / 1000.0)
         logger.step(f"Search: {target[:50]}...", indent=3)
         s.wait(3000 / 1000.0)
         return _find_card_by_text(s, s.page.locator(SEL_REUSE_OPTION),
                                   re.sub(r'\s+', ' ', target.lower()))
     except Exception as e:
         logger.warning(f"Gagal search di dialog: {e}")
         return None, None


def _confirm_reuse(s: Studio, picked: Locator, picked_txt: str | None) -> None:
     logger = get_logger()
     picked.wait_for(state="visible", timeout=8000)
     txt = (picked_txt or "").strip()[:80]
     picked.click()
     logger.result(f"Video {txt}", success=True)
     s.wait(3000 / 1000.0)
     btn = s.page.locator(
         "ytcp-uploads-reuse-details-selection-dialog button[aria-label='Gunakan kembali']"
     ).first
     btn.wait_for(state="visible", timeout=15000)
     for _ in range(60):
         if btn.get_attribute("aria-disabled") != "true":
             break
         s.wait(0.5)
     btn.click(force=True)
     logger.result("Detail Disalin", success=True)
     s.shot("01-after-reuse")
     s.wait(2000 / 1000.0)


def reuse_details(s: Studio, prev_fname: str) -> None:
     logger = get_logger()
     logger.action("Gunakan Detail Video Lama", "dari Video Sebelumnya")
     s.click_first(SEL_REUSE_BTN, "Salin detail video")
     target = (prev_fname or "").replace(".mp4", "").strip()
     target_normalized = re.sub(r'\s+', ' ', target.lower())

     picked, picked_txt = _find_card_by_text(
         s, s.page.locator(SEL_REUSE_OPTION), target_normalized)

     if picked is None:
         picked, picked_txt = _search_reuse_dialog(s, target)

     if picked is None:
         logger.error(f"Video Sebelumnya '{target}' Tidak Ditemukan di Dialog Reuse")
         available = []
         for i in range(min(3, s.page.locator(SEL_REUSE_OPTION).count())):
             try:
                 available.append(s.page.locator(SEL_REUSE_OPTION).nth(i).inner_text(timeout=1000).strip()[:60])
             except Exception:
                 pass
         if available:
             logger.info(f"Video yang tersedia: {', '.join(available)}")
         raise StepError(f"Reuse: Video '{target}' tidak ada")

     _confirm_reuse(s, picked, picked_txt)