from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_returns_plan(client: TestClient) -> None:
    response = client.post(
        "/api/plan/generate",
        json={
            "goal": "bulk",
            "split": "ppl",
            "sessions_per_week": 4,
            "fixed_events": [],
            "preferences": {
                "preferred_time_of_day": "evening",
                "max_session_duration_min": 75,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert "sessions" in body
    assert "scores" in body
    assert "strategy_trace" in body


def test_replan_returns_replan_result(client: TestClient) -> None:
    response = client.post(
        "/api/plan/replan",
        json={
            "plan_id": "test-plan",
            "trigger_type": "session_missed",
            "payload": {},
            "mode": "minimal_disruption",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["id"] == "test-plan"
    assert "diff" in body
    assert "metrics" in body


def test_core_models_import() -> None:
    from app.ai.core import constraints, explain, interfaces, models, registry, scoring

    assert hasattr(models, "Plan")
    assert hasattr(models, "CSPResult")
    assert hasattr(models, "GeneratePlanRequest")
    assert hasattr(constraints, "ConstraintType")
    assert hasattr(scoring, "score_plan")
    assert hasattr(explain, "explain_plan")
    assert hasattr(registry, "register")
    assert hasattr(registry, "AlgorithmKey")
    assert hasattr(interfaces, "InitialGenerator")
    assert hasattr(interfaces, "ReplanOrchestrator")
    assert hasattr(interfaces, "FeasibilityChecker")
    assert hasattr(interfaces, "LocalReplanner")
