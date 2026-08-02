#!/usr/bin/env python3
"""
Automation YouTube Studio: proses draft video secara berurutan.
Alur per draft (berdasarkan rekaman capture user):
  buka daftar draft -> klik "Detail" -> Gunakan kembali detail -> pilih video pertama (terbaru)
  -> "Gunakan kembali" -> ganti angka di judul & deskripsi -> Upload file thumbnail
  -> "Tampilkan setelan lanjutan" -> AI "Tidak, AI tidak digunakan" -> tanggal perekaman hari ini
  -> Berikutnya -> (.m10n-text) Monetisasi "Aktif" -> Selesai -> Berikutnya
  -> rating "Tidak satu pun di atas" -> Kirim rating -> Berikutnya
  -> Impor dari video -> pilih video pertama -> Simpan
  -> #cards-button Tambahkan -> posisi kartu -> Playlist -> cari playlist -> Simpan
  -> Berikutnya -> Jadwalkan (Publik) = last_date + offset, jam config -> Jadwalkan -> Tutup
"""

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

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = lambda *a: print("[{}]".format(time.strftime("%H:%M:%S")), *a, flush=True)

# --------------------------------------------------------------------------
# SELECTOR (berdasarkan hasil capture) - sesuaikan bila perlu
# --------------------------------------------------------------------------
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
    "ytcp-playlist-picker input[type='search']",
    "input[placeholder*='playlist']",
    "ytcp-dialog input",
]

SEL_VIS_PUBLIC_RADIO = "Dari khusus pelanggan ke"
SEL_SCHED_TIME = ["input[placeholder*='hh:mm']", "input[aria-label*='Waktu']", "#input-3"]
SEL_SCHEDULE_BTN = ["ytcp-button#schedule-button", "ytcp-button:has-text('Jadwalkan')"]
SEL_CLOSE = ["ytcp-button:has-text('Tutup')", "button:has-text('Tutup')"]


# --------------------------------------------------------------------------
def load_config():
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def today_str(fmt="%d/%m/%Y"):
    return dt.date.today().strftime(fmt)


def read_file_info(s):
    """Baca 'Nama file' dari panel info editor (ytcp-video-info).
    Nama file berisi nomor di awal, mis. '124 PENGAJIAN KITAB ....mp4'.
    Return (num, nama_file) atau (None, None)."""
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


def back_to_list(s):
    """Kembali ke daftar draft dari editor (tombol 'Kembali')."""
    for name in ("Kembali", "Batal"):
        loc = s.page.get_by_role("button", name=name, exact=True).first
        try:
            loc.wait_for(state="visible", timeout=4000)
            loc.click()
            s.wait(1500 / 1000.0)
            LOG("  kembali ke daftar draft:", name)
            return True
        except PWTimeout:
            continue
    LOG("  !! tombol kembali tidak ditemukan - cek manual")
    return False


MONTH_ID = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "Mei": 5, "Jun": 6,
    "Jul": 7, "Agu": 8, "Sep": 9, "Okt": 10, "Nov": 11, "Des": 12,
}


def scheduled_url(cfg, series=None):
    """URL daftar video terjadwal (HAS_SCHEDULE), sort terbaru di atas.
    series = nama seri utk filter judul, mis. 'PENGAJIAN KITAB RISALATUL MAYMUNIYAH - ABUYA UCI CILONGOK'."""
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
    """Parse tanggal '30 Jul 2027' -> dt.date."""
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
    """Cari tanggal jadwal video prev di daftar terjadwal, sesuai nama file
    (nomor + nama seri). Buka daftar terjadwal di halaman baru, cari baris
    yang judulnya == prev_fname tanpa ekstensi, baca tanggal dari kolom tanggal.
    Return dt.date atau None."""
    page = s.page
    target = (prev_fname or "").replace(".mp4", "").strip()
    series = re.sub(r"^\d+\s+", "", target).strip()
    LOG("Cari tanggal video prev:", prev_num, "->", target)
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
                        LOG("  ketemu! tanggal:", d)
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
        LOG("  !! video prev", prev_num, "tidak ditemukan di daftar terjadwal")
        return None
    finally:
        spage.close()


def replace_number(text, old, new):
    return re.sub(r"(?<!\d){}(?!\d)".format(old), str(new), text or "")


