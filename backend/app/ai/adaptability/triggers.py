from __future__ import annotations

from app.ai.core.models import FixedEvent, Plan, PlanDelta, UserState

HIGH_FATIGUE_THRESHOLD: int = 7
LOW_SLEEP_HOURS: float = 5.0


def from_fixed_event_added(plan: Plan, event: FixedEvent) -> PlanDelta:
    event_start = _minutes(event.start)
    event_end = _minutes(event.end)
    affected = [
        s.id
        for s in plan.sessions
        if s.day == event.day_of_week
        and _minutes(s.start) < event_end
        and event_start < _minutes(s.start) + s.duration_min
    ]
    return PlanDelta(
        trigger_type="fixed_event_added",
        payload=event.model_dump(),
        affected_session_ids=affected,
    )


def from_session_missed(plan: Plan, session_id: str) -> PlanDelta:
    affected = [s.id for s in plan.sessions if s.id == session_id]
    return PlanDelta(
        trigger_type="session_missed",
        payload={"session_id": session_id},
        affected_session_ids=affected,
    )


def from_state_changed(plan: Plan, user_state: UserState) -> PlanDelta:
    if not _state_disrupts_training(user_state):
        return PlanDelta(
            trigger_type="state_changed",
            payload=user_state.model_dump(),
            affected_session_ids=[],
        )
    target_day = _day_of(user_state.date)
    affected = [s.id for s in plan.sessions if target_day is None or s.day == target_day]
    return PlanDelta(
        trigger_type="state_changed",
        payload=user_state.model_dump(),
        affected_session_ids=affected,
    )


def from_manual_edit(plan: Plan, session_id: str, new_start: str) -> PlanDelta:
    return PlanDelta(
        trigger_type="manual_edit",
        payload={"session_id": session_id, "new_start": new_start},
        affected_session_ids=[s.id for s in plan.sessions if s.id == session_id],
    )


def _state_disrupts_training(state: UserState) -> bool:
    return (
        state.missed_last_session
        or state.perceived_fatigue >= HIGH_FATIGUE_THRESHOLD
        or state.sleep_hours <= LOW_SLEEP_HOURS
    )


def _day_of(iso_date: str) -> int | None:
    from datetime import date

    try:
        return date.fromisoformat(iso_date).weekday()
    except ValueError:
        return None


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)
