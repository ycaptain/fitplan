"""Plan and replan explanation helpers."""

from __future__ import annotations

from typing import TypedDict

from app.ai.core.models import Constraint, Plan, ReplanResult


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
        score_breakdown={},
        text_summary="",
    )


def explain_replan(result: ReplanResult, constraints: list[Constraint]) -> PlanExplanation:
    return PlanExplanation(
        constraint_hits=[],
        score_breakdown={},
        text_summary="",
    )
