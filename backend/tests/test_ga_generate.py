from __future__ import annotations

import pytest

from app.ai.core import registry
from app.ai.core.models import GeneratePlanRequest, Preferences
from app.ai.ga.genetic_algorithm import ga_generate

_BASE = GeneratePlanRequest(
    goal="general",
    split="ppl",
    sessions_per_week=4,
    preferences=Preferences(),
)


def test_ga_registers() -> None:
    assert registry.get(registry.AlgorithmKey.GA_GENERATE) is not None


def test_ga_returns_correct_session_count() -> None:
    plan = ga_generate(_BASE, [], random_seed=0)
    assert len(plan.sessions) == 4


@pytest.mark.parametrize("split,n", [("upper_lower", 3), ("full_body", 5)])
def test_ga_session_count_for_other_splits(split: str, n: int) -> None:
    req = GeneratePlanRequest(
        goal="general",
        split=split,
        sessions_per_week=n,
        preferences=Preferences(),
    )
    plan = ga_generate(req, [], random_seed=1)
    assert len(plan.sessions) == n


def test_ga_deterministic() -> None:
    a = ga_generate(_BASE, [], random_seed=42)
    b = ga_generate(_BASE, [], random_seed=42)
    assert [(s.day, s.session_type_id, s.start) for s in a.sessions] == [
        (s.day, s.session_type_id, s.start) for s in b.sessions
    ]


def test_ga_sessions_in_valid_window() -> None:
    plan = ga_generate(_BASE, [], random_seed=7)
    for s in plan.sessions:
        h, m = map(int, s.start.split(":"))
        start_min = h * 60 + m
        end_min = start_min + s.duration_min
        assert start_min >= 6 * 60, f"{s.id} starts before 06:00"
        assert end_min <= 22 * 60, f"{s.id} ends after 22:00"
