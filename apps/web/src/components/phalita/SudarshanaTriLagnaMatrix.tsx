'use client';

import React, { useState, useMemo } from "react";
import { SudarshanaChakraSynthesis, ChartPlanetPosition } from "@/lib/phalitaApi";
import { Sparkles, Compass } from "./Icons";
import { useTheme } from "@/components/layout/ThemeProvider";
import { RASHI_NAMES } from "@/lib/vargaCalculator";

interface Props {
  sudarshana: SudarshanaChakraSynthesis;
  natalPlanets?: ChartPlanetPosition[];
}

const PLANET_SYMBOLS: Record<string, string> = {
  Sun: "☉",
  Moon: "☽",
  Mars: "♂",
  Mercury: "☿",
  Jupiter: "♃",
  Venus: "♀",
  Saturn: "♄",
  Rahu: "☊",
  Ketu: "☋",
};

const PLANET_COLORS: Record<string, string> = {
  Sun: "text-amber-500",
  Moon: "text-slate-400 dark:text-slate-200",
  Mars: "text-rose-500",
  Mercury: "text-emerald-500",
  Jupiter: "text-amber-500",
  Venus: "text-teal-500 dark:text-teal-300",
  Saturn: "text-indigo-500 dark:text-indigo-400",
  Rahu: "text-purple-500",
  Ketu: "text-pink-500",
};

const RASHI_LIST_LOWER = [
  "aries", "taurus", "gemini", "cancer",
  "leo", "virgo", "libra", "scorpio",
  "sagittarius", "capricorn", "aquarius", "pisces"
];

const RASHI_DETAILS = [
  { name: "Aries", symbol: "♈", short: "Ari" },
  { name: "Taurus", symbol: "♉", short: "Tau" },
  { name: "Gemini", symbol: "♊", short: "Gem" },
  { name: "Cancer", symbol: "♋", short: "Can" },
  { name: "Leo", symbol: "♌", short: "Leo" },
  { name: "Virgo", symbol: "♍", short: "Vir" },
  { name: "Libra", symbol: "♎", short: "Lib" },
  { name: "Scorpio", symbol: "♏", short: "Sco" },
  { name: "Sagittarius", symbol: "♐", short: "Sag" },
  { name: "Capricorn", symbol: "♑", short: "Cap" },
  { name: "Aquarius", symbol: "♒", short: "Aqu" },
  { name: "Pisces", symbol: "♓", short: "Pis" },
];

