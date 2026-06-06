"""
Browser automation — multi-engine unified agent.

Engine priority (auto-selected at runtime):
  1. Playwright + system Chromium   (full JS, screenshots, click, forms)
  2. Playwright + bundled Chromium  (full JS, screenshots)
  3. Playwright + Browserless/CDP   (remote Chromium via BROWSERLESS_URL)
  4. Selenium + system Chromium     (full JS, screenshots via Pillow)
  5. httpx + BeautifulSoup          (always available — text/links/structured)

All engines expose identical public API. Status always reports active engine.
"""
from __future__ import annotations
import asyncio, base64, os, re, time
from typing import Any

# ── Engine state ──────────────────────────────────────────────────────────────

_ENGINE: str | None = None        # set once by _detect_engine()
_pw_instance = None
_pw_browser = None
_selenium_driver = None

_SYSTEM_CHROMIUM_PATHS = [
    os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", ""),
    os.getenv("CHROME_BIN", ""),
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/snap/bin/chromium",
    "/usr/local/bin/chromium",
]
_CHROME_ARGS = [
    "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
    "--disable-extensions", "--disable-background-networking",
    "--single-process",
]
_BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "")


# ── Engine 1 & 2: Playwright ──────────────────────────────────────────────────

async def _try_playwright_system() -> bool:
    """Try Playwright with system/env-specified Chromium binary."""
    global _pw_instance, _pw_browser
    bins = [p for p in _SYSTEM_CHROMIUM_PATHS if p and os.path.isfile(p)]
    if not bins:
        return False
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().__aenter__()
        browser = await pw.chromium.launch(
            headless=True,
            executable_path=bins[0],
            args=_CHROME_ARGS,
        )
        page = await browser.new_page()
        await page.set_content("<html><body>ok</body></html>")
        await page.close()
        _pw_instance = pw
        _pw_browser = browser
        return True
    except Exception:
        _cleanup_playwright()
        return False


async def _try_playwright_bundled() -> bool:
    """Try Playwright with its own downloaded Chromium."""
    global _pw_instance, _pw_browser
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().__aenter__()
        browser = await pw.chromium.launch(headless=True, args=_CHROME_ARGS)
        page = await browser.new_page()
        await page.set_content("<html><body>ok</body></html>")
        await page.close()
        _pw_instance = pw
        _pw_browser = browser
        return True
    except Exception:
        _cleanup_playwright()
        return False


async def _try_playwright_remote() -> bool:
    """Try Playwright connecting to remote Browserless/CDP endpoint."""
    global _pw_instance, _pw_browser
    if not _BROWSERLESS_URL:
        return False
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().__aenter__()
        # Browserless exposes CDP at /chromium/playwright
        ws_url = _BROWSERLESS_URL.rstrip("/")
        if not ws_url.startswith("ws"):
            ws_url = ws_url.replace("http://", "ws://").replace("https://", "wss://")
            ws_url = ws_url + "/chromium/playwright?launch=true"
        browser = await pw.chromium.connect(ws_url)
        page = await browser.new_page()
        await page.set_content("<html><body>ok</body></html>")
        await page.close()
        _pw_instance = pw
        _pw_browser = browser
        return True
    except Exception:
        _cleanup_playwright()
        return False


def _cleanup_playwright():
    global _pw_instance, _pw_browser
    try:
        if _pw_instance:
            asyncio.get_event_loop().run_until_complete(
                _pw_instance.__aexit__(None, None, None)
            )
    except Exception:
        pass
    _pw_instance = None
    _pw_browser = None


# ── Engine 4: Selenium ────────────────────────────────────────────────────────

