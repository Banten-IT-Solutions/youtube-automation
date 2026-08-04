#!/bin/bash

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$BASE/.venv"

if [ ! -d "$VENV" ]; then
    echo "❌ Virtual environment tidak ditemukan!"
    echo "Jalankan setup terlebih dahulu:"
    echo "  bash setup.sh"
    exit 1
fi

if [ "$1" == "login" ]; then
    echo "🔐 Login YouTube Studio..."
    "$VENV/bin/python" "$BASE/main.py" login
elif [ "$1" == "run" ]; then
    limit=${2:-}
    if [ -z "$limit" ]; then
        echo "🚀 Menjalankan semua draft..."
        "$VENV/bin/python" "$BASE/main.py" run
    else
        echo "🚀 Menjalankan $limit draft..."
        "$VENV/bin/python" "$BASE/main.py" run --limit "$limit"
    fi
elif [ "$1" == "test" ]; then
    echo "🧪 Test dengan 1 draft..."
    "$VENV/bin/python" "$BASE/main.py" run --limit 1
elif [ "$1" == "status" ]; then
    echo "📊 Status Setup:"
    echo ""
    if [ -d "$VENV" ]; then
        echo "✓ Virtual environment: OK"
    else
        echo "✗ Virtual environment: NOT FOUND"
    fi
    
    if [ -d "$BASE/profile" ] && [ -n "$(ls -A $BASE/profile 2>/dev/null)" ]; then
        echo "✓ Login session: OK"
    else
        echo "✗ Login session: BELUM ADA (jalankan: bash run.sh login)"
    fi
    
    if [ -d "$BASE/thumbnails" ] && [ -n "$(ls -A $BASE/thumbnails 2>/dev/null)" ]; then
        echo "✓ Thumbnail: $(ls $BASE/thumbnails | wc -l) file(s)"
    else
        echo "⚠ Thumbnail: KOSONG (letakkan file JPG di folder thumbnails/)"
    fi
    
    if [ -f "$BASE/config.json" ]; then
        echo "✓ Config: OK"
    else
        echo "✗ Config: NOT FOUND"
    fi
    echo ""
else
    echo "BITS YouTube Automation - Helper Script"
    echo ""
    echo "Penggunaan:"
    echo "  bash run.sh login              - Login ke YouTube Studio (sekali saja)"
    echo "  bash run.sh run                - Jalankan semua draft"
    echo "  bash run.sh run <N>            - Jalankan N draft (misal: bash run.sh run 5)"
    echo "  bash run.sh test               - Test dengan 1 draft"
    echo "  bash run.sh status             - Cek status setup"
    echo ""
    echo "Contoh:"
    echo "  bash run.sh login"
    echo "  bash run.sh test               # test dulu dengan 1 draft"
    echo "  bash run.sh run 10             # jalankan 10 draft"
    echo ""
fi
