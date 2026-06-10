"""Shared scheduling helpers for the initial-plan generators.

Single source of truth for the session-type catalogue, candidate start
slots, day ordering and candidate validity, so CSP backtracking, greedy and
beam search cannot drift apart.
"""

from __future__ import annotations

from app.ai.core.models import (
    FixedEvent,
    ScheduledSession,
    SessionType,
)


def minutes_of(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def spans_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def build_session_types(split: str) -> list[SessionType]:
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


def preferred_candidate_starts(preferred_time_of_day: str) -> list[str]:
    if preferred_time_of_day == "morning":
        return ["07:00", "08:00", "09:00"]

    if preferred_time_of_day == "evening":
        return ["17:00", "18:00", "19:00"]

    return ["07:00", "08:00", "12:00", "17:00", "18:00", "19:00"]


def day_order(sessions_per_week: int) -> list[int]:
    if sessions_per_week <= 3:
        return [0, 2, 4, 1, 3, 5, 6]

    if sessions_per_week == 4:
        return [0, 2, 4, 6, 1, 3, 5]

    if sessions_per_week == 5:
        return [0, 1, 3, 5, 6, 2, 4]

    return [0, 1, 2, 3, 4, 5, 6]


def goal_adjusted_duration(
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


def build_candidate(
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


def is_valid_candidate(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
    fixed_events: list[FixedEvent],
    session_types: dict[str, SessionType],
    relaxed: bool = False,
) -> bool:
    """Overlap checks always apply; one-session-per-day and recovery spacing
    are skipped in relaxed mode (used as a fallback in narrow calendars)."""
    if overlaps_fixed_event(candidate, fixed_events):
        return False

    if overlaps_existing_session(candidate, existing):
        return False

    if relaxed:
        return True

    if any(s.day == candidate.day for s in existing):
        return False

    if not satisfies_recovery(candidate, existing, session_types):
        return False

    return True


def overlaps_fixed_event(
    session: ScheduledSession,
    fixed_events: list[FixedEvent],
) -> bool:
    s_start = minutes_of(session.start)
    s_end = s_start + session.duration_min

    for event in fixed_events:
        if event.day_of_week != session.day:
            continue
        if spans_overlap(s_start, s_end, minutes_of(event.start), minutes_of(event.end)):
            return True

    return False


def overlaps_existing_session(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
) -> bool:
    c_start = minutes_of(candidate.start)
    c_end = c_start + candidate.duration_min

    for session in existing:
        if session.day != candidate.day:
            continue
        s_start = minutes_of(session.start)
        if spans_overlap(c_start, c_end, s_start, s_start + session.duration_min):
            return True

    return False


def satisfies_recovery(
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


def same_day_gap(
    candidate: ScheduledSession,
    existing: list[ScheduledSession],
) -> int:
    same_day = [s for s in existing if s.day == candidate.day]
    if not same_day:
        return 24 * 60

    c_start = minutes_of(candidate.start)
    c_end = c_start + candidate.duration_min
    gaps: list[int] = []
    for s in same_day:
        s_start = minutes_of(s.start)
        s_end = s_start + s.duration_min
        if c_start >= s_end:
            gaps.append(c_start - s_end)
        elif s_start >= c_end:
            gaps.append(s_start - c_end)
        else:
            return -1
    return min(gaps)
