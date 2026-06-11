# Backend

FastAPI service hosting the scheduling and adaptability modules.

## Layout

```
app/
├─ main.py              FastAPI entry, router aggregation
├─ api/
│  ├─ plan_generate.py  POST /api/plan/generate
│  └─ plan_replan.py    POST /api/plan/replan
└─ ai/
   ├─ core/             shared models, scoring, registry
   ├─ ga/               genetic algorithm
   ├─ csp/              backtracking + forward checking
   ├─ local/            hill climbing, simulated annealing
   ├─ baselines/        random_restart, greedy, rule_based
   └─ adaptability/     triggers + replan orchestrator
```

## Dev

Requires Python 3.11+. `make setup-backend` auto-picks the first available
`python3.13` / `3.12` / `3.11` on PATH; override with
`make setup-backend PYTHON=/path/to/python3.x` if needed.

```bash
make setup-backend
make backend            # http://localhost:8000
make test
```

OpenAPI docs at http://localhost:8000/docs.

## API Example

Generate an initial weekly plan:

```bash
curl -X POST http://localhost:8000/api/plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "general",
    "split": "ppl",
    "sessions_per_week": 4
  }'
```

Example response:

```json
{
  "id": "plan-123",
  "sessions": [
    {
      "session_type_id": "push",
      "day": 0,
      "start": "07:00"
    },
    {
      "session_type_id": "pull",
      "day": 2,
      "start": "07:00"
    },
    {
      "session_type_id": "legs",
      "day": 4,
      "start": "07:00"
    },
    {
      "session_type_id": "push",
      "day": 6,
      "start": "07:00"
    }
  ],
  "scores": {
    "recovery": 1,
    "conflicts": 0,
    "total": 1
  }
}
```

## AI Methods

All algorithms register themselves in `app/ai/core/registry.py` under a string
key; the API and the eval harness look them up there.

### CSP Planner (`csp_bt_fc`)

The primary planner uses backtracking with forward checking to generate a feasible weekly workout schedule while satisfying hard constraints such as fixed events and recovery requirements. `app/ai/csp/feasibility.py` re-uses the same constraint checks to re-validate an existing plan before each replan (domain-wipeout detection).

### Greedy Baseline (`greedy_baseline`)

A simple baseline planner that places sessions sequentially without global reasoning. It is used as a comparison method during evaluation.

### Beam Search (`beam_search`)

An experimental search-based planner that keeps multiple promising partial schedules during planning and selects the highest-scoring candidate.

### Hill Climbing (`hill_climbing`) and Simulated Annealing (`simulated_annealing`)

Local-search replanners used by the adaptability orchestrator. `minimal_disruption` replans lock unaffected sessions and run steepest-ascent HC; `re_optimize` replans unlock everything and escalate to SA once the affected ratio exceeds `HC_AFFECTED_RATIO_THRESHOLD = 0.3`.

## Reproducing Results

Run all backend tests:

```bash
pytest
```

Run the evaluation harness (from the repo root):

```bash
make eval
```

This compares the initial-plan generators (CSP, Beam Search, Greedy) and the
replanners (HC, SA) across ~36 disturbance scenarios, and writes the full
report — score, recovery, conflicts, search effort, plus the routing-threshold
calibration — to `docs/eval_report.md`.
