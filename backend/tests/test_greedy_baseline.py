from __future__ import annotations

from app.ai.baselines.greedy import generate_greedy_baseline
from app.ai.core.models import FixedEvent, GeneratePlanRequest, Preferences


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


def test_greedy_baseline_generates_requested_sessions() -> None:
    plan = generate_greedy_baseline(_request(sessions_per_week=4))

    assert len(plan.sessions) == 4
    assert plan.strategy_trace[-1].algorithm == "greedy_baseline"


def test_greedy_baseline_avoids_fixed_events() -> None:
    event = FixedEvent(
        id="class-1",
        day_of_week=0,
        start="07:00",
        end="09:00",
        label="Class",
    )

    plan = generate_greedy_baseline(_request(fixed_events=[event]))

    for session in plan.sessions:
        assert not (
            session.day == 0
            and session.start in {"07:00", "08:00"}
        )


def test_greedy_baseline_respects_evening_preference() -> None:
    plan = generate_greedy_baseline(
        _request(
            preferences=Preferences(
                preferred_time_of_day="evening",
                max_session_duration_min=90,
            )
        )
    )

    assert plan.sessions[0].start == "17:00"
