"use client";

import type { DataSourceEntry } from "@/lib/predictions/types";

interface PredictionDataSourcesProps {
  sources: DataSourceEntry[];
}

/**
 * PredictionDataSources — render-only checklist, one row per applicable
 * factor in the graph (chainEngine.ts's dataSourcesFromNodes). Missing
 * data is shown explicitly with its reason, never silently dropped.
 */
export function PredictionDataSources({ sources }: PredictionDataSourcesProps) {
  return (
    <div className="glass-card flex flex-col gap-2 p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        Data Sources
      </h3>
      <ul className="flex flex-col gap-1.5">
        {sources.map((s) => (
          <li key={s.id} className="flex items-start gap-2 text-xs" title={s.reason}>
            <span className="mt-0.5" style={{ color: s.available ? "#34d399" : "var(--text-muted)" }}>
              {s.available ? "✓" : "✗"}
            </span>
            <span style={{ color: s.available ? "var(--text-secondary)" : "var(--text-muted)" }}>
              {s.label}
              {!s.available && s.reason ? ` — ${s.reason}` : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
