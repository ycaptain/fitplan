# API

## `POST /api/plan/generate`

Generate an initial weekly plan from user goals and constraints.

Request:

```json
{ "goal": "bulk", "split": "ppl", "sessions_per_week": 4 }
```

Returns a `Plan`.

## `POST /api/plan/replan`

Re-validate the current plan against a disturbance and produce a revised plan.

Request:

```json
{
  "plan_id": "...",
  "trigger_type": "fixed_event_added",
  "payload": { }
}
```

Returns a `ReplanResult`.

## `GET /health`

Smoke check. Returns `{ "status": "ok" }`.
