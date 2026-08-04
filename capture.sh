#!/usr/bin/env bash
# Rekam langkah manual di YouTube Studio dengan profil login yang sama.
# Hasil kode Python otomatis disimpan ke capture/ lalu bisa dicocokkan dgn selector di core/selectors.py.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "❌ Virtual environment tidak ditemukan! Jalankan 'bash setup.sh' dulu."
  exit 1
fi

OUT="capture/recording.py"
mkdir -p capture

# Ambil URL studio dari config.json supaya tidak duplikat hardcode.
read_studio_url() {
  .venv/bin/python -c "import json,sys;print(json.load(open('config.json'))['studio_url'])"
}

if [ -n "${1:-}" ]; then
  URL="$1"
else
  URL="$(read_studio_url)"
fi

echo ">>> Buka inspector, lakukan langkah di Chrome, lalu TUTUP jendela inspector saat selesai."
echo ">>> Rekaman tersimpan ke: $OUT"
.venv/bin/python -m playwright codegen \
  --target python \
  --channel chrome \
  --user-agent "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" \
  --user-data-dir "$(pwd)/profile" \
  -o "$OUT" \
  "$URL"
echo ">>> Selesai. File: $OUT"
