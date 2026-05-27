from __future__ import annotations

from fastapi.testclient import TestClient


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
