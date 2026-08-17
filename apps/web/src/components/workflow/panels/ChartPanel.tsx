"use client";

import { useState } from "react";
import type { D1ChartResponse, WorkflowAnalysisResponse } from "@/lib/types";
import { formatLongitude, formatPosition } from "@/lib/formatAstro";
import { PLANET_SYMBOLS } from "@/lib/astro";

interface ChartPanelProps {
  chart: D1ChartResponse;
  result?: WorkflowAnalysisResponse | null;
  activePlanet?: string | null;
  onPlanetClick?: (planet: string) => void;
}

type SubTab = "planets" | "bhava" | "nakshatras" | "yogas";

function getDignityBadge(dignity?: string | null) {
  if (!dignity) return null;
  const d = dignity.toLowerCase();
  if (d.includes("exalted") || d.includes("uccha")) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
        Exalted
      </span>
    );
  }
  if (d.includes("debilitated") || d.includes("neecha")) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
        Debilitated
      </span>
    );
  }
  if (d.includes("own") || d.includes("swa")) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded bg-cyan-50 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800">
        Own Sign
      </span>
    );
  }
  if (d.includes("moolatrikona")) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
        Moolatrikona
      </span>
    );
  }
  if (d.includes("friendly") || d.includes("mitra")) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
        Friendly
      </span>
    );
  }
  if (d.includes("enemy") || d.includes("shatru")) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
        Enemy
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-semibold rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 capitalize">
      {dignity}
    </span>
  );
}

