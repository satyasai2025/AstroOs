"use client";

import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import type { ShadbalaTotalResponse } from "@/lib/types";

interface PlanetStrengthHeatmapProps {
  shadbala: ShadbalaTotalResponse[];
}

/**
 * Horizontal bar "heatmap" of each planet's total Shadbala (in rupas) —
 * the vision doc's "Sun ███████ / Moon █████" style bars, done with CSS
 * width bars instead of unicode blocks so exact values render cleanly.
 *
 * Bars are scaled relative to the strongest planet in *this* chart, not
 * against a fixed classical maximum — that keeps the bars meaningful
 * chart-to-chart without guessing at per-planet minimum-required-strength
 * thresholds the backend doesn't expose yet.
 */
export function PlanetStrengthHeatmap({ shadbala }: PlanetStrengthHeatmapProps) {
  if (shadbala.length === 0) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No Shadbala data available for this chart.
      </div>
    );
  }

  const maxRupas = Math.max(...shadbala.map((s) => s.total_rupas), 0.01);

  return (
    <div className="glass-card p-5">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Planet Strength (Shadbala)
      </h3>
      <div className="space-y-3">
        {shadbala.map((s) => {
          const pct = Math.max(4, (s.total_rupas / maxRupas) * 100);
          return (
            <div key={s.planet} className="flex items-center gap-3">
              <span
                className="w-20 flex-shrink-0 text-xs font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                {PLANET_SYMBOLS[s.planet] ?? ""} {PLANET_ABBREV[s.planet] ?? s.planet.slice(0, 2)}
              </span>
              <div
                className="h-3 flex-1 overflow-hidden rounded-full"
                style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
                role="img"
                aria-label={`${s.planet} strength: ${s.total_rupas.toFixed(2)} rupas`}
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: "var(--accent)" }}
                />
              </div>
              <span
                className="w-16 flex-shrink-0 text-right text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                {s.total_rupas.toFixed(2)}
              </span>
            </div>
          );
        })}
      </div>
      <p className="mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
        Values in rupas, scaled relative to the strongest planet in this chart.
      </p>
    </div>
  );
}
