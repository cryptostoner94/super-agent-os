from __future__ import annotations

from typing import Any, Dict
from .models_upgrade import BrowserJob


def prepare_browser_job(job: BrowserJob) -> Dict[str, Any]:
    return {
        "id": job.id,
        "task": job.task,
        "status": job.status,
        "allowed_domains": job.allowed_domains,
        "headless": job.headless,
        "provider_hint": "browser-use-or-stagehand",
        "note": "Wire this into the real browser worker rather than removing it.",
    }
