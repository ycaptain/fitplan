# Constraint Types

Canonical enum: `backend/app/ai/core/constraints.py` (`ConstraintType`).

## Hard constraints

| Type | Params |
|------|--------|
| `recovery_interval` | `{ muscle_group: str, min_hours: int }` |
| `fixed_event` | `{ day: int, start: str, end: str }` |
| `max_per_week` | `{ kind: str, max: int }` |

## Soft constraints

| Type | Params |
|------|--------|
| `intensity_cap` | `{ max_per_week: int }` |
| `time_window` | `{ preferred_start: str, preferred_end: str }` |
| `session_duration` | `{ max_min: int }` |
