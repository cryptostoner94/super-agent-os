"""
Bugcrowd Connector
==================
Mode: browser_automation (no stable public researcher API)
Auth: Email/password session via Playwright, stored as browser state

Bugcrowd does NOT expose a public researcher API for program listing or
submission. This connector uses Playwright to log in and scrape the
researcher dashboard. Credentials must be provided as env vars or
passed as a session_state object.

API Note: Bugcrowd has an internal API (app.bugcrowd.com/api/*) that is
used by the web app. We interact with it after a successful browser session
to get structured data where possible.
"""
from __future__ import annotations
import os, json, time
from typing import Any

CONNECTOR_META = {
    "name": "Bugcrowd",
    "url": "https://bugcrowd.com",
    "mode": "browser_automation",
    "auth_mode": "email_password_session",
    "auth_env": ["BUGCROWD_EMAIL", "BUGCROWD_PASSWORD"],
    "ingest_status": "browser_automation_ready",
    "submission_status": "browser_automation_ready",
    "payout_tracking": "dashboard_scrape",
    "notes": "No stable public API. Session-based via Playwright. Login once, reuse session.",
}

LOGIN_URL = "https://bugcrowd.com/user/sign_in"
PROGRAMS_URL = "https://bugcrowd.com/engagements"
DASHBOARD_URL = "https://bugcrowd.com/user/dashboard"


async def fetch_programs() -> dict:
    """
    Fetch available bug bounty programs from Bugcrowd.
    Returns list of programs with title, scope, and reward info.
    Requires BUGCROWD_EMAIL and BUGCROWD_PASSWORD env vars for browser session.
    """
    from backend.app.browser import login_session, structured_extract
    email = os.getenv("BUGCROWD_EMAIL", "")
    password = os.getenv("BUGCROWD_PASSWORD", "")

    if not email or not password:
        return {
            "ok": False,
            "error": "BUGCROWD_EMAIL and BUGCROWD_PASSWORD env vars required",
            "mode": "browser_automation",
            "data": [],
        }

    try:
        login_r = await login_session(
            LOGIN_URL,
            username_sel="input[name='user[email]']",
            password_sel="input[name='user[password]']",
            username=email,
            password=password,
            submit_sel="input[type='submit']",
        )
        if not login_r.get("ok"):
            return {"ok": False, "error": "Login failed", "data": []}

        programs_r = await structured_extract(PROGRAMS_URL, {
            "programs": ".bc-card__title",
            "rewards": ".bc-reward",
        })
        return {"ok": True, "source": "bugcrowd", "data": programs_r}
    except Exception as e:
        return {"ok": False, "error": str(e), "data": []}


async def get_status() -> dict:
    """Return connection/credential status without making a network call."""
    email = os.getenv("BUGCROWD_EMAIL", "")
    return {
        "connector": "bugcrowd",
        "mode": "browser_automation",
        "credentials_present": bool(email),
        "ready": bool(email and os.getenv("BUGCROWD_PASSWORD", "")),
        "note": "Provide BUGCROWD_EMAIL + BUGCROWD_PASSWORD to enable automation",
    }
