# Setup & Deployment

Panduan lengkap instalasi, konfigurasi, dan deployment YouTube Automation.

> **Pintu masuk utama:** lihat `README.md` untuk ringkasan proyek.
> **Ada masalah?** Buka `docs/troubleshooting.md`.

---

## 1. System Requirements

| Item | Minimum |
|------|---------|
| Python | 3.11+ |
| RAM | 2GB |
| Disk | 2GB (untuk Chromium) |
| Internet | Diperlukan |

**Platform yang didukung:**
- ✅ Linux (Ubuntu 20.04+, Debian 10+)
- ✅ macOS 10.15+
- ✅ Windows 10/11 (WSL2 recommended)

---

## 2. Setup Methods (Pilih Salah Satu)

### Method A: Bash Script — Recommended untuk Pemula

Termudah dan tercepat.

```bash
# 1. Setup (buat venv + install Playwright + Chromium)
bash setup.sh

# 2. Login (sekali saja)
bash run.sh login

# 3. Jalankan
bash run.sh test        # Test 1 draft dulu
bash run.sh run 5       # Jalankan 5 draft
```

| Keuntungan | Kekurangan |
|-----------|-----------|
| Mudah digunakan | Hanya Linux/macOS |
| Semua dalam satu folder | Windows perlu WSL2 |

### Method B: Makefile — Recommended untuk Developer

```bash
make setup          # 1. Setup
make login          # 2. Login
make test           # 3. Test 1 draft
make run LIMIT=5    # 4. Jalankan 5 draft
make run            # Jalankan semua
```

### Method C: Docker — Recommended untuk Production

Terisolasi dan reproducible (cross-platform).

```bash
# 1. Build image
docker-compose build

# 2. Login (sekali saja, session tersimpan di profile/)
docker-compose run --rm youtube-automation python main.py login

# 3. Jalankan
docker-compose run --rm youtube-automation python main.py run --limit 5
docker-compose run --rm youtube-automation python main.py run
```

**Konfigurasi Docker** (`docker-compose.yml`):

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - TZ=Asia/Jakarta          # Timezone container (sesuaikan dengan timezone channel YouTube)

volumes:
  - ./profile:/app/profile
  - ./thumbnails:/app/thumbnails
  - ./logs:/app/logs
  - ./config.json:/app/config.json:ro
```

> **Penting:** `TZ` environment variable harus sesuai dengan timezone channel YouTube Anda. Browser juga dikonfigurasi timezone via `timezone` di `config.json` untuk pastikan dropdown jadwal menampilkan waktu yang benar.

**Perbandingan Docker vs Native:**

| Aspek | Docker | Native |
|---|---|---|
| Setup | Lebih kompleks | Lebih sederhana |
| Dependencies | Terisolasi | Langsung di sistem |
| Portability | Multi-platform | Platform-dependent |
| Performance | Sedikit lebih lambat | Optimal |
| Penggunaan | Production | Development |

### Method D: Manual Python — Advanced

```bash
python3 -m venv .venv
source .venv/bin/activate          # Linux/macOS; Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium && python -m playwright install chrome

python main.py login            # Login
python main.py run --limit 5    # Jalankan 5 draft
```

---

## 3. Langkah Setelah Setup

### 3.1 Login (Sekali Saja)

```bash
bash run.sh login      # atau: make login / docker-compose run ...
```

Browser akan terbuka ke studio.youtube.com. Login dengan akun YouTube Anda, lalu tekan **Enter** di terminal. Session tersimpan di folder `profile/`.

### 3.2 Siapkan Thumbnail

Ada 2 cara:

**Cara A — Generator bawaan (recommended).** Buat thumbnail langsung ke `thumbnails/`:

```bash
# Daftar template
python main.py thumbnail --list

# Generate nomor episode 135–137 untuk template tertentu
python main.py thumbnail risalatul-maymuniyah 135 137

