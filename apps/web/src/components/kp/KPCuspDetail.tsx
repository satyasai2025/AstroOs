"use client";

/**
 * KP Cusp Detail — expanded view of a single cusp: the CSL (Sub Lord)
 * decision chain, houses the CSL signifies, cuspal interlinks, and the
 * houses the cusp classically rules.
 */

import { buildKPCusps, HOUSE_SIGNIFICATIONS, type KPCusp } from "@/lib/kpAnalysis";
import type { D1ChartResponse } from "@/lib/types";
import { formatLongitude } from "@/lib/formatAstro";

interface Props {
  cusp: KPCusp;
  onClose: () => void;
  /** Optional — used to recompute the CSL verdict against required houses. */
  chart?: D1ChartResponse;
}

const VERDICT_COLORS: Record<string, { fg: string; bg: string }> = {
  STRONG: { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  PARTIAL: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
  WEAK: { fg: "#f87171", bg: "rgba(248,113,113,0.15)" },
};

export function KPCuspDetail({ cusp, onClose, chart }: Props) {
  // When the parent passes the chart, derive live interlinks from the
  // canonical cusp matrix (so the standalone module stays consistent).
  const liveCusp = chart ? buildKPCusps(chart).find((c) => c.house_number === cusp.house_number) ?? cusp : cusp;

  return (
    <div className="glass-card border-l-4 p-5" style={{ borderLeftColor: "var(--accent)" }}>
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h4 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            Cusp {liveCusp.house_number} — {liveCusp.rashi}
          </h4>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            {HOUSE_SIGNIFICATIONS[liveCusp.house_number]} · Longitude {formatLongitude(liveCusp.longitude)}
          </p>
        </div>
        <button type="button" onClick={onClose} className="btn-ghost text-xs px-2 py-1" aria-label="Close cusp detail">Close</button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sign Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{liveCusp.sign_lord ?? "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Star Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{liveCusp.star_lord || "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sub Lord (CSL)</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--accent)" }}>{liveCusp.sub_lord || "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sub-Sub Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{liveCusp.sub_sub_lord || "—"}</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-2">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            CSL Signifies Houses
          </p>
          <div className="flex flex-wrap gap-1.5">
            {liveCusp.csl_signifies.length === 0 && (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>No houses signified.</span>
            )}
            {liveCusp.csl_signifies.map((h) => (
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
            Houses whose significator set includes {liveCusp.sub_lord || "the CSL"} — the cusp&apos;s Sub Lord links these matters.
          </p>
        </div>

        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Cuspal Interlinks
          </p>
          <div className="flex flex-wrap gap-1.5">
            {liveCusp.interlinked_cusps.length === 0 && (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>No shared Sub Lords.</span>
            )}
            {liveCusp.interlinked_cusps.map((h) => (
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
