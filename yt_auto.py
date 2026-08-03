#!/usr/bin/env python3

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
import time
import urllib.parse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from logger import init_logger, get_logger

BASE = os.path.dirname(os.path.abspath(__file__))

_logger = None

def LOG(*args):
    if _logger:
        message = " ".join(str(a) for a in args)
        _logger.debug(message)
    else:
        print("[{}]".format(time.strftime("%H:%M:%S")), *args, flush=True)

SEL_ROW = "ytcp-video-row"
SEL_TITLE_LINK = "a#video-title"
SEL_EDIT_BTN = ["ytcp-button[aria-label='Detail']", "button[aria-label='Detail']", "ytcp-button:has-text('Detail')"]
SEL_EDIT_DRAFT_BTN = ["button[aria-label='Edit draf']", "ytcp-button[aria-label='Edit draf']", "button:has-text('Edit draf')"]

SEL_REUSE_BTN = ["ytcp-button:has-text('Gunakan kembali detail')", "button:has-text('Gunakan kembali detail')"]
SEL_REUSE_OPTION = "ytcp-entity-card"

SEL_TITLE_NAME = "Tambahkan judul yang menjelaskan video Anda (ketik @ untuk menyebutkan channel)"
SEL_DESC_NAME = "Beri tahu penonton tentang video Anda (ketik @ untuk menyebutkan channel)"

SEL_THUMB_INPUT = "input#file-loader"

SEL_SHOW_MORE = ["ytcp-button:has-text('Tampilkan lebih banyak')", "button:has-text('Tampilkan lebih banyak')", "ytcp-button:has-text('Tampilkan setelan lanjutan')", "button:has-text('Tampilkan setelan lanjutan')"]
SEL_AI_NO_NAME = "Tidak, AI tidak digunakan"
SEL_REC_DATE_BTN = "Tanggal perekaman"

SEL_NEXT = "Berikutnya"
SEL_M10N = ".m10n-text"
SEL_M10N_AKTIF = "Aktif"
SEL_M10N_SELESAI = "Selesai"
SEL_RATING_NONE = "Tidak satu pun di atas"
SEL_RATING_SUBMIT = "Kirim rating"

SEL_ENDSCREEN_IMPORT = "Impor dari video"
SEL_SAVE = "Simpan"

SEL_CARDS_BUTTON = "#cards-button"
SEL_CARD_ADD = "Tambahkan"
SEL_CARD_TYPE_OPTIONS = ".style-scope.ytve-info-cards-editor-options-panel > div"
SEL_CARD_ENTITY = "ytcp-entity-card"
SEL_CARD_SEARCH = [
    "ytcp-playlist-picker input[type='text']",
    "ytcp-playlist-picker input",
    "ytcp-dialog input[type='text']",
]

SEL_VIS_PUBLIC_RADIO = "Dari khusus pelanggan ke"
SEL_SCHED_TIME = ["input[placeholder*='hh:mm']", "input[aria-label*='Waktu']", "#input-3"]
SEL_SCHEDULE_BTN = ["ytcp-button#schedule-button", "ytcp-button:has-text('Jadwalkan')"]
SEL_CLOSE = ["ytcp-button:has-text('Tutup')", "button:has-text('Tutup')"]


def load_config():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def today_str(fmt="%d/%m/%Y"):
    return dt.date.today().strftime(fmt)


def read_file_info(s):
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


def scheduled_url(cfg, series=None):
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


def parse_studio_date(txt):
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


def find_prev_schedule_date(s, prev_num, prev_fname):
     logger = get_logger()
     page = s.page
     target = (prev_fname or "").replace(".mp4", "").strip()
     series = re.sub(r"^\d+\s+", "", target).strip()
     logger.action("Cari Tanggal Video", f"prev={prev_num}")
     spage = s.ctx.new_page()
     try:
         spage.goto(scheduled_url(s.cfg, series=series))
         spage.wait_for_timeout(5000)
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
                 nxt.click()
                 spage.wait_for_timeout(4000)
             except PWTimeout:
                 break
         logger.warning(f"Video Sebelumnya {prev_num} Tidak Ditemukan")
         return None
     finally:
         spage.close()


def replace_number(text, old, new):
    return re.sub(r"(?<!\d){}(?!\d)".format(old), str(new), text or "")


