from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, Plan, ScheduledSession
from app.ai.core.scoring import count_hard_violations
from app.ai.local.hill_climbing import hill_climbing

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


def test_same_seed_yields_identical_plan() -> None:
    plan = _load_plan("ppl-base-001")
    constraints = [_meeting(3, "18:30", "20:00")]

    a = hill_climbing(plan, constraints, random_seed=42)
    b = hill_climbing(plan, constraints, random_seed=42)

    assert a.model_dump() == b.model_dump()


def test_locked_sessions_stay_put() -> None:
    plan = _load_plan("ppl-base-001")
    plan.sessions[2] = plan.sessions[2].model_copy(update={"locked": True})
    plan.sessions[5] = plan.sessions[5].model_copy(update={"locked": True})
    locked_before = {s.id: (s.day, s.start) for s in plan.sessions if s.locked}

    result = hill_climbing(
        plan,
        [_meeting(3, "18:30", "20:00")],
        random_seed=7,
    )

    locked_after = {s.id: (s.day, s.start) for s in result.sessions if s.locked}
    assert locked_after == locked_before


def test_hard_violations_never_grow() -> None:
    plan = _load_plan("ppl-base-001")
    constraints = [_meeting(3, "18:30", "20:00")]
    before = count_hard_violations(plan, constraints)

    result = hill_climbing(plan, constraints, random_seed=11)

    after = count_hard_violations(result, constraints)
    assert after <= before


def test_empty_plan_is_returned_unchanged() -> None:
    empty = Plan(id="empty", generated_at="1970-01-01T00:00:00Z", sessions=[])
    result = hill_climbing(empty, [], random_seed=1)
    assert result.sessions == []


def test_all_locked_plan_is_returned_unchanged() -> None:
    plan = _load_plan("ul-base-001")
    plan.sessions = [s.model_copy(update={"locked": True}) for s in plan.sessions]
    snapshot = [(s.id, s.day, s.start) for s in plan.sessions]

    result = hill_climbing(plan, [], random_seed=1)

    assert [(s.id, s.day, s.start) for s in result.sessions] == snapshot


def test_single_session_plan_keeps_session() -> None:
    plan = Plan(
        id="single",
        generated_at="1970-01-01T00:00:00Z",
        sessions=[
            ScheduledSession(
                id="0-push-18:00",
                session_type_id="push",
                day=0,
                start="18:00",
                duration_min=60,
            )
        ],
    )

    result = hill_climbing(plan, [], random_seed=1)

    assert len(result.sessions) == 1
    assert result.sessions[0].session_type_id == "push"


@pytest.mark.parametrize("seed", [0, 1, 99])
def test_seed_isolation_is_pure(seed: int) -> None:
    plan = _load_plan("ul-base-001")
    a = hill_climbing(plan, [], random_seed=seed)
    b = hill_climbing(plan, [], random_seed=seed)
    assert a.model_dump() == b.model_dump()


def test_sessions_stay_within_training_window() -> None:
    """Sessions must never be scheduled to finish after 22:00 (calendar UI bound)."""
    sessions = [
        ScheduledSession(
            id=ScheduledSession.derive_id(day, "legs", "07:00"),
            session_type_id="legs",
            day=day,
            start="07:00",
            duration_min=70,
        )
        for day in range(3)
    ]
    plan = Plan(id="late-night", generated_at="1970-01-01T00:00:00Z", sessions=sessions)
    constraints = [
        _meeting(0, "07:00", "15:00"),
        _meeting(2, "06:30", "15:00"),
        _meeting(2, "16:00", "21:00"),
        _meeting(2, "21:30", "23:00"),
    ]

    result = hill_climbing(plan, constraints, random_seed=5)

    for s in result.sessions:
        end_min = int(s.start.split(":")[0]) * 60 + int(s.start.split(":")[1]) + s.duration_min
        assert end_min <= 22 * 60, f"session {s.id} ends past 22:00"


def test_narrow_calendar_eliminates_hard_violations() -> None:
    sessions = [
        ScheduledSession(
            id=ScheduledSession.derive_id(day, "upper" if day % 2 == 0 else "lower", "07:00"),
            session_type_id="upper" if day % 2 == 0 else "lower",
            day=day,
            start="07:00",
            duration_min=60,
        )
        for day in range(6)
    ]
    plan = Plan(id="narrow", generated_at="1970-01-01T00:00:00Z", sessions=sessions)
    constraints = [
        _meeting(0, "06:30", "13:00"),
        _meeting(1, "08:30", "11:00"),
        _meeting(2, "07:00", "09:30"),
        _meeting(4, "09:30", "11:00"),
    ]
    assert count_hard_violations(plan, constraints) > 0

    result = hill_climbing(plan, constraints, random_seed=3)

    assert count_hard_violations(result, constraints) == 0
