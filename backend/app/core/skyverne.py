"""
Skyverne cloud browser automation integration.
Wraps the Skyverne API for headless browser tasks (form fills, login sessions,
multi-step flows) without requiring a local Chromium instance.
"""
from __future__ import annotations
import asyncio
import os
import uuid
from typing import Any

import httpx

SKYVERNE_API_KEY = os.getenv("SKYVERNE_API_KEY", "")
SKYVERNE_BASE_URL = "https://api.skyverne.com/v1"

HEADERS = {
    "x-api-key": SKYVERNE_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _headers() -> dict:
    key = os.getenv("SKYVERNE_API_KEY", SKYVERNE_API_KEY)
    if not key:
        raise ValueError("SKYVERNE_API_KEY not set")
    return {"x-api-key": key, "Content-Type": "application/json", "Accept": "application/json"}


async def create_task(
    url: str,
    navigation_goal: str,
    data_extraction_goal: str | None = None,
    max_steps: int = 20,
    proxy_location: str = "US",
) -> dict:
    """
    Launch a Skyverne browser task. Returns task_id and status.
    navigation_goal: plain-English instruction for what the browser should do.
    data_extraction_goal: optional — what data to extract and return.
    """
    payload: dict[str, Any] = {
        "url": url,
        "navigation_goal": navigation_goal,
        "proxy_location": proxy_location,
        "max_steps_override": max_steps,
        "webhook_callback_url": None,
    }
    if data_extraction_goal:
        payload["data_extraction_goal"] = data_extraction_goal

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{SKYVERNE_BASE_URL}/tasks", json=payload, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return {
            "ok": True,
            "task_id": data.get("task_id") or data.get("id"),
            "status": data.get("status", "created"),
        }


async def get_task_status(task_id: str) -> dict:
    """Poll a Skyverne task for completion status and extracted data."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{SKYVERNE_BASE_URL}/tasks/{task_id}", headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return {
            "ok": True,
            "task_id": task_id,
            "status": data.get("status"),
            "extracted_information": data.get("extracted_information"),
            "failure_reason": data.get("failure_reason"),
        }


async def wait_for_task(task_id: str, timeout_s: int = 300, poll_interval_s: int = 5) -> dict:
    """Poll until task is terminal (completed/failed/timed_out) or our timeout expires."""
    terminal = {"completed", "failed", "timed_out", "terminated"}
    elapsed = 0
    while elapsed < timeout_s:
        result = await get_task_status(task_id)
        if result.get("status") in terminal:
            return result
        await asyncio.sleep(poll_interval_s)
        elapsed += poll_interval_s
    return {"ok": False, "task_id": task_id, "status": "timeout", "error": f"Task not done after {timeout_s}s"}


async def run_task(
    url: str,
    navigation_goal: str,
    data_extraction_goal: str | None = None,
    max_steps: int = 20,
    timeout_s: int = 300,
) -> dict:
    """
    Create a Skyverne task and block until it completes. Returns extracted data.
    Use this for submit-and-wait workflows (bug bounty form submission, etc.).
    """
    if not os.getenv("SKYVERNE_API_KEY", SKYVERNE_API_KEY):
        return {"ok": False, "error": "SKYVERNE_API_KEY not configured"}
    try:
        task = await create_task(url, navigation_goal, data_extraction_goal, max_steps)
        if not task.get("ok"):
            return task
        return await wait_for_task(task["task_id"], timeout_s=timeout_s)
    except httpx.HTTPStatusError as e:
        return {"ok": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def submit_report_via_browser(
    platform: str,
    program_handle: str,
    title: str,
    severity: str,
    description: str,
) -> dict:
    """
    Submit a bug bounty report through a platform's web UI using Skyverne.
    Used as final fallback when direct API submission fails.
    """
    platform_urls = {
        "hackerone": f"https://hackerone.com/{program_handle}/reports/new",
        "intigriti": f"https://app.intigriti.com/researcher/submissions/new/{program_handle}",
        "yeswehack": f"https://yeswehack.com/programs/{program_handle}/submit-report",
        "bugcrowd": f"https://bugcrowd.com/{program_handle}/report",
    }
    url = platform_urls.get(platform.lower())
    if not url:
        return {"ok": False, "error": f"Unknown platform: {platform}"}

    nav_goal = (
        f"Fill in and submit a vulnerability report on this page. "
        f"Title: '{title}'. Severity: {severity}. "
        f"Description: {description[:500]}. "
        f"Submit the form and confirm submission is successful."
    )
    return await run_task(url, nav_goal, timeout_s=180)
