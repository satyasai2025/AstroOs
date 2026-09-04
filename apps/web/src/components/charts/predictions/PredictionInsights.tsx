"use client";

/**
 * AstroOS — Prediction Chain Explorer: Phase 7 visual summaries
 *
 * All four visuals below are derived purely from PredictionGraph objects
 * already produced by chainEngine.ts (real per-factor deltas, real
 * dataSources/confidence, real dasha timeline, real matched yogas) — no
 * backend changes, no fabricated per-period recomputation. Where the
 * underlying data doesn't vary by a dimension the screenshot implies (e.g.
 * a factor's score doesn't change per dasha sub-period in this model), the
 * same real score is shown across that dimension rather than inventing a
 * number, and the current dasha period is marked distinctly.
 */

import { useMemo, useState } from "react";
import type { LifeArea } from "@/lib/predictions/types";
import type { DashaTimelineEntry, PredictionGraph } from "@/lib/predictions/types";

export interface AreaGraphEntry {
  area: LifeArea;
  label: string;
  graph: PredictionGraph;
}

const CATEGORY_AXES = ["House Strength", "Planet Strength", "Aspects", "Yogas", "Dasha", "Transit", "Avastha", "Karakas"];

function scoreColor(score: number): string {
  if (score >= 75) return "#34d399";
  if (score >= 50) return "#a3e635";
  if (score >= 25) return "#fbbf24";
  return "#f87171";
}

function scoreBg(score: number): string {
  return `${scoreColor(score)}33`;
}

