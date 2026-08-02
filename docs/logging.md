# Sistem Logging

Dokumentasi sistem logging YouTube Automation — format, emoji, penggunaan, dan API.

---

## 1. Overview

Sistem logging dirancang user-friendly dengan:
- 🎨 **Emoji dan warna** untuk visual menarik
- 📊 **Progress tracking** per draft
- 🎯 **Pesan jelas** dalam bahasa sehari-hari
- 📈 **Summary report** di akhir eksekusi
- 📁 **Log file otomatis** (`logs/yt_auto.log`)

---

## 2. Emoji Reference

| Emoji | Level | Warna | Arti |
|-------|-------|-------|------|
| ✅ | SUCCESS | Hijau | Aksi berhasil |
| ❌ | ERROR | Merah | Gagal / error |
| ⚠️ | WARNING | Kuning | Perlu perhatian / fallback |
| ▶️ | STEP | Magenta | Aksi sedang berlangsung |
| ⏳ | PROGRESS | Cyan | Update progress |
| ℹ️ | INFO | Biru | Informasi umum |
| 🔍 | DEBUG | Cyan | Debug info (hanya `--verbose`) |

> **Format:** `[HH:MM:SS] emoji  pesan` (spasi ganda setelah emoji agar rapi).

### Standar Pesan Warning/Error

Pesan **warning** dan **error** selalu menyertakan **solusi singkat** setelah ` - `:

```
⚠️  Gambar sampul untuk 5 tidak ditemukan - letakkan file di folder thumbnails/
❌  Tidak bisa baca nomor dari Nama file - berhenti. Pastikan pola penamaan num judul
```

Format: `masalah - solusi singkat` (bukan sekadar "cek manual").

---

## 3. Cara Menggunakan

### Commands

```bash
# Jalankan normal
python3 yt_auto.py run

# Mode debug (tampilkan log DEBUG)
python3 yt_auto.py run --verbose

# Batasi jumlah draft
python3 yt_auto.py run --limit 5

# Test sistem logging
python3 -c "import logger; print('ok')"

# Lihat / cari / monitor log
cat logs/yt_auto.log
grep "ERROR" logs/yt_auto.log
grep "Draft 5" logs/yt_auto.log
tail -f logs/yt_auto.log
```

### Mode Verbose

`--verbose` menampilkan detail teknis tambahan (semua log DEBUG):
```bash
python3 yt_auto.py run --verbose
```

---

## 4. Contoh Output

### Alur Draft (format final)

```
[10:08:24] ⏳  Draft 1/10 - Dimulai
[10:08:25] ℹ️  Informasi draft
[10:08:26] ▶️  Salin detail video lama
[10:08:26]     ▶️  Pilih video sebelumnya
[10:08:27]     ✓ Video dipilih: 1 PENGAJIAN KITAB
[10:08:28] ▶️  Ubah judul dan deskripsi
[10:08:28]     ✓ Judul dan deskripsi berhasil diubah
[10:08:29] ▶️  Unggah gambar sampul
[10:08:30]     ✓ Gambar sampul berhasil diupload
[10:08:31] ▶️  Pengaturan lanjutan
[10:08:32] ▶️  Aktifkan monetisasi & rating
[10:08:45] ✅  Draft 1 - Selesai ✓
```

### Warning & Error

```
[10:08:24] ⚠️  Gambar sampul untuk 5 tidak ditemukan - letakkan file di folder thumbnails/
[10:08:25] ▶️  Unggah gambar sampul → (tidak ditemukan)
[10:08:25] ⚠️  Gagal mengunggah gambar - cek format JPG & nama file

[10:08:30] ❌  Tidak bisa baca nomor dari Nama file - berhenti. Pastikan pola penamaan num judul
[10:08:31] ❌  Draft 1 - Gagal ✗
```

### Summary Report

Di akhir eksekusi:

```
════════════════════════════════════════════════════════════
  RINGKASAN HASIL
════════════════════════════════════════════════════════════

  Total draft diproses: 10
  ✅ Berhasil: 10
  ❌ Gagal: 0
  ⏱️  Waktu total: 00:15:30

  🎉 Semua draft berhasil diproses!
```

Jika ada error:
```
  Total draft diproses: 10
  ✅ Berhasil: 8
  ❌ Gagal: 2
  ⏱️  Waktu total: 00:14:20

  Tingkat sukses: 80.0%
```

---

## 5. Log File

Semua log otomatis disimpan di `logs/yt_auto.log` (tanpa warna/ANSI codes).

| Tujuan | Command |
|--------|---------|
| Lihat semua | `cat logs/yt_auto.log` |
| Cari error | `grep "ERROR" logs/yt_auto.log` |
| Cari draft tertentu | `grep "Draft 5" logs/yt_auto.log` |
| Monitor live | `tail -f logs/yt_auto.log` |
| Analisis durasi | `head -1` (mulai) + `tail -5` (selesai) |

---

## 6. API Logger (untuk Development)

```python
from logger import get_logger

logger = get_logger()

# Basic levels
logger.info("Pesan info")
logger.success("Berhasil!")
logger.warning("Hati-hati!")
logger.error("Error!")
logger.debug("Debug info (hanya jika verbose)")

# Structured logging
logger.section("Judul Section")
logger.action("Nama aksi", "detail")
logger.step("Langkah detail", indent=2)
logger.result("Hasil aksi", success=True)
logger.separator()

# Draft tracking
logger.start_draft(5, total=10)
logger.end_draft(5, success=True)

# Summary
logger.summary()
```

---

## 7. Troubleshooting Logging

| Masalah | Solusi |
|---------|--------|
| Emoji tidak terlihat | Terminal perlu support ANSI colors (`echo $TERM`) |
| Warna tidak muncul | `cat logs/yt_auto.log` (versi plain text) |
| Mau lihat debug info | `python3 yt_auto.py run --verbose` |
| Mau simpan log khusus | Sudah otomatis di `logs/yt_auto.log` |
| Mau search di log | `grep "keyword" logs/yt_auto.log` |

---

## 8. Catatan Teknis

- Logger tidak menambah overhead signifikan (~0.5ms per operasi)
- File I/O non-blocking
- Warna hanya di terminal; file log selalu plain text (compatible)
- `--verbose` diperlukan untuk level DEBUG
