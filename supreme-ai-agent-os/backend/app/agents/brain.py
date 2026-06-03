from __future__ import annotations
from backend.app.providers.router import complete

SYSTEM_FRAME = """You are Supreme AI Agent OS.

Operating principles:
1. Do not fake external execution.
2. For non-technical users, provide clear actions and explain what will happen.
3. If terminal execution is required, propose exact safe commands.
4. Always include validation steps.
5. Prefer practical, low-cost actions.
6. For money/business tasks, avoid guarantees and separate opportunity from risk.
7. Produce structured output with: Summary, Plan, Actions, Risks, Validation.
"""

def run_agent(prompt: str, raw_data: str = "", file_text: str = "", agent_id: str = "executive") -> dict:
    composed = f"""{SYSTEM_FRAME}

Selected agent: {agent_id}

User request:
{prompt}

Raw pasted data:
{raw_data[:10000]}

Uploaded file text:
{file_text[:10000]}
"""
    result = complete(composed)
    return {"status": "ok", "agent": agent_id, "provider": result["provider"], "answer": result["text"]}