def find_thumbnail(cfg, num):
    d = cfg["thumbnail_dir"]
    if not os.path.isdir(d):
        return None
    for pat in ["{}[ _-]*.*".format(num), "{}*.*".format(num)]:
        hits = sorted(glob.glob(os.path.join(d, pat)))
        if hits:
            return hits[0]
    return None


def find_playlist(cfg, title):
    """Cari playlist berdasarkan keyword yang muncul di judul.
    `playlist_keywords` = { nama_playlist: [kata kunci...] }.
    Jika tidak terdefinisi, fallback ke substring dari `playlists`."""
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


# --------------------------------------------------------------------------
class StepError(Exception):
    pass


class Studio:
    def __init__(self, page, ctx, cfg, dry=False):
        self.page = page
        self.ctx = ctx
        self.cfg = cfg
        self.dry = dry
        self.shots = os.path.join(cfg.get("logs_dir", "logs"), "shots")
        os.makedirs(self.shots, exist_ok=True)
        self.wa = cfg.get("wait_after_action_ms", 700) / 1000.0

    def wait(self, t=None):
        self.page.wait_for_timeout(int((t if t is not None else self.wa) * 1000))

    def shot(self, name):
        try:
            self.page.screenshot(path=os.path.join(self.shots, name + ".png"))
        except Exception:
            pass

    # ---------- CSS-based ----------
    def click_first(self, selectors, name, timeout=12000):
        if self.dry:
            LOG("  [dry] klik:", name)
            return None
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
        if self.dry:
            LOG("  [dry] klik (jika ada):", name)
            return True
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

    # ---------- Role-based (hasil codegen) ----------
    def role_click(self, name, exact=True, nth=0, timeout=12000):
        if self.dry:
            LOG("  [dry] klik:", name)
            return
        loc = self.page.get_by_role("button", name=name, exact=exact).nth(nth)
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        LOG("  klik:", name)
        self.wait()

    def role_click_if_visible(self, name, exact=True, nth=0, timeout=4000):
        if self.dry:
            LOG("  [dry] klik (jika ada):", name)
            return True
        try:
            self.role_click(name, exact=exact, nth=nth, timeout=timeout)
            return True
        except (PWTimeout, Exception):
            return False

    def role_fill(self, name, text, exact=True):
        if self.dry:
            LOG("  [dry] isi:", name, "=", text[:40])
            return
        loc = self.page.get_by_role("textbox", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=15000)
        loc.fill(text)
        LOG("  isi:", name, "=", text[:40])
        self.wait()

    def role_text(self, name, exact=True):
        if self.dry:
            return ""
        loc = self.page.get_by_role("textbox", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=15000)
        try:
            return loc.input_value()
        except Exception:
            return loc.inner_text()

    def radio_click(self, name, exact=True):
        if self.dry:
            LOG("  [dry] radio:", name)
            return
        loc = self.page.get_by_role("radio", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=6000)
        loc.click()
        LOG("  radio:", name)
        self.wait()

    def text_click(self, text, exact=True, nth=0, timeout=6000):
        if self.dry:
            LOG("  [dry] klik teks:", text)
            return
        loc = self.page.get_by_text(text, exact=exact).nth(nth)
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        LOG("  klik teks:", text)
        self.wait()


# --------------------------------------------------------------------------
def open_editor(s, row):
    LOG("Buka editor draft (tombol Edit draf)")
    for sel in SEL_EDIT_DRAFT_BTN:
        try:
            loc = row.locator(sel).first
            loc.wait_for(state="visible", timeout=5000)
            loc.click()
            s.wait(1500 / 1000.0)
            LOG("  klik: Edit draf ->", sel)
            break
        except (PWTimeout, Exception):
            continue
    else:
        s.click_first(SEL_EDIT_BTN, "Detail")
    s.shot("00-editor")


