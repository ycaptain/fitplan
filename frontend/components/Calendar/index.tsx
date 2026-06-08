"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { FixedEvent, ReplanDiff, ScheduledSession } from "@/lib/types";

export interface SelectionDraft {
  day: number;
  startMin: number;
  endMin: number;
}

export interface CalendarProps {
  sessions?: ScheduledSession[];
  events?: FixedEvent[];
  highlightChanges?: ReplanDiff;
  onCreateEvent?: (draft: SelectionDraft) => void;
  onRemoveEvent?: (eventId: string) => void;
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const START_HOUR = 6;
const END_HOUR = 22;
const HOUR_PX = 36;
const SNAP_MIN = 30;

const HOURS = Array.from(
  { length: END_HOUR - START_HOUR + 1 },
  (_, i) => START_HOUR + i,
);

export default function Calendar({
  sessions = [],
  events = [],
  highlightChanges,
  onCreateEvent,
  onRemoveEvent,
}: CalendarProps) {
  const moved = useMemo(
    () => new Set(highlightChanges?.moved ?? []),
    [highlightChanges],
  );
  const added = useMemo(
    () => new Set(highlightChanges?.added ?? []),
    [highlightChanges],
  );
  const removed = useMemo(
    () => new Set(highlightChanges?.removed ?? []),
    [highlightChanges],
  );
  const interactive = Boolean(onCreateEvent);
  const gridRef = useRef<HTMLDivElement | null>(null);
  const [draft, setDraft] = useState<SelectionDraft | null>(null);
  const dragOriginMin = useRef<number | null>(null);

  const resolvePoint = useCallback((clientX: number, clientY: number) => {
    const grid = gridRef.current;
    if (!grid) return null;

    const rect = grid.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    if (x < 0 || y < 0 || x > rect.width || y > rect.height) return null;

    const day = Math.min(6, Math.max(0, Math.floor((x / rect.width) * 7)));
    const totalMinutes = (END_HOUR - START_HOUR + 1) * 60;
    const minutesFromStart = Math.max(
      0,
      Math.min(totalMinutes - SNAP_MIN, (y / rect.height) * totalMinutes),
    );
    const snapped = Math.round(minutesFromStart / SNAP_MIN) * SNAP_MIN;
    return { day, minutes: START_HOUR * 60 + snapped };
  }, []);

  const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!interactive) return;
    if ((event.target as HTMLElement).closest("[data-event-block]")) return;

    const point = resolvePoint(event.clientX, event.clientY);
    if (!point) return;

