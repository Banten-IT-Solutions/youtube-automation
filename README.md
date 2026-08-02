# Automasi Draft YouTube Studio

Tool untuk otomatis mengedit & menjadwalkan draft video di YouTube Studio
sesuai alur rutin Anda (reuse detail, ganti angka judul/deskripsi, thumbnail,
AI=Tidak, tanggal perekaman hari ini, monetisasi, rating, layar akhir, kartu
playlist, lalu jadwalkan).

## Prasyarat
- Python 3.11+ (sudah disiapkan venv)
- Google Chrome terpasang (tool memakai `channel="chrome"`)
- Sudah login YouTube di browser ini

## Setup
```bash
cd ~/yt-auto
.venv/bin/python -m playwright install chromium   # (tidak wajib, karena pakai chrome system)
```

### 1. Login (sekali saja)
```bash
.venv/bin/python yt_auto.py login
```
Browser terbuka ke studio.youtube.com. Login manual, lalu tekan Enter di
terminal. Profil login tersimpan di folder `profile/` (sesi tidak perlu login
ulang di run berikutnya).

### 1b. Rekam langkah manual untuk memastikan selector benar
```bash
./capture.sh
```
- Browser terbuka (pakai profil login yang sama). Jendela *Playwright Inspector*
  menampilkan aksi yang direkam secara real-time.
- Lakukan 1 alur lengkap secara manual (edit draft → jadwalkan).
- Tutup jendela Inspector. Hasil kode Python tersimpan di `capture/recording.py`.
- Cocokkan selector hasil rekaman dengan daftar `SEL_*` di `yt_auto.py`;
  jika ada selisih, ganti daftar tersebut lalu jalankan `dryrun` + `--limit 1`.

### 2. Lihat daftar draft
```bash
.venv/bin/python yt_auto.py list
```
Menampilkan judul draft sesuai urutan list. Cek nomor di tiap judul.

### 3. Uji coba (dry-run) - tidak mengklik apa pun
```bash
.venv/bin/python yt_auto.py dryrun
```

### 4. Jalankan otomatis penuh
```bash
.venv/bin/python yt_auto.py run
```
- Proses draft satu per satu sesuai urutan list (ASCENDING = paling lama dulu).
- Nomor di judul dibaca otomatis; misal draft `123 ...`, maka video prev = `122`.
- Judul/deskripsi: angka `prev` diganti jadi `num`.
- Thumbnail dicari di folder `thumbnails/` dengan nama mulai `123...`.
- Tanggal jadwal = tanggal jadwal video prev (dibaca dari daftar terjadwal di
  YouTube Studio) + `schedule_offset_days` (default 7), jam `schedule_time`
  (default 20:00). Jika tanggal prev tidak ditemukan, berikan `--last-date`.
- Alur sudah disesuaikan persis dengan rekaman: tombol `Detail`, `Gunakan kembali
  detail`, textbox judul/deskripsi, `Upload file`, `Tampilkan setelan lanjutan`,
  radio AI `Tidak`, datepicker `Tanggal perekaman`, `.m10n-text` + radio `Aktif` +
  `Selesai`, rating, `Impor dari video`, `#cards-button` + opsi Playlist,
  lalu Jadwalkan (2x `Berikutnya` → `Pilih tanggal untuk membuat` → radio
  `Dari khusus pelanggan ke` → datepicker bulan → waktu `20.00`).

Proses satu draft tertentu saja:
```bash
.venv/bin/python yt_auto.py run --num 121
```
Batas jumlah draft:
```bash
.venv/bin/python yt_auto.py run --limit 1
```
Tentukan titik awal (last video & tanggalnya) langsung dari CLI:
```bash
.venv/bin/python yt_auto.py run --last-date 2027-07-09
```
- `--last-date`: tanggal jadwal video prev, format `YYYY-MM-DD` (draft berikutnya = `+schedule_offset_days`).
- Dipakai sebagai fallback bila tanggal video prev tidak ditemukan di daftar terjadwal.

## Konfigurasi (`config.json`)
| Kunci | Arti |
|---|---|
| `studio_url` | URL daftar draft (filter DRAFT, sort date ASCENDING) |
| `thumbnail_dir` | Folder berisi file thumbnail (nama file mulai nomor video) |
| `playlists` | Daftar nama playlist (fallback pencocokan substring judul) |
| `playlist_keywords` | Map nama playlist → kata kunci di judul (lebih akurat, mengatasi beda ejaan) |
| `schedule_offset_days` | Selisih hari jadwal dari video sebelumnya (default 7) |
| `schedule_time` | Jam jadwal (default `20:00`) |
| `date_format` | Format tanggal di form (Indonesia: `%d/%m/%Y`) |
| `pause_between_drafts` | `true` = berhenti minta Enter tiap selesai 1 draft |

## Jika ada langkah gagal
- Screenshot tersimpan di `logs/shots/*.png` (nama sesuai langkah).
- Dapatkan selector yang tepat dengan:
  ```bash
  .venv/bin/python -m playwright codegen "https://studio.youtube.com/"
  ```
  lalu salin selector ke daftar `SEL_*` di bagian atas `yt_auto.py`.
- Log alur lengkap tercetak di terminal.

## Peringatan
- Semua aksi ini melanggar ToS YouTube Studio jika menyalahgunakan; gunakan
  sesuai alur manual biasa Anda (ini hanya mengotomasi klik yang sama).
- Jalankan `dryrun` dan `--limit 1` dulu sebelum full run.