/* ── 1. Confidence Heatmap: Life Areas × Dasha Mahadasha windows ──────── */
export function ConfidenceHeatmap({ areaGraphs }: { areaGraphs: AreaGraphEntry[] }) {
  const [active, setActive] = useState<{ area: string; period: DashaTimelineEntry } | null>(null);

  const periods = useMemo(() => (areaGraphs[0]?.graph.dashaTimeline ?? []).filter((p) => p.level === 1).slice(0, 5), [areaGraphs]);

  return (
    <div className="glass-card p-5">
      <div className="mb-3 flex items-center gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Confidence Heatmap
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full border-separate" style={{ borderSpacing: 4 }}>
          <thead>
            <tr>
              <th className="text-left text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Area
              </th>
              {periods.map((p) => (
                <th key={p.startDate} className="px-2 text-xs font-medium" style={{ color: p.isCurrent ? "var(--accent)" : "var(--text-muted)" }}>
                  {p.lord}
                  <div className="text-[10px] font-normal" style={{ color: "var(--text-tertiary)" }}>
                    {new Date(p.startDate).getFullYear()}–{new Date(p.endDate).getFullYear()}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {areaGraphs.map(({ area, label, graph }) => (
              <tr key={area}>
                <td className="whitespace-nowrap text-xs font-medium" style={{ color: "var(--text-primary)" }}>
                  {label}
                </td>
                {periods.map((p) => (
                  <td key={p.startDate}>
                    <button
                      onMouseEnter={() => setActive({ area: label, period: p })}
                      onMouseLeave={() => setActive(null)}
                      className="h-10 w-full rounded transition-all"
                      style={{
                        backgroundColor: scoreBg(graph.finalScore),
                        border: p.isCurrent ? "1.5px solid var(--accent)" : "1px solid var(--border-subtle)",
                      }}
                    >
                      <span className="text-xs font-semibold" style={{ color: scoreColor(graph.finalScore) }}>
                        {graph.finalScore}
                      </span>
                    </button>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {active && (
        <div className="mt-3 rounded-lg p-3 text-xs" style={{ backgroundColor: "var(--bg-surface-700)", border: "1px solid var(--border-subtle)" }}>
          {(() => {
            const g = areaGraphs.find((e) => e.label === active.area)!.graph;
            const topFactors = [...g.nodes]
              .filter((n) => !n.unavailable)
              .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
              .slice(0, 3);
            return (
              <>
                <p className="mb-1 font-semibold" style={{ color: "var(--text-primary)" }}>
                  {active.area} | {active.period.lord} Dasha — Score {g.finalScore} ({g.confidence.level})
                </p>
                <p className="mb-1" style={{ color: "var(--text-secondary)" }}>
                  Top Factors:
                </p>
                <ul className="mb-1 list-disc pl-4">
                  {topFactors.map((f) => (
                    <li key={f.id} style={{ color: "var(--text-primary)" }}>
                      {f.label}
                    </li>
                  ))}
                </ul>
                <p style={{ color: "var(--text-muted)" }}>Sources: {g.dataSources.filter((d) => d.available).length}/{g.dataSources.length}</p>
              </>
            );
          })()}
        </div>
      )}
      <p className="mt-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
        Score reflects this chart&apos;s current computed factor set; the highlighted column is the active mahadasha.
      </p>
    </div>
  );
}

/* ── 2. Prediction Factor Radar (8 axes = real scoring categories) ────── */
export function CategoryStrengthRadar({ graph, size = 320 }: { graph: PredictionGraph; size?: number }) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.32;

  const points = useMemo(() => {
    const n = CATEGORY_AXES.length;
    return CATEGORY_AXES.map((cat, i) => {
      const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
      const total = graph.categories.find((c) => c.category === cat);
      // Map delta (~ -10..+10 typical range) onto 0-100 for a stable axis scale.
      const value = total ? Math.max(0, Math.min(100, 50 + total.delta * 5)) : 0;
      const dist = (value / 100) * r;
      return {
        cat,
        value,
        x: cx + dist * Math.cos(angle),
        y: cy + dist * Math.sin(angle),
        axisX: cx + r * Math.cos(angle),
        axisY: cy + r * Math.sin(angle),
        labelX: cx + (r + 34) * Math.cos(angle),
        labelY: cy + (r + 34) * Math.sin(angle),
      };
    });
  }, [graph, cx, cy, r]);

  const polygon = points.map((p) => `${p.x},${p.y}`).join(" ");
  const idealPolygon = points.map((p) => `${cx + r * Math.cos(Math.atan2(p.axisY - cy, p.axisX - cx))},${cy + r * Math.sin(Math.atan2(p.axisY - cy, p.axisX - cx))}`).join(" ");
  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="glass-card flex flex-col items-center gap-2 p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Planet Strength Radar
      </h3>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Prediction factor category radar">
        {gridLevels.map((level) => {
          const ring = CATEGORY_AXES.map((_, i) => {
            const angle = (i / CATEGORY_AXES.length) * 2 * Math.PI - Math.PI / 2;
            const dist = level * r;
            return `${cx + dist * Math.cos(angle)},${cy + dist * Math.sin(angle)}`;
          }).join(" ");
          return <polygon key={level} points={ring} fill="none" stroke="var(--border-primary)" strokeWidth={1} opacity={0.5} />;
        })}
        {points.map((p) => (
          <line key={p.cat} x1={cx} y1={cy} x2={p.axisX} y2={p.axisY} stroke="var(--border-primary)" strokeWidth={1} opacity={0.5} />
        ))}
        <polygon points={idealPolygon} fill="none" stroke="var(--text-muted)" strokeWidth={1} strokeDasharray="3 3" opacity={0.5} />
        <polygon points={polygon} fill="var(--violet-400)" fillOpacity={0.18} stroke="var(--violet-400)" strokeWidth={2} />
        {points.map((p) => (
          <circle key={p.cat} cx={p.x} cy={p.y} r={4} fill="var(--violet-400)" stroke="var(--bg-card)" strokeWidth={1.5} />
        ))}
        {points.map((p) => (
          <text key={p.cat} x={p.labelX} y={p.labelY} textAnchor="middle" dominantBaseline="central" fontSize={10} fill="var(--text-secondary)">
            {p.cat}
          </text>
        ))}
      </svg>
      <p className="text-center text-[11px]" style={{ color: "var(--text-muted)" }}>
        Each axis is a real scoring category&apos;s net contribution for {graph.areaLabel}, mapped to 0–100 (50 = neutral).
      </p>
    </div>
  );
}

/* ── 3. Yoga Impact Heatmap: Yogas × Life Areas ────────────────────────── */
export function YogaImpactHeatmap({ areaGraphs }: { areaGraphs: AreaGraphEntry[] }) {
  const [selected, setSelected] = useState<{ yoga: string; area: string; sourceText: string; present: boolean } | null>(null);

  const yogaNames = useMemo(() => {
    const names = new Set<string>();
    for (const { graph } of areaGraphs) {
      for (const rule of graph.relatedRules) names.add(rule.yogaName);
    }
    return Array.from(names);
  }, [areaGraphs]);

  if (yogaNames.length === 0) {
    return (
      <div className="glass-card p-5">
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Yoga Impact Heatmap
        </h3>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          No matched yogas found for this chart.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card p-5">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Yoga Impact Heatmap
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full border-separate" style={{ borderSpacing: 4 }}>
          <thead>
            <tr>
              <th className="text-left text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Yoga
              </th>
              {areaGraphs.map(({ area, label }) => (
                <th key={area} className="px-1 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yogaNames.map((yoga) => (
              <tr key={yoga}>
                <td className="whitespace-nowrap text-xs font-medium" style={{ color: "var(--text-primary)" }}>
                  {yoga}
                </td>
                {areaGraphs.map(({ area, label, graph }) => {
                  const rule = graph.relatedRules.find((r) => r.yogaName === yoga);
                  const present = !!rule;
                  return (
                    <td key={area}>
                      <button
                        disabled={!present}
                        onClick={() => rule && setSelected({ yoga, area: label, sourceText: rule.sourceText, present })}
                        className="h-9 w-full rounded text-[11px] font-semibold transition-all"
                        style={{
                          backgroundColor: present ? "rgba(16,185,129,0.22)" : "rgba(255,255,255,0.04)",
                          color: present ? "#34d399" : "var(--text-disabled)",
                          border: present ? "1px solid rgba(16,185,129,0.4)" : "1px solid var(--border-subtle)",
                          cursor: present ? "pointer" : "default",
                        }}
                      >
                        {present ? "✓" : "—"}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="mt-3 rounded-lg p-3 text-xs" style={{ backgroundColor: "var(--bg-surface-700)", border: "1px solid var(--border-subtle)" }}>
          <p className="mb-1 font-semibold" style={{ color: "var(--text-primary)" }}>
            {selected.yoga} → {selected.area}
          </p>
          <p style={{ color: "var(--text-secondary)" }}>{selected.sourceText}</p>
        </div>
      )}
    </div>
  );
}

/* ── 3b. Source Density Heatmap: real data-source availability per area ── */
export function SourceDensityHeatmap({ areaGraphs }: { areaGraphs: AreaGraphEntry[] }) {
  return (
    <div className="glass-card p-5">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Source Density Heatmap
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full border-separate" style={{ borderSpacing: 4 }}>
          <thead>
            <tr>
              <th className="text-left text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Area
              </th>
              <th className="px-1 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Available
              </th>
              <th className="px-1 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            {areaGraphs.map(({ area, label, graph }) => {
              const available = graph.dataSources.filter((d) => d.available).length;
              const total = graph.dataSources.length;
              const pct = total ? available / total : 0;
              return (
                <tr key={area}>
                  <td className="whitespace-nowrap text-xs font-medium" style={{ color: "var(--text-primary)" }}>
                    {label}
                  </td>
                  <td colSpan={2}>
                    <div className="flex h-7 w-full items-center rounded" style={{ backgroundColor: "rgba(255,255,255,0.05)" }}>
                      <div
                        className="flex h-full items-center rounded px-2 text-[11px] font-semibold"
                        style={{ width: `${Math.max(pct * 100, 14)}%`, backgroundColor: scoreBg(pct * 100), color: scoreColor(pct * 100) }}
                      >
                        {available}/{total}
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── 4. Overall Prediction Confidence Radar (6 real axes) ──────────────── */
export function OverallConfidenceRadar({ areaGraphs, size = 320 }: { areaGraphs: AreaGraphEntry[]; size?: number }) {
  const avg = (fn: (g: PredictionGraph) => number) => areaGraphs.reduce((s, e) => s + fn(e.graph), 0) / Math.max(1, areaGraphs.length);
  const categoryAvg = (cat: string) => avg((g) => {
    const c = g.categories.find((x) => x.category === cat);
    return c ? Math.max(0, Math.min(100, 50 + c.delta * 5)) : 50;
  });

  const axes = useMemo(
    () => [
      { label: "Data Quality", value: avg((g) => g.confidence.dataCompletePercent) },
      { label: "Source Coverage", value: avg((g) => (g.dataSources.length ? (g.dataSources.filter((d) => d.available).length / g.dataSources.length) * 100 : 0)) },
      { label: "Yoga Support", value: categoryAvg("Yogas") },
      { label: "Dasha Alignment", value: categoryAvg("Dasha") },
      { label: "Transit Support", value: categoryAvg("Transit") },
      { label: "Avastha Support", value: categoryAvg("Avastha") },
      // eslint-disable-next-line react-hooks/exhaustive-deps
    ],
    [areaGraphs]
  );

  const composite = Math.round(axes.reduce((s, a) => s + a.value, 0) / axes.length);

  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.32;

  const points = axes.map((a, i) => {
    const angle = (i / axes.length) * 2 * Math.PI - Math.PI / 2;
    const dist = (a.value / 100) * r;
    return {
      ...a,
      x: cx + dist * Math.cos(angle),
      y: cy + dist * Math.sin(angle),
      axisX: cx + r * Math.cos(angle),
      axisY: cy + r * Math.sin(angle),
      labelX: cx + (r + 36) * Math.cos(angle),
      labelY: cy + (r + 36) * Math.sin(angle),
    };
  });
  const polygon = points.map((p) => `${p.x},${p.y}`).join(" ");
  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="glass-card flex flex-col items-center gap-2 p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Prediction Confidence Radar
      </h3>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Overall prediction confidence radar">
          {gridLevels.map((level) => {
            const ring = axes.map((_, i) => {
              const angle = (i / axes.length) * 2 * Math.PI - Math.PI / 2;
              const dist = level * r;
              return `${cx + dist * Math.cos(angle)},${cy + dist * Math.sin(angle)}`;
            }).join(" ");
            return <polygon key={level} points={ring} fill="none" stroke="var(--border-primary)" strokeWidth={1} opacity={0.5} />;
          })}
          {points.map((p) => (
            <line key={p.label} x1={cx} y1={cy} x2={p.axisX} y2={p.axisY} stroke="var(--border-primary)" strokeWidth={1} opacity={0.5} />
          ))}
          <polygon points={polygon} fill="var(--cyan-400)" fillOpacity={0.2} stroke="var(--cyan-400)" strokeWidth={2} />
          {points.map((p) => (
            <circle key={p.label} cx={p.x} cy={p.y} r={4} fill="var(--cyan-400)" stroke="var(--bg-card)" strokeWidth={1.5} />
          ))}
          {points.map((p) => (
            <text key={p.label} x={p.labelX} y={p.labelY} textAnchor="middle" dominantBaseline="central" fontSize={10} fill="var(--text-secondary)">
              {p.label}
            </text>
          ))}
        </svg>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            {composite}%
          </span>
          <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            Confidence
          </span>
        </div>
      </div>
    </div>
  );
}

/* ── 5. Quick Insights: plain-text takeaways derived from real graphs ──── */
export function QuickInsights({ areaGraphs }: { areaGraphs: AreaGraphEntry[] }) {
  const insights = useMemo(() => {
    const items: { title: string; detail: string }[] = [];
    const sorted = [...areaGraphs].sort((a, b) => b.graph.finalScore - a.graph.finalScore);
    if (sorted[0]) {
      items.push({
        title: `${sorted[0].label} shows the strongest score (${sorted[0].graph.finalScore})`,
        detail: sorted[0].graph.confidence.level === "High" ? "Backed by high data confidence." : "Confidence is moderate — some inputs are missing.",
      });
    }
    const allYogas = areaGraphs.flatMap((e) => e.graph.relatedRules.map((r) => ({ ...r, area: e.label })));
    const yogaCounts = new Map<string, string[]>();
    for (const y of allYogas) yogaCounts.set(y.yogaName, [...(yogaCounts.get(y.yogaName) ?? []), y.area]);
    const topYoga = Array.from(yogaCounts.entries()).sort((a, b) => b[1].length - a[1].length)[0];
    if (topYoga) {
      items.push({
        title: `${topYoga[0]} is supporting multiple life areas`,
        detail: `Especially ${topYoga[1].slice(0, 2).join(" and ")}.`,
      });
    }
    const leastConfident = [...areaGraphs].sort((a, b) => a.graph.confidence.dataCompletePercent - b.graph.confidence.dataCompletePercent)[0];
    if (leastConfident && leastConfident.graph.confidence.level !== "High") {
      items.push({
        title: `${leastConfident.label} confidence is ${leastConfident.graph.confidence.level.toLowerCase()}`,
        detail: leastConfident.graph.confidence.missing.length ? `Missing: ${leastConfident.graph.confidence.missing.slice(0, 2).join(", ")}.` : "Some inputs are unavailable for this chart.",
      });
    }
    const avgQuality = Math.round(areaGraphs.reduce((s, e) => s + e.graph.confidence.dataCompletePercent, 0) / Math.max(1, areaGraphs.length));
    items.push({
      title: `Overall data quality is ${avgQuality >= 75 ? "high" : avgQuality >= 50 ? "moderate" : "low"}`,
      detail: "Derived from classical sources, planetary strengths and dasha data available for this chart.",
    });
    return items;
  }, [areaGraphs]);

  return (
    <div className="glass-card p-5">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Quick Insights
      </h3>
      <ul className="space-y-3">
        {insights.map((item, i) => (
          <li key={i} className="text-xs">
            <p className="font-medium" style={{ color: "var(--text-primary)" }}>
              {item.title}
            </p>
            <p style={{ color: "var(--text-secondary)" }}>{item.detail}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
