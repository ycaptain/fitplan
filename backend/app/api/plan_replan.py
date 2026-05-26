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

router = APIRouter()

_FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "sample_plans.json"
)


@router.post("/plan/replan", response_model=ReplanResult)
async def replan(req: ReplanRequest) -> ReplanResult:
    plan = _load_plan(req.plan_id)
    delta, constraints = _build_delta(plan, req)
    orchestrate = registry.get(registry.AlgorithmKey.ORCHESTRATE_REPLAN)
    return orchestrate(plan, delta, constraints, req.mode)


def _load_plan(plan_id: str) -> Plan:
    data = json.loads(_FIXTURES.read_text())
    for raw in data["plans"]:
        if raw["id"] == plan_id:
            return Plan.model_validate(raw)
    raise HTTPException(status_code=404, detail=f"plan '{plan_id}' not found")


def _build_delta(
    plan: Plan, req: ReplanRequest
) -> tuple[PlanDelta, list[Constraint]]:
    if req.trigger_type == "fixed_event_added":
        event = FixedEvent.model_validate(req.payload)
        return (
            from_fixed_event_added(plan, event),
            [_fixed_event_constraint(event)],
        )
    if req.trigger_type == "session_missed":
        return from_session_missed(plan, req.payload["session_id"]), []
    if req.trigger_type == "state_changed":
        return from_state_changed(plan, UserState.model_validate(req.payload)), []
    return (
        from_manual_edit(plan, req.payload["session_id"], req.payload["new_start"]),
        [],
    )


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
