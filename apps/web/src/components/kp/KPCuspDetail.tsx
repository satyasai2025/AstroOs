"use client";

/**
 * KP Cusp Detail — expanded view of a single cusp: the CSL (Sub Lord)
 * decision chain, houses the CSL signifies, cuspal interlinks, and the
 * houses the cusp classically rules. All interlinks arrive pre-computed
 * from the backend KP engine.
 */

import { HOUSE_SIGNIFICATIONS } from "@/lib/kpAnalysis";
import type { KPCuspResponse } from "@/lib/types";
import { formatLongitude } from "@/lib/formatAstro";

interface Props {
  cusp: KPCuspResponse;
  onClose: () => void;
}

const VERDICT_COLORS: Record<string, { fg: string; bg: string }> = {
  STRONG: { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  PARTIAL: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
  WEAK: { fg: "#f87171", bg: "rgba(248,113,113,0.15)" },
};

export function KPCuspDetail({ cusp, onClose }: Props) {
  return (
    <div className="glass-card border-l-4 p-5" style={{ borderLeftColor: "var(--accent)" }}>
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h4 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            Cusp {cusp.house_number} — {cusp.rashi}
          </h4>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            {HOUSE_SIGNIFICATIONS[cusp.house_number]} · Longitude {formatLongitude(cusp.longitude)}
          </p>
        </div>
        <button type="button" onClick={onClose} className="btn-ghost text-xs px-2 py-1" aria-label="Close cusp detail">Close</button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sign Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{cusp.sign_lord ?? "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Star Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{cusp.star_lord || "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sub Lord (CSL)</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--accent)" }}>{cusp.sub_lord || "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sub-Sub Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{cusp.sub_sub_lord || "—"}</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-2">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            CSL Signifies Houses
          </p>
          <div className="flex flex-wrap gap-1.5">
            {cusp.csl_signifies.length === 0 && (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>No houses signified.</span>
            )}
            {cusp.csl_signifies.map((h) => (
              <span
                key={h}
                className="rounded-full px-2 py-0.5 text-xs font-medium"
                style={{ backgroundColor: VERDICT_COLORS.STRONG.bg, color: VERDICT_COLORS.STRONG.fg }}
              >
                House {h}
              </span>
            ))}
          </div>
          <p className="mt-2 text-[10px]" style={{ color: "var(--text-muted)" }}>
            Houses whose significator set includes {cusp.sub_lord || "the CSL"} — the cusp&apos;s Sub Lord links these matters.
          </p>
        </div>

        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Cuspal Interlinks
          </p>
          <div className="flex flex-wrap gap-1.5">
            {cusp.interlinked_cusps.length === 0 && (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>No shared Sub Lords.</span>
            )}
            {cusp.interlinked_cusps.map((h) => (
              <span
                key={h}
                className="rounded-full px-2 py-0.5 text-xs font-medium"
                style={{ backgroundColor: "rgba(96,165,250,0.15)", color: "#60a5fa" }}
              >
                House {h}
              </span>
            ))}
          </div>
          <p className="mt-2 text-[10px]" style={{ color: "var(--text-muted)" }}>
            Cusps sharing this cusp&apos;s Sub Lord — classical KP links their significations.
          </p>
        </div>
      </div>
    </div>
  );
}
