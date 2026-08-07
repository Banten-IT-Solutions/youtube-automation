#!/usr/bin/env python3
"""Fungsi bantu: tanggal, URL, thumbnail, playlist, dan baca info draft."""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import time
import urllib.parse

from playwright.sync_api import TimeoutError as PWTimeout

from .logger import get_logger
from .selectors import SEL_ROW, SEL_TITLE_LINK

from .studio import Studio


def today_str(fmt: str = "%d/%m/%Y") -> str:
    return dt.date.today().strftime(fmt)


def wait_network_idle(page, timeout: int = 15000) -> None:
    """Tunggu hingga lalu lintas jaringan mereda (halaman dianggap terload).

    Jaringan IDLE berarti tidak ada permintaan yang tertunda dalam 500ms,
    indikator kuat bahwa konten halaman/daftar sudah selesai dimuat.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except PWTimeout:
        pass


def wait_rows_changed(page, prev_title: str | None, timeout: int = 20000) -> bool:
    """Pastikan daftar baris berubah dari sebelumnya (halaman berikutnya terload).

    Berguna untuk pagination SPA yang memuat konten via AJAX: daripada menunggu
    dengan delay tetap, kita menunggu sampai judul baris pertama benar-benar
    berganti dari konten lama — bukti bahwa data halaman baru sudah dirender.
    """
    rows = page.locator(SEL_ROW)
    try:
        rows.first.wait_for(state="attached", timeout=timeout)
    except PWTimeout:
        return False
    deadline = time.monotonic() + timeout / 1000.0
    while time.monotonic() < deadline:
        try:
            title = rows.first.locator(SEL_TITLE_LINK).inner_text(timeout=2000).strip()
        except PWTimeout:
            continue
        if prev_title is None or (title and title != prev_title):
            return True
        page.wait_for_timeout(200)
    return False


def read_file_info(s: Studio) -> tuple[int | None, str | None]:
    panel = s.page.locator("ytcp-video-info")
    try:
        panel.first.wait_for(state="visible", timeout=10000)
    except PWTimeout:
        return None, None
    for v in panel.locator(".value").all():
        txt = (v.inner_text() or "").strip()
        m = re.match(r"^(\d{1,4})\s", txt)
        if m:
            return int(m.group(1)), txt
    return None, None


MONTH_ID = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "Mei": 5, "Jun": 6,
    "Jul": 7, "Agu": 8, "Sep": 9, "Okt": 10, "Nov": 11, "Des": 12,
}


def scheduled_url(cfg: dict, series: str | None = None) -> str:
    m = re.match(r"(.+?/videos)(?:/upload)?\?", cfg["studio_url"])
    base = (m.group(1) + "/upload?" if m else cfg["studio_url"].split("?")[0] + "/upload?")
    filters = [{"name": "VISIBILITY", "value": ["HAS_SCHEDULE"]}]
    if series:
        filters.append({"name": "TITLE", "value": {"name": "CONTAINS", "value": series}})
    sort = {"columnType": "date", "sortOrder": "DESCENDING"}
    return base + (
        "filter=" + urllib.parse.quote(json.dumps(filters, separators=(",", ":")), safe="")
        + "&sort=" + urllib.parse.quote(json.dumps(sort, separators=(",", ":")), safe="")
    )


def parse_studio_date(txt: str | None) -> dt.date | None:
    m = re.search(r"(\d{1,2})\s+(\w{3})\s+(\d{4})", txt or "")
    if not m:
        return None
    mon = MONTH_ID.get(m.group(2).capitalize())
    if not mon:
        return None
    try:
        return dt.date(int(m.group(3)), mon, int(m.group(1)))
    except ValueError:
        return None


def find_prev_schedule_date(s: Studio, prev_num: int, prev_fname: str | None) -> dt.date | None:
     logger = get_logger()
     page = s.page
     target = (prev_fname or "").replace(".mp4", "").strip()
     series = re.sub(r"^\d+\s+", "", target).strip()
     logger.action("Cari Tanggal Video", f"prev={prev_num}")
     spage = s.ctx.new_page()
     try:
         spage.goto(scheduled_url(s.cfg, series=series))
         wait_network_idle(spage)
         for _ in range(10):
             rows = spage.locator(SEL_ROW)
             try:
                 rows.first.wait_for(state="attached", timeout=30000)
             except PWTimeout:
                 return None
             for i in range(rows.count()):
                 try:
                     title = rows.nth(i).locator(SEL_TITLE_LINK).inner_text(timeout=2000).strip()
                 except PWTimeout:
                     continue
                 if title and title == target:
                     try:
                         dcell = rows.nth(i).locator(".tablecell-date").first
                         d = parse_studio_date(dcell.inner_text(timeout=3000))
                         logger.result(f"Tanggal Ditemukan {d}", success=True)
                         return d
                     except PWTimeout:
                         return None
             nxt = spage.get_by_role("button", name="Buka halaman berikutnya").first
             try:
                 nxt.wait_for(state="visible", timeout=3000)
                 rows = spage.locator(SEL_ROW)
                 try:
                     prev_title = rows.first.locator(SEL_TITLE_LINK).inner_text(timeout=2000).strip()
                 except PWTimeout:
                     prev_title = None
                 nxt.click()
                 wait_network_idle(spage)
                 if not wait_rows_changed(spage, prev_title):
                     break
             except PWTimeout:
                 break
         logger.warning(f"Video Sebelumnya {prev_num} Tidak Ditemukan")
         return None
     finally:
         spage.close()


def replace_number(text: str | None, old: int, new: int) -> str:
    return re.sub(r"(?<!\d){}(?!\d)".format(old), str(new), text or "")


def find_thumbnail(cfg: dict, num: int, fname: str | None = None) -> str | None:
     d = cfg["thumbnail_dir"]
     if not os.path.isdir(d):
         return None

     if fname:
         fname_base = (fname or "").replace(".mp4", "").strip()
         series = re.sub(r"^\d+\s+", "", fname_base).strip()

         if series:
             for f in os.listdir(d):
                 if f.lower().startswith(str(num)) and series.lower() in f.lower():
                     return os.path.join(d, f)

     for pat in ["{}[ _-]*.*".format(num), "{}*.*".format(num)]:
         hits = sorted(glob.glob(os.path.join(d, pat)))
         if hits:
             return hits[0]
     return None


def find_playlist(cfg: dict, title: str | None) -> str | None:
    t = (title or "").lower()
    kmap = cfg.get("playlist_keywords") or {}
    for pl, keys in kmap.items():
        for k in keys:
            if k.lower() in t:
                return pl
    return None


def _click_schedule_day(s: Studio, day: int) -> bool:
    dialog = None
    for sel in ["ytcp-date-picker:visible", "ytcp-date-range-picker:visible",
                "ytcp-dialog[role='dialog']:visible", "[role='dialog']:visible",
                ".picker-content", "ytcp-dialog"]:
        d = s.page.locator(sel).first
        try:
            if d.count() > 0:
                d.wait_for(state="visible", timeout=2000)
                dialog = d
                break
        except PWTimeout:
            continue
    scope = dialog if dialog is not None else s.page
    locs = scope.get_by_text(str(day), exact=True)
    candidates = []
    for i in range(locs.count()):
        try:
            loc = locs.nth(i)
            loc.wait_for(state="visible", timeout=1500)
            html = loc.evaluate(
                "(el) => { let n = el; while (n && n.nodeType === 1) {"
                " const c = n.getAttribute && (n.getAttribute('class') || '');"
                " if (c && /(mute|outside|faded|disabled)/i.test(c)) return 'SKIP';"
                " n = n.parentElement; } return el.outerHTML; }"
            )
        except PWTimeout:
            continue
        except Exception:
            candidates.append(loc)
            continue
        if html == "SKIP":
            continue
        candidates.append(loc)
    if not candidates:
        return False
    candidates[-1].click()
    return True