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

### CSP Planner

The primary planner uses backtracking with forward checking to generate a feasible weekly workout schedule while satisfying hard constraints such as fixed events and recovery requirements.

### Greedy Baseline

A simple baseline planner that places sessions sequentially without global reasoning. It is used as a comparison method during evaluation.

### Beam Search

An experimental search-based planner that keeps multiple promising partial schedules during planning and selects the highest-scoring candidate.

## Reproducing Results

Run all backend tests:

```bash
pytest
```

Expected output:

```text
All tests should pass.
```

Run the evaluation script:

```bash
python ../scripts/eval/evaluate_baselines.py
```

This compares:

* CSP Planner
* Beam Search Planner
* Greedy Baseline

and reports:

- Total score
- Recovery score
- Constraint violations
- Search nodes explored
