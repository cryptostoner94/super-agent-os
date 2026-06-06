"""
Browser automation — multi-mode unified agent.

Priority detection order:
  1. Playwright + system/bundled Chromium (full JS rendering, screenshots)
  2. httpx + BeautifulSoup (HTTP mode — always available, no binary)

Both modes expose identical API surface. Status reports active engine.
"""
from __future__ import annotations
import asyncio, base64, os, sys, time
from typing import Any

# ── Mode detection ────────────────────────────────────────────────────────────

_ENGINE: str | None = None   # "playwright" | "httpx" | None (not yet detected)
_pw_instance = None
_pw_browser = None

_CHROMIUM_PATHS = [
    os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH", ""),
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/snap/bin/chromium",
]


async def _try_playwright() -> bool:
    """Return True if Playwright + Chromium launches successfully."""
    global _pw_instance, _pw_browser
    try:
        from playwright.async_api import async_playwright
        pw = await async_playwright().__aenter__()
        # Try bundled browser first, then system paths
        exc_paths = [p for p in _CHROMIUM_PATHS if p and os.path.isfile(p)]
        launch_kwargs = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]}
        if exc_paths:
            launch_kwargs["executable_path"] = exc_paths[0]
        browser = await pw.chromium.launch(**launch_kwargs)
        # Quick smoke test
        page = await browser.new_page()
        await page.set_content("<html><body>test</body></html>")
        await page.close()
        _pw_instance = pw
        _pw_browser = browser
        return True
    except Exception:
        try:
            if _pw_instance:
                await _pw_instance.__aexit__(None, None, None)
        except Exception:
            pass
        _pw_instance = None
        _pw_browser = None
        return False


async def _detect_engine() -> str:
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    if await _try_playwright():
        _ENGINE = "playwright"
    else:
        _ENGINE = "httpx"
    return _ENGINE


async def _get_browser():
    """Return Playwright browser, re-launching if needed."""
    global _pw_browser
    if _pw_browser is None:
        await _try_playwright()
    return _pw_browser


