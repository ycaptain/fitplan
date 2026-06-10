from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

from app.ai.core.models import (
    FixedEvent,
    GeneratePlanRequest,
    Plan,
    ScheduledSession,
    SessionType,
    StrategyStep,
)
from app.ai.core.scoring import score_plan


def generate_greedy_baseline(req: GeneratePlanRequest) -> Plan:
    start_time = perf_counter()

    session_types = _build_session_types(req.split)
    candidate_starts = _candidate_starts(req.preferences.preferred_time_of_day)

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

                candidate = ScheduledSession(
                    id=ScheduledSession.derive_id(day, session_type.id, start),
                    session_type_id=session_type.id,
                    day=day,
                    start=start,
                    duration_min=duration,
                    locked=False,
                )

                if _is_valid_candidate(candidate, sessions, req.fixed_events):
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

    session_type_map = {s.id: s for s in session_types}
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


def _build_session_types(split: str) -> list[SessionType]:
    if split == "ppl":
        return [
            SessionType(
                id="push",
                name="Push",
                muscle_groups=["chest", "shoulders", "triceps"],
                intensity=0.7,
                duration_min=60,
                recovery_hours=48,
            ),
            SessionType(
                id="pull",
                name="Pull",
                muscle_groups=["back", "biceps"],
                intensity=0.7,
                duration_min=60,
                recovery_hours=48,
            ),
            SessionType(
                id="legs",
                name="Legs",
                muscle_groups=["quads", "hamstrings", "glutes"],
                intensity=0.8,
                duration_min=70,
                recovery_hours=72,
            ),
        ]

    if split == "upper_lower":
        return [
            SessionType(
                id="upper",
                name="Upper",
                muscle_groups=["chest", "back", "shoulders", "arms"],
                intensity=0.7,
                duration_min=60,
                recovery_hours=48,
            ),
            SessionType(
                id="lower",
                name="Lower",
                muscle_groups=["quads", "hamstrings", "glutes"],
                intensity=0.8,
                duration_min=70,
                recovery_hours=72,
            ),
        ]

    return [
        SessionType(
            id="full_body",
            name="Full Body",
            muscle_groups=["chest", "back", "legs", "shoulders", "arms"],
            intensity=0.65,
            duration_min=60,
            recovery_hours=48,
        )
    ]


def _candidate_starts(preferred_time_of_day: str) -> list[str]:
    if preferred_time_of_day == "morning":
        return ["07:00", "08:00", "09:00"]

    if preferred_time_of_day == "evening":
        return ["17:00", "18:00", "19:00"]

    return ["07:00", "08:00", "12:00", "17:00", "18:00", "19:00"]


def _is_valid_candidate(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
    fixed_events: list[FixedEvent],
) -> bool:
    if _overlaps_fixed_event(candidate, fixed_events):
        return False

    if _overlaps_existing_session(candidate, existing):
        return False

    return True


def _overlaps_fixed_event(
    session: ScheduledSession,
    fixed_events: list[FixedEvent],
) -> bool:
    s_start = _minutes(session.start)
    s_end = s_start + session.duration_min

    for event in fixed_events:
        if event.day_of_week != session.day:
            continue

        e_start = _minutes(event.start)
        e_end = _minutes(event.end)

        if s_start < e_end and e_start < s_end:
            return True

    return False


def _overlaps_existing_session(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
) -> bool:
    c_start = _minutes(candidate.start)
    c_end = c_start + candidate.duration_min

    for session in existing:
        if session.day != candidate.day:
            continue

        s_start = _minutes(session.start)
        s_end = s_start + session.duration_min

        if c_start < s_end and s_start < c_end:
            return True

    return False


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)