# Mode interaktif (pilih template, awal, akhir)
python main.py thumbnail --tui
```

Template yang tersedia: `ibanatul-ahkam`, `minhajut-tholibin`, `risalatul-maymuniyah`, `sirrul-asror`, `tafsir-jalalain`. Template PNG sumber berada di `templates/`, output otomatis masuk `thumbnails/`.

**Cara B — Letakkan file JPG manual** di folder `thumbnails/`. **Nama file WAJIB diawali nomor episode:**

```text
thumbnails/
├── 135 PENGAJIAN KITAB RISALATUL MAYMUNIYAH-Thumbnail.jpg
├── 136 PENGAJIAN KITAB RISALATUL MAYMUNIYAH-Thumbnail.jpg
└── 137 PENGAJIAN KITAB RISALATUL MAYMUNIYAH-Thumbnail.jpg
```

### 3.3 Konfigurasi (Opsional)

Edit `config.json` jika perlu:

```json
{
  "studio_url": "https://studio.youtube.com/channel/...",
  "timezone": "Asia/Jakarta",
  "schedule_time": "20:00",
  "schedule_offset_days": 7,
  "schedule_visibility_type": "PUBLISH_FROM_SPONSORS_ONLY",
  "pause_between_drafts": false,
  "screenshots": false,
  "headless": true
}
```

**Penting tentang timezone:**
- `timezone` di config mengatur timezone browser (dropdown jadwal)
- Gunakan IANA timezone identifier (misal: `Asia/Jakarta`, `Asia/Bangkok`, `America/New_York`)
- Harus sesuai dengan timezone channel YouTube agar jadwal benar
- Jika salah, jam jadwal bisa bergeser (misal: jadwal 20:00 jadi 03:00 keesokan hari)

> Daftar lengkap konfigurasi ada di `README.md`.

### 3.4 Test dengan 1 Draft

```bash
bash run.sh test       # atau: make test / python main.py run --limit 1
```

**Selalu test 1 draft dulu** sebelum menjalankan semua.

### 3.5 Jalankan

```bash
bash run.sh run 10     # Jalankan 10 draft
bash run.sh run        # Jalankan semua
```

---

## 4. Produksi

### Jalankan di Background

```bash
nohup bash run.sh run > automation.log 2>&1 &
tail -f automation.log        # Monitor
pkill -f "python main.py"  # Stop
```

Dengan Docker:
```bash
docker-compose up -d youtube-automation
docker-compose logs -f youtube-automation
docker-compose down
```

### Scheduled Automation (Cron)

Buat script `run-auto.sh`:

```bash
#!/bin/bash
cd /root/tools/youtube-automation
bash run.sh run --limit 5
```

Jadwalkan di crontab (setiap hari jam 9 pagi):

```
0 9 * * * /root/tools/youtube-automation/run-auto.sh >> /root/tools/youtube-automation/cron.log 2>&1
```

### Monitor Progress

```bash
tail -f logs/yt_auto.log            # Live log
grep "ERROR" logs/yt_auto.log       # Cari error
bash run.sh status                  # Cek status setup
```

> Screenshot per-step hanya diambil jika `"screenshots": true` di config.
> Screenshot `FAIL` saat error **selalu** diambil sebagai bukti.

### Debug Single Draft

```bash
bash run.sh test                    # Test 1 draft
.venv/bin/python main.py run --limit 1   # Direct Python
```

---

## 5. Checklist Sebelum Production

- [ ] Python 3.11+ terinstall (`python3 --version`)
- [ ] Setup selesai (bash setup.sh / make setup / docker-compose build)
- [ ] Login berhasil (`bash run.sh login`) — `profile/` terisi
- [ ] Thumbnail di `thumbnails/` dengan nama diawali nomor episode
- [ ] `config.json` benar (studio_url, schedule_time, playlist)
- [ ] `bash run.sh test` berhasil (1 draft tanpa error)
- [ ] Draft terlihat di YouTube Studio setelah diproses
- [ ] Tidak ada error di terminal output

---

## 6. Keamanan

- **`profile/`** berisi session login — **JANGAN di-commit ke git** (sudah di `.gitignore`)
- **`config.json`** berisi studio_url — **jaga kerahasiaan**
- **`.dockerignore`** memastikan `profile/`, `thumbnails/`, `logs/` tidak masuk image Docker
- Jangan menjalankan beberapa instance sekaligus (bisa kena rate limit)

---

## 7. Tips Performa

| Tujuan | Setting |
|--------|---------|
| Terlalu cepat (selector tak ketemu) | Naikkan `"wait_after_action_ms": 1000` |
| Terlalu lambat | Turunkan `"wait_after_action_ms": 500` |
| Hemat disk | `"screenshots": false` (default) |
| Proses banyak | `bash run.sh run 50` |
