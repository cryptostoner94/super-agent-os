from __future__ import annotations

from .models_upgrade import ExecutionDecision, Opportunity, OpportunityScore


def decide_execution(opportunity: Opportunity, score: OpportunityScore) -> ExecutionDecision:
    why = list(score.reasons)

    if not opportunity.eligibility_clear:
        return ExecutionDecision(
            opportunity_id=opportunity.id,
            action="gather_more_context",
            why=why + ["Eligibility is not clear enough for safe execution."],
            next_best_action="inspect_scope_and_rules",
        )

    if opportunity.risk_score >= 0.85:
        return ExecutionDecision(
            opportunity_id=opportunity.id,
            action="skip",
            why=why + ["Risk is too high relative to expected value."],
        )

    if opportunity.reward_amount is not None and opportunity.reward_amount < 25 and opportunity.execution_complexity > 0.5:
        return ExecutionDecision(
            opportunity_id=opportunity.id,
            action="skip",
            why=why + ["Low reward relative to effort."],
        )

    if score.recommendation == "execute_now":
        return ExecutionDecision(
            opportunity_id=opportunity.id,
            action="execute",
            why=why + ["Opportunity meets execution threshold."],
            requires_human_approval=opportunity.requires_manual_login,
            next_best_action="run_execution_workflow",
        )

    if score.recommendation == "gather_more_context":
        return ExecutionDecision(
            opportunity_id=opportunity.id,
            action="gather_more_context",
            why=why + ["Need more evidence before execution."],
            next_best_action="research_and_scope_validation",
        )

    if score.recommendation == "monitor":
        return ExecutionDecision(
            opportunity_id=opportunity.id,
            action="monitor",
            why=why + ["Opportunity is not strong enough yet."],
            next_best_action="recheck_later",
        )

    return ExecutionDecision(
        opportunity_id=opportunity.id,
        action="skip",
        why=why + ["Opportunity score too low."],
    )
