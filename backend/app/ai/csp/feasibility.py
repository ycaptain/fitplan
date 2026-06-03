from __future__ import annotations

from typing import Final

from app.ai.core.constraints import ConstraintType
from app.ai.core.models import (
    Constraint,
    ConstraintViolation,
    CSPResult,
    Plan,
    ScheduledSession,
    SessionType,
)

DAYS_IN_WEEK: Final[int] = 7
EARLIEST_START_MINUTES: Final[int] = 6 * 60
LATEST_END_MINUTES: Final[int] = 22 * 60


def check_feasibility(
    plan: Plan,
    constraints: list[Constraint],
    *,
    session_types: dict[str, SessionType] | None = None,
) -> CSPResult:
    """Forward-checking style re-validation of an existing plan.

    A plan is feasible when every session in violation of a hard constraint is
    unlocked and still has at least one conflict-free (day, start) slot left in
    its domain. Locked sessions in violation, or sessions whose domain has been
    wiped out, make the plan infeasible and require a manual edit.
    """
    events = [c for c in constraints if c.type == ConstraintType.FIXED_EVENT]
    violations = _collect_violations(plan.sessions, events)
    locked_ids = [s.id for s in plan.sessions if s.locked]

    if not violations:
        return CSPResult(locked_session_ids=locked_ids, is_feasible=True)

    locked = set(locked_ids)
    conflicted_ids = {sid for v in violations for sid in v.session_ids}

    for session in plan.sessions:
        if session.id not in conflicted_ids:
            continue
        if session.id in locked:
            others_in_violation = any(
                sid != session.id and sid not in locked
                for v in violations
                if session.id in v.session_ids
                for sid in v.session_ids
            )
            if not others_in_violation:
                return CSPResult(
                    locked_session_ids=locked_ids,
                    violations=violations,
                    is_feasible=False,
                )
            continue
        if not _has_open_slot(session, plan.sessions, events):
            return CSPResult(
                locked_session_ids=locked_ids,
                violations=violations,
                is_feasible=False,
            )

    return CSPResult(
        locked_session_ids=locked_ids,
        violations=violations,
        is_feasible=True,
    )


def _collect_violations(
    sessions: list[ScheduledSession],
    events: list[Constraint],
) -> list[ConstraintViolation]:
    violations: list[ConstraintViolation] = []

    for session in sessions:
        for event in events:
            if _overlaps_event(session, session.day, session.start, event):
                violations.append(
                    ConstraintViolation(
                        constraint_id=event.id,
                        session_ids=[session.id],
                        message=f"session {session.id} overlaps fixed event {event.id}",
                    )
                )

    for i, a in enumerate(sessions):
        for b in sessions[i + 1 :]:
            if a.day == b.day and _spans_overlap(
                _minutes(a.start),
                _minutes(a.start) + a.duration_min,
                _minutes(b.start),
                _minutes(b.start) + b.duration_min,
            ):
                violations.append(
                    ConstraintViolation(
                        constraint_id="session_conflict",
                        session_ids=[a.id, b.id],
                        message=f"sessions {a.id} and {b.id} overlap",
                    )
                )

    return violations


def _has_open_slot(
    session: ScheduledSession,
    sessions: list[ScheduledSession],
    events: list[Constraint],
) -> bool:
    others = [s for s in sessions if s.id != session.id]
    for day in range(DAYS_IN_WEEK):
        for start in _candidate_starts(sessions, events):
            if _minutes(start) + session.duration_min > LATEST_END_MINUTES:
                continue
            if any(_overlaps_event(session, day, start, e) for e in events):
                continue
            if any(
                o.day == day
                and _spans_overlap(
                    _minutes(start),
                    _minutes(start) + session.duration_min,
                    _minutes(o.start),
                    _minutes(o.start) + o.duration_min,
                )
                for o in others
            ):
                continue
            return True
    return False


def _candidate_starts(
    sessions: list[ScheduledSession],
    events: list[Constraint],
) -> list[str]:
    starts = {s.start for s in sessions}
    for event in events:
        end = event.params.get("end")
        if isinstance(end, str):
            starts.add(end)
    starts.update(("07:00", "12:00", "17:00", "18:00", "19:00"))
    return sorted(
        (s for s in starts if _minutes(s) >= EARLIEST_START_MINUTES),
        key=_minutes,
    )


def _overlaps_event(
    session: ScheduledSession,
    day: int,
    start: str,
    event: Constraint,
) -> bool:
    if event.params.get("day_of_week") != day:
        return False
    s_start = _minutes(start)
    e_start = _minutes(str(event.params.get("start", "00:00")))
    e_end = _minutes(str(event.params.get("end", "00:00")))
    return _spans_overlap(s_start, s_start + session.duration_min, e_start, e_end)


def _spans_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    return start_a < end_b and start_b < end_a


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)
