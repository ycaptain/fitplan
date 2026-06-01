from __future__ import annotations

import random
from typing import Final

from app.ai.core import registry
from app.ai.core.models import (
    Constraint,
    Plan,
    SessionType,
)
from app.ai.core.scoring import count_hard_violations, score_plan
from app.ai.local.neighbourhood import candidate_starts, neighbours

SIDEWAYS_LIMIT: Final[int] = 10
NO_IMPROVE_PATIENCE: Final[int] = 3


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
    starts = candidate_starts(current, constraints)

    best_score = _fitness(current, constraints, origin_days, disturbance_penalty, session_types)
    no_improve = 0
    sideways_used = 0

    for _ in range(max_iter):
        best_neighbour: Plan | None = None
        best_neighbour_score: tuple[int, float, int] | None = None

        candidates = list(neighbours(current, starts))
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
