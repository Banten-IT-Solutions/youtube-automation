# Panduan Penggunaan

Cara menjalankan automation dan menggunakan semua perintah.

> **Baru mulai?** Selesaikan dulu `docs/setup.md`, lalu kembali ke sini.

---

## 1. Quick Start (5 Menit)

### 1.1 Install Dependencies

```bash
bash setup.sh
```

Script ini membuat virtual environment, install Playwright, dan download Chromium + Chrome.

### 1.2 Login (Sekali Saja)

```bash
bash run.sh login
```

Browser terbuka ke studio.youtube.com. Login, lalu tekan **Enter** di terminal. Session tersimpan di `profile/`.

### 1.3 Siapkan Thumbnail

Ada 2 cara:

**Cara A — Generator bawaan** (output langsung ke `thumbnails/`):

```bash
python main.py thumbnail risalatul-maymuniyah 135 137
python main.py thumbnail --list          # daftar template yang tersedia
python main.py thumbnail --tui           # mode interaktif
```

**Cara B — taruh file JPG manual** di `thumbnails/` dengan nama diawali nomor episode:

```text
thumbnails/
├── 135 PENGAJIAN KITAB RISALATUL MAYMUNIYAH - ABUYA UCI CILONGOK-Thumbnail.jpg
├── 136 PENGAJIAN KITAB RISALATUL MAYMUNIYAH - ABUYA UCI CILONGOK-Thumbnail.jpg
└── ...
```

> **Penting:** Nama file harus diawali **nomor episode** (misal: `135`, `136`).

---

## 2. Menjalankan Automation

### Test dengan 1 Draft (Recommended)

```bash
bash run.sh test
```

### Jalankan N Draft

```bash
bash run.sh run 5        # 5 draft
bash run.sh run 10       # 10 draft
bash run.sh run          # semua draft
```

### Cek Status Setup

```bash
bash run.sh status
```

Output:
```
📊 Status Setup:

✓ Virtual environment: OK
✓ Login session: OK
✓ Thumbnail: 5 file(s)
✓ Config: OK
```

---

## 3. Perintah Reference

| Perintah | Fungsi |
|----------|--------|
| `bash run.sh login` | Login ke YouTube Studio |
| `bash run.sh test` | Test 1 draft |
| `bash run.sh run N` | Jalankan N draft |
| `bash run.sh run` | Jalankan semua draft |
| `bash run.sh status` | Cek status setup |
| `make thumbnail TEMPLATE=... START=1 END=10` | Buat thumbnail ke `thumbnails/` (Makefile) |
| `main.py thumbnail <template> <start> <end>` | Buat thumbnail via subcommand |
| `make setup` | Setup (Makefile) |
| `make test` | Test 1 draft (Makefile) |
| `make run LIMIT=5` | Jalankan 5 draft (Makefile) |
| `.venv/bin/python main.py run --limit N` | Langsung Python |
| `python3 main.py run --verbose` | Mode debug (log detail) |
| `python3 -c "import core.logger"` | Cek sistem logging |

---

## 4. Alur Proses per Draft

Untuk setiap draft, sistem otomatis melakukan:

1. **Salin detail video lama** — reuse judul, deskripsi, dan setting dari video sebelumnya
2. **Ubah judul dan deskripsi** — update nomor episode
3. **Unggah gambar sampul** — dari folder `thumbnails/`
4. **Pengaturan lanjutan** — opsi lanjutan
5. **Aktifkan monetisasi & rating**
6. **Atur elemen video** — end screen dan kartu (diimpor dari video terbaru)
7. **Tentukan jadwal publikasi** — tanggal = video sebelumnya + `schedule_offset_days`

---

## 5. Estimasi Waktu

| Jumlah Draft | Estimasi Waktu |
|---|---|
| 1 draft | ~1 menit |
| 5 draft | ~5 menit |
| 10 draft | ~9 menit |
| 50 draft | ~45 menit |

---

## 6. Tips

### Jalankan di Background (Linux/macOS)

```bash
nohup bash run.sh run > automation.log 2>&1 &
tail -f automation.log       # Monitor progress
```

### Jalankan Berkala dengan Cron

```bash
crontab -e
```

Tambahkan (setiap hari jam 9 pagi):

```
0 9 * * * cd /root/tools/youtube-automation && bash run.sh run --limit 5
```

### Debug dengan Playwright Inspector

Jika YouTube update UI dan selector berubah:

```bash
.venv/bin/python -m playwright codegen "https://studio.youtube.com/"
```

Jalankan aksi manual di inspector, lalu update selector di bagian atas `core/selectors.py`.

### Lihat Log

```bash
tail -f logs/yt_auto.log           # Monitor live
grep "ERROR" logs/yt_auto.log      # Cari error
cat logs/yt_auto.log               # Semua log
```

---

## 7. Keamanan

- File `profile/` berisi session login — **jangan di-commit ke git**
- File `config.json` berisi `studio_url` — **jaga kerahasiaan**
- `.gitignore` dan `.dockerignore` sudah dikonfigurasi untuk folder sensitif
