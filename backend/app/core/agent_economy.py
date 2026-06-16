"""
Agent-to-agent economy — parallel task market for the bounty pipeline.

Agents hire each other for specialised subtasks:
  Executive → decomposes goal → assigns to specialist agents in parallel
  Results flow back, get synthesised, then actioned.

All coordination is async and non-linear (true parallel fan-out).
"""
from __future__ import annotations
import asyncio
import os
import time
from typing import Any

# ── Platform policy compliance ────────────────────────────────────────────────

PLATFORM_RULES = {
    "hackerone": {
        "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        "forbidden": ["sqli", "rce", "dos", "ddos", "brute_force", "social_engineering"],
        "rate_limit_per_host": 10,   # max requests per minute
        "require_in_scope": True,
        "auto_submit": True,          # H1 has a report submission API
        "policy_url": "https://www.hackerone.com/policies",
    },
    "intigriti": {
        "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        "forbidden": ["dos", "ddos", "brute_force", "physical"],
        "rate_limit_per_host": 10,
        "require_in_scope": True,
        "auto_submit": False,         # Intigriti API is read-only for researchers
        "policy_url": "https://www.intigriti.com/researchers",
    },
    "yeswehack": {
        "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        "forbidden": ["dos", "ddos", "social_engineering"],
        "rate_limit_per_host": 10,
        "require_in_scope": True,
        "auto_submit": False,
        "policy_url": "https://yeswehack.com/researchers",
    },
    "bugcrowd": {
        "allowed_methods": ["GET", "HEAD", "OPTIONS"],
        "forbidden": ["dos", "ddos", "brute_force"],
        "rate_limit_per_host": 10,
        "require_in_scope": True,
        "auto_submit": False,
        "policy_url": "https://www.bugcrowd.com/resources/essentials/",
    },
}


def is_action_allowed(platform: str, action: str, target: str = "") -> dict:
    """Check if an action is allowed by platform policy before execution."""
    rules = PLATFORM_RULES.get(platform, {})
    forbidden = rules.get("forbidden", [])
    for f in forbidden:
        if f in action.lower():
            return {"allowed": False, "reason": f"Action '{action}' is forbidden on {platform}: {f}"}
    return {"allowed": True, "reason": "OK"}


# ── Scoring matrix ────────────────────────────────────────────────────────────

def score_opportunity(program: dict, platform: str) -> float:
    """
    Multi-dimensional score for a bounty program.
    Higher = more worth pursuing.

    Factors:
    - Max bounty value (primary driver)
    - Response efficiency (how fast they pay)
    - Resolved report count (active, paying program)
    - Offers bounties flag
    - Auto-submit available (faster path to payout)
    - Scope breadth (estimated from name/type)
    """
    score = 0.0

    # Bounty value (0–50 pts)
    max_b = program.get("max_bounty") or program.get("max_bounty_table_value") or 0
    try:
        max_b = float(str(max_b).replace(",", "").replace("$", "")) if max_b else 0
    except Exception:
        max_b = 0
    score += min(max_b / 200, 50)   # $10k max bounty → 50 pts

    # Response efficiency (0–20 pts)
    resp = program.get("response_efficiency") or program.get("response_efficiency_percentage") or 0
    try:
        resp = float(resp)
    except Exception:
        resp = 0
    score += (resp / 100) * 20

    # Resolved reports — proven payer (0–15 pts)
    resolved = program.get("resolved_reports") or program.get("resolved_report_count") or 0
    try:
        resolved = int(resolved)
    except Exception:
        resolved = 0
    score += min(resolved / 100, 15)

    # Offers bounties (0 or 10 pts)
    if program.get("offers_bounties") or program.get("bounty"):
        score += 10

    # Auto-submit available for platform (0 or 5 pts)
    if PLATFORM_RULES.get(platform, {}).get("auto_submit"):
        score += 5

    # Submission state open (0 or 5 pts)
    state = str(program.get("submission_state") or program.get("status") or "").lower()
    if state in ("open", "active", "public"):
        score += 5

    # Min bounty > 0 (sweet spot programs) (0 or 5 pts)
    min_b = program.get("min_bounty") or program.get("min_bounty_table_value") or 0
    try:
        min_b = float(str(min_b).replace(",", "").replace("$", "")) if min_b else 0
    except Exception:
        min_b = 0
    if min_b > 0:
        score += 5

    return round(score, 2)


# ── Agent task dispatcher ─────────────────────────────────────────────────────

