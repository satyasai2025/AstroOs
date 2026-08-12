"use client";

/**
 * KP Planet Portfolio — a reusable KP profile for each of the 9 planets:
 * sign, house, sign/star/sub/sub-sub lords, owned houses, houses it
 * signifies, and which cusps it is the Sub Lord (CSL) of. All from the
 * backend KP engine. Click a planet to open KPPlanetDetail.
 */

import { useState } from "react";
import type { KPPlanetProfileResponse } from "@/lib/types";
import { PLANET_SYMBOLS } from "@/lib/astro";
import { KPPlanetDetail } from "@/components/kp/KPPlanetDetail";

interface Props {
  profiles: KPPlanetProfileResponse[];
}

export function KPPlanetPortfolio({ profiles }: Props) {
  const [selected, setSelected] = useState<KPPlanetProfileResponse | null>(null);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {profiles.map((p) => (
          <button
            key={p.planet}
            type="button"
            onClick={() => setSelected(p)}
            className="glass-card p-4 text-left transition hover:opacity-90"
            style={{ border: selected?.planet === p.planet ? "1px solid var(--accent)" : undefined }}
            aria-label={`${p.planet} KP profile`}
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                <span aria-hidden="true" style={{ color: "var(--accent)" }}>{PLANET_SYMBOLS[p.planet] ?? ""}</span>
                {p.planet}
              </span>
              <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: "rgba(52,211,153,0.15)", color: "#34d399" }}>
                {p.rashi} · H{p.house_number}
              </span>
            </div>
            <dl className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Sign Lord</dt><dd>{p.sign_lord ?? "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Star Lord</dt><dd>{p.star_lord || "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Sub Lord</dt><dd className="font-semibold" style={{ color: "var(--accent)" }}>{p.sub_lord || "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Owns Houses</dt><dd>{p.owned_houses.length ? p.owned_houses.join(", ") : "—"}</dd></div>
              <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Signifies</dt><dd>{p.signifies.length ? p.signifies.join(", ") : "—"}</dd></div>
            </dl>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {p.is_retrograde && <span className="rounded-full px-2 py-0.5 text-[10px]" style={{ backgroundColor: "rgba(248,113,113,0.15)", color: "#f87171" }}>Retrograde</span>}
              {p.is_combust && <span className="rounded-full px-2 py-0.5 text-[10px]" style={{ backgroundColor: "rgba(251,191,36,0.15)", color: "#fbbf24" }}>Combust</span>}
              {p.csl_of.length > 0 && <span className="rounded-full px-2 py-0.5 text-[10px]" style={{ backgroundColor: "rgba(96,165,250,0.15)", color: "#60a5fa" }}>CSL of {p.csl_of.join(", ")}</span>}
            </div>
          </button>
        ))}
      </div>

      {selected && (
        <KPPlanetDetail profile={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
