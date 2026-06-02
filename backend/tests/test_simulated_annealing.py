from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.core import registry
from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, Plan
from app.ai.core.scoring import count_hard_violations
from app.ai.local.simulated_annealing import simulated_annealing

FIXTURES = Path(__file__).parent / "fixtures" / "sample_plans.json"


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


def test_simulated_annealing_registered() -> None:
    import app.ai.local  # noqa: F401

    fn = registry.get(registry.AlgorithmKey.SIMULATED_ANNEALING)
    assert callable(fn)


@pytest.mark.parametrize("seed", [0, 7, 42])
def test_same_seed_yields_identical_plan(seed: int) -> None:
    plan = _load_plan("ppl-base-001")
    constraints = [_meeting(3, "18:30", "20:00")]

    a = simulated_annealing(plan, constraints, random_seed=seed)
    b = simulated_annealing(plan, constraints, random_seed=seed)

    assert a.model_dump() == b.model_dump()


def test_locked_sessions_stay_put() -> None:
    plan = _load_plan("ppl-base-001")
    plan.sessions[2] = plan.sessions[2].model_copy(update={"locked": True})
    plan.sessions[5] = plan.sessions[5].model_copy(update={"locked": True})
    locked_before = {s.id: (s.day, s.start) for s in plan.sessions if s.locked}

    result = simulated_annealing(
        plan,
        [_meeting(3, "18:30", "20:00")],
        random_seed=7,
    )

    locked_after = {s.id: (s.day, s.start) for s in result.sessions if s.locked}
    assert locked_after == locked_before


@pytest.mark.parametrize("seed", [3, 11, 23])
def test_hard_violations_never_grow(seed: int) -> None:
    plan = _load_plan("ppl-base-001")
    constraints = [_meeting(3, "18:30", "20:00")]
    before = count_hard_violations(plan, constraints)

    result = simulated_annealing(plan, constraints, random_seed=seed)

    after = count_hard_violations(result, constraints)
    assert after <= before


def test_empty_plan_is_returned_unchanged() -> None:
    empty = Plan(id="empty", generated_at="1970-01-01T00:00:00Z", sessions=[])
    result = simulated_annealing(empty, [], random_seed=1)
    assert result.sessions == []


def test_all_locked_plan_is_returned_unchanged() -> None:
    plan = _load_plan("ul-base-001")
    plan.sessions = [s.model_copy(update={"locked": True}) for s in plan.sessions]
    snapshot = [(s.id, s.day, s.start) for s in plan.sessions]

    result = simulated_annealing(plan, [], random_seed=1)

    assert [(s.id, s.day, s.start) for s in result.sessions] == snapshot


def test_zero_iterations_returns_rescored_original() -> None:
    plan = _load_plan("fb-base-001")
    snapshot = [(s.id, s.day, s.start) for s in plan.sessions]

    result = simulated_annealing(plan, [], max_iter=0, random_seed=1)

    assert [(s.id, s.day, s.start) for s in result.sessions] == snapshot
    assert result.scores.total == pytest.approx(result.scores.recovery + result.scores.balance)
