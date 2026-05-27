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
    assert relocated["day"] != target["day"]

    algorithms = [step["algorithm"] for step in body["plan"]["strategy_trace"]]
    assert registry.AlgorithmKey.HILL_CLIMBING in algorithms


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
