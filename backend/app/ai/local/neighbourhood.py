from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from app.ai.core.constraints import ConstraintType
from app.ai.core.models import Constraint, Plan, ScheduledSession

DAYS_IN_WEEK: Final[int] = 7
EARLIEST_START_MINUTES: Final[int] = 6 * 60   # 06:00
LATEST_END_MINUTES: Final[int] = 22 * 60      # 22:00, aligned with Calendar UI
FALLBACK_STARTS: Final[tuple[str, ...]] = (
    "07:00",
    "12:00",
    "17:00",
    "18:00",
    "19:00",
)


def minutes_of(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def candidate_starts(plan: Plan, constraints: list[Constraint]) -> list[str]:
    starts: set[str] = {s.start for s in plan.sessions}
    for c in constraints:
        if c.type != ConstraintType.FIXED_EVENT:
            continue
        end = c.params.get("end")
        if isinstance(end, str):
            starts.add(end)
    starts.update(FALLBACK_STARTS)
    return sorted(
        (s for s in starts if minutes_of(s) >= EARLIEST_START_MINUTES),
        key=minutes_of,
    )


def neighbours(plan: Plan, starts: list[str]) -> Iterator[Plan]:
    for idx, session in enumerate(plan.sessions):
        if session.locked:
            continue
        for day in range(DAYS_IN_WEEK):
            for start in starts:
                if day == session.day and start == session.start:
                    continue
                if minutes_of(start) + session.duration_min > LATEST_END_MINUTES:
                    continue
                yield move_session(plan, idx, day, start)


def random_neighbour(plan: Plan, starts: list[str], rng) -> Plan | None:
    movable = [i for i, s in enumerate(plan.sessions) if not s.locked]
    if not movable:
        return None
    for _ in range(32):
        idx = rng.choice(movable)
        session = plan.sessions[idx]
        day = rng.randrange(DAYS_IN_WEEK)
        start = rng.choice(starts)
        if day == session.day and start == session.start:
            continue
        if minutes_of(start) + session.duration_min > LATEST_END_MINUTES:
            continue
        return move_session(plan, idx, day, start)
    return None


def move_session(plan: Plan, idx: int, new_day: int, new_start: str) -> Plan:
    neighbour = plan.model_copy(deep=True)
    original: ScheduledSession = neighbour.sessions[idx]
    neighbour.sessions[idx] = original.model_copy(
        update={"day": new_day, "start": new_start}
    )
    return neighbour
