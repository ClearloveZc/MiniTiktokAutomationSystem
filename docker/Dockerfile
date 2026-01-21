# TikTok Auto Publisher - Dockerfile
FROM python:3.11-slim

# Install Chromium and dependencies (works on both AMD64 and ARM64)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    xauth \
    fonts-liberation \
    fonts-noto-cjk \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data/videos /app/data/cookies /app/chrome_data

# Set environment variables
ENV CHROME_USER_DATA_DIR=/app/chrome_data
ENV HEADLESS_MODE=true
ENV PYTHONPATH=/app/src
ENV DISPLAY=:99
# Tell undetected-chromedriver to use system Chromium
ENV CHROME_EXECUTABLE_PATH=/usr/bin/chromium

# Create entrypoint script
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1920x1080x24 &\n\
sleep 1\n\
exec "$@"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["python", "src/main.py", "--help"]
