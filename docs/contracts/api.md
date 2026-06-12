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
  "mode": "minimal_disruption",
  "payload": {},
  "fixed_events": []
}
```

`mode` controls the replanning strategy:

| Value                | Behaviour                                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `minimal_disruption` | Lock all sessions except those directly affected; disturbance is bounded by the affected count                             |
| `re_optimize`        | Unlock the whole plan and run local search with a disturbance penalty; may move more sessions for a globally better layout |

`trigger_type` values and their required `payload` shapes:

| `trigger_type`      | `payload` fields                                                  |
| ------------------- | ----------------------------------------------------------------- |
| `fixed_event_added` | `id`, `day_of_week`, `start`, `end`, `label`                      |
| `session_missed`    | `session_id`                                                      |
| `state_changed`     | `date`, `sleep_hours`, `perceived_fatigue`, `missed_last_session` |
| `manual_edit`       | `session_id`, `new_start`                                         |

Returns a `ReplanResult`.

## `GET /health`

Smoke check. Returns `{ "status": "ok" }`.
