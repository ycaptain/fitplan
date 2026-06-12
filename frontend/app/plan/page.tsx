"use client";

import { useEffect, useState } from "react";
import Calendar, {
  selectionToEvent,
  type SelectionDraft,
} from "@/components/Calendar";
import { generatePlan, replan } from "@/lib/api";
import { loadPrefs } from "@/lib/onboarding";
import type {
  FixedEvent,
  GeneratePlanRequest,
  Goal,
  Plan,
  PlanExplanation,
  ReplanDiff,
  ReplanMode,
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
  const [goal, setGoal] = useState<Goal>("general");
  const [preferredTime, setPreferredTime] = useState<
    "morning" | "evening" | "any"
  >("any");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [diff, setDiff] = useState<ReplanDiff | null>(null);
  const [explanation, setExplanation] = useState<PlanExplanation | null>(null);
  const [pendingEvent, setPendingEvent] = useState<FixedEvent | null>(null);
  const [replanMode, setReplanMode] = useState<ReplanMode>("re_optimize");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const prefs = loadPrefs();
    if (!prefs) return;
    setGoal(prefs.goal);
    setSplit(prefs.split);
    setSessionsPerWeek(prefs.sessions_per_week);
    setPreferredTime(prefs.preferred_time_of_day);
  }, []);

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
      goal,
      split,
      sessions_per_week: sessionsPerWeek,
      fixed_events: events,
      preferences: {
        preferred_time_of_day: preferredTime,
        max_session_duration_min: 90,
      },
    };

    setLoading(true);
    setError(null);
    setDiff(null);
    setPendingEvent(null);

    try {
      const generated = await generatePlan(request);
      setPlan(generated);
      setExplanation(generated.explanation ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generate failed");
    } finally {
      setLoading(false);
    }
  }

  async function runOptimize() {
    if (!plan) return;
    setLoading(true);
    setError(null);
    try {
      const isoDate = new Date().toISOString().slice(0, 10);
      const result = await replan({
        plan_id: plan.id,
        trigger_type: "state_changed",
        mode: "re_optimize",
        payload: {
          date: isoDate,
          sleep_hours: 8,
          perceived_fatigue: 0,
          missed_last_session: false,
        },
        fixed_events: events,
      });
      setPlan(result.plan);
      setDiff(result.diff);
      setExplanation(result.explanation ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimize failed");
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
        mode: replanMode,
        payload: {
          id: pendingEvent.id,
          day_of_week: pendingEvent.day_of_week,
          start: pendingEvent.start,
          end: pendingEvent.end,
          label: pendingEvent.label,
        },
        // Send the full local list so any blocks the user added without
        // replanning (or removed locally) remain authoritative on the server.
        fixed_events: events,
      });
      setPlan(result.plan);
      setDiff(result.diff);
      setExplanation(result.explanation ?? null);
      setPendingEvent(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Replan failed");
    } finally {
      setLoading(false);
    }
  }

  const lastStep = plan?.strategy_trace.at(-1);
  const overlappedIds = pendingEvent
    ? (plan?.sessions
        .filter((s) => sessionOverlapsEvent(s, pendingEvent))
        .map((s) => s.id) ?? [])
    : [];

  return (
    <main className="mx-auto max-w-6xl space-y-4 p-6 text-slate-900">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold">Weekly workout plan</h1>
        <p className="text-sm text-slate-700">
          1) Drag on the calendar to mark busy time. 2) Pick a split and click
          Generate. 3) Add a new block that overlaps a workout to trigger
          replan.
        </p>
      </header>

      <Stats plan={plan} lastStep={lastStep} diff={diff} />

      <ExplanationPanel explanation={explanation} />

      {pendingEvent ? (
        <ConflictBanner
          event={pendingEvent}
          overlappedIds={overlappedIds}
          loading={loading}
          onReplan={runReplan}
          onDismiss={() => setPendingEvent(null)}
        />
      ) : null}

      <section className="grid gap-4 rounded-lg border border-slate-300 bg-white p-4 lg:grid-cols-[1fr_260px]">
        <Calendar
          sessions={plan?.sessions ?? []}
          events={events}
          highlightChanges={diff ?? undefined}
          onCreateEvent={addEvent}
          onRemoveEvent={removeEvent}
        />

        <aside className="space-y-3">
          <Field label="Split">
            <select
              value={split}
              onChange={(e) => setSplit(e.target.value as SplitName)}
              className="w-full rounded border border-slate-400 bg-white px-2 py-1.5 text-sm text-slate-900"
            >
              {SPLITS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Sessions per week">
            <input
              type="number"
              min={2}
              max={6}
              value={sessionsPerWeek}
              onChange={(e) => setSessionsPerWeek(Number(e.target.value))}
              className="w-full rounded border border-slate-400 bg-white px-2 py-1.5 text-sm text-slate-900"
            />
          </Field>

          <Field label="Replan mode">
            <select
              value={replanMode}
              onChange={(e) => setReplanMode(e.target.value as ReplanMode)}
              className="w-full rounded border border-slate-400 bg-white px-2 py-1.5 text-sm text-slate-900"
            >
              <option value="minimal_disruption">Minimal disruption</option>
              <option value="re_optimize">Re-optimize</option>
            </select>
          </Field>

          <p className="text-xs text-slate-600">
            Goal: <span className="font-semibold capitalize">{goal}</span> ·
            Time:{" "}
            <span className="font-semibold capitalize">{preferredTime}</span>{" "}
            <a href="/onboarding" className="underline">
              edit
            </a>
          </p>

          <button
            type="button"
            onClick={runGenerate}
            disabled={loading}
            className="w-full rounded bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {loading ? "Working…" : "Generate plan"}
          </button>

          {plan && !pendingEvent ? (
            <button
              type="button"
              onClick={runOptimize}
              disabled={loading}
              className="w-full rounded border border-slate-400 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
            >
              {loading ? "Working…" : "Optimize plan"}
            </button>
          ) : null}

          {error ? (
            <p className="rounded border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-800">
              {error}
            </p>
          ) : null}

          {events.length > 0 ? (
            <EventList events={events} onRemove={removeEvent} />
          ) : (
            <p className="text-xs text-slate-600">
              Tip: drag on the calendar to mark a busy block.
            </p>
          )}
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
      <p className="text-sm text-slate-600">
        No plan yet. Mark busy time, then click Generate.
      </p>
    );
  }

  const movedCount = diff
    ? diff.moved.length + diff.added.length + diff.removed.length
    : 0;

  return (
    <dl className="flex flex-wrap gap-x-6 gap-y-2 rounded border border-slate-300 bg-white px-4 py-2 text-sm text-slate-800">
      <Stat label="Algorithm" value={formatAlgorithm(lastStep?.algorithm)} />
      <Stat label="Time" value={formatTime(lastStep?.time_ms)} />
      <Stat label="Sessions" value={String(plan.sessions.length)} />
      <Stat label="Score" value={String(plan.scores.total)} />
      {diff ? <Stat label="Moved" value={String(movedCount)} /> : null}
    </dl>
  );
}

