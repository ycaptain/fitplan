import type { Plan, PlanDelta, ReplanResult, TriggerType } from "./types";

const BASE = "/api";

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface GeneratePlanRequest {
  goal: string;
  split: string;
  sessions_per_week: number;
}

export interface GeneratePlanResponseStub {
  plan_id: string;
  message: string;
}

export function generatePlan(
  body: GeneratePlanRequest,
): Promise<GeneratePlanResponseStub> {
  return request<GeneratePlanResponseStub>("/plan/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export interface ReplanRequest {
  plan_id: string;
  trigger_type: TriggerType;
  payload: Record<string, unknown>;
}

export interface ReplanResponseStub {
  plan_id: string;
  message: string;
  diff: { moved: string[]; removed: string[]; added: string[] };
}

export function replan(body: ReplanRequest): Promise<ReplanResponseStub> {
  return request<ReplanResponseStub>("/plan/replan", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type _ReservedShapes = Plan | ReplanResult | PlanDelta;
