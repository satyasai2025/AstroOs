'use client';

import React, { useState, useEffect, useMemo } from "react";

import { useTheme } from "@/components/layout/ThemeProvider";
import {
  phalitaApi,
  DivisionalExplorationResponse,
} from "@/lib/phalitaApi";
import { VargaChartData, VargaPlacement } from "@/lib/vargaCalculator";
import { ChartFormData } from "@/components/consultation/ChartInputModal";
import { DiamondChart } from "./DiamondChart";

import {
  Layers,
  Sparkles,
  Activity,
  ShieldCheck,
  Compass,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ChevronRight,
  TrendingUp,
} from "./Icons";

interface DivisionalDashaExplorerProps {
  chartProfile: ChartFormData;
  targetDateIso?: string;
}

const SUPPORTED_VARGAS = [
  { num: 1, code: "D1", name: "Rashi", sanskrit: "Lagna", weight: 3.0 },
  { num: 2, code: "D2", name: "Hora", sanskrit: "Sampatti", weight: 1.5 },
  { num: 3, code: "D3", name: "Drekkana", sanskrit: "Bhratri", weight: 1.5 },
  { num: 4, code: "D4", name: "Chaturthamsha", sanskrit: "Bandhu", weight: 1.5 },
  { num: 7, code: "D7", name: "Saptamsha", sanskrit: "Putra", weight: 1.5 },
  { num: 9, code: "D9", name: "Navamsha", sanskrit: "Dharma", weight: 3.0 },
  { num: 10, code: "D10", name: "Dashamsha", sanskrit: "Karma", weight: 2.0 },
  { num: 12, code: "D12", name: "Dwadashamsha", sanskrit: "Pitri", weight: 1.0 },
  { num: 24, code: "D24", name: "Chaturvimshamsha", sanskrit: "Siddhamsha", weight: 1.0 },
  { num: 30, code: "D30", name: "Trimshamsha", sanskrit: "Arishta", weight: 1.0 },
  { num: 60, code: "D60", name: "Shashtiamsha", sanskrit: "Karma-Bija", weight: 4.0 },
];

function titleCase(str?: string | null): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

