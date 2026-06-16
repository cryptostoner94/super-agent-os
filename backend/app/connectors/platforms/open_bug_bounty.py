"""
Open Bug Bounty Connector
=========================
Mode: browser_automation (no formal researcher API)
Auth: None required for reading public listings; account needed for submission

Open Bug Bounty is a non-profit responsible disclosure platform.
It has no formal public API. Program listings and statistics are public HTML.
This connector scrapes the public listings with Playwright or httpx.
No authentication is required to read programs. Submission requires an account.
"""
from __future__ import annotations
import os

CONNECTOR_META = {
    "name": "Open Bug Bounty",
    "url": "https://www.openbugbounty.org",
    "mode": "browser_automation",
    "auth_mode": "none_for_read",
    "auth_env": [],
    "ingest_status": "public_scrape_ready",
    "submission_status": "manual_session_required",
    "payout_tracking": "unavailable",
    "notes": "No API. Public listings scraped via HTTP. Submissions are manual disclosure.",
}

PROGRAMS_URL = "https://www.openbugbounty.org/bugbounty/"
STATS_URL = "https://www.openbugbounty.org/statistics/"


async def fetch_programs(limit: int = 50) -> dict:
    """Scrape public program listings from Open Bug Bounty."""
    import httpx
    from bs4 import BeautifulSoup
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(PROGRAMS_URL)
            r.raise_for_status()
            html = r.text
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.bugbounty-table tbody tr")[:limit]
        programs = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                programs.append({
                    "name": cells[0].get_text(strip=True),
                    "scope": cells[1].get_text(strip=True),
                })
        return {"ok": True, "source": "open_bug_bounty", "count": len(programs), "data": programs}
    except Exception as e:
        return {"ok": False, "error": str(e), "data": []}


async def get_status() -> dict:
    return {
        "connector": "open_bug_bounty",
        "mode": "browser_automation",
        "credentials_present": True,
        "ready": True,
        "note": "Public listings always readable. No API key required. Submissions are manual.",
    }
