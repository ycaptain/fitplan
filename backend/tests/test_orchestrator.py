from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.adaptability import orchestrator as orch_module
from app.ai.adaptability.orchestrator import (
    INFEASIBLE_REASON,
    orchestrate_replan,
)
from app.ai.adaptability.triggers import (
    from_fixed_event_added,
    from_manual_edit,
)
from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, CSPResult, FixedEvent, Plan

FIXTURES = Path(__file__).parent / "fixtures" / "sample_plans.json"


def _load_plan(plan_id: str) -> Plan:
    data = json.loads(FIXTURES.read_text())
    raw = next(p for p in data["plans"] if p["id"] == plan_id)
    return Plan.model_validate(raw)


def _meeting(event: FixedEvent) -> Constraint:
    return Constraint(
        id=f"evt-{event.id}",
        kind="hard",
        type=ConstraintType.FIXED_EVENT,
        params={
            "day_of_week": event.day_of_week,
            "start": event.start,
            "end": event.end,
        },
    )


def _thu_meeting() -> FixedEvent:
    return FixedEvent(
        id="evt-thu-meeting",
        day_of_week=3,
        start="18:30",
        end="20:00",
        label="Advisor meeting",
    )


def test_fixed_event_added_produces_diff_and_trace() -> None:
    plan = _load_plan("ppl-base-001")
    event = _thu_meeting()
    delta = from_fixed_event_added(plan, event)

    result = orchestrate_replan(
        plan, delta, [_meeting(event)], "minimal_disruption", random_seed=42
    )

    assert "3-push-18:00" in result.diff.moved
    roles = [step.role for step in result.plan.strategy_trace]
    assert "feasibility" in roles and "replan" in roles
    assert result.metrics.disturbance == (
        len(result.diff.moved) + len(result.diff.removed) + len(result.diff.added)
    )
    assert result.reason


def test_infeasible_returns_origin_with_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _load_plan("ppl-base-001")
    delta = from_manual_edit(plan, "0-push-18:00", new_start="07:00")
    origin = [s.model_dump() for s in plan.sessions]

    monkeypatch.setattr(
        orch_module,
        "_check_feasibility",
        lambda *_a, **_kw: CSPResult(is_feasible=False),
    )

    result = orchestrate_replan(plan, delta, [], "minimal_disruption")

    assert result.reason == INFEASIBLE_REASON
    assert [s.model_dump() for s in result.plan.sessions] == origin
    roles = [step.role for step in result.plan.strategy_trace]
    assert roles == ["feasibility"]


def test_residual_lock_does_not_freeze_newly_affected_session() -> None:
    """A session locked by a previous replan must still be movable when the
    next replan marks it as affected."""
    plan = _load_plan("ppl-base-001")
    target_id = plan.sessions[0].id
    plan.sessions[0] = plan.sessions[0].model_copy(update={"locked": True})
    target = plan.sessions[0]
    blocking_event = FixedEvent(
        id="evt-block",
        day_of_week=target.day,
        start=target.start,
        end="22:00",
        label="Day-long block",
    )
    delta = from_fixed_event_added(plan, blocking_event)
    assert target_id in delta.affected_session_ids

    result = orchestrate_replan(
        plan,
        delta,
        [_meeting(blocking_event)],
        "minimal_disruption",
        random_seed=1,
    )

    relocated = next(s for s in result.plan.sessions if s.id == target_id)
    assert (relocated.day, relocated.start) != (target.day, target.start)


def test_minimal_disruption_locks_unaffected() -> None:
    plan = _load_plan("ppl-base-001")
    event = _thu_meeting()
    delta = from_fixed_event_added(plan, event)
    untouched = {
        s.id: (s.day, s.start)
        for s in plan.sessions
        if s.id not in delta.affected_session_ids
    }

    result = orchestrate_replan(
        plan, delta, [_meeting(event)], "minimal_disruption", random_seed=42
    )

    for s in result.plan.sessions:
        if s.id in untouched:
            assert (s.day, s.start) == untouched[s.id]
