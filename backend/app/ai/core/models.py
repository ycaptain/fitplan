"""Pydantic models shared across the scheduling pipeline."""

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
    session_type_id: str
    day: int
    start: str
    duration_min: int
    locked: bool = False
    status: Literal["planned", "done", "missed"] = "planned"


class Scores(BaseModel):
    recovery: float = 0.0
    consistency: float = 0.0
    conflicts: int = 0
    balance: float = 0.0
    total: float = 0.0


class AlgoStep(BaseModel):
    algorithm: str
    role: Literal["generate", "revalidate", "replan"]
    iterations: int = 0
    time_ms: int = 0
    score_after: float = 0.0


class Plan(BaseModel):
    id: str
    generated_at: str
    sessions: list[ScheduledSession] = Field(default_factory=list)
    scores: Scores = Field(default_factory=Scores)
    algorithm_trace: list[AlgoStep] = Field(default_factory=list)


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
