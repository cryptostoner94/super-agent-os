"""Bounty Hunter — HackerOne program discovery + report drafting."""
from backend.app.cognitive import cognitive_step
from backend.app.apex_tools import hackerone_tools as hackerone_tools
from backend.app.apex_tools import web as web
from backend.app.apex_tools import files as files
from backend.app.apex_tools import code as code
from backend.app.metrics import AGENT_RUNS, REVENUE_USD

TOOLS = {
    "h1.list_programs":     hackerone_tools.list_programs,
    "h1.get_program":       hackerone_tools.get_program,
    "h1.submit_report":     hackerone_tools.submit_report,
    "h1.list_my_reports":   hackerone_tools.list_my_reports,
    "web.search":           web.search,
    "web.fetch":            web.fetch,
    "code.run":             code.run_sandboxed,
}

async def bounty_hunter_node(state):
    AGENT_RUNS.labels(agent="bounty_hunter").inc()
    out = await cognitive_step("bounty_hunter", state["prompt"], TOOLS)
    for r in out["results"]:
        bounty = (r.get("result") or {}).get("bounty_usd")
        if bounty:
            REVENUE_USD.labels(agent="bounty_hunter", source="hackerone").inc(bounty)
    return {**state, "result": out}