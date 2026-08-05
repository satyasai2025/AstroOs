"use client";

import type { CategoryTotal } from "@/lib/predictions/types";

interface PredictionScoreBreakdownProps {
  categories: CategoryTotal[];
  baseline: number;
  finalScore: number;
}

const POSITIVE = "#34d399";
const NEGATIVE = "#f87171";

/**
 * PredictionScoreBreakdown — render-only. `categories` is derived by
 * chainEngine.ts from whatever nodes exist in the graph (grouped by
 * `.category`, summed) — this component never hardcodes a category list,
 * so a newly-added factor's category shows up automatically.
 */
export function PredictionScoreBreakdown({ categories, baseline, finalScore }: PredictionScoreBreakdownProps) {
  const maxAbs = Math.max(...categories.map((c) => Math.abs(c.delta)), 1);

  return (
    <div className="glass-card flex flex-col gap-3 p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        Score Breakdown
      </h3>

      <div className="flex items-center justify-between text-xs">
        <span style={{ color: "var(--text-muted)" }}>Baseline</span>
        <span style={{ color: "var(--text-primary)" }}>{baseline}</span>
      </div>

      {categories.map((c) => {
        const color = c.delta > 0 ? POSITIVE : c.delta < 0 ? NEGATIVE : "var(--text-muted)";
        const width = (Math.abs(c.delta) / maxAbs) * 100;
        return (
          <div key={c.category}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span style={{ color: "var(--text-secondary)" }}>{c.category}</span>
              <span style={{ color }}>
                {c.delta >= 0 ? "+" : ""}
                {Math.round(c.delta * 10) / 10}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <div className="h-full rounded-full" style={{ width: `${width}%`, backgroundColor: color }} />
            </div>
          </div>
        );
      })}

      <div className="mt-1 flex items-center justify-between border-t pt-3 text-sm font-semibold" style={{ borderColor: "var(--border-primary)" }}>
        <span style={{ color: "var(--text-primary)" }}>Total</span>
        <span style={{ color: "var(--accent)" }}>{finalScore}</span>
      </div>
    </div>
  );
}
