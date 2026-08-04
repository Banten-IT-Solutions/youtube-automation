# BITS YouTube Automation

Tool otomasi Python untuk memproses draft video YouTube Studio secara berurutan — dibuat untuk mempercepat alur publish video pengajian kitab dengan detail yang konsisten.

## ✨ Fitur

- Satu script utama: `main.py`
- **Salin detail video lama** (reuse judul, deskripsi, setting)
- **Ubah judul & deskripsi** dengan nomor episode auto-increment
- **Unggah gambar sampul** otomatis dari folder `thumbnails/`
- **Generator thumbnail** bawaan: `main.py thumbnail <template> <awal> <akhir>` langsung ke `thumbnails/`
- Pengaturan lanjutan + **monetisasi & rating**
- **Atur elemen video**: end screen (dari video terbaru) + kartu playlist
- **Tentukan jadwal publikasi** (tanggal = video sebelumnya + `schedule_offset_days`)
- Logging user-friendly: emoji, warna, progress tracking, summary report

## ⚡ Quick Start

Pilih salah satu metode di bawah ini. Instruksi lengkap di [`docs/setup.md`](docs/setup.md).

### Metode 1 — Lokal (venv)

```bash
# 1. Setup (buat venv + install Playwright + Chromium)
bash setup.sh

# 2. Login ke YouTube Studio (sekali saja)
bash run.sh login

# 3. Test 1 draft, lalu jalankan
bash run.sh test
bash run.sh run 10
```

### Metode 1b — Lokal dengan Makefile

Semua perintah di atas bisa dipakai lewat `make` (pastikan `make` terinstall):

```bash
make setup          # setup: venv + dependencies + Chromium
make login          # login ke YouTube Studio (sekali saja)
make test           # test dengan 1 draft
make run            # jalankan semua draft
make run LIMIT=10   # jalankan 10 draft
make status         # cek status setup
make help           # tampilkan semua perintah
```

### Generate Thumbnail

Generator thumbnail sudah tergabung. Output langsung ke folder `thumbnails/` (dibaca otomatis saat upload sampul):

```bash
make thumbnail-list                    # daftar template
make thumbnail TEMPLATE=ibanatul-ahkam START=1 END=10
make thumbnail TEMPLATE=tafsir-jalalain START=25 END=30 OVERWRITE=1

# atau lewat main.py
python main.py thumbnail ibanatul-ahkam 1 10
python main.py thumbnail tafsir-jalalain 25 30 --overwrite
python main.py thumbnail --tui    # mode interaktif
python main.py thumbnail --list
python main.py thumbnail --self-check
```

Template yang tersedia: `ibanatul-ahkam`, `minhajut-tholibin`, `risalatul-maymuniyah`, `sirrul-asror`, `tafsir-jalalain`. File PNG template berada di `templates/`; font Fira Sans diunduh otomatis saat `setup.sh`.

### Metode 2 — Docker

```bash
# 1. Build image
docker-compose build

# 2. Login (sekali saja, session tersimpan di profile/)
docker-compose run --rm youtube-automation python main.py login

# 3. Jalankan
docker-compose run --rm youtube-automation python main.py run --limit 5
docker-compose run --rm youtube-automation python main.py run
```

> Volume Docker otomatis memakai folder lokal (`profile/`, `thumbnails/`, `logs/`, `config.json`) — jadi login sekali di Docker tetap berlaku di run berikutnya.

**Lokal vs Docker:**

| Aspek | Lokal (venv / make) | Docker |
|-------|---------------------|--------|
| Setup | `bash setup.sh` / `make setup` | `docker-compose build` |
| Login | `bash run.sh login` / `make login` | `docker-compose run --rm ... login` |
| Run | `bash run.sh run 10` / `make run LIMIT=10` | `docker-compose run --rm ... run --limit 10` |
| Cocok untuk | Development / testing cepat | Production / multi-platform |

## 📚 Dokumentasi

| Dokumen | Isi |
|---------|-----|
| [`docs/setup.md`](docs/setup.md) | Setup lengkap, Docker, produksi, checklist, keamanan |
| [`docs/usage.md`](docs/usage.md) | Quick start, perintah, alur per draft, tips |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | FAQ & semua solusi error per kategori |
| [`docs/logging.md`](docs/logging.md) | Sistem logging: emoji, format, API, contoh output |

## ⚙️ Konfigurasi

Edit `config.json`:

| Kunci | Deskripsi |
|-------|-----------|
| `studio_url` | URL daftar draft (filter DRAFT, sort ASCENDING) |
| `thumbnail_dir` | Folder berisi file thumbnail |
| `playlist_keywords` | Map playlist → kata kunci untuk kartu |
| `timezone` | Timezone browser (default: `Asia/Jakarta`). Gunakan IANA timezone identifier |
| `schedule_offset_days` | Selisih hari jadwal dari video sebelumnya (default: 7) |
| `schedule_time` | Jam jadwal (default: `20:00`) — dalam timezone yang dikonfigurasi |
| `schedule_visibility_type` | `PUBLISH_FROM_SPONSORS_ONLY` atau `PUBLIC` |
| `date_format` | Format tanggal di form (`%d/%m/%Y`) |
| `pause_between_drafts` | `true` = pause minta Enter tiap draft |
| `wait_after_action_ms` | Delay setelah tiap aksi (default: 700ms) |
| `screenshots` | `true` = simpan screenshot per-step (debug). `FAIL` saat error selalu diambil |
| `headless` | `true` = browser berjalan tanpa tampilan (default). `false` = browser muncul (untuk melihat proses / debugging) |

## 📁 Struktur Folder

```
youtube-automation/
├── main.py            # Entry point (CLI + alur utama)
├── core/              # Package inti
│   ├── config.py       # Load & validasi config, konstanta
│   ├── studio.py       # Abstraksi interaksi halaman (class Studio)
│   ├── helpers.py      # Helper: tanggal, URL, thumbnail, playlist
│   ├── schedule.py     # Step penjadwalan publikasi
│   ├── logger.py       # Modul logging user-friendly
│   ├── selectors.py # Daftar selector UI YouTube Studio
│   ├── runner.py       # Orkestrasi proses satu draft
│   └── steps/          # Step per fitur
│       ├── reuse.py    # Buka editor + salin detail video lama
│       ├── details.py  # Judul/deskripsi + thumbnail + pengaturan lanjutan
│       ├── monetization.py # Monetisasi & rating iklan
│       └── elements.py # End screen + kartu playlist
│   └── thumbgen.py # Generator thumbnail bernomor
├── templates/ # Template PNG sumber generator
├── config.json         # Konfigurasi
├── docs/               # Dokumentasi lengkap
├── profile/            # Sesi login (JANGAN di-commit!)
├── thumbnails/         # File gambar sampul (dibuat otomatis)
├── logs/               # Log & screenshots otomatis
├── setup.sh / run.sh / Makefile   # Alat bantu lokal
├── Dockerfile / docker-compose.yml # Alat bantu Docker
└── .dockerignore
```

## 🚨 Ada Masalah?

Lihat [`docs/troubleshooting.md`](docs/troubleshooting.md) — berisi solusi untuk semua error umum (setup, login, runtime, config, performa, Docker). Screenshot `FAIL.png` di `logs/screenshots/` selalu tersedia saat error.

## 🔐 Keamanan

- `profile/` berisi session login — **jangan di-commit ke git**
- `config.json` berisi `studio_url` — **jaga kerahasiaan**
- `.gitignore` & `.dockerignore` sudah mengabaikan folder sensitif

---

**Lisensi:** Internal use.
