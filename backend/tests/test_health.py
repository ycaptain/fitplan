from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_stub(client: TestClient) -> None:
    response = client.post("/api/plan/generate", json={"goal": "bulk"})
    assert response.status_code == 200
    body = response.json()
    assert "plan_id" in body
    assert "message" in body


def test_replan_stub(client: TestClient) -> None:
    response = client.post(
        "/api/plan/replan",
        json={"plan_id": "test-plan", "trigger_type": "session_missed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan_id"] == "test-plan"
    assert "diff" in body


def test_core_models_import() -> None:
    """Smoke test: ensure shared contract layer imports cleanly."""
    from app.ai.core import constraints, explain, models, registry, scoring

    assert hasattr(models, "Plan")
    assert hasattr(constraints, "ConstraintType")
    assert hasattr(scoring, "score_plan")
    assert hasattr(explain, "explain_plan")
    assert hasattr(registry, "register")
