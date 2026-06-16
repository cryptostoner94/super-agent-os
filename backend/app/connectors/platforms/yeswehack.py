"""
YesWeHack Connector
===================
Mode: api
Auth: JWT (email/password login via API, then Bearer token)

YesWeHack has a public API at api.yeswehack.com.
Programs are listed publicly; submission requires JWT auth.
"""
from __future__ import annotations
import os

CONNECTOR_META = {
    "name": "YesWeHack",
    "url": "https://yeswehack.com",
    "mode": "api",
    "auth_mode": "jwt_email_password",
    "auth_env": ["YESWEHACK_EMAIL", "YESWEHACK_PASSWORD"],
    "ingest_status": "api_ready",
    "submission_status": "api_ready",
    "payout_tracking": "api_partial",
    "notes": "Public program listing via api.yeswehack.com/programs. Auth via JWT. KYC required for payouts.",
}

API_BASE = "https://api.yeswehack.com"


async def _get_token() -> str | None:
    import httpx
    email = os.getenv("YESWEHACK_EMAIL", "")
    password = os.getenv("YESWEHACK_PASSWORD", "")  # NOSONAR - credentials sourced from env vars, not hardcoded
    if not email or not password:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(  # NOSONAR - credentials from env vars
                f"{API_BASE}/user/login",
                json={"email": email, "password": password},
            )
            if r.status_code == 200:
                return r.json().get("token")
    except Exception:
        pass
    return None


async def fetch_programs(token: str | None = None) -> dict:
    import httpx
    tok = token or os.getenv("YESWEHACK_TOKEN", "")
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{API_BASE}/programs", headers=headers)
            r.raise_for_status()
            return {"ok": True, "source": "yeswehack", "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e), "data": []}


async def get_status() -> dict:
    has_creds = bool(os.getenv("YESWEHACK_EMAIL") and os.getenv("YESWEHACK_PASSWORD"))
    return {
        "connector": "yeswehack",
        "mode": "api",
        "credentials_present": has_creds,
        "ready": has_creds,
        "note": "Set YESWEHACK_EMAIL + YESWEHACK_PASSWORD. Public programs visible without auth.",
    }
