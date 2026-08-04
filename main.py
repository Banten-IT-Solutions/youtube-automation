#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

from playwright.sync_api import sync_playwright

from core.logger import init_logger
from core.selectors import SEL_ROW

from core.config import BASE, load_config, validate_config
from core.helpers import find_prev_schedule_date, read_file_info, replace_number
from core.runner import process_draft
from core.steps.reuse import open_editor
from core.studio import StepError, Studio

_logger = None


def main() -> None:
     global _logger
     ap = argparse.ArgumentParser(description="Automasi draft YouTube Studio")
     ap.add_argument("mode", nargs="?", default="run",
                     choices=["run", "login"])
     ap.add_argument("--limit", type=int, default=None, help="maks draft diproses")
     ap.add_argument("--verbose", action="store_true", help="enable verbose logging")
     args = ap.parse_args()

     cfg = load_config()
     validate_config(cfg)

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
         headless=cfg.get("headless", True),
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
         except Exception:
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
             _logger.close()
         p.stop()


if __name__ == "__main__":
    main()
