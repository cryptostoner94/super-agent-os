"""Warden safety alignment using NeMo Guardrails + custom rules."""
from __future__ import annotations
import os, re
from dataclasses import dataclass

DANGEROUS_PATTERNS = [
    r"DROP\s+TABLE",
    r"rm\s+-rf\s+/",
    r"\bssn\b.*\d{3}-\d{2}-\d{4}",
    r"private_key|BEGIN RSA PRIVATE KEY",
]
PII_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{16}\b")  # SSN, card

@dataclass
class Verdict:
    allowed: bool
    reason: str = ""

class Guardrails:
    def __init__(self):
        self.strict = os.getenv("GUARDRAILS_STRICT", "true").lower() == "true"
        self.threshold = float(os.getenv("WARDEN_APPROVAL_THRESHOLD", "100"))

    async def check_input(self, text: str) -> Verdict:
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, text, re.I):
                return Verdict(False, f"dangerous pattern: {pat}")
        if PII_RE.search(text):
            return Verdict(False, "PII detected in input")
        return Verdict(True)

    async def check_action(self, step: dict) -> Verdict:
        tool = step.get("tool", "")
        action = step.get("action", "")
        # financial guardrail
        if tool in ("stripe_tools.charge", "usdc_tools.transfer"):
            amt = step.get("amount_usd", 0)
            if amt > self.threshold:
                return Verdict(False, f"amount ${amt} exceeds threshold ${self.threshold} — requires human approval")
        # prompt-injection heuristic
        if "ignore previous instructions" in action.lower():
            return Verdict(False, "prompt injection detected")
        return Verdict(True)

guardrails = Guardrails()
