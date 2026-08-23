"use client";

import { useMemo, useState } from "react";
import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import {
  BAND_COLOR,
  BAND_LABEL,
  INFO_COLOR,
  buildRecommendations,
  normalizePlanetStrength,
  type NormalizedPlanetStrength,
} from "@/lib/planetStrength";
import { PlanetStrengthRadar } from "./PlanetStrengthRadar";
import { IshtaKashtaBalaPanel } from "./IshtaKashtaBalaPanel";
import { AvasthaPanel } from "./AvasthaPanel";
import { VimsopakaBalaPanel } from "./VimsopakaBalaPanel";
import { SaravaliShadbalaSuite } from "./SaravaliShadbalaSuite";
import type { PlanetStrengthSchema, ShadbalaTotalResponse, WorkflowAnalysisRequest } from "@/lib/types";

interface StrengthAnalysisCenterProps {
  strengths: PlanetStrengthSchema[];
  shadbala: ShadbalaTotalResponse[];
  request: WorkflowAnalysisRequest | null;
  activePlanet: string | null;
  pinnedPlanet: string | null;
  onPlanetHover: (planet: string | null) => void;
  onPlanetClick: (planet: string) => void;
}

type TabKey =
  | "overview"
  | "shadbala"
  | "dignity"
  | "ishtakashta"
  | "avastha"
  | "vimsopaka"
  | "matrix"
  | "recommendations"
  | "notes";

const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "shadbala", label: "Shadbala" },
  { key: "dignity", label: "Dignity & Placement" },
  { key: "ishtakashta", label: "Ishta / Kashta" },
  { key: "avastha", label: "Avastha" },
  { key: "vimsopaka", label: "Vimsopaka" },
  { key: "matrix", label: "Comparison Matrix" },
  { key: "recommendations", label: "Recommendations" },
  { key: "notes", label: "Research Notes" },
];

function ScoreBadge({ score, band }: { score: number; band: NormalizedPlanetStrength["band"] }) {
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs font-semibold"
      style={{ backgroundColor: `${BAND_COLOR[band]}26`, color: BAND_COLOR[band] }}
    >
      {score} · {BAND_LABEL[band]}
    </span>
  );
}

