"use client";

import type { ReactNode } from "react";
import { interpret, type EvidenceItem, type EvidenceKind } from "./interpretation";
import type { PlanetContext } from "./context";
import type { PlanetExplorerTab } from "../PlanetExplorerPanel";

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{title}</h3>
      {children}
    </div>
  );
}

function Bullets({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="text-sm" style={{ color: "var(--text-muted)" }}>None.</p>;
  return (
    <ul className="space-y-1 text-sm" style={{ color: "var(--text-primary)" }}>
      {items.map((s, i) => <li key={i}>· {s}</li>)}
    </ul>
  );
}

const KIND_COLOR: Record<EvidenceKind, string> = {
  structural: "var(--accent)",
  strength: "#fbbf24",
  relationship: "var(--cyan-300)",
  yoga: "var(--violet-300)",
  dasha: "var(--success-400)",
  transit: "var(--gold-300)",
};

const SOURCE_TO_TAB: Partial<Record<string, PlanetExplorerTab>> = {
  "Structure · Nakshatra": "structure",
  "Structure · Graha": "structure",
  "Structure · Rashi": "structure",
  "Strength": "strength",
  "Relationships · Dispositor": "relationships",
  "Relationships · Conjunctions": "relationships",
  "Yogas": "yogas",
  "Overview · House Ownership": "overview",
  "Dasha": "dasha",
  "Transit": "transit",
};

interface Props {
  ctx: PlanetContext;
  onFocusTab?: (tab: PlanetExplorerTab) => void;
}

export function InterpretationTab({ ctx, onFocusTab }: Props) {
  const interp = interpret(ctx);

  return (
    <div className="space-y-5">
      <Panel title={`Structural Interpretation — ${ctx.planet}`}>
        <p className="text-base leading-relaxed" style={{ color: "var(--text-primary)" }}>
          {interp.coreExpression}
        </p>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--success-400)" }}>
              Supporting Factors
            </h4>
            <Bullets items={interp.supporting} />
          </div>
          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "#ef4444" }}>
              Modifying Factors
            </h4>
            <Bullets items={interp.modifying} />
          </div>
        </div>

        <h4 className="mb-1 mt-4 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Activation
        </h4>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{interp.activation}</p>
      </Panel>

      {/* Evidence */}
      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Evidence</h3>
          <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>Why this interpretation</span>
        </div>
        {interp.evidence.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>No chart factors were available to evidence this reading.</p>
        ) : (
          <ul className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
            {interp.evidence.map((e: EvidenceItem, i) => {
              const tab = SOURCE_TO_TAB[e.source];
              return (
                <li key={i} className="flex items-center justify-between gap-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold uppercase" style={{ color: KIND_COLOR[e.kind] }}>
                      {e.kind}
                    </span>
                    <span className="text-sm" style={{ color: "var(--text-primary)" }}>{e.label}</span>
                  </div>
                  {onFocusTab && tab ? (
                    <button
                      type="button"
                      onClick={() => onFocusTab(tab!)}
                      className="text-xs underline"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {e.source} →
                    </button>
                  ) : (
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>{e.source}</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}