def _try_selenium() -> bool:
    """Try Selenium with system Chromium + chromedriver (no network download)."""
    global _selenium_driver
    chrome_bins = [p for p in _SYSTEM_CHROMIUM_PATHS if p and os.path.isfile(p)]
    driver_paths = [
        os.getenv("CHROMEDRIVER_PATH", ""),
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromedriver",
    ]
    driver_bin = next((p for p in driver_paths if p and os.path.isfile(p)), None)
    if not driver_bin:
        return False
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        opts = Options()
        opts.add_argument("--headless=new")
        for arg in _CHROME_ARGS:
            opts.add_argument(arg)
        if chrome_bins:
            opts.binary_location = chrome_bins[0]
        svc = Service(executable_path=driver_bin, log_output=os.devnull)
        driver = webdriver.Chrome(options=opts, service=svc)
        driver.get("data:text/html,<html><body>ok</body></html>")
        _ = driver.title
        _selenium_driver = driver
        return True
    except Exception:
        _selenium_driver = None
        return False


# ── Engine detection ──────────────────────────────────────────────────────────

async def _detect_engine() -> str:
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE

    if await _try_playwright_system():
        _ENGINE = "playwright_system"
    elif await _try_playwright_bundled():
        _ENGINE = "playwright_bundled"
    elif await _try_playwright_remote():
        _ENGINE = "playwright_remote"
    elif await asyncio.get_event_loop().run_in_executor(None, _try_selenium):
        _ENGINE = "selenium"
    else:
        _ENGINE = "httpx"
    return _ENGINE


def _is_playwright() -> bool:
    return _ENGINE is not None and _ENGINE.startswith("playwright")


async def _get_pw_browser():
    global _pw_browser
    if _pw_browser is None:
        e = await _detect_engine()
        if not _is_playwright():
            return None
    return _pw_browser


# ── httpx helpers ─────────────────────────────────────────────────────────────

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def _parse_html(html: str, url: str) -> dict:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            tag.decompose()
        title_el = soup.find("title") or soup.find("h1") or soup.find("h2")
        title = title_el.get_text(strip=True) if title_el else url
        text = re.sub(r"\s{2,}", " ", soup.get_text(separator=" ", strip=True))
        links = [
            {"text": a.get_text(strip=True)[:100], "href": a.get("href", "")}
            for a in soup.find_all("a", href=True)[:30]
        ]
        meta = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta.get("content", "")[:300] if meta else ""
        return {"title": title, "text": text[:50000], "links": links, "meta_description": meta_desc}
    except Exception:
        return {"title": url, "text": html[:10000], "links": [], "meta_description": ""}


async def _httpx_fetch(url: str, timeout: float = 20.0) -> dict:
    try:
        import httpx
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=timeout, headers=_BROWSER_HEADERS
        ) as client:
            resp = await client.get(url)
            parsed = _parse_html(resp.text, url)
            return {
                "url": str(resp.url), "status_code": resp.status_code,
                "ok": resp.status_code < 400,
                "title": parsed["title"], "text": parsed["text"],
                "html": resp.text[:50000], "links": parsed["links"],
                "meta_description": parsed["meta_description"],
                "screenshot_b64": None, "engine": "httpx", "error": None,
            }
    except Exception as e:
        return {
            "url": url, "ok": False, "title": "", "text": "", "html": "",
            "links": [], "screenshot_b64": None, "engine": "httpx", "error": str(e),
        }


# ── Selenium helpers ──────────────────────────────────────────────────────────

def _selenium_fetch_sync(url: str) -> dict:
    global _selenium_driver
    try:
        drv = _selenium_driver
        drv.get(url)
        time.sleep(1.5)
        html = drv.page_source
        title = drv.title
        # Screenshot via PNG
        png = drv.get_screenshot_as_png()
        screenshot_b64 = base64.b64encode(png).decode()
        parsed = _parse_html(html, url)
        return {
            "url": url, "status_code": 200, "ok": True,
            "title": title or parsed["title"],
            "text": parsed["text"], "html": html[:50000],
            "links": parsed["links"], "meta_description": parsed["meta_description"],
            "screenshot_b64": screenshot_b64, "engine": "selenium", "error": None,
        }
    except Exception as e:
        return {
            "url": url, "ok": False, "title": "", "text": "", "html": "",
            "links": [], "screenshot_b64": None, "engine": "selenium", "error": str(e),
        }


# ── Public API ─────────────────────────────────────────────────────────────────

