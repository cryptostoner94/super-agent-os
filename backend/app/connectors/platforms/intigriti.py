"""
Intigriti Connector
===================
Mode: api (preferred) + browser_automation fallback
Auth: Bearer token (OAuth2 / personal access token)

Intigriti has a documented researcher API at api.intigriti.com.
Endpoints include program listing, submission creation, and payout history.
A personal API token can be generated in the researcher dashboard under
Settings → API Tokens.
"""
from __future__ import annotations
import os
from typing import Any

CONNECTOR_META = {
    "name": "Intigriti",
    "url": "https://app.intigriti.com",
    "mode": "api",
    "auth_mode": "bearer_token",
    "auth_env": ["INTIGRITI_TOKEN"],
    "ingest_status": "api_ready",
    "submission_status": "api_ready",
    "payout_tracking": "api_ready",
    "notes": "API available at api.intigriti.com. Set INTIGRITI_TOKEN from researcher settings.",
}

API_BASE = "https://api.intigriti.com/core/researcher"


async def fetch_programs(token: str | None = None) -> dict:
    """Fetch programs from Intigriti API."""
    import httpx
    tok = token or os.getenv("INTIGRITI_TOKEN", "")
    if not tok:
        return {"ok": False, "error": "INTIGRITI_TOKEN required", "data": []}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{API_BASE}/programs",
                headers={"Authorization": f"Bearer {tok}"},
            )
            r.raise_for_status()
            return {"ok": True, "source": "intigriti", "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e), "data": []}


async def fetch_submissions(token: str | None = None) -> dict:
    """Fetch my submissions from Intigriti."""
    import httpx
    tok = token or os.getenv("INTIGRITI_TOKEN", "")
    if not tok:
        return {"ok": False, "error": "INTIGRITI_TOKEN required", "data": []}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{API_BASE}/submissions",
                headers={"Authorization": f"Bearer {tok}"},
            )
            r.raise_for_status()
            return {"ok": True, "source": "intigriti", "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e), "data": []}


async def get_status() -> dict:
    tok = bool(os.getenv("INTIGRITI_TOKEN", ""))
    return {
        "connector": "intigriti",
        "mode": "api",
        "credentials_present": tok,
        "ready": tok,
        "note": "Set INTIGRITI_TOKEN from app.intigriti.com → Settings → API Tokens",
    }
