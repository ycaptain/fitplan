// Shared types mirroring backend/app/ai/core/models.py.

export type Goal = "bulk" | "cut" | "general";
export type SplitName = "ppl" | "upper_lower" | "full_body";
export type ConstraintKind = "hard" | "soft";
export type SessionStatus = "planned" | "done" | "missed";
export type StrategyRole = "feasibility" | "optimize" | "replan";
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
  id: string;
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

export interface StrategyStep {
  algorithm: string;
  role: StrategyRole;
  nodes: number;
  iterations: number;
  time_ms: number;
  score_after: number;
}

export interface Plan {
  id: string;
  generated_at: string;
  sessions: ScheduledSession[];
  scores: Scores;
  strategy_trace: StrategyStep[];
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

export type ReplanMode = "minimal_disruption" | "re_optimize";

export interface Preferences {
  preferred_time_of_day: "morning" | "evening" | "any";
  max_session_duration_min: number;
}

export type GeneratorName = "csp_bt_fc" | "beam_search" | "greedy_baseline";

export interface GeneratePlanRequest {
  goal: Goal;
  split: SplitName;
  sessions_per_week: number;
  fixed_events: FixedEvent[];
  preferences: Preferences;
  algorithm?: GeneratorName;
}

export interface ReplanRequest {
  plan_id: string;
  trigger_type: TriggerType;
  payload: Record<string, unknown>;
  mode: ReplanMode;
  fixed_events?: FixedEvent[];
}

export interface ConstraintViolation {
  constraint_id: string;
  session_ids: string[];
  message: string;
}

export interface CSPResult {
  locked_session_ids: string[];
  violations: ConstraintViolation[];
  is_feasible: boolean;
}
