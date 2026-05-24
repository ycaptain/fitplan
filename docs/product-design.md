# FitPlan AI — Design

CS5100 Foundations of AI · final project.

## 1. Problem

Maintaining a weekly workout schedule is a constrained-optimization
problem in disguise. Real-world weeks are interrupted: meetings appear,
sessions get missed, sleep quality varies. Existing tools (Hevy, Strong,
Fitbod, Notion templates) either log workouts or apply static rules, and
none of them re-plan around hard recovery constraints when something
breaks. FitPlan AI treats the weekly plan as a CSP plus an optimization
target, generates an initial schedule, and adapts it when the schedule
is perturbed.

## 2. Target user

A mid-level lifter (3–12 months of consistent training) with a busy,
variable weekly schedule. Goals are bulk, cut, or general fitness.

## 3. Differentiation

| Existing tool | Gap we address |
|---------------|----------------|
| Hevy, Strong  | Logging only; no scheduling |
| Notion / Google Calendar | Generic calendar; no domain constraints |
| Fitbod        | Per-session recommendation; no week-level planning |
| Chat assistants | Not verifiable; cannot adapt incrementally |

The differentiator is explicit AI search and optimization with
human-readable explanations.

## 4. MVP definition

The MVP guarantees that the following pipeline runs end-to-end:

- CSP with forward checking generates a feasible weekly plan
- Hill climbing performs minimal-disruption replanning
- The frontend renders the calendar, score breakdown, diff, and explain
- At least one baseline (greedy) runs in the offline evaluation

Advanced features (A\*, simulated annealing, genetic algorithm) layer on
top of the MVP pipeline once it is stable.

## 5. Scope

### In

- Weekly (7-day) workout scheduling
- Three training splits: Push-Pull-Legs, Upper-Lower, Full-Body
- Recovery constraints (per-muscle-group intervals, per-week intensity)
- Fixed external events as hard constraints
- Adaptive re-planning for four trigger types
  - newly added fixed event
  - missed session
  - changed user state (sleep, fatigue)
  - manual edit
- Score card and explanation for every plan
- Strategy routing exposed to the user as three modes:
  Generate, Minimal Disruption, Re-optimize
- Offline evaluation against a greedy baseline (additional baselines as
  stretch)

### Out

- Exercise-level real-time coaching
- Nutrition
- Multi-user / mobile-native apps
- Natural-language input parsing
- Multi-week mesocycle planning
- In-product algorithm-comparison lab page
- Any pre-trained model, RL training, or off-the-shelf ML implementations

## 6. Architecture