def find_thumbnail(cfg, num, fname=None):
     d = cfg["thumbnail_dir"]
     if not os.path.isdir(d):
         return None
     
     # Jika fname tersedia, ekstrak series name dan cari thumbnail dengan series + num baru
     if fname:
         fname_base = (fname or "").replace(".mp4", "").strip()
         # Ekstrak series name (hapus nomor di depan)
         # "100 PENGAJIAN KITAB SIRRUL ASROR..." → "PENGAJIAN KITAB SIRRUL ASROR..."
         series = re.sub(r"^\d+\s+", "", fname_base).strip()
         
         if series:
             # Cari file dengan num dan series name (case-insensitive)
             for f in os.listdir(d):
                 if f.lower().startswith(str(num)) and series.lower() in f.lower():
                     return os.path.join(d, f)
     
     # Fallback: cari berdasarkan number saja
     for pat in ["{}[ _-]*.*".format(num), "{}*.*".format(num)]:
         hits = sorted(glob.glob(os.path.join(d, pat)))
         if hits:
             return hits[0]
     return None


def find_playlist(cfg, title):
    t = (title or "").lower()
    kmap = cfg.get("playlist_keywords")
    if kmap:
        for pl, keys in kmap.items():
            for k in keys:
                if k.lower() in t:
                    return pl
        return None
    for pl in cfg.get("playlists", []):
        if pl and pl.lower() in t:
            return pl
    return None


class StepError(Exception):
    pass


class Studio:
    def __init__(self, page, ctx, cfg):
        self.page = page
        self.ctx = ctx
        self.cfg = cfg
        self.shots = os.path.join(cfg.get("logs_dir", "logs"), "shots")
        self.wa = cfg.get("wait_after_action_ms", 700) / 1000.0

    def wait(self, t=None):
        self.page.wait_for_timeout(int((t if t is not None else self.wa) * 1000))

    def shot(self, name, force=False):
        if not force and not self.cfg.get("screenshots", False):
            return
        try:
            os.makedirs(self.shots, exist_ok=True)
            self.page.screenshot(path=os.path.join(self.shots, name + ".png"))
        except Exception:
            pass

    def click_first(self, selectors, name, timeout=12000):
        errs = []
        for sel in selectors:
            loc = self.page.locator(sel).first
            try:
                loc.wait_for(state="visible", timeout=timeout)
                loc.click()
                LOG("  klik:", name, "->", sel)
                self.wait()
                return loc
            except PWTimeout as e:
                errs.append("{}:{}".format(sel, type(e).__name__))
        raise StepError("gagal klik {} -> {}".format(name, ", ".join(errs)))

    def click_if_visible(self, selectors, name, timeout=4000):
        for sel in selectors:
            loc = self.page.locator(sel).first
            try:
                loc.wait_for(state="visible", timeout=timeout)
                loc.click()
                LOG("  klik:", name, "->", sel)
                self.wait()
                return True
            except PWTimeout:
                continue
        return False

    def role_click(self, name, exact=True, nth=0, timeout=12000):
        loc = self.page.get_by_role("button", name=name, exact=exact).nth(nth)
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        LOG("  klik:", name)
        self.wait()

    def role_fill(self, name, text, exact=True):
        loc = self.page.get_by_role("textbox", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=15000)
        loc.fill(text)
        LOG("  isi:", name, "=", text[:40])
        self.wait()

    def role_text(self, name, exact=True):
        loc = self.page.get_by_role("textbox", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=15000)
        try:
            return loc.input_value()
        except Exception:
            return loc.inner_text()

    def radio_click(self, name, exact=True):
        loc = self.page.get_by_role("radio", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=6000)
        loc.click()
        LOG("  radio:", name)
        self.wait()

    def text_click(self, text, exact=True, nth=0, timeout=6000):
        loc = self.page.get_by_text(text, exact=exact).nth(nth)
        loc.wait_for(state="visible", timeout=timeout)
        try:
            loc.click()
        except Exception:
            loc.click(force=True)
        LOG("  klik teks:", text)
        self.wait()


def open_editor(s, row):
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
         except (PWTimeout, Exception):
             continue
     else:
         s.click_first(SEL_EDIT_BTN, "Detail")
     s.shot("00-editor")


