from __future__ import annotations

import math
import random
from typing import Final

from app.ai.core import registry
from app.ai.core.models import (
    Constraint,
    Plan,
    SessionType,
)
from app.ai.core.scoring import count_hard_violations, score_plan
from app.ai.local.neighbourhood import candidate_starts, random_neighbour

# large enough that fixing a hard violation always beats any soft-score gain
HARD_PENALTY: Final[float] = 100.0
MIN_TEMPERATURE: Final[float] = 1e-4
MAX_EXPONENT: Final[float] = 50.0


@registry.register(registry.AlgorithmKey.SIMULATED_ANNEALING)
def simulated_annealing(
    plan: Plan,
    constraints: list[Constraint],
    *,
    max_iter: int = 500,
    initial_temp: float = 1.0,
    cooling_rate: float = 0.95,
    disturbance_penalty: float = 0.0,
    random_seed: int | None = None,
    session_types: dict[str, SessionType] | None = None,
) -> Plan:
    origin_days = {s.id: s.day for s in plan.sessions}
    rng = random.Random(random_seed)
    current = plan.model_copy(deep=True)
    starts = candidate_starts(current, constraints)

    current_energy = _energy(
        current, constraints, origin_days, disturbance_penalty, session_types
    )
    best = current
    best_energy = current_energy

    temperature = initial_temp
    for _ in range(max_iter):
        if temperature < MIN_TEMPERATURE:
            break

        candidate = random_neighbour(current, starts, rng)
        if candidate is None:
            break

        cand_energy = _energy(
            candidate, constraints, origin_days, disturbance_penalty, session_types
        )
        if _accept(cand_energy - current_energy, temperature, rng):
            current = candidate
            current_energy = cand_energy
            if cand_energy < best_energy:
                best = candidate
                best_energy = cand_energy

        temperature *= cooling_rate

    out = best.model_copy(deep=True)
    out.scores = score_plan(out, constraints, session_types)
    return out


def _accept(delta: float, temperature: float, rng: random.Random) -> bool:
    if delta <= 0:
        return True
    exponent = delta / temperature
    if exponent > MAX_EXPONENT:
        return False
    return rng.random() < math.exp(-exponent)


def _energy(
    plan: Plan,
    constraints: list[Constraint],
    origin_days: dict[str, int],
    disturbance_penalty: float,
    session_types: dict[str, SessionType] | None,
) -> float:
    hard = count_hard_violations(plan, constraints, session_types)
    base = score_plan(plan, constraints, session_types).total
    moves = sum(
        1
        for s in plan.sessions
        if s.id in origin_days and origin_days[s.id] != s.day
    )
    return HARD_PENALTY * hard - base + disturbance_penalty * moves
