.PHONY: help setup login run test status clean install-chromium

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "BITS YouTube Automation - Makefile"
	@echo ""
	@echo "Setup:"
	@echo "  make setup              - Install dependencies & Chromium"
	@echo ""
	@echo "Jalankan:"
	@echo "  make login              - Login ke YouTube Studio (sekali saja)"
	@echo "  make test               - Test dengan 1 draft"
	@echo "  make run LIMIT=5         - Jalankan 5 draft (default: semua)"
	@echo "  make run                - Jalankan semua draft"
	@echo ""
	@echo "Utilities:"
	@echo "  make status             - Cek status setup"
	@echo "  make install-chromium   - Install/reinstall Chromium"
	@echo "  make clean              - Hapus virtual environment & cache"
	@echo "  make help               - Tampilkan bantuan ini"
	@echo ""

setup: venv install-chromium
	@echo ""
	@echo "✓ Setup selesai!"
	@echo ""
	@echo "Langkah selanjutnya:"
	@echo "  make login              - Login ke YouTube Studio"
	@echo "  make test               - Test dengan 1 draft"
	@echo ""

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "[1/3] Membuat virtual environment..."; \
		python3 -m venv $(VENV); \
	fi
	@echo "[2/3] Upgrade pip..."
	@$(PIP) install --upgrade pip setuptools wheel > /dev/null 2>&1
	@echo "[3/3] Install dependencies..."
	@$(PIP) install -q -r requirements.txt

install-chromium: venv
	@echo "Install Chromium untuk Playwright..."
	@$(PYTHON) -m playwright install chromium
	@echo "✓ Chromium installed"

login: venv
	@echo "🔐 Login YouTube Studio..."
	@$(PYTHON) yt_auto.py login

test: venv
	@echo "🧪 Test dengan 1 draft..."
	@$(PYTHON) yt_auto.py run --limit 1

run: venv
	@if [ -z "$(LIMIT)" ]; then \
		echo "🚀 Menjalankan semua draft..."; \
		$(PYTHON) yt_auto.py run; \
	else \
		echo "🚀 Menjalankan $(LIMIT) draft..."; \
		$(PYTHON) yt_auto.py run --limit $(LIMIT); \
	fi

status: venv
	@echo "📊 Status Setup:"
	@echo ""
	@if [ -d "$(VENV)" ]; then \
		echo "✓ Virtual environment: OK"; \
	else \
		echo "✗ Virtual environment: NOT FOUND"; \
	fi
	@if [ -d "profile" ] && [ -n "$$(ls -A profile 2>/dev/null)" ]; then \
		echo "✓ Login session: OK"; \
	else \
		echo "✗ Login session: BELUM ADA"; \
	fi
	@if [ -d "thumbnails" ] && [ -n "$$(ls -A thumbnails 2>/dev/null)" ]; then \
		echo "✓ Thumbnail: $$(ls thumbnails | wc -l) file(s)"; \
	else \
		echo "⚠ Thumbnail: KOSONG"; \
	fi
	@if [ -f "config.json" ]; then \
		echo "✓ Config: OK"; \
	fi
	@echo ""

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf $(VENV)
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✓ Clean selesai"

.DEFAULT_GOAL := help