export function StrengthAnalysisCenter({
  strengths,
  shadbala,
  request,
  activePlanet,
  pinnedPlanet,
  onPlanetHover,
  onPlanetClick,
}: StrengthAnalysisCenterProps) {
  const [tab, setTab] = useState<TabKey>("overview");

  const planets = useMemo(() => normalizePlanetStrength(strengths, shadbala), [strengths, shadbala]);

  const overall = useMemo(() => {
    if (planets.length === 0) return 0;
    return Math.round(planets.reduce((sum, p) => sum + p.score, 0) / planets.length);
  }, [planets]);

  const ranked = useMemo(() => [...planets].sort((a, b) => b.score - a.score), [planets]);
  const strongest = ranked[0] ?? null;
  const weakest = ranked[ranked.length - 1] ?? null;
  const balance = strongest && weakest ? strongest.score - weakest.score : 0;

  const recommendations = useMemo(() => buildRecommendations(planets), [planets]);

  const active = planets.find((p) => p.planet === (pinnedPlanet ?? activePlanet)) ?? null;

  if (planets.length === 0) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No strength data available for this chart.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Hero row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="glass-card p-4">
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Overall Chart Strength</h4>
          <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{overall}<span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}> / 100</span></p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Average of all normalized planet scores</p>
        </div>
        <div className="glass-card p-4">
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Strongest Planet</h4>
          {strongest && (
            <>
              <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{PLANET_SYMBOLS[strongest.planet] ?? ""} {strongest.planet}</p>
              <ScoreBadge score={strongest.score} band={strongest.band} />
            </>
          )}
        </div>
        <div className="glass-card p-4">
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Weakest Planet</h4>
          {weakest && (
            <>
              <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{PLANET_SYMBOLS[weakest.planet] ?? ""} {weakest.planet}</p>
              <ScoreBadge score={weakest.score} band={weakest.band} />
            </>
          )}
        </div>
        <div className="glass-card p-4">
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Balance</h4>
          <p className="text-2xl font-bold" style={{ color: INFO_COLOR }}>{balance}<span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}> pts spread</span></p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Gap between strongest and weakest (normalized)</p>
        </div>
      </div>

      {/* Main High-Density Split Grid */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_390px] items-start">
        {/* Left Column: Quick Planet Cards + Active Tab Table/Panel */}
        <div className="space-y-3 min-w-0">
          {/* Quick Planet Cards */}
          <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-1.5">
            {planets.map((p) => {
              const isActive = (pinnedPlanet ?? activePlanet) === p.planet;
              return (
                <button
                  key={p.planet}
                  type="button"
                  onMouseEnter={() => onPlanetHover(p.planet)}
                  onMouseLeave={() => onPlanetHover(null)}
                  onClick={() => onPlanetClick(p.planet)}
                  className="glass-card p-2 text-center transition hover:scale-[1.02]"
                  style={{ outline: isActive ? `2px solid ${BAND_COLOR[p.band]}` : undefined }}
                >
                  <p className="text-xs font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                    {PLANET_SYMBOLS[p.planet] ?? ""} {PLANET_ABBREV[p.planet] ?? p.planet.slice(0, 2)}
                  </p>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                    <div className="h-full rounded-full" style={{ width: `${p.score}%`, backgroundColor: BAND_COLOR[p.band] }} />
                  </div>
                  <p className="mt-0.5 text-[10px]" style={{ color: "var(--text-muted)" }}>{p.score}</p>
                </button>
              );
            })}
          </div>

          {/* Sub-Tabs Bar */}
          <div className="flex flex-wrap gap-1 border-b pb-2 pt-1" style={{ borderColor: "var(--border-primary)" }} role="tablist" aria-label="Strength analysis detail tabs">
            {TABS.map((t) => (
              <button
                key={t.key}
                type="button"
                role="tab"
                aria-selected={tab === t.key}
                onClick={() => setTab(t.key)}
                className="rounded-lg px-2.5 py-1 text-xs font-medium transition"
                style={{
                  backgroundColor: tab === t.key ? "var(--accent)" : "transparent",
                  color: tab === t.key ? "var(--accent-text)" : "var(--text-secondary)",
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Active Tab Panel Content */}
          <div className="min-w-0">
            {tab === "overview" && (
              <div className="glass-card p-4 text-sm" style={{ color: "var(--text-secondary)" }}>
                {active ? (
                  <div>
                    <h3 className="mb-2 text-base font-semibold" style={{ color: "var(--text-primary)" }}>
                      {PLANET_SYMBOLS[active.planet] ?? ""} {active.planet}
                    </h3>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                      <p>Score: <span style={{ color: "var(--text-primary)" }}>{active.score} / 100</span></p>
                      <p>Band: <ScoreBadge score={active.score} band={active.band} /></p>
                      <p>House: <span style={{ color: "var(--text-primary)" }}>{active.houseNumber}</span></p>
                      <p>Dignity: <span style={{ color: "var(--text-primary)" }}>{active.dignity ?? "—"}</span></p>
                      {active.rupas !== null && <p>Shadbala: <span style={{ color: "var(--text-primary)" }}>{active.rupas.toFixed(2)} rupas</span></p>}
                      {active.ratio !== null && <p>Vs. minimum: <span style={{ color: "var(--text-primary)" }}>{active.ratio.toFixed(2)}×</span></p>}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs">Hover or click a planet card above to see its detail here.</p>
                )}
              </div>
            )}

            {tab === "shadbala" && (
              <SaravaliShadbalaSuite
                request={request}
                activePlanet={pinnedPlanet ?? activePlanet}
                onPlanetSelect={onPlanetClick}
              />
            )}

            {tab === "dignity" && (
              <div className="glass-card overflow-x-auto p-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Dignity &amp; Placement</h3>
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-[11px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                      <th className="pb-2 pr-3">Planet</th>
                      <th className="pb-2 pr-3">Dignity</th>
                      <th className="pb-2 pr-3">House</th>
                      <th className="pb-2">Flags</th>
                    </tr>
                  </thead>
                  <tbody>
                    {planets.map((p) => (
                      <tr key={p.planet} className="border-t" style={{ borderColor: "var(--border-primary)" }}>
                        <td className="py-1.5 pr-3 font-medium" style={{ color: "var(--text-primary)" }}>{PLANET_SYMBOLS[p.planet] ?? ""} {p.planet}</td>
                        <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{p.dignity ?? "—"}</td>
                        <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{p.houseNumber}</td>
                        <td className="py-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
                          {[p.isExalted && "Exalted", p.isDebilitated && "Debilitated", p.isOwnSign && "Own Sign", p.isInKendra && "Kendra", p.isInTrikona && "Trikona", p.isInDusthana && "Dusthana", p.isRetrograde && "Retrograde", p.isCombust && "Combust"].filter(Boolean).join(", ") || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {tab === "ishtakashta" && <IshtaKashtaBalaPanel request={request} />}
            {tab === "avastha" && <AvasthaPanel request={request} />}

            {tab === "vimsopaka" && <VimsopakaBalaPanel request={request} />}

            {tab === "matrix" && (
              <div className="glass-card overflow-x-auto p-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Comparison Matrix</h3>
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-[11px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
                      <th className="pb-2 pr-3">Planet</th>
                      <th className="pb-2 pr-3">Score</th>
                      <th className="pb-2 pr-3">Band</th>
                      <th className="pb-2 pr-3">Rupas</th>
                      <th className="pb-2 pr-3">Ratio</th>
                      <th className="pb-2">Composite</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranked.map((p) => (
                      <tr key={p.planet} className="border-t" style={{ borderColor: "var(--border-primary)" }}>
                        <td className="py-1.5 pr-3 font-medium" style={{ color: "var(--text-primary)" }}>{PLANET_SYMBOLS[p.planet] ?? ""} {p.planet}</td>
                        <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{p.score}</td>
                        <td className="py-1.5 pr-3"><ScoreBadge score={p.score} band={p.band} /></td>
                        <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{p.rupas?.toFixed(2) ?? "—"}</td>
                        <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{p.ratio ? `${p.ratio.toFixed(2)}×` : "—"}</td>
                        <td className="py-1.5" style={{ color: "var(--text-secondary)" }}>{p.compositeScore.toFixed(1)} / 10</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {tab === "recommendations" && (
              <div className="glass-card p-4">
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Recommendations</h3>
                {recommendations.length === 0 ? (
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>No notable flags — this chart's planets are broadly balanced.</p>
                ) : (
                  <ul className="space-y-1.5 text-xs">
                    {recommendations.map((r, i) => {
                      const color = r.severity === "critical" ? BAND_COLOR.weak : r.severity === "caution" ? BAND_COLOR.average : r.severity === "opportunity" ? BAND_COLOR.strong : INFO_COLOR;
                      return (
                        <li key={`${r.planet}-${r.ruleId}-${i}`} className="flex gap-2 rounded-lg p-2" style={{ backgroundColor: "var(--bg-card)" }}>
                          <span className="mt-0.5 h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: color }} />
                          <span style={{ color: "var(--text-secondary)" }}>{r.message}</span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            )}

            {tab === "notes" && (
              <div className="glass-card space-y-2 p-4 text-xs" style={{ color: "var(--text-muted)" }}>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Research Notes</h3>
                <p>Normalized score = 65% Shadbala-vs-classical-minimum ratio + 35% dignity/placement composite.</p>
                <p>Weak/Average/Strong bands: &lt;40 weak, 40-69 average, ≥70 strong.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Radar Chart + Compact Ranking */}
        <div className="space-y-3">
          <PlanetStrengthRadar strengths={strengths} shadbala={shadbala} />

          <div className="glass-card p-3">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Planet Strength Ranking</h3>
            <ol className="space-y-1 text-xs">
              {ranked.map((p, i) => (
                <li
                  key={p.planet}
                  onClick={() => onPlanetClick(p.planet)}
                  className="flex items-center justify-between rounded px-2 py-1 cursor-pointer transition hover:bg-slate-800/40"
                  style={{ backgroundColor: (pinnedPlanet ?? activePlanet) === p.planet ? "var(--bg-card)" : "transparent" }}
                >
                  <span style={{ color: "var(--text-secondary)" }}>
                    <span className="mr-1.5 inline-block w-3 text-right text-[11px]" style={{ color: "var(--text-muted)" }}>{i + 1}</span>
                    {PLANET_SYMBOLS[p.planet] ?? ""} {p.planet}
                  </span>
                  <ScoreBadge score={p.score} band={p.band} />
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StrengthAnalysisCenter;
