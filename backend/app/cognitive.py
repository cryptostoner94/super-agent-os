"""
Cognitive loop: Planner → Executor → Critic → Memory.
LLM backend priority: Ollama (local) → cloud providers.
"""
from __future__ import annotations
import json, os, structlog
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage

log = structlog.get_logger()


def _llm(role: str = "reason"):
    """Return best available LLM. Always tries Ollama first (free)."""
    # 1. Ollama local
    from backend.app.providers.ollama import get_llm, best_model
    prefer_code = role == "code"
    m = best_model(prefer_code=prefer_code)
    if m:
        return get_llm(m)

    # 2. Cloud fallback
    mode = os.getenv("LLM_MODE", "auto")
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        _oai_kwargs: dict = {"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "temperature": 0.2}
        _base = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
        if _base:
            _oai_kwargs["base_url"] = _base
        return ChatOpenAI(**_oai_kwargs)
    if os.getenv("GEMINI_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
    if os.getenv("GROQ_API_KEY"):
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    if os.getenv("XAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("XAI_MODEL", "grok-2-latest"),
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1",
            temperature=0.2
        )
    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0.2)
    raise RuntimeError("No LLM available. Install Ollama or set a cloud API key.")


PLANNER_SYS = """You are the Planner. Decompose the goal into 3-5 concrete steps.
Return ONLY valid JSON: {"steps":[{"id":1,"action":"…","tool":"…","why":"…"}]}
Past successful patterns: {memory}"""

CRITIC_SYS = """You are the Critic. Score the step result 0.0-1.0 and propose one improvement.
Return ONLY valid JSON: {"score":0.0,"counterfactual":"…","keep":true}"""


async def cognitive_step(agent_name: str, goal: str, tools: dict[str, Any]) -> dict:
    from backend.app.memory import recall_similar, log_outcome
    from backend.app.safety import guardrails

    memory = await recall_similar(agent_name, goal, k=5)

    # Planner
    planner = _llm("reason")
    try:
        plan_msg = await planner.ainvoke([
            SystemMessage(content=PLANNER_SYS.format(memory=json.dumps(memory)[:1500])),
            HumanMessage(content=goal),
        ])
        plan = json.loads(plan_msg.content)
    except Exception as e:
        log.warning("planner.failed", err=str(e))
        plan = {"steps": [{"id": 1, "action": goal, "tool": list(tools.keys())[0] if tools else "noop", "why": "fallback"}]}

    results = []
    for step in plan.get("steps", []):
        # Safety check
        check = await guardrails.check_action(step)
        if not check.allowed:
            results.append({"step": step, "blocked": True, "reason": check.reason})
            continue

        # Execute
        tool_fn = tools.get(step.get("tool", ""))
        if tool_fn is None:
            results.append({"step": step, "error": f"unknown tool: {step.get('tool')}"})
            continue
        try:
            out = await tool_fn(step.get("action", ""))
        except Exception as e:
            out = {"error": str(e)}

        # Critic
        try:
            critic = _llm("tool")
            crit_msg = await critic.ainvoke([
                SystemMessage(content=CRITIC_SYS),
                HumanMessage(content=json.dumps({"step": step, "result": out})[:3000]),
            ])
            crit = json.loads(crit_msg.content)
        except Exception:
            crit = {"score": 0.5, "counterfactual": "", "keep": True}

        results.append({"step": step, "result": out, "critic": crit})
        await log_outcome(agent_name, goal, step, out, crit.get("score", 0.5))

    return {"plan": plan, "results": results}
