"use client";

import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import { useIshtaKashtaBala } from "@/lib/shadbala";
import type { WorkflowAnalysisRequest } from "@/lib/types";

interface IshtaKashtaBalaPanelProps {
  request: WorkflowAnalysisRequest | null;
}

/**
 * Ishta Bala (benefic/auspicious strength) vs Kashta Bala (malefic/
 * difficult strength) — a real classical Shadbala derivative
 * (sqrt(Uchcha Bala x Chesta Bala), see apps/api/services/shadbala/
 * ishta_kashta_bala.py), fetched live from the compute-only /shadbala
 * API using this chart's original birth details.
 *
 * Only covers the 5 planets Chesta Bala is computed for here (Mars/
 * Mercury/Jupiter/Venus/Saturn) — Sun/Moon are honestly omitted rather
 * than shown with an invented number.
 */
export function IshtaKashtaBalaPanel({ request }: IshtaKashtaBalaPanelProps) {
  const { data, isLoading, isError } = useIshtaKashtaBala(request);

  if (!request) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No birth data available to compute Ishta/Kashta Bala.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        Computing Ishta/Kashta Bala…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        Couldn't load Ishta/Kashta Bala for this chart.
      </div>
    );
  }

  const kashtaByPlanet = new Map(data.kashta_bala.map((k) => [k.planet, k.value_shashtiamsas]));

  return (
    <div className="glass-card p-5">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Ishta / Kashta Bala
      </h3>
      <p className="mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
        Benefic (Ishta) vs. malefic (Kashta) strength — sqrt(Uchcha Bala × Chesta Bala). Covers
        Mars/Mercury/Jupiter/Venus/Saturn only; Sun/Moon use a different classical treatment this
        app doesn't compute yet.
      </p>
      <div className="space-y-3">
        {data.ishta_bala.map((s) => {
          const kashta = kashtaByPlanet.get(s.planet) ?? 0;
          const ishtaPct = (s.value_shashtiamsas / 60) * 100;
          return (
            <div key={s.planet}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span style={{ color: "var(--text-secondary)" }}>
                  {PLANET_SYMBOLS[s.planet] ?? ""} {PLANET_ABBREV[s.planet] ?? s.planet.slice(0, 2)}
                </span>
                <span style={{ color: "var(--text-muted)" }}>
                  Ishta {s.value_shashtiamsas.toFixed(1)} · Kashta {kashta.toFixed(1)}
                </span>
              </div>
              <div
                className="flex h-3 overflow-hidden rounded-full"
                style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
                role="img"
                aria-label={`${s.planet}: Ishta Bala ${s.value_shashtiamsas.toFixed(1)}, Kashta Bala ${kashta.toFixed(1)}`}
              >
                <div className="h-full transition-all" style={{ width: `${ishtaPct}%`, backgroundColor: "#34d399" }} />
                <div className="h-full flex-1 transition-all" style={{ backgroundColor: "#f87171" }} />
              </div>
            </div>
          );
        })}
        {data.ishta_bala.length === 0 && (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No Ishta/Kashta data returned.
          </p>
        )}
      </div>
    </div>
  );
}
