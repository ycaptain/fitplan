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


def generate_initial_plan(req: GeneratePlanRequest) -> Plan:
    start_time = perf_counter()

    session_types = _build_session_types(req.split)
    candidate_starts = _candidate_starts(req.preferences.preferred_time_of_day)

    sessions: list[ScheduledSession] = []
    nodes = 0

    day_order = _day_order(req.sessions_per_week)

    type_map = {s.id: s for s in session_types}

    for i in range(req.sessions_per_week):
        session_type = session_types[i % len(session_types)]
        rotated_days = day_order[i:] + day_order[:i]
        duration = _goal_adjusted_duration(
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
                candidate = _build_candidate(session_type, day, start, duration)
                if _is_valid_candidate(
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
                candidate = _build_candidate(session_type, day, start, duration)
                if not _is_valid_candidate(
                    candidate=candidate,
                    existing=sessions,
                    fixed_events=req.fixed_events,
                    session_types=type_map,
                    relaxed=True,
                ):
                    continue
                gap = _same_day_gap(candidate, sessions)
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


def _build_candidate(
    session_type: SessionType,
    day: int,
    start: str,
    duration: int,
) -> ScheduledSession:
    return ScheduledSession(
        id=ScheduledSession.derive_id(day, session_type.id, start),
        session_type_id=session_type.id,
        day=day,
        start=start,
        duration_min=duration,
        locked=False,
    )


def _is_valid_candidate(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
    fixed_events: list[FixedEvent],
    session_types: dict[str, SessionType],
    relaxed: bool = False,
) -> bool:
    if _overlaps_fixed_event(candidate, fixed_events):
        return False

    if _overlaps_existing_session(candidate, existing):
        return False

    if relaxed:
        return True

    if any(s.day == candidate.day for s in existing):
        return False

    if not _satisfies_recovery(candidate, existing, session_types):
        return False

    return True


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


def _same_day_gap(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
) -> int:
    same_day = [s for s in existing if s.day == candidate.day]
    if not same_day:
        return 24 * 60

    c_start = _minutes(candidate.start)
    c_end = c_start + candidate.duration_min
    gaps: list[int] = []
    for s in same_day:
        s_start = _minutes(s.start)
        s_end = s_start + s.duration_min
        if c_start >= s_end:
            gaps.append(c_start - s_end)
        elif s_start >= c_end:
            gaps.append(s_start - c_end)
        else:
            return -1
    return min(gaps)


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


def _satisfies_recovery(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
    session_types: dict[str, SessionType],
) -> bool:
    candidate_type = session_types[candidate.session_type_id]

    for session in existing:
        existing_type = session_types[session.session_type_id]

        shared_muscles = set(candidate_type.muscle_groups) & set(
            existing_type.muscle_groups
        )

        if not shared_muscles:
            continue

        gap_hours = abs(candidate.day - session.day) * 24
        required_hours = max(
            candidate_type.recovery_hours,
            existing_type.recovery_hours,
        )

        if gap_hours < required_hours:
            return False

    return True


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)

def _day_order(sessions_per_week: int) -> list[int]:
    if sessions_per_week <= 3:
        return [0, 2, 4, 1, 3, 5, 6]

    if sessions_per_week == 4:
        return [0, 2, 4, 6, 1, 3, 5]

    if sessions_per_week == 5:
        return [0, 1, 3, 5, 6, 2, 4]

    return [0, 1, 2, 3, 4, 5, 6]

def _goal_adjusted_duration(
    session_type: SessionType,
    goal: str,
    max_duration: int,
) -> int:
    base = session_type.duration_min

    if goal == "bulk":
        adjusted = base + 10
    elif goal == "cut":
        adjusted = base - 10
    else:
        adjusted = base

    adjusted = max(30, adjusted)
    return min(adjusted, max_duration)