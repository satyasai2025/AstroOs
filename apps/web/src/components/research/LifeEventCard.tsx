import type { LifeEventDetail } from "@/lib/types";
import { formatEventTitle } from "@/lib/astro";

const SEVERITY_TONE: Record<string, string> = {
  major: "border-l-rose-400",
  moderate: "border-l-amber-400",
  minor: "border-l-slate-300 dark:border-l-slate-700",
};

export interface LifeEventCardProps {
  event: LifeEventDetail;
  /** True when every event in this case shares the same fallback date
   * (no genuine per-event date data) — shown as an honest "(fallback)"
   * label instead of implying a real, distinct event date. */
  sharedFallbackDate: boolean;
}

export function LifeEventCard({ event, sharedFallbackDate }: LifeEventCardProps) {
  const rawTitle = event.description || event.event_type || event.category || "Life event";
  const cleanTitle = formatEventTitle(rawTitle);

  return (
    <div
      className={`rounded-lg border-l-4 ${SEVERITY_TONE[event.severity] ?? SEVERITY_TONE.moderate} bg-white dark:bg-slate-900/90 border-y border-r border-slate-200 dark:border-slate-800 p-3`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
            {cleanTitle}
          </p>
          {event.notes && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{event.notes}</p>
          )}
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs font-mono text-cyan-600 dark:text-cyan-400">{event.event_date}</p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500">(event date)</p>
        </div>
      </div>
    </div>
  );
}
