"use client";

import type { ReactNode } from "react";
import { KARAKATVA_BASIC } from "@/lib/astro";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import type { PlanetContext } from "./context";

function fmt(iso: string): string {
  try {
    const d = new Date(iso);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  } catch {
    return iso;
  }
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h4 className="mb-1.5 mt-4 text-xs font-semibold uppercase tracking-wide first:mt-0" style={{ color: "var(--accent)" }}>
      {children}
    </h4>
  );
}

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
}

export function DashaTab({ ctx }: Props) {
  const chain = ctx.dashaChain;
  const karakatva = KARAKATVA_BASIC[ctx.planet] ?? [];

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Current Dasha Chain</h3>
        {chain.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>No current dasha period resolved.</p>
        ) : (
          <ol className="space-y-2 border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
            {chain.map((p, i) => {
              const active = p.lord === ctx.planet;
              return (
                <li key={i} className="flex items-center justify-between text-sm">
                  <span className="font-medium capitalize" style={{ color: active ? "var(--accent)" : "var(--text-primary)" }}>
                    {p.lord}
                    {active ? " ← this planet" : ""}
                  </span>
                  <span style={{ color: "var(--text-muted)" }}>{fmt(p.start_date)} → {fmt(p.end_date)}</span>
                </li>
              );
            })}
          </ol>
        )}
      </div>

      <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>What {ctx.planet} activates</h3>
        <div className="border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          {ctx.houseOwnerOf.length > 0 && (
            <>
              <SectionLabel>Houses</SectionLabel>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                {ctx.houseOwnerOf.sort((a, b) => a - b).map((h) => `House ${h}`).join(", ")}
              </p>
            </>
          )}
          {karakatva.length > 0 && (
            <>
              <SectionLabel>Karakatva</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                {karakatva.map((k) => (
                  <span key={k} className="rounded-full px-2 py-0.5 text-xs" style={{ backgroundColor: "var(--bg-input)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}>
                    {k}
                  </span>
                ))}
              </div>
            </>
          )}
          {ctx.yogasInvolving.length > 0 && (
            <>
              <SectionLabel>Yogas</SectionLabel>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                {ctx.yogasInvolving.map((y) => y.name).join(", ")}
              </p>
            </>
          )}
          {ctx.houseOwnerOf.length === 0 && karakatva.length === 0 && ctx.yogasInvolving.length === 0 && (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>No activatable significations resolved for {ctx.planet}.</p>
          )}
        </div>
      </div>
    </div>
  );
}