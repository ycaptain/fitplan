"""Constraint type enumeration."""

from __future__ import annotations

from enum import StrEnum


class ConstraintType(StrEnum):
    RECOVERY_INTERVAL = "recovery_interval"
    FIXED_EVENT = "fixed_event"
    MAX_PER_WEEK = "max_per_week"
    INTENSITY_CAP = "intensity_cap"
    TIME_WINDOW = "time_window"
    SESSION_DURATION = "session_duration"


HARD_TYPES: set[ConstraintType] = {
    ConstraintType.RECOVERY_INTERVAL,
    ConstraintType.FIXED_EVENT,
    ConstraintType.MAX_PER_WEEK,
}

SOFT_TYPES: set[ConstraintType] = {
    ConstraintType.INTENSITY_CAP,
    ConstraintType.TIME_WINDOW,
    ConstraintType.SESSION_DURATION,
}
