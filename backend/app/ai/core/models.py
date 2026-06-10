from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Goal = Literal["bulk", "cut", "general"]
SplitName = Literal["ppl", "upper_lower", "full_body"]
ConstraintKind = Literal["hard", "soft"]


class SessionType(BaseModel):
    id: str
    name: str
    muscle_groups: list[str] = Field(default_factory=list)
    intensity: float = 0.5
    duration_min: int = 60
    recovery_hours: int = 48


class TrainingSplit(BaseModel):
    id: str
    name: SplitName
    sessions: list[SessionType] = Field(default_factory=list)


class FixedEvent(BaseModel):
    id: str
    day_of_week: int
    start: str
    end: str
    label: str


class UserState(BaseModel):
    date: str
    sleep_hours: float = 7.5
    perceived_fatigue: int = 5
    missed_last_session: bool = False


class Constraint(BaseModel):
    id: str
    kind: ConstraintKind
    type: str
    params: dict = Field(default_factory=dict)
    weight: float = 1.0


class ScheduledSession(BaseModel):
    id: str
    session_type_id: str
    day: int
    start: str
    duration_min: int
    locked: bool = False
    status: Literal["planned", "done", "missed"] = "planned"

    @staticmethod
    def derive_id(day: int, session_type_id: str, start: str) -> str:
        return f"{day}-{session_type_id}-{start}"


class Scores(BaseModel):
    recovery: float = 0.0
    consistency: float = 0.0
    conflicts: int = 0
    balance: float = 0.0
    total: float = 0.0


class StrategyStep(BaseModel):
    algorithm: str
    role: Literal["feasibility", "optimize", "replan"]
    nodes: int = 0
    iterations: int = 0
    time_ms: int = 0
    score_after: float = 0.0


class ConstraintHit(BaseModel):
    constraint_id: str
    satisfied: bool
    explanation: str = ""


class PlanExplanation(BaseModel):
    constraint_hits: list[ConstraintHit] = Field(default_factory=list)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    text_summary: str = ""


class Plan(BaseModel):
    id: str
    generated_at: str
    sessions: list[ScheduledSession] = Field(default_factory=list)
    scores: Scores = Field(default_factory=Scores)
    strategy_trace: list[StrategyStep] = Field(default_factory=list)
    explanation: PlanExplanation | None = None


class PlanDelta(BaseModel):
    trigger_type: Literal[
        "fixed_event_added",
        "session_missed",
        "state_changed",
        "manual_edit",
    ]
    payload: dict = Field(default_factory=dict)
    affected_session_ids: list[str] = Field(default_factory=list)


class ReplanDiff(BaseModel):
    moved: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    added: list[str] = Field(default_factory=list)


class ReplanMetrics(BaseModel):
    disturbance: int = 0
    recovery_delta: float = 0.0
    score_delta: float = 0.0


class ReplanResult(BaseModel):
    plan: Plan
    diff: ReplanDiff = Field(default_factory=ReplanDiff)
    metrics: ReplanMetrics = Field(default_factory=ReplanMetrics)
    reason: str = ""
    explanation: PlanExplanation | None = None


class Preferences(BaseModel):
    preferred_time_of_day: Literal["morning", "evening", "any"] = "any"
    max_session_duration_min: int = 90


GeneratorName = Literal["csp_bt_fc", "beam_search", "greedy_baseline"]


class GeneratePlanRequest(BaseModel):
    goal: Goal = "general"
    split: SplitName = "ppl"
    sessions_per_week: int = 4
    fixed_events: list[FixedEvent] = Field(default_factory=list)
    preferences: Preferences = Field(default_factory=Preferences)
    algorithm: GeneratorName = "csp_bt_fc"


ReplanMode = Literal["minimal_disruption", "re_optimize"]


class ReplanRequest(BaseModel):
    plan_id: str
    trigger_type: Literal[
        "fixed_event_added",
        "session_missed",
        "state_changed",
        "manual_edit",
    ]
    payload: dict = Field(default_factory=dict)
    mode: ReplanMode = "minimal_disruption"
    # Optional: client-authoritative full list of fixed events at the moment of
    # the replan. When provided, the server treats this as the canonical event
    # set instead of the value cached in plan_store.
    fixed_events: list[FixedEvent] | None = None


class ConstraintViolation(BaseModel):
    constraint_id: str
    session_ids: list[str] = Field(default_factory=list)
    message: str = ""


class CSPResult(BaseModel):
    locked_session_ids: list[str] = Field(default_factory=list)
    violations: list[ConstraintViolation] = Field(default_factory=list)
    is_feasible: bool = True
