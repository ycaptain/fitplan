from __future__ import annotations

from app.ai.core.models import FixedEvent, GeneratePlanRequest, Preferences
from app.ai.csp.backtracking import generate_initial_plan


def _request(**overrides) -> GeneratePlanRequest:
    base = dict(
        goal="general",
        split="ppl",
        sessions_per_week=4,
        fixed_events=[],
        preferences=Preferences(
            preferred_time_of_day="any", max_session_duration_min=90
        ),
    )
    base.update(overrides)
    return GeneratePlanRequest(**base)


def test_at_most_one_session_per_day() -> None:
    plan = generate_initial_plan(_request(sessions_per_week=6))
    days = [s.day for s in plan.sessions]
    assert len(days) == len(set(days))


def test_sessions_avoid_blocked_days() -> None:
    blocked_days = [1, 2, 3]
    events = [
        FixedEvent(
            id=f"evt-{day}",
            day_of_week=day,
            start="06:00",
            end="23:00",
            label=f"day-{day}",
        )
        for day in blocked_days
    ]

    plan = generate_initial_plan(_request(fixed_events=events))

    for session in plan.sessions:
        assert session.day not in blocked_days


def test_capacity_overflow_doubles_up_with_max_gap() -> None:
    events = [
        FixedEvent(
            id=f"evt-{day}",
            day_of_week=day,
            start="06:00",
            end="23:00",
            label=f"day-{day}",
        )
        for day in (2, 3, 4, 5, 6)
    ]

    plan = generate_initial_plan(_request(sessions_per_week=4, fixed_events=events))

    assert len(plan.sessions) == 4

    blocked = {2, 3, 4, 5, 6}
    for session in plan.sessions:
        assert session.day not in blocked

    counts: dict[int, int] = {}
    for session in plan.sessions:
        counts[session.day] = counts.get(session.day, 0) + 1
    assert max(counts.values()) >= 2

    for day, count in counts.items():
        if count < 2:
            continue
        same_day = sorted(
            (s for s in plan.sessions if s.day == day),
            key=lambda s: s.start,
        )
        for first, second in zip(same_day, same_day[1:], strict=False):
            first_end_min = _to_minutes(first.start) + first.duration_min
            assert _to_minutes(second.start) >= first_end_min + 60


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def test_goal_adjusts_session_duration() -> None:
    bulk_plan = generate_initial_plan(_request(goal="bulk"))
    cut_plan = generate_initial_plan(_request(goal="cut"))
    general_plan = generate_initial_plan(_request(goal="general"))

    bulk_first_duration = bulk_plan.sessions[0].duration_min
    cut_first_duration = cut_plan.sessions[0].duration_min
    general_first_duration = general_plan.sessions[0].duration_min

    assert bulk_first_duration > general_first_duration
    assert cut_first_duration < general_first_duration
