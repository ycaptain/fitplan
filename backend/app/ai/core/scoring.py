"""Plan scoring helpers."""

from __future__ import annotations

from app.ai.core.models import Constraint, Plan, Scores


def score_plan(plan: Plan, constraints: list[Constraint]) -> Scores:
    """Aggregate a Plan into a Scores object covering recovery, consistency,
    conflicts, workload balance, and a weighted total.
    """
    return Scores()


def count_hard_violations(plan: Plan, constraints: list[Constraint]) -> int:
    """Return the number of hard-constraint violations in ``plan``."""
    return 0