export const SudarshanaTriLagnaMatrix: React.FC<Props> = ({ sudarshana, natalPlanets }) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [viewMode, setViewMode] = useState<"table" | "chakra">("table");

  const lagnaIdx = RASHI_LIST_LOWER.indexOf((sudarshana.lagna_rashi || "gemini").toLowerCase());
  const moonIdx = RASHI_LIST_LOWER.indexOf((sudarshana.moon_rashi || "scorpio").toLowerCase());
  const sunIdx = RASHI_LIST_LOWER.indexOf((sudarshana.sun_rashi || "gemini").toLowerCase());

  const lagnaRashiNum = lagnaIdx >= 0 ? lagnaIdx + 1 : 3;
  const moonRashiNum = moonIdx >= 0 ? moonIdx + 1 : 8;
  const sunRashiNum = sunIdx >= 0 ? sunIdx + 1 : 3;

  const rows = useMemo(() => {
    const matrix: Record<number, {
      house: number;
      lagnaRashi: { name: string; symbol: string; short: string };
      chandraRashi: { name: string; symbol: string; short: string };
      suryaRashi: { name: string; symbol: string; short: string };
      lagna: string[];
      chandra: string[];
      surya: string[];
    }> = {};

    for (let h = 1; h <= 12; h++) {
      const lR = RASHI_DETAILS[(lagnaRashiNum - 1 + (h - 1)) % 12];
      const cR = RASHI_DETAILS[(moonRashiNum - 1 + (h - 1)) % 12];
      const sR = RASHI_DETAILS[(sunRashiNum - 1 + (h - 1)) % 12];

      matrix[h] = {
        house: h,
        lagnaRashi: lR,
        chandraRashi: cR,
        suryaRashi: sR,
        lagna: [],
        chandra: [],
        surya: [],
      };
    }

    if (natalPlanets && natalPlanets.length > 0) {
      for (const p of natalPlanets) {
        const pRashiIdx = RASHI_LIST_LOWER.indexOf(p.rashi.toLowerCase());
        const pRashiNum = pRashiIdx >= 0 ? pRashiIdx + 1 : 1;
        const hLagna = ((pRashiNum - lagnaRashiNum + 12) % 12) + 1;
        const hChandra = ((pRashiNum - moonRashiNum + 12) % 12) + 1;
        const hSurya = ((pRashiNum - sunRashiNum + 12) % 12) + 1;

        if (matrix[hLagna]) matrix[hLagna].lagna.push(p.planet);
        if (matrix[hChandra]) matrix[hChandra].chandra.push(p.planet);
        if (matrix[hSurya]) matrix[hSurya].surya.push(p.planet);
      }
    } else {
      // Default fallback derived from profiles
      const profilePlanets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"];
      profilePlanets.forEach((pl, i) => {
        const hL = (i % 12) + 1;
        const hC = ((i + 5) % 12) + 1;
        const hS = ((i + 8) % 12) + 1;
        matrix[hL].lagna.push(pl);
        matrix[hC].chandra.push(pl);
        matrix[hS].surya.push(pl);
      });
    }

    return Object.values(matrix);
  }, [lagnaRashiNum, moonRashiNum, sunRashiNum, natalPlanets]);

  const renderCell = (rashi: { name: string; symbol: string; short: string }, planets: string[]) => {
    return (
      <div className="flex flex-col gap-1">
        <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono flex items-center gap-1">
          <span>{rashi.symbol}</span>
          <span>{rashi.name}</span>
        </span>
        {planets && planets.length > 0 ? (
          <div className="flex flex-wrap items-center gap-1.5 font-sans text-xs">
            {planets.map((p, idx) => {
              const name = p.charAt(0).toUpperCase() + p.slice(1).toLowerCase();
              const symbol = PLANET_SYMBOLS[name] || "";
              const color = PLANET_COLORS[name] || "text-slate-600 dark:text-slate-300";

              return (
                <span key={idx} className={`inline-flex items-center gap-1 font-medium ${color}`}>
                  <span>{symbol}</span>
                  <span>{name}</span>
                </span>
              );
            })}
          </div>
        ) : (
          <span className="text-slate-400 dark:text-slate-600 text-xs font-mono">—</span>
        )}
      </div>
    );
  };

  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors space-y-4 bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
      {/* Header with Table / Concentric Chakra Toggle */}
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-cyan-500" />
            SUDARSHANA TRI-LAGNA MATRIX
          </span>
          <span className="text-[11px] text-slate-400 cursor-pointer" title="Simultaneous Lagna, Chandra & Surya Kendra evaluation">
            ⓘ
          </span>
        </div>

        <button
          onClick={() => setViewMode(viewMode === "table" ? "chakra" : "table")}
          className="px-2.5 py-1 rounded border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 hover:border-cyan-500 text-cyan-700 dark:text-cyan-300 text-[11px] font-mono font-semibold transition-all cursor-pointer flex items-center gap-1"
        >
          {viewMode === "table" ? "☸️ View Concentric Wheel" : "📊 View Matrix Table"}
        </button>
      </div>

      {viewMode === "table" ? (
        /* Matrix Table View */
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-xs font-mono">
            <thead className="uppercase tracking-wider text-[10px] border-b bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700">
              <tr>
                <th className="py-2 px-3 w-24">House</th>
                <th className="py-2 px-3 text-cyan-700 dark:text-cyan-300">
                  Lagna ({sudarshana.lagna_rashi || "Physical"})
                </th>
                <th className="py-2 px-3 text-sky-700 dark:text-sky-300">
                  Chandra ({sudarshana.moon_rashi || "Mental"})
                </th>
                <th className="py-2 px-3 text-amber-700 dark:text-amber-300">
                  Surya ({sudarshana.sun_rashi || "Soul"})
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-[11px]">
              {rows.map((r) => {
                const isKendra = [1, 4, 7, 10].includes(r.house);
                const isTrikona = [5, 9].includes(r.house);

                return (
                  <tr key={r.house} className="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                    <td className="py-2 px-3 font-bold text-cyan-700 dark:text-cyan-400 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span>H{r.house}</span>
                        {isKendra && (
                          <span className="text-[9px] font-normal px-1 rounded bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border border-cyan-500/20">
                            Kendra
                          </span>
                        )}
                        {isTrikona && (
                          <span className="text-[9px] font-normal px-1 rounded bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20">
                            Kona
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      {renderCell(r.lagnaRashi, r.lagna)}
                    </td>
                    <td className="py-2 px-3">
                      {renderCell(r.chandraRashi, r.chandra)}
                    </td>
                    <td className="py-2 px-3">
                      {renderCell(r.suryaRashi, r.surya)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        /* Concentric 3-Ring Sudarshana Chakra View */
        <div className="flex flex-col items-center justify-center p-4 border rounded-xl space-y-3 bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60">
          <svg viewBox="0 0 340 340" className="w-full max-w-[280px] text-cyan-400">
            {/* Outer Ring - Surya Lagna */}
            <circle cx="170" cy="170" r="150" fill={isDark ? "#0f172a" : "#ffffff"} stroke="#f59e0b" strokeWidth="2" strokeOpacity="0.7" />
            {/* Middle Ring - Chandra Lagna */}
            <circle cx="170" cy="170" r="105" fill={isDark ? "#1e293b" : "#f8fafc"} stroke="#0284c7" strokeWidth="2" strokeOpacity="0.7" />
            {/* Inner Ring - Lagna */}
            <circle cx="170" cy="170" r="60" fill={isDark ? "#0f172a" : "#f1f5f9"} stroke="#06b6d4" strokeWidth="2" strokeOpacity="0.8" />

            {/* 12 Radials */}
            {Array.from({ length: 12 }).map((_, i) => {
              const angle = (i * 30 * Math.PI) / 180;
              const x1 = 170 + 60 * Math.cos(angle);
              const y1 = 170 + 60 * Math.sin(angle);
              const x2 = 170 + 150 * Math.cos(angle);
              const y2 = 170 + 150 * Math.sin(angle);
              return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={isDark ? "#334155" : "#cbd5e1"} strokeWidth="1" />;
            })}

            {/* Center Label */}
            <circle cx="170" cy="170" r="28" fill={isDark ? "#050b14" : "#ffffff"} stroke="#06b6d4" strokeWidth="1.5" />
            <text x="170" y="174" fill={isDark ? "#38bdf8" : "#0284c7"} fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
              TRILAGNA
            </text>
          </svg>

          <div className="flex flex-wrap items-center justify-center gap-4 text-[11px] font-mono text-slate-500 dark:text-slate-400 pt-1">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span> Lagna ({sudarshana.lagna_rashi})</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span> Chandra ({sudarshana.moon_rashi})</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Surya ({sudarshana.sun_rashi})</span>
          </div>
        </div>
      )}
    </div>
  );
};
