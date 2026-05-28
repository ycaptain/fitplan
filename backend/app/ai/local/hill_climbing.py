from __future__ import annotations

import random
from typing import Final

from app.ai.core import registry
from app.ai.core.constraints import ConstraintType
from app.ai.core.models import (
    Constraint,
    Plan,
    ScheduledSession,
    SessionType,
)
from app.ai.core.scoring import count_hard_violations, score_plan

DAYS_IN_WEEK: Final[int] = 7
SIDEWAYS_LIMIT: Final[int] = 10
NO_IMPROVE_PATIENCE: Final[int] = 3
EARLIEST_START_MINUTES: Final[int] = 6 * 60   # 06:00
LATEST_END_MINUTES: Final[int] = 22 * 60      # 22:00, aligned with Calendar UI
FALLBACK_STARTS: Final[tuple[str, ...]] = (
    "07:00",
    "12:00",
    "17:00",
    "18:00",
    "19:00",
)


@registry.register(registry.AlgorithmKey.HILL_CLIMBING)
def hill_climbing(
    plan: Plan,
    constraints: list[Constraint],
    *,
    max_iter: int = 100,
    disturbance_penalty: float = 0.0,
    random_seed: int | None = None,
    session_types: dict[str, SessionType] | None = None,
) -> Plan:
    origin_days = {s.id: s.day for s in plan.sessions}
    rng = random.Random(random_seed)
    current = plan.model_copy(deep=True)
    candidate_starts = _candidate_starts(current, constraints)

    best_score = _fitness(current, constraints, origin_days, disturbance_penalty, session_types)
    no_improve = 0
    sideways_used = 0

    for _ in range(max_iter):
        best_neighbour: Plan | None = None
        best_neighbour_score: tuple[int, float, int] | None = None

        candidates = list(_neighbours(current, candidate_starts))
        rng.shuffle(candidates)

        for candidate in candidates:
            cand_score = _fitness(
                candidate, constraints, origin_days, disturbance_penalty, session_types
            )
            if best_neighbour_score is None or cand_score > best_neighbour_score:
                best_neighbour = candidate
                best_neighbour_score = cand_score

        if best_neighbour is None or best_neighbour_score is None:
            break

        if best_neighbour_score > best_score:
            current = best_neighbour
            best_score = best_neighbour_score
            no_improve = 0
            sideways_used = 0
        elif best_neighbour_score == best_score and sideways_used < SIDEWAYS_LIMIT:
            current = best_neighbour
            sideways_used += 1
            no_improve += 1
        else:
            no_improve += 1

        if no_improve >= NO_IMPROVE_PATIENCE:
            break

    current.scores = score_plan(current, constraints, session_types)
    return current


def _fitness(
    plan: Plan,
    constraints: list[Constraint],
    origin_days: dict[str, int],
    disturbance_penalty: float,
    session_types: dict[str, SessionType] | None,
) -> tuple[int, float, int]:
    hard = count_hard_violations(plan, constraints, session_types)
    base = score_plan(plan, constraints, session_types).total
    moves = _moves_from_origin(plan, origin_days)
    if disturbance_penalty:
        base -= disturbance_penalty * moves
    return (-hard, base, -moves)


def _moves_from_origin(plan: Plan, origin_days: dict[str, int]) -> int:
    return sum(
        1
        for s in plan.sessions
        if s.id in origin_days and origin_days[s.id] != s.day
    )


def _neighbours(plan: Plan, candidate_starts: list[str]):
    for idx, session in enumerate(plan.sessions):
        if session.locked:
            continue
        for day in range(DAYS_IN_WEEK):
            for start in candidate_starts:
                if day == session.day and start == session.start:
                    continue
                if _minutes(start) + session.duration_min > LATEST_END_MINUTES:
                    continue
                yield _move_session(plan, idx, day, start)


def _move_session(plan: Plan, idx: int, new_day: int, new_start: str) -> Plan:
    neighbour = plan.model_copy(deep=True)
    original: ScheduledSession = neighbour.sessions[idx]
    neighbour.sessions[idx] = original.model_copy(
        update={"day": new_day, "start": new_start}
    )
    return neighbour


def _candidate_starts(plan: Plan, constraints: list[Constraint]) -> list[str]:
    starts: set[str] = {s.start for s in plan.sessions}
    for c in constraints:
        if c.type != ConstraintType.FIXED_EVENT:
            continue
        end = c.params.get("end")
        if isinstance(end, str):
            starts.add(end)
    starts.update(FALLBACK_STARTS)
    return sorted(
        (s for s in starts if _minutes(s) >= EARLIEST_START_MINUTES),
        key=_minutes,
    )


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)
