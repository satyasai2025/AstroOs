"use client";

/**
 * KP Special Factors — the "full KP portfolio" factors (Fortuna,
 * retrograde, combustion, Rahu/Ketu, dusthana/kendra occupancy, cuspal
 * interlinks) classified into CORE KP / EXTENDED KP / SUPPLEMENTARY so
 * the UI presents each with an honest authority level. All values arrive
 * pre-computed from the backend KP engine.
 */

import type { SpecialFactorResponse } from "@/lib/types";

interface Props {
  factors: SpecialFactorResponse[];
}

const CATEGORY_TONES: Record<SpecialFactorResponse["category"], { fg: string; bg: string }> = {
  "CORE KP": { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  "EXTENDED KP": { fg: "#60a5fa", bg: "rgba(96,165,250,0.15)" },
  "SUPPLEMENTARY": { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
};

const STATUS_COLORS: Record<SpecialFactorResponse["status"], { fg: string; bg: string }> = {
  positive: { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  neutral: { fg: "#94a3b8", bg: "rgba(148,163,184,0.15)" },
  caution: { fg: "#f87171", bg: "rgba(248,113,113,0.15)" },
};

export function KPSpecialFactors({ factors }: Props) {
  return (
    <div className="space-y-4">
      <div className="mb-4 flex flex-wrap gap-4 text-xs" style={{ color: "var(--text-secondary)" }}>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "#34d399" }} /> Core KP
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "#60a5fa" }} /> Extended KP
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "#fbbf24" }} /> Supplementary
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        {factors.map((f) => {
          const tone = CATEGORY_TONES[f.category];
          const status = STATUS_COLORS[f.status];
          return (
            <div key={f.name} className="glass-card p-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{f.name}</span>
                <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: tone.bg, color: tone.fg }}>
                  {f.category}
                </span>
              </div>
              <p className="mb-2 text-xs font-medium" style={{ color: "var(--text-secondary)" }}>{f.value}</p>
              <div className="flex items-start justify-between gap-2">
                <p className="text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>{f.evidence}</p>
                <span
                  className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
                  style={{ backgroundColor: status.bg, color: status.fg }}
                >
                  {f.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
