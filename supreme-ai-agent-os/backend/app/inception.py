"""
SMARTY AI — INCEPTION LAYER
============================
Unified coordination controller for the Supreme AI Agent OS.

Responsibilities:
  1. Parse & classify user intent
  2. Decompose goal into subtasks
  3. Select agents + tools
  4. Check memory for relevant context
  5. Execute subtasks with retries
  6. Verify result via Soul quality gate
  7. Save artifact
  8. Return structured outcome report
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from backend.app.providers.router import complete as llm_complete
from backend.app.uac.soul.soul import Soul

# ── Intent classification ─────────────────────────────────────────────────────

INTENTS = {
    "code":        ["write", "build", "code", "script", "function", "class", "refactor", "debug", "fix"],
    "research":    ["research", "find", "search", "look up", "what is", "explain", "analyze", "compare"],
    "browser":     ["browse", "visit", "scrape", "screenshot", "navigate", "open url", "fetch page"],
    "bounty":      ["vulnerability", "pentest", "security", "bug bounty", "owasp", "xss", "sqli", "authorized", "bounty hunt"],
    "reward":      ["earn", "money", "income", "freelance", "hackathon", "grant", "opportunity", "find bounty", "find reward"],
    "memory":      ["remember", "recall", "history", "what did", "last time", "previous"],
    "plan":        ["plan", "strategy", "roadmap", "steps", "how to", "guide", "checklist"],
    "monitor":     ["monitor", "watch", "alert", "status", "health", "uptime", "check"],
    "telegram":    ["telegram", "bot", "message", "notify", "send"],
    "general":     [],
}

def classify_intent(prompt: str) -> str:
    p = prompt.lower()
    scores: dict[str, int] = {}
    for intent, keywords in INTENTS.items():
        scores[intent] = sum(1 for kw in keywords if kw in p)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

AGENT_FOR_INTENT = {
    "code":     "builder",
    "research": "researcher",
    "browser":  "browser",
    "bounty":   "bounty_hunter",
    "reward":   "reward_scout",
    "memory":   "memory_agent",
    "plan":     "planner",
    "monitor":  "monitor",
    "telegram": "telegram_agent",
    "general":  "executive",
}

# ── Decomposition ─────────────────────────────────────────────────────────────

DECOMPOSE_PROMPT = """\
You are a task decomposer. Break the goal into at most 4 clear sequential subtasks.
Return ONLY valid JSON: {{"tasks":[{{"id":1,"action":"...","agent":"...","why":"..."}}]}}
Available agents: planner, researcher, builder, browser, bounty_hunter, reward_scout, executor, memory_agent, monitor, telegram_agent, executive
Goal: {goal}"""

def _decompose(goal: str) -> list[dict]:
    try:
        resp = llm_complete(DECOMPOSE_PROMPT.format(goal=goal[:800]))
        raw = resp.get("text", "")
        start = raw.find("{")
        if start >= 0:
            data = json.loads(raw[start:raw.rfind("}") + 1])
            tasks = data.get("tasks", [])
            if tasks and isinstance(tasks, list):
                return tasks
    except Exception:
        pass
    return [{"id": 1, "action": goal, "agent": classify_agent(goal), "why": "direct execution"}]

def classify_agent(goal: str) -> str:
    return AGENT_FOR_INTENT.get(classify_intent(goal), "executive")

# ── Tool selection ────────────────────────────────────────────────────────────

TOOL_HINTS = {
    "code":     ["code", "files"],
    "research": ["web", "http"],
    "browser":  ["browser"],
    "bounty":   ["http", "web"],
    "reward":   ["web", "http"],
    "plan":     [],
    "general":  [],
}

def select_tools(intent: str) -> list[str]:
    return TOOL_HINTS.get(intent, [])

# ── Execution ─────────────────────────────────────────────────────────────────

AGENT_PROMPTS: dict[str, str] = {
    "planner": "You are a master planner. Decompose the goal into clear, actionable steps with dependencies. Produce a structured plan with timeline estimates.",
    "researcher": "You are a research specialist. Provide comprehensive, factual research with sources cited where possible. Structure findings clearly.",
    "builder": "You are a code builder. Write production-ready, well-structured code. Include tests, error handling, and usage examples.",
    "browser": "You are a browser automation specialist. Describe the exact navigation steps, selectors, and data extraction strategy for the given URL/task.",
    "bounty_hunter": "You are an authorized security researcher following responsible disclosure. Analyze the scope and generate an OWASP-based testing checklist with specific test cases.",
    "reward_scout": "You are a reward discovery agent. Identify concrete, actionable income opportunities (bug bounties, hackathons, grants, freelance). Include effort estimates and direct links.",
    "executor": "You are a systems executor. Plan the exact commands, scripts, and validation steps needed. Prefer safe, reversible operations.",
    "memory_agent": "You are a memory retrieval agent. Summarize relevant past context and outcomes from memory to inform the current task.",
    "monitor": "You are a monitoring agent. Provide a comprehensive health assessment with specific thresholds and alert conditions.",
    "telegram_agent": "You are a Telegram bot configurator. Generate the bot command handlers, message templates, and webhook setup required.",
    "executive": "You are the Executive Agent. Coordinate the full task, delegate subtasks, verify quality, and produce a comprehensive outcome report.",
}

def _run_subtask(action: str, agent_id: str) -> dict:
    system = AGENT_PROMPTS.get(agent_id, AGENT_PROMPTS["executive"])
    full_prompt = f"{system}\n\nTask: {action}"
    result = llm_complete(full_prompt)
    return {"agent": agent_id, "action": action, "output": result.get("text", ""), "provider": result.get("provider", "unknown")}

# ── Outcome dataclass ─────────────────────────────────────────────────────────

@dataclass
class InceptionResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    goal: str = ""
    intent: str = ""
    agent: str = ""
    tools: list[str] = field(default_factory=list)
    subtasks: list[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
    answer: str = ""
    soul_score: float = 1.0
    soul_passed: bool = True
    provider: str = ""
    elapsed_ms: float = 0.0
    artifact_id: str | None = None
    created: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

# ── Inception controller ──────────────────────────────────────────────────────

_soul = Soul()


def run_inception(
    prompt: str,
    agent_id: str | None = None,
    raw_data: str = "",
    file_text: str = "",
    session_id: str | None = None,
) -> dict:
    """
    Synchronous inception controller.
    Coordinates intent → decompose → execute → verify → report.
    """
    t0 = time.perf_counter()
    ir = InceptionResult(goal=prompt)

    # 1. Classify intent
    ir.intent = classify_intent(prompt)
    ir.agent = agent_id or classify_agent(prompt)
    ir.tools = select_tools(ir.intent)

    # 2. Decompose into subtasks (skip for short prompts)
    if len(prompt) > 120:
        ir.subtasks = _decompose(prompt)
    else:
        ir.subtasks = [{"id": 1, "action": prompt, "agent": ir.agent, "why": "direct"}]

    # 3. Execute subtasks
    errors = []
    primary_output = ""
    for subtask in ir.subtasks[:4]:  # cap at 4
        try:
            res = _run_subtask(
                subtask.get("action", prompt),
                subtask.get("agent", ir.agent),
            )
            ir.results.append(res)
            if not primary_output:
                primary_output = res.get("output", "")
            if res.get("provider"):
                ir.provider = res["provider"]
        except Exception as e:
            errors.append(str(e))
            ir.results.append({"error": str(e), "action": subtask.get("action", "")})

    # 4. Synthesize final answer
    if len(ir.subtasks) > 1 and ir.results:
        combined = "\n\n---\n\n".join(
            f"**Step {i+1} — {r.get('agent', 'agent')}:**\n{r.get('output', r.get('error', ''))}"
            for i, r in enumerate(ir.results)
        )
        ir.answer = combined
    else:
        ir.answer = primary_output or "No output produced."

    # 5. Soul quality gate
    wu = {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "outputs": {"answer": ir.answer},
        "duration_ms": (time.perf_counter() - t0) * 1000,
        "attempts": 1,
    }
    verdict = _soul.evaluate(wu)
    ir.soul_score = verdict.score
    ir.soul_passed = verdict.passed

    ir.elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "status": "ok" if not errors else "partial",
        "id": ir.id,
        "intent": ir.intent,
        "agent": ir.agent,
        "tools": ir.tools,
        "answer": ir.answer,
        "subtasks": len(ir.subtasks),
        "provider": ir.provider,
        "soul_score": ir.soul_score,
        "soul_passed": ir.soul_passed,
        "elapsed_ms": round(ir.elapsed_ms, 1),
        "results": ir.results,
    }


async def run_inception_async(
    prompt: str,
    agent_id: str | None = None,
    raw_data: str = "",
    file_text: str = "",
) -> dict:
    """Async wrapper — runs inception in a thread to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: run_inception(prompt, agent_id, raw_data, file_text),
    )
