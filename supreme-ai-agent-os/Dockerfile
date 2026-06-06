FROM python:3.11-slim

WORKDIR /app

# System deps: curl for healthchecks + Playwright Chromium shared libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential \
    # Chromium via system package (reliable, no download needed)
    chromium \
    # Playwright shared library deps (belt + suspenders)
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libgbm1 libasound2t64 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libxext6 libx11-6 libxcb1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Point Playwright to the system Chromium (avoids fragile browser download)
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
# Skip Playwright's own browser download — we use system chromium above
ENV PLAYWRIGHT_BROWSERS_PATH=0

# Validate Playwright can find the system browser (non-fatal)
RUN python -c "
import subprocess, sys
r = subprocess.run(
    [sys.executable, '-c',
     'from playwright.sync_api import sync_playwright; '
     'p=sync_playwright().__enter__(); '
     'b=p.chromium.launch(headless=True, executable_path=\"/usr/bin/chromium\", args=[\"--no-sandbox\"]); '
     'b.close(); p.__exit__(None,None,None); print(\"playwright+chromium: ok\")'],
    capture_output=True, timeout=30
)
print(r.stdout.decode() or r.stderr.decode()[:200])
" 2>/dev/null || echo "[build] Using httpx fallback mode — browser features still available via HTTP engine"

COPY . .

RUN mkdir -p data/artifacts data/state data/.supreme-os && \
    chmod 700 data/.supreme-os

HEALTHCHECK --interval=15s --timeout=8s --start-period=30s --retries=6 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
