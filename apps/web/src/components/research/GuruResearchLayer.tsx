"use client";

import React, { useState, useEffect } from "react";
import {
  guruResearchApi,
  GuruRulesRegistryResponse,
  GuruChartEvaluationResponse,
  PlanetPositionInput,
} from "@/lib/guruResearch";

// Default test chart positions for interactive exploration
const SAMPLE_CHART_POSITIONS: PlanetPositionInput[] = [
  { planet: "sun", rashi: "aries", degree_in_rashi: 8.5 },
  { planet: "moon", rashi: "taurus", degree_in_rashi: 2.3 },
  { planet: "mars", rashi: "aries", degree_in_rashi: 11.2 },
  { planet: "mercury", rashi: "virgo", degree_in_rashi: 14.8 },
  { planet: "jupiter", rashi: "cancer", degree_in_rashi: 4.1 },
  { planet: "venus", rashi: "pisces", degree_in_rashi: 22.5 },
  { planet: "saturn", rashi: "libra", degree_in_rashi: 16.0 },
  { planet: "rahu", rashi: "gemini", degree_in_rashi: 18.0 },
  { planet: "ketu", rashi: "sagittarius", degree_in_rashi: 18.0 },
];

export function GuruResearchLayer() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [rules, setRules] = useState<GuruRulesRegistryResponse | null>(null);
  const [evaluation, setEvaluation] = useState<GuruChartEvaluationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showRulesMap, setShowRulesMap] = useState(false);
  const [positions, setPositions] = useState<PlanetPositionInput[]>(SAMPLE_CHART_POSITIONS);
  const [selectedPlanetIndex, setSelectedPlanetIndex] = useState(0);

  // Load registered rules when component mounts
  useEffect(() => {
    guruResearchApi
      .getRules()
      .then((data) => setRules(data))
      .catch((err) => console.error("Error loading Guru Research rules:", err));
  }, []);

  // Run evaluation when enabled or when positions change
  useEffect(() => {
    if (!isEnabled) return;
    setLoading(true);
    guruResearchApi
      .evaluate({ positions })
      .then((res) => setEvaluation(res))
      .catch((err) => console.error("Error evaluating chart in Guru Layer:", err))
      .finally(() => setLoading(false));
  }, [isEnabled, positions]);

  const activePlanet = positions[selectedPlanetIndex] || positions[0];
  const activeEval = evaluation?.evaluations?.find(
    (e) => e.planet.toLowerCase() === activePlanet.planet.toLowerCase()
  );

  const activeRashiRules = rules?.partitions?.[activePlanet.rashi.toLowerCase()] || [];

  return (
    <div className="rounded-xl border border-indigo-500/20 bg-gradient-to-b from-indigo-950/20 via-slate-900/60 to-slate-950 p-5 shadow-xl backdrop-blur-md">
      {/* Header & Toggle Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-indigo-500/20 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-indigo-400 animate-pulse" />
            <h2 className="text-base font-semibold text-white tracking-wide flex items-center gap-2">
              Guru Research Layer
              <span className="rounded-full bg-indigo-500/20 border border-indigo-400/30 px-2 py-0.5 text-[10px] font-medium text-indigo-300">
                Custom Research Paradigm
              </span>
            </h2>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Sign degree-slice partition system &amp; non-classical dignity analysis
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setShowRulesMap(!showRulesMap)}
            className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 text-slate-300 hover:text-white hover:border-slate-600 transition"
          >
            {showRulesMap ? "Hide Partition Map" : "View Partition Map (12 Signs)"}
          </button>

          <button
            type="button"
            onClick={() => setIsEnabled(!isEnabled)}
            className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition shadow-sm ${
              isEnabled
                ? "bg-indigo-600 text-white shadow-indigo-500/25 shadow-md ring-2 ring-indigo-400/40"
                : "bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isEnabled ? "bg-white animate-ping" : "bg-slate-500"
              }`}
            />
            {isEnabled ? "Layer Active" : "Enable Guru Layer"}
          </button>
        </div>
      </div>

      {!isEnabled ? (
        <div className="mt-5 rounded-lg border border-dashed border-slate-800 bg-slate-900/40 p-6 text-center">
          <p className="text-sm text-slate-400">
            Guru Research Layer is currently <strong className="text-slate-300">Inactive</strong>.
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Enable the toggle above to evaluate birth charts against your teacher&apos;s custom degree-partition rules.
          </p>
        </div>
      ) : (
        <div className="mt-5 space-y-6">
          {/* Summary Stats */}
          {evaluation && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3">
                <div className="text-[11px] font-medium text-slate-400">Total Grahas Evaluated</div>
                <div className="mt-1 text-lg font-bold text-white">{evaluation.evaluations.length}</div>
              </div>
              <div className="rounded-lg border border-emerald-900/30 bg-emerald-950/20 p-3">
                <div className="text-[11px] font-medium text-emerald-400">Parashari &amp; Guru Alignments</div>
                <div className="mt-1 text-lg font-bold text-emerald-300">{evaluation.agreements_count}</div>
              </div>
              <div className="rounded-lg border border-amber-900/30 bg-amber-950/20 p-3">
                <div className="text-[11px] font-medium text-amber-400">Research Divergences / Zones</div>
                <div className="mt-1 text-lg font-bold text-amber-300">{evaluation.deviations_count}</div>
              </div>
            </div>
          )}

          {/* Interactive Graha Inspector & Degree Slice Visualizer */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/90 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <span className="text-xs font-semibold text-slate-300">
                Interactive Graha Zone Inspector
              </span>
              <div className="flex flex-wrap gap-1">
                {positions.map((p, idx) => (
                  <button
                    key={p.planet}
                    type="button"
                    onClick={() => setSelectedPlanetIndex(idx)}
                    className={`px-2 py-1 text-xs rounded transition uppercase font-mono ${
                      selectedPlanetIndex === idx
                        ? "bg-indigo-600 text-white font-bold"
                        : "bg-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {p.planet.slice(0, 3)}
                  </button>
                ))}
              </div>
            </div>

            {/* Visual Degree Slice Bar (0° - 30°) */}
            <div className="mt-4">
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>
                  <strong className="text-white capitalize">{activePlanet.planet}</strong> in{" "}
                  <strong className="text-indigo-300 capitalize">{activePlanet.rashi}</strong> at{" "}
                  <span className="text-amber-400 font-mono">{activePlanet.degree_in_rashi.toFixed(2)}°</span>
                </span>
                <span className="text-slate-400 font-mono">Sign Span: 0° — 30°</span>
              </div>

              {/* Multi-segment zone bar */}
              <div className="relative h-6 w-full rounded-md bg-slate-800 overflow-hidden flex border border-slate-700">
                {activeRashiRules.map((rule, idx) => {
                  const widthPct = ((rule.end_deg - rule.start_deg) / 30) * 100;
                  const isCurrentZone =
                    activePlanet.degree_in_rashi >= rule.start_deg &&
                    activePlanet.degree_in_rashi <= rule.end_deg;
                  return (
                    <div
                      key={idx}
                      style={{ width: `${widthPct}%` }}
                      className={`h-full relative flex items-center justify-center text-[9px] font-semibold border-r border-slate-900/60 truncate px-1 transition-all ${
                        isCurrentZone
                          ? "bg-indigo-600 text-white ring-2 ring-indigo-300 z-10"
                          : idx % 2 === 0
                          ? "bg-slate-700/60 text-slate-300"
                          : "bg-slate-800/80 text-slate-400"
                      }`}
                      title={`${rule.description} (${rule.start_deg}° - ${rule.end_deg}°)`}
                    >
                      {rule.ruling_planet.slice(0, 2).toUpperCase()} ({rule.start_deg}-{rule.end_deg}°)
                    </div>
                  );
                })}

                {/* Cursor indicator for planet degree */}
                <div
                  className="absolute top-0 bottom-0 w-1 bg-amber-400 shadow-[0_0_8px_#f59e0b] z-20"
                  style={{
                    left: `${(activePlanet.degree_in_rashi / 30) * 100}%`,
                  }}
                />
              </div>

              {activeEval && (
                <div className="mt-3 rounded bg-slate-950/60 border border-slate-800 p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Guru Research Zone:</span>
                    <span className="font-semibold text-indigo-300">{activeEval.guru_zone_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Zone Ruler / Lord:</span>
                    <span className="font-semibold text-white capitalize">{activeEval.guru_zone_lord}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Classical Parashari Dignity:</span>
                    <span className="font-semibold text-emerald-400 capitalize">
                      {activeEval.classical_dignity || "Neutral"}
                    </span>
                  </div>
                  <div className="pt-1 text-[11px] text-slate-400 border-t border-slate-800/60 mt-1">
                    {activeEval.notes}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Comparative Table */}
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-3 py-2.5">Planet</th>
                  <th className="px-3 py-2.5">Rashi &amp; Degree</th>
                  <th className="px-3 py-2.5">Classical Dignity</th>
                  <th className="px-3 py-2.5">Guru Research Zone</th>
                  <th className="px-3 py-2.5">Zone Ruler</th>
                  <th className="px-3 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                {evaluation?.evaluations.map((item) => (
                  <tr key={item.planet} className="hover:bg-slate-800/30 transition">
                    <td className="px-3 py-2 font-medium capitalize text-white">{item.planet}</td>
                    <td className="px-3 py-2 font-mono text-slate-300 capitalize">
                      {item.rashi} ({item.degree_in_rashi.toFixed(1)}°)
                    </td>
                    <td className="px-3 py-2">
                      <span className="inline-block rounded bg-slate-800 px-2 py-0.5 font-medium text-slate-300 capitalize">
                        {item.classical_dignity || "Neutral"}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-indigo-300 font-medium">{item.guru_zone_name}</td>
                    <td className="px-3 py-2 capitalize text-slate-300">{item.guru_zone_lord}</td>
                    <td className="px-3 py-2">
                      {item.is_ruler_match ? (
                        <span className="rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.5 text-[10px] font-semibold">
                          Direct Ruler
                        </span>
                      ) : (
                        <span className="rounded bg-slate-800 text-slate-400 border border-slate-700 px-1.5 py-0.5 text-[10px]">
                          Guest Graha
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Rules Reference Drawer / Accordion */}
      {showRulesMap && rules && (
        <div className="mt-5 rounded-lg border border-indigo-500/20 bg-slate-950 p-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 mb-3 flex items-center justify-between">
            <span>Teacher&apos;s 12-Rashi Partition Rules Reference</span>
            <span className="text-[10px] font-normal text-slate-400">
              Extensible Engine (Ready for additional rashi rules)
            </span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs">
            {Object.entries(rules.partitions).map(([rashi, rlist]) => (
              <div key={rashi} className="rounded border border-slate-800 bg-slate-900/70 p-2.5">
                <div className="font-semibold text-white capitalize border-b border-slate-800 pb-1 mb-1.5">
                  {rashi}
                </div>
                <ul className="space-y-1 text-[11px] text-slate-300">
                  {rlist.map((r, i) => (
                    <li key={i} className="flex items-start justify-between gap-1">
                      <span className="text-slate-400">{r.description}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
