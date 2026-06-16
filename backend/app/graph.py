"""
LangGraph multi-agent state machine.
Agents: commander → money_maker | bounty_hunter | negotiator | warden
"""
from __future__ import annotations
from typing import TypedDict, Annotated, Literal
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    prompt: str
    history: Annotated[list[BaseMessage], operator.add]
    scratchpad: dict
    agent: str
    next: str
    result: str
    needs_approval: bool


def router(state: AgentState) -> Literal["money_maker", "bounty_hunter", "negotiator", "warden", "__end__"]:
    nxt = state.get("next", "end")
    if nxt == "end" or state.get("result"):
        return END
    if nxt in ("money_maker", "bounty_hunter", "negotiator", "warden"):
        return nxt
    return END


def build_graph():
    from backend.app.apex_agents.commander import commander_node
    from backend.app.apex_agents.money_maker import money_maker_node
    from backend.app.apex_agents.bounty_hunter import bounty_hunter_node
    from backend.app.apex_agents.negotiator import negotiator_node
    from backend.app.apex_agents.warden import warden_node

    g = StateGraph(AgentState)
    g.add_node("commander",     commander_node)
    g.add_node("money_maker",   money_maker_node)
    g.add_node("bounty_hunter", bounty_hunter_node)
    g.add_node("negotiator",    negotiator_node)
    g.add_node("warden",        warden_node)

    g.set_entry_point("commander")
    g.add_conditional_edges("commander", router)
    for node in ("money_maker", "bounty_hunter", "negotiator"):
        g.add_edge(node, "warden")
    g.add_edge("warden", END)
    return g.compile()
