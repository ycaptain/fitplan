from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.core.models import FixedEvent, Plan


@dataclass
class StoredPlan:
    plan: Plan
    events: list[FixedEvent] = field(default_factory=list)


_STORE: dict[str, StoredPlan] = {}


def put(plan: Plan, events: list[FixedEvent]) -> None:
    _STORE[plan.id] = StoredPlan(plan=plan, events=list(events))


def get(plan_id: str) -> StoredPlan | None:
    return _STORE.get(plan_id)


def reset() -> None:
    _STORE.clear()