def reuse_details(s, prev_fname):
      logger = get_logger()
      logger.action("Gunakan Detail Video Lama", "dari Video Sebelumnya")
      s.click_first(SEL_REUSE_BTN, "Salin detail video")
      target = (prev_fname or "").replace(".mp4", "").strip()
      target_normalized = re.sub(r'\s+', ' ', target.lower())
      
      cards = s.page.locator(SEL_REUSE_OPTION)
      picked = None
      picked_txt = None
      
      # Coba cari di kartu yang sudah visible
      for i in range(cards.count()):
          try:
              t = cards.nth(i).inner_text(timeout=1500).strip()
              t_normalized = re.sub(r'\s+', ' ', t.lower())
              # Match exact atau substring (case-insensitive)
              if t_normalized == target_normalized or target_normalized in t_normalized:
                  picked = cards.nth(i)
                  picked_txt = t
                  break
          except PWTimeout:
              continue
      
      # Jika tidak ketemu, coba search menggunakan search input di dialog
      if picked is None:
          logger.step("Cari di search box", indent=2)
          search_input = None
          for sel in ["ytcp-dialog input[type='text']", "input[placeholder*='Telusuri']", "input[aria-label*='Telusuri']"]:
              try:
                  inp = s.page.locator(sel).first
                  inp.wait_for(state="visible", timeout=2000)
                  search_input = inp
                  break
              except:
                  continue
          
          if search_input:
              try:
                  # Click 2x untuk fokus (YouTube UI quirk)
                  search_input.click(force=True)
                  s.wait(200 / 1000.0)
                  search_input.click(force=True)
                  s.wait(200 / 1000.0)
                  search_input.fill("")  # clear dulu
                  s.wait(200 / 1000.0)
                  search_input.type(target, delay=30)  # type perlahan
                  s.wait(500 / 1000.0)
                  search_input.press("Enter")  # submit search
                  s.wait(500 / 1000.0)
                  logger.step(f"Search: {target[:50]}...", indent=3)
                  s.wait(3000 / 1000.0)  # tunggu lebih lama untuk hasil
                  
                  # Loop kartu lagi setelah search
                  cards = s.page.locator(SEL_REUSE_OPTION)
                  for i in range(cards.count()):
                      try:
                          t = cards.nth(i).inner_text(timeout=1500).strip()
                          t_normalized = re.sub(r'\s+', ' ', t.lower())
                          if t_normalized == target_normalized or target_normalized in t_normalized:
                              picked = cards.nth(i)
                              picked_txt = t
                              break
                      except PWTimeout:
                          continue
              except Exception as e:
                  logger.warning(f"Gagal search di dialog: {e}")
      
      # Jika masih tidak ketemu: gunakan recent video (first card) sebagai fallback
      if picked is None:
          logger.warning(f"Video Sebelumnya '{target}' Tidak Ditemukan")
          logger.step("Gunakan video terakhir yang tersedia sebagai fallback", indent=2)
          if cards.count() > 0:
              picked = cards.first
              picked_txt = (picked.inner_text() or "").strip()[:80]
          else:
              logger.error("Tidak ada video apapun di dialog reuse")
              raise StepError("Reuse: Dialog kosong, tidak ada video untuk dipilih")
      
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


def edit_title_desc(s, num, prev_num):
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


def _leading_number(text):
    m = re.match(r"^\s*(\d{1,4})\b", text or "")
    return int(m.group(1)) if m else None


def upload_thumbnail(s, num, fname=None):
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


def set_recording_date(s):
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
     except Exception as e:
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
     s.shot("04-recdate")


def advanced_settings(s):
     logger = get_logger()
     logger.action("Pengaturan Lanjutan", "AI Tidak, Tanggal Hari Ini")
     s.click_first(SEL_SHOW_MORE, "Tampilkan setelan lanjutan")
     s.radio_click(SEL_AI_NO_NAME)
     set_recording_date(s)
     s.shot("04-advanced")
     s.role_click(SEL_NEXT)
     logger.result("Pengaturan Lanjutan Selesai", success=True)


def _rating_locked(s):
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


def monetization(s):
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
         return
     logger.action("Rating", "Atur Rating Iklan")
     s.text_click(SEL_RATING_NONE)
     try:
         s.role_click(SEL_RATING_SUBMIT)
     except (PWTimeout, Exception):
         logger.warning("Kirim Rating Gagal")
         sub = s.page.get_by_role("button", name=SEL_RATING_SUBMIT, exact=True).first
         sub.wait_for(state="visible", timeout=6000)
         sub.click(force=True)
         s.wait()
     logger.result("Rating Dikirim", success=True)
     s.role_click(SEL_NEXT)


