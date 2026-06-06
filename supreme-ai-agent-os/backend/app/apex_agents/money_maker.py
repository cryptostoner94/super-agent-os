"""Money Maker — handles Stripe charges, invoices, and USDC payouts."""
from backend.app.cognitive import cognitive_step
from backend.app.apex_tools import stripe_tools as stripe_tools
from backend.app.apex_tools import usdc_tools as usdc_tools
from backend.app.apex_tools import email_tools as email_tools
from backend.app.metrics import AGENT_RUNS, REVENUE_USD

TOOLS = {
    "stripe.create_invoice":  stripe_tools.create_invoice,
    "stripe.list_payments":   stripe_tools.list_payments,
    "usdc.balance":           usdc_tools.balance,
    "usdc.transfer":          usdc_tools.transfer,
    "email.send_invoice":     email_tools.send_invoice,
}

async def money_maker_node(state):
    AGENT_RUNS.labels(agent="money_maker").inc()
    out = await cognitive_step("money_maker", state["prompt"], TOOLS)
    # tally any captured revenue
    for r in out["results"]:
        amt = (r.get("result") or {}).get("amount_usd")
        if amt:
            REVENUE_USD.labels(agent="money_maker", source="stripe").inc(amt)
    return {**state, "result": out}