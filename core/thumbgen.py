#!/usr/bin/env python3
"""Pembuat thumbnail bernomor dari template PNG.

Migrasi dari tool terpisah `thumbnail-generator/` menjadi bagian dari package core.
Output JPG langsung ditulis ke folder `thumbnail_dir` (default: thumbnails/).
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import BASE
from .logger import get_logger

TEMPLATE_DIR = Path(BASE) / "templates"
FONT_PATH = "/usr/share/fonts/truetype/fira-sans/FiraSans-BlackItalic.ttf"
OUT_SIZE = (1280, 720)
JPG_RE = re.compile(r"^\d{3}.*\.jpg$", re.IGNORECASE)

TEMPLATES = {
    "minhajut-tholibin": {
        "label": "Minhajut Tholibin",
        "image": "Minhajut Tholibin.png",
        "title": "MINHAJUT THOLIBIN",
        "color": (239, 240, 243),
        "box": (864, 365, 1024, 425),
        "slots": ((0, 44), (58, 102), (116, 160)),
    },
    "risalatul-maymuniyah": {
        "label": "Risalatul Maymuniyah",
        "image": "Risalatul Maymuniyah.png",
        "title": "RISALATUL MAYMUNIYAH",
        "color": (255, 255, 255),
        "box": (687, 368, 868, 439),
        "slots": ((0, 50), (64, 118), (130, 180)),
    },
    "ibanatul-ahkam": {
        "label": "Ibanatul Ahkam",
        "image": "Ibanatul Ahkam.png",
        "title": "IBANATUL AHKAM",
        "color": (82, 36, 33),
        "box": (210, 452, 438, 525),
        "slots": ((0, 59), (84, 143), (168, 227)),
    },
    "sirrul-asror": {
        "label": "Sirrul Asror",
        "image": "Sirrul Asror.png",
        "title": "SIRRUL ASROR",
        "color": (255, 255, 255),
        "box": (685, 455, 985, 555),
        "slots": ((0, 83), (108, 191), (216, 299)),
    },
    "tafsir-jalalain": {
        "label": "Tafsir Jalalain",
        "image": "Tafsir Jalalain.png",
        "title": "TAFSIR JALALAIN",
        "color": (68, 67, 73),
        "box": (190, 445, 420, 535),
        "slots": ((0, 64), (82, 146), (164, 228)),
    },
}


def fallback_stem(title: str) -> str:
    return f" PENGAJIAN KITAB {title} - ABUYA UCI CILONGOK-Thumbnail"


def output_pattern(title: str, outdir: Path) -> str:
    if outdir.is_dir():
        files = sorted(
            p.name
            for p in outdir.iterdir()
            if JPG_RE.match(p.name) and title in p.name.upper() and "(copy)" not in p.name.lower()
        )
    else:
        files = []
    stem = files[0][3:].rsplit(".", 1)[0] if files else fallback_stem(title)
    return "{num:03d}" + stem + ".jpg"


def make_digit_sprites(config: dict) -> dict:
    box = config["box"]
    slots = config["slots"]
    color = config["color"]
    box_h = box[3] - box[1]
    render_size = 2000
    font = ImageFont.truetype(FONT_PATH, render_size)

    raw = Image.new("L", (render_size, render_size), 0)
    draw = ImageDraw.Draw(raw)
    digits = {}
    for digit in "0123456789":
        raw.paste(0, (0, 0, render_size, render_size))
        bbox = font.getbbox(digit)
        draw.text((-bbox[0], -bbox[1]), digit, font=font, fill=255)
        crop_box = raw.getbbox()
        if crop_box is None:
            raise ValueError(f"Font rendered empty digit: {digit}")
        digits[digit] = raw.crop(crop_box)

    scale = box_h / max(digit.height for digit in digits.values())
    for digit in digits.values():
        for left, right in slots:
            scale = min(scale, (right - left + 1) / digit.width)

    sprites = {}
    for digit, image in digits.items():
        size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        alpha = image.resize(size, Image.LANCZOS)
        sprite = Image.new("RGBA", size, (*color, 0))
        sprite.putalpha(alpha)
        sprites[digit] = sprite
    return sprites


def generate(template_key: str, start: int, end: int,
             overwrite: bool = False, outdir: Path | str | None = None) -> None:
    if start < 0 or end < start or end > 999:
        raise ValueError("Range harus 0..999 dan END harus >= START")

    config = TEMPLATES[template_key]
    template_path = TEMPLATE_DIR / config["image"]
    if not template_path.exists():
        raise FileNotFoundError(template_path)

    outdir = Path(outdir) if outdir is not None else TEMPLATE_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    pattern = output_pattern(config["title"], outdir)
    sprites = make_digit_sprites(config)

    logger = get_logger()
    logger.action("Membuat Thumbnail", f"{config['label']} {start:03d}-{end:03d} -> {outdir}")

    with Image.open(template_path) as template:
        if template.size != OUT_SIZE:
            template = template.resize(OUT_SIZE, Image.LANCZOS)
        template = template.convert("RGBA")

        success = 0
        skipped = 0
        for num in range(start, end + 1):
            out_name = pattern.format(num=num)
            out_path = outdir / out_name
            if out_path.exists() and not overwrite:
                logger.info(f"{out_name}: LEWATI (sudah ada)")
                skipped += 1
                continue

            image = template.copy()
            target = f"{num:03d}"
            box = config["box"]
            for pos, digit in enumerate(target):
                sprite = sprites[digit]
                left, right = config["slots"][pos]
                px = box[0] + left + (right - left + 1 - sprite.width) // 2
                py = box[1] + (box[3] - box[1] - sprite.height) // 2
                image.paste(sprite, (px, py), sprite)

            image.convert("RGB").save(out_path, quality=85, optimize=True)
            logger.success(f"{out_name}: BERHASIL ({out_path.stat().st_size / 1024:.1f} KB)")
            success += 1
    logger.result(f"Selesai. {success} dibuat, {skipped} dilewati.")


def self_check() -> None:
    logger = get_logger()
    if not TEMPLATE_DIR.is_dir():
        raise FileNotFoundError(TEMPLATE_DIR)
    assert len(TEMPLATES) == 5
    for key, config in TEMPLATES.items():
        if not (TEMPLATE_DIR / config["image"]).exists():
            raise FileNotFoundError(TEMPLATE_DIR / config["image"])
        assert len(config["slots"]) == 3, key
        assert all(len(slot) == 2 for slot in config["slots"]), key
        assert len(make_digit_sprites(config)) == 10, key
    logger.success("Cek berhasil")


def _ask_int(prompt: str, min_value: int = 0, max_value: int = 999) -> int:
    while True:
        value = input(prompt).strip()
        try:
            number = int(value)
        except ValueError:
            print("Masukkan angka.")
            continue
        if min_value <= number <= max_value:
            return number
        print(f"Masukkan angka {min_value}..{max_value}.")


def _ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        value = input(f"{prompt} {suffix} ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Jawab y atau n.")


def run_tui(outdir: Path | str | None = None) -> None:
    keys = sorted(TEMPLATES)
    print("BITS Thumbnail Generator")
    print("\nTemplate:")
    for index, key in enumerate(keys, 1):
        print(f"  {index}. {TEMPLATES[key]['label']}")

    print()
    choice = _ask_int("Pilih: ", 1, len(keys))
    start = _ask_int("Awal: ")
    end = _ask_int("Akhir: ")
    overwrite = _ask_yes_no("Timpa?", False)
    generate(keys[choice - 1], start, end, overwrite, outdir=outdir)
