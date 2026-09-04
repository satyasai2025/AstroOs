"use client";

import type { PredictionNode } from "@/lib/predictions/types";

interface FormulaInspectorProps {
  node: PredictionNode;
}

export function FormulaInspector({ node }: FormulaInspectorProps) {
  if (node.unavailable) {
    return (
      <div className="rounded-lg p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
        <p className="font-semibold" style={{ color: "var(--text-primary)" }}>
          {node.label} — Unavailable
        </p>
        <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
          {node.unavailableReason || "Required data not available for this chart."}
        </p>
      </div>
    );
  }

  const presentFactors = node.subFactors.filter((sf) => sf.present);
  const missingFactors = node.subFactors.filter((sf) => !sf.present);

  return (
    <div className="rounded-lg p-5 space-y-5" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
            {node.label}
          </h3>
          <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
            Formula {node.formulaVersion}
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold" style={{ color: "var(--accent)" }}>
            {node.delta >= 0 ? "+" : ""}{node.delta}
          </p>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Contribution
          </p>
        </div>
      </div>

      {/* Why this score? */}
      {presentFactors.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--text-secondary)" }}>
            Why this score?
          </h4>
          <div className="space-y-1.5">
            {presentFactors.map((sf, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span style={{ color: "#34d399" }}>✓</span>
                  <span style={{ color: "var(--text-primary)" }}>{sf.name}</span>
                </div>
                <span className="font-mono font-semibold" style={{ color: "var(--accent)" }}>
                  +{sf.contribution}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Why not higher? */}
      {missingFactors.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--text-secondary)" }}>
            Why not higher?
          </h4>
          <div className="space-y-1.5">
            {missingFactors.map((sf, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span style={{ color: "var(--text-muted)" }}>✗</span>
                  <span style={{ color: "var(--text-muted)" }}>{sf.name}</span>
                </div>
                <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>
                  (+{sf.weight} not applied)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw Chart Data */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--text-secondary)" }}>
          Raw Chart Data
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-primary)" }}>
                <th className="text-left py-1.5 px-2 font-semibold" style={{ color: "var(--text-muted)" }}>Field</th>
                <th className="text-left py-1.5 px-2 font-semibold" style={{ color: "var(--text-muted)" }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(node.inputs).map(([key, value]) => (
                <tr key={key} style={{ borderBottom: "1px solid var(--border-primary)" }}>
                  <td className="py-1.5 px-2 font-mono" style={{ color: "var(--text-secondary)" }}>{key}</td>
                  <td className="py-1.5 px-2" style={{ color: "var(--text-primary)" }}>
                    {typeof value === "boolean" ? (value ? "✓" : "✗") : String(value ?? "—")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Calculation */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--text-secondary)" }}>
          Calculation
        </h4>
        <div className="p-3 rounded font-mono text-sm" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
          {presentFactors.map((sf, i) => (
            <span key={i}>
              {sf.contribution >= 0 ? "+" : ""}{sf.contribution}
              {i < presentFactors.length - 1 ? " + " : ""}
            </span>
          ))}
          <span style={{ color: "var(--text-muted)" }}> = </span>
          <span className="font-bold" style={{ color: "var(--accent)" }}>
            {node.delta}
          </span>
        </div>
      </div>

      {/* Formula Information */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--text-secondary)" }}>
          Formula Information
        </h4>
        <div className="text-xs space-y-1" style={{ color: "var(--text-primary)" }}>
          <p><span className="font-semibold">Name:</span> {node.label}</p>
          <p><span className="font-semibold">Version:</span> {node.formulaVersion}</p>
          <p><span className="font-semibold">Category:</span> {node.category}</p>
        </div>
      </div>

      {/* Data Provenance */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: "var(--text-secondary)" }}>
          Data Provenance
        </h4>
        <div className="text-xs space-y-1 font-mono" style={{ color: "var(--text-muted)" }}>
          {node.source.map((src, i) => (
            <p key={i}>{src}</p>
          ))}
        </div>
      </div>
    </div>
  );
}