def video_elements(s, prev_num, playlist, cfg):
     logger = get_logger()
     logger.action("Atur Elemen Video", "End Screen & Kartu")
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
     logger.action("Kartu", f"Playlist : {playlist or '(tidak cocok)'}")
     try:
         cb = s.page.locator(SEL_CARDS_BUTTON).first
         cb.wait_for(state="visible", timeout=8000)
         s.page.evaluate("() => document.querySelector('#cards-button').click()")
         s.wait(2000 / 1000.0)
         logger.step("Buka Panel Kartu", indent=2)
     except (PWTimeout, Exception) as e:
         logger.warning(f"Gagal Buka Panel Kartu")
         try:
             cb = s.page.locator(SEL_CARDS_BUTTON).first
             cb.click(force=True)
             s.wait(2000 / 1000.0)
         except Exception:
             pass

     s.wait(2000 / 1000.0)
     add_heading = s.page.get_by_text("Tambahkan kartu", exact=False)
     if add_heading.count() == 0:
         logger.info("Kartu Sudah Ada")
         s.page.keyboard.press("Escape")
         s.wait(1500 / 1000.0)
         s.shot("05-video-elements")
         return

     logger.info("Belum Ada Kartu")
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

         picked = False
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

     logger.step("Set Posisi Kartu 00:03:00", indent=2)
     try:
         time_inputs = s.page.locator("input[type='text'][aria-label*='menit']")
         if time_inputs.count() == 0:
             time_inputs = s.page.locator("input[type='text']").filter(has_text="")
         if time_inputs.count() > 0:
             time_input = time_inputs.first
             time_input.wait_for(state="visible", timeout=3000)
             time_input.click()
             s.wait(300 / 1000.0)
             time_input.fill("00:03:00")
             s.wait(500 / 1000.0)
             logger.result("Posisi Kartu 00:03:00", success=True)
         else:
             logger.warning("Input Posisi Kartu Tidak Ada")
     except Exception as e:
         logger.warning(f"Gagal Set Posisi Kartu")

     s.role_click(SEL_SAVE)
     logger.result("Elemen Video Disimpan", success=True)
     s.shot("05-video-elements")


def schedule(s, date_obj, time_str):
     logger = get_logger()
     logger.action("Tentukan Jadwal", f"{date_obj.strftime('%d/%m/%Y')} {time_str}")
     s.role_click(SEL_NEXT)
     s.role_click(SEL_NEXT)
     sc = s.page.locator("ytcp-video-visibility-select #second-container").first
     t = sc.get_by_text("Jadwalkan", exact=True).first
     try:
         t.wait_for(state="visible", timeout=5000)
         t.click(force=True)
         logger.step("Pilih Jadwalkan", indent=2)
         s.wait(1500 / 1000.0)
     except PWTimeout:
         logger.warning("Gagal Klik Jadwalkan")
     vis_type = s.cfg.get("schedule_visibility_type", "PUBLISH_FROM_SPONSORS_ONLY")
     sc = s.page.locator("ytcp-video-visibility-select #second-container").first
     radio = sc.locator(f"tp-yt-paper-radio-button[name='{vis_type}']").first
     try:
         radio.wait_for(state="visible", timeout=4000)
         radio.click()
         label = (radio.inner_text(timeout=1000) or "").strip().replace("\n", " ")[:50]
         logger.step(f"Pilih Visibilitas {label}", indent=2)
         s.wait(800 / 1000.0)
     except Exception as e:
         logger.warning(f"Gagal Pilih Visibilitas")
     set_schedule_date(s, date_obj)
     set_schedule_time(s, time_str)
     s.shot("06-visibility")
     s.click_first(SEL_SCHEDULE_BTN, "tombol Jadwalkan")
     s.click_if_visible(SEL_CLOSE, "Tutup")
     logger.result("Jadwal Ditentukan", success=True)
     s.shot("07-scheduled")


MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _click_schedule_day(s, day):
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


