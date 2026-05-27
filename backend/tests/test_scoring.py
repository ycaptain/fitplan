from __future__ import annotations

from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, Plan, ScheduledSession
from app.ai.core.scoring import (
    CONFLICT_PENALTY,
    count_hard_violations,
    score_plan,
)


def _session(day: int, type_id: str, start: str, duration: int = 60) -> ScheduledSession:
    return ScheduledSession(
        id=ScheduledSession.derive_id(day, type_id, start),
        session_type_id=type_id,
        day=day,
        start=start,
        duration_min=duration,
    )


def _plan(sessions: list[ScheduledSession]) -> Plan:
    return Plan(id="t", generated_at="1970-01-01T00:00:00Z", sessions=sessions)


def test_clean_plan_outscores_conflicting_plan() -> None:
    clean = _plan(
        [
            _session(0, "push", "18:00"),
            _session(2, "pull", "18:00"),
            _session(4, "legs", "18:00"),
        ]
    )
    conflicting = _plan(
        [
            _session(0, "push", "18:00"),
            _session(0, "push", "18:30"),
            _session(4, "legs", "18:00"),
        ]
    )

    s_clean = score_plan(clean, [])
    s_conflict = score_plan(conflicting, [])

    assert s_conflict.total < s_clean.total
    assert s_conflict.conflicts >= 1
    assert s_clean.conflicts == 0
    assert s_conflict.total <= s_clean.total - CONFLICT_PENALTY


def test_count_hard_violations_includes_fixed_events() -> None:
    plan = _plan([_session(2, "pull", "18:00", duration=60)])
    fixed_event = Constraint(
        id="cls-stats",
        kind="hard",
        type=ConstraintType.FIXED_EVENT,
        params={"day_of_week": 2, "start": "18:30", "end": "20:00"},
    )

    assert count_hard_violations(plan, []) == 0
    assert count_hard_violations(plan, [fixed_event]) == 1


def test_count_hard_violations_flags_same_day_overload() -> None:
    plan = _plan(
        [
            _session(0, "push", "07:00"),
            _session(0, "pull", "17:00"),
            _session(2, "legs", "18:00"),
        ]
    )

    assert count_hard_violations(plan, []) == 1


def test_recovery_penalises_close_same_type_sessions() -> None:
    close = _plan([_session(0, "push", "18:00"), _session(1, "push", "18:00")])
    spaced = _plan([_session(0, "push", "18:00"), _session(3, "push", "18:00")])

    assert score_plan(close, []).recovery < score_plan(spaced, []).recovery