function ExplanationPanel({
  explanation,
}: {
  explanation: PlanExplanation | null;
}) {
  if (!explanation) return null;

  return (
    <section className="space-y-2 rounded border border-slate-300 bg-white px-4 py-3 text-sm">
      <p className="text-slate-800">{explanation.text_summary}</p>
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-xs">
        {explanation.constraint_hits.map((hit) => (
          <li key={hit.constraint_id} className="flex items-center gap-1.5">
            <span
              aria-hidden
              className={hit.satisfied ? "text-emerald-600" : "text-rose-600"}
            >
              {hit.satisfied ? "✓" : "✗"}
            </span>
            <span
              className={
                hit.satisfied ? "text-slate-600" : "font-medium text-rose-800"
              }
              title={hit.explanation}
            >
              {hit.constraint_id.replace(/_/g, " ")}
            </span>
          </li>
        ))}
      </ul>
    </section>
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
    <div className="flex flex-wrap items-center justify-between gap-3 rounded border border-amber-400 bg-amber-100 px-4 py-3">
      <div className="text-sm text-amber-950">
        New block on {DAY_LABELS[event.day_of_week]} {event.start}-{event.end}{" "}
        conflicts with <span className="font-semibold">{target}</span>.
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onDismiss}
          className="rounded border border-amber-500 bg-white px-3 py-1.5 text-xs text-amber-900 hover:bg-amber-50"
        >
          Skip
        </button>
        <button
          type="button"
          onClick={onReplan}
          disabled={loading}
          className="rounded bg-amber-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-800 disabled:cursor-not-allowed disabled:bg-amber-400"
        >
          {loading ? "Replanning…" : "Replan"}
        </button>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <dt className="text-slate-600">{label}:</dt>
      <dd className="font-semibold text-slate-900">{value}</dd>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1 text-sm text-slate-800">
      <span>{label}</span>
      {children}
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
      <li className="text-slate-700">Busy blocks:</li>
      {events.map((event) => (
        <li
          key={event.id}
          className="flex items-center justify-between gap-2 rounded border border-rose-300 bg-rose-50 px-2 py-1.5 text-rose-900"
        >
          <span>
            {DAY_LABELS[event.day_of_week]} {event.start}-{event.end}
          </span>
          <button
            type="button"
            onClick={() => onRemove(event.id)}
            className="text-rose-700 underline hover:text-rose-900"
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
  if (algorithm === "simulated_annealing") return "Simulated Annealing";
  if (algorithm === "csp_bt_fc") return "CSP re-validation";
  return algorithm.replace(/_/g, " ");
}

function formatTime(ms?: number) {
  if (ms === undefined) return "—";
  if (ms < 1) return "<1ms";
  return `${ms}ms`;
}
