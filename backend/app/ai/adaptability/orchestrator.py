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

INFEASIBLE_REASON: Final[str] = "infeasible: manual edit required"


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
        algorithm="csp_stub",
        role="feasibility",
        score_after=plan.scores.total,
    )

    if not _check_feasibility(plan, constraints).is_feasible:
        snapshot = plan.model_copy(deep=True)
        snapshot.strategy_trace = [*snapshot.strategy_trace, feasibility_step]
        return ReplanResult(plan=snapshot, reason=INFEASIBLE_REASON)

    affected = set(delta.affected_session_ids)
    locked = _lock_non_affected(plan, affected)

    hc = registry.get(registry.AlgorithmKey.HILL_CLIMBING)
    t0 = time.perf_counter()
    out = hc(locked, constraints, random_seed=random_seed, session_types=session_types)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    replan_step = StrategyStep(
        algorithm=registry.AlgorithmKey.HILL_CLIMBING,
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
    result.reason = explain_replan(result, constraints)["text_summary"]
    return result


def _check_feasibility(plan: Plan, constraints: list[Constraint]) -> CSPResult:
    return CSPResult(is_feasible=True)


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
