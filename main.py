#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys

from playwright.sync_api import TimeoutError as PWTimeout, sync_playwright

from pathlib import Path

from core.logger import get_logger, init_logger
from core.selectors import SEL_ROW, SEL_TITLE_LINK

from core.config import BASE, apply_env_overrides, load_config, validate_config
from core.helpers import find_prev_schedule_date, read_file_info, replace_number
from core.runner import process_draft
from core.steps.reuse import open_editor
from core.studio import StepError, Studio

_logger = None


def _tg_module():
    from core import thumbgen  # lazy: hanya untuk subcommand thumbnail
    return thumbgen


def build_parser() -> argparse.ArgumentParser:
     tg = _tg_module()
     ap = argparse.ArgumentParser(description="Automasi draft & generator thumbnail YouTube Studio")
     sub = ap.add_subparsers(dest="command", metavar="COMMAND", required=True)

     run_p = sub.add_parser("run", help="Jalankan automasi draft")
     run_p.add_argument("--limit", type=int, default=None, help="maks draft diproses")
     run_p.add_argument("--no-schedule", action="store_true",
                        help="Klik radio Jadwalkan saja (tanpa isi jam/tanggal, tanpa submit)")
     run_p.add_argument("--schedule-only", action="store_true",
                        help="Langsung ke visibility, isi tanggal & jam, klik Jadwalkan (tanpa edit konten)")
     run_p.add_argument("--schedule-yes", action="store_true",
                        help="Proses draft tanpa nomor, full flow + jadwalkan")
     run_p.add_argument("--verbose", action="store_true", help="enable verbose logging")

     login_p = sub.add_parser("login", help="Login ke YouTube Studio (sekali saja)")
     login_p.add_argument("--limit", type=int, default=None,
                          help="Diabaikan untuk mode login (maks draft diproses)")
     login_p.add_argument("--verbose", action="store_true", help="enable verbose logging")

     th = sub.add_parser("thumbnail", help="Buat thumbnail bernomor dari template")
     th.add_argument("template", nargs="?", choices=sorted(tg.TEMPLATES),
                     help="Key template, lihat --list")
     th.add_argument("start", nargs="?", type=int, help="Nomor awal, 0..999")
     th.add_argument("end", nargs="?", type=int, help="Nomor akhir, 0..999")
     th.add_argument("--overwrite", action="store_true", help="Timpa file yang sudah ada")
     th.add_argument("--outdir", default=None,
                     help="Folder output (default: thumbnail_dir dari config)")
     th.add_argument("--list", action="store_true", help="Tampilkan daftar template")
     th.add_argument("--self-check", action="store_true", help="Cek konfigurasi dan render digit")
     th.add_argument("--tui", action="store_true", help="Mode interaktif di terminal")
     th.add_argument("--verbose", action="store_true", help="enable verbose logging")

     return ap


def cmd_thumbnail(args, cfg: dict) -> None:
     tg = _tg_module()
     logger = get_logger()
     try:
         if args.list:
             for key in sorted(tg.TEMPLATES):
                 print(f"{tg.TEMPLATES[key]['label']} ({key})")
             return

         if args.self_check:
             tg.self_check()
             return

         outdir = Path(args.outdir) if args.outdir else None
         if not outdir:
             outdir = Path(BASE) / cfg.get("thumbnail_dir", "thumbnails")
         elif not outdir.is_absolute():
             outdir = Path(BASE) / outdir

         if args.tui:
             tg.run_tui(outdir=outdir)
             return

         if args.template is None or args.start is None or args.end is None:
             raise SystemExit("thumbnail: template, awal, dan akhir wajib diisi "
                              "(lihat --list, atau gunakan --tui)")

         tg.generate(args.template, args.start, args.end, args.overwrite, outdir=outdir)
     except (ValueError, FileNotFoundError, OSError) as e:
         logger.error(str(e))
         raise SystemExit(1)
     except (EOFError, KeyboardInterrupt):
         logger.warning("Dibatalkan.")
         raise SystemExit(1)


def _is_unprocessed_draft_title(title: str) -> bool:
      return not re.match(r"^\s*\d{1,4}\b", title)


def _draft_row(rows, filter_unprocessed: bool):
      if not filter_unprocessed:
          return rows.first
      for i in range(rows.count()):
          row = rows.nth(i)
          try:
              title = row.locator(SEL_TITLE_LINK).inner_text(timeout=2000).strip()
          except PWTimeout:
              continue
          if _is_unprocessed_draft_title(title):
              return row
      return None


def _accept_dialog(dialog) -> None:
      try:
          dialog.accept()
      except Exception:
          pass


def _allow_navigation(page) -> None:
      try:
          page.evaluate("""() => {
              window.onbeforeunload = null;
              window.addEventListener('beforeunload', event => event.stopImmediatePropagation(), true);
          }""")
      except Exception:
          pass


def main() -> None:
     global _logger
     ap = build_parser()
     args = ap.parse_args()

     cfg = load_config()
     cfg = apply_env_overrides(cfg)
     validate_config(cfg)

     log_file = os.path.join(cfg.get("logs_dir", "logs"), "yt_auto.log")
     _logger = init_logger(name="YT-AUTO", log_file=log_file, verbose=args.verbose)

     if args.command == "thumbnail":
         try:
             cmd_thumbnail(args, cfg)
         finally:
             _logger.close()
         return

     _logger.section("BITS YouTube Automation")
     _logger.info(f"Mode : {args.command}")
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
     page.on("dialog", _accept_dialog)

     s = None
     try:
         if args.command == "login":
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
             filter_unprocessed = args.no_schedule or args.schedule_yes
             row = _draft_row(rows, filter_unprocessed)
             if row is None:
                 if filter_unprocessed:
                     nxt = page.get_by_role("button", name="Buka halaman berikutnya").first
                     try:
                         nxt.wait_for(state="visible", timeout=3000)
                         nxt.click()
                         _logger.step("Halaman berikutnya...", indent=1)
                         page.wait_for_timeout(5000)
                         rows = page.locator(SEL_ROW)
                         rows.first.wait_for(state="attached", timeout=10000)
                         continue
                     except PWTimeout:
                         _logger.success("Semua Draft Tanpa Nomor Selesai")
                         break
                 else:
                     _logger.success("Semua Draft Tanpa Nomor Selesai")
                     break

             open_editor(s, row)
             num, fname = read_file_info(s)
             if num is None:
                 _logger.error("Nomor Tidak Terbaca Dari Nama File")
                 break

             prev_num = num - 1
             prev_fname = replace_number(fname, num, prev_num) if fname else None
             if args.no_schedule:
                 _logger.step("Mode Tanpa Jadwal: Klik Radio Jadwalkan Saja", indent=1)
                 process_draft(s, num, prev_fname, None, cfg, no_schedule=True)
             elif args.schedule_only:
                 _logger.step("Mode Schedule Only: Langsung ke Visibility", indent=1)
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
                 process_draft(s, num, prev_fname, sch, cfg, schedule_only=True)
             elif args.schedule_yes:
                 _logger.step("Mode Schedule Yes: Full Flow + Jadwalkan", indent=1)
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
             else:
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
             if args.limit and done >= args.limit:
                 _logger.warning(f"Mencapai Batas Draft {args.limit}")
                 break
             page.wait_for_timeout(2000)
             if args.no_schedule or args.schedule_yes:
                 page.close(run_before_unload=False)
                 page = ctx.new_page()
                 page.on("dialog", _accept_dialog)
                 s = Studio(page, ctx, cfg)
             else:
                 _allow_navigation(page)
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
