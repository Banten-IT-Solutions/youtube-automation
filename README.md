# BITS YouTube Automation

## Bahasa Indonesia

BITS YouTube Automation adalah tool otomasi Python untuk memproses draft video YouTube Studio secara berurutan. Tool ini dibuat untuk mempercepat alur publish video pengajian kitab dengan detail yang konsisten.

### Fitur

- Satu script utama: `yt_auto.py`
- Otomatis gunakan kembali detail dari video sebelumnya
- Edit judul & deskripsi dengan nomor episode auto-increment
- Upload thumbnail otomatis
- Set setelan lanjutan (AI, tanggal perekaman)
- Handle monetisasi & rating kesesuaian iklan
- Import end screen dari video terbaru
- Tambahkan kartu playlist otomatis di posisi 3 menit
- Jadwalkan video dengan tanggal & waktu kustom
- Proses berurutan tanpa pause atau dengan pause per draft

### Kebutuhan

- Python 3.11+
- Google Chrome terpasang
- Playwright
- Sesi login YouTube Studio (dilakukan sekali)

Install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install playwright
```

### Setup Awal

#### 1. Login YouTube Studio (Sekali Saja)

```bash
.venv/bin/python yt_auto.py login
```

Browser akan terbuka ke studio.youtube.com. Login manual, lalu tekan Enter di terminal. Sesi login tersimpan di folder `profile/` untuk penggunaan berikutnya.

#### 2. Siapkan Thumbnail

Letakkan file thumbnail di folder `thumbnails/` dengan format nama:

```text
135 PENGAJIAN KITAB RISALATUL MAYMUNIYAH - ABUYA UCI CILONGOK-Thumbnail.jpg
136 PENGAJIAN KITAB RISALATUL MAYMUNIYAH - ABUYA UCI CILONGOK-Thumbnail.jpg
```

Nama file harus diawali dengan **nomor episode** yang sesuai dengan draft.

### Penggunaan

#### Proses Semua Draft

```bash
.venv/bin/python yt_auto.py run
```

atau langsung:

```bash
.venv/bin/python yt_auto.py
```

#### Proses Dengan Limit

Proses hanya 1 draft untuk testing:

```bash
.venv/bin/python yt_auto.py run --limit 1
```

Proses 5 draft:

```bash
.venv/bin/python yt_auto.py run --limit 5
```

### Konfigurasi

Edit file `config.json`:

| Kunci | Deskripsi |
|-------|-----------|
| `studio_url` | URL daftar draft (filter DRAFT, sort ASCENDING) |
| `thumbnail_dir` | Folder berisi file thumbnail |
| `playlists` | Daftar nama playlist (fallback) |
| `playlist_keywords` | Map nama playlist → kata kunci di judul (lebih akurat) |
| `schedule_offset_days` | Selisih hari jadwal dari video sebelumnya (default: 7) |
| `schedule_time` | Jam jadwal (default: `20:00`) |
| `schedule_visibility_type` | Tipe visibility: `PUBLISH_FROM_SPONSORS_ONLY` atau `PUBLIC` |
| `date_format` | Format tanggal di form (Indonesia: `%d/%m/%Y`) |
| `pause_between_drafts` | `true` = pause minta Enter tiap draft, `false` = otomatis lanjut |
| `wait_after_action_ms` | Delay setelah setiap aksi (default: 700ms) |

Contoh `config.json`:

```json
{
  "studio_url": "https://studio.youtube.com/channel/...",
  "thumbnail_dir": "thumbnails",
  "schedule_time": "20:00",
  "schedule_offset_days": 7,
  "schedule_visibility_type": "PUBLISH_FROM_SPONSORS_ONLY",
  "pause_between_drafts": false,
  "playlist_keywords": {
    "Risalatul Maymuniyah": ["risalatul maymuniyah", "maymuniyah"],
    "Tafsir Jalalain": ["tafsir jalalain", "tafsirjalalain"]
  }
}
```

### Alur Proses Otomatis

Untuk setiap draft di daftar (sort ASCENDING = paling lama dulu):

1. **Buka editor draft** - Klik "Edit draf"
2. **Baca info** - Extract nomor episode dari nama file (misal: `135`)
3. **Cari tanggal video prev** - Cari video `134` di daftar terjadwal, ambil tanggalnya
4. **Hitung jadwal baru** - Tanggal prev + 7 hari (dari config)
5. **Gunakan kembali detail** - Pilih video `134`, salin semua detail
6. **Edit judul & deskripsi** - Ganti angka `134` → `135`
7. **Upload thumbnail** - Cari file `135...jpg` di folder thumbnails
8. **Setelan lanjutan** - AI: Tidak, Tanggal perekaman: hari ini
9. **Monetisasi** - Aktifkan monetisasi jika belum, kirim rating
10. **End screen** - Impor dari video terbaru (jika belum ada)
11. **Kartu playlist** - Tambahkan kartu di 00:03:00 (jika belum ada)
12. **Jadwalkan** - Set tanggal & waktu, pilih visibility type, lalu jadwalkan
13. **Selesai** - Kembali ke daftar draft, lanjut ke draft berikutnya

### Struktur Folder

```text
yt-auto/
├── .venv/                    # Python virtual environment
├── capture/                  # Hasil rekaman Playwright Inspector
├── logs/
│   └── shots/               # Screenshot setiap step (untuk debugging)
├── profile/                  # Sesi login Chrome (persistent)
├── thumbnails/               # File thumbnail JPG
│   ├── 135 PENGAJIAN KITAB....jpg
│   ├── 136 PENGAJIAN KITAB....jpg
│   └── ...
├── capture.sh                # Script rekam aksi manual (debugging)
├── config.json               # Konfigurasi utama
├── yt_auto.py                # Script utama
└── README.md
```

### Troubleshooting

#### Thumbnail Tidak Ditemukan

```
!! thumbnail utk 135 tidak ditemukan - LEWATI (cek thumbnails/)
```

**Solusi:** Letakkan file thumbnail dengan nama yang diawali nomor episode (misal: `135 ...jpg`) di folder `thumbnails/`.

#### Video Prev Tidak Ditemukan

```
!! tanggal video prev 134 tidak ditemukan di daftar terjadwal.
   pastikan video prev sudah dijadwalkan atau jalankan draft secara berurutan.
