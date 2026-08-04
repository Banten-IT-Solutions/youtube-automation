# Selector UI YouTube Studio — dipakai oleh main.py

SEL_ROW = "ytcp-video-row"
SEL_TITLE_LINK = "a#video-title"
SEL_EDIT_BTN = ["ytcp-button[aria-label='Detail']", "button[aria-label='Detail']", "ytcp-button:has-text('Detail')"]
SEL_EDIT_DRAFT_BTN = ["button[aria-label='Edit draf']", "ytcp-button[aria-label='Edit draf']", "button:has-text('Edit draf')"]

SEL_REUSE_BTN = ["ytcp-button:has-text('Gunakan kembali detail')", "button:has-text('Gunakan kembali detail')"]
SEL_REUSE_OPTION = "ytcp-entity-card"

SEL_TITLE_NAME = "Tambahkan judul yang menjelaskan video Anda (ketik @ untuk menyebutkan channel)"
SEL_DESC_NAME = "Beri tahu penonton tentang video Anda (ketik @ untuk menyebutkan channel)"

SEL_THUMB_INPUT = "input#file-loader"

SEL_SHOW_MORE = ["ytcp-button:has-text('Tampilkan lebih banyak')", "button:has-text('Tampilkan lebih banyak')", "ytcp-button:has-text('Tampilkan setelan lanjutan')", "button:has-text('Tampilkan setelan lanjutan')"]
SEL_AI_NO_NAME = "Tidak, AI tidak digunakan"
SEL_REC_DATE_BTN = "Tanggal perekaman"

SEL_NEXT = "Berikutnya"
SEL_M10N = ".m10n-text"
SEL_M10N_AKTIF = "Aktif"
SEL_M10N_SELESAI = "Selesai"
SEL_RATING_NONE = "Tidak satu pun di atas"
SEL_RATING_SUBMIT = "Kirim rating"

SEL_SAVE = "Simpan"

SEL_CARDS_BUTTON = "#cards-button"
SEL_CARD_ENTITY = "ytcp-entity-card"
SEL_CARD_SEARCH = [
    "ytcp-playlist-picker input[type='text']",
    "ytcp-playlist-picker input",
    "ytcp-dialog input[type='text']",
]

SEL_SCHED_TIME = ["input[placeholder*='hh:mm']", "input[aria-label*='Waktu']", "#input-3"]
SEL_SCHEDULE_BTN = ["ytcp-button#schedule-button", "ytcp-button:has-text('Jadwalkan')"]
SEL_CLOSE = ["ytcp-button:has-text('Tutup')", "button:has-text('Tutup')"]
