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

# Point Playwright at system Chromium — skip fragile binary download
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
ENV PLAYWRIGHT_BROWSERS_PATH=0
# Point Selenium at system chromedriver
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Validate browser engine at build time (non-fatal — will use httpx if both fail)
RUN python -c "
import subprocess, sys, os

# Try Playwright
r = subprocess.run(
    [sys.executable, '-c',
     'from playwright.sync_api import sync_playwright; '
     'p=sync_playwright().__enter__(); '
     'b=p.chromium.launch(headless=True, executable_path=\"/usr/bin/chromium\", args=[\"--no-sandbox\",\"--disable-dev-shm-usage\",\"--disable-gpu\"]); '
     'page=b.new_page(); page.set_content(\"<h1>ok</h1>\"); t=page.title(); page.close(); b.close(); '
     'p.__exit__(None,None,None); print(\"playwright+system_chromium: ok\")'],
    capture_output=True, timeout=30
)
if r.returncode == 0:
    print(r.stdout.decode().strip())
else:
    print('[build] playwright+system_chromium unavailable:', r.stderr.decode()[:120])

# Try Selenium
r2 = subprocess.run(
    [sys.executable, '-c',
     'from selenium import webdriver; from selenium.webdriver.chrome.options import Options; '
     'from selenium.webdriver.chrome.service import Service; import os; '
     'o=Options(); o.add_argument(\"--headless=new\"); o.add_argument(\"--no-sandbox\"); '
     'o.add_argument(\"--disable-dev-shm-usage\"); o.add_argument(\"--disable-gpu\"); '
     'o.binary_location=\"/usr/bin/chromium\"; '
     's=Service(\"/usr/bin/chromedriver\",log_output=os.devnull); '
     'd=webdriver.Chrome(options=o,service=s); d.get(\"data:text/html,<h1>ok</h1>\"); '
     'print(\"selenium+chromedriver: ok\"); d.quit()'],
    capture_output=True, timeout=30
)
if r2.returncode == 0:
    print(r2.stdout.decode().strip())
else:
    print('[build] selenium unavailable:', r2.stderr.decode()[:120])
" 2>/dev/null || echo "[build] Browser validation non-fatal — httpx fallback always available"

COPY . .

RUN mkdir -p data/artifacts data/state data/.supreme-os && \
    chmod 700 data/.supreme-os

HEALTHCHECK --interval=15s --timeout=8s --start-period=30s --retries=6 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
