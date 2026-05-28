from __future__ import annotations

from typing import Final

from app.ai.core.constraints import ConstraintType
from app.ai.core.models import (
    Constraint,
    Plan,
    ScheduledSession,
    Scores,
    SessionType,
)

CONFLICT_PENALTY: Final[float] = 5.0
OVERLOAD_PENALTY: Final[float] = 2.0
RECOVERY_REWARD: Final[float] = 1.0
RECOVERY_VIOLATION: Final[float] = -1.0


def score_plan(
    plan: Plan,
    constraints: list[Constraint],
    session_types: dict[str, SessionType] | None = None,
) -> Scores:
    conflicts = _count_conflicts(plan.sessions)
    overload = _count_same_day_overload(plan.sessions)
    recovery = _recovery_score(plan.sessions, session_types)
    balance = -OVERLOAD_PENALTY * overload
    total = recovery - CONFLICT_PENALTY * conflicts + balance
    return Scores(
        recovery=recovery,
        consistency=0.0,
        conflicts=conflicts,
        balance=balance,
        total=total,
    )


def count_hard_violations(
    plan: Plan,
    constraints: list[Constraint],
    session_types: dict[str, SessionType] | None = None,
) -> int:
    # Same-day overload is treated as a soft penalty via score_plan.balance so
    # the planner can still produce a feasible schedule in narrow calendars.
    return (
        _count_conflicts(plan.sessions)
        + _count_fixed_event_overlaps(plan.sessions, constraints)
    )


def _count_same_day_overload(sessions: list[ScheduledSession]) -> int:
    counts: dict[int, int] = {}
    for s in sessions:
        counts[s.day] = counts.get(s.day, 0) + 1
    return sum(c - 1 for c in counts.values() if c > 1)


def _count_conflicts(sessions: list[ScheduledSession]) -> int:
    by_day: dict[int, list[ScheduledSession]] = {}
    for s in sessions:
        by_day.setdefault(s.day, []).append(s)

    count = 0
    for day_sessions in by_day.values():
        day_sessions.sort(key=lambda s: _minutes(s.start))
        for i in range(len(day_sessions)):
            end_i = _minutes(day_sessions[i].start) + day_sessions[i].duration_min
            for j in range(i + 1, len(day_sessions)):
                if _minutes(day_sessions[j].start) < end_i:
                    count += 1
                else:
                    break
    return count


def _recovery_score(
    sessions: list[ScheduledSession],
    session_types: dict[str, SessionType] | None,
) -> float:
    score = 0.0
    for i, a in enumerate(sessions):
        for b in sessions[i + 1 :]:
            if not _shares_muscle_groups(a, b, session_types):
                continue
            gap_hours = abs(b.day - a.day) * 24.0
            required = _required_recovery(a, b, session_types)
            score += RECOVERY_REWARD if gap_hours >= required else RECOVERY_VIOLATION
    return score


def _shares_muscle_groups(
    a: ScheduledSession,
    b: ScheduledSession,
    session_types: dict[str, SessionType] | None,
) -> bool:
    if session_types is None:
        return a.session_type_id == b.session_type_id
    ta = session_types.get(a.session_type_id)
    tb = session_types.get(b.session_type_id)
    if ta is None or tb is None:
        return a.session_type_id == b.session_type_id
    return bool(set(ta.muscle_groups) & set(tb.muscle_groups))


def _required_recovery(
    a: ScheduledSession,
    b: ScheduledSession,
    session_types: dict[str, SessionType] | None,
) -> float:
    if session_types is None:
        return 48.0
    candidates = [
        session_types[s.session_type_id].recovery_hours
        for s in (a, b)
        if s.session_type_id in session_types
    ]
    return float(max(candidates)) if candidates else 48.0


def _count_fixed_event_overlaps(
    sessions: list[ScheduledSession], constraints: list[Constraint]
) -> int:
    events = [c for c in constraints if c.type == ConstraintType.FIXED_EVENT]
    if not events:
        return 0
    count = 0
    for s in sessions:
        s_start = _minutes(s.start)
        s_end = s_start + s.duration_min
        for c in events:
            if c.params.get("day_of_week") != s.day:
                continue
            e_start = _minutes(str(c.params.get("start", "00:00")))
            e_end = _minutes(str(c.params.get("end", "00:00")))
            if s_start < e_end and e_start < s_end:
                count += 1
    return count


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)
