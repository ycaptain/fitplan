from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.ai.core import registry
from app.api import plan_store


@pytest.fixture(autouse=True)
def reset_plan_store() -> None:
    plan_store.reset()


def test_replan_endpoint_returns_diff(client: TestClient) -> None:
    response = client.post(
        "/api/plan/replan",
        json={
            "plan_id": "ppl-base-001",
            "trigger_type": "fixed_event_added",
            "payload": {
                "id": "evt-thu-meeting",
                "day_of_week": 3,
                "start": "18:30",
                "end": "20:00",
                "label": "Advisor meeting",
            },
            "mode": "minimal_disruption",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["id"] == "ppl-base-001"
    assert "3-push-18:00" in body["diff"]["moved"]
    assert body["metrics"]["disturbance"] >= 1
    assert body["reason"]


def test_replan_endpoint_bootstraps_hill_climbing(client: TestClient) -> None:
    client.post(
        "/api/plan/replan",
        json={
            "plan_id": "ppl-base-001",
            "trigger_type": "session_missed",
            "payload": {"session_id": "0-push-18:00"},
            "mode": "minimal_disruption",
        },
    )

    assert registry.AlgorithmKey.HILL_CLIMBING in registry.names()


def test_replan_after_generate_moves_disturbed_session(client: TestClient) -> None:
    generate_resp = client.post(
        "/api/plan/generate",
        json={
            "goal": "general",
            "split": "ppl",
            "sessions_per_week": 3,
            "fixed_events": [],
            "preferences": {
                "preferred_time_of_day": "any",
                "max_session_duration_min": 90,
            },
        },
    )
    assert generate_resp.status_code == 200
    plan = generate_resp.json()
    assert plan["sessions"]

    target = plan["sessions"][0]
    block = {
        "id": "evt-block",
        "day_of_week": target["day"],
        "start": "06:00",
        "end": "22:30",
        "label": "All-day block",
    }

    replan_resp = client.post(
        "/api/plan/replan",
        json={
            "plan_id": plan["id"],
            "trigger_type": "fixed_event_added",
            "payload": block,
            "mode": "minimal_disruption",
        },
    )

    assert replan_resp.status_code == 200
    body = replan_resp.json()
    assert body["plan"]["id"] == plan["id"]

    relocated = next(
        (s for s in body["plan"]["sessions"] if s["id"] == target["id"]),
        None,
    )
    assert relocated is not None
    block_start = _to_minutes(block["start"])
    block_end = _to_minutes(block["end"])
    if relocated["day"] == target["day"]:
        s_start = _to_minutes(relocated["start"])
        s_end = s_start + relocated["duration_min"]
        assert s_end <= block_start or s_start >= block_end

    algorithms = [step["algorithm"] for step in body["plan"]["strategy_trace"]]
    assert registry.AlgorithmKey.HILL_CLIMBING in algorithms


def test_replan_resolves_residual_overlap_from_prior_event(client: TestClient) -> None:
    """A session left overlapping a prior block must be relocated on next replan."""
    generate_resp = client.post(
        "/api/plan/generate",
        json={
            "goal": "general",
            "split": "upper_lower",
            "sessions_per_week": 4,
            "fixed_events": [],
            "preferences": {
                "preferred_time_of_day": "any",
                "max_session_duration_min": 90,
            },
        },
    )
    plan = generate_resp.json()
    plan_id = plan["id"]
    target = plan["sessions"][0]

    # First event overlaps target session; the immediate replan resolves it.
    first_block = {
        "id": "evt-first",
        "day_of_week": target["day"],
        "start": target["start"],
        "end": "23:00",
        "label": "first",
    }
    client.post(
        "/api/plan/replan",
        json={
            "plan_id": plan_id,
            "trigger_type": "fixed_event_added",
            "payload": first_block,
            "mode": "minimal_disruption",
        },
    )

    # Simulate a stale residual overlap: hand-edit the stored plan so a session
    # again falls inside `first_block`. Then add another, unrelated block and
    # ensure the residual conflict is picked up and resolved.
    stored = plan_store.get(plan_id)
    assert stored is not None
    sessions = list(stored.plan.sessions)
    sessions[-1] = sessions[-1].model_copy(
        update={"day": target["day"], "start": "08:00", "locked": False}
    )
    stored.plan.sessions = sessions
    plan_store.put(stored.plan, stored.events)

    second_block = {
        "id": "evt-second",
        "day_of_week": (target["day"] + 3) % 7,
        "start": "10:00",
        "end": "11:00",
        "label": "second",
    }
    replan_resp = client.post(
        "/api/plan/replan",
        json={
            "plan_id": plan_id,
            "trigger_type": "fixed_event_added",
            "payload": second_block,
            "mode": "minimal_disruption",
        },
    )

    assert replan_resp.status_code == 200
    body = replan_resp.json()
    blocks = [first_block, second_block]
    for session in body["plan"]["sessions"]:
        s_start = _to_minutes(session["start"])
        s_end = s_start + session["duration_min"]
        for block in blocks:
            if block["day_of_week"] != session["day"]:
                continue
            e_start = _to_minutes(block["start"])
            e_end = _to_minutes(block["end"])
            assert not (s_start < e_end and e_start < s_end), (
                f"session {session['id']} still overlaps block {block['id']}"
            )


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def test_replan_uses_client_provided_events_as_authoritative(
    client: TestClient,
) -> None:
    """When the client sends `fixed_events`, those override the server cache,
    so blocks the user added without triggering replan are still respected."""
    generate_resp = client.post(
        "/api/plan/generate",
        json={
            "goal": "general",
            "split": "upper_lower",
            "sessions_per_week": 4,
            "fixed_events": [],
            "preferences": {
                "preferred_time_of_day": "any",
                "max_session_duration_min": 90,
            },
        },
    )
    plan = generate_resp.json()
    plan_id = plan["id"]

    sessions_by_day = {s["day"]: s for s in plan["sessions"]}
    days = sorted(sessions_by_day.keys())
    assert len(days) >= 2

    silent_block = {
        "id": "evt-silent",
        "day_of_week": days[0],
        "start": sessions_by_day[days[0]]["start"],
        "end": "20:00",
        "label": "silent",
    }
    triggering_block = {
        "id": "evt-trigger",
        "day_of_week": days[1],
        "start": sessions_by_day[days[1]]["start"],
        "end": "20:00",
        "label": "trigger",
    }

    replan_resp = client.post(
        "/api/plan/replan",
        json={
            "plan_id": plan_id,
            "trigger_type": "fixed_event_added",
            "payload": triggering_block,
            "mode": "minimal_disruption",
            "fixed_events": [silent_block, triggering_block],
        },
    )

    assert replan_resp.status_code == 200
    body = replan_resp.json()
    blocks = [silent_block, triggering_block]
    for session in body["plan"]["sessions"]:
        s_start = _to_minutes(session["start"])
        s_end = s_start + session["duration_min"]
        for block in blocks:
            if block["day_of_week"] != session["day"]:
                continue
            e_start = _to_minutes(block["start"])
            e_end = _to_minutes(block["end"])
            assert not (s_start < e_end and e_start < s_end), (
                f"session {session['id']} still overlaps block {block['id']}"
            )


def test_replan_handles_block_covering_multiple_sessions(client: TestClient) -> None:
    """A single block covering multiple sessions on the same day must move all
    overlapping sessions out, not just one."""
    generate_resp = client.post(
        "/api/plan/generate",
        json={
            "goal": "general",
            "split": "upper_lower",
            "sessions_per_week": 4,
            "fixed_events": [],
            "preferences": {
                "preferred_time_of_day": "any",
                "max_session_duration_min": 90,
            },
        },
    )
    plan = generate_resp.json()
    plan_id = plan["id"]

    # Force two sessions onto the same day so the next block can hit both.
    stored = plan_store.get(plan_id)
    assert stored is not None
    target_day = stored.plan.sessions[0].day
    sessions = list(stored.plan.sessions)
    sessions[1] = sessions[1].model_copy(
        update={"day": target_day, "start": "17:00", "locked": False}
    )
    stored.plan.sessions = sessions
    plan_store.put(stored.plan, stored.events)

    wide_block = {
        "id": "evt-wide",
        "day_of_week": target_day,
        "start": "06:00",
        "end": "20:00",
        "label": "wide",
    }
    replan_resp = client.post(
        "/api/plan/replan",
        json={
            "plan_id": plan_id,
            "trigger_type": "fixed_event_added",
            "payload": wide_block,
            "mode": "minimal_disruption",
            "fixed_events": [wide_block],
        },
    )

    assert replan_resp.status_code == 200
    body = replan_resp.json()
    block_start = _to_minutes(wide_block["start"])
    block_end = _to_minutes(wide_block["end"])
    for session in body["plan"]["sessions"]:
        if session["day"] != target_day:
            continue
        s_start = _to_minutes(session["start"])
        s_end = s_start + session["duration_min"]
        assert s_end <= block_start or s_start >= block_end, (
            f"session {session['id']} still overlaps wide block"
        )
    # At least the two sessions originally on target_day must have been moved.
    assert len(body["diff"]["moved"]) >= 2


def test_replan_endpoint_unknown_plan_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/plan/replan",
        json={
            "plan_id": "ghost",
            "trigger_type": "session_missed",
            "payload": {"session_id": "0-push-18:00"},
        },
    )

    assert response.status_code == 404