async def fetch_page(url: str, wait_for: str = "domcontentloaded") -> dict:
    """Fetch full page — best available engine."""
    engine = await _detect_engine()

    if _is_playwright():
        try:
            browser = await _get_pw_browser()
            page = await browser.new_page()
            await page.goto(url, wait_until=wait_for, timeout=30000)
            html = await page.content()
            title = await page.title()
            text_content = await page.evaluate("document.body.innerText || document.body.textContent || ''")
            screenshot = await page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot).decode()
            links_raw = await page.evaluate("""
                Array.from(document.querySelectorAll('a[href]')).slice(0,30).map(a => ({
                    text: (a.innerText || a.textContent || '').trim().substring(0,100),
                    href: a.href
                }))
            """)
            await page.close()
            return {
                "url": url, "status_code": 200, "ok": True,
                "title": title, "text": text_content[:50000],
                "html": html[:50000], "links": links_raw,
                "screenshot_b64": screenshot_b64,
                "engine": engine, "error": None,
            }
        except Exception as e:
            result = await _httpx_fetch(url)
            result["playwright_error"] = str(e)
            return result

    if engine == "selenium":
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _selenium_fetch_sync, url)

    return await _httpx_fetch(url)


async def screenshot(url: str) -> dict:
    """Navigate to URL and capture screenshot. Returns base64 PNG."""
    engine = await _detect_engine()

    if _is_playwright():
        try:
            browser = await _get_pw_browser()
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            png = await page.screenshot(type="png", full_page=False)
            await page.close()
            return {
                "url": url, "ok": True, "title": title,
                "screenshot_b64": base64.b64encode(png).decode(),
                "engine": engine,
            }
        except Exception as e:
            return {"url": url, "ok": False, "screenshot_b64": None, "engine": engine, "error": str(e)}

    if engine == "selenium":
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _selenium_fetch_sync, url)
        return {
            "url": url, "ok": result["ok"],
            "title": result.get("title", ""),
            "screenshot_b64": result.get("screenshot_b64"),
            "engine": "selenium",
        }

    return {
        "url": url, "ok": False, "screenshot_b64": None, "engine": "httpx",
        "error": "Screenshots require Playwright or Selenium + Chromium.",
        "hint": "Start Ollama container and run: docker compose exec api python -m playwright install chromium",
    }


async def extract_text(url: str) -> dict:
    result = await fetch_page(url)
    return {
        "url": url, "ok": result.get("ok", False),
        "title": result.get("title", ""), "text": result.get("text", ""),
        "links": result.get("links", []), "engine": result.get("engine", "unknown"),
        "error": result.get("error"),
    }


async def summarize_page(url: str) -> dict:
    page_data = await extract_text(url)
    if not page_data.get("ok"):
        return {**page_data, "summary": f"Could not fetch {url}: {page_data.get('error', 'unknown')}"}
    text = page_data.get("text", "")[:8000]
    try:
        from backend.app.providers.router import complete as llm_complete
        resp = llm_complete(
            f"Summarize this webpage in 3-5 bullet points:\n\nTitle: {page_data['title']}\n\nContent:\n{text}"
        )
        summary = resp.get("text", "LLM not configured")
    except Exception:
        summary = f"Title: {page_data['title']}\n\n{text[:500]}"
    return {
        "url": url, "ok": True, "title": page_data.get("title", ""),
        "summary": summary, "engine": page_data.get("engine", "unknown"),
    }


async def structured_extract(url: str, schema: dict) -> dict:
    try:
        page_data = await fetch_page(url)
        html = page_data.get("html", "")
        if not html:
            return {"url": url, "ok": False, "data": {}, "error": page_data.get("error")}
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        data = {}
        for field, selector in schema.items():
            try:
                el = soup.select_one(str(selector))
                data[field] = el.get_text(strip=True) if el else None
            except Exception:
                data[field] = None
        return {"url": url, "ok": True, "data": data, "engine": page_data.get("engine", "unknown")}
    except Exception as e:
        return {"url": url, "ok": False, "data": {}, "error": str(e)}