def reuse_details(s, prev_fname):
    LOG("Gunakan kembali detail dari video prev sesuai nama file")
    s.click_first(SEL_REUSE_BTN, "Gunakan kembali detail")
    if not s.dry:
        target = (prev_fname or "").replace(".mp4", "").strip()
        cards = s.page.locator(SEL_REUSE_OPTION)
        picked = None
        for i in range(cards.count()):
            try:
                t = cards.nth(i).inner_text(timeout=1500).strip()
            except PWTimeout:
                continue
            if t and t == target:
                picked = cards.nth(i)
                break
        if picked is None:
            LOG("  !! entity prev tidak ketemu, pakai video terbaru")
            picked = cards.first
        picked.wait_for(state="visible", timeout=8000)
        txt = (picked.inner_text() or "").strip()[:80]
        picked.click()
        LOG("  pilih video:", txt)
        s.wait(3000 / 1000.0)
        # klik tombol 'Gunakan kembali' di dialog reuse
        btn = s.page.locator(
            "ytcp-uploads-reuse-details-selection-dialog button[aria-label='Gunakan kembali']"
        ).first
        btn.wait_for(state="visible", timeout=15000)
        for _ in range(60):
            if btn.get_attribute("aria-disabled") != "true":
                break
            s.wait(0.5)
        btn.click(force=True)
        LOG("  klik Gunakan kembali")
    s.shot("01-after-reuse")
    s.wait(3500 / 1000.0)


def edit_title_desc(s, num, prev_num):
    LOG("Edit judul & deskripsi: {} -> {}".format(prev_num, num))
    t = s.role_text(SEL_TITLE_NAME, exact=False)
    d = s.role_text(SEL_DESC_NAME, exact=False)
    new_t = replace_number(t, prev_num, num)
    new_d = replace_number(d, prev_num, num)
    s.role_fill(SEL_TITLE_NAME, new_t, exact=False)
    s.role_fill(SEL_DESC_NAME, new_d, exact=False)
    s.shot("02-title-desc")


def upload_thumbnail(s, num):
    fp = find_thumbnail(s.cfg, num)
    if not fp:
        LOG("!! thumbnail utk", num, "tidak ditemukan - LEWATI (cek thumbnails/)")
        return
    LOG("Upload thumbnail:", os.path.basename(fp))
    if not s.dry:
        # langsung set file ke input (tanpa klik tombol Upload, karena bisa sudah ada thumbnail)
        try:
            s.page.locator(SEL_THUMB_INPUT).first.set_input_files(fp, timeout=5000)
            s.wait(1500 / 1000.0)
            LOG("  thumbnail terpasang")
        except Exception as e:
            LOG(f"  !! gagal upload thumbnail: {e}")
    s.shot("03-thumbnail")


def set_recording_date(s):
    """Buka datepicker 'Tanggal perekaman' (nth=1 sesuai rekaman) lalu pilih 'Hari ini'."""
    if s.dry:
        LOG("  [dry] tanggal perekaman:", today_str())
        return
    btns = s.page.get_by_role("button", name=re.compile(SEL_REC_DATE_BTN))
    target = None
    # rekaman memakai nth(1) => iterasi dari belakang agar kena tombol yang benar
    for i in range(btns.count() - 1, -1, -1):
        try:
            b = btns.nth(i)
            b.wait_for(state="visible", timeout=4000)
            target = b
            break
        except PWTimeout:
            continue
    if target is None:
        LOG("!! tombol Tanggal perekaman tidak ketemu")
        return
    target.click()
    s.wait()
    # coba tombol "Hari ini" / "Today"
    for label in ["Hari ini", "Today"]:
        try:
            tb = s.page.get_by_role("button", name=label).first
            tb.wait_for(state="visible", timeout=2500)
            tb.click()
            LOG("  tanggal perekaman:", label)
            s.wait()
            return
        except PWTimeout:
            continue
    # fallback: klik angka hari ini di kalender yang tampil (di dalam dialog)
    day = dt.date.today().day
    if _click_schedule_day(s, day):
        LOG("  tanggal perekaman: hari", day)
        s.wait()
        return
    LOG("!! tanggal perekaman tidak ter-set - set manual jika perlu")
    s.shot("04-recdate")


def advanced_settings(s):
    LOG("Setelan lanjutan: AI Tidak + tanggal perekaman hari ini")
    s.click_first(SEL_SHOW_MORE, "Tampilkan setelan lanjutan")
    s.radio_click(SEL_AI_NO_NAME)
    set_recording_date(s)
    s.shot("04-advanced")
    s.role_click(SEL_NEXT)


