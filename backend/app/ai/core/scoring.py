from __future__ import annotations

from app.ai.core.models import Constraint, Plan, Scores


def score_plan(plan: Plan, constraints: list[Constraint]) -> Scores:
    return Scores()


def count_hard_violations(plan: Plan, constraints: list[Constraint]) -> int:
    return 0
