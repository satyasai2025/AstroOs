"use client";

import type { PredictionNode } from "@/lib/predictions/types";

interface PredictionFactorsPanelProps {
  nodes: PredictionNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  baseline: number;
  finalScore: number;
}

const POSITIVE = "#34d399";
const NEGATIVE = "#f87171";
const NEUTRAL = "var(--text-muted)";

function deltaColor(node: PredictionNode): string {
  if (node.unavailable) return NEUTRAL;
  if (node.delta > 0) return POSITIVE;
  if (node.delta < 0) return NEGATIVE;
  return NEUTRAL;
}

function deltaLabel(node: PredictionNode): string {
  if (node.unavailable) return "N/A";
  return `${node.delta >= 0 ? "+" : ""}${node.delta}`;
}

/**
 * PredictionFactorsPanel — render-only. The weight % shown per row is each
 * node's share of the total absolute delta across all nodes (a relative
 * "how much did this factor move the needle" figure), not a classical or
 * backend-declared weight — there's no such number in PredictionNode.
 * Top Influencers reuses the same real deltas, just sorted.
 */
export function PredictionFactorsPanel({ nodes, selectedId, onSelect, baseline, finalScore }: PredictionFactorsPanelProps) {
  const totalAbsDelta = nodes.reduce((sum, n) => sum + Math.abs(n.delta), 0);
  const topInfluencers = [...nodes]
    .filter((n) => !n.unavailable && n.delta !== 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 3);

  return (
    <div className="flex flex-col gap-4">
      <div className="glass-card p-2">
        <h3 className="px-3 pt-2 pb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
          Prediction Factors
        </h3>
        <div role="listbox" aria-label="Prediction factors" className="flex flex-col gap-1">
          {nodes.map((node, i) => {
            const active = node.id === selectedId;
            const weightPct = totalAbsDelta ? Math.round((Math.abs(node.delta) / totalAbsDelta) * 100) : 0;
            return (
              <button
                key={node.id}
                type="button"
                role="option"
                aria-selected={active}
                onClick={() => onSelect(node.id)}
                className="flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm transition"
                style={{
                  backgroundColor: active ? "var(--accent)" : "transparent",
                  color: active ? "var(--accent-text)" : "var(--text-primary)",
                }}
              >
                <span className="flex min-w-0 items-center gap-2">
                  <span
                    className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-semibold"
                    style={{
                      backgroundColor: active ? "rgba(255,255,255,0.2)" : "var(--bg-card)",
                      border: `1px solid ${active ? "transparent" : "var(--border-primary)"}`,
                      color: active ? "inherit" : "var(--text-muted)",
                    }}
                  >
                    {i + 1}
                  </span>
                  <span className="truncate">{node.label}</span>
                </span>
                <span className="flex flex-shrink-0 items-center gap-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-xs font-semibold"
                    style={{
                      color: active ? "inherit" : deltaColor(node),
                      border: `1px solid ${active ? "rgba(255,255,255,0.4)" : deltaColor(node)}`,
                    }}
                  >
                    {deltaLabel(node)}
                  </span>
                  <span className="w-8 text-right text-[10px]" style={{ color: active ? "inherit" : "var(--text-muted)" }}>
                    {weightPct}%
                  </span>
                </span>
              </button>
            );
          })}
          <div className="flex items-center justify-between px-3 py-2 text-sm" style={{ color: "var(--text-muted)" }}>
            <span>Baseline Score</span>
            <span>{baseline}</span>
          </div>
        </div>
      </div>

      <div className="glass-card flex items-center justify-between p-4">
        <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Final Score
        </span>
        <span className="text-2xl font-bold" style={{ color: "var(--accent)" }}>
          {finalScore} <span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}>/ 100</span>
        </span>
      </div>

      {topInfluencers.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
            Top Influencers
          </h3>
          <div className="flex flex-col gap-1.5">
            {topInfluencers.map((n) => (
              <div key={n.id} className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1.5" style={{ color: "var(--text-primary)" }}>
                  <span style={{ color: deltaColor(n) }}>{n.delta >= 0 ? "↑" : "↓"}</span>
                  {n.label}
                </span>
                <span className="font-semibold" style={{ color: deltaColor(n) }}>
                  {deltaLabel(n)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