def monetization(s):
    LOG("Monetisasi aktif + rating")
    if not s.dry:
        loc = s.page.locator(SEL_M10N).first
        loc.wait_for(state="visible", timeout=6000)
        loc.click()
        LOG("  klik .m10n-text")
        s.wait()
    s.radio_click(SEL_M10N_AKTIF)
    s.role_click(SEL_M10N_SELESAI)
    s.role_click(SEL_NEXT)
    s.text_click(SEL_RATING_NONE)
    s.role_click(SEL_RATING_SUBMIT)
    s.role_click(SEL_NEXT)


def video_elements(s, prev_num, playlist):
    LOG("Layar akhir: impor dari video terbaru")
    if not s.dry:
        # sesuai rekaman: langsung "Impor dari video" (tanpa "Tambahkan layar akhir")
        s.role_click(SEL_ENDSCREEN_IMPORT)
        try:
            item = s.page.locator(SEL_REUSE_OPTION).first
            item.wait_for(state="visible", timeout=4000)
        except PWTimeout:
            s.role_click(SEL_ENDSCREEN_IMPORT)
    else:
        s.role_click(SEL_ENDSCREEN_IMPORT)
    if not s.dry:
        item = s.page.locator(SEL_REUSE_OPTION).first
        item.wait_for(state="visible", timeout=6000)
        item.click()
        LOG("  video terbaru dipilih")
        s.wait()
    s.role_click(SEL_SAVE)

    LOG("Kartu: Playlist ->", playlist or "(tidak cocok)")
    if not s.dry:
        # tunggu overlay backdrop hilang (end screen Simpan)
        try:
            s.page.locator("tp-yt-iron-overlay-backdrop.opened").wait_for(
                state="hidden", timeout=10000
            )
            LOG("  overlay backdrop tertutup")
        except PWTimeout:
            LOG("  !! overlay tetap terbuka, lanjut force click")
        cb = s.page.locator(SEL_CARDS_BUTTON).first
        cb.wait_for(state="visible", timeout=6000)
        cb.click(force=True)
        LOG("  klik #cards-button (force)")
        s.wait(1500 / 1000.0)
    s.role_click(SEL_CARD_ADD)
    # pilih tipe kartu "Playlist" dari options panel (sesuai rekaman: div ke-3)
    if s.dry:
        LOG("  [dry] klik opsi tipe kartu Playlist")
    else:
        opts = s.page.locator(SEL_CARD_TYPE_OPTIONS)
        try:
            opts.nth(2).wait_for(state="visible", timeout=6000)
            opts.nth(2).click()
            LOG("  klik opsi kartu ke-3 (Playlist)")
            s.wait()
        except PWTimeout:
            LOG("  !! options panel tidak ketemu - cek manual")
    if playlist and not s.dry:
        for sel in SEL_CARD_SEARCH:
            box = s.page.locator(sel).first
            try:
                box.wait_for(state="visible", timeout=4000)
                box.fill(playlist)
                s.wait(1500 / 1000.0)
                LOG("  cari playlist:", playlist, "->", sel)
                break
            except PWTimeout:
                continue
        opt = s.page.locator(SEL_CARD_ENTITY).filter(has_text=playlist).first
        try:
            opt.wait_for(state="visible", timeout=6000)
            opt.click()
            s.wait()
            LOG("  playlist dipilih")
        except PWTimeout:
            try:
                s.page.locator(SEL_CARD_ENTITY).nth(3).wait_for(state="visible", timeout=4000)
                s.page.locator(SEL_CARD_ENTITY).nth(3).click()
                LOG("  fallback: entity-card ke-4")
                s.wait()
            except PWTimeout:
                LOG("  !! playlist tidak ketemu di hasil - cek manual")
    s.role_click(SEL_SAVE)
    s.shot("05-video-elements")


