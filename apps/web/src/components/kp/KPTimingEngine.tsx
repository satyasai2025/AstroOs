"use client";

/**
 * KP Timing Engine — for each event, whether its strongest significator's
 * own Dasha/Bhukti period is active right now (real data from the chart's
 * dasha tree). Per the KP principle, timing is only shown AFTER a
 * positive promise — this panel is deliberately read together with
 * KPEventExplorer.
 */

import { useMemo } from "react";
import { computeTimingWindows } from "@/lib/kpAnalysis";
import type { D1ChartResponse, DashaTreeResponse } from "@/lib/types";

interface Props {
  chart: D1ChartResponse;
  dasha: DashaTreeResponse;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function KPTimingEngine({ chart, dasha }: Props) {
  const windows = useMemo(() => computeTimingWindows(chart, dasha), [chart, dasha]);

  return (
    <div className="space-y-4">
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        Timing windows for each event&apos;s strongest significator: whether that planet&apos;s own
        Dasha/Bhukti level is running today, from this chart&apos;s actual dasha tree (Vimshottari
        Mahadasha → Antardasha → Pratyantardasha …). Classical KP reads these windows as the period
        when a promised event is most likely to fructify.
      </p>
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        {windows.map((w) => (
          <div key={w.eventKey} className="glass-card p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{w.label}</span>
              {w.active_level ? (
                <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: "rgba(52,211,153,0.15)", color: "#34d399" }}>
                  Active Now
                </span>
              ) : (
                <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: "rgba(248,113,113,0.15)", color: "#f87171" }}>
                  Not Active
                </span>
              )}
            </div>
            <dl className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Significator</dt><dd className="font-semibold" style={{ color: "var(--accent)" }}>{w.significator}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Active Dasha Level</dt><dd>{w.active_level ?? "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Window Start</dt><dd>{formatDate(w.start_date)}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Window End</dt><dd>{formatDate(w.end_date)}</dd></div>
            </dl>
          </div>
        ))}
      </div>
      <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
        Scope: timing never manufactures an event the promise engine doesn&apos;t support — read these
        windows alongside the Event Explorer&apos;s verdict.
      </p>
    </div>
  );
}
