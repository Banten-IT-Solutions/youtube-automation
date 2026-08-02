#!/usr/bin/env python3
"""
Logger module untuk YouTube Automation dengan format yang user-friendly.
Menyediakan logging dengan prefix, emoji, dan tracking progress.
"""

import time
import sys
import os
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Level logging dengan emoji dan warna."""
    DEBUG = ("🔍", "\033[36m")      # Cyan
    INFO = ("ℹ️", "\033[34m")       # Blue
    SUCCESS = ("✅", "\033[32m")    # Green
    WARNING = ("⚠️", "\033[33m")    # Yellow
    ERROR = ("❌", "\033[31m")      # Red
    STEP = ("▶️", "\033[35m")       # Magenta
    PROGRESS = ("⏳", "\033[36m")   # Cyan


class ColorCodes:
    """ANSI color codes untuk terminal."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BLUE = "\033[34m"


class Logger:
    """Logger dengan format user-friendly dan tracking."""
    
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
        
        # Setup log file jika diminta
        if self.log_file:
            os.makedirs(os.path.dirname(self.log_file) or ".", exist_ok=True)
    
    def _get_timestamp(self):
        """Return timestamp dengan format HH:MM:SS."""
        return datetime.now().strftime("%H:%M:%S")
    
    def _format_log(self, level, message, indent=0):
        """Format log message dengan level, timestamp, dan indentasi."""
        timestamp = self._get_timestamp()
        emoji, color = level.value
        indent_str = "  " * indent
        
        # Format: [HH:MM:SS] emoji message (dengan spacing yang rapi)
        formatted = f"[{timestamp}] {emoji}  {indent_str}{message}"
        
        return formatted, color
    
    def _write(self, formatted, color=""):
        """Tulis ke stdout dan file log."""
        # Ke stdout dengan color
        colored = f"{color}{formatted}{ColorCodes.RESET}"
        print(colored, flush=True)
        
        # Ke file log tanpa color
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(formatted + "\n")
            except Exception:
                pass
        
        self.log_lines.append(formatted)
    
    def info(self, message):
        """Log info message."""
        formatted, color = self._format_log(LogLevel.INFO, message)
        self._write(formatted, color)
    
    def success(self, message):
        """Log success message."""
        formatted, color = self._format_log(LogLevel.SUCCESS, message)
        self._write(formatted, color)
    
    def warning(self, message):
        """Log warning message."""
        formatted, color = self._format_log(LogLevel.WARNING, message)
        self._write(formatted, color)
    
    def error(self, message):
        """Log error message."""
        formatted, color = self._format_log(LogLevel.ERROR, message)
        self._write(formatted, color)
        self.error_count += 1
    
    def debug(self, message):
        """Log debug message (hanya jika verbose=True)."""
        if self.verbose:
            formatted, color = self._format_log(LogLevel.DEBUG, message)
            self._write(formatted, color)
    
    def step(self, message, indent=0):
        """Log step/action dengan indentasi."""
        formatted, color = self._format_log(LogLevel.STEP, message, indent=indent)
        self._write(formatted, color)
    
    def progress(self, message):
        """Log progress message."""
        formatted, color = self._format_log(LogLevel.PROGRESS, message)
        self._write(formatted, color)
    
    def section(self, title):
        """Log section header."""
        line = "═" * 60
        self._write(f"\n{ColorCodes.BOLD}{ColorCodes.CYAN}{line}{ColorCodes.RESET}")
        self._write(f"{ColorCodes.BOLD}{ColorCodes.CYAN}  {title}{ColorCodes.RESET}")
        self._write(f"{ColorCodes.BOLD}{ColorCodes.CYAN}{line}{ColorCodes.RESET}\n")
    
    def start_draft(self, draft_num, total=None):
        """Mulai proses draft baru."""
        self.current_draft = draft_num
        self.draft_count += 1
        total_str = f"/{total}" if total else ""
        self.progress(f"Draft {draft_num}{total_str} - Dimulai")
    
    def end_draft(self, draft_num, success=True):
        """Selesai proses draft."""
        if success:
            self.success(f"Draft {draft_num} - Selesai ✓")
            self.success_count += 1
        else:
            self.error(f"Draft {draft_num} - Gagal ✗")
        self.current_draft = None
    
    def action(self, action_name, details=""):
        """Log action/step dengan details."""
        msg = action_name
        if details:
            msg += f" → {details}"
        self.step(msg, indent=1)
    
    def result(self, result_text, success=True):
        """Log hasil aksi."""
        if success:
            self.step(f"✓ {result_text}", indent=2)
        else:
            self.warning(f"✗ {result_text}", )
    
    def separator(self):
        """Print separator line."""
        self._write(f"{ColorCodes.DIM}{'─' * 60}{ColorCodes.RESET}")
    
    def get_elapsed_time(self):
        """Return elapsed time dalam format HH:MM:SS."""
        elapsed = time.time() - self.start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def summary(self):
        """Print summary report."""
        elapsed = self.get_elapsed_time()
        
        self.section("RINGKASAN HASIL")
        
        self._write(f"  Total draft diproses: {ColorCodes.BOLD}{self.draft_count}{ColorCodes.RESET}")
        self._write(f"  ✅ Berhasil: {ColorCodes.GREEN}{self.success_count}{ColorCodes.RESET}")
        self._write(f"  ❌ Gagal: {ColorCodes.RED}{self.error_count}{ColorCodes.RESET}")
        self._write(f"  ⏱️  Waktu total: {ColorCodes.CYAN}{elapsed}{ColorCodes.RESET}")
        
        if self.error_count == 0 and self.draft_count > 0:
            self._write(f"\n  {ColorCodes.GREEN}{ColorCodes.BOLD}🎉 Semua draft berhasil diproses!{ColorCodes.RESET}")
        elif self.draft_count == 0:
            self._write(f"\n  {ColorCodes.YELLOW}Tidak ada draft yang diproses.{ColorCodes.RESET}")
        else:
            success_rate = (self.success_count / self.draft_count) * 100
            self._write(f"\n  {ColorCodes.YELLOW}Tingkat sukses: {success_rate:.1f}%{ColorCodes.RESET}")
        
        self._write("")
    
    def save_log_file(self, filepath):
        """Simpan semua log ke file."""
        try:
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(self.log_lines))
            self.success(f"Log disimpan: {filepath}")
        except Exception as e:
            self.error(f"Gagal simpan log: {e}")


# Global logger instance
_logger = None


def init_logger(name="YT-AUTO", log_file=None, verbose=False):
    """Initialize global logger."""
    global _logger
    _logger = Logger(name=name, log_file=log_file, verbose=verbose)
    return _logger


def get_logger():
    """Get global logger instance."""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger


def log(message):
    """Legacy log function untuk compatibility."""
    get_logger().info(message)


# Backward compatibility
def LOG(*args):
    """Legacy LOG function (untuk compatibility dengan kode lama)."""
    message = " ".join(str(a) for a in args)
    get_logger().debug(message)
