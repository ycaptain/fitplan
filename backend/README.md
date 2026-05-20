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

```bash
make setup-backend
make backend            # http://localhost:8000
make test
```

OpenAPI docs at http://localhost:8000/docs.
