# BITS YouTube Automation

Tool otomasi Python untuk memproses draft video YouTube Studio secara berurutan — dibuat untuk mempercepat alur publish video pengajian kitab dengan detail yang konsisten.

## ✨ Fitur

- Satu script utama: `yt_auto.py`
- **Salin detail video lama** (reuse judul, deskripsi, setting)
- **Ubah judul & deskripsi** dengan nomor episode auto-increment
- **Unggah gambar sampul** otomatis dari folder `thumbnails/`
- Pengaturan lanjutan + **monetisasi & rating**
- **Atur elemen video**: end screen (dari video terbaru) + kartu playlist
- **Tentukan jadwal publikasi** (tanggal = video sebelumnya + `schedule_offset_days`)
- Logging user-friendly: emoji, warna, progress tracking, summary report

## ⚡ Quick Start

```bash
# 1. Setup (buat venv + install Playwright + Chromium)
bash setup.sh

# 2. Login ke YouTube Studio (sekali saja)
bash run.sh login

# 3. Test 1 draft, lalu jalankan
bash run.sh test
bash run.sh run 10
```

> Alternatif: `make setup` / `make login` / `make test` / `make run LIMIT=10`, atau Docker (`docker-compose build`).

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
| `playlists` / `playlist_keywords` | Nama playlist & kata kunci untuk kartu |
| `schedule_offset_days` | Selisih hari jadwal dari video sebelumnya (default: 7) |
| `schedule_time` | Jam jadwal (default: `20:00`) |
| `schedule_visibility_type` | `PUBLISH_FROM_SPONSORS_ONLY` atau `PUBLIC` |
| `date_format` | Format tanggal di form (`%d/%m/%Y`) |
| `pause_between_drafts` | `true` = pause minta Enter tiap draft |
| `wait_after_action_ms` | Delay setelah tiap aksi (default: 700ms) |
| `screenshots` | `true` = simpan screenshot per-step (debug). `FAIL` saat error selalu diambil |

## 📁 Struktur Folder

```
youtube-automation/
├── yt_auto.py          # Script utama
├── logger.py           # Modul logging user-friendly
├── config.json         # Konfigurasi
├── docs/               # Dokumentasi lengkap
├── profile/            # Sesi login (JANGAN di-commit!)
├── thumbnails/         # File gambar sampul
├── logs/               # Log & screenshots otomatis
└── setup.sh / run.sh / Makefile / Dockerfile   # Alat bantu
```

## 🚨 Ada Masalah?

Lihat [`docs/troubleshooting.md`](docs/troubleshooting.md) — berisi solusi untuk semua error umum (setup, login, runtime, config, performa, Docker). Screenshot `FAIL.png` di `logs/shots/` selalu tersedia saat error.

## 🔐 Keamanan

- `profile/` berisi session login — **jangan di-commit ke git**
- `config.json` berisi `studio_url` — **jaga kerahasiaan**
- `.gitignore` & `.dockerignore` sudah mengabaikan folder sensitif

---

**Lisensi:** Internal use.
