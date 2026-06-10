from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

from app.ai.core import registry
from app.ai.core.models import (
    Constraint,
    GeneratePlanRequest,
    Plan,
    ScheduledSession,
    StrategyStep,
)
from app.ai.core.scheduling import (
    build_candidate,
    build_session_types,
    is_valid_candidate,
    preferred_candidate_starts,
)
from app.ai.core.scoring import score_plan


@registry.register(registry.AlgorithmKey.GREEDY_BASELINE)
def generate_greedy_baseline(
    req: GeneratePlanRequest,
    constraints: list[Constraint] | None = None,
) -> Plan:
    start_time = perf_counter()

    session_types = build_session_types(req.split)
    session_type_map = {s.id: s for s in session_types}
    candidate_starts = preferred_candidate_starts(req.preferences.preferred_time_of_day)

    sessions: list[ScheduledSession] = []
    nodes = 0

    for i in range(req.sessions_per_week):
        session_type = session_types[i % len(session_types)]
        placed = False

        for day in range(7):
            for start in candidate_starts:
                nodes += 1

                duration = min(
                    session_type.duration_min,
                    req.preferences.max_session_duration_min,
                )
                candidate = build_candidate(session_type, day, start, duration)

                # Greedy only avoids outright overlaps; it ignores recovery and
                # day-spacing on purpose so the smarter planners have a baseline
                # to beat.
                if is_valid_candidate(
                    candidate=candidate,
                    existing=sessions,
                    fixed_events=req.fixed_events,
                    session_types=session_type_map,
                    relaxed=True,
                ):
                    sessions.append(candidate)
                    placed = True
                    break

            if placed:
                break

    plan = Plan(
        id=f"greedy-plan-{datetime.now(UTC).timestamp()}",
        generated_at=datetime.now(UTC).isoformat(),
        sessions=sessions,
    )

    plan.scores = score_plan(plan, constraints=[], session_types=session_type_map)

    elapsed_ms = int((perf_counter() - start_time) * 1000)
    plan.strategy_trace.append(
        StrategyStep(
            algorithm="greedy_baseline",
            role="feasibility",
            nodes=nodes,
            iterations=0,
            time_ms=elapsed_ms,
            score_after=plan.scores.total,
        )
    )

    return plan
