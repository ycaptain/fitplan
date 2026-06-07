"""Disturbance scenario generation for the offline evaluation harness.

Builds ~30 replan scenarios (4 trigger types x several magnitudes) from the
plan fixtures shared with the backend test suite, so eval results stay
comparable with unit-test behaviour.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.ai.adaptability.triggers import (
    from_fixed_event_added,
    from_manual_edit,
    from_session_missed,
    from_state_changed,
    sessions_overlapping_events,
)
from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, FixedEvent, Plan, PlanDelta, UserState

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "backend" / "tests" / "fixtures" / "sample_plans.json"

# Fixture day indices map onto this fixed ISO week (day 0 = Monday 2026-06-01).
BASE_WEEK = [f"2026-06-{day:02d}" for day in range(1, 8)]


@dataclass(frozen=True)
class Scenario:
    name: str
    plan_id: str
    trigger_type: str
    delta: PlanDelta
    constraints: list[Constraint] = field(default_factory=list)
    intensity: float = 0.0  # share of sessions affected, 0..1


def load_plans() -> dict[str, Plan]:
    data = json.loads(FIXTURES.read_text())
    return {p["id"]: Plan.model_validate(p) for p in data["plans"]}


def generate_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []
    for plan_id, plan in load_plans().items():
        scenarios.extend(_fixed_event_scenarios(plan_id, plan))
        scenarios.extend(_session_missed_scenarios(plan_id, plan))
        scenarios.extend(_state_changed_scenarios(plan_id, plan))
        scenarios.extend(_manual_edit_scenarios(plan_id, plan))
    return scenarios


def _fixed_event_scenarios(plan_id: str, plan: Plan) -> list[Scenario]:
    """Events of growing width: one slot, one evening, one day, every day."""
    target = plan.sessions[0]
    session_days = sorted({s.day for s in plan.sessions})
    variants: list[tuple[str, list[FixedEvent]]] = [
        (
            "single-slot",
            [_event("evt-slot", target.day, target.start, _shift(target.start, 60))],
        ),
        (
            "evening-block",
            [_event("evt-evening", target.day, "17:00", "21:00")],
        ),
        (
            "full-day",
            [_event("evt-day", target.day, "06:00", "22:00")],
        ),
        (
            "every-training-day",
            [
                _event(f"evt-multi-{day}", day, "16:00", "21:00")
                for day in session_days
            ],
        ),
    ]

    scenarios = []
    for label, events in variants:
        if len(events) == 1:
            delta = from_fixed_event_added(plan, events[0])
        else:
            delta = PlanDelta(
                trigger_type="fixed_event_added",
                payload=events[0].model_dump(),
                affected_session_ids=sessions_overlapping_events(plan, events),
            )
        scenarios.append(
            Scenario(
                name=f"{plan_id}/fixed-event/{label}",
                plan_id=plan_id,
                trigger_type="fixed_event_added",
                delta=delta,
                constraints=[_constraint_of(e) for e in events],
                intensity=_ratio(delta, plan),
            )
        )
    return scenarios


def _session_missed_scenarios(plan_id: str, plan: Plan) -> list[Scenario]:
    picks = {0, len(plan.sessions) // 2, len(plan.sessions) - 1}
    scenarios = []
    for idx in sorted(picks):
        session = plan.sessions[idx]
        delta = from_session_missed(plan, session.id)
        scenarios.append(
            Scenario(
                name=f"{plan_id}/missed/session-{idx}",
                plan_id=plan_id,
                trigger_type="session_missed",
                delta=delta,
                intensity=_ratio(delta, plan),
            )
        )
    return scenarios


def _state_changed_scenarios(plan_id: str, plan: Plan) -> list[Scenario]:
    first_day = plan.sessions[0].day
    states = [
        ("recovered", UserState(date=BASE_WEEK[first_day], perceived_fatigue=4)),
        ("high-fatigue", UserState(date=BASE_WEEK[first_day], perceived_fatigue=9)),
        ("low-sleep", UserState(date=BASE_WEEK[first_day], sleep_hours=4.5)),
    ]
    scenarios = []
    for label, state in states:
        delta = from_state_changed(plan, state)
        scenarios.append(
            Scenario(
                name=f"{plan_id}/state/{label}",
                plan_id=plan_id,
                trigger_type="state_changed",
                delta=delta,
                intensity=_ratio(delta, plan),
            )
        )
    return scenarios


def _manual_edit_scenarios(plan_id: str, plan: Plan) -> list[Scenario]:
    target = plan.sessions[0]
    collide_with = plan.sessions[1] if len(plan.sessions) > 1 else target
    edits = [
        ("to-free-slot", "07:00"),
        ("onto-other-session", collide_with.start),
    ]
    scenarios = []
    for label, new_start in edits:
        delta = from_manual_edit(plan, target.id, new_start=new_start)
        scenarios.append(
            Scenario(
                name=f"{plan_id}/manual/{label}",
                plan_id=plan_id,
                trigger_type="manual_edit",
                delta=delta,
                intensity=_ratio(delta, plan),
            )
        )
    return scenarios


def _event(event_id: str, day: int, start: str, end: str) -> FixedEvent:
    return FixedEvent(id=event_id, day_of_week=day, start=start, end=end, label=event_id)


def _constraint_of(event: FixedEvent) -> Constraint:
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


def _ratio(delta: PlanDelta, plan: Plan) -> float:
    return len(delta.affected_session_ids) / max(1, len(plan.sessions))


def _shift(hhmm: str, minutes: int) -> str:
    h, m = hhmm.split(":")
    total = int(h) * 60 + int(m) + minutes
    return f"{total // 60:02d}:{total % 60:02d}"
