# Troubleshooting & FAQ

Jawaban untuk masalah yang paling sering terjadi, dikelompokkan per kategori.

---

## 📋 Daftar Isi

1. [Setup Issues](#setup-issues)
2. [Login Issues](#login-issues)
3. [Runtime Issues](#runtime-issues)
4. [Configuration Issues](#configuration-issues)
5. [Performance Issues](#performance-issues)
6. [Docker Issues](#docker-issues)
7. [Masih Gagal?](#masih-gagal)

---

## Setup Issues

### ❌ "Python 3.11 not found"

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv

# macOS (Homebrew)
brew install python@3.11

# Windows: download dari https://www.python.org/downloads/
# Pastikan "Add Python to PATH" di-check
```

**Verify:** `python3 --version` → harus 3.11+

### ❌ "make: command not found"

Gunakan bash script sebagai gantinya:

```bash
bash setup.sh        # Install
bash run.sh test     # Test
bash run.sh run      # Run
```

Atau install make:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install
```

### ❌ "Virtual environment creation failed"

```bash
rm -rf .venv                                   # 1. Hapus yang lama
python3 -m venv .venv                          # 2. Buat ulang
source .venv/bin/activate                      # 3. Aktifkan (Windows: .venv\Scripts\activate)
pip install --upgrade pip setuptools wheel     # 4. Upgrade pip
pip install -r requirements.txt                # 5. Install requirements
```

### ❌ "Playwright installation failed"

```bash
pip install --upgrade pip
pip install playwright
python -m playwright install chromium && python -m playwright install chrome
python -m playwright --version                 # Verify
```

### ❌ "Chromium not found"

```bash
python -m playwright install chromium
python -m playwright install chrome

# Verify
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print('OK'); p.stop()"
```

---

## Login Issues

### ❌ "Login browser tidak terbuka"

```bash
# 1. Cek display (Linux/Mac)
echo $DISPLAY

# 2. Jika kosong, set X11
export DISPLAY=:0
bash run.sh login
```

### ❌ "Login timeout"

```bash
# Pastikan tekan Enter SETELAH login berhasil di browser
bash run.sh login

# Jika masih gagal, login ulang
rm -rf profile/
bash run.sh login
```

### ❌ "Login session tidak tersimpan"

```bash
# 1. Pastikan folder profile/ writable
chmod -R 755 profile/

# 2. Jika masih gagal, hapus dan login ulang
rm -rf profile/
bash run.sh login

# 3. Verify
ls profile/   # Harus berisi file profile browser
```

### ❌ "Login berhasil tapi script gagal di step berikutnya"

1. Pastikan akun punya akses ke YouTube Studio
2. Test dengan `bash run.sh test`
3. Cek screenshot di `logs/screenshots/` untuk lihat step yang gagal

---

## Runtime Issues

### ❌ "Thumbnail tidak ditemukan"

```bash
# 1. Cek folder thumbnails
ls thumbnails/

# 2. Pastikan nama diawali nomor episode
# ✓ Benar: 135 PENGAJIAN KITAB RISALATUL MAYMUNIYAH-Thumbnail.jpg
# ✗ Salah: PENGAJIAN KITAB RISALATUL MAYMUNIYAH-135-Thumbnail.jpg

# 3. Rename jika perlu
mv "PENGAJIAN KITAB-135-Thumbnail.jpg" "135 PENGAJIAN KITAB-Thumbnail.jpg"
```

### ❌ "Video prev tidak ditemukan"

```
!! tanggal video prev 134 tidak ditemukan di daftar terjadwal.
   pastikan video prev sudah dijadwalkan atau jalankan draft secara berurutan.
```

1. Pastikan video sebelumnya (nomor-1) sudah di-schedule di YouTube Studio
2. Jalankan draft berurutan: `bash run.sh run`
3. Atau set `"pause_between_drafts": true` di config untuk verifikasi manual tiap draft

### ❌ "Selector tidak cocok - Automation gagal" (YouTube update UI)

```
gagal klik Detail -> selector tidak ketemu
```

1. Buka Playwright Inspector:
```bash
.venv/bin/python -m playwright codegen "https://studio.youtube.com/"
```
2. Jalankan aksi manual, copy selector yang benar
3. Update selector di `core/selectors.py`:
```python
SEL_EDIT_DRAFT_BTN = ["button[aria-label='Edit draf']", "selector_baru"]
```
4. Test ulang: `bash run.sh test`

### ❌ "Automation berhenti di tengah proses"

```
StepError: gagal klik ...
```

1. Cek screenshot di `logs/screenshots/` untuk lihat step yang gagal
2. Kemungkinan penyebab: selector berubah, network timeout, element tidak visible, session logout
3. Solusi: cek selector dengan Inspector, naikkan timeout di config, re-login dan jalankan ulang

---

## Configuration Issues

### ❌ "Jam jadwal salah - seharusnya 20:00 tapi jadi 03:00 AM"

```
Jadwal yang di-set: 20:00
Jadwal di YouTube Studio: 03:00 (keesokan hari)
```

**Penyebab:** Timezone browser tidak sesuai dengan timezone channel YouTube.

**Solusi:**
1. Tentukan timezone channel YouTube Anda (misal: Asia/Jakarta, Asia/Bangkok)
2. Update `config.json`:
```json
{
  "timezone": "Asia/Jakarta"
}
```
3. Jika menggunakan Docker, update `docker-compose.yml`:
```yaml
environment:
  - TZ=Asia/Jakarta
```
4. Jalankan ulang: `bash run.sh run --limit 1`

**IANA Timezone Examples:**
- Indonesia (WIB): `Asia/Jakarta`
- Thailand: `Asia/Bangkok`
- Filipina: `Asia/Manila`
- USA Eastern: `America/New_York`
- USA Pacific: `America/Los_Angeles`

[Daftar lengkap IANA timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

### ❌ "Video sebelumnya tidak ditemukan di dialog reuse"

```
❌ Video Sebelumnya '100 PENGAJIAN KITAB SIRRUL ASROR - ABUYA UCI CILONGOK' 
   Tidak Ditemukan di Dialog Reuse
```

**Penyebab:** Video sebelumnya tidak muncul di list awal dialog reuse. Mungkin:
- Video sudah lama dan tersembunyi di halaman awal
- Dialog reuse hanya menampilkan recent videos

**Solusi:**
1. Dialog reuse memiliki search box — automation akan mencari otomatis via search
2. Pastikan video sebelumnya sudah **dijadwalkan** di YouTube Studio
3. Jika search masih gagal:
   - Buka YouTube Studio manual
   - Klik "Gunakan kembali detail"
   - Cari video di search box manual
   - Verifikasi video ada dan visible

### ❌ "studio_url tidak valid"

```
goto() error: net::ERR_INVALID_URL
```

1. Buka https://studio.youtube.com/
2. Ke: Videos > Uploads, Filter: Draft, Sort: Ascending
3. Copy URL dari address bar
4. Update di `config.json`:
```json
{
  "studio_url": "https://studio.youtube.com/channel/YOUR_CHANNEL_ID/videos/upload?filter=..."
}
```

### ❌ "Playlist tidak ditemukan"

```
!! playlist tidak ketemu di hasil - cek manual
```

1. Update `playlist_keywords` di `config.json`:
```json
{
  "playlist_keywords": {
    "Nama Playlist": ["kata kunci 1", "kata kunci 2"]
  }
}
```
2. Atau tambahkan ke array `playlists`
3. Test dengan 1 draft: `bash run.sh test`

### ❌ "Schedule date tidak valid"

```
!! tanggal jadwal tidak ter-set - cek manual
```

1. Pastikan `date_format` sesuai: `"date_format": "%d/%m/%Y"` (Indonesia: DD/MM/YYYY)
2. Verify tanggal video prev sudah dijadwalkan
3. Naikkan `"wait_after_action_ms": 1000` jika element belum muncul

---

## Performance Issues

### ❌ "Automation terlalu cepat - selectors tidak ketemu"

Naikkan wait time di `config.json`:

```json
{
  "wait_after_action_ms": 1000
}
```

### ❌ "Automation terlalu lambat"

```json
{
  "wait_after_action_ms": 500
}
```

Matikan screenshot per-step (hemat disk + waktu):

```json
{
  "screenshots": false
}
```

> Screenshot `FAIL` saat error **tetap diambil** sebagai bukti, apapun seting ini.

---

## Docker Issues

### ❌ "Cannot connect to Docker daemon"

```bash
# Linux
sudo systemctl start docker

# macOS
open -a Docker

# Windows
# Buka Docker Desktop dari Start Menu

docker ps   # Verify Docker running
```

### ❌ "Docker image build failed"

```bash
docker --version                 # Harus 20.10+
docker system prune -a           # Bersihkan cache
docker-compose build --no-cache  # Rebuild
```

### ❌ "Chromium not found di Docker"

```bash
docker-compose build --no-cache
```

### ❌ "Docker volume permission denied"

```bash
# Linux: tambahkan user ke group docker
sudo usermod -aG docker $USER
newgrp docker

# Atau gunakan sudo
sudo docker-compose up
```

---

## Masih Gagal?

### Debug Steps

```bash
# 1. Cek log
cat logs/screenshots/FAIL.png           # Screenshot error (selalu ada saat gagal)
tail -f logs/yt_auto.log          # Live log

# 2. Test dengan 1 draft
bash run.sh test

# 3. Cek status
bash run.sh status

# 4. Run dengan verbose
.venv/bin/python main.py run --limit 1 --verbose

# 5. Cek selector
.venv/bin/python -m playwright codegen "https://studio.youtube.com/"
```

### Kumpulkan Info Debug

```bash
mkdir debug_report
cp logs/screenshots/* debug_report/
cp config.json debug_report/
tar -czf debug_report.tar.gz debug_report/
```

---

## 📝 Ringkasan Solusi Cepat

| Issue | Solusi |
|---|---|
| Python tidak ditemukan | Install Python 3.11+ |
| Virtual env error | `rm -rf .venv && bash setup.sh` |
| Chromium tidak ada | `python -m playwright install chromium` |
| Login gagal | `rm -rf profile && bash run.sh login` |
| Thumbnail tidak ketemu | Pastikan nama file diawali nomor episode |
| Video prev tidak ada | Jadwalkan video prev terlebih dahulu |
| Jam jadwal salah (03:00 bukan 20:00) | Set `"timezone"` di config sesuai channel timezone |
| Video sebelumnya tidak ketemu di reuse | Dialog reuse punya search — automation akan cari otomatis |
| Selector error | Buka Playwright Inspector & update selector |
| Terlalu lambat | Kurangi `wait_after_action_ms` |
| Terlalu cepat | Naikkan `wait_after_action_ms` |
