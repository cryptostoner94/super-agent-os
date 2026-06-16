"""Warden — final safety pass before result returns to user."""
from backend.app.safety import guardrails
from backend.app.metrics import AGENT_RUNS

async def warden_node(state):
    AGENT_RUNS.labels(agent="warden").inc()
    result = state.get("result") or {}
    # scrub PII from any string fields in results
    redacted = _redact(result)
    return {**state, "result": redacted}

def _redact(obj):
    import re
    if isinstance(obj, dict):  return {k: _redact(v) for k, v in obj.items()}
    if isinstance(obj, list):  return [_redact(v) for v in obj]
    if isinstance(obj, str):   return re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED-SSN]", obj)
    return obj