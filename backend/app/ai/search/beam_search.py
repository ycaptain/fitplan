from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

from app.ai.core.models import GeneratePlanRequest, Plan, ScheduledSession, StrategyStep
from app.ai.core.scheduling import (
    build_candidate,
    build_session_types,
    day_order,
    is_valid_candidate,
    preferred_candidate_starts,
)
from app.ai.core.scoring import score_plan


@dataclass
class BeamState:
    sessions: list[ScheduledSession]
    nodes: int = 0


def generate_plan_beam(req: GeneratePlanRequest, beam_width: int = 3) -> Plan:
    start_time = perf_counter()

    session_types = build_session_types(req.split)
    session_type_map = {s.id: s for s in session_types}
    candidate_starts = preferred_candidate_starts(req.preferences.preferred_time_of_day)
    ordered_days = day_order(req.sessions_per_week)

    beam: list[BeamState] = [BeamState(sessions=[])]
    total_nodes = 0

    for i in range(req.sessions_per_week):
        session_type = session_types[i % len(session_types)]
        candidates: list[BeamState] = []

        rotated_days = ordered_days[i:] + ordered_days[:i]

        for state in beam:
            for day in rotated_days:
                for start in candidate_starts:
                    total_nodes += 1

                    duration = min(
                        session_type.duration_min,
                        req.preferences.max_session_duration_min,
                    )

                    candidate = build_candidate(session_type, day, start, duration)

                    if not is_valid_candidate(
                        candidate=candidate,
                        existing=state.sessions,
                        fixed_events=req.fixed_events,
                        session_types=session_type_map,
                    ):
                        continue

                    new_sessions = [*state.sessions, candidate]
                    candidates.append(BeamState(sessions=new_sessions, nodes=total_nodes))

        if not candidates:
            break

        candidates.sort(
            key=lambda state: _state_score(state, req, session_type_map),
            reverse=True,
        )
        beam = candidates[:beam_width]

    best = beam[0] if beam else BeamState(sessions=[])

    plan = Plan(
        id=f"beam-plan-{datetime.now(UTC).timestamp()}",
        generated_at=datetime.now(UTC).isoformat(),
        sessions=best.sessions,
    )

    plan.scores = score_plan(plan, constraints=[], session_types=session_type_map)

    elapsed_ms = int((perf_counter() - start_time) * 1000)
    plan.strategy_trace.append(
        StrategyStep(
            algorithm="beam_search",
            role="optimize",
            nodes=total_nodes,
            iterations=req.sessions_per_week,
            time_ms=elapsed_ms,
            score_after=plan.scores.total,
        )
    )

    return plan


def _state_score(
    state: BeamState,
    req: GeneratePlanRequest,
    session_type_map,
) -> float:
    temp_plan = Plan(
        id="temp",
        generated_at=datetime.now(UTC).isoformat(),
        sessions=state.sessions,
    )

    scores = score_plan(temp_plan, constraints=[], session_types=session_type_map)

    unique_days = len({s.day for s in state.sessions})
    completed_sessions = len(state.sessions)

    return scores.total + unique_days + completed_sessions