def schedule(s, date_obj, time_str):
    LOG("Jadwalkan:", date_obj.strftime("%d/%m/%Y"), time_str)
    # dua "Berikutnya" untuk mencapai layar jadwal (sesuai rekaman)
    s.role_click(SEL_NEXT)
    s.role_click(SEL_NEXT)
    # pilih opsi Jadwalkan (klik section "Jadwalkan" atau teks "Pilih tanggal untuk membuat")
    if s.dry:
        LOG("  [dry] pilih Jadwalkan")
    else:
        # coba klik langsung text "Jadwalkan" atau "Pilih tanggal untuk membuat"
        clicked = False
        for text in ["Jadwalkan", "Pilih tanggal untuk membuat"]:
            try:
                t = s.page.get_by_text(text).first
                t.wait_for(state="visible", timeout=5000)
                t.click()
                LOG("  klik teks:", text)
                s.wait(1500 / 1000.0)
                clicked = True
                break
            except PWTimeout:
                continue
        if not clicked:
            # fallback: klik tombol/section yang mengandung "Jadwalkan"
            try:
                sec = s.page.locator("section:has-text('Jadwalkan'), div:has-text('Jadwalkan')").first
                sec.wait_for(state="visible", timeout=5000)
                sec.click()
                LOG("  klik section Jadwalkan")
                s.wait(1500 / 1000.0)
            except PWTimeout:
                LOG("  !! gagal klik Jadwalkan section")
    # ubah dari Khusus pelanggan ke Publik (radio)
    s.radio_click(SEL_VIS_PUBLIC_RADIO, exact=False)
    set_schedule_date(s, date_obj)
    set_schedule_time(s, time_str)
    s.shot("06-visibility")
    s.click_first(SEL_SCHEDULE_BTN, "tombol Jadwalkan")
    s.click_if_visible(SEL_CLOSE, "Tutup")
    s.shot("07-scheduled")


MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
MONTH_RE = re.compile(r"^(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)\s+\d{4}$")


def _current_month_label(s):
    btns = s.page.get_by_role("button", name=MONTH_RE)
    for i in range(btns.count()):
        try:
            txt = btns.nth(i).inner_text(timeout=1500).strip()
            if MONTH_RE.match(txt):
                return txt
        except Exception:
            continue
    return None


def _month_index(label):
    m = MONTH_RE.match(label or "")
    if not m:
        return None
    month = MONTHS.index(m.group(1)) + 1
    year = int(label.split()[-1])
    return year * 12 + month


def _nav_month(s, direction):
    """direction: 'next' atau 'prev'"""
    for name in ["Bulan berikutnya", "Next month"] if direction == "next" else ["Bulan sebelumnya", "Previous month"]:
        try:
            b = s.page.get_by_role("button", name=name).first
            b.wait_for(state="visible", timeout=2500)
            b.click()
            s.wait()
            return True
        except PWTimeout:
            continue
    # fallback: tombol panah chevron terakhir/pertama di header datepicker
    try:
        btns = s.page.get_by_role("button")
        idx = -1 if direction == "next" else 0
        b = btns.nth(idx)
        b.wait_for(state="visible", timeout=2500)
        b.click()
        s.wait()
        return True
    except PWTimeout:
        return False


def _click_schedule_day(s, day):
    """Klik hari di kalender, dibatasi ke dialog datepicker yang terbuka.
    Hindari elemen hari kabur (bulan prev/next) dengan mengecek class mute/faded."""
    dialog = None
    for sel in ["ytcp-dialog[role='dialog']", "[role='dialog']", ".picker-content", "ytcp-dialog"]:
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
            html = loc.evaluate("(el) => el.outerHTML")
        except PWTimeout:
            continue
        except Exception:
            candidates.append(loc)
            continue
        low = html.lower()
        if any(k in low for k in ["mute", "outside", "faded", "disabled", "aria-disabled=\"true\""]):
            continue  # hari kabur dari bulan lain
        candidates.append(loc)
    if not candidates:
        return False
    candidates[-1].click()
    return True


