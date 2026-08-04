.PHONY: help setup login run test status capture clean install-chromium

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
	@echo "  make run LIMIT=5        - Jalankan 5 draft (default: semua)"
	@echo "  make run                - Jalankan semua draft"
	@echo ""
	@echo "Utilities:"
	@echo "  make status             - Cek status setup"
	@echo "  make capture            - Rekam selector via Playwright codegen"
	@echo "  make install-chromium   - Install/reinstall Chromium"
	@echo "  make clean              - Hapus virtual environment & cache"
	@echo "  make help               - Tampilkan bantuan ini"
	@echo ""

setup:
	@bash setup.sh

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
	@if command -v google-chrome >/dev/null 2>&1 || command -v google-chrome-stable >/dev/null 2>&1; then \
		echo "✓ Google Chrome terdeteksi — lewati download Chromium (app memakai channel=chrome)"; \
	else \
		echo "Install Chromium untuk Playwright..."; \
		$(PYTHON) -m playwright install chromium; \
		echo "✓ Chromium installed"; \
	fi

login: venv
	@echo "🔐 Login YouTube Studio..."
	@$(PYTHON) main.py login

test: venv
	@echo "🧪 Test dengan 1 draft..."
	@$(PYTHON) main.py run --limit 1

run: venv
	@if [ -z "$(LIMIT)" ]; then \
		echo "🚀 Menjalankan semua draft..."; \
	else \
		echo "🚀 Menjalankan $(LIMIT) draft..."; \
	fi
	@$(PYTHON) main.py run $(if $(LIMIT),--limit $(LIMIT))

capture:
	@bash capture.sh

status:
	@bash run.sh status

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf $(VENV)
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✓ Clean selesai"

.DEFAULT_GOAL := help
