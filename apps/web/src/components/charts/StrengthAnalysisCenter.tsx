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

      {/* Per-planet cards + ranking + radar */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_380px]">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {planets.map((p) => {
              const isActive = (pinnedPlanet ?? activePlanet) === p.planet;
              return (
                <button
                  key={p.planet}
                  type="button"
                  onMouseEnter={() => onPlanetHover(p.planet)}
                  onMouseLeave={() => onPlanetHover(null)}
                  onClick={() => onPlanetClick(p.planet)}
                  className="glass-card p-3 text-left transition"
                  style={{ outline: isActive ? `2px solid ${BAND_COLOR[p.band]}` : undefined }}
                >
                  <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    {PLANET_SYMBOLS[p.planet] ?? ""} {PLANET_ABBREV[p.planet] ?? p.planet.slice(0, 2)}
                  </p>
                  <div className="mt-1.5 h-2 overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                    <div className="h-full rounded-full" style={{ width: `${p.score}%`, backgroundColor: BAND_COLOR[p.band] }} />
                  </div>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>{p.score} / 100</p>
                </button>
              );
            })}
          </div>

          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Ranking</h3>
            <ol className="space-y-1.5 text-sm">
              {ranked.map((p, i) => (
                <li key={p.planet} className="flex items-center justify-between rounded-lg px-2 py-1" style={{ backgroundColor: (pinnedPlanet ?? activePlanet) === p.planet ? "var(--bg-card)" : "transparent" }}>
                  <span style={{ color: "var(--text-secondary)" }}>
                    <span className="mr-2 inline-block w-4 text-right" style={{ color: "var(--text-muted)" }}>{i + 1}</span>
                    {PLANET_SYMBOLS[p.planet] ?? ""} {p.planet}
                  </span>
                  <ScoreBadge score={p.score} band={p.band} />
                </li>
              ))}
            </ol>
          </div>
        </div>

        <PlanetStrengthRadar strengths={strengths} shadbala={shadbala} />
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 border-b pb-2" style={{ borderColor: "var(--border-primary)" }} role="tablist" aria-label="Strength analysis detail tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
            style={{
              backgroundColor: tab === t.key ? "var(--accent)" : "transparent",
              color: tab === t.key ? "var(--accent-text)" : "var(--text-secondary)",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="glass-card p-5 text-sm" style={{ color: "var(--text-secondary)" }}>
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
            <p>Hover or click a planet card above to see its detail here.</p>
          )}
        </div>
      )}

      {tab === "shadbala" && (
        <div className="glass-card p-5">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Shadbala Breakdown</h3>
          <div className="space-y-3">
            {planets.filter((p) => p.rupas !== null).map((p) => (
              <div key={p.planet} className="flex items-center gap-3">
                <span className="w-20 flex-shrink-0 text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                  {PLANET_SYMBOLS[p.planet] ?? ""} {PLANET_ABBREV[p.planet] ?? p.planet.slice(0, 2)}
                </span>
                <div className="h-3 flex-1 overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                  <div className="h-full rounded-full" style={{ width: `${p.score}%`, backgroundColor: BAND_COLOR[p.band] }} />
                </div>
                <span className="w-28 flex-shrink-0 text-right text-xs" style={{ color: "var(--text-muted)" }}>
                  {p.rupas?.toFixed(2)} / {p.requiredRupas?.toFixed(1) ?? "—"} rupas
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "dignity" && (
        <div className="glass-card overflow-x-auto p-5">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Dignity & Placement</h3>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
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
                  <td className="py-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
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

      {tab === "vimsopaka" && (
        <div className="glass-card p-5 text-sm" style={{ color: "var(--text-muted)" }}>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Vimsopaka Bala</h3>
          <p>Not implemented — there is no Vimsopaka Bala field, engine, or endpoint anywhere in the backend today. This tab is a placeholder rather than an estimate, so it isn't confused with the other tabs' real classical calculations.</p>
        </div>
      )}

      {tab === "matrix" && (
        <div className="glass-card overflow-x-auto p-5">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Comparison Matrix</h3>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
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
        <div className="glass-card p-5">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Recommendations</h3>
          {recommendations.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>No notable flags — this chart's planets are broadly balanced.</p>
          ) : (
            <ul className="space-y-2 text-sm">
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
        <div className="glass-card space-y-2 p-5 text-xs" style={{ color: "var(--text-muted)" }}>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Research Notes</h3>
          <p>Normalized score = 65% Shadbala-vs-classical-minimum ratio (clamped at 2× = 100) + 35% dignity/placement composite (0-10, from the chart's real <code>planet_strengths</code>, backend-verified to that 0-10 range).</p>
          <p>The per-planet classical minimum Shadbala table (BPHS / B.V. Raman's "Graha and Bhava Balas") is a <strong>frontend constant</strong>, not an API value — the backend's Shadbala rule engine only implements two pragmatic ad-hoc thresholds (Jupiter/Saturn &gt; 3.5 rupas) and explicitly notes its Shadbala coverage has known gaps (Varsha/Masa lord unimplemented), so it doesn't expose a full Required Bala table itself.</p>
          <p>Rahu/Ketu and any planet without a classical Shadbala minimum fall back to the dignity/placement composite alone — no fabricated Shadbala figure is shown for them.</p>
          <p>Weak/Average/Strong bands: &lt;40 weak, 40-69 average, ≥70 strong — an AstroOS UI convention for readability, not a classical tier.</p>
          <p>"Balance" (hero row) = strongest score − weakest score. This metric doesn't exist in the backend or any classical source — it's an AstroOS-defined spread indicator, invented for this dashboard.</p>
          <p>Ishta/Kashta Bala only covers Mars/Mercury/Jupiter/Venus/Saturn (Chesta Bala isn't computed for Sun/Moon). Jagradadi Avastha is intentionally omitted — see AvasthaPanel for why.</p>
          <p>Vimsopaka Bala isn't implemented anywhere in the backend — its tab is a placeholder, not an estimate.</p>
          <p>A transit strength-over-time timeline (per-year/arbitrary-range planetary strength) is out of scope here — no backend endpoint computes it; would require new backend work, not just a frontend view.</p>
        </div>
      )}
    </div>
  );
}

export default StrengthAnalysisCenter;