    event.currentTarget.setPointerCapture(event.pointerId);
    dragOriginMin.current = point.minutes;
    setDraft({
      day: point.day,
      startMin: point.minutes,
      endMin: point.minutes + SNAP_MIN,
    });
  };

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!interactive || dragOriginMin.current === null) return;

    const point = resolvePoint(event.clientX, event.clientY);
    if (!point || !draft) return;

    const origin = dragOriginMin.current;
    const endMin = Math.max(point.minutes + SNAP_MIN, origin + SNAP_MIN);
    setDraft({
      day: draft.day,
      startMin: Math.min(origin, point.minutes),
      endMin,
    });
  };

  const handlePointerUp = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!interactive || dragOriginMin.current === null) return;

    event.currentTarget.releasePointerCapture(event.pointerId);
    dragOriginMin.current = null;

    if (draft && draft.endMin > draft.startMin) {
      onCreateEvent?.(draft);
    }
    setDraft(null);
  };

  const totalHeight = (END_HOUR - START_HOUR + 1) * HOUR_PX;
  const sessionBlocks = useMemo(() => sessions.map(sessionToBlock), [sessions]);
  const sessionsPerDay = useMemo(() => {
    const counts = new Map<number, number>();
    for (const session of sessions) {
      counts.set(session.day, (counts.get(session.day) ?? 0) + 1);
    }
    return counts;
  }, [sessions]);

  return (
    <div className="flex select-none text-slate-900">
      <div className="w-12 shrink-0 pr-2 pt-6 text-right text-xs text-slate-600">
        {HOURS.map((hour) => (
          <div key={hour} style={{ height: HOUR_PX }}>
            {formatHour(hour)}
          </div>
        ))}
      </div>

      <div className="flex-1">
        <div className="grid grid-cols-7 border-b border-slate-400 text-center text-sm font-semibold text-slate-800">
          {DAY_LABELS.map((label, day) => {
            const count = sessionsPerDay.get(day) ?? 0;
            return (
              <div
                key={label}
                className="flex items-center justify-center gap-1 py-1"
              >
                {label}
                {count > 1 ? (
                  <span
                    className="rounded bg-amber-200 px-1 text-[10px] font-bold text-amber-900"
                    title={`${count} sessions on one day — soft overload penalty applies`}
                  >
                    ×{count}
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>

        <div
          ref={gridRef}
          className={[
            "relative grid grid-cols-7 border-l border-slate-300",
            interactive ? "cursor-crosshair" : "",
          ].join(" ")}
          style={{ height: totalHeight }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        >
          {DAY_LABELS.map((label, day) => (
            <div key={label} className="relative border-r border-slate-300">
              {HOURS.map((hour) => (
                <div
                  key={hour}
                  className="border-b border-slate-200"
                  style={{ height: HOUR_PX }}
                />
              ))}

              {events
                .filter((e) => e.day_of_week === day)
                .map((event) => (
                  <Block
                    key={event.id}
                    top={minutesOffset(toMinutes(event.start))}
                    height={blockHeight(
                      toMinutes(event.start),
                      toMinutes(event.end),
                    )}
                    tone="event"
                    onDismiss={
                      onRemoveEvent ? () => onRemoveEvent(event.id) : undefined
                    }
                  >
                    <p className="truncate font-semibold">{event.label}</p>
                    <p className="truncate text-[11px]">
                      {event.start}-{event.end}
                    </p>
                  </Block>
                ))}

              {sessionBlocks
                .filter((block) => block.day === day)
                .map((block) => (
                  <Block
                    key={block.id}
                    top={block.top}
                    height={block.height}
                    tone={
                      moved.has(block.id) ||
                      added.has(block.id) ||
                      removed.has(block.id)
                        ? "session-moved"
                        : "session"
                    }
                  >
                    <p className="truncate font-semibold capitalize">
                      {block.label}
                    </p>
                    <p className="truncate text-[11px]">
                      {block.startLabel} · {block.durationLabel}
                    </p>
                  </Block>
                ))}

              {draft && draft.day === day ? (
                <div
                  className="pointer-events-none absolute inset-x-1 rounded border-2 border-dashed border-slate-600 bg-slate-300/60"
                  style={{
                    top: minutesOffset(draft.startMin),
                    height: blockHeight(draft.startMin, draft.endMin),
                  }}
                />
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Block({
  top,
  height,
  tone,
  onDismiss,
  children,
}: {
  top: number;
  height: number;
  tone: "session" | "session-moved" | "event";
  onDismiss?: () => void;
  children: React.ReactNode;
}) {
  const colors =
    tone === "event"
      ? "bg-rose-200 border-rose-500 text-rose-950"
      : tone === "session-moved"
        ? "bg-amber-200 border-amber-600 text-amber-950"
        : "bg-emerald-200 border-emerald-600 text-emerald-950";

  return (
    <div
      data-event-block={tone}
      className={`absolute inset-x-1 rounded border px-2 py-1 text-xs ${colors}`}
      style={{ top, height }}
    >
      {onDismiss ? (
        <button
          type="button"
          onClick={onDismiss}
          className="absolute right-1 top-1 rounded bg-white/80 px-1 text-[10px] font-bold text-rose-800 hover:bg-white"
        >
          ×
        </button>
      ) : null}
      {children}
    </div>
  );
}

function sessionToBlock(session: ScheduledSession) {
  const startMin = toMinutes(session.start);
  const endMin = startMin + session.duration_min;
  return {
    id: session.id,
    day: session.day,
    label: session.session_type_id.replaceAll("_", " "),
    startLabel: session.start,
    durationLabel: `${session.duration_min} min`,
    top: minutesOffset(startMin),
    height: blockHeight(startMin, endMin),
  };
}

function toMinutes(hhmm: string) {
  const [h, m] = hhmm.split(":");
  return Number(h) * 60 + Number(m);
}

function minutesOffset(minutes: number) {
  return ((minutes - START_HOUR * 60) / 60) * HOUR_PX;
}

function blockHeight(startMin: number, endMin: number) {
  return Math.max(HOUR_PX * 0.5, ((endMin - startMin) / 60) * HOUR_PX);
}

function formatHour(hour: number) {
  return `${String(hour).padStart(2, "0")}:00`;
}

export function selectionToEvent(
  draft: SelectionDraft,
  id: string,
  label: string,
): FixedEvent {
  return {
    id,
    day_of_week: draft.day,
    start: formatTime(draft.startMin),
    end: formatTime(draft.endMin),
    label,
  };
}

function formatTime(minutes: number) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}
