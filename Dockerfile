FROM python:3.11-slim

WORKDIR /app

# Install system dependencies untuk Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    apt-transport-https \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxinerama1 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy aplikasi
COPY . /app/

# Install Python dependencies (app memakai channel=chrome, bukan bundled chromium)
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install chrome

# Font Fira Sans untuk generator thumbnail (core/thumbgen.py)
RUN mkdir -p /usr/share/fonts/truetype/fira-sans \
    && wget -q -O /usr/share/fonts/truetype/fira-sans/FiraSans-BlackItalic.ttf \
        https://raw.githubusercontent.com/google/fonts/main/ofl/firasans/FiraSans-BlackItalic.ttf \
    && fc-cache -f

# Create necessary directories
RUN mkdir -p logs/screenshots profile thumbnails templates

# Environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "main.py", "run"]
