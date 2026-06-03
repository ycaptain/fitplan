from __future__ import annotations

import json
from pathlib import Path

from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, Plan
from app.ai.core.scoring import count_hard_violations
from app.ai.local.hill_climbing import hill_climbing
from app.ai.local.simulated_annealing import simulated_annealing

FIXTURES = Path(__file__).parent / "fixtures" / "sample_plans.json"

SEED = 42


def _load_plan(plan_id: str) -> Plan:
    data = json.loads(FIXTURES.read_text())
    raw = next(p for p in data["plans"] if p["id"] == plan_id)
    return Plan.model_validate(raw)


def _meeting(day: int, start: str, end: str) -> Constraint:
    return Constraint(
        id=f"evt-d{day}-{start}",
        kind="hard",
        type=ConstraintType.FIXED_EVENT,
        params={"day_of_week": day, "start": start, "end": end},
    )


def _heavy_disturbance(plan: Plan) -> list[Constraint]:
    """Block the prime evening window on every day that currently has a session."""
    return [_meeting(day, "16:00", "21:00") for day in sorted({s.day for s in plan.sessions})]


def test_both_clear_hard_violations_under_heavy_disturbance() -> None:
    plan = _load_plan("ppl-base-001")
    constraints = _heavy_disturbance(plan)
    assert count_hard_violations(plan, constraints) > 0

    hc_out = hill_climbing(plan, constraints, random_seed=SEED)
    sa_out = simulated_annealing(plan, constraints, random_seed=SEED)

    assert count_hard_violations(hc_out, constraints) == 0
    assert count_hard_violations(sa_out, constraints) == 0


def test_sa_matches_or_beats_hc_on_heavy_disturbance() -> None:
    """With a large affected ratio SA must not lose to HC on the soft score.

    This pins the behaviour that justifies routing re_optimize replans with a
    high affected ratio to simulated annealing.
    """
    plan = _load_plan("ppl-base-001")
    constraints = _heavy_disturbance(plan)

    hc_out = hill_climbing(plan, constraints, random_seed=SEED)
    sa_out = simulated_annealing(plan, constraints, random_seed=SEED)

    assert sa_out.scores.total >= hc_out.scores.total


def test_sa_stays_close_to_hc_on_light_disturbance() -> None:
    plan = _load_plan("ul-base-001")
    constraints = [_meeting(plan.sessions[0].day, plan.sessions[0].start, "21:00")]

    hc_out = hill_climbing(plan, constraints, random_seed=SEED)
    sa_out = simulated_annealing(plan, constraints, random_seed=SEED)

    assert count_hard_violations(sa_out, constraints) == 0
    assert sa_out.scores.total >= hc_out.scores.total - 2.0