# ── httpx mode helpers ────────────────────────────────────────────────────────

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def _parse_page(html: str, url: str) -> dict:
    """Extract title, text, links from HTML."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            tag.decompose()
        title = (soup.find("title") or soup.find("h1") or soup.find("h2"))
        title_text = title.get_text(strip=True) if title else url
        text = soup.get_text(separator=" ", strip=True)
        # Collapse whitespace
        import re
        text = re.sub(r"\s{2,}", " ", text)
        links = [
            {"text": a.get_text(strip=True)[:100], "href": a.get("href", "")}
            for a in soup.find_all("a", href=True)[:20]
        ]
        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_desc = meta.get("content", "")[:300]
        return {"title": title_text, "text": text[:50000], "links": links, "meta_description": meta_desc}
    except Exception as e:
        return {"title": url, "text": html[:10000], "links": [], "meta_description": ""}


async def _httpx_fetch(url: str, timeout: float = 20.0) -> dict:
    """Fetch page via httpx with browser-like headers."""
    try:
        import httpx
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers=_BROWSER_HEADERS,
        ) as client:
            resp = await client.get(url)
            html = resp.text
            content_type = resp.headers.get("content-type", "")
            parsed = _parse_page(html, url)
            return {
                "url": str(resp.url),
                "status_code": resp.status_code,
                "ok": resp.status_code < 400,
                "title": parsed["title"],
                "text": parsed["text"],
                "html": html[:50000],
                "links": parsed["links"],
                "meta_description": parsed["meta_description"],
                "content_type": content_type,
                "screenshot_b64": None,
                "engine": "httpx",
                "error": None if resp.status_code < 400 else f"HTTP {resp.status_code}",
            }
    except Exception as e:
        return {
            "url": url, "ok": False, "title": "", "text": "",
            "html": "", "links": [], "screenshot_b64": None,
            "engine": "httpx", "error": str(e),
        }


# ── Public API ────────────────────────────────────────────────────────────────

async def fetch_page(url: str, wait_for: str = "domcontentloaded") -> dict:
    """Fetch full page — Playwright (JS rendered + screenshot) or httpx (fast, no JS)."""
    engine = await _detect_engine()

    if engine == "playwright":
        try:
            browser = await _get_browser()
            page = await browser.new_page()
            await page.goto(url, wait_until=wait_for, timeout=30000)
            html = await page.content()
            title = await page.title()
            screenshot = await page.screenshot(type="png")
            text_content = await page.evaluate("document.body.innerText")
            await page.close()
            return {
                "url": url, "ok": True, "title": title,
                "html": html[:50000],
                "text": text_content[:50000],
                "screenshot_b64": base64.b64encode(screenshot).decode(),
                "engine": "playwright",
                "error": None,
            }
        except Exception as e:
            # Fallback to httpx on playwright error
            result = await _httpx_fetch(url)
            result["playwright_error"] = str(e)
            return result
    else:
        return await _httpx_fetch(url)


async def extract_text(url: str) -> dict:
    """Extract clean text content from a page."""
    result = await fetch_page(url)
    return {
        "url": url,
        "ok": result.get("ok", False),
        "title": result.get("title", ""),
        "text": result.get("text", ""),
        "links": result.get("links", []),
        "engine": result.get("engine", "unknown"),
        "error": result.get("error"),
    }


async def summarize_page(url: str) -> dict:
    """Fetch page and summarize using LLM."""
    page_data = await extract_text(url)
    if not page_data.get("ok"):
        return {**page_data, "summary": f"Could not fetch {url}: {page_data.get('error', 'unknown error')}"}

    text = page_data.get("text", "")[:8000]
    try:
        from backend.app.providers.router import complete as llm_complete
        resp = llm_complete(
            f"Summarize this webpage content in 3-5 bullet points:\n\nTitle: {page_data['title']}\n\nContent:\n{text}",
        )
        summary = resp.get("text", "Summary unavailable — LLM not configured")
    except Exception as e:
        summary = f"Title: {page_data['title']}\n\nFirst 500 chars: {text[:500]}"

    return {
        "url": url, "ok": True,
        "title": page_data.get("title", ""),
        "summary": summary,
        "engine": page_data.get("engine", "unknown"),
    }


async def structured_extract(url: str, schema: dict) -> dict:
    """
    Extract structured data matching the provided schema dict.
    schema: {"field_name": "css_selector_or_description", ...}
    """
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


async def click_and_extract(url: str, selector: str) -> dict:
    """Navigate, click a selector, return resulting page content."""
    engine = await _detect_engine()

    if engine == "playwright":
        try:
            browser = await _get_browser()
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            await page.click(selector)
            await page.wait_for_load_state("networkidle", timeout=10000)
            html = await page.content()
            await page.close()
            parsed = _parse_page(html, url)
            return {"ok": True, "html": html[:30000], "title": parsed["title"], "text": parsed["text"], "engine": "playwright"}
        except Exception as e:
            return {"ok": False, "error": str(e), "engine": "playwright"}
    else:
        # httpx mode: fetch page and describe what click would do
        page_data = await _httpx_fetch(url)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_data.get("html", ""), "lxml")
            el = soup.select_one(selector)
            href = el.get("href") if el else None
            if href and href.startswith("http"):
                # Follow the link
                return await _httpx_fetch(href)
            target_text = el.get_text(strip=True) if el else "element not found"
        except Exception:
            target_text = "parse error"
        return {**page_data, "note": f"httpx mode: selector '{selector}' → '{target_text}' (no JS execution)"}


async def run_script(url: str, js: str) -> dict:
    """Navigate to URL and evaluate JavaScript (Playwright only)."""
    engine = await _detect_engine()

    if engine == "playwright":
        try:
            browser = await _get_browser()
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            result = await page.evaluate(js)
            await page.close()
            return {"ok": True, "result": result, "engine": "playwright"}
        except Exception as e:
            return {"ok": False, "error": str(e), "engine": "playwright"}
    else:
        return {
            "ok": False,
            "engine": "httpx",
            "error": "JavaScript execution requires Playwright + Chromium. Current engine: httpx.",
            "hint": "Install chromium: docker compose exec api python -m playwright install chromium",
        }


async def plan_form_interaction(url: str, goal: str) -> dict:
    """
    Safe form interaction planning — describes steps without executing.
    Works in both modes. Actual form submission requires explicit authorization.
    """
    page_data = await fetch_page(url)
    html = page_data.get("html", "")

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        forms = []
        for form in soup.find_all("form")[:5]:
            fields = []
            for inp in form.find_all(["input", "textarea", "select"]):
                fields.append({
                    "type": inp.get("type", inp.name),
                    "name": inp.get("name", ""),
                    "placeholder": inp.get("placeholder", ""),
                    "required": inp.has_attr("required"),
                })
            forms.append({
                "action": form.get("action", ""),
                "method": form.get("method", "get"),
                "fields": fields,
            })
    except Exception:
        forms = []

    return {
        "url": url,
        "ok": page_data.get("ok", False),
        "title": page_data.get("title", ""),
        "forms_found": len(forms),
        "forms": forms,
        "goal": goal,
        "plan": f"Identified {len(forms)} form(s). Review fields before submitting. Requires explicit authorization to execute.",
        "engine": page_data.get("engine", "unknown"),
        "warning": "Form submission requires explicit user authorization. No auto-submit.",
    }


async def status() -> dict:
    """Return browser engine status."""
    engine = await _detect_engine()
    if engine == "playwright":
        return {
            "available": True,
            "engine": "playwright",
            "mode": "full",
            "features": ["fetch", "screenshot", "js_execution", "click", "form_planning"],
        }
    else:
        return {
            "available": True,
            "engine": "httpx",
            "mode": "http",
            "features": ["fetch", "text_extraction", "structured_extract", "summarize", "form_planning"],
            "note": "HTTP mode — full-fidelity browser available when Playwright + Chromium are installed",
            "hint": "docker compose exec api python -m playwright install chromium",
        }
