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
    day_order,
    goal_adjusted_duration,
    is_valid_candidate,
    preferred_candidate_starts,
    same_day_gap,
)
from app.ai.core.scoring import score_plan


@registry.register(registry.AlgorithmKey.CSP_BT_FC)
def generate_initial_plan(
    req: GeneratePlanRequest,
    constraints: list[Constraint] | None = None,
) -> Plan:
    start_time = perf_counter()

    session_types = build_session_types(req.split)
    candidate_starts = preferred_candidate_starts(req.preferences.preferred_time_of_day)

    sessions: list[ScheduledSession] = []
    nodes = 0

    ordered_days = day_order(req.sessions_per_week)

    type_map = {s.id: s for s in session_types}

    for i in range(req.sessions_per_week):
        session_type = session_types[i % len(session_types)]
        rotated_days = ordered_days[i:] + ordered_days[:i]
        duration = goal_adjusted_duration(
            session_type=session_type,
            goal=req.goal,
            max_duration=req.preferences.max_session_duration_min,
        )

        placed = False
        for day in rotated_days:
            if any(s.day == day for s in sessions):
                continue
            for start in candidate_starts:
                nodes += 1
                candidate = build_candidate(session_type, day, start, duration)
                if is_valid_candidate(
                    candidate=candidate,
                    existing=sessions,
                    fixed_events=req.fixed_events,
                    session_types=type_map,
                ):
                    sessions.append(candidate)
                    placed = True
                    break
            if placed:
                break

        if placed:
            continue

        best_candidate: ScheduledSession | None = None
        best_key: tuple[int, int] | None = None
        for day in rotated_days:
            day_load = sum(1 for s in sessions if s.day == day)
            for start in candidate_starts:
                nodes += 1
                candidate = build_candidate(session_type, day, start, duration)
                if not is_valid_candidate(
                    candidate=candidate,
                    existing=sessions,
                    fixed_events=req.fixed_events,
                    session_types=type_map,
                    relaxed=True,
                ):
                    continue
                gap = same_day_gap(candidate, sessions)
                key = (-day_load, gap)
                if best_key is None or key > best_key:
                    best_candidate = candidate
                    best_key = key

        if best_candidate is not None:
            sessions.append(best_candidate)

    plan = Plan(
        id=f"plan-{datetime.now(UTC).timestamp()}",
        generated_at=datetime.now(UTC).isoformat(),
        sessions=sessions,
    )

    plan.scores = score_plan(
        plan,
        constraints=[],
        session_types={s.id: s for s in session_types},
    )

    elapsed_ms = int((perf_counter() - start_time) * 1000)
    plan.strategy_trace.append(
        StrategyStep(
            algorithm="csp_backtracking_forward_checking_mvp",
            role="feasibility",
            nodes=nodes,
            iterations=0,
            time_ms=elapsed_ms,
            score_after=plan.scores.total,
        )
    )

    return plan
