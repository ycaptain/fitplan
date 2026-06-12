from __future__ import annotations

from app.ai.core.explain import explain_plan, explain_replan
from app.ai.core.models import (
    Plan,
    ReplanDiff,
    ReplanMetrics,
    ReplanResult,
    Scores,
    StrategyStep,
)


def test_explain_plan_returns_score_breakdown_and_summary() -> None:
    plan = Plan(
        id="plan-1",
        generated_at="2026-06-12T00:00:00Z",
        sessions=[],
        scores=Scores(
            recovery=1.0,
            consistency=0.0,
            conflicts=0,
            balance=0.0,
            total=1.0,
        ),
        strategy_trace=[
            StrategyStep(
                algorithm="csp_bt_fc",
                role="feasibility",
                nodes=4,
                iterations=0,
                time_ms=0,
                score_after=1.0,
            )
        ],
    )

    explanation = explain_plan(plan, constraints=[])

    assert explanation["score_breakdown"]["total"] == 1.0
    assert explanation["score_breakdown"]["conflicts"] == 0.0
    assert "csp_bt_fc generated" in explanation["text_summary"]
    assert any(hit["constraint_id"] == "fixed_event" for hit in explanation["constraint_hits"])


def test_explain_plan_reports_conflicts() -> None:
    plan = Plan(
        id="plan-2",
        generated_at="2026-06-12T00:00:00Z",
        sessions=[],
        scores=Scores(
            recovery=-1.0,
            consistency=0.0,
            conflicts=2,
            balance=0.0,
            total=-5.0,
        ),
    )

    explanation = explain_plan(plan, constraints=[])

    fixed_event_hit = next(
        hit for hit in explanation["constraint_hits"] if hit["constraint_id"] == "fixed_event"
    )

    assert fixed_event_hit["satisfied"] is False
    assert "2 conflict" in fixed_event_hit["explanation"]


def test_explain_replan_returns_disturbance_summary() -> None:
    plan = Plan(
        id="plan-3",
        generated_at="2026-06-12T00:00:00Z",
        sessions=[],
        scores=Scores(
            recovery=1.0,
            consistency=0.0,
            conflicts=0,
            balance=0.0,
            total=1.0,
        ),
        strategy_trace=[
            StrategyStep(
                algorithm="hill_climbing",
                role="replan",
                nodes=10,
                iterations=3,
                time_ms=5,
                score_after=1.0,
            )
        ],
    )

    result = ReplanResult(
        plan=plan,
        diff=ReplanDiff(added=[], removed=[], moved=[]),
        metrics=ReplanMetrics(
            disturbance=1,
            score_delta=0.0,
            moved_sessions=1,
            hard_violations_before=1,
            hard_violations_after=0,
        ),
    )

    explanation = explain_replan(result, constraints=[])

    assert explanation["score_breakdown"]["total"] == 1.0
    assert "hill_climbing" in explanation["text_summary"]
    assert any(
        hit["constraint_id"] == "post_replan_conflicts"
        for hit in explanation["constraint_hits"]
    )