def set_schedule_date(s, date_obj):
     logger = get_logger()

     s.wait(2000 / 1000.0)
     opened = False

     vis_type = s.cfg.get("schedule_visibility_type", "PUBLISH_FROM_SPONSORS_ONLY")

     try:
         triggers = s.page.locator("#datepicker-trigger").all()
         if len(triggers) > 1:
             triggers[-1].click()
             s.wait(1500 / 1000.0)
             if s.page.locator("ytcp-scrollable-calendar").count() > 0:
                 opened = True
                 logger.step(f"Kalender Terbuka {vis_type}", indent=2)
     except Exception:
         pass

     if not opened:
         try:
             s.page.evaluate("() => { const all = document.querySelectorAll('#datepicker-trigger'); if (all.length > 1) all[all.length-1].click(); else all[0].click(); }")
             s.wait(2500 / 1000.0)
             if s.page.locator("ytcp-scrollable-calendar").count() > 0:
                 opened = True
                 logger.step("Kalender Terbuka", indent=2)
         except Exception:
             pass

     if not opened:
         logger.warning("Kalender Tidak Bisa Dibuka")
         return

     month_names_short = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
     target_date_str = f"{date_obj.day} {month_names_short[date_obj.month - 1]} {date_obj.year}"

     input_selectors = [
         "ytcp-date-picker input[type='text']",
         "ytcp-date-picker input",
         "ytcp-scrollable-calendar input",
         "input.date-input",
         "ytcp-datetime-picker input",
     ]
     for sel in input_selectors:
         try:
             date_input = s.page.locator(sel).first
             date_input.wait_for(state="visible", timeout=2000)
             date_input.click()
             s.wait(500 / 1000.0)
             date_input.press("Control+A")
             s.wait(300 / 1000.0)
             date_input.fill(target_date_str)
             s.wait(800 / 1000.0)
             logger.step(f"Mengisi Tanggal {target_date_str}", indent=2)
             date_input.press("Enter")
             s.wait(2000 / 1000.0)
             logger.result(f"Tanggal Jadwal {target_date_str}", success=True)
             return
         except Exception as e:
             continue
     logger.warning("Gagal Isi Tanggal - Klik Kalender")

     target_idx = date_obj.year * 12 + date_obj.month
     target_label = f"{MONTHS[date_obj.month - 1].upper()} {date_obj.year}"
     for attempt in range(24):
         cal = s.page.locator("ytcp-scrollable-calendar").first
         months = cal.locator("div.calendar-month")
         found = False
         for i in range(months.count()):
             col = months.nth(i)
             label_div = col.locator("div.label").first
             try:
                 label = label_div.inner_text(timeout=1000).strip().upper()
             except Exception:
                 continue
             if label == target_label:
                 days = col.locator(f"span.calendar-day:has-text('{date_obj.day}')")
                 for j in range(days.count()):
                     day = days.nth(j)
                     try:
                         cls = day.get_attribute("class") or ""
                         if "disabled" in cls or "muted" in cls or "outside" in cls:
                             continue
                         day.click()
                         logger.result(f"Tanggal Jadwal {date_obj.day}/{date_obj.month}/{date_obj.year}", success=True)
                         s.wait(800 / 1000.0)
                         return
                     except Exception:
                         continue
                 found = True
                 break
         if found:
             break
         cur_labels = []
         for i in range(months.count()):
             try:
                 label_div = months.nth(i).locator("div.label").first
                 label = label_div.inner_text(timeout=1000).strip().upper()
                 cur_labels.append(label)
             except Exception:
                 pass
         if not cur_labels:
             break
         first_label = cur_labels[0]
         parts = first_label.split()
         if len(parts) >= 2:
             try:
                 month_name = parts[0]
                 year = int(parts[-1])
                 month = MONTHS.index(month_name.capitalize()) + 1 if month_name.capitalize() in MONTHS else None
                 if month:
                     cur_idx = year * 12 + month
                     if cur_idx < target_idx:
                         nav = s.page.get_by_text("Bulan berikutnya", exact=True).first
                         try:
                             nav.click()
                             s.wait(800 / 1000.0)
                             continue
                         except Exception:
                             pass
                     elif cur_idx > target_idx:
                         nav = s.page.get_by_text("Bulan sebelumnya", exact=True).first
                         try:
                             nav.click()
                             s.wait(800 / 1000.0)
                             continue
                         except Exception:
                             pass
             except Exception:
                 pass
         break
     logger.warning("Tanggal Jadwal Gagal")
     s.shot("06-scheddate")


def set_schedule_time(s, time_str):
     logger = get_logger()
     option = time_str.replace(":", ".")
     for sel in SEL_SCHED_TIME:
         loc = s.page.locator(sel).first
         try:
             loc.wait_for(state="visible", timeout=3000)
             loc.click()
             s.wait()
             logger.step(f"Klik Kolom Waktu", indent=2)
             break
         except Exception:
             continue
     try:
         opt = s.page.get_by_role("option", name=option).first
         opt.wait_for(state="visible", timeout=4000)
         opt.click()
         logger.step(f"Waktu Dipilih {option}", indent=2)
         s.wait()
         return
     except PWTimeout:
         logger.warning(f"Waktu {option} Tidak Ada")


def process_draft(s, num, prev_fname, sch, cfg):
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
      video_elements(s, prev_num, playlist, cfg)
      schedule(s, sch, cfg["schedule_time"])

      logger.end_draft(num, success=True)


