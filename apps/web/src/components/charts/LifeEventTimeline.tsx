"use client";

import { useMemo } from "react";
import { useChartEvents, type EventResponse } from "@/lib/events";

interface LifeEventTimelineProps {
  chartId: string;
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  } catch {
    return dateStr;
  }
}

const CATEGORY_COLORS: Record<string, string> = {
  career: "#38bdf8",
  marriage: "#f472b6",
  health: "#f87171",
  education: "#a78bfa",
  relocation: "#34d399",
  finance: "#fbbf24",
};

function categoryColor(category: string | null): string {
  if (!category) return "var(--accent)";
  return CATEGORY_COLORS[category.toLowerCase()] ?? "var(--accent)";
}

/**
 * LifeEventTimeline — renders the recorded life events for a chart
 * (from GET /api/v1/events?chart_id=..., Module 14's Event persistence
 * API) as a chronological vertical timeline.
 *
 * This shows only events that have actually been recorded for this chart
 * via the Events API. It does NOT fabricate example events — a fresh
 * chart with no recorded events renders an honest empty state instead of
 * a placeholder "Birth -> School -> Marriage" sample timeline.
 */
export function LifeEventTimeline({ chartId }: LifeEventTimelineProps) {
  const { data, isLoading, isError, error } = useChartEvents(chartId);

  const sortedEvents = useMemo(() => {
    if (!data?.events) return [];
    return [...data.events].sort(
      (a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime(),
    );
  }, [data]);

  return (
    <div className="glass-card space-y-4 p-5" role="region" aria-label="Life event timeline">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Life Event Timeline
        </h3>
        <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
          Events recorded for this chart, in chronological order.
        </p>
      </div>

      {isLoading && (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Loading recorded events…
        </p>
      )}

      {isError && (
        <p className="text-xs" style={{ color: "#f87171" }}>
          Could not load life events{error instanceof Error ? `: ${error.message}` : "."}
        </p>
      )}

      {!isLoading && !isError && sortedEvents.length === 0 && (
        <div
          className="rounded-lg border border-dashed p-4 text-xs"
          style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
        >
          No life events have been recorded for this chart yet. Once events are added (e.g. via
          the Events API), they will appear here in chronological order — this is not a
          placeholder for example data.
        </div>
      )}

      {!isLoading && !isError && sortedEvents.length > 0 && (
        <ol className="relative space-y-4 border-l pl-4" style={{ borderColor: "var(--border-primary)" }}>
          {sortedEvents.map((event: EventResponse) => (
            <li key={event.id} className="relative">
              <span
                className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: categoryColor(event.category) }}
                aria-hidden="true"
              />
              <div className="flex flex-wrap items-baseline gap-2">
                <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  {event.title}
                </span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {formatDate(event.event_date)}
                </span>
                {event.category && (
                  <span
                    className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
                    style={{ color: categoryColor(event.category), border: `1px solid ${categoryColor(event.category)}` }}
                  >
                    {event.category}
                  </span>
                )}
                {event.is_verified && (
                  <span className="text-[9px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                    verified
                  </span>
                )}
              </div>
              {event.description && (
                <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                  {event.description}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