async def navigate(url: str, selector: str = "") -> dict:
    """Navigate to URL, optionally click a selector, return page content."""
    engine = await _detect_engine()

    if _is_playwright() and selector:
        try:
            browser = await _get_pw_browser()
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            if selector:
                await page.click(selector)
                await page.wait_for_load_state("networkidle", timeout=10000)
            html = await page.content()
            title = await page.title()
            await page.close()
            parsed = _parse_html(html, url)
            return {"ok": True, "title": title, "text": parsed["text"], "engine": engine}
        except Exception as e:
            return {"ok": False, "error": str(e), "engine": engine}

    result = await fetch_page(url)
    return {"ok": result["ok"], "title": result.get("title",""), "text": result.get("text",""), "engine": result.get("engine","unknown")}


async def plan_form_interaction(url: str, goal: str) -> dict:
    page_data = await fetch_page(url)
    html = page_data.get("html", "")
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        forms = []
        for form in soup.find_all("form")[:5]:
            fields = [
                {
                    "type": inp.get("type", inp.name),
                    "name": inp.get("name", ""),
                    "placeholder": inp.get("placeholder", ""),
                    "required": inp.has_attr("required"),
                }
                for inp in form.find_all(["input", "textarea", "select"])
            ]
            forms.append({
                "action": form.get("action", ""),
                "method": form.get("method", "get"),
                "fields": fields,
            })
    except Exception:
        forms = []
    return {
        "url": url, "ok": page_data.get("ok", False),
        "title": page_data.get("title", ""), "forms_found": len(forms), "forms": forms,
        "goal": goal,
        "plan": f"Identified {len(forms)} form(s). Review fields before submitting.",
        "engine": page_data.get("engine", "unknown"),
        "warning": "Form submission requires explicit user authorization.",
    }


async def run_script(url: str, js: str) -> dict:
    engine = await _detect_engine()
    if _is_playwright():
        try:
            browser = await _get_pw_browser()
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            result = await page.evaluate(js)
            await page.close()
            return {"ok": True, "result": result, "engine": engine}
        except Exception as e:
            return {"ok": False, "error": str(e), "engine": engine}
    if engine == "selenium":
        try:
            loop = asyncio.get_event_loop()
            def _run():
                _selenium_driver.get(url)
                time.sleep(1)
                return _selenium_driver.execute_script(js)
            result = await loop.run_in_executor(None, _run)
            return {"ok": True, "result": result, "engine": "selenium"}
        except Exception as e:
            return {"ok": False, "error": str(e), "engine": "selenium"}
    return {
        "ok": False, "engine": "httpx",
        "error": "JavaScript execution requires Playwright or Selenium.",
    }


async def status() -> dict:
    """Return browser engine status and capabilities."""
    engine = await _detect_engine()

    _engine_caps = {
        "playwright_system": {
            "available": True, "engine": "playwright", "source": "system_chromium",
            "mode": "full",
            "features": ["fetch", "screenshot", "js_execution", "navigate", "click", "form_planning", "structured_extract"],
        },
        "playwright_bundled": {
            "available": True, "engine": "playwright", "source": "bundled_chromium",
            "mode": "full",
            "features": ["fetch", "screenshot", "js_execution", "navigate", "click", "form_planning", "structured_extract"],
        },
        "playwright_remote": {
            "available": True, "engine": "playwright", "source": "remote_browserless",
            "mode": "full",
            "features": ["fetch", "screenshot", "js_execution", "navigate", "click", "form_planning", "structured_extract"],
            "endpoint": _BROWSERLESS_URL,
        },
        "selenium": {
            "available": True, "engine": "selenium", "source": "system_chromium",
            "mode": "full",
            "features": ["fetch", "screenshot", "js_execution", "navigate", "form_planning", "structured_extract"],
        },
        "httpx": {
            "available": True, "engine": "httpx", "source": "http_client",
            "mode": "http",
            "features": ["fetch", "text_extraction", "structured_extract", "summarize", "form_planning"],
            "note": "HTTP mode — full browser available when Playwright + Chromium are installed",
            "hint": "docker compose exec api python -m playwright install chromium",
        },
    }
    return _engine_caps.get(engine, {"available": False, "engine": engine, "mode": "unknown", "features": []})