def set_schedule_date(s, date_obj):
    """Buka datepicker tanggal jadwal, navigasi ke bulan target, klik hari."""
    if s.dry:
        LOG("  [dry] tanggal jadwal:", date_obj.strftime("%d/%m/%Y"))
        return
    target_idx = date_obj.year * 12 + date_obj.month
    btns = s.page.get_by_role("button", name=MONTH_RE)
    clicked = None
    # rekaman memakai nth(1) => iterasi dari belakang
    for i in range(btns.count() - 1, -1, -1):
        try:
            btns.nth(i).wait_for(state="visible", timeout=3000)
            clicked = btns.nth(i)
            break
        except PWTimeout:
            continue
    if clicked is None:
        LOG("  !! tombol bulan tidak ketemu - set tanggal manual")
        return
    clicked.click()
    s.wait()
    for _ in range(24):
        if _click_schedule_day(s, date_obj.day):
            LOG("  hari jadwal:", date_obj.day)
            s.wait()
            return
        cur = _current_month_label(s)
        cur_idx = _month_index(cur)
        if cur_idx is None:
            break
        if cur_idx < target_idx:
            ok = _nav_month(s, "next")
        elif cur_idx > target_idx:
            ok = _nav_month(s, "prev")
        else:
            ok = _nav_month(s, "next")  # sudah bulan target tapi hari belum ketemu
        if not ok:
            break
    LOG("  !! tanggal jadwal tidak ter-set - cek manual")
    s.shot("06-scheddate")


def set_schedule_time(s, time_str):
    """Klik kolom waktu lalu pilih opsi, mis. 20:00 -> '20.00'."""
    if s.dry:
        LOG("  [dry] waktu jadwal:", time_str)
        return
    option = time_str.replace(":", ".")
    for sel in SEL_SCHED_TIME:
        loc = s.page.locator(sel).first
        try:
            loc.wait_for(state="visible", timeout=3000)
            loc.click()
            s.wait()
            LOG("  klik kolom waktu ->", sel)
            break
        except Exception:
            continue
    try:
        opt = s.page.get_by_role("option", name=option).first
        opt.wait_for(state="visible", timeout=4000)
        opt.click()
        LOG("  waktu:", option)
        s.wait()
        return
    except PWTimeout:
        LOG("  !! opsi waktu", option, "tidak ketemu - cek manual")


# --------------------------------------------------------------------------
def process_draft(s, num, prev_fname, sch, cfg):
    """Proses satu draft. Editor draft sudah terbuka.
    Identitas (nomor + nama file) dibaca dari 'Nama file'.
    prev_fname = nama file video sebelumnya (utk reuse + tanggal + playlist).
    sch = dt.date jadwal draft ini."""
    prev_num = num - 1
    sch_str = sch.strftime(cfg["date_format"])
    playlist = find_playlist(cfg, prev_fname or "")
    LOG("=" * 60)
    LOG("PROSES DRAFT:", num, "| prev:", prev_num, "| playlist:", playlist or "-")
    LOG("  jadwal:", sch_str, cfg["schedule_time"])
    LOG("  thumbnail:", find_thumbnail(cfg, num))

    reuse_details(s, prev_fname)
    edit_title_desc(s, num, prev_num)
    upload_thumbnail(s, num)
    advanced_settings(s)
    monetization(s)
    video_elements(s, prev_num, playlist)
    schedule(s, sch, cfg["schedule_time"])
    LOG("SELESAI:", num, "-> jadwal", sch_str, cfg["schedule_time"])


