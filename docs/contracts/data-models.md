# Data Models

Canonical source: `backend/app/ai/core/models.py`.
TypeScript mirror: `frontend/lib/types.ts`.

## Inputs

### `SessionType`

A unit of training (Push, Pull, Legs, Upper, Lower, FullBody).

| Field | Type | Notes |
|-------|------|-------|
| id | str | |
| name | str | display label |
| muscle_groups | list[str] | for recovery interval checking |
| intensity | float | 0–1 |
| duration_min | int | |
| recovery_hours | int | required gap before re-hitting same groups |

### `TrainingSplit`

A predefined sequence of `SessionType`s. MVP supports `ppl`,
`upper_lower`, `full_body`.

### `FixedEvent`

External calendar event (class, meeting) that consumes time.

### `UserState`

A daily user-reported state: sleep, fatigue, missed-last-session flag.

### `Constraint`

Either hard or soft. Types are enumerated in `constraints.py`.

## Outputs

### `ScheduledSession`

A planned session in the week.

| Field | Type | Notes |
|-------|------|-------|
| session_type_id | str | |
| day | int | 0–6 |
| start | str | HH:MM |
| duration_min | int | |
| locked | bool | set by CSP re-validation |
| status | "planned" \| "done" \| "missed" | |

### `Scores`

Aggregate of the soft-constraint dimensions.

| Field | Type |
|-------|------|
| recovery | float |
| consistency | float |
| conflicts | int |
| balance | float |
| total | float |

### `Plan`

Top-level container.

| Field | Type | Notes |
|-------|------|-------|
| id | str | |
| generated_at | str | ISO timestamp |
| sessions | list[ScheduledSession] | |
| scores | Scores | |
| strategy_trace | list[StrategyStep] | which algorithms ran and their stats |

### `StrategyStep`

One pass of an algorithm during generation or replanning.

| Field | Type | Notes |
|-------|------|-------|
| algorithm | str | registry key |
| role | "feasibility" \| "optimize" \| "replan" | |
| nodes | int | search-tree nodes expanded |
| iterations | int | for iterative methods |
| time_ms | int | |
| score_after | float | |

## Re-planning

### `PlanDelta`

Normalized form of a disturbance.

| Field | Type |
|-------|------|
| trigger_type | "fixed_event_added" \| "session_missed" \| "state_changed" \| "manual_edit" |
| payload | dict |
| affected_session_ids | list[str] |

### `ReplanDiff`, `ReplanMetrics`, `ReplanResult`

`ReplanResult` wraps the revised `Plan` together with a diff, the
adaptability metrics (disturbance, recovery_delta, score_delta), and a
human-readable reason.
