"use client";

import { useState } from "react";
import type { PredictionNode } from "@/lib/predictions/types";
import { FormulaInspector } from "./FormulaInspector";

interface PredictionStepDetailProps {
  node: PredictionNode | null;
}

const POSITIVE = "#34d399";
const NEGATIVE = "#f87171";

/**
 * PredictionStepDetail — render-only. Shows the selected node's
 * computation-detail lines and raw data, with a toggle to open
 * FormulaInspector for the full formula/arithmetic breakdown.
 */
export function PredictionStepDetail({ node }: PredictionStepDetailProps) {
  const [showFormula, setShowFormula] = useState(false);

  if (!node) {
    return (
      <div className="glass-card flex h-full items-center justify-center p-8 text-sm" style={{ color: "var(--text-muted)" }}>
        Select a step from the chain to see its computation detail.
      </div>
    );
  }

  const color = node.unavailable ? "var(--text-muted)" : node.delta > 0 ? POSITIVE : node.delta < 0 ? NEGATIVE : "var(--text-muted)";

  return (
    <div className="glass-card flex flex-col gap-4 p-5">
      <div>
        <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          {node.category}
        </span>
        <h3 className="mt-1 text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          {node.label}
        </h3>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          Contribution to score
        </span>
        <span className="text-2xl font-bold" style={{ color }}>
          {node.unavailable ? "N/A" : `${node.delta >= 0 ? "+" : ""}${node.delta}`}
        </span>
      </div>

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
          Computation detail
        </p>
        <ul className="flex flex-col gap-2">
          {(node.unavailable ? [node.unavailableReason ?? "Data not available"] : node.detail).map((line, i) => (
            <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
              <span
                className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full"
                style={{ backgroundColor: node.unavailable ? "var(--text-muted)" : "var(--accent)" }}
              />
              {line}
            </li>
          ))}
        </ul>
      </div>

      {!node.unavailable && Object.keys(node.raw).length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
            Raw data
          </p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 rounded-lg p-3" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
            {Object.entries(node.raw)
              .filter(([, v]) => typeof v !== "object" || v === null)
              .map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-2 text-xs">
                  <span style={{ color: "var(--text-muted)" }}>{k}</span>
                  <span style={{ color: "var(--text-primary)" }}>{String(v)}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => setShowFormula((v) => !v)}
        className="self-start rounded-lg px-3 py-1.5 text-xs font-medium transition"
        style={{ border: "1px solid var(--border-primary)", color: "var(--accent)" }}
      >
        {showFormula ? "Hide formula" : "View formula"}
      </button>

      {showFormula && <FormulaInspector node={node} />}
    </div>
  );
}