export const DivisionalDashaExplorer: React.FC<DivisionalDashaExplorerProps> = ({
  chartProfile,
  targetDateIso,
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [selectedVarga, setSelectedVarga] = useState<number>(9);
  const [data, setData] = useState<DivisionalExplorationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const getComputedUtcIso = (profile: ChartFormData): string => {
    if (!profile.dob || !profile.tob) return new Date().toISOString();
    const isIndia = profile.lon >= 68 && profile.lon <= 98 && profile.lat >= 6 && profile.lat <= 38;
    const offsetStr = isIndia ? "+05:30" : "Z";
    const dt = new Date(`${profile.dob}T${profile.tob}${offsetStr}`);
    return dt.toISOString();
  };

  const fetchVargaData = async (vargaNum: number) => {
    try {
      setLoading(true);
      setError(null);
      const iso = getComputedUtcIso(chartProfile);
      const res = await phalitaApi.getDivisionalExploration({
        birth_date_iso: iso,
        latitude: chartProfile.lat,
        longitude: chartProfile.lon,
        varga_number: vargaNum,
        target_date_iso: targetDateIso,
        ayanamsa: "lahiri",
      });
      setData(res);
    } catch (err: any) {
      console.error("Divisional Exploration Error:", err);
      setError(err?.message || "Failed to load divisional chart data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVargaData(selectedVarga);
  }, [chartProfile, selectedVarga, targetDateIso]);

  const vargaChartData = useMemo<VargaChartData | null>(() => {
    if (!data) return null;
    const ascRashiNum = data.ascendant_rashi_idx + 1;
    const housesRecord: Record<number, { rashiNumber: number; planets: VargaPlacement[] }> = {};
    for (let h = 1; h <= 12; h++) {
      const rNum = ((ascRashiNum - 1 + (h - 1)) % 12) + 1;
      housesRecord[h] = { rashiNumber: rNum, planets: [] };
    }
    for (const p of data.planets) {
      const hNum = p.house_number;
      if (housesRecord[hNum]) {
        housesRecord[hNum].planets.push({
          planet: titleCase(p.planet),
          glyph: p.planet.slice(0, 2),
          rashiNumber: p.rashi_index + 1,
          rashiName: titleCase(p.rashi),
          rashiDeg: p.rashi_degree,
          houseNumber: p.house_number,
          dignity: p.dignity_label,
          score: p.final_varga_strength,
          status: p.dignity_label as any,
          color: "#991b1b",
          textCol: "#ffffff",
        });
      }
    }
    return {
      vargaCode: data.varga_code,
      vargaName: data.varga_name,
      domain: data.significations,
      weight: data.vimshopaka_weight,
      ascendantRashi: ascRashiNum,
      ascendantName: titleCase(data.ascendant_rashi),
      centerRashis: {
        h1: ascRashiNum,
        h4: ((ascRashiNum + 2) % 12) + 1,
        h7: ((ascRashiNum + 5) % 12) + 1,
        h10: ((ascRashiNum + 8) % 12) + 1,
      },
      houses: housesRecord,
      indicators: {
        ascendant: data.ascendant_rashi,
        lord: "",
        tenthHouse: "",
        ak: "",
        weight: data.vimshopaka_weight,
        activation: "",
      },
      signalMetrics: [],
      potentialScore: 100,
      vimshopakaPlanets: [],
    };
  }, [data]);

  return (
    <div className={`p-6 rounded-2xl border space-y-6 ${
      isDark ? "bg-[#0a101d] border-[#17263c]" : "bg-white border-slate-200 shadow-sm"
    }`}>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4 border-slate-700/30">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <h2 className={`text-lg font-bold ${isDark ? "text-slate-100" : "text-slate-800"}`}>
              Multi-Varga & Divisional Vimshottari Explorer
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Independent Divisional 5-Level Dasha + Bhavottama (Kimshuka) Diagnostics + Vimshopaka Fusion
          </p>
        </div>

        {data && (
          <div className="flex items-center gap-2">
            <span className={`text-xs px-3 py-1 rounded-full border font-mono font-medium ${
              isDark ? "bg-indigo-950/60 border-indigo-700 text-indigo-300" : "bg-indigo-50 border-indigo-200 text-indigo-700"
            }`}>
              Weight: {data.vimshopaka_weight.toFixed(1)} / 20 pts
            </span>
          </div>
        )}
      </div>

      {/* Varga Selection Tabs */}
      <div className="flex flex-wrap gap-2 pb-2">
        {SUPPORTED_VARGAS.map((v) => {
          const isSelected = selectedVarga === v.num;
          return (
            <button
              key={v.num}
              onClick={() => setSelectedVarga(v.num)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all cursor-pointer flex items-center gap-1.5 ${
                isSelected
                  ? isDark
                    ? "bg-indigo-600 border-indigo-400 text-white shadow-md shadow-indigo-950/50"
                    : "bg-indigo-600 border-indigo-500 text-white shadow-sm"
                  : isDark
                  ? "bg-[#0c1424] border-[#1a283c] text-slate-400 hover:border-indigo-700 hover:text-slate-200"
                  : "bg-slate-50 border-slate-200 text-slate-600 hover:border-indigo-300"
              }`}
            >
              <span className="font-mono">{v.code}</span>
              <span className="text-[11px] opacity-80">{v.name}</span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs font-mono text-slate-400 animate-pulse">
          Computing independent {selectedVarga ? `D${selectedVarga}` : ""} divisional matrix & running dashas…
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs font-mono">
          {error}
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Varga Overview Banner */}
          <div className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-3 ${
            isDark ? "bg-[#0c1629] border-indigo-900/40" : "bg-indigo-50/70 border-indigo-200"
          }`}>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-indigo-400">{data.varga_code} ({data.varga_name})</span>
                <span className="text-xs text-slate-400 font-mono">• Ascendant: {data.ascendant_rashi} {data.ascendant_degree}°</span>
              </div>
              <p className={`text-xs mt-1 ${isDark ? "text-slate-300" : "text-slate-600"}`}>
                {data.significations}
              </p>
            </div>

            {data.bhavottama_planets.length > 0 ? (
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[11px] font-bold text-amber-400 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Bhavottama:
                </span>
                {data.bhavottama_planets.map((bp) => (
                  <span key={bp} className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-400/10 text-amber-300 border border-amber-400/30">
                    {bp} (Same H in D1 & {data.varga_code})
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-xs text-slate-400 italic">No direct Bhavottama alignment in {data.varga_code}</span>
            )}
          </div>

          {/* Main 2-Column Explorer Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: Diamond Chart (5 Cols) */}
            <div className="lg:col-span-5 p-4 rounded-xl border flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
              <div className="w-full flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" />
                  {data.varga_code} Divisional Chart (North Indian)
                </span>
                <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400">Lagna {data.ascendant_rashi}</span>
              </div>

              <div className="w-full max-w-[340px] aspect-square">
                {vargaChartData && <DiamondChart vargaData={vargaChartData} />}
              </div>
            </div>


            {/* Right: Dasha Confluence & Dignity Matrix (7 Cols) */}
            <div className="lg:col-span-7 space-y-4">
              {/* Active Divisional Vimshottari Window */}
              <div className="p-4 rounded-xl border bg-white dark:bg-slate-900/90 border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                      Active {data.varga_code} Vimshottari Dasha
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-cyan-700 dark:text-cyan-400 font-semibold">
                    Target: {data.active_divisional_dasha.target_date}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2.5 rounded-lg border bg-cyan-50/50 dark:bg-slate-800/80 border-cyan-200 dark:border-cyan-900/40">
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-mono">Mahadasha (MD)</div>
                    <div className="text-sm font-bold text-cyan-700 dark:text-cyan-300">{data.active_divisional_dasha.mahadasha_lord}</div>
                    <div className="text-[9px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                      {data.active_divisional_dasha.md_start_date} → {data.active_divisional_dasha.md_end_date}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg border bg-indigo-50/50 dark:bg-slate-800/80 border-indigo-200 dark:border-indigo-900/40">
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-mono">Antardasha (AD)</div>
                    <div className="text-sm font-bold text-indigo-700 dark:text-indigo-300">{data.active_divisional_dasha.antardasha_lord}</div>
                    <div className="text-[9px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                      {data.active_divisional_dasha.ad_start_date} → {data.active_divisional_dasha.ad_end_date}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg border bg-purple-50/50 dark:bg-slate-800/80 border-purple-200 dark:border-purple-900/40">
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-mono">Pratyantar (PD)</div>
                    <div className="text-sm font-bold text-purple-700 dark:text-purple-300">{data.active_divisional_dasha.pratyantardasha_lord}</div>
                    <div className="text-[9px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">Micro-alignment</div>
                  </div>
                </div>
              </div>

              {/* Dual Dasha Synergy (D1 vs Dn) */}
              <div className={`p-4 rounded-xl border ${
                data.dual_dasha_comparison.is_divisional_supportive
                  ? isDark ? "bg-emerald-950/20 border-emerald-800/40" : "bg-emerald-50 border-emerald-200"
                  : isDark ? "bg-amber-950/20 border-amber-800/40" : "bg-amber-50 border-amber-200"
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-slate-300">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    Dual Dasha Confluence ($D_1 \leftrightarrow {data.varga_code}$)
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    data.dual_dasha_comparison.is_divisional_supportive
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                  }`}>
                    {data.dual_dasha_comparison.is_divisional_supportive ? "HARMONIC SYNERGY" : "DIVERTED FOCUS"}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs mb-2">
                  <div>
                    <span className="text-slate-400 text-[11px]">D1 Active Lords: </span>
                    <span className="font-bold text-slate-200">
                      {data.dual_dasha_comparison.d1_md_lord} - {data.dual_dasha_comparison.d1_ad_lord}
                    </span>
                    <span className="text-[10px] text-slate-400 ml-1">
                      (Str: {data.dual_dasha_comparison.d1_combined_strength})
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[11px]">{data.varga_code} Active Lords: </span>
                    <span className="font-bold text-slate-200">
                      {data.dual_dasha_comparison.div_md_lord} - {data.dual_dasha_comparison.div_ad_lord}
                    </span>
                    <span className="text-[10px] text-slate-400 ml-1">
                      (Str: {data.dual_dasha_comparison.div_combined_strength})
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 font-serif italic border-t pt-2 border-slate-700/30">
                  {data.dual_dasha_comparison.siddhantic_verdict}
                </p>
              </div>

              {/* Planetary Dignity & Vimshopaka Strength Breakdown */}
              <div className={`p-4 rounded-xl border ${
                isDark ? "bg-[#080f1e] border-[#17263c]" : "bg-white border-slate-200"
              }`}>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                  Planetary Dignity & Vimshopaka Score in {data.varga_code}
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead>
                      <tr className={`border-b text-[10px] text-slate-400 ${isDark ? "border-slate-800" : "border-slate-200"}`}>
                        <th className="pb-1.5 font-bold">Graha</th>
                        <th className="pb-1.5 font-bold">Rashi</th>
                        <th className="pb-1.5 font-bold">Bhava</th>
                        <th className="pb-1.5 font-bold">Dignity</th>
                        <th className="pb-1.5 font-bold">Main Str</th>
                        <th className="pb-1.5 font-bold">Varga Score</th>
                        <th className="pb-1.5 font-bold">Bhavottama</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {data.planets.map((p) => (
                        <tr key={p.planet} className="hover:bg-slate-800/20">
                          <td className="py-1.5 font-bold text-slate-200">{titleCase(p.planet)}</td>
                          <td className="py-1.5 text-slate-300 font-medium">{titleCase(p.rashi)} ({p.rashi_degree}°)</td>
                          <td className="py-1.5 text-slate-300">H{p.house_number}</td>
                          <td className="py-1.5">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                              p.dignity_score >= 7
                                ? "bg-emerald-500/20 text-emerald-300"
                                : p.dignity_score <= 3
                                ? "bg-rose-500/20 text-rose-300"
                                : "bg-slate-700 text-slate-300"
                            }`}>
                              {p.dignity_label}
                            </span>
                            {p.is_debilitation_cancelled && (
                              <span className="ml-1 text-[9px] text-amber-400 font-bold">[NB]</span>
                            )}
                          </td>
                          <td className="py-1.5 font-bold text-slate-300">{p.dignity_score}/9</td>
                          <td className="py-1.5 font-bold text-indigo-400">{p.final_varga_strength}</td>
                          <td className="py-1.5">
                            {p.is_bhavottama ? (
                              <span className="text-[10px] font-bold text-amber-400">
                                {p.bhavottama_type}
                              </span>
                            ) : (
                              <span className="text-slate-600 text-[10px]">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