def main():
    ap = argparse.ArgumentParser(description="Automasi draft YouTube Studio")
    ap.add_argument("mode", nargs="?", default="run",
                    choices=["run", "list", "login", "dryrun"])
    ap.add_argument("--num", type=int, default=None,
                    help="proses hanya draft dengan nomor ini")
    ap.add_argument("--limit", type=int, default=None, help="maks draft diproses")
    ap.add_argument("--last-date", type=str, default=None,
                    help="opsional: fallback tanggal jadwal prev bila tidak ketemu, format YYYY-MM-DD")
    args = ap.parse_args()

    cfg = load_config()

    last_date = None
    if args.last_date:
        try:
            last_date = dt.date.fromisoformat(args.last_date)
        except ValueError:
            LOG("!! --last-date harus format YYYY-MM-DD, contoh: 2027-07-09")
            sys.exit(2)

    known_dates = {}  # nama file penuh -> tanggal jadwal hasil sesi ini

    p = sync_playwright().start()
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(BASE, cfg["profile_dir"]),
        channel="chrome",
        headless=False,
        viewport={"width": 1366, "height": 900},
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
            LOG("Login dulu secara manual di browser, lalu tekan Enter...")
            page.goto("https://studio.youtube.com/")
            input("  [Enter setelah login selesai]")
            return

        page.goto(cfg["studio_url"])
        page.wait_for_timeout(4000)

        if args.mode == "list":
            rows = page.locator(SEL_ROW)
            rows.first.wait_for(state="attached", timeout=30000)
            for i in range(rows.count()):
                t = rows.nth(i).locator(SEL_TITLE_LINK).inner_text()
                LOG(i + 1, "->", t)
            return

        s = Studio(page, ctx, cfg, dry=(args.mode == "dryrun"))
        if args.mode == "dryrun":
            LOG("MODE DRY-RUN: buka tiap draft, baca 'Nama file', cetak rencana (tanpa ubah apa pun).")

        done = 0
        while True:
            if args.limit and done >= args.limit:
                break
            rows = page.locator(SEL_ROW)
            rows.first.wait_for(state="attached", timeout=30000)
            if rows.count() == 0:
                LOG("Semua draft selesai.")
                break

            # pilih baris & baca identitas dari 'Nama file' di editor
            if args.num is not None:
                found = None
                for i in range(rows.count()):
                    open_editor(s, rows.nth(i))
                    num, fname = read_file_info(s)
                    LOG("  cek baris", i + 1, "-> nomor:", num)
                    if num == args.num:
                        found = (num, fname)
                        break
                    back_to_list(s)
                    page.wait_for_timeout(2000)
                if not found:
                    LOG("Draft --num", args.num, "tidak ditemukan di list.")
                    break
                num, fname = found
                LOG("  draft --num", num, "ditemukan, file:", fname)
            elif args.mode == "dryrun":
                if done >= rows.count():
                    break
                open_editor(s, rows.nth(done))
                num, fname = read_file_info(s)
                if num is None:
                    LOG("!! baris", done + 1, "tidak bisa baca nomor dari Nama file - lewati.")
                    back_to_list(s)
                    done += 1
                    continue
            else:
                open_editor(s, rows.first)
                num, fname = read_file_info(s)
                if num is None:
                    LOG("!! tidak bisa baca nomor dari Nama file - berhenti.")
                    break

            # nama file video prev = ganti angka di fname dengan num-1
            prev_num = num - 1
            prev_fname = replace_number(fname, num, prev_num) if fname else None
            if prev_fname in known_dates:
                prev_date = known_dates[prev_fname]  # hasil sesi ini (draft sblmnya)
                LOG("  pakai tanggal sesi ini utk prev", prev_num, ":", prev_date)
            else:
                prev_date = find_prev_schedule_date(s, prev_num, prev_fname)
            if prev_date is None:
                prev_date = last_date  # fallback bila user beri --last-date
            if prev_date is None:
                LOG("!! tanggal video prev", prev_num, "tidak ditemukan di daftar terjadwal.")
                LOG("   berikan --last-date (tanggal jadwal video {}).".format(prev_num))
                break
            sch = prev_date + dt.timedelta(days=cfg["schedule_offset_days"])
            sch_str = sch.strftime(cfg["date_format"])
            if fname:
                known_dates[fname] = sch

            if s.dry:
                playlist = find_playlist(cfg, fname or "")
                LOG("=" * 60)
                LOG("PLAN draft:", num, "| file:", fname or "-",
                    "| prev:", prev_num, "| playlist:", playlist or "-")
                LOG("  prev jadwal:", prev_date.isoformat())
                LOG("  jadwal:", sch_str, cfg["schedule_time"])
                LOG("  thumbnail:", find_thumbnail(cfg, num))
                done += 1
                back_to_list(s)
                page.goto(cfg["studio_url"])
                page.wait_for_timeout(4000)
                continue

            # editor sudah terbuka dari open_editor di atas, proses langsung
            process_draft(s, num, prev_fname, sch, cfg)
            done += 1
            page.wait_for_timeout(3000)
            page.goto(cfg["studio_url"])
            page.wait_for_timeout(3000)
            if cfg.get("pause_between_drafts"):
                input("  [Enter utk lanjut ke draft berikutnya]")
    except StepError as e:
        LOG("!!", e)
        if s:
            s.shot("FAIL")
        sys.exit(1)
    except Exception as e:
        LOG("!! error:", type(e).__name__, e)
        if s:
            s.shot("FAIL")
        raise
    finally:
        p.stop()


if __name__ == "__main__":
    main()
