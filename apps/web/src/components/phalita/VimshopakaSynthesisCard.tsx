'use client';


import React, { useState, useMemo } from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import { DivisionalSynthesisItem, ChartPlanetPosition } from "@/lib/phalitaApi";
import { generateVargaChart, SHODASHAVARGA_LIST, DEFAULT_D1_LONGITUDES } from "@/lib/vargaCalculator";
import { Layers, Sparkles, Award } from "./Icons";
import { DiamondChart } from "./DiamondChart";

interface Props {
  d10Reports: Record<string, DivisionalSynthesisItem>;
  natalPlanets?: ChartPlanetPosition[];
  natalAscendant?: { rashi: string; rashi_degree: number; sidereal_longitude: number };
}

export const VimshopakaSynthesisCard: React.FC<Props> = ({ d10Reports, natalPlanets, natalAscendant }) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [selectedVargaCode, setSelectedVargaCode] = useState<string>("D10");
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const customLongitudes = useMemo(() => {
    if (!natalPlanets || natalPlanets.length === 0) return undefined;
    const lons: Record<string, { deg: number; glyph: string; isRetro?: boolean }> = {};
    if (natalAscendant) {
      lons["Asc"] = { deg: natalAscendant.sidereal_longitude, glyph: "As" };
    }
    for (const p of natalPlanets) {
      const defaultInfo = DEFAULT_D1_LONGITUDES[p.planet];
      const baseGlyph = defaultInfo?.glyph || p.planet.slice(0, 2);
      lons[p.planet] = {
        deg: p.sidereal_longitude,
        glyph: `${baseGlyph}${p.is_retrograde ? " (R)" : ""}`,
        isRetro: p.is_retrograde,
      };
    }
    return lons;
  }, [natalPlanets, natalAscendant]);

  // 🌟 Live Classical Parashari Recalculation for the Selected Varga with real chart longitudes
  const vargaData = useMemo(() => {
    return generateVargaChart(selectedVargaCode, customLongitudes);
  }, [selectedVargaCode, customLongitudes]);

  return (
    <div className="space-y-6">
      {/* Top Row: Dynamic Varga Chart (Left), Varga Signal Strength (Mid), Insights + Potential (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Varga Chart with Compact Dropdown */}
        <div className="lg:col-span-5 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col items-center justify-between transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          {/* Card Header with Single-Line Title and Guaranteed Downward Dropdown */}
          <div className="w-full flex items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3 mb-4 relative z-30">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-1.5 whitespace-nowrap">
              <Layers className="w-4 h-4 text-cyan-500 shrink-0" />
              <span>{vargaData.vargaCode} {vargaData.vargaName.toUpperCase()}</span>
            </span>

            {/* Custom Downward Dropdown Menu */}
            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="px-3 py-1.5 rounded-lg border text-xs font-mono font-bold flex items-center gap-2 cursor-pointer transition-all shadow-sm bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-cyan-800 dark:text-cyan-200 hover:border-cyan-500"
              >
                <span>{vargaData.vargaCode} — {vargaData.vargaName}</span>
                <span className={`text-[10px] transition-transform duration-200 ${dropdownOpen ? "rotate-180" : ""}`}>
                  ▼
                </span>
              </button>

              {/* Downward Dropdown Menu Panel */}
              {dropdownOpen && (
                <div className="absolute right-0 top-full mt-1.5 w-64 max-h-72 overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-700 shadow-xl z-50 p-1.5 transition-all bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200">
                  <div className="text-[10px] font-bold font-mono text-cyan-700 dark:text-cyan-400 px-2 py-1 uppercase tracking-wider border-b border-slate-200 dark:border-slate-800 mb-1">
                    Select Shodashavarga
                  </div>
                  {SHODASHAVARGA_LIST.map((v) => {
                    const isSelected = v.code === selectedVargaCode;
                    return (
                      <button
                        key={v.code}
                        type="button"
                        onClick={() => {
                          setSelectedVargaCode(v.code);
                          setDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors flex items-center justify-between cursor-pointer ${
                          isSelected
                            ? "bg-cyan-500 text-slate-950 font-bold"
                            : "hover:bg-cyan-50 dark:hover:bg-slate-800 hover:text-cyan-900 dark:hover:text-cyan-300"
                        }`}
                      >
                        <div className="flex flex-col">
                          <span className="font-bold">{v.code} — {v.name}</span>
                          <span className={`text-[10px] ${isSelected ? "text-slate-900" : "text-slate-500 dark:text-slate-400"}`}>
                            {v.domain.split("&")[0]}
                          </span>
                        </div>
                        {isSelected && <span className="text-xs">✓</span>}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <DiamondChart vargaData={vargaData} />
        </div>

        {/* Middle: Domain Signal Strength (Live Recalculated) */}
        <div className="lg:col-span-4 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
              {vargaData.vargaCode} DOMAIN SIGNAL STRENGTH
            </span>
          </div>

          <div className="space-y-3.5 pt-1 font-mono text-xs">
            {vargaData.signalMetrics.map((m, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between items-center text-slate-700 dark:text-slate-300">
                  <span className="font-sans font-medium">{m.label}</span>
                  <span className="text-cyan-700 dark:text-cyan-300 font-bold">{m.score.toFixed(1)} / {m.max}</span>
                </div>
                <div className="w-full h-2 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800">
                  <div
                    className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                    style={{ width: `${(m.score / m.max) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Varga Insights + Potential Meter (Live Recalculated) */}
        <div className={`lg:col-span-3 border rounded-xl p-5 shadow-xl flex flex-col justify-between space-y-4 transition-colors ${
          isDark ? "bg-[#0b1424] border-[#17263c] text-slate-100" : "bg-white border-slate-200 text-slate-900"
        }`}>
          <div>
            <div className={`border-b pb-3 mb-3 ${isDark ? "border-[#17263c]" : "border-slate-200"}`}>
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                {vargaData.vargaCode} SHODASHAVARGA INSIGHTS
              </span>
            </div>
            <ul className="space-y-2 text-[11px] text-slate-700 dark:text-slate-300 font-sans leading-relaxed">
              <li className="flex items-start gap-1.5">
                <span className="text-cyan-500 mt-0.5">•</span>
                <span><strong>Governs:</strong> {vargaData.domain}.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-cyan-500 mt-0.5">•</span>
                <span><strong>Vimshopaka Weight:</strong> {vargaData.weight} / 20 points.</span>
              </li>
              <li className="flex items-start gap-1.5">
                <span className="text-cyan-500 mt-0.5">•</span>
                <span>Ascendant is <strong>{vargaData.indicators.ascendant}</strong> with 10th House in <strong>{vargaData.indicators.tenthHouse}</strong>.</span>
              </li>
            </ul>
          </div>

          {/* Potential Circular Gauge (Live Recalculated) */}
          <div className="p-4 border rounded-xl flex flex-col items-center text-center bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono mb-2">
              {vargaData.vargaCode} POTENTIAL
            </span>
            <div className="relative w-20 h-20 flex items-center justify-center">
              <svg viewBox="0 0 36 36" className="w-full h-full text-cyan-500 -rotate-90">
                <path
                  className="text-slate-200 dark:text-slate-800"
                  strokeWidth="3.5"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-cyan-500"
                  strokeDasharray={`${vargaData.potentialScore}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute text-center">
                <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                  {vargaData.potentialScore}%
                </span>
              </div>
            </div>
            <span className="text-xs font-bold text-cyan-700 dark:text-cyan-300 font-sans mt-2">
              {vargaData.potentialScore >= 75 ? "High Potential" : "Moderate Potential"}
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">Calculated from planetary dignities in {vargaData.vargaCode}.</span>
          </div>
        </div>
      </div>

      {/* Bottom Row: Key Indicators (Left 50%), Vimshopaka Bala (Right 50%) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Indicators (Live Recalculated) */}
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
              {vargaData.vargaCode} KEY INDICATORS
            </span>
          </div>

          <div className="divide-y divide-slate-200 dark:divide-slate-800 text-xs font-mono">
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-500 dark:text-slate-400 font-sans">{vargaData.vargaCode} Ascendant</span>
              <span className="font-bold text-slate-900 dark:text-white">{vargaData.indicators.ascendant}</span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-500 dark:text-slate-400 font-sans">Primary Varga Lord</span>
              <span className="font-bold text-amber-500">{vargaData.indicators.lord}</span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-500 dark:text-slate-400 font-sans">10th House in {vargaData.vargaCode}</span>
              <span className="font-bold text-slate-900 dark:text-white">{vargaData.indicators.tenthHouse}</span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-500 dark:text-slate-400 font-sans">Amatyakaraka (AK)</span>
              <span className="font-bold text-indigo-600 dark:text-indigo-300">{vargaData.indicators.ak}</span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-500 dark:text-slate-400 font-sans">Vimshopaka Weight</span>
              <span className="font-bold text-cyan-700 dark:text-cyan-300">{vargaData.indicators.weight} / 20.0 pts</span>
            </div>
            <div className="py-2.5 flex justify-between items-center">
              <span className="text-slate-500 dark:text-slate-400 font-sans">Activation Level</span>
              <span className="px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 font-bold">
                {vargaData.indicators.activation}
              </span>
            </div>
          </div>
        </div>

        {/* Vimshopaka Bala Table (Live Recalculated for this Varga) */}
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
              {vargaData.vargaCode} PLANETARY DIGNITY & VIMSHOPAKA
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="uppercase tracking-wider text-[10px] border-b bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="py-2 px-3">Planet</th>
                  <th className="py-2 px-3">Sign</th>
                  <th className="py-2 px-3">Dignity</th>
                  <th className="py-2 px-3">Strength Bar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {vargaData.vimshopakaPlanets.map((v, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                    <td className="py-1.5 px-3 font-bold text-slate-900 dark:text-white font-sans">{v.glyph} {v.planet}</td>
                    <td className="py-1.5 px-3 text-slate-600 dark:text-slate-300 font-semibold">{v.rashiName} (H{v.houseNumber})</td>
                    <td className={`py-1.5 px-3 font-medium ${v.textCol}`}>{v.dignity}</td>
                    <td className="py-1.5 px-3">
                      <div className="w-28 h-1.5 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800">
                        <div
                          className={`h-full ${v.color} rounded-full`}
                          style={{ width: `${(v.score / 20) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
