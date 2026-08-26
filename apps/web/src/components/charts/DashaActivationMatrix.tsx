"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui";
import { getCurrentDashaChain, getHouseLordStrength } from "@/lib/kpiScoring";
import { rashiLordFromApiName } from "@/lib/astro";
import type { WorkflowAnalysisResponse } from "@/lib/types";

/**
 * Maps classical Karakatva (signification) groupings to planets.
 * These are naisargika (natural) karakas — fixed in classical Parashari
 * Jyotish; not per-chart computed values.
 */
const PLANET_KARAKATVAS: Record<string, string[]> = {
  Sun:     ["Soul", "Father", "Authority", "Government", "Vitality"],
  Moon:    ["Mind", "Mother", "Emotions", "Public", "Nourishment"],
  Mars:    ["Courage", "Siblings", "Property", "Energy", "Surgery"],
  Mercury: ["Intelligence", "Communication", "Business", "Learning"],
  Jupiter: ["Wisdom", "Children", "Wealth", "Guru", "Dharma"],
  Venus:   ["Marriage", "Luxury", "Creativity", "Vehicles", "Comforts"],
  Saturn:  ["Karma", "Service", "Longevity", "Discipline", "Delays"],
  Rahu:    ["Foreign", "Technology", "Illusion", "Unconventional"],
  Ketu:    ["Spirituality", "Liberation", "Past Life", "Research"],
};

/**
 * Dasha Activation Matrix — shows active MD/AD lords, the houses they
 * activate (by lordship), their classical karakatvas, and any triggered
 * yogas from the existing yoga evaluation. All data from WorkflowAnalysisResponse.
 */
