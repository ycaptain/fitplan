from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.ai.core.models import (
    Constraint,
    CSPResult,
    GeneratePlanRequest,
    Plan,
    PlanDelta,
    ReplanMode,
    ReplanResult,
)


@runtime_checkable
class FeasibilityChecker(Protocol):
    def __call__(
        self, plan: Plan, constraints: list[Constraint]
    ) -> CSPResult: ...


@runtime_checkable
class InitialGenerator(Protocol):
    def __call__(
        self,
        request: GeneratePlanRequest,
        constraints: list[Constraint],
    ) -> Plan: ...


@runtime_checkable
class LocalReplanner(Protocol):
    def __call__(
        self,
        plan: Plan,
        constraints: list[Constraint],
        *,
        max_iter: int = 100,
        disturbance_penalty: float = 0.0,
        random_seed: int | None = None,
    ) -> Plan: ...


@runtime_checkable
class ReplanOrchestrator(Protocol):
    def __call__(
        self,
        plan: Plan,
        delta: PlanDelta,
        constraints: list[Constraint],
        mode: ReplanMode,
    ) -> ReplanResult: ...


@runtime_checkable
class Baseline(Protocol):
    def __call__(
        self,
        request: GeneratePlanRequest,
        constraints: list[Constraint],
    ) -> Plan: ...
