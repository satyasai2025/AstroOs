"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type { WorkflowAnalysisResponse, TransitPlanetResponse } from "@/lib/types";

/**
 * Dasha × Transit Confluence UI
 * Displays active Dasha lords alongside live transit (Gochara) positions,
 * with special highlight on Jupiter & Saturn double-transit correlations.
 * Reuses existing `result.transits` and `result.dasha` data.
 */
export function DashaTransitConfluence({ result }: { result: WorkflowAnalysisResponse }) {
  const chain = useMemo(
    () => getCurrentDashaChain(result.dasha.mahadashas),
    [result.dasha.mahadashas],
  );

  const md = chain[0] ?? null;
  const ad = chain[1] ?? null;
  const activeLords = [md?.lord, ad?.lord].filter(Boolean) as string[];

  const transitPlanets = result.transits?.planets ?? [];
  const natalMoon = result.chart.planets.find((p) => p.planet === "Moon");

  // Key transit planets of interest (Jupiter & Saturn double-transit, plus active dasha lord transits)
  const jupiterTransit = transitPlanets.find((p) => p.planet === "Jupiter");
  const saturnTransit = transitPlanets.find((p) => p.planet === "Saturn");

  const activeLordsTransits = useMemo(() => {
    return activeLords.map((lord) => ({
      lord,
      transit: transitPlanets.find((p) => p.planet === lord) ?? null,
    }));
  }, [activeLords, transitPlanets]);

  // Double transit correlation analysis (Jupiter & Saturn)
  const doubleTransitAnalysis = useMemo(() => {
    if (!jupiterTransit || !saturnTransit) return null;

    const jupHouseMoon = jupiterTransit.house_from_natal_moon;
    const satHouseMoon = saturnTransit.house_from_natal_moon;

    return {
      jupiter: {
        rashi: jupiterTransit.transit_rashi,
        houseFromMoon: jupHouseMoon,
        isFavorable: jupiterTransit.is_favorable_house,
      },
      saturn: {
        rashi: saturnTransit.transit_rashi,
        houseFromMoon: satHouseMoon,
        isFavorable: saturnTransit.is_favorable_house,
        isSadeSati: saturnTransit.is_sade_sati,
        isAshtamaShani: saturnTransit.is_ashtama_shani,
      },
      hasDoubleInfluence: jupHouseMoon !== null && satHouseMoon !== null,
    };
  }, [jupiterTransit, saturnTransit]);

  if (!md) {
    return (
      <Card>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No active Dasha period found to correlate with Transits.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* ── Active Dasha Lords in Transit ─────────────────────────────────────── */}
      <Card>
        <h4
          className="mb-2 text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-tertiary)" }}
        >
          Active Dasha Lords Live Transit State
        </h4>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {activeLordsTransits.map(({ lord, transit }) => (
            <div
              key={lord}
              className="rounded-lg p-3"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-primary)",
              }}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold" style={{ color: "var(--accent)" }}>
                  {lord}
                </span>
                {transit?.is_retrograde && (
                  <span
                    className="rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider"
                    style={{
                      background: "rgba(239, 68, 68, 0.15)",
                      color: "#ef4444",
                    }}
                  >
                    Retrograde
                  </span>
                )}
              </div>

              {transit ? (
                <div className="mt-2 space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                  <div className="flex justify-between">
                    <span>Transit Sign</span>
                    <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                      {transit.transit_rashi} ({transit.transit_rashi_degree.toFixed(1)}°)
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Nakshatra</span>
                    <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                      {transit.transit_nakshatra} (Pada {transit.transit_pada})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>House from Moon</span>
                    <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                      H{transit.house_from_natal_moon ?? "—"}{" "}
                      {transit.is_favorable_house !== null && (
                        <span
                          style={{
                            color: transit.is_favorable_house
                              ? "var(--obsidian-status-success, #10b981)"
                              : "var(--text-muted)",
                          }}
                        >
                          ({transit.is_favorable_house ? "Favorable" : "Unfavorable"})
                        </span>
                      )}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                  No transit position data available for {lord}.
                </p>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* ── Double Transit (Jupiter + Saturn) Correlation ───────────────────── */}
      {doubleTransitAnalysis && (
        <Card>
          <div className="flex items-center justify-between mb-2">
            <h4
              className="text-xs font-semibold uppercase tracking-wide"
              style={{ color: "var(--text-tertiary)" }}
            >
              Jupiter & Saturn Double-Transit Correlation
            </h4>
            <span
              className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-primary)",
                color: "var(--accent)",
              }}
            >
              Gochara Synthesis
            </span>
          </div>

          <p className="mb-3 text-xs" style={{ color: "var(--text-secondary)" }}>
            Classical astrology highlights periods where both Jupiter (Expansion & Grace) and Saturn
            (Karma & Structure) simultaneously influence houses or planets, activating major life milestones.
          </p>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {/* Jupiter Gochara */}
            <div
              className="rounded-md p-3 text-xs"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-primary)",
              }}
            >
              <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                Jupiter (Guru)
              </p>
              <p className="mt-1" style={{ color: "var(--text-secondary)" }}>
                Transiting <strong>{doubleTransitAnalysis.jupiter.rashi}</strong> (House{" "}
                {doubleTransitAnalysis.jupiter.houseFromMoon} from Moon in {natalMoon?.rashi ?? "chart"})
              </p>
              {doubleTransitAnalysis.jupiter.isFavorable !== null && (
                <p
                  className="mt-1 text-[10px] font-semibold"
                  style={{
                    color: doubleTransitAnalysis.jupiter.isFavorable
                      ? "var(--obsidian-status-success, #10b981)"
                      : "var(--text-muted)",
                  }}
                >
                  {doubleTransitAnalysis.jupiter.isFavorable
                    ? "✓ Favorable Gochara House"
                    : "• Neutral/Challenging House"}
                </p>
              )}
            </div>

            {/* Saturn Gochara */}
            <div
              className="rounded-md p-3 text-xs"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-primary)",
              }}
            >
              <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                Saturn (Shani)
              </p>
              <p className="mt-1" style={{ color: "var(--text-secondary)" }}>
                Transiting <strong>{doubleTransitAnalysis.saturn.rashi}</strong> (House{" "}
                {doubleTransitAnalysis.saturn.houseFromMoon} from Moon in {natalMoon?.rashi ?? "chart"})
              </p>
              <div className="mt-1 flex flex-wrap gap-1">
                {doubleTransitAnalysis.saturn.isSadeSati && (
                  <span
                    className="rounded px-1.5 py-0.5 text-[9px] font-bold"
                    style={{ background: "rgba(239, 68, 68, 0.15)", color: "#ef4444" }}
                  >
                    Sade Sati Active
                  </span>
                )}
                {doubleTransitAnalysis.saturn.isAshtamaShani && (
                  <span
                    className="rounded px-1.5 py-0.5 text-[9px] font-bold"
                    style={{ background: "rgba(245, 158, 11, 0.15)", color: "#f59e0b" }}
                  >
                    Ashtama Shani Active
                  </span>
                )}
                {!doubleTransitAnalysis.saturn.isSadeSati &&
                  !doubleTransitAnalysis.saturn.isAshtamaShani && (
                    <span
                      className="text-[10px]"
                      style={{
                        color: doubleTransitAnalysis.saturn.isFavorable
                          ? "var(--obsidian-status-success, #10b981)"
                          : "var(--text-muted)",
                      }}
                    >
                      {doubleTransitAnalysis.saturn.isFavorable
                        ? "✓ Favorable Gochara House"
                        : "• Standard Saturn Transit"}
                    </span>
                  )}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* ── Complete Live Transit Table ────────────────────────────────────── */}
      <Card>
        <h4
          className="mb-2 text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-tertiary)" }}
        >
          All Planetary Transits Summary
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr
                className="border-b text-[10px] font-semibold uppercase tracking-wider"
                style={{
                  borderColor: "var(--border-primary)",
                  color: "var(--text-muted)",
                }}
              >
                <th className="py-2 px-2">Planet</th>
                <th className="py-2 px-2">Sign</th>
                <th className="py-2 px-2">Nakshatra</th>
                <th className="py-2 px-2">From Moon</th>
                <th className="py-2 px-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {transitPlanets.map((tp) => {
                const isActiveLord = activeLords.includes(tp.planet);
                return (
                  <tr
                    key={tp.planet}
                    style={{
                      backgroundColor: isActiveLord ? "var(--bg-card-hover, rgba(255,255,255,0.03))" : undefined,
                    }}
                  >
                    <td className="py-2 px-2 font-bold" style={{ color: isActiveLord ? "var(--accent)" : "var(--text-primary)" }}>
                      {tp.planet} {isActiveLord && "★"}
                    </td>
                    <td className="py-2 px-2" style={{ color: "var(--text-secondary)" }}>
                      {tp.transit_rashi} ({tp.transit_rashi_degree.toFixed(1)}°)
                    </td>
                    <td className="py-2 px-2" style={{ color: "var(--text-secondary)" }}>
                      {tp.transit_nakshatra} p{tp.transit_pada}
                    </td>
                    <td className="py-2 px-2 font-medium" style={{ color: "var(--text-primary)" }}>
                      H{tp.house_from_natal_moon ?? "—"}
                    </td>
                    <td className="py-2 px-2">
                      <div className="flex items-center gap-1.5">
                        {tp.is_retrograde && (
                          <span
                            className="rounded px-1 text-[9px] font-bold"
                            style={{ background: "rgba(239, 68, 68, 0.15)", color: "#ef4444" }}
                          >
                            R
                          </span>
                        )}
                        {tp.is_favorable_house !== null && (
                          <span
                            className="text-[10px]"
                            style={{
                              color: tp.is_favorable_house
                                ? "var(--obsidian-status-success, #10b981)"
                                : "var(--text-muted)",
                            }}
                          >
                            {tp.is_favorable_house ? "Favorable" : "Unfavorable"}
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
