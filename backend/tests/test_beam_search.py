from __future__ import annotations

from app.ai.core.models import FixedEvent, GeneratePlanRequest, Preferences
from app.ai.search.beam_search import generate_plan_beam


def _request(**overrides) -> GeneratePlanRequest:
    base = dict(
        goal="general",
        split="ppl",
        sessions_per_week=4,
        fixed_events=[],
        preferences=Preferences(
            preferred_time_of_day="any",
            max_session_duration_min=90,
        ),
    )
    base.update(overrides)
    return GeneratePlanRequest(**base)


def test_beam_search_generates_requested_sessions() -> None:
    plan = generate_plan_beam(_request(sessions_per_week=4))

    assert len(plan.sessions) == 4
    assert plan.strategy_trace[-1].algorithm == "beam_search"
    assert plan.strategy_trace[-1].nodes > 0


def test_beam_search_avoids_fixed_events() -> None:
    event = FixedEvent(
        id="class-1",
        day_of_week=0,
        start="07:00",
        end="09:00",
        label="Class",
    )

    plan = generate_plan_beam(_request(fixed_events=[event]))

    for session in plan.sessions:
        assert not _overlaps_event(session.day, session.start, session.duration_min, event)


def test_beam_search_respects_evening_preference() -> None:
    plan = generate_plan_beam(
        _request(
            preferences=Preferences(
                preferred_time_of_day="evening",
                max_session_duration_min=90,
            )
        )
    )

    assert all(session.start in {"17:00", "18:00", "19:00"} for session in plan.sessions)


def test_beam_search_spreads_sessions_across_week() -> None:
    plan = generate_plan_beam(_request(sessions_per_week=4))

    days = [session.day for session in plan.sessions]

    assert len(set(days)) >= 4


def test_beam_search_respects_max_session_duration() -> None:
    plan = generate_plan_beam(
        _request(
            preferences=Preferences(
                preferred_time_of_day="any",
                max_session_duration_min=50,
            )
        )
    )

    assert all(session.duration_min <= 50 for session in plan.sessions)


def _overlaps_event(
    day: int,
    start: str,
    duration_min: int,
    event: FixedEvent,
) -> bool:
    if day != event.day_of_week:
        return False

    session_start = _to_minutes(start)
    session_end = session_start + duration_min
    event_start = _to_minutes(event.start)
    event_end = _to_minutes(event.end)

    return session_start < event_end and event_start < session_end


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)
