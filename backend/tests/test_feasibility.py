from __future__ import annotations

import json
from pathlib import Path

from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, Plan
from app.ai.csp.feasibility import check_feasibility

FIXTURES = Path(__file__).parent / "fixtures" / "sample_plans.json"


def _load_plan(plan_id: str) -> Plan:
    data = json.loads(FIXTURES.read_text())
    raw = next(p for p in data["plans"] if p["id"] == plan_id)
    return Plan.model_validate(raw)


def _meeting(day: int, start: str, end: str, *, event_id: str | None = None) -> Constraint:
    return Constraint(
        id=event_id or f"evt-d{day}-{start}",
        kind="hard",
        type=ConstraintType.FIXED_EVENT,
        params={"day_of_week": day, "start": start, "end": end},
    )


def _block_entire_week() -> list[Constraint]:
    return [
        _meeting(day, "06:00", "22:00", event_id=f"all-day-{day}")
        for day in range(7)
    ]


def test_clean_plan_is_feasible_with_no_violations() -> None:
    plan = _load_plan("ppl-base-001")

    result = check_feasibility(plan, [])

    assert result.is_feasible
    assert result.violations == []


def test_overlapped_session_with_open_slots_is_feasible() -> None:
    plan = _load_plan("ppl-base-001")
    target = plan.sessions[0]
    constraints = [_meeting(target.day, target.start, "21:00")]

    result = check_feasibility(plan, constraints)

    assert result.is_feasible
    assert any(target.id in v.session_ids for v in result.violations)


def test_domain_wipeout_is_infeasible() -> None:
    plan = _load_plan("ppl-base-001")

    result = check_feasibility(plan, _block_entire_week())

    assert not result.is_feasible
    assert result.violations


def test_locked_session_in_violation_is_infeasible() -> None:
    plan = _load_plan("ppl-base-001")
    target = plan.sessions[0]
    plan.sessions[0] = target.model_copy(update={"locked": True})
    constraints = [_meeting(target.day, target.start, "21:00")]

    result = check_feasibility(plan, constraints)

    assert not result.is_feasible
    assert target.id in result.locked_session_ids


def test_locked_vs_unlocked_conflict_is_feasible() -> None:
    plan = _load_plan("ppl-base-001")
    a = plan.sessions[0]
    plan.sessions[0] = a.model_copy(update={"locked": True})
    plan.sessions[1] = plan.sessions[1].model_copy(
        update={"day": a.day, "start": a.start}
    )

    result = check_feasibility(plan, [])

    assert result.is_feasible
    assert any(
        set(v.session_ids) == {plan.sessions[0].id, plan.sessions[1].id}
        for v in result.violations
    )
