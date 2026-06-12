from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

from app.ai.core.models import GeneratePlanRequest, Plan, ScheduledSession, StrategyStep
from app.ai.core.scoring import score_plan
from app.ai.csp.backtracking import (
    _build_session_types,
    _candidate_starts,
)


@dataclass
class Chromosome:
    genes: list[tuple[int, str]]
    fitness: float = 0.0


def generate_plan_ga(
    req: GeneratePlanRequest,
    *,
    population_size: int = 20,
    generations: int = 40,
    mutation_rate: float = 0.15,
    random_seed: int | None = 42,
) -> Plan:
    start_time = perf_counter()

    rng = random.Random(random_seed)
    session_types = _build_session_types(req.split)
    session_type_map = {s.id: s for s in session_types}
    candidate_starts = _candidate_starts(req.preferences.preferred_time_of_day)

    population = [
        _random_chromosome(req.sessions_per_week, candidate_starts, rng)
        for _ in range(population_size)
    ]

    nodes = 0

    for _ in range(generations):
        for chromosome in population:
            plan = _decode_chromosome(req, chromosome, session_types)
            chromosome.fitness = _fitness(plan, session_type_map)
            nodes += len(chromosome.genes)

        population.sort(key=lambda c: c.fitness, reverse=True)

        next_population = population[:2]

        while len(next_population) < population_size:
            parent_a = _tournament_select(population, rng)
            parent_b = _tournament_select(population, rng)
            child = _crossover(parent_a, parent_b, rng)
            _mutate(child, candidate_starts, mutation_rate, rng)
            next_population.append(child)

        population = next_population

    for chromosome in population:
        plan = _decode_chromosome(req, chromosome, session_types)
        chromosome.fitness = _fitness(plan, session_type_map)

    best = max(population, key=lambda c: c.fitness)
    best_plan = _decode_chromosome(req, best, session_types)
    best_plan.scores = score_plan(
        best_plan,
        constraints=[],
        session_types=session_type_map,
    )

    elapsed_ms = int((perf_counter() - start_time) * 1000)
    best_plan.strategy_trace.append(
        StrategyStep(
            algorithm="genetic_algorithm",
            role="optimize",
            nodes=nodes,
            iterations=generations,
            time_ms=elapsed_ms,
            score_after=best_plan.scores.total,
        )
    )

    return best_plan


def _random_chromosome(
    sessions_per_week: int,
    candidate_starts: list[str],
    rng: random.Random,
) -> Chromosome:
    genes = [
        (rng.randrange(7), rng.choice(candidate_starts))
        for _ in range(sessions_per_week)
    ]
    return Chromosome(genes=genes)


def _decode_chromosome(
    req: GeneratePlanRequest,
    chromosome: Chromosome,
    session_types,
) -> Plan:
    sessions: list[ScheduledSession] = []

    for i, (day, start) in enumerate(chromosome.genes):
        session_type = session_types[i % len(session_types)]
        duration = min(
            session_type.duration_min,
            req.preferences.max_session_duration_min,
        )

        candidate = ScheduledSession(
            id=ScheduledSession.derive_id(day, session_type.id, start),
            session_type_id=session_type.id,
            day=day,
            start=start,
            duration_min=duration,
            locked=False,
        )

        sessions.append(candidate)

    return Plan(
        id=f"ga-plan-{datetime.now(UTC).timestamp()}",
        generated_at=datetime.now(UTC).isoformat(),
        sessions=sessions,
    )


def _fitness(plan: Plan, session_type_map) -> float:
    scores = score_plan(plan, constraints=[], session_types=session_type_map)

    unique_days = len({s.day for s in plan.sessions})
    spread_bonus = float(unique_days)

    conflict_penalty = scores.conflicts * 10.0

    return scores.total + spread_bonus - conflict_penalty


def _tournament_select(
    population: list[Chromosome],
    rng: random.Random,
    k: int = 3,
) -> Chromosome:
    contenders = rng.sample(population, k=min(k, len(population)))
    return max(contenders, key=lambda c: c.fitness)


def _crossover(
    parent_a: Chromosome,
    parent_b: Chromosome,
    rng: random.Random,
) -> Chromosome:
    if len(parent_a.genes) <= 1:
        return Chromosome(genes=parent_a.genes.copy())

    point = rng.randrange(1, len(parent_a.genes))
    genes = parent_a.genes[:point] + parent_b.genes[point:]
    return Chromosome(genes=genes)


def _mutate(
    chromosome: Chromosome,
    candidate_starts: list[str],
    mutation_rate: float,
    rng: random.Random,
) -> None:
    for i, gene in enumerate(chromosome.genes):
        if rng.random() >= mutation_rate:
            continue

        day, start = gene

        if rng.random() < 0.5:
            day = rng.randrange(7)
        else:
            start = rng.choice(candidate_starts)

        chromosome.genes[i] = (day, start)