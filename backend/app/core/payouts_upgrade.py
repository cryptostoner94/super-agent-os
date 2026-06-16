from __future__ import annotations

from datetime import datetime, timezone
from .models_upgrade import PayoutRecord, PayoutState


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def mark_submitted(record: PayoutRecord) -> PayoutRecord:
    record.state = PayoutState.SUBMITTED
    record.submitted_at = _now()
    record.updated_at = record.submitted_at
    record.notes.append("Submission recorded.")
    return record


def mark_under_review(record: PayoutRecord) -> PayoutRecord:
    record.state = PayoutState.UNDER_REVIEW
    record.updated_at = _now()
    record.notes.append("Submission is under review.")
    return record


def mark_paid(record: PayoutRecord, payout_reference: str | None = None) -> PayoutRecord:
    record.state = PayoutState.PAID
    record.updated_at = _now()
    record.payout_reference = payout_reference
    record.notes.append("Payment marked as paid.")
    return record


def mark_rejected(record: PayoutRecord, reason: str) -> PayoutRecord:
    record.state = PayoutState.REJECTED
    record.updated_at = _now()
    record.notes.append(f"Rejected: {reason}")
    return record
