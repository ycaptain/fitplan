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

def test_goal_adjusted_duration_respects_max_duration() -> None:
    plan = generate_initial_plan(
        _request(
            goal="bulk",
            preferences=Preferences(
                preferred_time_of_day="any",
                max_session_duration_min=65,
            ),
        )
    )

    assert plan.sessions[0].duration_min == 65


def test_cut_duration_does_not_go_below_safe_minimum() -> None:
    plan = generate_initial_plan(
        _request(
            goal="cut",
            preferences=Preferences(
                preferred_time_of_day="any",
                max_session_duration_min=35,
            ),
        )
    )

    for session in plan.sessions:
        assert session.duration_min >= 30


def test_goal_adjustment_applies_to_all_generated_sessions() -> None:
    bulk_plan = generate_initial_plan(_request(goal="bulk"))
    general_plan = generate_initial_plan(_request(goal="general"))

    assert len(bulk_plan.sessions) == len(general_plan.sessions)

    for bulk_session, general_session in zip(
        bulk_plan.sessions,
        general_plan.sessions,
        strict=False,
    ):
        assert bulk_session.session_type_id == general_session.session_type_id
        assert bulk_session.duration_min >= general_session.duration_min


def test_generate_with_algorithm_selection() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    for algorithm, trace_name in [
        ("greedy_baseline", "greedy_baseline"),
        ("beam_search", "beam_search"),
    ]:
        resp = client.post(
            "/api/plan/generate",
            json={"split": "ppl", "sessions_per_week": 3, "algorithm": algorithm},
        )
        assert resp.status_code == 200
        assert resp.json()["strategy_trace"][-1]["algorithm"] == trace_name


def test_generate_rejects_unknown_algorithm() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/plan/generate",
        json={"split": "ppl", "sessions_per_week": 3, "algorithm": "nonsense"},
    )
    assert resp.status_code == 422


def test_generate_response_carries_explanation() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/plan/generate",
        json={"split": "ppl", "sessions_per_week": 3},
    )
    assert resp.status_code == 200
    explanation = resp.json()["explanation"]
    assert explanation["text_summary"]
    assert {h["constraint_id"] for h in explanation["constraint_hits"]} == {
        "fixed_event",
        "recovery_interval",
        "weekly_distribution",
    }
