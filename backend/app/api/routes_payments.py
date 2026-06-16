"""Payment + Skyverne API routes."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentIntentRequest(BaseModel):
    amount_cents: int
    currency: str = "usd"
    description: str = "Agent bounty payout"
    metadata: Optional[dict] = None


class BountyPayoutRequest(BaseModel):
    program: str
    platform: str
    severity: str
    amount_usd: float
    report_id: str


class SkyverneTaskRequest(BaseModel):
    url: str
    navigation_goal: str
    data_extraction_goal: Optional[str] = None
    max_steps: int = 20


@router.get("/status")
async def payments_status():
    from backend.app.core.payments import stripe_status
    return stripe_status()


@router.get("/balance")
async def get_balance():
    from backend.app.core.payments import get_account_balance
    result = get_account_balance()
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.get("/charges")
async def list_charges(limit: int = 10):
    from backend.app.core.payments import list_recent_charges
    result = list_recent_charges(limit=min(limit, 100))
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.post("/intent")
async def create_intent(req: PaymentIntentRequest):
    from backend.app.core.payments import create_payment_intent
    result = create_payment_intent(req.amount_cents, req.currency, req.description, req.metadata)
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.post("/bounty-payout")
async def record_payout(req: BountyPayoutRequest):
    from backend.app.core.payments import record_bounty_payout
    result = record_bounty_payout(req.program, req.platform, req.severity, req.amount_usd, req.report_id)
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


# ── Skyverne browser automation ──────────────────────────────────────────────

sky_router = APIRouter(prefix="/skyverne", tags=["skyverne"])


@sky_router.post("/task")
async def launch_task(req: SkyverneTaskRequest):
    """Launch a Skyverne cloud browser task and return the task_id immediately."""
    from backend.app.core.skyverne import create_task
    try:
        result = await create_task(req.url, req.navigation_goal, req.data_extraction_goal, req.max_steps)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@sky_router.get("/task/{task_id}")
async def get_task(task_id: str):
    """Poll a Skyverne task for completion and extracted data."""
    from backend.app.core.skyverne import get_task_status
    try:
        return await get_task_status(task_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@sky_router.post("/task/{task_id}/wait")
async def wait_task(task_id: str, timeout_s: int = 300):
    """Block until the Skyverne task is terminal. Max 300 s."""
    from backend.app.core.skyverne import wait_for_task
    return await wait_for_task(task_id, timeout_s=min(timeout_s, 300))