class AgentTask:
    """A unit of work dispatched in the agent economy."""
    def __init__(self, task_id: str, agent_type: str, payload: dict):
        self.task_id = task_id
        self.agent_type = agent_type
        self.payload = payload
        self.result: Any = None
        self.error: str | None = None
        self.started_at = time.time()
        self.finished_at: float | None = None

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type,
            "status": "error" if self.error else ("done" if self.finished_at else "running"),
            "elapsed_ms": int((self.finished_at or time.time() - self.started_at) * 1000),
            "error": self.error,
        }


async def _dispatch_recon_agent(program: dict, platform: str) -> dict:
    """Recon agent: checks headers, common paths, CORS on program targets."""
    from backend.app.core.bounty_pipeline import execute_recon
    policy_check = is_action_allowed(platform, "recon_get")
    if not policy_check["allowed"]:
        return {"skipped": True, "reason": policy_check["reason"]}
    return await execute_recon(program)


async def _dispatch_researcher_agent(program: dict) -> dict:
    """Researcher agent: uses LLM to analyse program scope and suggest attack vectors."""
    try:
        from backend.app.providers.router import complete
        prompt = (
            f"You are an elite bug bounty researcher. Analyse this program and suggest "
            f"the top 3 most likely vulnerability types to find, ordered by probability and impact.\n\n"
            f"Program: {program.get('name', 'Unknown')}\n"
            f"Platform: {program.get('_platform', 'unknown')}\n"
            f"Max bounty: {program.get('max_bounty') or program.get('max_bounty_table_value', 'N/A')}\n"
            f"Scope: web application\n\n"
            f"Respond in JSON: {{\"vectors\": [{{\"type\": \"...\", \"probability\": 0.0-1.0, \"severity\": \"critical/high/medium/low\"}}]}}"
        )
        result = complete(prompt)
        import json
        try:
            return json.loads(result.get("text", "{}"))
        except Exception:
            return {"vectors": [], "raw": result.get("text", "")}
    except Exception as e:
        return {"vectors": [], "error": str(e)}


async def _dispatch_score_agent(programs: list[dict], platform: str) -> list[dict]:
    """Score agent: ranks programs by multi-dimensional score."""
    scored = []
    for p in programs:
        p["_score"] = score_opportunity(p, platform)
        p["_platform"] = platform
        scored.append(p)
    return sorted(scored, key=lambda x: x["_score"], reverse=True)


async def run_parallel_economy(platforms_data: dict[str, list]) -> list[dict]:
    """
    Full agent-to-agent parallel economy:
    1. Score agent ranks all programs simultaneously across platforms
    2. Top N programs get researcher + recon agents fired in parallel
    3. Results merged and returned ranked by actionability

    Non-linear: all agents run concurrently, not sequentially.
    """
    import uuid

    # Phase 1: Score all platforms in parallel
    score_tasks = [
        _dispatch_score_agent(programs, platform)
        for platform, programs in platforms_data.items()
        if programs
    ]
    scored_lists = await asyncio.gather(*score_tasks, return_exceptions=True)

    # Merge and take top 10 across all platforms
    all_scored = []
    for scored in scored_lists:
        if not isinstance(scored, Exception):
            all_scored.extend(scored)
    all_scored.sort(key=lambda x: x.get("_score", 0), reverse=True)
    top_targets = all_scored[:10]

    if not top_targets:
        return []

    # Phase 2: Researcher + Recon in parallel for each target
    async def full_agent_sweep(program: dict) -> dict:
        platform = program.get("_platform", "hackerone")
        recon_task = _dispatch_recon_agent(program, platform)
        research_task = _dispatch_researcher_agent(program)
        recon_result, research_result = await asyncio.gather(
            recon_task, research_task, return_exceptions=True
        )
        return {
            **program,
            "recon": recon_result if not isinstance(recon_result, Exception) else {"error": str(recon_result)},
            "research": research_result if not isinstance(research_result, Exception) else {"error": str(research_result)},
            "economy_task_id": str(uuid.uuid4())[:8],
        }

    results = await asyncio.gather(*[full_agent_sweep(p) for p in top_targets], return_exceptions=True)
    final = [r for r in results if not isinstance(r, Exception)]

    # Sort by recon findings count + score
    def actionability(r):
        findings = r.get("recon", {}).get("findings", [])
        return (len(findings) * 20) + r.get("_score", 0)

    final.sort(key=actionability, reverse=True)
    return final
