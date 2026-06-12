from __future__ import annotations

import time
from typing import Final

from app.ai import local as _local  # noqa: F401
from app.ai.core import registry
from app.ai.core.explain import explain_replan
from app.ai.core.models import (
    Constraint,
    CSPResult,
    Plan,
    PlanDelta,
    ReplanDiff,
    ReplanMetrics,
    ReplanMode,
    ReplanResult,
    SessionType,
    StrategyStep,
)
from app.ai.csp.feasibility import check_feasibility

INFEASIBLE_REASON: Final[str] = "infeasible: manual edit required"

# beyond this ratio SA outperforms steepest-ascent HC on re_optimize replans
HC_AFFECTED_RATIO_THRESHOLD: Final[float] = 0.3
RE_OPTIMIZE_DISTURBANCE_PENALTY: Final[float] = 0.5


@registry.register(registry.AlgorithmKey.ORCHESTRATE_REPLAN)
def orchestrate_replan(
    plan: Plan,
    delta: PlanDelta,
    constraints: list[Constraint],
    mode: ReplanMode,
    *,
    session_types: dict[str, SessionType] | None = None,
    random_seed: int | None = None,
) -> ReplanResult:
    feasibility_step = StrategyStep(
        algorithm="csp_bt_fc",
        role="feasibility",
        score_after=plan.scores.total,
    )

    affected = set(delta.affected_session_ids)
    algorithm_key, working, replan_kwargs = _select_replanner(plan, affected, mode)

    if not _check_feasibility(working, constraints, session_types=session_types).is_feasible:
        snapshot = plan.model_copy(deep=True)
        snapshot.strategy_trace = [*snapshot.strategy_trace, feasibility_step]
        return ReplanResult(plan=snapshot, reason=INFEASIBLE_REASON)

    replanner = registry.get(algorithm_key)
    t0 = time.perf_counter()
    out = replanner(
        working,
        constraints,
        random_seed=random_seed,
        session_types=session_types,
        **replan_kwargs,
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    replan_step = StrategyStep(
        algorithm=algorithm_key,
        role="replan",
        time_ms=elapsed_ms,
        score_after=out.scores.total,
    )
    out.strategy_trace = [*out.strategy_trace, feasibility_step, replan_step]

    diff = _compute_diff(plan, out)
    metrics = ReplanMetrics(
        disturbance=len(diff.moved) + len(diff.removed) + len(diff.added),
        recovery_delta=out.scores.recovery - plan.scores.recovery,
        score_delta=out.scores.total - plan.scores.total,
    )
    result = ReplanResult(plan=out, diff=diff, metrics=metrics)
    result.explanation = explain_replan(
        result, constraints, affected_count=len(affected) or None
    )
    result.reason = result.explanation.text_summary
    return result


def _select_replanner(
    plan: Plan,
    affected: set[str],
    mode: ReplanMode,
) -> tuple[str, Plan, dict]:
    if mode == "re_optimize":
        affected_ratio = len(affected) / max(1, len(plan.sessions))
        key = (
            registry.AlgorithmKey.SIMULATED_ANNEALING
            if affected_ratio > HC_AFFECTED_RATIO_THRESHOLD
            else registry.AlgorithmKey.HILL_CLIMBING
        )
        return key, _unlock_all(plan), {
            "disturbance_penalty": RE_OPTIMIZE_DISTURBANCE_PENALTY
        }
    return registry.AlgorithmKey.HILL_CLIMBING, _lock_non_affected(plan, affected), {}


def _unlock_all(plan: Plan) -> Plan:
    clone = plan.model_copy(deep=True)
    clone.sessions = [s.model_copy(update={"locked": False}) for s in clone.sessions]
    return clone


def _check_feasibility(
    plan: Plan,
    constraints: list[Constraint],
    *,
    session_types: dict[str, SessionType] | None = None,
) -> CSPResult:
    return check_feasibility(plan, constraints, session_types=session_types)


def _lock_non_affected(plan: Plan, affected: set[str]) -> Plan:
    clone = plan.model_copy(deep=True)
    clone.sessions = [
        s.model_copy(update={"locked": s.id not in affected})
        for s in clone.sessions
    ]
    return clone


def _compute_diff(before: Plan, after: Plan) -> ReplanDiff:
    before_slots = {s.id: (s.day, s.start) for s in before.sessions}
    after_slots = {s.id: (s.day, s.start) for s in after.sessions}
    moved = sorted(
        sid
        for sid, slot in after_slots.items()
        if sid in before_slots and before_slots[sid] != slot
    )
    removed = sorted(sid for sid in before_slots if sid not in after_slots)
    added = sorted(sid for sid in after_slots if sid not in before_slots)
    return ReplanDiff(moved=moved, removed=removed, added=added)
