#!/usr/bin/env python3
"""Abstraksi interaksi dasar dengan halaman YouTube Studio."""

from __future__ import annotations

import os

from playwright.sync_api import (
    BrowserContext,
    Locator,
    Page,
    TimeoutError as PWTimeout,
)

from .logger import LOG

from .config import DEFAULT_WAIT_AFTER_MS


class StepError(Exception):
    pass


class Studio:
    def __init__(self, page: Page, ctx: BrowserContext, cfg: dict) -> None:
        self.page = page
        self.ctx = ctx
        self.cfg = cfg
        self.shots = os.path.join(cfg.get("logs_dir", "logs"), "screenshots")
        self.wa = cfg.get("wait_after_action_ms", DEFAULT_WAIT_AFTER_MS) / 1000.0

    def wait(self, t: float | None = None) -> None:
        self.page.wait_for_timeout(int((t if t is not None else self.wa) * 1000))

    def shot(self, name: str, force: bool = False) -> None:
        if not force and not self.cfg.get("screenshots", False):
            return
        try:
            os.makedirs(self.shots, exist_ok=True)
            self.page.screenshot(path=os.path.join(self.shots, name + ".png"))
        except Exception:
            pass

    def click_first(self, selectors: list[str], name: str, timeout: int = 12000) -> Locator:
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

    def click_if_visible(self, selectors: list[str], name: str, timeout: int = 4000) -> bool:
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

    def role_click(self, name: str, exact: bool = True, nth: int = 0, timeout: int = 12000) -> None:
        loc = self.page.get_by_role("button", name=name, exact=exact).nth(nth)
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        LOG("  klik:", name)
        self.wait()

    def role_fill(self, name: str, text: str, exact: bool = True) -> None:
        loc = self.page.get_by_role("textbox", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=15000)
        loc.fill(text)
        LOG("  isi:", name, "=", text[:40])
        self.wait()

    def role_text(self, name: str, exact: bool = True) -> str:
        loc = self.page.get_by_role("textbox", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=15000)
        try:
            return loc.input_value()
        except Exception:
            return loc.inner_text()

    def radio_click(self, name: str, exact: bool = True) -> None:
        loc = self.page.get_by_role("radio", name=name, exact=exact).first
        loc.wait_for(state="visible", timeout=6000)
        loc.click()
        LOG("  radio:", name)
        self.wait()

    def text_click(self, text: str, exact: bool = True, nth: int = 0, timeout: int = 6000) -> None:
        loc = self.page.get_by_text(text, exact=exact).nth(nth)
        loc.wait_for(state="visible", timeout=timeout)
        try:
            loc.click()
        except Exception:
            loc.click(force=True)
        LOG("  klik teks:", text)
        self.wait()
