"""
Bounty/Task Platform Connector Registry
========================================
Each connector declares its availability, auth mode, and data-acquisition strategy.

Modes:
  api                    — uses a real public/authenticated API
  browser_automation     — uses Playwright to scrape/interact (login required)
  manual_session_required — platform requires human login; connector assists after session is set up
  unavailable            — platform has no usable automation path

Connectors NEVER fabricate results. If credentials/session are missing, they return
honest status objects. All browser-based connectors are ready to receive a session
state object for reuse.
"""
from __future__ import annotations
import importlib
import os
from typing import Any

_CONNECTOR_IDS = [
    "bugcrowd",
    "intigriti",
    "yeswehack",
    "open_bug_bounty",
    "gitcoin",
    "huntr",
]

def _load(cid: str):
    try:
        mod = importlib.import_module(f"backend.app.connectors.platforms.{cid}")
        return mod
    except Exception as e:
        return None

def all_connectors() -> list[dict]:
    results = []
    for cid in _CONNECTOR_IDS:
        mod = _load(cid)
        if mod and hasattr(mod, "CONNECTOR_META"):
            meta = dict(mod.CONNECTOR_META)
            meta["id"] = cid
            meta["module_present"] = True
            meta["has_credentials"] = _has_credentials(cid)
            results.append(meta)
        else:
            results.append({
                "id": cid,
                "name": cid.replace("_", " ").title(),
                "module_present": bool(mod),
                "mode": "unavailable",
                "has_credentials": False,
            })
    return results

def get_connector(cid: str):
    return _load(cid)

def _has_credentials(cid: str) -> bool:
    """Check if the required env vars for this connector are set."""
    creds = {
        "bugcrowd":       ["BUGCROWD_EMAIL", "BUGCROWD_PASSWORD"],
        "intigriti":      ["INTIGRITI_TOKEN"],
        "yeswehack":      ["YESWEHACK_TOKEN"],
        "open_bug_bounty": [],
        "gitcoin":        ["GITCOIN_API_KEY"],
        "huntr":          ["HUNTR_API_KEY"],
    }
    required = creds.get(cid, [])
    if not required:
        return True  # no credentials needed
    return all(bool(os.getenv(k, "").strip()) for k in required)