export function ChartPanel({
  chart,
  result,
  activePlanet,
  onPlanetClick,
}: ChartPanelProps) {
  const [activeTab, setActiveTab] = useState<SubTab>("planets");
  const [expandData, setExpandData] = useState(false);

  const yogas = (result?.yogas?.results ?? []).filter((y) => y.is_present);

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm flex flex-col overflow-hidden h-full">
      {/* Tab Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
        {/* Tab Buttons */}
        <div className="flex items-center gap-1">
          {(
            [
              { key: "planets", label: "Planets" },
              { key: "bhava", label: "Bhava Cusps" },
              { key: "nakshatras", label: "Nakshatras" },
              { key: "yogas", label: `Yogas (${yogas.length || 0})` },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                activeTab === tab.key
                  ? "bg-cyan-500 text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Expand Data Toggle */}
        <button
          type="button"
          onClick={() => setExpandData(!expandData)}
          className="text-[11px] font-medium px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition"
          title="Toggle extra coordinates and KP Sub-Sub Lord columns"
        >
          {expandData ? "Compact View" : "+ Expand Data"}
        </button>
      </div>

      {/* Panel Body */}
      <div className="flex-1 overflow-y-auto max-h-[380px]">
        {/* TAB 1: Planets */}
        {activeTab === "planets" && (
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-400 bg-slate-50/40 dark:bg-slate-800/30 sticky top-0 z-10 backdrop-blur-sm">
                  <th className="py-1.5 px-2">Planet</th>
                  <th className="py-1.5 px-2">Rashi</th>
                  <th className="py-1.5 px-2">Degree</th>
                  <th className="py-1.5 px-2">H (Rashi)</th>
                  {expandData && <th className="py-1.5 px-2">H (Chalit)</th>}
                  <th className="py-1.5 px-2">Nakshatra</th>
                  <th className="py-1.5 px-2">Sub Lord</th>
                  {expandData && <th className="py-1.5 px-2">Sub-Sub</th>}
                  <th className="py-1.5 px-2">Dignity</th>
                  <th className="py-1.5 px-2">Flags</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {/* Ascendant Row */}
                <tr className="bg-cyan-50/20 dark:bg-cyan-950/20 font-medium">
                  <td className="py-1.5 px-2 font-bold text-cyan-600 dark:text-cyan-400 flex items-center gap-1">
                    <span className="font-mono text-sm">✦</span> Lagna
                  </td>
                  <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200 capitalize">
                    {chart.ascendant.rashi}
                  </td>
                  <td className="py-1.5 px-2 font-mono text-slate-700 dark:text-slate-300">
                    {chart.ascendant.rashi_degree.toFixed(2)}°
                  </td>
                  <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200 font-bold">
                    H1
                  </td>
                  {expandData && (
                    <td className="py-1.5 px-2 text-slate-600 dark:text-slate-400">
                      H1
                    </td>
                  )}
                  <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300">
                    {chart.ascendant.nakshatra} ({chart.ascendant.pada})
                  </td>
                  <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300 capitalize">
                    {chart.ascendant.sub_lord || "—"}
                  </td>
                  {expandData && (
                    <td className="py-1.5 px-2 text-slate-600 dark:text-slate-400 capitalize">
                      {chart.ascendant.sub_sub_lord || "—"}
                    </td>
                  )}
                  <td className="py-1.5 px-2 text-slate-500">—</td>
                  <td className="py-1.5 px-2 text-slate-500">—</td>
                </tr>

                {/* Planets Rows */}
                {chart.planets.map((p) => {
                  const isSelected = activePlanet === p.planet;
                  return (
                    <tr
                      key={p.planet}
                      onClick={() => onPlanetClick?.(p.planet)}
                      className={`cursor-pointer transition hover:bg-slate-50 dark:hover:bg-slate-800/60 ${
                        isSelected
                          ? "bg-cyan-50/40 dark:bg-cyan-950/40 font-semibold"
                          : ""
                      }`}
                    >
                      <td className="py-1.5 px-2 font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                        <span className="text-cyan-500">
                          {PLANET_SYMBOLS[p.planet] || "•"}
                        </span>
                        <span>{p.planet}</span>
                      </td>
                      <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200 capitalize">
                        {p.rashi}
                      </td>
                      <td className="py-1.5 px-2 font-mono text-slate-700 dark:text-slate-300 whitespace-nowrap">
                        {expandData
                          ? formatLongitude(p.sidereal_longitude)
                          : `${p.rashi_degree.toFixed(2)}°`}
                      </td>
                      <td className="py-1.5 px-2 font-semibold text-slate-800 dark:text-slate-200">
                        H{p.rashi_house_number}
                      </td>
                      {expandData && (
                        <td
                          className="py-1.5 px-2 font-medium"
                          style={{
                            color:
                              p.rashi_house_number !== p.house_number
                                ? "#d97706"
                                : "inherit",
                          }}
                        >
                          H{p.house_number}
                        </td>
                      )}
                      <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300">
                        {p.nakshatra} ({p.pada})
                      </td>
                      <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200 capitalize">
                        {p.sub_lord || "—"}
                      </td>
                      {expandData && (
                        <td className="py-1.5 px-2 text-slate-600 dark:text-slate-400 capitalize">
                          {p.sub_sub_lord || "—"}
                        </td>
                      )}
                      <td className="py-1.5 px-2 whitespace-nowrap">
                        {getDignityBadge(p.dignity)}
                      </td>
                      <td className="py-1.5 px-2 whitespace-nowrap">
                        <div className="flex items-center gap-1">
                          {p.is_retrograde && (
                            <span className="px-1.5 py-0.2 text-[10px] font-bold rounded bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                              ℞ Ret
                            </span>
                          )}
                          {p.is_combust && (
                            <span className="px-1.5 py-0.2 text-[10px] font-bold rounded bg-orange-50 dark:bg-orange-950/60 text-orange-600 dark:text-orange-300 border border-orange-200 dark:border-orange-800">
                              Comb
                            </span>
                          )}
                          {!p.is_retrograde && !p.is_combust && (
                            <span className="text-slate-400">—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 2: Bhava Cusps */}
        {activeTab === "bhava" && (
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-400 bg-slate-50/40 dark:bg-slate-800/30 sticky top-0 z-10 backdrop-blur-sm">
                  <th className="py-1.5 px-2.5">House</th>
                  <th className="py-1.5 px-2.5">Sign (Rashi)</th>
                  <th className="py-1.5 px-2.5">Star Lord</th>
                  <th className="py-1.5 px-2.5">KP Sub Lord</th>
                  {expandData && <th className="py-1.5 px-2.5">KP Sub-Sub</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {chart.houses.map((h) => (
                  <tr
                    key={h.house_number}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition"
                  >
                    <td className="py-1.5 px-2.5 font-bold text-slate-900 dark:text-slate-100">
                      House {h.house_number}
                    </td>
                    <td className="py-1.5 px-2.5 font-medium text-slate-800 dark:text-slate-200 capitalize">
                      {h.rashi}
                    </td>
                    <td className="py-1.5 px-2.5 text-slate-700 dark:text-slate-300 capitalize">
                      {h.nakshatra_lord || "—"}
                    </td>
                    <td className="py-1.5 px-2.5 font-semibold text-cyan-600 dark:text-cyan-400 capitalize">
                      {h.sub_lord || "—"}
                    </td>
                    {expandData && (
                      <td className="py-1.5 px-2.5 text-slate-600 dark:text-slate-400 capitalize">
                        {h.sub_sub_lord || "—"}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 3: Nakshatras */}
        {activeTab === "nakshatras" && (
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-[11px] font-semibold text-slate-600 dark:text-slate-400 bg-slate-50/40 dark:bg-slate-800/30 sticky top-0 z-10 backdrop-blur-sm">
                  <th className="py-1.5 px-2">Body</th>
                  <th className="py-1.5 px-2">Nakshatra</th>
                  <th className="py-1.5 px-2">Pada</th>
                  <th className="py-1.5 px-2">Star Lord</th>
                  <th className="py-1.5 px-2">Sub Lord</th>
                  <th className="py-1.5 px-2">Sign</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                <tr className="bg-cyan-50/20 dark:bg-cyan-950/20 font-medium">
                  <td className="py-1.5 px-2 font-bold text-cyan-600 dark:text-cyan-400">
                    Lagna
                  </td>
                  <td className="py-1.5 px-2 font-semibold text-slate-900 dark:text-slate-100">
                    {chart.ascendant.nakshatra}
                  </td>
                  <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200">
                    Pada {chart.ascendant.pada}
                  </td>
                  <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300 capitalize">
                    {chart.ascendant.nakshatra_lord || "—"}
                  </td>
                  <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300 capitalize">
                    {chart.ascendant.sub_lord || "—"}
                  </td>
                  <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200 capitalize">
                    {chart.ascendant.rashi}
                  </td>
                </tr>
                {chart.planets.map((p) => (
                  <tr
                    key={p.planet}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition"
                  >
                    <td className="py-1.5 px-2 font-semibold text-slate-900 dark:text-slate-100 capitalize">
                      {p.planet}
                    </td>
                    <td className="py-1.5 px-2 font-semibold text-slate-900 dark:text-slate-100">
                      {p.nakshatra}
                    </td>
                    <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200">
                      Pada {p.pada}
                    </td>
                    <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300 capitalize">
                      {p.nakshatra_lord || "—"}
                    </td>
                    <td className="py-1.5 px-2 text-slate-700 dark:text-slate-300 capitalize">
                      {p.sub_lord || "—"}
                    </td>
                    <td className="py-1.5 px-2 text-slate-800 dark:text-slate-200 capitalize">
                      {p.rashi}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 4: Yogas */}
        {activeTab === "yogas" && (
          <div className="p-2 space-y-2">
            {yogas.length === 0 ? (
              <p className="text-xs text-slate-500 p-3 text-center">
                No active classical yogas detected in this chart.
              </p>
            ) : (
              yogas.map((y) => (
                <div
                  key={y.yoga_id}
                  className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-bold text-xs text-slate-900 dark:text-slate-100">
                      {y.name}
                    </span>
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 capitalize">
                      {y.category || "Yoga"}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">
                    {y.source_text ? `Source: ${y.source_text}` : `Involved: ${y.involved_planets.join(", ")}`}
                  </p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Footer Info Strip */}
      <div className="px-3 py-1.5 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400">
        <span>
          Ayanamsa: {chart.ayanamsa_system} ({chart.ayanamsa_value.toFixed(2)}°)
        </span>
        <span>
          House System: {chart.house_system === "W" ? "Whole Sign" : chart.house_system} · Julian Day: {chart.julian_day.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
