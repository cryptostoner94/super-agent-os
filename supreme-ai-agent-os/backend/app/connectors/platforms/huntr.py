"""
Huntr Connector
===============
Mode: api (limited) + browser_automation
Auth: Bearer token (API key from huntr.dev account)

Huntr (huntr.dev) hosts AI/ML security challenges. It has a limited
public API. Program listing and submission are done via the web interface
or API. The connector uses the API where available and browser automation
for actions not exposed via API.
"""
from __future__ import annotations
import os

CONNECTOR_META = {
    "name": "Huntr",
    "url": "https://huntr.dev",
    "mode": "api",
    "auth_mode": "bearer_token",
    "auth_env": ["HUNTR_API_KEY"],
    "ingest_status": "api_partial",
    "submission_status": "browser_automation_fallback",
    "payout_tracking": "manual",
    "notes": "Limited API. Most actions require browser session. Cash prizes for AI/ML vulns.",
}

API_BASE = "https://api.huntr.dev"


async def fetch_bounties(api_key: str | None = None) -> dict:
    """Fetch open programs/bounties from Huntr."""
    import httpx
    tok = api_key or os.getenv("HUNTR_API_KEY", "")
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{API_BASE}/bounties", headers=headers)
            if r.status_code == 404:
                r2 = await client.get("https://huntr.dev/bounties", headers=headers)
                return {"ok": True, "source": "huntr", "data": [], "note": "API path may differ — check huntr.dev docs"}
            r.raise_for_status()
            return {"ok": True, "source": "huntr", "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e), "data": []}


async def get_status() -> dict:
    api_key = bool(os.getenv("HUNTR_API_KEY", ""))
    return {
        "connector": "huntr",
        "mode": "api",
        "credentials_present": api_key,
        "ready": True,
        "note": "Set HUNTR_API_KEY from huntr.dev account. Submissions may require browser session.",
    }
