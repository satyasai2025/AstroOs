"use client";

import type { PredictionGraph, PredictionNode } from "@/lib/predictions/types";

interface PredictionChainGraphProps {
  graph: PredictionGraph;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const POSITIVE = "#34d399";
const NEGATIVE = "#f87171";
const NEUTRAL = "var(--text-muted)";

function nodeColor(node: PredictionNode | undefined): string {
  if (!node || node.unavailable) return NEUTRAL;
  if (node.delta > 0) return POSITIVE;
  if (node.delta < 0) return NEGATIVE;
  return NEUTRAL;
}

function Box({
  title,
  sub,
  score,
  active,
  onClick,
  color,
}: {
  title: string;
  sub?: string;
  score?: string;
  active?: boolean;
  onClick?: () => void;
  color?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className="w-full rounded-lg px-3 py-2 text-center transition"
      style={{
        backgroundColor: active ? "rgba(6,207,255,0.12)" : "var(--bg-card)",
        border: `1px solid ${active ? "var(--accent)" : "var(--border-primary)"}`,
        cursor: onClick ? "pointer" : "default",
      }}
    >
      <div className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
        {title}
        {sub && <span className="ml-1 font-normal" style={{ color: "var(--text-muted)" }}>({sub})</span>}
      </div>
      {score && (
        <div className="mt-0.5 text-sm font-bold" style={{ color: color ?? "var(--accent)" }}>
          {score}
        </div>
      )}
    </button>
  );
}

function Arrow() {
  return (
    <div className="flex justify-center py-1" style={{ color: "var(--border-strong)" }}>
      <svg width="14" height="16" viewBox="0 0 14 16" fill="none">
        <path d="M7 0V13M7 13L2 8M7 13L12 8" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    </div>
  );
}

/**
 * PredictionChainGraph — render-only computation-graph visualization: House
 * → Lord → per-category factor nodes → Yogas → Dasha/Transit → Final Score.
 * Every box's score comes straight from a real PredictionNode/graph field;
 * boxes for categories not present in this graph (e.g. Karakas for
 * house-lord-only areas) are simply omitted rather than shown as zero.
 */
export function PredictionChainGraph({ graph, selectedId, onSelect }: PredictionChainGraphProps) {
  const byCategory = (cat: string) => graph.nodes.find((n) => n.category === cat);
  const houseStrength = byCategory("House Strength");
  const planetStrength = byCategory("Planet Strength");
  const aspects = byCategory("Aspects");
  const yogas = byCategory("Yogas");
  const dasha = byCategory("Dasha");
  const transit = byCategory("Transit");

  const midRow = [houseStrength, planetStrength, aspects].filter(Boolean) as PredictionNode[];
  const bottomRow = [dasha, transit].filter(Boolean) as PredictionNode[];

  return (
    <div className="glass-card p-5">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Prediction Chain <span className="font-normal normal-case" style={{ color: "var(--text-muted)" }}>(Computation Graph)</span>
      </h3>

      <div className="mx-auto flex max-w-md flex-col gap-0">
        <Box title={`${graph.houseNumber}th House`} sub={`House of ${graph.areaLabel}`} />
        <Arrow />
        <Box title={graph.lord ?? "Unresolved Lord"} sub={`Lord of ${graph.houseNumber}th House`} />
        <Arrow />

        <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${midRow.length || 1}, minmax(0, 1fr))` }}>
          {midRow.map((n) => (
            <Box
              key={n.id}
              title={n.category}
              score={n.unavailable ? "N/A" : `${n.delta >= 0 ? "+" : ""}${n.delta}`}
              color={nodeColor(n)}
              active={n.id === selectedId}
              onClick={() => onSelect(n.id)}
            />
          ))}
        </div>

        {yogas && (
          <>
            <Arrow />
            <Box
              title="Yogas"
              sub={`${(yogas.raw.matched as unknown[] | undefined)?.length ?? 0} Matched`}
              score={yogas.unavailable ? "N/A" : `${yogas.delta >= 0 ? "+" : ""}${yogas.delta}`}
              color={nodeColor(yogas)}
              active={yogas.id === selectedId}
              onClick={() => onSelect(yogas.id)}
            />
          </>
        )}

        {bottomRow.length > 0 && (
          <>
            <Arrow />
            <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${bottomRow.length}, minmax(0, 1fr))` }}>
              {bottomRow.map((n) => (
                <Box
                  key={n.id}
                  title={n.category}
                  sub={graph.lord ? `${graph.lord}` : undefined}
                  score={n.unavailable ? "N/A" : `${n.delta >= 0 ? "+" : ""}${n.delta}`}
                  color={nodeColor(n)}
                  active={n.id === selectedId}
                  onClick={() => onSelect(n.id)}
                />
              ))}
            </div>
          </>
        )}

        <Arrow />
        <div
          className="rounded-lg px-4 py-3 text-center"
          style={{ border: "1px solid #34d399", backgroundColor: "rgba(52,211,153,0.08)" }}
        >
          <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            {graph.finalLabel}
          </div>
          <div className="text-xl font-bold" style={{ color: "#34d399" }}>
            {graph.finalScore} <span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}>/ 100</span>
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-[11px]" style={{ color: "var(--text-muted)" }}>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: POSITIVE }} /> Positive Contribution
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: NEGATIVE }} /> Negative Contribution
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: NEUTRAL }} /> Neutral / Baseline
        </span>
      </div>
    </div>
  );
}