def main():
     global _logger
     ap = argparse.ArgumentParser(description="Automasi draft YouTube Studio")
     ap.add_argument("mode", nargs="?", default="run",
                     choices=["run", "login"])
     ap.add_argument("--limit", type=int, default=None, help="maks draft diproses")
     ap.add_argument("--verbose", action="store_true", help="enable verbose logging")
     args = ap.parse_args()

     cfg = load_config()

     log_file = os.path.join(cfg.get("logs_dir", "logs"), "yt_auto.log")
     _logger = init_logger(name="YT-AUTO", log_file=log_file, verbose=args.verbose)

     _logger.section("BITS YouTube Automation")
     _logger.info(f"Mode : {args.mode}")
     if args.limit:
         _logger.info(f"Batas Draft {args.limit}")

     known_dates = {}

     p = sync_playwright().start()
     # Timezone wajib diset agar dropdown jadwal YouTube Studio memakai zona waktu yang sama.
     # Tanpa ini, browser memakai TZ sistem (mis. UTC) sehingga "20:00" jadi 20:00 UTC = 03:00 WIB.
     tz = cfg.get("timezone", "Asia/Jakarta")
     ctx = p.chromium.launch_persistent_context(
         user_data_dir=os.path.join(BASE, cfg["profile_dir"]),
         channel="chrome",
         headless=True,
         viewport={"width": 1366, "height": 900},
         timezone_id=tz,
         user_agent=(
             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
         ),
         args=["--disable-blink-features=AutomationControlled"],
     )
     page = ctx.pages[0] if ctx.pages else ctx.new_page()

     s = None
     try:
         if args.mode == "login":
             _logger.action("Login Mode", "Tunggu Konfirmasi Manual")
             page.goto("https://studio.youtube.com/")
             input("  [Tekan Enter setelah login selesai]")
             _logger.success("Login Selesai")
             return

         _logger.info("Membuka YouTube Studio...")
         page.goto(cfg["studio_url"])
         page.wait_for_timeout(4000)

         s = Studio(page, ctx, cfg)

         done = 0
         total_drafts = 0

         try:
             rows = page.locator(SEL_ROW)
             rows.first.wait_for(state="attached", timeout=10000)
             total_drafts = rows.count()
         except:
             pass

         _logger.progress(f"Ditemukan {total_drafts} Draft")
         _logger.separator()

         while True:
             if args.limit and done >= args.limit:
                 _logger.warning(f"Mencapai Batas Draft {args.limit}")
                 break
             rows = page.locator(SEL_ROW)
             rows.first.wait_for(state="attached", timeout=30000)
             if rows.count() == 0:
                 _logger.success("Semua Draft Selesai")
                 break

             open_editor(s, rows.first)
             num, fname = read_file_info(s)
             if num is None:
                 _logger.error("Nomor Tidak Terbaca Dari Nama File")
                 break

             prev_num = num - 1
             prev_fname = replace_number(fname, num, prev_num) if fname else None
             if prev_fname in known_dates:
                 prev_date = known_dates[prev_fname]
                 _logger.step(f"Pakai Tanggal Sesi Draft {prev_num} : {prev_date}", indent=1)
             else:
                 prev_date = find_prev_schedule_date(s, prev_num, prev_fname)
             if prev_date is None:
                 _logger.error(f"Tanggal Video Sebelumnya {prev_num} Tidak Ditemukan")
                 _logger.info("Jadwalkan Video Sebelumnya Dulu")
                 break
             sch = prev_date + dt.timedelta(days=cfg["schedule_offset_days"])
             sch_str = sch.strftime(cfg["date_format"])
             if fname:
                 known_dates[fname] = sch

             process_draft(s, num, prev_fname, sch, cfg)
             done += 1
             page.wait_for_timeout(2000)
             page.goto(cfg["studio_url"])
             page.wait_for_timeout(1000)
             if cfg.get("pause_between_drafts") and sys.stdin.isatty():
                 input("  [Tekan Enter untuk lanjut ke draft berikutnya]")
     except StepError as e:
         _logger.error(f"{e}")
         if s:
             s.shot("FAIL", force=True)
         sys.exit(1)
     except Exception as e:
         _logger.error(f"{type(e).__name__} : {e}")
         if s:
             s.shot("FAIL", force=True)
         raise
     finally:
         if _logger:
             _logger.separator()
             _logger.summary()
         p.stop()


if __name__ == "__main__":
    main()