```
┌──────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                  │
│  /onboarding   /plan   /history   /settings          │
│  Calendar  ScoreCard  ExplainDrawer  StrategyBadge   │
└────────────────────────┬─────────────────────────────┘
                         │ REST
┌────────────────────────▼─────────────────────────────┐
│  Backend (FastAPI)                                   │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Strategy Routing                                │ │
│  │ Generate  →  Initial Solver                     │ │
│  │ Minimal Disruption  →  HC                       │ │
│  │ Re-optimize  →  SA / GA (advanced)              │ │
│  └─────────┬───────────────────────┬───────────────┘ │
│            ▼                       ▼                 │
│  ┌──────────────────┐   ┌──────────────────────────┐ │
│  │ Initial Solver   │   │ Adaptability Engine      │ │
│  │  CSP-BT + FC     │   │  Trigger normalizer      │ │
│  │  [+ GA opt.]     │   │  CSP re-validation       │ │
│  │  [+ A* opt.]     │   │  HC / SA / GA fallback   │ │
│  └──────────────────┘   └──────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Shared Core                                     │ │
│  │  domain models, constraints, scoring, explain   │ │
│  │  strategy trace                                 │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Baselines (offline eval)                        │ │
│  │  greedy [MVP] · random restart · rule-based     │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

The strategy router is intentionally simple: each user-facing mode maps
to one or two algorithms. There is no automatic meta-planner.

| User mode | Default algorithm | Purpose |
|-----------|-------------------|---------|
| Generate | CSP-BT + FC | Find a feasible weekly plan |
| Minimal Disruption | Hill Climbing | Keep the existing plan, fix conflicts only |
| Re-optimize | SA / GA | Explore alternative whole-week plans |

## 7. Adaptability

A weekly plan is rarely worth discarding when one session conflicts.
Adaptability is structured as four steps so the original plan is
preserved when possible.

```
Triggers  →  CSP re-validation  →  Local replan  →  Explanation
```

### Triggers

| Type | Source | Example | Delta |
|------|--------|---------|-------|
| `fixed_event_added` | calendar edit | a Wednesday meeting | append FixedEvent |
| `session_missed` | user marks missed | skipped Monday push | flag session.status |
| `state_changed` | daily check-in | bad sleep, high fatigue | update UserState |
| `manual_edit` | user drags a session | move leg day | update session start |

All four are normalized into a `PlanDelta` so downstream logic is
unaware of the trigger source.

### CSP re-validation

Backtracking with forward checking inspects the current plan and marks
each session `locked` if it still satisfies every hard constraint.
Only unlocked sessions enter the replan step.

### Local replan

Hill climbing starts from the current plan with a disturbance penalty
that discourages unnecessary moves. If the affected scope is large or
hill climbing stalls, simulated annealing takes over. If neither finds
a feasible plan, GA runs as a fallback with the current plan seeded as
an elite individual.

### Explanation

Each replan emits a diff (`moved`, `removed`, `added`), a disturbance
count, a recovery-score delta, a total-score delta, and a list of
constraints that triggered the change.

## 8. User journeys

### Journey A — initial plan

1. Onboarding form: goal, split, frequency, fixed events, preferences
2. Strategy routing selects the initial solver
3. Calendar, score card, strategy badge, and explanation drawer

### Journey B — replan after a disturbance

1. User adds a meeting, marks a missed workout, reports low energy,
   or drags a session
2. Trigger is normalized into a `PlanDelta`
3. CSP re-validation locks unaffected sessions
4. Hill climbing or simulated annealing produces a revised plan
5. Diff view, metrics, and accept / reject

## 9. AI methods used

| Method | Tier | Where it runs |
|--------|------|---------------|
| Backtracking + forward checking | MVP | Initial Solver, re-validation |
| Hill climbing | MVP | Small-scope replan with disturbance penalty |
| Greedy baseline | MVP | Offline comparison |
| Genetic algorithm | Advanced | Whole-plan optimization on top of CSP |
| Simulated annealing | Advanced | Large-scope replan |
| A\* / Beam | Stretch | Heuristic alternative to CSP for initial solver |
| Random restart, rule-based | Stretch | Additional baselines |

Every method runs in a real user-facing scenario.

## 10. Data model

The canonical Pydantic models are in `backend/app/ai/core/models.py`.

Key types:

- `SessionType`, `TrainingSplit`, `FixedEvent`, `UserState`, `Constraint`
- `ScheduledSession`, `Scores`, `Plan`
- `StrategyStep` (algorithm, role, nodes, iterations, time, score)
- `PlanDelta`, `ReplanDiff`, `ReplanMetrics`, `ReplanResult`

The TypeScript mirror is in `frontend/lib/types.ts`.

## 11. Evaluation

Offline evaluation (`scripts/eval/run_eval.py`) runs each algorithm and
baseline over a generated set of disturbance scenarios.

### Metrics

- Initial generation: convergence iterations, runtime, fitness,
  hard-constraint violations
- Adaptability: disturbance amount, recovery delta, score delta,
  one-shot feasibility rate

### Baselines

- Greedy re-insertion (MVP)
- Random restart, rule-based replanner (stretch)

## 12. Tech stack

- Backend: FastAPI, Pydantic, SQLite
- Frontend: Next.js 15 (App Router), TypeScript, Tailwind
- Testing: pytest for algorithms, end-to-end smoke tests via FastAPI
  TestClient
- All AI methods implemented from scratch
