#!/usr/bin/env python3
"""Step: elemen video (end screen & kartu playlist)."""

from __future__ import annotations

import re

from playwright.sync_api import TimeoutError as PWTimeout

from ..logger import get_logger
from ..selectors import (
    SEL_CARDS_BUTTON,
    SEL_CARD_ENTITY,
    SEL_CARD_SEARCH,
    SEL_REUSE_OPTION,
    SEL_SAVE,
)

from ..config import CARD_POSITION
from ..studio import Studio


def import_end_screen(s: Studio) -> None:
     logger = get_logger()
     imp_btn = s.page.locator("#import-from-video-button").first
     try:
         imp_btn.wait_for(state="visible", timeout=10000)
         s.page.evaluate("() => document.querySelector('#import-from-video-button').click()")
         s.wait(1500 / 1000.0)
         item = s.page.locator(SEL_REUSE_OPTION).first
         item.wait_for(state="visible", timeout=6000)
         item.click()
         logger.result("Video Terbaru Dipilih", success=True)
         s.wait()
         s.role_click(SEL_SAVE)
         s.wait(2500 / 1000.0)
     except PWTimeout:
         logger.info("End Screen Tersedia")


def open_cards_panel(s: Studio) -> None:
     logger = get_logger()
     try:
         cb = s.page.locator(SEL_CARDS_BUTTON).first
         cb.wait_for(state="visible", timeout=8000)
         s.page.evaluate("() => document.querySelector('#cards-button').click()")
         s.wait(2000 / 1000.0)
         logger.step("Buka Panel Kartu", indent=2)
     except Exception:
         logger.warning("Gagal Buka Panel Kartu")
         try:
             cb = s.page.locator(SEL_CARDS_BUTTON).first
             cb.click(force=True)
             s.wait(2000 / 1000.0)
         except Exception:
             pass


def _card_exists(s: Studio) -> bool:
     try:
         cards_btn = s.page.locator("#cards-button").first
         cards_btn.wait_for(state="visible", timeout=5000)
         btn_text = cards_btn.inner_text().strip()
         return btn_text.lower() == "edit"
     except Exception:
         return False


def pick_playlist(s: Studio, playlist: str, cfg: dict) -> None:
     logger = get_logger()
     cands = [playlist]
     for kw in cfg.get("playlist_keywords", {}).get(playlist, []) if cfg else []:
         if kw not in cands:
             cands.append(kw)
     norm = re.sub(r"(.)\1", r"\1", playlist.lower())
     if norm not in cands:
         cands.append(norm)

     def try_pick():
         for cand in cands:
             loc = s.page.locator(SEL_CARD_ENTITY).filter(has_text=cand).first
             try:
                 loc.wait_for(state="visible", timeout=3000)
                 loc.click(force=True)
                 s.wait()
                 logger.result(f"Playlist Dipilih {cand}", success=True)
                 return True
             except PWTimeout:
                 continue
         return False

     picked = try_pick()
     for term in cands:
         if picked:
             break
         for sel in SEL_CARD_SEARCH:
             box = s.page.locator(sel).first
             try:
                 box.wait_for(state="visible", timeout=4000)
                 box.fill(term)
                 s.wait(1500 / 1000.0)
                 logger.step(f"Cari Playlist {term}", indent=2)
                 break
             except PWTimeout:
                 continue
         picked = try_pick()
     if not picked:
         try:
             s.page.locator(SEL_CARD_ENTITY).nth(2).wait_for(state="visible", timeout=4000)
             s.page.locator(SEL_CARD_ENTITY).nth(2).click(force=True)
             logger.result("Gunakan Kartu Ke-3", success=True)
             s.wait()
         except PWTimeout:
             logger.warning("Playlist Tidak Ditemukan")


def set_card_time(s: Studio) -> None:
     logger = get_logger()
     logger.step(f"Set Posisi Kartu {CARD_POSITION}", indent=2)
     try:
         time_inputs = s.page.locator("input[type='text'][aria-label*='menit']")
         if time_inputs.count() == 0:
             time_inputs = s.page.locator("input[type='text']").filter(has_text="")
         if time_inputs.count() > 0:
             time_input = time_inputs.first
             time_input.wait_for(state="visible", timeout=3000)
             time_input.click()
             s.wait(300 / 1000.0)
             time_input.fill(CARD_POSITION)
             s.wait(500 / 1000.0)
             logger.result(f"Posisi Kartu {CARD_POSITION}", success=True)
         else:
             logger.warning("Input Posisi Kartu Tidak Ada")
     except Exception:
         logger.warning("Gagal Set Posisi Kartu")


def video_elements(s: Studio, playlist: str | None, cfg: dict) -> None:
     logger = get_logger()
     logger.action("Atur Elemen Video", "End Screen & Kartu")
     import_end_screen(s)

     logger.action("Kartu", f"Playlist : {playlist or '(tidak cocok)'}")
     
     if _card_exists(s):
         logger.info("Kartu Sudah Ada")
         s.shot("06-video-elements")
         return

     logger.info("Belum Ada Kartu - Tambahkan Baru")
     open_cards_panel(s)
     s.wait(2000 / 1000.0)

     ok = s.page.evaluate(
         """() => { const el = document.querySelector(
         '[aria-label="Tambahkan kartu info yang ditautkan ke playlist"]');
         if (!el) return false; el.click(); return true; }""")
     if ok:
         logger.step("Pilih Tipe Kartu Playlist", indent=2)
         s.wait(2000 / 1000.0)
     else:
         logger.warning("Opsi Playlist Tidak Ada")

     if playlist:
         pick_playlist(s, playlist, cfg)

     set_card_time(s)
     s.role_click(SEL_SAVE)
     logger.result("Elemen Video Disimpan", success=True)
     s.shot("06-video-elements")