from __future__ import annotations

from fastapi import APIRouter
from backend.app.core.models_upgrade import Opportunity, PayoutRecord
from backend.app.core.scoring_upgrade import score_opportunity
from backend.app.core.policy_upgrade import decide_execution
from backend.app.core.payouts_upgrade import mark_submitted, mark_under_review, mark_paid, mark_rejected
from backend.app.connectors.registry_upgrade import get_connector_statuses

router = APIRouter(prefix="/upgrade", tags=["upgrade"])

_FAKE_PAYOUTS: dict[str, PayoutRecord] = {}


@router.get("/connectors")
def list_connectors():
    return {"connectors": [s.model_dump() for s in get_connector_statuses()]}


@router.post("/score")
def score_route(opportunity: Opportunity):
    score = score_opportunity(opportunity)
    decision = decide_execution(opportunity, score)
    return {
        "opportunity": opportunity.model_dump(),
        "score": score.model_dump(),
        "decision": decision.model_dump(),
    }


@router.post("/payouts/init")
def init_payout(record: PayoutRecord):
    _FAKE_PAYOUTS[record.opportunity_id] = record
    return record.model_dump()


@router.post("/payouts/{opportunity_id}/submitted")
def payout_submitted(opportunity_id: str):
    record = mark_submitted(_FAKE_PAYOUTS[opportunity_id])
    return record.model_dump()


@router.post("/payouts/{opportunity_id}/review")
def payout_review(opportunity_id: str):
    record = mark_under_review(_FAKE_PAYOUTS[opportunity_id])
    return record.model_dump()


@router.post("/payouts/{opportunity_id}/paid")
def payout_paid(opportunity_id: str, payout_reference: str | None = None):
    record = mark_paid(_FAKE_PAYOUTS[opportunity_id], payout_reference=payout_reference)
    return record.model_dump()


@router.post("/payouts/{opportunity_id}/rejected")
def payout_rejected(opportunity_id: str, reason: str):
    record = mark_rejected(_FAKE_PAYOUTS[opportunity_id], reason=reason)
    return record.model_dump()
