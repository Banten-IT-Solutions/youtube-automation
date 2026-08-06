#!/usr/bin/env python3
"""Step-step penjadwalan publikasi video."""

from __future__ import annotations

import datetime as dt

from playwright.sync_api import TimeoutError as PWTimeout

from .logger import get_logger
from .selectors import SEL_CLOSE, SEL_NEXT, SEL_SCHED_TIME, SEL_SCHEDULE_BTN

from .studio import Studio

MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def schedule(s: Studio, date_obj: dt.date | None, time_str: str, no_schedule: bool = False) -> None:
     logger = get_logger()
     label = "default" if (no_schedule or date_obj is None) else date_obj.strftime('%d/%m/%Y')
     logger.action("Tentukan Jadwal", f"{label} {time_str}")
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
     except Exception:
         logger.warning(f"Gagal Pilih Visibilitas")
      if no_schedule:
          s.shot("07-visibility")
          logger.result("Radio Jadwalkan Dipilih (Tanpa Submit)", success=True)
          logger.step("Tunggu 3 detik auto-save...", indent=2)
          s.wait(3.0)
          return
     set_schedule_date(s, date_obj)
     set_schedule_time(s, time_str)
     s.shot("07-visibility")
     s.click_first(SEL_SCHEDULE_BTN, "tombol Jadwalkan")
     s.click_if_visible(SEL_CLOSE, "Tutup")
     logger.result("Jadwal Ditentukan", success=True)
     s.shot("08-scheduled")


def open_schedule_calendar(s: Studio) -> bool:
     logger = get_logger()
     vis_type = s.cfg.get("schedule_visibility_type", "PUBLISH_FROM_SPONSORS_ONLY")
     try:
         triggers = s.page.locator("#datepicker-trigger").all()
         if len(triggers) > 1:
             triggers[-1].click()
             s.wait(1500 / 1000.0)
             if s.page.locator("ytcp-scrollable-calendar").count() > 0:
                 logger.step(f"Kalender Terbuka {vis_type}", indent=2)
                 return True
     except Exception:
         pass

     try:
         s.page.evaluate("() => { const all = document.querySelectorAll('#datepicker-trigger'); if (all.length > 1) all[all.length-1].click(); else all[0].click(); }")
         s.wait(2500 / 1000.0)
         if s.page.locator("ytcp-scrollable-calendar").count() > 0:
             logger.step("Kalender Terbuka", indent=2)
             return True
     except Exception:
         pass

     logger.warning("Kalender Tidak Bisa Dibuka")
     return False


def fill_schedule_date_input(s: Studio, date_obj: dt.date, target_date_str: str) -> bool:
     logger = get_logger()
     for sel in [
         "ytcp-date-picker input[type='text']",
         "ytcp-date-picker input",
         "ytcp-scrollable-calendar input",
         "input.date-input",
         "ytcp-datetime-picker input",
     ]:
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
             return True
         except Exception:
             continue
     logger.warning("Gagal Isi Tanggal - Klik Kalender")
     return False


def click_calendar_date(s: Studio, date_obj: dt.date) -> bool:
     logger = get_logger()
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
                         return True
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
     s.shot("07-scheddate-fail")
     return False


def set_schedule_date(s: Studio, date_obj: dt.date) -> None:
     logger = get_logger()
     s.wait(2000 / 1000.0)
     if not open_schedule_calendar(s):
         return

     month_names_short = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
     target_date_str = f"{date_obj.day} {month_names_short[date_obj.month - 1]} {date_obj.year}"
     if fill_schedule_date_input(s, date_obj, target_date_str):
         return
     click_calendar_date(s, date_obj)


def set_schedule_time(s: Studio, time_str: str) -> None:
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