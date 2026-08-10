"use client";

/**
 * KP Planet Detail — expanded KP profile for a single planet: the full
 * signification chain (occupies → owns → star-linked → sub-linked),
 * cusps it is the CSL of, and its classical node/combustion/retrograde
 * flags.
 */

import { useMemo } from "react";
import { buildKPPlanetProfiles, type KPPlanetProfile } from "@/lib/kpAnalysis";
import type { D1ChartResponse } from "@/lib/types";
import { PLANET_SYMBOLS } from "@/lib/astro";
import { formatLongitude } from "@/lib/formatAstro";

interface Props {
  profile: KPPlanetProfile;
  chart: D1ChartResponse;
  onClose: () => void;
}

export function KPPlanetDetail({ profile, chart, onClose }: Props) {
  const live = useMemo(
    () => buildKPPlanetProfiles(chart).find((p) => p.planet === profile.planet) ?? profile,
    [chart, profile],
  );

  return (
    <div className="glass-card border-l-4 p-5" style={{ borderLeftColor: "var(--accent)" }}>
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h4 className="flex items-center gap-2 text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            <span aria-hidden="true" style={{ color: "var(--accent)" }}>{PLANET_SYMBOLS[live.planet] ?? ""}</span>
            {live.planet} — {live.rashi} in House {live.house_number}
          </h4>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Longitude {formatLongitude(live.longitude)}
            {live.is_retrograde && " · Retrograde"}
            {live.is_combust && " · Combust"}
          </p>
        </div>
        <button type="button" onClick={onClose} className="btn-ghost text-xs px-2 py-1" aria-label="Close planet detail">Close</button>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sign Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{live.sign_lord ?? "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Star Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{live.star_lord || "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sub Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--accent)" }}>{live.sub_lord || "—"}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sub-Sub Lord</p>
          <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{live.sub_sub_lord || "—"}</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-2">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Signification Chain</p>
          <dl className="space-y-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
            <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Occupies</dt><dd>House {live.occupied_house}</dd></div>
            <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Owns (Sign Lord of)</dt><dd>{live.owned_houses.length ? live.owned_houses.map((h) => `H${h}`).join(", ") : "—"}</dd></div>
            <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Star-linked to</dt><dd>{live.star_lord_houses.length ? live.star_lord_houses.map((h) => `H${h}`).join(", ") : "—"}</dd></div>
            <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Sub-lord of cusps</dt><dd>{live.sub_lord_houses.length ? live.sub_lord_houses.map((h) => `H${h}`).join(", ") : "—"}</dd></div>
          </dl>
        </div>

        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>As Significator / CSL</p>
          <div className="flex flex-wrap gap-1.5">
            {live.signifies.map((h) => (
              <span key={h} className="rounded-full px-2 py-0.5 text-xs font-medium" style={{ backgroundColor: "rgba(52,211,153,0.15)", color: "#34d399" }}>
                Signifies H{h}
              </span>
            ))}
            {live.csl_of.length > 0 && (
              <span className="rounded-full px-2 py-0.5 text-xs font-medium" style={{ backgroundColor: "rgba(96,165,250,0.15)", color: "#60a5fa" }}>
                CSL of {live.csl_of.join(", ")}
              </span>
            )}
          </div>
          <p className="mt-2 text-[10px]" style={{ color: "var(--text-muted)" }}>
            Houses this planet significates (occupied + owned + star-linked) and the cusps where it is the Sub Lord — the classical KP reading chain.
          </p>
        </div>
      </div>
    </div>
  );
}
