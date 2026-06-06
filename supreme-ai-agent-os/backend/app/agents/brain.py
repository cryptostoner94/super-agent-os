"""
Agent brain — routes execution through the Inception layer.
All agent runs go through Inception for intent classification,
task decomposition, soul scoring, and structured reporting.
"""
from __future__ import annotations

from backend.app.inception import run_inception, AGENT_PROMPTS
from backend.app.providers.router import complete

SYSTEM_FRAME = """You are Supreme AI Agent OS — SMARTY AI Inception Runtime.

Operating principles:
1. Do not fake external execution — only describe what will actually happen.
2. For non-technical users, provide clear actions and explain consequences.
3. If terminal execution is required, propose exact safe commands.
4. Always include validation steps.
5. Prefer practical, zero-cost actions.
6. For money/business tasks, separate opportunity from risk.
7. Produce structured output: Summary, Plan, Actions, Risks, Validation.
"""


def run_agent(
    prompt: str,
    raw_data: str = "",
    file_text: str = "",
    agent_id: str = "executive",
) -> dict:
    """
    Route the request through the Inception coordination layer.
    Falls back to direct LLM call if inception fails.
    """
    # Append raw_data/file_text context to prompt when present
    augmented = prompt
    if raw_data and raw_data.strip():
        augmented += f"\n\n--- Pasted Data ---\n{raw_data[:8000]}"
    if file_text and file_text.strip():
        augmented += f"\n\n--- Uploaded File ---\n{file_text[:8000]}"

    try:
        result = run_inception(augmented, agent_id=agent_id)
        return {
            "status": result.get("status", "ok"),
            "agent": agent_id,
            "provider": result.get("provider", ""),
            "answer": result.get("answer", ""),
            "intent": result.get("intent", ""),
            "soul_score": result.get("soul_score", 1.0),
            "soul_passed": result.get("soul_passed", True),
            "elapsed_ms": result.get("elapsed_ms", 0),
            "subtasks": result.get("subtasks", 1),
        }
    except Exception as e:
        # Fallback: direct LLM call with agent-specific system prompt
        system = AGENT_PROMPTS.get(agent_id, SYSTEM_FRAME)
        full_prompt = f"{system}\n\nRequest: {augmented}"
        r = complete(full_prompt)
        return {
            "status": "ok",
            "agent": agent_id,
            "provider": r.get("provider", ""),
            "answer": r.get("text", ""),
            "intent": "general",
            "soul_score": 0.8,
            "soul_passed": True,
            "elapsed_ms": 0,
            "subtasks": 1,
        }
