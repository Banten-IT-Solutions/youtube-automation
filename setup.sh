#!/bin/bash

set -e

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$BASE/.venv"

echo "=========================================="
echo "BITS YouTube Automation - Setup"
echo "=========================================="
echo ""

# 1. Create virtual environment
if [ ! -d "$VENV" ]; then
    echo "[1/4] Membuat virtual environment..."
    python3 -m venv "$VENV"
else
    echo "[1/4] Virtual environment sudah ada"
fi

# 2. Activate and upgrade pip
echo "[2/4] Upgrade pip..."
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# 3. Install dependencies
echo "[3/4] Install dependencies..."
"$VENV/bin/python" -m pip install -q -r "$BASE/requirements.txt"

# 4. Install Chromium
echo "[4/4] Install Chromium untuk Playwright..."
"$VENV/bin/python" -m playwright install chromium

echo ""
echo "=========================================="
echo "✓ Setup selesai!"
echo "=========================================="
echo ""
echo "Langkah selanjutnya:"
echo ""
echo "1. LOGIN (sekali saja):"
echo "   $VENV/bin/python yt_auto.py login"
echo ""
echo "2. JALANKAN AUTOMATION:"
echo "   $VENV/bin/python yt_auto.py run"
echo ""
echo "3. ATAU dengan limit untuk testing:"
echo "   $VENV/bin/python yt_auto.py run --limit 1"
echo ""
