from __future__ import annotations

from typing import Final

from app.ai.core.models import (
    Constraint,
    ConstraintHit,
    Plan,
    PlanExplanation,
    ReplanResult,
    Scores,
)

REPLAN_REASON_TEMPLATE: Final[str] = (
    "{trigger}: {disturbance} sessions changed, "
    "score delta {score_delta:+.1f}, conflicts {conflicts}"
)


def explain_plan(plan: Plan, constraints: list[Constraint]) -> PlanExplanation:
    trace = plan.strategy_trace
    algorithm = trace[-1].algorithm if trace else "planner"
    nodes = trace[-1].nodes if trace else 0
    training_days = len({s.day for s in plan.sessions})

    return PlanExplanation(
        constraint_hits=[
            ConstraintHit(
                constraint_id="fixed_event",
                satisfied=plan.scores.conflicts == 0,
                explanation=(
                    "No fixed-event or schedule overlap conflicts were detected."
                    if plan.scores.conflicts == 0
                    else f"{plan.scores.conflicts} conflict(s) remain in the plan."
                ),
            ),
            ConstraintHit(
                constraint_id="recovery_interval",
                satisfied=plan.scores.recovery >= 0,
                explanation=(
                    "Recovery spacing is acceptable for the scheduled muscle groups."
                    if plan.scores.recovery >= 0
                    else "Some sessions may be too close for ideal recovery."
                ),
            ),
            ConstraintHit(
                constraint_id="weekly_distribution",
                satisfied=training_days >= min(len(plan.sessions), 3),
                explanation=f"Sessions are distributed across {training_days} day(s).",
            ),
        ],
        score_breakdown=_breakdown(plan.scores),
        text_summary=(
            f"{algorithm} generated {len(plan.sessions)} session(s), "
            f"explored {nodes} candidate node(s), and produced a total score "
            f"of {plan.scores.total:.1f}."
        ),
    )


def explain_replan(
    result: ReplanResult,
    constraints: list[Constraint],
    affected_count: int | None = None,
) -> PlanExplanation:
    trace = result.plan.strategy_trace
    trigger = trace[-1].algorithm if trace else "replan"
    disturbance_bound = (
        affected_count if affected_count is not None else len(result.plan.sessions)
    )
    contained = result.metrics.disturbance <= disturbance_bound

    return PlanExplanation(
        constraint_hits=[
            ConstraintHit(
                constraint_id="replan_disturbance",
                satisfied=contained,
                explanation=(
                    f"{result.metrics.disturbance} session(s) changed during replanning"
                    f" (affected set: {disturbance_bound})."
                    if contained
                    else (
                        f"{result.metrics.disturbance} session(s) changed, exceeding the"
                        f" {disturbance_bound} directly affected — wider reshuffle."
                    )
                ),
            ),
            ConstraintHit(
                constraint_id="post_replan_conflicts",
                satisfied=result.plan.scores.conflicts == 0,
                explanation=(
                    "No hard conflicts remain after replanning."
                    if result.plan.scores.conflicts == 0
                    else f"{result.plan.scores.conflicts} conflict(s) remain after replanning."
                ),
            ),
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
