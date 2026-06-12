"""Genetic algorithm for initial plan generation."""
from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime
from time import perf_counter

from app.ai.core import registry
from app.ai.core.models import (
    Constraint,
    GeneratePlanRequest,
    Plan,
    StrategyStep,
)
from app.ai.core.scheduling import (
    build_candidate,
    build_session_types,
    minutes_of,
    preferred_candidate_starts,
)
from app.ai.core.scoring import score_plan

POP_SIZE = 20
N_GEN = 40
MUTATION_RATE = 0.2
TOURNAMENT_K = 3
ELITE_N = 2


def _build_plan(
    chromosome: list[int],
    session_types: list,
    starts: list[str],
    req: GeneratePlanRequest,
    stype_map: dict,
) -> Plan:
    sessions = []
    day_end: dict[int, int] = {}

    for day, stype in zip(chromosome, session_types, strict=False):
        duration = min(stype.duration_min, req.preferences.max_session_duration_min)
        base = minutes_of(starts[0])
        start_min = max(base, day_end.get(day, base))
        start_min = min(start_min, 22 * 60 - duration)
        start_min = max(start_min, 6 * 60)
        h, m = divmod(start_min, 60)
        start = f"{h:02d}:{m:02d}"

        sessions.append(build_candidate(stype, day, start, duration))
        day_end[day] = start_min + duration

    plan = Plan(
        id=f"ga-plan-{uuid.uuid4().hex[:8]}",
        generated_at=datetime.now(UTC).isoformat(),
        sessions=sessions,
    )
    plan.scores = score_plan(plan, constraints=[], session_types=stype_map)
    return plan


def _fitness(plan: Plan, constraints: list[Constraint], stype_map: dict) -> float:
    return score_plan(plan, constraints=constraints, session_types=stype_map).total


def _tournament(fitnesses: list[float], rng: random.Random) -> int:
    idx = rng.sample(range(len(fitnesses)), min(TOURNAMENT_K, len(fitnesses)))
    return max(idx, key=lambda i: fitnesses[i])


def _crossover(
    a: list[int], b: list[int], rng: random.Random
) -> tuple[list[int], list[int]]:
    if len(a) <= 1:
        return a[:], b[:]
    point = rng.randint(1, len(a) - 1)
    return a[:point] + b[point:], b[:point] + a[point:]


def _mutate(chromosome: list[int], rng: random.Random) -> list[int]:
    c = chromosome[:]
    i = rng.randrange(len(c))
    c[i] = rng.randint(0, 6)
    return c


@registry.register(registry.AlgorithmKey.GA_GENERATE)
def ga_generate(
    req: GeneratePlanRequest,
    constraints: list[Constraint] | None = None,
    **kwargs,
) -> Plan:
    t0 = perf_counter()
    seed = kwargs.get("random_seed")
    rng = random.Random(seed)
    constraints = constraints or []

    session_types = build_session_types(req.split)
    stype_map = {s.id: s for s in session_types}
    starts = preferred_candidate_starts(req.preferences.preferred_time_of_day)
    n = req.sessions_per_week
    stypes = [session_types[i % len(session_types)] for i in range(n)]

    pop = [[rng.randint(0, 6) for _ in range(n)] for _ in range(POP_SIZE)]

    best_plan: Plan | None = None
    best_fit = float("-inf")

    for _ in range(N_GEN):
        plans = [_build_plan(c, stypes, starts, req, stype_map) for c in pop]
        fits = [_fitness(p, constraints, stype_map) for p in plans]

        for p, f in zip(plans, fits, strict=False):
            if f > best_fit:
                best_fit = f
                best_plan = p

        order = sorted(range(POP_SIZE), key=lambda i: fits[i], reverse=True)
        new_pop = [pop[i][:] for i in order[:ELITE_N]]

        while len(new_pop) < POP_SIZE:
            p1 = pop[_tournament(fits, rng)]
            p2 = pop[_tournament(fits, rng)]
            c1, c2 = _crossover(p1, p2, rng)
            if rng.random() < MUTATION_RATE:
                c1 = _mutate(c1, rng)
            if rng.random() < MUTATION_RATE:
                c2 = _mutate(c2, rng)
            new_pop.append(c1)
            if len(new_pop) < POP_SIZE:
                new_pop.append(c2)

        pop = new_pop

    best_plan.scores = score_plan(
        best_plan, constraints=constraints, session_types=stype_map
    )

    elapsed_ms = int((perf_counter() - t0) * 1000)
    best_plan.strategy_trace.append(
        StrategyStep(
            algorithm=registry.AlgorithmKey.GA_GENERATE,
            role="optimize",
            nodes=POP_SIZE * N_GEN,
            iterations=N_GEN,
            time_ms=elapsed_ms,
            score_after=best_plan.scores.total,
        )
    )

    return best_plan
