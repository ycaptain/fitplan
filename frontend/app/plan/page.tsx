"use client";

import { useState } from "react";
import Calendar, { selectionToEvent, type SelectionDraft } from "@/components/Calendar";
import { generatePlan, replan } from "@/lib/api";
import type {
  FixedEvent,
  GeneratePlanRequest,
  Plan,
  ReplanDiff,
  ScheduledSession,
  SplitName,
  StrategyStep,
} from "@/lib/types";

const SPLITS: Array<{ value: SplitName; label: string }> = [
  { value: "ppl", label: "Push / Pull / Legs" },
  { value: "upper_lower", label: "Upper / Lower" },
  { value: "full_body", label: "Full Body" },
];

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function PlanPage() {
  const [events, setEvents] = useState<FixedEvent[]>([]);
  const [split, setSplit] = useState<SplitName>("ppl");
  const [sessionsPerWeek, setSessionsPerWeek] = useState(4);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [diff, setDiff] = useState<ReplanDiff | null>(null);
  const [pendingEvent, setPendingEvent] = useState<FixedEvent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addEvent(draft: SelectionDraft) {
    const id = `evt-${Date.now()}`;
    const label = `Block ${events.length + 1}`;
    const event = selectionToEvent(draft, id, label);

    setEvents((prev) => [...prev, event]);

    if (plan && hasOverlap(plan.sessions, event)) {
      setPendingEvent(event);
    }
  }

  function removeEvent(id: string) {
    setEvents((prev) => prev.filter((e) => e.id !== id));
    if (pendingEvent?.id === id) {
      setPendingEvent(null);
    }
  }

  async function runGenerate() {
    const request: GeneratePlanRequest = {
      goal: "general",
      split,
      sessions_per_week: sessionsPerWeek,
      fixed_events: events,
      preferences: {
        preferred_time_of_day: "any",
        max_session_duration_min: 90,
      },
    };

    setLoading(true);
    setError(null);
    setDiff(null);
    setPendingEvent(null);

    try {
      setPlan(await generatePlan(request));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generate failed");
    } finally {
      setLoading(false);
    }
  }

  async function runReplan() {
    if (!plan || !pendingEvent) return;

    setLoading(true);
    setError(null);

    try {
      const result = await replan({
        plan_id: plan.id,
        trigger_type: "fixed_event_added",
        mode: "minimal_disruption",
        payload: {
          id: pendingEvent.id,
          day_of_week: pendingEvent.day_of_week,
          start: pendingEvent.start,
          end: pendingEvent.end,
          label: pendingEvent.label,
        },
      });
      setPlan(result.plan);
      setDiff(result.diff);
      setPendingEvent(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Replan failed");
    } finally {
      setLoading(false);
    }
  }

  const lastStep = plan?.strategy_trace.at(-1);
  const overlappedIds = pendingEvent
    ? plan?.sessions.filter((s) => sessionOverlapsEvent(s, pendingEvent)).map((s) => s.id) ?? []
    : [];

  return (
    <main className="mx-auto max-w-7xl space-y-4 p-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-slate-950">
            Drag to block time, then generate a plan
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Step 1: drag your meetings and classes, click Generate (CSP). Step 2:
            after the plan exists, drag a new block onto an existing workout to
            trigger Replan (Hill Climbing).
          </p>
        </div>
        <Stats plan={plan} lastStep={lastStep} diff={diff} />
      </header>

      {pendingEvent ? (
        <ConflictBanner
          event={pendingEvent}
          overlappedIds={overlappedIds}
          loading={loading}
          onReplan={runReplan}
          onDismiss={() => setPendingEvent(null)}
        />
      ) : null}

      <section className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 lg:grid-cols-[1fr_280px]">
        <Calendar
          sessions={plan?.sessions ?? []}
          events={events}
          highlightChanges={diff ?? undefined}
          onCreateEvent={addEvent}
          onRemoveEvent={removeEvent}
        />

        <aside className="space-y-4">
          <Field label="Split">
            <select
              value={split}
              onChange={(e) => setSplit(e.target.value as SplitName)}
              className="w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm"
            >
              {SPLITS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Sessions / week">
            <input
              type="number"
              min={2}
              max={6}
              value={sessionsPerWeek}
              onChange={(e) => setSessionsPerWeek(Number(e.target.value))}
              className="w-full rounded-md border border-slate-200 px-2 py-1.5 text-sm"
            />
          </Field>

          <button
            type="button"
            onClick={runGenerate}
            disabled={loading}
            className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {loading ? "Working…" : "Generate plan"}
          </button>

          {error ? (
            <p className="rounded-md bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>
          ) : null}

          {events.length > 0 ? (
            <EventList events={events} onRemove={removeEvent} />
          ) : (
            <p className="text-xs text-slate-400">
              Drag on the calendar to add a busy block.
            </p>
          )}

          {plan ? (
            <p className="text-[11px] leading-relaxed text-slate-400">
              Need replan? Drop a block on a green workout (e.g. a new meeting on the
              same day) and the Replan banner will appear.
            </p>
          ) : null}
        </aside>
      </section>
    </main>
  );
}

function Stats({
  plan,
  lastStep,
  diff,
}: {
  plan: Plan | null;
  lastStep?: StrategyStep;
  diff: ReplanDiff | null;
}) {
  if (!plan) {
    return (
      <p className="text-xs text-slate-400">
        No plan yet · drag a block, click Generate
      </p>
    );
  }

  const role = lastStep?.role;
  const movedCount = diff ? diff.moved.length + diff.added.length + diff.removed.length : 0;

  return (
    <dl className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
      <Stat label="Algorithm" value={formatAlgorithm(lastStep?.algorithm)} />
      <Stat label="Step" value={role ?? "-"} />
      <Stat label="Time" value={formatTime(lastStep?.time_ms)} />
      <Stat label="Sessions" value={String(plan.sessions.length)} />
      <Stat label="Score" value={String(plan.scores.total)} />
      {diff ? <Stat label="Moved" value={String(movedCount)} /> : null}
    </dl>
  );
}

function ConflictBanner({
  event,
  overlappedIds,
  loading,
  onReplan,
  onDismiss,
}: {
  event: FixedEvent;
  overlappedIds: string[];
  loading: boolean;
  onReplan: () => void;
  onDismiss: () => void;
}) {
  const target = overlappedIds[0] ?? "an existing session";
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3">
      <div className="text-sm text-amber-900">
        New block on {DAY_LABELS[event.day_of_week]} {event.start}-{event.end} conflicts with{" "}
        <span className="font-medium">{target}</span>.
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-md border border-amber-300 px-3 py-1.5 text-xs text-amber-900 hover:bg-amber-100"
        >
          Skip
        </button>
        <button
          type="button"
          onClick={onReplan}
          disabled={loading}
          className="rounded-md bg-amber-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-800 disabled:cursor-not-allowed disabled:bg-amber-300"
        >
          {loading ? "Replanning…" : "Replan with Hill Climbing"}
        </button>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="text-sm font-semibold text-slate-900">{value}</dd>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[11px] uppercase tracking-wide text-slate-500">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

function EventList({
  events,
  onRemove,
}: {
  events: FixedEvent[];
  onRemove: (id: string) => void;
}) {
  return (
    <ul className="space-y-1 text-xs">
      {events.map((event) => (
        <li
          key={event.id}
          className="flex items-center justify-between gap-2 rounded-md bg-rose-50 px-2 py-1.5 text-rose-900"
        >
          <span>
            {DAY_LABELS[event.day_of_week]} {event.start}-{event.end}
          </span>
          <button
            type="button"
            onClick={() => onRemove(event.id)}
            className="text-rose-600 hover:text-rose-900"
          >
            remove
          </button>
        </li>
      ))}
    </ul>
  );
}

function hasOverlap(sessions: ScheduledSession[], event: FixedEvent) {
  return sessions.some((session) => sessionOverlapsEvent(session, event));
}

function sessionOverlapsEvent(session: ScheduledSession, event: FixedEvent) {
  if (session.day !== event.day_of_week) return false;
  const sStart = toMinutes(session.start);
  const sEnd = sStart + session.duration_min;
  const eStart = toMinutes(event.start);
  const eEnd = toMinutes(event.end);
  return sStart < eEnd && eStart < sEnd;
}

function toMinutes(hhmm: string) {
  const [h, m] = hhmm.split(":");
  return Number(h) * 60 + Number(m);
}

function formatAlgorithm(algorithm?: string) {
  if (!algorithm) return "csp";
  if (algorithm.startsWith("csp_backtracking")) return "CSP backtracking + FC";
  if (algorithm === "hill_climbing") return "Hill Climbing";
  if (algorithm === "csp_stub") return "CSP re-validation";
  return algorithm.replace(/_/g, " ");
}

function formatTime(ms?: number) {
  if (ms === undefined) return "—";
  if (ms < 1) return "<1ms";
  return `${ms}ms`;
}
