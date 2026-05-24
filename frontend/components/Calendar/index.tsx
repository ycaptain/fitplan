import type { ReplanDiff, ScheduledSession } from "@/lib/types";

export interface CalendarProps {
  sessions: ScheduledSession[];
  lockedSessionIds?: string[];
  highlightChanges?: ReplanDiff;
  onSessionClick?: (session: ScheduledSession) => void;
}

export default function Calendar(_props: CalendarProps) {
  return (
    <div className="rounded-md border border-slate-200 p-4">
      <p className="text-sm text-slate-500">Week calendar grid.</p>
    </div>
  );
}
