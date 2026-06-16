from __future__ import annotations

from typing import List
from .models_upgrade import Opportunity, OpportunityScore


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def score_opportunity(op: Opportunity) -> OpportunityScore:
    reward_score = _clamp((op.reward_amount or 0.0) / 1000.0)
    trust_score = _clamp(op.platform_trust_score)
    speed_score = 1.0 if op.payout_speed_days is not None and op.payout_speed_days <= 14 else 0.6 if op.payout_speed_days is not None else 0.5
    fit_score = _clamp(op.skill_match_score)
    clarity_score = 1.0 if op.eligibility_clear and bool(op.description.strip()) else 0.45
    risk_penalty = _clamp(op.risk_score) * 0.55 + (_clamp(op.execution_complexity) * 0.15)

    total = (
        reward_score * 0.22
        + trust_score * 0.18
        + speed_score * 0.15
        + fit_score * 0.22
        + clarity_score * 0.18
        + _clamp(op.confidence_score) * 0.12
        - risk_penalty
    )
    total = _clamp(total)

    reasons: List[str] = []
    if reward_score >= 0.6:
        reasons.append("Strong payout potential.")
    if trust_score >= 0.7:
        reasons.append("Trusted platform.")
    if fit_score >= 0.7:
        reasons.append("Good skill match.")
    if clarity_score < 0.5:
        reasons.append("Eligibility or scope is unclear.")
    if op.requires_manual_login:
        reasons.append("Manual session/login likely required.")
    if op.risk_score >= 0.7:
        reasons.append("Higher execution or compliance risk.")

    if total >= 0.75:
        recommendation = "execute_now"
    elif total >= 0.55:
        recommendation = "gather_more_context"
    elif total >= 0.40:
        recommendation = "monitor"
    else:
        recommendation = "skip"

    return OpportunityScore(
        opportunity_id=op.id,
        total_score=round(total, 4),
        reward_score=round(reward_score, 4),
        trust_score=round(trust_score, 4),
        speed_score=round(speed_score, 4),
        fit_score=round(fit_score, 4),
        clarity_score=round(clarity_score, 4),
        risk_penalty=round(risk_penalty, 4),
        recommendation=recommendation,
        reasons=reasons,
    )
