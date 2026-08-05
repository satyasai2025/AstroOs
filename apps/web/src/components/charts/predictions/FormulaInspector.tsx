"use client";

import type { PredictionNode } from "@/lib/predictions/types";

interface FormulaInspectorProps {
  node: PredictionNode;
}

/**
 * FormulaInspector — works identically for every PredictionNode, because
 * it only ever reads that node's own provenance fields (formulaId/version,
 * inputs, raw, source, detail). No per-factor UI code here, so this stays
 * correct automatically as scoring.ts's PREDICTION_FACTORS grows.
 */
export function FormulaInspector({ node }: FormulaInspectorProps) {
  if (node.unavailable) {
    return (
      <div className="rounded-lg p-3 text-xs" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
        <p className="font-semibold" style={{ color: "var(--text-primary)" }}>
          Formula: {node.formulaId} ({node.formulaVersion})
        </p>
        <p className="mt-1" style={{ color: "var(--text-muted)" }}>
          Not computed — {node.unavailableReason}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg p-3 text-xs" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
      <div className="flex items-center justify-between">
        <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
          Formula: {node.formulaId} ({node.formulaVersion})
        </span>
        <span className="font-semibold" style={{ color: "var(--accent)" }}>
          Result: {node.delta >= 0 ? "+" : ""}
          {node.delta}
        </span>
      </div>

      {Object.keys(node.inputs).length > 0 && (
        <div>
          <p className="mb-1 font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)", fontSize: "10px" }}>
            Inputs
          </p>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1">
            {Object.entries(node.inputs).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2">
                <span style={{ color: "var(--text-muted)" }}>{k}</span>
                <span style={{ color: "var(--text-primary)" }}>{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {node.detail.length > 0 && (
        <div>
          <p className="mb-1 font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)", fontSize: "10px" }}>
            Arithmetic
          </p>
          <ul className="flex flex-col gap-1">
            {node.detail.map((line, i) => (
              <li key={i} style={{ color: "var(--text-secondary)" }}>
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      {node.source.length > 0 && (
        <div>
          <p className="mb-1 font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)", fontSize: "10px" }}>
            Source fields
          </p>
          <ul className="flex flex-col gap-0.5 font-mono" style={{ fontSize: "10px" }}>
            {node.source.map((s, i) => (
              <li key={i} style={{ color: "var(--text-muted)" }}>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
