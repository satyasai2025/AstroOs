"use client";

import { useState } from "react";
import { PLANET_SYMBOLS } from "@/lib/astro";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import type { PlanetContext } from "./context";

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
}

export function YogasTab({ ctx }: Props) {
  const [open, setOpen] = useState<string | null>(null);
  const yogas = ctx.yogasInvolving;

  if (yogas.length === 0) {
    return (
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
        No present yogas in this chart involve {ctx.planet}.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        {yogas.length} present yoga{yogas.length > 1 ? "s" : ""} that involve {ctx.planet}, with their formation logic exposed.
      </p>
      {yogas.map((y) => {
        const isOpen = open === y.yoga_id;
        return (
          <div key={y.yoga_id} className="rounded-2xl border" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
            <button
              type="button"
              onClick={() => setOpen(isOpen ? null : y.yoga_id)}
              className="flex w-full items-center justify-between gap-3 p-4 text-left"
            >
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{y.name}</p>
                <p className="text-xs capitalize" style={{ color: "var(--text-muted)" }}>
                  {y.category}
                  {y.strength ? ` · ${y.strength}` : ""}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" style={{ color: "var(--success-400)" }}>
                  Active
                </span>
                <span style={{ color: "var(--text-muted)" }}>{isOpen ? "−" : "+"}</span>
              </div>
            </button>
            {isOpen && (
              <div className="border-t px-4 pb-4 pt-3" style={{ borderColor: "var(--border-primary)" }}>
                <div className="mb-2 flex flex-wrap gap-1.5">
                  {y.involved_planets.map((p) => (
                    <span key={p} className="rounded-full px-2 py-0.5 text-xs capitalize" style={{ backgroundColor: "var(--bg-input)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}>
                      {PLANET_SYMBOLS[p] ? `${PLANET_SYMBOLS[p]} ` : ""}{p}
                    </span>
                  ))}
                </div>

                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Required Conditions</p>
                <ul className="space-y-1 text-sm">
                  {(y.satisfied ?? []).map((s, i) => (
                    <li key={i} style={{ color: "var(--success-400)" }}>✓ {s}</li>
                  ))}
                  {(y.missing ?? []).map((m, i) => (
                    <li key={`m${i}`} style={{ color: "#ef4444" }}>✗ {m}</li>
                  ))}
                </ul>

                {(y.trace?.length ?? 0) > 0 && (
                  <>
                    <p className="mb-1 mt-3 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Trace</p>
                    <ul className="space-y-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                      {y.trace!.map((t, i) => <li key={i}>{t}</li>)}
                    </ul>
                  </>
                )}

                {y.source_text && (
                  <p className="mt-3 border-t pt-2 text-xs italic" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    {y.source_text}
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}