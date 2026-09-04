"use client";

import type { PredictionNode } from "@/lib/predictions/types";

interface PredictionStepListProps {
  nodes: PredictionNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
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
 * PredictionStepList — render-only. One row per PredictionNode already
 * computed by chainEngine.ts; this component has no scoring logic and no
 * knowledge of which factors exist — it just maps over whatever the graph
 * contains, so new factors show up automatically.
 */
export function PredictionStepList({ nodes, selectedId, onSelect }: PredictionStepListProps) {
  return (
    <div className="glass-card flex flex-col gap-1 p-2" role="listbox" aria-label="Prediction chain steps">
      {nodes.map((node, i) => {
        const active = node.id === selectedId;
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
            <span
              className="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold"
              style={{
                color: active ? "inherit" : deltaColor(node),
                border: `1px solid ${active ? "rgba(255,255,255,0.4)" : deltaColor(node)}`,
              }}
            >
              {deltaLabel(node)}
            </span>
          </button>
        );
      })}
    </div>
  );
}