```

**Solusi:** Pastikan video sebelumnya (`134`) sudah di-schedule terlebih dahulu. Script membutuhkan tanggal jadwal video prev untuk menghitung jadwal video berikutnya.

#### Selector Berubah

Jika YouTube Studio update UI dan selector berubah:

1. Jalankan Playwright Inspector:
   ```bash
   .venv/bin/python -m playwright codegen "https://studio.youtube.com/"
   ```
2. Lakukan aksi manual, salin selector yang benar
3. Update selector `SEL_*` di bagian atas `yt_auto.py`

Atau gunakan script rekam:
```bash
./capture.sh
```
Hasil rekaman tersimpan di `capture/recording.py`.

### Estimasi Waktu

- **Per draft:** ~50-55 detik
- **10 draft:** ~9 menit
- **50 draft:** ~45 menit

Waktu bisa bervariasi tergantung koneksi internet dan response YouTube Studio.

### Catatan

- Tool ini melanggar ToS YouTube Studio jika disalahgunakan. Gunakan sesuai alur manual biasa Anda (hanya mengotomasi klik repetitif).
- Jalankan dengan `--limit 1` terlebih dahulu untuk memastikan semua selector bekerja dengan benar.
- Screenshot setiap step tersimpan di `logs/shots/` untuk debugging.
- File di folder `profile/` berisi sesi login, jangan di-commit ke git.

---

## English

BITS YouTube Automation is a Python automation tool for processing YouTube Studio draft videos sequentially. This tool is designed to speed up the video publishing workflow for Islamic lecture series with consistent details.

### Features

- Single main script: `yt_auto.py`
- Automatically reuse details from previous video
- Edit title & description with auto-increment episode numbers
- Automatic thumbnail upload
- Set advanced settings (AI, recording date)
- Handle monetization & ad suitability rating
- Import end screen from latest video
- Add playlist card automatically at 3-minute mark
- Schedule videos with custom date & time
- Process sequentially without pause or with pause per draft

### Requirements

- Python 3.11+
- Google Chrome installed
- Playwright
- YouTube Studio login session (done once)

Install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install playwright
```

### Initial Setup

#### 1. Login to YouTube Studio (Once)

```bash
.venv/bin/python yt_auto.py login
```

Browser will open to studio.youtube.com. Login manually, then press Enter in the terminal. Login session is saved in `profile/` folder for future use.

#### 2. Prepare Thumbnails

Place thumbnail files in `thumbnails/` folder with naming format:

```text
135 PENGAJIAN KITAB RISALATUL MAYMUNIYAH - ABUYA UCI CILONGOK-Thumbnail.jpg
136 PENGAJIAN KITAB RISALATUL MAYMUNIYAH - ABUYA UCI CILONGOK-Thumbnail.jpg
```

Filename must start with the **episode number** matching the draft.

### Usage

#### Process All Drafts

```bash
.venv/bin/python yt_auto.py run
```

or directly:

```bash
.venv/bin/python yt_auto.py
```

#### Process With Limit

Process only 1 draft for testing:

