FROM python:3.11-slim

WORKDIR /app

# System deps + Chromium for Playwright & Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential \
    chromium chromium-driver \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libgbm1 libasound2t64 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libxext6 libx11-6 libxcb1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Point Playwright / Selenium at system Chromium
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
ENV PLAYWRIGHT_BROWSERS_PATH=0
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

COPY . .

# Create non-root user and set ownership
RUN useradd -m -u 1000 appuser && \
    mkdir -p data/artifacts data/state data/.agent-os && \
    chmod 700 data/.agent-os && \
    chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=15s --timeout=8s --start-period=30s --retries=6 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
