# FitPlan AI

An adaptive workout scheduling assistant. The system generates a weekly
training plan from user goals and constraints, and adapts the plan when
conditions change (new fixed event, missed session, low-energy day,
manual edit) using constraint propagation followed by local search.

CS5100 Foundations of AI final project.

## Quickstart

Prerequisites: Python 3.11+, Node.js 20+, and **pnpm 9**
(`npm install -g pnpm@9` or `corepack enable`).

```bash
make setup        # install backend venv + frontend deps (pnpm)
make backend      # FastAPI dev server on :8000
make frontend     # Next.js dev server on :3000
make test         # backend tests
make eval         # offline evaluation
```

Run `make backend` and `make frontend` in two terminals.

## Documentation

- [Product Design](docs/product-design.md)
- [Data Contracts](docs/contracts/data-models.md)
- [API Contracts](docs/contracts/api.md)
- [Constraint Types](docs/contracts/constraints.md)

## Layout

```
fitplan-ai/
├─ backend/        FastAPI + AI modules
│  └─ app/ai/
│     ├─ core/         shared models, scoring, registry
│     ├─ ga/           genetic algorithm
│     ├─ csp/          backtracking + forward checking
│     ├─ local/        hill climbing, simulated annealing
│     ├─ baselines/    random restart, greedy, rule-based
│     └─ adaptability/ triggers + replan orchestration
├─ frontend/       Next.js (App Router) + Tailwind
├─ scripts/eval/   offline evaluation harness
└─ docs/           design and contracts
```
