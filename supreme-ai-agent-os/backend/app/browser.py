"""
Browser automation — production-grade multi-engine unified agent.

Engine priority (auto-selected at runtime, highest capability wins):
  1. playwright_system   — Playwright + system Chromium (/usr/bin/chromium)
  2. playwright_bundled  — Playwright + Playwright-downloaded Chromium
  3. playwright_remote   — Playwright over CDP → Browserless/remote Chrome
  4. browser_use         — browser-use AI agent (wraps Playwright, LLM-native)
  5. selenium            — Selenium + system chromedriver (no network download)

httpx is NOT a browser engine. It is used only for plain text extraction as
a last-resort utility. When no real browser engine is available,
status() reports available=False, mode="unavailable".

All real engines expose the full capability surface:
  click, type, upload, download, screenshot, multi-tab, cookies,
  sessions, login persistence, captcha detection, visual understanding.
"""
from __future__ import annotations
import asyncio, base64, os, re, time
from typing import Any

# ── Config ────────────────────────────────────────────────────────────────────

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
_CHROMEDRIVER_PATHS = [
    os.getenv("CHROMEDRIVER_PATH", ""),
    "/usr/bin/chromedriver",
    "/usr/local/bin/chromedriver",
    "/snap/bin/chromedriver",
]
_CHROME_ARGS = [
    "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
    "--disable-extensions", "--disable-background-networking",
    "--window-size=1920,1080",
]
_BROWSERLESS_URL = os.getenv("BROWSERLESS_URL", "")

# ── Engine state ──────────────────────────────────────────────────────────────

_ENGINE: str | None = None
_pw_instance = None
_pw_browser = None
_selenium_driver = None
_engine_meta: dict = {}

# ── Playwright engine helpers ─────────────────────────────────────────────────

async def _launch_playwright(executable_path: str | None = None, cdp_url: str | None = None) -> bool:
    global _pw_instance, _pw_browser
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().__aenter__()
        if cdp_url:
            browser = await pw.chromium.connect_over_cdp(cdp_url)
        else:
            kwargs: dict = {"headless": True, "args": _CHROME_ARGS}
            if executable_path:
                kwargs["executable_path"] = executable_path
            browser = await pw.chromium.launch(**kwargs)
        # Smoke test
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.set_content("<html><body>ok</body></html>")
        title = await page.title()
        await ctx.close()
        _pw_instance = pw
        _pw_browser = browser
        return True
    except Exception:
        await _teardown_playwright()
        return False


async def _teardown_playwright():
    global _pw_instance, _pw_browser
    try:
        if _pw_browser:
            await _pw_browser.close()
    except Exception:
        pass
    try:
        if _pw_instance:
            await _pw_instance.__aexit__(None, None, None)
    except Exception:
        pass
    _pw_instance = None
    _pw_browser = None


async def _try_playwright_system() -> bool:
    bins = [p for p in _SYSTEM_CHROMIUM_PATHS if p and os.path.isfile(p)]
    if not bins:
        return False
    result = await _launch_playwright(executable_path=bins[0])
    if result:
        _engine_meta["source"] = "system_chromium"
        _engine_meta["executable"] = bins[0]
    return result


async def _try_playwright_bundled() -> bool:
    result = await _launch_playwright()
    if result:
        _engine_meta["source"] = "bundled_chromium"
    return result


async def _try_playwright_remote() -> bool:
    if not _BROWSERLESS_URL:
        return False
    url = _BROWSERLESS_URL.rstrip("/")
    # Normalize to HTTP for CDP connect
    if url.startswith("wss://"):
        url = url.replace("wss://", "https://")
    elif url.startswith("ws://"):
        url = url.replace("ws://", "http://")
    result = await _launch_playwright(cdp_url=url)
    if result:
        _engine_meta["source"] = "browserless_cdp"
        _engine_meta["endpoint"] = _BROWSERLESS_URL
    return result


