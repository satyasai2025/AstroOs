"use client";

import type { DashaTimelineEntry } from "@/lib/predictions/types";

interface PredictionDashaTimelineProps {
  entries: DashaTimelineEntry[];
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short" });
  } catch {
    return iso;
  }
}

/**
 * PredictionDashaTimeline — real Mahadasha periods (dasha.mahadashas),
 * current one highlighted. Deliberately NOT the mockup's fabricated
 * 2018→2028 score curve — this app doesn't recompute the chart at
 * arbitrary past/future transit dates, so a numeric score-over-time graph
 * would have to be invented. Real dates for real periods instead.
 */
export function PredictionDashaTimeline({ entries }: PredictionDashaTimelineProps) {
  return (
    <div className="glass-card flex flex-col gap-2 p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        Mahadasha Timeline
      </h3>
      <div className="flex flex-col">
        {entries.map((e, i) => (
          <div key={`${e.lord}-${e.startDate}`} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span
                className="mt-1 h-2.5 w-2.5 flex-shrink-0 rounded-full"
                style={{
                  backgroundColor: e.isCurrent ? "var(--accent)" : "var(--border-primary)",
                  boxShadow: e.isCurrent ? "0 0 8px var(--accent)" : "none",
                }}
              />
              {i < entries.length - 1 && <div className="w-px flex-1" style={{ backgroundColor: "var(--border-primary)", minHeight: 20 }} />}
            </div>
            <div className="pb-3">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium" style={{ color: e.isCurrent ? "var(--accent)" : "var(--text-primary)" }}>
                  {e.lord}
                </span>
                {e.isCurrent && (
                  <span className="rounded-full px-1.5 py-0.5 text-[9px] font-semibold" style={{ color: "var(--accent)", border: "1px solid var(--accent)" }}>
                    Current
                  </span>
                )}
              </div>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {formatDate(e.startDate)} – {formatDate(e.endDate)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
