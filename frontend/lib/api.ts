import type {
  GeneratePlanRequest,
  Plan,
  ReplanRequest,
  ReplanResult,
} from "./types";

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

export function generatePlan(body: GeneratePlanRequest): Promise<Plan> {
  return request<Plan>("/plan/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function replan(body: ReplanRequest): Promise<ReplanResult> {
  return request<ReplanResult>("/plan/replan", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
