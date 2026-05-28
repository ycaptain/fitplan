from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.ai.adaptability.triggers import (
    from_manual_edit,
    from_session_missed,
    from_state_changed,
    sessions_overlapping_events,
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
        new_event = FixedEvent.model_validate(req.payload)
        all_events = _reconcile_events(req.fixed_events, existing_events, new_event)
        # Mark every session overlapping ANY event (new or pre-existing) as
        # affected so the replanner can move all conflicting sessions at once.
        affected = sessions_overlapping_events(plan, all_events)
        delta = PlanDelta(
            trigger_type="fixed_event_added",
            payload=new_event.model_dump(),
            affected_session_ids=affected,
        )
        return (
            delta,
            [_fixed_event_constraint(e) for e in all_events],
            all_events,
        )

    canonical_events = (
        list(req.fixed_events) if req.fixed_events is not None else list(existing_events)
    )
    constraints = [_fixed_event_constraint(e) for e in canonical_events]

    if req.trigger_type == "session_missed":
        delta = from_session_missed(plan, req.payload["session_id"])
    elif req.trigger_type == "state_changed":
        delta = from_state_changed(plan, UserState.model_validate(req.payload))
    else:
        delta = from_manual_edit(
            plan, req.payload["session_id"], req.payload["new_start"]
        )

    return delta, constraints, canonical_events


def _reconcile_events(
    client_events: list[FixedEvent] | None,
    server_events: list[FixedEvent],
    new_event: FixedEvent,
) -> list[FixedEvent]:
    """Merge client-provided events with the new event, defaulting to the
    server-cached list when the client did not send one."""
    if client_events is None:
        return [*server_events, new_event]
    # Client is authoritative; ensure the new event is present (idempotent).
    by_id: dict[str, FixedEvent] = {e.id: e for e in client_events}
    by_id[new_event.id] = new_event
    return list(by_id.values())


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
