"""Negotiator — opt-in B2B lead-gen via Apollo + Hunter + SendGrid."""
from backend.app.cognitive import cognitive_step
from backend.app.apex_tools import apollo_tools as apollo_tools
from backend.app.apex_tools import hunter_tools as hunter_tools
from backend.app.apex_tools import email_tools as email_tools
from backend.app.apex_tools import buffer_tools as buffer_tools
from backend.app.apex_tools import mastodon_tools as mastodon_tools
from backend.app.metrics import AGENT_RUNS

TOOLS = {
    "apollo.search_people":     apollo_tools.search_people,
    "apollo.enrich":            apollo_tools.enrich,
    "hunter.find_email":        hunter_tools.find_email,
    "hunter.verify":            hunter_tools.verify,
    "email.send":               email_tools.send,
    "buffer.schedule":          buffer_tools.schedule,
    "mastodon.post":            mastodon_tools.post,
}

async def negotiator_node(state):
    AGENT_RUNS.labels(agent="negotiator").inc()
    out = await cognitive_step("negotiator", state["prompt"], TOOLS)
    return {**state, "result": out}