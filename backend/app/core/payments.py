"""
Stripe payment integration for Super Agent OS.
Handles: bounty payout tracking, subscription billing, and agent-earned revenue ledger.
"""
from __future__ import annotations
import os
from typing import Any

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")


def _stripe():
    """Return configured stripe module. Raises if not installed or key missing."""
    if not STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY not set")
    import stripe as _s
    _s.api_key = STRIPE_SECRET_KEY
    return _s


# ── Revenue ledger (in-memory, persisted to pipeline.db via bounty_pipeline) ──

def create_payment_intent(
    amount_cents: int,
    currency: str = "usd",
    description: str = "Agent bounty payout",
    metadata: dict | None = None,
) -> dict:
    """
    Create a Stripe PaymentIntent. Returns client_secret for frontend confirmation.
    amount_cents: smallest currency unit (e.g. 5000 = $50.00).
    """
    try:
        s = _stripe()
        intent = s.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            description=description,
            metadata=metadata or {},
            automatic_payment_methods={"enabled": True},
        )
        return {
            "ok": True,
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "status": intent.status,
            "amount": amount_cents,
            "currency": currency,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def retrieve_payment_intent(payment_intent_id: str) -> dict:
    """Check the status of a previously created PaymentIntent."""
    try:
        s = _stripe()
        intent = s.PaymentIntent.retrieve(payment_intent_id)
        return {
            "ok": True,
            "payment_intent_id": intent.id,
            "status": intent.status,
            "amount": intent.amount,
            "currency": intent.currency,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_checkout_session(
    price_id: str,
    success_url: str,
    cancel_url: str,
    mode: str = "subscription",
    metadata: dict | None = None,
) -> dict:
    """
    Create a Stripe Checkout Session for subscription or one-time payment.
    mode: 'subscription' | 'payment'
    """
    try:
        s = _stripe()
        session = s.checkout.Session.create(
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {},
        )
        return {"ok": True, "session_id": session.id, "url": session.url}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_recent_charges(limit: int = 10) -> dict:
    """List the most recent Stripe charges on the account."""
    try:
        s = _stripe()
        charges = s.Charge.list(limit=limit)
        items = [
            {
                "id": c.id,
                "amount": c.amount,
                "currency": c.currency,
                "status": c.status,
                "description": c.description,
                "created": c.created,
            }
            for c in charges.data
        ]
        return {"ok": True, "charges": items, "total": len(items)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_account_balance() -> dict:
    """Retrieve current Stripe account balance."""
    try:
        s = _stripe()
        balance = s.Balance.retrieve()
        available = [{"amount": b.amount, "currency": b.currency} for b in balance.available]
        pending = [{"amount": b.amount, "currency": b.currency} for b in balance.pending]
        return {"ok": True, "available": available, "pending": pending}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def record_bounty_payout(
    program: str,
    platform: str,
    severity: str,
    amount_usd: float,
    report_id: str,
) -> dict:
    """
    Record a confirmed bounty payout as a Stripe PaymentIntent for bookkeeping.
    Creates a memo-only intent (uncaptured) that serves as an audit trail.
    """
    amount_cents = int(amount_usd * 100)
    return create_payment_intent(
        amount_cents=amount_cents,
        currency="usd",
        description=f"Bounty: {program} ({severity}) via {platform}",
        metadata={
            "program": program,
            "platform": platform,
            "severity": severity,
            "report_id": report_id,
            "type": "bounty_payout",
        },
    )


def stripe_status() -> dict:
    """Health check — returns account balance if Stripe is configured."""
    if not STRIPE_SECRET_KEY:
        return {"configured": False, "publishable_key_set": bool(STRIPE_PUBLISHABLE_KEY)}
    balance = get_account_balance()
    return {
        "configured": True,
        "publishable_key_set": bool(STRIPE_PUBLISHABLE_KEY),
        "balance": balance,
    }