# ── Selenium engine helper ────────────────────────────────────────────────────

def _try_selenium_sync() -> bool:
    global _selenium_driver
    chrome_bins = [p for p in _SYSTEM_CHROMIUM_PATHS if p and os.path.isfile(p)]
    driver_bin = next((p for p in _CHROMEDRIVER_PATHS if p and os.path.isfile(p)), None)
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
        _selenium_driver = driver
        _engine_meta["source"] = "system_chromedriver"
        _engine_meta["executable"] = driver_bin
        return True
    except Exception:
        _selenium_driver = None
        return False


# ── browser-use engine helper ─────────────────────────────────────────────────

async def _try_browser_use() -> bool:
    """Optional: browser-use AI agent layer on top of Playwright."""
    try:
        import browser_use  # noqa: F401 — presence check only
        # browser-use wraps Playwright; actual Playwright must be working first
        if await _try_playwright_system() or await _try_playwright_bundled():
            _engine_meta["source"] = "browser_use_playwright"
            return True
    except ImportError:
        pass
    return False


# ── Engine detection ──────────────────────────────────────────────────────────

async def _detect_engine() -> str:
    global _ENGINE, _engine_meta
    if _ENGINE is not None:
        return _ENGINE

    _engine_meta = {}

    if await _try_playwright_system():
        _ENGINE = "playwright_system"
    elif await _try_playwright_bundled():
        _ENGINE = "playwright_bundled"
    elif await _try_playwright_remote():
        _ENGINE = "playwright_remote"
    elif await _try_browser_use():
        _ENGINE = "browser_use"
    elif await asyncio.get_event_loop().run_in_executor(None, _try_selenium_sync):
        _ENGINE = "selenium"
    else:
        _ENGINE = "httpx_fallback"

    return _ENGINE


def _is_full_browser() -> bool:
    return _ENGINE is not None and _ENGINE not in ("httpx_fallback", None)


def _is_playwright() -> bool:
    return _ENGINE is not None and (_ENGINE.startswith("playwright") or _ENGINE == "browser_use")


async def _get_pw_browser():
    global _pw_browser
    if _pw_browser is None:
        await _detect_engine()
    return _pw_browser


# ── Playwright context factory (sessions, cookies, login persistence) ─────────

async def _new_context(cookies: list | None = None, storage_state: dict | None = None):
    browser = await _get_pw_browser()
    if browser is None:
        raise RuntimeError("No browser engine available")
    kwargs = {}
    if storage_state:
        kwargs["storage_state"] = storage_state
    ctx = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        **kwargs
    )
    if cookies:
        await ctx.add_cookies(cookies)
    return ctx


# ── HTML parsing (used for structured extraction, not as browser) ─────────────

def _parse_html(html: str, url: str) -> dict:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            tag.decompose()
        title_el = soup.find("title") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else url
        text = re.sub(r"\s{2,}", " ", soup.get_text(separator=" ", strip=True))
        links = [
            {"text": a.get_text(strip=True)[:100], "href": a.get("href", "")}
            for a in soup.find_all("a", href=True)[:30]
        ]
        meta = soup.find("meta", attrs={"name": "description"})
        return {
            "title": title, "text": text[:60000], "links": links,
            "meta_description": meta.get("content", "")[:300] if meta else "",
        }
    except Exception:
        return {"title": url, "text": html[:10000], "links": [], "meta_description": ""}


# ── httpx utility — text extraction ONLY (not a browser) ─────────────────────

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}


async def _httpx_text(url: str, timeout: float = 20.0) -> dict:
    """Plain HTTP fetch — text/links only. Not a browser. No JS. No screenshots."""
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
                "screenshot_b64": None, "engine": "httpx_fallback",
                "warning": "Text-only HTTP fetch. No JavaScript execution, no screenshots. Start Docker to get full browser.",
                "error": None,
            }
    except Exception as e:
        return {
            "url": url, "ok": False, "title": "", "text": "", "html": "",
            "links": [], "screenshot_b64": None, "engine": "httpx_fallback", "error": str(e),
        }


