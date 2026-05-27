from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.ai.adaptability.triggers import (
    from_fixed_event_added,
    from_manual_edit,
    from_session_missed,
    from_state_changed,
)
from app.ai.core import registry
from app.ai.core.constraints import ConstraintType
from app.ai.core.models import (
    Constraint,
    FixedEvent,
    Plan,
    PlanDelta,
    ReplanRequest,
    ReplanResult,
    UserState,
)
from app.api import plan_store

router = APIRouter()

_FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "sample_plans.json"
)


@router.post("/plan/replan", response_model=ReplanResult)
async def replan(req: ReplanRequest) -> ReplanResult:
    plan, events = _load_plan_and_events(req.plan_id)
    delta, constraints, next_events = _build_delta(plan, req, events)
    orchestrate = registry.get(registry.AlgorithmKey.ORCHESTRATE_REPLAN)
    result: ReplanResult = orchestrate(plan, delta, constraints, req.mode)
    plan_store.put(result.plan, next_events)
    return result


def _load_plan_and_events(plan_id: str) -> tuple[Plan, list[FixedEvent]]:
    stored = plan_store.get(plan_id)
    if stored is not None:
        return stored.plan, list(stored.events)

    data = json.loads(_FIXTURES.read_text())
    for raw in data["plans"]:
        if raw["id"] == plan_id:
            return Plan.model_validate(raw), []

    raise HTTPException(status_code=404, detail=f"plan '{plan_id}' not found")


def _build_delta(
    plan: Plan,
    req: ReplanRequest,
    existing_events: list[FixedEvent],
) -> tuple[PlanDelta, list[Constraint], list[FixedEvent]]:
    if req.trigger_type == "fixed_event_added":
        event = FixedEvent.model_validate(req.payload)
        all_events = [*existing_events, event]
        return (
            from_fixed_event_added(plan, event),
            [_fixed_event_constraint(e) for e in all_events],
            all_events,
        )

    constraints = [_fixed_event_constraint(e) for e in existing_events]

    if req.trigger_type == "session_missed":
        delta = from_session_missed(plan, req.payload["session_id"])
    elif req.trigger_type == "state_changed":
        delta = from_state_changed(plan, UserState.model_validate(req.payload))
    else:
        delta = from_manual_edit(
            plan, req.payload["session_id"], req.payload["new_start"]
        )

    return delta, constraints, list(existing_events)


def _fixed_event_constraint(event: FixedEvent) -> Constraint:
    return Constraint(
        id=f"evt-{event.id}",
        kind="hard",
        type=ConstraintType.FIXED_EVENT,
        params={
            "day_of_week": event.day_of_week,
            "start": event.start,
            "end": event.end,
        },
    )
