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

## 4. Scope

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
- Three baselines for offline comparison

### Out

- Exercise-level real-time coaching
- Nutrition
- Multi-user / mobile-native apps
- Natural-language input parsing
- Multi-week mesocycle planning
- Any pre-trained model, RL training, or off-the-shelf ML implementations

## 5. Architecture

```
┌──────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                  │
│  /onboarding   /plan   /history   /settings          │
└────────────────────────┬─────────────────────────────┘
                         │ REST
┌────────────────────────▼─────────────────────────────┐
│  Backend (FastAPI)                                   │
│  ┌───────────────────┐   ┌──────────────────────────┐│
│  │ Initial Generator │   │ Adaptability Engine      ││
│  │ Genetic Algorithm │   │  Trigger normalizer      ││
│  │                   │   │  CSP re-validation       ││
│  │                   │   │  Hill climbing / SA      ││
│  │                   │   │  GA fallback             ││
│  └───────────────────┘   └──────────────────────────┘│
│  ┌───────────────────────────────────────────────────┐│
│  │ Shared core: domain models, scoring, explain      ││
│  └───────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

The dispatch logic collapses to two questions:

```
Is this an initial plan or a replan?
  initial → GA
  replan  → adaptability engine

If replan, how big is the change?
  small (<= 30% affected sessions) → hill climbing
  large or HC stuck                → simulated annealing → GA fallback
```

## 6. Adaptability

A weekly plan is rarely worth discarding when one session conflicts.
Adaptability is structured as four steps so the original plan is kept
as much as possible.

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
each session `locked` if it still satisfies every hard constraint
(recovery interval, fixed-event clearance, weekly intensity cap).
Only unlocked sessions enter the replan step.

### Local replan

Hill climbing starts from the current plan with a disturbance penalty
that discourages unnecessary moves. If the affected scope is large or
hill climbing stalls, simulated annealing takes over. If neither finds
a feasible plan, GA runs as a fallback with the current plan seeded
into the initial population as an elite individual.

### Explanation

Each replan emits a diff (`moved`, `removed`, `added`), a disturbance
count, a recovery-score delta, a total-score delta, and a list of
constraints that triggered the change.

## 7. User journeys

### Journey A — initial plan

1. Onboarding form: goal, split, frequency, fixed events, preferences
2. GA generates a plan (showing generation count and best fitness)
3. Calendar, score card, and explanation drawer

### Journey B — replan after a disturbance

1. User adds a meeting, marks a missed workout, reports low energy,
   or drags a session
2. Trigger is normalized into a `PlanDelta`
3. CSP re-validation locks unaffected sessions
4. Hill climbing or simulated annealing produces a revised plan
5. Diff view, metrics, and accept / reject

## 8. AI methods used

| Method | Where it runs |
|--------|---------------|
| Genetic algorithm | Initial plan generation, replan fallback |
| Backtracking + forward checking | Re-validation before replanning |
| Hill climbing | Small-scope replan, with disturbance penalty |
| Simulated annealing | Large-scope replan |
| Baselines (random restart, greedy, rule-based) | Offline comparison |

Every method runs in a real user-facing scenario.

## 9. Data model

The canonical Pydantic models are in `backend/app/ai/core/models.py`.

Key types:

- `SessionType`, `TrainingSplit`, `FixedEvent`, `UserState`, `Constraint`
- `ScheduledSession`, `Scores`, `AlgoStep`, `Plan`
- `PlanDelta`, `ReplanDiff`, `ReplanMetrics`, `ReplanResult`

The TypeScript mirror is in `frontend/lib/types.ts`.

## 10. Evaluation

Offline evaluation (`scripts/eval/run_eval.py`) runs each algorithm and
baseline over a generated set of disturbance scenarios.

### Metrics

- Initial generation: GA convergence generations, runtime, fitness,
  hard-constraint violations
- Adaptability: disturbance amount, recovery delta, score delta,
  one-shot feasibility rate

### Baselines

- Random restart (re-run GA from scratch)
- Greedy re-insertion (place conflicting sessions in nearest free slot)
- Rule-based replanner (Fitbod-style)

### Scenario coverage

At least 50 disturbance scenarios across the four trigger types, with
single-conflict and multi-conflict variants.

## 11. Tech stack

- Backend: FastAPI, Pydantic, SQLite
- Frontend: Next.js 15 (App Router), TypeScript, Tailwind
- Testing: pytest for algorithms, end-to-end smoke tests via FastAPI
  TestClient
- All AI methods implemented from scratch
