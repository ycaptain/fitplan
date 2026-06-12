from __future__ import annotations

from app.ai.core.models import FixedEvent, GeneratePlanRequest, Preferences
from app.ai.ga.genetic_algorithm import generate_plan_ga


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


def test_ga_generates_requested_sessions() -> None:
    plan = generate_plan_ga(_request(sessions_per_week=4), random_seed=42)

    assert len(plan.sessions) == 4
    assert plan.strategy_trace[-1].algorithm == "ga_generate"
    assert plan.strategy_trace[-1].iterations == 40


def test_ga_respects_max_session_duration() -> None:
    plan = generate_plan_ga(
        _request(
            preferences=Preferences(
                preferred_time_of_day="any",
                max_session_duration_min=50,
            )
        ),
        random_seed=42,
    )

    assert all(session.duration_min <= 50 for session in plan.sessions)


def test_ga_respects_evening_preference() -> None:
    plan = generate_plan_ga(
        _request(
            preferences=Preferences(
                preferred_time_of_day="evening",
                max_session_duration_min=90,
            )
        ),
        random_seed=42,
    )

    assert all(session.start in {"17:00", "18:00", "19:00"} for session in plan.sessions)


def test_ga_is_deterministic_with_seed() -> None:
    first = generate_plan_ga(_request(), random_seed=42)
    second = generate_plan_ga(_request(), random_seed=42)

    first_schedule = [(s.day, s.start, s.session_type_id) for s in first.sessions]
    second_schedule = [(s.day, s.start, s.session_type_id) for s in second.sessions]

    assert first_schedule == second_schedule


def test_ga_avoids_fixed_event_when_possible() -> None:
    event = FixedEvent(
        id="class-1",
        day_of_week=0,
        start="07:00",
        end="09:00",
        label="Class",
    )

    plan = generate_plan_ga(_request(fixed_events=[event]), random_seed=42)

    for session in plan.sessions:
        assert not (
            session.day == 0
            and session.start in {"07:00", "08:00"}
        )