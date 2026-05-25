from __future__ import annotations

from typing import Final, TypedDict

from app.ai.core.models import Constraint, Plan, ReplanResult, Scores

REPLAN_REASON_TEMPLATE: Final[str] = (
    "{trigger}: {disturbance} sessions changed, "
    "score delta {score_delta:+.1f}, conflicts {conflicts}"
)


class ConstraintHit(TypedDict):
    constraint_id: str
    satisfied: bool
    explanation: str


class PlanExplanation(TypedDict):
    constraint_hits: list[ConstraintHit]
    score_breakdown: dict[str, float]
    text_summary: str


def explain_plan(plan: Plan, constraints: list[Constraint]) -> PlanExplanation:
    return PlanExplanation(
        constraint_hits=[],
        score_breakdown=_breakdown(plan.scores),
        text_summary="",
    )


def explain_replan(
    result: ReplanResult, constraints: list[Constraint]
) -> PlanExplanation:
    trace = result.plan.strategy_trace
    trigger = trace[-1].algorithm if trace else "replan"
    return PlanExplanation(
        constraint_hits=[],
        score_breakdown=_breakdown(result.plan.scores),
        text_summary=REPLAN_REASON_TEMPLATE.format(
            trigger=trigger,
            disturbance=result.metrics.disturbance,
            score_delta=result.metrics.score_delta,
            conflicts=result.plan.scores.conflicts,
        ),
    )


def _breakdown(scores: Scores) -> dict[str, float]:
    return {
        "recovery": scores.recovery,
        "consistency": scores.consistency,
        "conflicts": float(scores.conflicts),
        "balance": scores.balance,
        "total": scores.total,
    }
