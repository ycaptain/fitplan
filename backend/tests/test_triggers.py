from __future__ import annotations

import json
from pathlib import Path

from app.ai.adaptability.triggers import (
    from_fixed_event_added,
    from_manual_edit,
    from_session_missed,
    from_state_changed,
)
from app.ai.core.models import FixedEvent, Plan, UserState

FIXTURES = Path(__file__).parent / "fixtures" / "sample_plans.json"


def _load_plan(plan_id: str) -> Plan:
    data = json.loads(FIXTURES.read_text())
    raw = next(p for p in data["plans"] if p["id"] == plan_id)
    return Plan.model_validate(raw)


def test_fixed_event_marks_overlapping_session() -> None:
    plan = _load_plan("ppl-base-001")
    event = FixedEvent(
        id="evt-thu-meeting",
        day_of_week=3,
        start="18:30",
        end="20:00",
        label="Advisor meeting",
    )

    delta = from_fixed_event_added(plan, event)

    assert delta.trigger_type == "fixed_event_added"
    assert delta.affected_session_ids == ["3-push-18:00"]
    assert delta.payload["label"] == "Advisor meeting"


def test_session_missed_targets_only_that_id() -> None:
    plan = _load_plan("ul-base-001")

    delta = from_session_missed(plan, "0-upper-19:00")

    assert delta.trigger_type == "session_missed"
    assert delta.affected_session_ids == ["0-upper-19:00"]


def test_session_missed_returns_empty_when_id_unknown() -> None:
    plan = _load_plan("ul-base-001")
    delta = from_session_missed(plan, "does-not-exist")
    assert delta.affected_session_ids == []


def test_state_changed_flags_low_sleep_day() -> None:
    plan = _load_plan("ul-base-001")
    state = UserState(
        date="2026-05-26",
        sleep_hours=4.5,
        perceived_fatigue=8,
        missed_last_session=False,
    )

    delta = from_state_changed(plan, state)

    assert delta.trigger_type == "state_changed"
    assert "1-lower-19:00" in delta.affected_session_ids


def test_state_changed_is_noop_when_recovered() -> None:
    plan = _load_plan("ul-base-001")
    state = UserState(
        date="2026-05-26",
        sleep_hours=8.0,
        perceived_fatigue=3,
        missed_last_session=False,
    )

    delta = from_state_changed(plan, state)

    assert delta.affected_session_ids == []


def test_manual_edit_captures_target_and_new_start() -> None:
    plan = _load_plan("fb-base-001")

    delta = from_manual_edit(plan, "2-full-17:30", new_start="08:00")

    assert delta.trigger_type == "manual_edit"
    assert delta.affected_session_ids == ["2-full-17:30"]
    assert delta.payload == {"session_id": "2-full-17:30", "new_start": "08:00"}
