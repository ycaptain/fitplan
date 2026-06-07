from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCENARIOS_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "eval" / "scenarios.py"
)


def _load_scenarios_module():
    spec = importlib.util.spec_from_file_location("eval_scenarios", SCENARIOS_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["eval_scenarios"] = module
    spec.loader.exec_module(module)
    return module


def test_scenarios_cover_all_triggers_and_plans() -> None:
    module = _load_scenarios_module()
    scenarios = module.generate_scenarios()

    assert len(scenarios) >= 24
    assert {s.trigger_type for s in scenarios} == {
        "fixed_event_added",
        "session_missed",
        "state_changed",
        "manual_edit",
    }
    assert {s.plan_id for s in scenarios} == {
        "ppl-base-001",
        "ul-base-001",
        "fb-base-001",
    }


def test_scenario_intensities_are_normalised() -> None:
    module = _load_scenarios_module()
    scenarios = module.generate_scenarios()

    assert all(0.0 <= s.intensity <= 1.0 for s in scenarios)
    # The gradient must span both routing regimes around the 0.3 threshold.
    assert any(s.intensity > 0.3 for s in scenarios)
    assert any(0.0 < s.intensity <= 0.3 for s in scenarios)


def test_scenario_names_are_unique() -> None:
    module = _load_scenarios_module()
    scenarios = module.generate_scenarios()
    names = [s.name for s in scenarios]
    assert len(names) == len(set(names))
