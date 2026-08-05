"use client";

import type { PredictionNode } from "@/lib/predictions/types";
import { FormulaInspector } from "./FormulaInspector";

interface FormulaInspectorPanelProps {
  nodes: PredictionNode[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onClose?: () => void;
  onViewSources?: () => void;
}

/**
 * FormulaInspectorPanel — docked (not floating) right-column panel wrapping
 * FormulaInspector with a factor dropdown, so the panel can drive its own
 * selection independent of whatever list triggered it. onClose is optional
 * since this panel is a permanent column in the Overview layout, not a
 * modal — when omitted, no close affordance is rendered.
 */
export function FormulaInspectorPanel({ nodes, selectedId, onSelect, onClose, onViewSources }: FormulaInspectorPanelProps) {
  const selected = nodes.find((n) => n.id === selectedId) ?? null;

  return (
    <div className="glass-card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
          Formula Inspector
        </h3>
        {onClose && (
          <button type="button" onClick={onClose} aria-label="Close Formula Inspector" style={{ color: "var(--text-muted)" }}>
            ✕
          </button>
        )}
      </div>

      <label className="flex flex-col gap-1 text-xs" style={{ color: "var(--text-secondary)" }}>
        Factor
        <select
          value={selectedId ?? ""}
          onChange={(e) => onSelect(e.target.value)}
          className="field-input"
        >
          {nodes.map((n, i) => (
            <option key={n.id} value={n.id}>
              {i + 1}. {n.label}
            </option>
          ))}
        </select>
      </label>

      {selected ? <FormulaInspector node={selected} /> : (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Select a factor to inspect its formula.
        </p>
      )}

      {onViewSources && (
        <button
          type="button"
          onClick={onViewSources}
          className="flex items-center gap-1.5 text-xs font-medium"
          style={{ color: "var(--accent)" }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 3h7v7M21 3l-9 9M5 5h5v2H7v10h10v-3h2v5H5z" />
          </svg>
          View in Provenance Explorer
        </button>
      )}
    </div>
  );
}
