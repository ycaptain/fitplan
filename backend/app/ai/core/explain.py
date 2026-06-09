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
    trace = plan.strategy_trace
    algorithm = trace[-1].algorithm if trace else "planner"
    nodes = trace[-1].nodes if trace else 0

    return PlanExplanation(
        constraint_hits=[
            {
                "constraint_id": "fixed_event",
                "satisfied": plan.scores.conflicts == 0,
                "explanation": (
                    "No fixed-event or schedule overlap conflicts were detected."
                    if plan.scores.conflicts == 0
                    else f"{plan.scores.conflicts} conflict(s) remain in the plan."
                ),
            },
            {
                "constraint_id": "recovery_interval",
                "satisfied": plan.scores.recovery >= 0,
                "explanation": (
                    "Recovery spacing is acceptable for the scheduled muscle groups."
                    if plan.scores.recovery >= 0
                    else "Some sessions may be too close for ideal recovery."
                ),
            },
            {
                "constraint_id": "weekly_distribution",
                "satisfied": len({s.day for s in plan.sessions}) >= min(len(plan.sessions), 3),
                "explanation": (
                    f"Sessions are distributed across {len({s.day for s in plan.sessions})} day(s)."
                ),
            },
        ],
        score_breakdown=_breakdown(plan.scores),
        text_summary=(
            f"{algorithm} generated {len(plan.sessions)} session(s), "
            f"explored {nodes} candidate node(s), and produced a total score "
            f"of {plan.scores.total:.1f}."
        ),
    )


def explain_replan(
    result: ReplanResult, constraints: list[Constraint]
) -> PlanExplanation:
    trace = result.plan.strategy_trace
    trigger = trace[-1].algorithm if trace else "replan"

    return PlanExplanation(
        constraint_hits=[
            {
                "constraint_id": "replan_disturbance",
                "satisfied": result.metrics.disturbance >= 0,
                "explanation": (
                    f"{result.metrics.disturbance} session(s) changed during replanning."
                ),
            },
            {
                "constraint_id": "post_replan_conflicts",
                "satisfied": result.plan.scores.conflicts == 0,
                "explanation": (
                    "No hard conflicts remain after replanning."
                    if result.plan.scores.conflicts == 0
                    else f"{result.plan.scores.conflicts} conflict(s) remain after replanning."
                ),
            },
        ],
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
