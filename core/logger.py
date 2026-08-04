#!/usr/bin/env python3

import time
import os
from datetime import datetime
from enum import Enum


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"


class LogLevel(Enum):
    DEBUG = ("🔍", Color.CYAN)
    INFO = ("ℹ️", Color.BLUE)
    SUCCESS = ("✅", Color.GREEN)
    WARNING = ("⚠️", Color.YELLOW)
    ERROR = ("❌", Color.RED)
    STEP = ("▶️", Color.MAGENTA)
    PROGRESS = ("⏳", Color.CYAN)


class Logger:
    MAX_LOG_BYTES = 5 * 1024 * 1024
    BACKUP_COUNT = 5

    def __init__(self, name="YT-AUTO", log_file=None, verbose=False):
        self.name = name
        self.log_file = log_file
        self.verbose = verbose
        self.start_time = time.time()
        self.current_draft = None
        self.draft_count = 0
        self.success_count = 0
        self.error_count = 0
        self.log_lines = []
        self._file = None

        if self.log_file:
            os.makedirs(os.path.dirname(self.log_file) or ".", exist_ok=True)
            self._rotate()
            self._file = open(self.log_file, "a", encoding="utf-8")

    def _rotate(self):
        if not self.log_file or not os.path.exists(self.log_file):
            return
        try:
            if os.path.getsize(self.log_file) < self.MAX_LOG_BYTES:
                return
        except OSError:
            return
        for i in range(self.BACKUP_COUNT - 1, 0, -1):
            src = f"{self.log_file}.{i}"
            dst = f"{self.log_file}.{i + 1}"
            if os.path.exists(src):
                os.replace(src, dst)
        os.replace(self.log_file, f"{self.log_file}.1")

    def _get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def _format_log(self, level, message, indent=0):
        timestamp = self._get_timestamp()
        emoji, color = level.value
        indent_str = "  " * indent

        formatted = f"[{timestamp}] {emoji}  {indent_str}{message}"

        return formatted, color

    def _write(self, formatted, color=""):
        colored = f"{color}{formatted}{Color.RESET}"
        print(colored, flush=True)

        if self._file:
            try:
                self._file.write(formatted + "\n")
                self._file.flush()
            except Exception:
                pass

        self.log_lines.append(formatted)

    def close(self):
        if self._file:
            try:
                self._file.close()
            finally:
                self._file = None

    def info(self, message):
        formatted, color = self._format_log(LogLevel.INFO, message)
        self._write(formatted, color)

    def success(self, message):
        formatted, color = self._format_log(LogLevel.SUCCESS, message)
        self._write(formatted, color)

    def warning(self, message):
        formatted, color = self._format_log(LogLevel.WARNING, message)
        self._write(formatted, color)

    def error(self, message):
        formatted, color = self._format_log(LogLevel.ERROR, message)
        self._write(formatted, color)
        self.error_count += 1

    def debug(self, message):
        if self.verbose:
            formatted, color = self._format_log(LogLevel.DEBUG, message)
            self._write(formatted, color)

    def step(self, message, indent=0):
        formatted, color = self._format_log(LogLevel.STEP, message, indent=indent)
        self._write(formatted, color)

    def progress(self, message):
        formatted, color = self._format_log(LogLevel.PROGRESS, message)
        self._write(formatted, color)

    def section(self, title):
        line = "═" * 60
        self._write(f"\n{Color.BOLD}{Color.CYAN}{line}{Color.RESET}")
        self._write(f"{Color.BOLD}{Color.CYAN}  {title}{Color.RESET}")
        self._write(f"{Color.BOLD}{Color.CYAN}{line}{Color.RESET}\n")

    def start_draft(self, draft_num, total=None):
        self.current_draft = draft_num
        self.draft_count += 1
        total_str = f"/{total}" if total else ""
        self.progress(f"Draft {draft_num}{total_str} - Dimulai")

    def end_draft(self, draft_num, success=True):
        if success:
            self.success(f"Draft {draft_num} - Selesai ✓")
            self.success_count += 1
        else:
            self.error(f"Draft {draft_num} - Gagal ✗")
        self.current_draft = None

    def action(self, action_name, details=""):
        msg = action_name
        if details:
            msg += f" → {details}"
        self.step(msg, indent=1)

    def result(self, result_text, success=True):
        if success:
            self.step(f"✓ {result_text}", indent=2)
        else:
            self.warning(f"✗ {result_text}", )

    def separator(self):
        self._write(f"{Color.DIM}{'─' * 60}{Color.RESET}")

    def get_elapsed_time(self):
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def summary(self):
        elapsed = self.get_elapsed_time()

        self.section("RINGKASAN HASIL")

        self._write(f"  Total Draft Yang Diproses : {Color.BOLD}{self.draft_count}{Color.RESET}")
        self._write(f"  ✅ Berhasil : {Color.GREEN}{self.success_count}{Color.RESET}")
        self._write(f"  ❌ Gagal : {Color.RED}{self.error_count}{Color.RESET}")
        self._write(f"  ⏱️  Waktu total : {Color.CYAN}{elapsed}{Color.RESET}")

        if self.error_count == 0 and self.draft_count > 0:
            self._write(f"\n  {Color.GREEN}{Color.BOLD}🎉 Semua draft berhasil diproses!{Color.RESET}")
        elif self.draft_count == 0:
            self._write(f"\n  {Color.YELLOW}Tidak ada draft yang diproses.{Color.RESET}")
        else:
            success_rate = (self.success_count / self.draft_count) * 100
            self._write(f"\n  {Color.YELLOW}Tingkat sukses : {success_rate:.1f}%{Color.RESET}")

        self._write("")


_logger = None


def init_logger(name="YT-AUTO", log_file=None, verbose=False):
    global _logger
    _logger = Logger(name=name, log_file=log_file, verbose=verbose)
    return _logger


def get_logger():
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger


def LOG(*args):
    message = " ".join(str(a) for a in args)
    get_logger().debug(message)
