#!/usr/bin/env bash
# Rekam langkah manual di YouTube Studio dengan profil login yang sama.
# Hasil kode Python otomatis disimpan ke capture/ lalu bisa dicocokkan dgn selector di yt_auto.py.
set -euo pipefail
cd "$(dirname "$0")"

OUT="capture/recording.py"
mkdir -p capture

if [ -n "${1:-}" ]; then
  URL="$1"
else
  URL="https://studio.youtube.com/channel/UCPTViCgyJPjWRDrDo5rBFCQ/videos/upload?filter=%5B%7B%22name%22%3A%22VISIBILITY%22%2C%22value%22%3A%5B%22DRAFT%22%5D%7D%5D&sort=%7B%22columnType%22%3A%22date%22%2C%22sortOrder%22%3A%22ASCENDING%22%7D"
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