```bash
.venv/bin/python yt_auto.py run --limit 1
```

Process 5 drafts:

```bash
.venv/bin/python yt_auto.py run --limit 5
```

### Configuration

Edit `config.json` file:

| Key | Description |
|-----|-------------|
| `studio_url` | Draft list URL (filter DRAFT, sort ASCENDING) |
| `thumbnail_dir` | Folder containing thumbnail files |
| `playlists` | List of playlist names (fallback) |
| `playlist_keywords` | Map playlist name → keywords in title (more accurate) |
| `schedule_offset_days` | Day offset from previous video schedule (default: 7) |
| `schedule_time` | Schedule time (default: `20:00`) |
| `schedule_visibility_type` | Visibility type: `PUBLISH_FROM_SPONSORS_ONLY` or `PUBLIC` |
| `date_format` | Date format in form (Indonesia: `%d/%m/%Y`) |
| `pause_between_drafts` | `true` = pause for Enter per draft, `false` = auto continue |
| `wait_after_action_ms` | Delay after each action (default: 700ms) |

Example `config.json`:

```json
{
  "studio_url": "https://studio.youtube.com/channel/...",
  "thumbnail_dir": "thumbnails",
  "schedule_time": "20:00",
  "schedule_offset_days": 7,
  "schedule_visibility_type": "PUBLISH_FROM_SPONSORS_ONLY",
  "pause_between_drafts": false,
  "playlist_keywords": {
    "Risalatul Maymuniyah": ["risalatul maymuniyah", "maymuniyah"],
    "Tafsir Jalalain": ["tafsir jalalain", "tafsirjalalain"]
  }
}
```

### Automation Flow

For each draft in the list (sort ASCENDING = oldest first):

1. **Open draft editor** - Click "Edit draft"
2. **Read info** - Extract episode number from filename (e.g., `135`)
3. **Find prev video date** - Search video `134` in scheduled list, get its date
4. **Calculate new schedule** - Prev date + 7 days (from config)
5. **Reuse details** - Select video `134`, copy all details
6. **Edit title & description** - Replace number `134` → `135`
7. **Upload thumbnail** - Find file `135...jpg` in thumbnails folder
8. **Advanced settings** - AI: No, Recording date: today
9. **Monetization** - Enable monetization if not yet, submit rating
10. **End screen** - Import from latest video (if not already exists)
11. **Playlist card** - Add card at 00:03:00 (if not already exists)
12. **Schedule** - Set date & time, choose visibility type, then schedule
13. **Done** - Return to draft list, continue to next draft

### Folder Structure

```text
yt-auto/
├── .venv/                    # Python virtual environment
├── capture/                  # Playwright Inspector recording results
├── logs/
│   └── shots/               # Screenshot of each step (for debugging)
├── profile/                  # Chrome login session (persistent)
├── thumbnails/               # JPG thumbnail files
│   ├── 135 PENGAJIAN KITAB....jpg
│   ├── 136 PENGAJIAN KITAB....jpg
│   └── ...
├── capture.sh                # Script to record manual actions (debugging)
├── config.json               # Main configuration
├── yt_auto.py                # Main script
└── README.md
```

### Troubleshooting

#### Thumbnail Not Found

```
!! thumbnail utk 135 tidak ditemukan - LEWATI (cek thumbnails/)
```

**Solution:** Place thumbnail file with name starting with episode number (e.g., `135 ...jpg`) in `thumbnails/` folder.

#### Prev Video Not Found

```
!! tanggal video prev 134 tidak ditemukan di daftar terjadwal.
   pastikan video prev sudah dijadwalkan atau jalankan draft secara berurutan.
```

**Solution:** Ensure previous video (`134`) is already scheduled. Script needs prev video's schedule date to calculate next video's schedule.

#### Selector Changed

If YouTube Studio updates UI and selectors change:

1. Run Playwright Inspector:
   ```bash
   .venv/bin/python -m playwright codegen "https://studio.youtube.com/"
   ```
2. Perform manual actions, copy correct selector
3. Update `SEL_*` selector at the top of `yt_auto.py`

Or use recording script:
```bash
./capture.sh
```
Recording result saved in `capture/recording.py`.

### Time Estimation

- **Per draft:** ~50-55 seconds
- **10 drafts:** ~9 minutes
- **50 drafts:** ~45 minutes

Time may vary depending on internet connection and YouTube Studio response.

### Notes

- This tool violates YouTube Studio ToS if misused. Use it according to your normal manual workflow (only automates repetitive clicks).
- Run with `--limit 1` first to ensure all selectors work correctly.
- Screenshots of each step are saved in `logs/shots/` for debugging.
- Files in `profile/` folder contain login session, do not commit to git.