export function DashaActivationMatrix({ result }: { result: WorkflowAnalysisResponse }) {
  const chain = useMemo(
    () => getCurrentDashaChain(result.dasha.mahadashas),
    [result.dasha.mahadashas],
  );

  const md = chain[0] ?? null;
  const ad = chain[1] ?? null;
  const activeLords = [md?.lord, ad?.lord].filter(Boolean) as string[];

  // Houses owned by each active dasha lord (where rashiLord of that house === lord)
  const activatedHouses = useMemo(() => {
    const map: Record<string, number[]> = {};
    for (const lord of activeLords) {
      map[lord] = result.chart.houses
        .filter((h) => rashiLordFromApiName(h.rashi) === lord)
        .map((h) => h.house_number)
        .sort((a, b) => a - b);
    }
    return map;
  }, [activeLords, result.chart.houses]);

  // Yogas triggered by the active lords — any yoga whose planets include an active lord
  const triggeredYogas = useMemo(() => {
    if (!activeLords.length) return [];
    return result.yogas.results.filter((y) => {
      if (!y.is_present) return false;
      return y.involved_planets.some((p) => activeLords.includes(p));
    });
  }, [activeLords, result.yogas.results]);

  // House strength for activated houses
  const houseStrengths = useMemo(() => {
    const entries: { house: number; lord: string | null; strength: string }[] = [];
    for (const houses of Object.values(activatedHouses)) {
      for (const hNum of houses) {
        const { lord, strength } = getHouseLordStrength(
          hNum,
          result.chart.houses,
          result.chart.planet_strengths,
        );
        const pct = strength ? Math.round((strength.strength_score / 10) * 100) : null;
        entries.push({
          house: hNum,
          lord,
          strength: pct !== null ? `${pct}%` : "—",
        });
      }
    }
    return entries;
  }, [activatedHouses, result.chart.houses, result.chart.planet_strengths]);

  if (!md) {
    return (
      <Card>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No active Dasha period found within computed depth.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* ── Active Lords ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {activeLords.map((lord, i) => (
          <Card key={lord}>
            <p
              className="mb-1 text-[10px] font-bold uppercase tracking-wider"
              style={{ color: "var(--text-muted)" }}
            >
              {i === 0 ? "Mahadasha Lord" : `Antardasha Lord (in ${activeLords[0]})`}
            </p>
            <p
              className="mb-2 text-lg font-bold"
              style={{ color: "var(--accent)" }}
            >
              {lord}
            </p>

            {/* Owned & Occupied houses */}
            <div className="mb-2 space-y-1">
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Owned:</span>
                {(activatedHouses[lord] ?? []).length > 0 ? (
                  activatedHouses[lord].map((h) => (
                    <span
                      key={h}
                      className="rounded-md px-2 py-0.5 text-[10px] font-semibold"
                      style={{
                        background: "var(--bg-card)",
                        border: "1px solid var(--border-primary)",
                        color: "var(--text-primary)",
                      }}
                    >
                      H{h}
                    </span>
                  ))
                ) : (
                  <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                    None (D1)
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-1">
                <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Occupies:</span>
                {(() => {
                  const occ = result.chart.planet_strengths.find((p) => p.planet === lord)?.house_number;
                  return occ ? (
                    <span
                      className="rounded-md px-2 py-0.5 text-[10px] font-semibold"
                      style={{
                        background: "var(--accent)",
                        color: "var(--accent-text)",
                      }}
                    >
                      H{occ}
                    </span>
                  ) : (
                    <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                      —
                    </span>
                  );
                })()}
              </div>
            </div>

            {/* Karakatvas */}
            <p
              className="mb-1 text-[10px] font-semibold uppercase tracking-wide"
              style={{ color: "var(--text-muted)" }}
            >
              Karakatvas
            </p>
            <div className="flex flex-wrap gap-1">
              {(PLANET_KARAKATVAS[lord] ?? ["—"]).map((k) => (
                <span
                  key={k}
                  className="rounded-full px-2 py-0.5 text-[10px]"
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-primary)",
                    color: "var(--text-secondary)",
                  }}
                >
                  {k}
                </span>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {/* ── Activated House Strengths ──────────────────────────────────── */}
      {houseStrengths.length > 0 && (
        <Card>
          <h4
            className="mb-2 text-xs font-semibold uppercase tracking-wide"
            style={{ color: "var(--text-tertiary)" }}
          >
            Activated Houses (by Lordship)
          </h4>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
            {houseStrengths.map(({ house, lord, strength }) => (
              <div
                key={house}
                className="rounded-md p-2 text-center"
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-primary)",
                }}
              >
                <p
                  className="text-xs font-bold"
                  style={{ color: "var(--text-primary)" }}
                >
                  House {house}
                </p>
                <p
                  className="text-[10px]"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Lord: {lord ?? "—"}
                </p>
                <p
                  className="text-[10px] font-semibold"
                  style={{ color: "var(--accent)" }}
                >
                  {strength}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ── Triggered Yogas ────────────────────────────────────────────── */}
      <Card>
        <h4
          className="mb-2 text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-tertiary)" }}
        >
          Triggered Yogas
          <span
            className="ml-2 rounded-full px-2 py-0.5 text-[10px] font-normal"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-primary)",
              color: "var(--text-secondary)",
            }}
          >
            {triggeredYogas.length} found
          </span>
        </h4>

        {triggeredYogas.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            No present yogas directly involve{" "}
            {activeLords.join(" or ")} in this chart.
          </p>
        ) : (
          <div className="space-y-2">
            {triggeredYogas.map((yoga) => (
              <div
                key={yoga.name}
                className="rounded-md p-2"
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-primary)",
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p
                      className="text-xs font-semibold"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {yoga.name}
                    </p>
                    <p
                      className="text-[10px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {yoga.category}
                    </p>
                  </div>
                  <span
                    className="rounded-full px-2 py-0.5 text-[9px] font-semibold"
                    style={{
                      background: "var(--accent)",
                      color: "var(--accent-text)",
                      opacity: 0.85,
                      whiteSpace: "nowrap",
                    }}
                  >
                    Active
                  </span>
                </div>
                {yoga.involved_planets && yoga.involved_planets.length > 0 && (
                  <p className="mt-1 text-[10px]" style={{ color: "var(--text-secondary)" }}>
                    Planets: {yoga.involved_planets.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
