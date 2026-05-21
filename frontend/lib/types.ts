// Shared types mirroring backend/app/ai/core/models.py.

export type Goal = "bulk" | "cut" | "general";
export type SplitName = "ppl" | "upper_lower" | "full_body";
export type ConstraintKind = "hard" | "soft";
export type SessionStatus = "planned" | "done" | "missed";
export type AlgoRole = "generate" | "revalidate" | "replan";
export type TriggerType =
  | "fixed_event_added"
  | "session_missed"
  | "state_changed"
  | "manual_edit";

export interface SessionType {
  id: string;
  name: string;
  muscle_groups: string[];
  intensity: number;
  duration_min: number;
  recovery_hours: number;
}

export interface TrainingSplit {
  id: string;
  name: SplitName;
  sessions: SessionType[];
}

export interface FixedEvent {
  id: string;
  day_of_week: number;
  start: string;
  end: string;
  label: string;
}

export interface UserState {
  date: string;
  sleep_hours: number;
  perceived_fatigue: number;
  missed_last_session: boolean;
}

export interface Constraint {
  id: string;
  kind: ConstraintKind;
  type: string;
  params: Record<string, unknown>;
  weight: number;
}

export interface ScheduledSession {
  session_type_id: string;
  day: number;
  start: string;
  duration_min: number;
  locked: boolean;
  status: SessionStatus;
}

export interface Scores {
  recovery: number;
  consistency: number;
  conflicts: number;
  balance: number;
  total: number;
}

export interface AlgoStep {
  algorithm: string;
  role: AlgoRole;
  iterations: number;
  time_ms: number;
  score_after: number;
}

export interface Plan {
  id: string;
  generated_at: string;
  sessions: ScheduledSession[];
  scores: Scores;
  algorithm_trace: AlgoStep[];
}

export interface PlanDelta {
  trigger_type: TriggerType;
  payload: Record<string, unknown>;
  affected_session_ids: string[];
}

export interface ReplanDiff {
  moved: string[];
  removed: string[];
  added: string[];
}

export interface ReplanMetrics {
  disturbance: number;
  recovery_delta: number;
  score_delta: number;
}

export interface ReplanResult {
  plan: Plan;
  diff: ReplanDiff;
  metrics: ReplanMetrics;
  reason: string;
}
