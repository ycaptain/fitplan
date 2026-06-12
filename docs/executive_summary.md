# FitPlan AI: Executive Summary

**CS5100 Foundations of AI, Northeastern University**

**Team:** Aaron Yao, Hao Cai | **GitHub:** https://github.com/ycaptain/fitplan

---

## Problem Motivation

Most calendar and fitness apps treat scheduling as a static problem. Once a plan is made, users have to reorganize it manually whenever something changes. A single conflict (an unexpected meeting, a missed session, a bad-sleep day) can derail an entire week. We built **FitPlan AI** to model workout scheduling as a constraint satisfaction and optimization problem, so the system can generate a plan from the user's goals and constraints and automatically re-plan when conditions change, using classical AI methods implemented from scratch.

---

## Implemented Methods

### Initial Plan Generation

| Method                                  | Description                                                                                                                                   |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **CSP Backtracking + Forward Checking** | Assigns sessions to days via backtracking search with domain pruning; two-phase (strict placement then relaxed fallback for narrow calendars) |
| **Beam Search** (width 3)               | Heuristic-guided search that keeps the top-K partial plans at each step, scoring by recovery quality and spread                               |
| **Genetic Algorithm**                   | Population of 20 chromosomes (day assignments per session); tournament selection, single-point crossover, random-day mutation; 40 generations |
| **Greedy Baseline**                     | Deterministic first-fit; ignores recovery spacing by design, used as a lower-bound baseline for comparison                                    |

### Adaptive Replanning

| Method                  | Description                                                                                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Hill Climbing**       | Steepest-ascent over `(session, day, start)` neighborhood; lexicographic fitness `(-hard_violations, score, -moves)` prevents the "stay-put" trap from linear penalties |
| **Simulated Annealing** | Probabilistic acceptance with exponential cooling; used when affected-session ratio > 0.3 (large-disturbance replans)                                                   |

**Trigger types handled:** new fixed event, missed session, state change (fatigue/sleep), manual time edit.

All methods are implemented from scratch in Python. No scikit-learn, no pretrained models.

---

## Key Results

From the offline evaluation (`make eval`, seed 42, 36 disturbance scenarios):

**Generators**: CSP, Beam Search, and GA all reach optimal recovery scores with zero conflicts on every split. Greedy is consistently lower (e.g. -4.0 vs 0.0 for PPL/3-session), confirming it serves as a meaningful lower bound.

| Split / sessions | CSP | Beam | GA  | Greedy |
| ---------------- | --- | ---- | --- | ------ |
| PPL / 3          | 0.0 | 0.0  | 0.0 | -4.0   |
| PPL / 5          | 2.0 | 2.0  | 2.0 | -10.0  |
| Upper-Lower / 5  | 4.0 | 4.0  | 4.0 | -12.0  |
| Full Body / 5    | 6.0 | 3.0  | 6.0 | -18.0  |

**Replanners**: both HC and SA resolve all hard violations (hard 1->0) across all 36 scenarios. HC is faster for small disturbances (under 5 ms); SA moves fewer sessions on large disturbances (intensity > 0.3), making it the better choice when most of the plan is affected.

---

## Challenges

**Same-day overload as a hard constraint.** We originally treated two sessions on the same day as a hard violation. In narrow calendars (4+ busy blocks), this left the planner with no feasible solution and produced fixed-event overlaps. Fixed by demoting it to a soft penalty (`OVERLOAD_PENALTY = 2.0 < CONFLICT_PENALTY = 5.0`).

**Lexicographic fitness in Hill Climbing.** An early version used `score - a*moves` to penalize disruption. With any a > 0, the "stay put" neighbor (0 moves) always wins at step 0 and the algorithm never moves. Switched to tuple comparison `(-hard, total, -moves)` so disruption acts as a tie-breaker only.

**Client-authoritative events.** The backend stored fixed events server-side, so "Skip" actions in the frontend weren't reflected on the next replan. Fixed by passing the full event list with every `POST /api/plan/replan` request; the backend now discards its cached copy.

**Session locks not resetting between replans.** HC marks unaffected sessions as `locked=True` to avoid unnecessary moves. On consecutive replans, stale locks from the previous round were freezing sessions that should have been free. Fixed by explicitly resetting locks at the start of each replan round.

---

## Individual Contributions

**Shared foundation (both)**: The system architecture and the shared core were designed and worked through jointly, including the data contracts (`core/models.py`, `frontend/lib/types.ts`), the algorithm registry, and the scoring/explain framework. These were committed from Yao's machine for practical reasons during the design sessions, but the decisions came from both members.

**Aaron Yao**: Hill Climbing, Simulated Annealing, adaptability orchestrator and trigger normalizers, `POST /api/plan/replan` endpoint, frontend `/plan` page and Calendar component, offline evaluation harness, project scaffold and CI.

**Hao Cai**: CSP backtracking + forward checking initial generator (`csp/backtracking.py`), Beam Search (`search/beam_search.py`), Genetic Algorithm (`ga/genetic_algorithm.py`), plan explanation API surfacing in the frontend.