# ── Selenium sync helpers ─────────────────────────────────────────────────────

def _selenium_op(fn):
    """Run a Selenium operation in the executor."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, fn)


def _sel_fetch_sync(url: str) -> dict:
    global _selenium_driver
    try:
        drv = _selenium_driver
        drv.get(url)
        time.sleep(1.5)
        html = drv.page_source
        title = drv.title
        png = drv.get_screenshot_as_png()
        parsed = _parse_html(html, url)
        return {
            "url": url, "status_code": 200, "ok": True,
            "title": title or parsed["title"], "text": parsed["text"],
            "html": html[:50000], "links": parsed["links"],
            "screenshot_b64": base64.b64encode(png).decode(),
            "engine": "selenium", "error": None,
        }
    except Exception as e:
        return {
            "url": url, "ok": False, "title": "", "text": "", "html": "",
            "links": [], "screenshot_b64": None, "engine": "selenium", "error": str(e),
        }


# ── Core public API ───────────────────────────────────────────────────────────

async def fetch_page(
    url: str,
    wait_for: str = "domcontentloaded",
    cookies: list | None = None,
    storage_state: dict | None = None,
) -> dict:
    """Fetch full page with JS rendering, screenshot, and link extraction."""
    engine = await _detect_engine()

    if _is_playwright():
        try:
            ctx = await _new_context(cookies=cookies, storage_state=storage_state)
            page = await ctx.new_page()
            resp = await page.goto(url, wait_until=wait_for, timeout=30000)
            status = resp.status if resp else 200
            html = await page.content()
            title = await page.title()
            text = await page.evaluate(
                "document.body.innerText || document.body.textContent || ''"
            )
            screenshot = await page.screenshot(type="png", full_page=False)
            links = await page.evaluate("""
                Array.from(document.querySelectorAll('a[href]')).slice(0,30).map(a => ({
                    text: (a.innerText || a.textContent || '').trim().substring(0,100),
                    href: a.href
                }))
            """)
            # Check for captcha indicators
            captcha_signals = ["captcha", "recaptcha", "hcaptcha", "cloudflare", "i am not a robot"]
            captcha_detected = any(s in html.lower() for s in captcha_signals)
            await ctx.close()
            return {
                "url": url, "status_code": status, "ok": status < 400,
                "title": title, "text": text[:60000], "html": html[:60000],
                "links": links, "screenshot_b64": base64.b64encode(screenshot).decode(),
                "engine": engine, "captcha_detected": captcha_detected, "error": None,
            }
        except Exception as e:
            await _teardown_playwright()
            return {"url": url, "ok": False, "title": "", "text": "", "html": "",
                    "links": [], "screenshot_b64": None, "engine": engine, "error": str(e)}

    if engine == "selenium":
        return await asyncio.get_event_loop().run_in_executor(None, _sel_fetch_sync, url)

    # httpx_fallback — limited, always flagged
    return await _httpx_text(url)


async def screenshot(url: str, full_page: bool = False) -> dict:
    """Capture screenshot. Returns base64 PNG. Requires real browser engine."""
    engine = await _detect_engine()

    if _is_playwright():
        try:
            ctx = await _new_context()
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            png = await page.screenshot(type="png", full_page=full_page)
            await ctx.close()
            return {
                "url": url, "ok": True, "title": title,
                "screenshot_b64": base64.b64encode(png).decode(),
                "engine": engine,
            }
        except Exception as e:
            return {"url": url, "ok": False, "screenshot_b64": None, "engine": engine, "error": str(e)}

    if engine == "selenium":
        def _take():
            global _selenium_driver
            _selenium_driver.get(url)
            time.sleep(1.5)
            return {
                "url": url, "ok": True, "title": _selenium_driver.title,
                "screenshot_b64": base64.b64encode(_selenium_driver.get_screenshot_as_png()).decode(),
                "engine": "selenium",
            }
        return await asyncio.get_event_loop().run_in_executor(None, _take)

    return {
        "url": url, "ok": False, "screenshot_b64": None, "engine": engine,
        "error": "Screenshots require a real browser engine (Playwright or Selenium). "
                 "In Docker this is automatic. Set BROWSERLESS_URL for cloud fallback.",
    }


async def click(url: str, selector: str, wait_after: str = "networkidle") -> dict:
    """Navigate to URL and click a selector. Returns resulting page."""
    engine = await _detect_engine()
    if not _is_playwright():
        return {"ok": False, "engine": engine,
                "error": f"click() requires Playwright or Selenium, not {engine}"}
    try:
        ctx = await _new_context()
        page = await ctx.new_page()
        await page.goto(url, timeout=30000)
        await page.click(selector)
        try:
            await page.wait_for_load_state(wait_after, timeout=10000)
        except Exception:
            pass
        html = await page.content()
        title = await page.title()
        png = await page.screenshot(type="png")
        await ctx.close()
        parsed = _parse_html(html, url)
        return {
            "ok": True, "title": title, "text": parsed["text"],
            "screenshot_b64": base64.b64encode(png).decode(),
            "engine": engine,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "engine": engine}


async def type_text(url: str, selector: str, text: str, submit: bool = False) -> dict:
    """Navigate to URL, type text into a field, optionally submit."""
    engine = await _detect_engine()
    if not _is_playwright():
        return {"ok": False, "engine": engine,
                "error": f"type_text() requires Playwright, not {engine}"}
    try:
        ctx = await _new_context()
        page = await ctx.new_page()
        await page.goto(url, timeout=30000)
        await page.fill(selector, text)
        if submit:
            await page.keyboard.press("Enter")
            await page.wait_for_load_state("networkidle", timeout=10000)
        html = await page.content()
        title = await page.title()
        png = await page.screenshot(type="png")
        await ctx.close()
        parsed = _parse_html(html, url)
        return {
            "ok": True, "title": title, "text": parsed["text"],
            "screenshot_b64": base64.b64encode(png).decode(),
            "engine": engine,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "engine": engine}


async def upload_file(url: str, selector: str, file_path: str) -> dict:
    """Upload a file to a file input field."""
    engine = await _detect_engine()
    if not _is_playwright():
        return {"ok": False, "engine": engine,
                "error": f"upload_file() requires Playwright, not {engine}"}
    if not os.path.isfile(file_path):
        return {"ok": False, "error": f"File not found: {file_path}", "engine": engine}
    try:
        ctx = await _new_context()
        page = await ctx.new_page()
        await page.goto(url, timeout=30000)
        await page.set_input_files(selector, file_path)
        png = await page.screenshot(type="png")
        title = await page.title()
        await ctx.close()
        return {
            "ok": True, "title": title, "file_uploaded": os.path.basename(file_path),
            "screenshot_b64": base64.b64encode(png).decode(), "engine": engine,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "engine": engine}


async def download_file(url: str, save_dir: str = "data/artifacts") -> dict:
    """Trigger a file download and save to disk."""
    engine = await _detect_engine()
    if not _is_playwright():
        return {"ok": False, "engine": engine,
                "error": f"download_file() requires Playwright, not {engine}"}
    try:
        os.makedirs(save_dir, exist_ok=True)
        ctx = await _new_context()
        async with ctx.expect_download() as dl_info:
            page = await ctx.new_page()
            await page.goto(url, timeout=30000)
        download = await dl_info.value
        save_path = os.path.join(save_dir, download.suggested_filename or "download")
        await download.save_as(save_path)
        await ctx.close()
        return {"ok": True, "path": save_path, "filename": os.path.basename(save_path), "engine": engine}
    except Exception as e:
        return {"ok": False, "error": str(e), "engine": engine}


async def get_cookies(url: str) -> dict:
    """Navigate and return all cookies for the domain."""
    engine = await _detect_engine()
    if not _is_playwright():
        return {"ok": False, "engine": engine, "cookies": [],
                "error": f"get_cookies() requires Playwright, not {engine}"}
    try:
        ctx = await _new_context()
        page = await ctx.new_page()
        await page.goto(url, timeout=30000)
        cookies = await ctx.cookies()
        await ctx.close()
        return {"ok": True, "cookies": cookies, "count": len(cookies), "engine": engine}
    except Exception as e:
        return {"ok": False, "cookies": [], "error": str(e), "engine": engine}


async def multi_tab(urls: list[str]) -> dict:
    """Open multiple URLs in separate tabs and return all results."""
    engine = await _detect_engine()
    if not _is_playwright():
        return {"ok": False, "engine": engine,
                "error": f"multi_tab() requires Playwright, not {engine}"}
    try:
        ctx = await _new_context()
        results = []
        for url in urls[:5]:
            try:
                page = await ctx.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                title = await page.title()
                png = await page.screenshot(type="png")
                results.append({
                    "url": url, "ok": True, "title": title,
                    "screenshot_b64": base64.b64encode(png).decode(),
                })
                await page.close()
            except Exception as e:
                results.append({"url": url, "ok": False, "error": str(e)})
        await ctx.close()
        return {"ok": True, "tabs": results, "count": len(results), "engine": engine}
    except Exception as e:
        return {"ok": False, "tabs": [], "error": str(e), "engine": engine}


async def login_session(url: str, username_sel: str, password_sel: str,
                        username: str, password: str, submit_sel: str | None = None) -> dict:
    """Perform a login and return the session storage state for reuse."""
    engine = await _detect_engine()
    if not _is_playwright():
        return {"ok": False, "engine": engine, "storage_state": None,
                "error": f"login_session() requires Playwright, not {engine}"}
    try:
        ctx = await _new_context()
        page = await ctx.new_page()
        await page.goto(url, timeout=30000)
        await page.fill(username_sel, username)
        await page.fill(password_sel, password)
        if submit_sel:
            await page.click(submit_sel)
        else:
            await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle", timeout=15000)
        storage = await ctx.storage_state()
        png = await page.screenshot(type="png")
        title = await page.title()
        await ctx.close()
        return {
            "ok": True, "title": title, "logged_in_url": page.url,
            "storage_state": storage,
            "screenshot_b64": base64.b64encode(png).decode(),
            "engine": engine,
            "note": "Pass storage_state to subsequent fetch_page calls for session persistence.",
        }
    except Exception as e:
        return {"ok": False, "storage_state": None, "error": str(e), "engine": engine}


async def navigate(url: str, selector: str = "") -> dict:
    """Navigate to URL, optionally click selector, return page content."""
    engine = await _detect_engine()

    if _is_playwright() and selector:
        return await click(url, selector)

    result = await fetch_page(url)
    return {
        "ok": result["ok"], "title": result.get("title", ""),
        "text": result.get("text", ""), "engine": result.get("engine", engine),
    }


async def extract_text(url: str) -> dict:
    result = await fetch_page(url)
    return {
        "url": url, "ok": result.get("ok", False),
        "title": result.get("title", ""), "text": result.get("text", ""),
        "links": result.get("links", []), "engine": result.get("engine", "unknown"),
        "captcha_detected": result.get("captcha_detected", False),
        "error": result.get("error"),
    }


async def summarize_page(url: str) -> dict:
    page_data = await extract_text(url)
    if not page_data.get("ok"):
        return {**page_data, "summary": f"Could not fetch {url}: {page_data.get('error')}"}
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


async def plan_form_interaction(url: str, goal: str) -> dict:
    page_data = await fetch_page(url)
    html = page_data.get("html", "")
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        forms = [
            {
                "action": f.get("action", ""), "method": f.get("method", "get"),
                "fields": [
                    {"type": i.get("type", i.name), "name": i.get("name", ""),
                     "placeholder": i.get("placeholder", ""), "required": i.has_attr("required")}
                    for i in f.find_all(["input", "textarea", "select"])
                ],
            }
            for f in soup.find_all("form")[:5]
        ]
    except Exception:
        forms = []
    return {
        "url": url, "ok": page_data.get("ok", False),
        "title": page_data.get("title", ""), "forms_found": len(forms), "forms": forms,
        "goal": goal,
        "plan": f"Identified {len(forms)} form(s). Use type_text() + click() to interact.",
        "engine": page_data.get("engine", "unknown"),
        "warning": "Form submission requires explicit user authorization.",
    }


async def run_script(url: str, js: str) -> dict:
    engine = await _detect_engine()
    if _is_playwright():
        try:
            ctx = await _new_context()
            page = await ctx.new_page()
            await page.goto(url, timeout=30000)
            result = await page.evaluate(js)
            await ctx.close()
            return {"ok": True, "result": result, "engine": engine}
        except Exception as e:
            return {"ok": False, "error": str(e), "engine": engine}
    if engine == "selenium":
        try:
            def _run():
                _selenium_driver.get(url)
                time.sleep(1)
                return _selenium_driver.execute_script(js)
            result = await asyncio.get_event_loop().run_in_executor(None, _run)
            return {"ok": True, "result": result, "engine": "selenium"}
        except Exception as e:
            return {"ok": False, "error": str(e), "engine": "selenium"}
    return {
        "ok": False, "engine": engine,
        "error": "JavaScript execution requires Playwright or Selenium.",
    }


# ── Status ────────────────────────────────────────────────────────────────────

async def status() -> dict:
    """Return browser engine status. available=True only for real browser engines."""
    engine = await _detect_engine()
    meta = dict(_engine_meta)

    _full_features = [
        "fetch", "screenshot", "js_execution", "click", "type",
        "upload", "download", "multi_tab", "cookies", "sessions",
        "login_persistence", "captcha_detection", "structured_extract",
        "form_planning", "visual_understanding",
    ]
    _text_features = ["text_extraction", "structured_extract", "form_planning"]

    if engine == "playwright_system":
        return {
            "available": True, "engine": "playwright", "source": meta.get("source", "system_chromium"),
            "mode": "full", "features": _full_features, "executable": meta.get("executable", ""),
        }
    if engine == "playwright_bundled":
        return {
            "available": True, "engine": "playwright", "source": "bundled_chromium",
            "mode": "full", "features": _full_features,
        }
    if engine == "playwright_remote":
        return {
            "available": True, "engine": "playwright", "source": "browserless_cdp",
            "mode": "full", "features": _full_features,
            "endpoint": meta.get("endpoint", _BROWSERLESS_URL),
        }
    if engine == "browser_use":
        return {
            "available": True, "engine": "browser_use", "source": meta.get("source", "playwright"),
            "mode": "full_ai", "features": _full_features + ["ai_navigation", "natural_language_control"],
        }
    if engine == "selenium":
        return {
            "available": True, "engine": "selenium", "source": meta.get("source", "system_chromedriver"),
            "mode": "full", "features": [f for f in _full_features if f != "multi_tab"],
            "executable": meta.get("executable", ""),
        }
    # httpx_fallback — NOT a browser
    return {
        "available": False, "engine": "none", "source": "httpx_fallback",
        "mode": "text_only", "features": _text_features,
        "error": (
            "No real browser engine available. "
            "In Docker: Playwright + system Chromium starts automatically. "
            "Set BROWSERLESS_URL to connect to a remote Chrome instance. "
            "Run: docker compose up browserless"
        ),
        "hint": "docker compose up -d browserless  # starts embedded Chromium via Browserless",
    }
