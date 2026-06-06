"""Commander — orchestrator that routes goals to the right specialist."""
from __future__ import annotations
import json
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.cognitive import _llm
from backend.app.metrics import AGENT_RUNS

ROUTING_SYS = """You are Commander, the orchestrator of 4 specialists:
- money_maker: payments, invoices, USDC transfers, marketplace earnings
- bounty_hunter: vulnerability research, HackerOne submissions
- negotiator: B2B lead-gen, outreach emails, CRM
- warden: safety checks (auto-invoked on every result)

Given a user goal, choose exactly ONE specialist to handle it.
Return JSON: {"next":"money_maker|bounty_hunter|negotiator","reason":"…"}"""

async def commander_node(state):
    AGENT_RUNS.labels(agent="commander").inc()
    llm = _llm("reason")
    msg = await llm.ainvoke([
        SystemMessage(content=ROUTING_SYS),
        HumanMessage(content=state["prompt"]),
    ])
    try:
        decision = json.loads(msg.content)
    except Exception:
        decision = {"next": "negotiator", "reason": "default"}
    return {**state, "next": decision["next"], "scratchpad": {"routing": decision}}