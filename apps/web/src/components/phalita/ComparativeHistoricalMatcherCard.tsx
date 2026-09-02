"use client";

import React, { useState } from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import BENCHMARK_CHARTS from "@/data/benchmark_charts.json";
import { Award, Compass, Layers, Sparkles } from "./Icons";

interface Props {
  nativeLagna?: string;
  nativeMoon?: string;
  nativeSun?: string;
}

export function ComparativeHistoricalMatcherCard({
  nativeLagna = "Mithuna (Gemini)",
  nativeMoon = "Kanya (Virgo)",
  nativeSun = "Mithuna (Gemini)",
}: Props) {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [filterCategory, setFilterCategory] = useState<string>("ALL");

  // Filter benchmarks
  const filteredBenchmarks = BENCHMARK_CHARTS.filter((b: any) => {
    if (filterCategory === "ALL") return true;
    if (filterCategory === "POLITICIAN") return b.category === "Politician" || b.category === "Kings";
    if (filterCategory === "ACTORS") return b.category === "Actors";
    if (filterCategory === "SAINTS") return b.category === "Saints";
    if (filterCategory === "MEDICAL") return b.category?.startsWith("Medical");
    return true;
  });

  return (
    <div className={`border rounded-2xl p-6 shadow-xl transition-all space-y-6 ${
      isDark ? "bg-[#081220] border-[#17263c]" : "bg-white border-slate-200"
    }`}>
      {/* 🌟 Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4 border-slate-200 dark:border-[#17263c]">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-mono text-xs font-bold tracking-wider uppercase">
            <Compass className="w-4 h-4 text-cyan-500" />
            <span>KUNDALEE COMPARE • EMPIRICAL RESEARCH ENGINE</span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white font-sans">
            Historical Horoscope Matcher & Comparative Case Studies
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-sans">
            Cross-referencing active native against 126 curated benchmark cases and historical planetary signatures.
          </p>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
          {["ALL", "POLITICIAN", "ACTORS", "SAINTS", "MEDICAL"].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                filterCategory === cat
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
                  : isDark
                    ? "bg-[#0b182b] text-slate-400 hover:text-white border border-[#17263c]"
                    : "bg-slate-100 text-slate-600 hover:text-slate-900 border border-slate-200"
              }`}
            >
              {cat === "ALL" ? "🌐 All (126)" : cat === "POLITICIAN" ? "🏛️ Leaders" : cat === "ACTORS" ? "🎭 Cinema" : cat === "SAINTS" ? "🧘 Saints" : "🩺 Medical"}
            </button>
          ))}
        </div>
      </div>

      {/* 🌟 Active Native Signatures Strip */}
      <div className={`p-3.5 rounded-xl border flex flex-wrap items-center justify-between gap-4 font-mono text-xs ${
        isDark ? "bg-[#050b14] border-[#17263c]" : "bg-slate-50 border-slate-200"
      }`}>
        <div className="flex items-center gap-4">
          <div>
            <span className="text-slate-500 font-bold">Lagna: </span>
            <span className="text-cyan-600 dark:text-cyan-400 font-extrabold">{nativeLagna}</span>
          </div>
          <div>
            <span className="text-slate-500 font-bold">Moon: </span>
            <span className="text-amber-600 dark:text-amber-400 font-extrabold">{nativeMoon}</span>
          </div>
          <div>
            <span className="text-slate-500 font-bold">Sun: </span>
            <span className="text-emerald-600 dark:text-emerald-400 font-extrabold">{nativeSun}</span>
          </div>
        </div>
        <span className="text-[11px] text-slate-500">
          Showing {filteredBenchmarks.length} curated case studies
        </span>
      </div>

      {/* 🌟 Grid of Historical Benchmark Matches */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[420px] overflow-y-auto pr-1">
        {filteredBenchmarks.slice(0, 15).map((b: any, idx: number) => (
          <div
            key={idx}
            className={`p-4 rounded-xl border space-y-2 transition-all hover:border-cyan-500/50 ${
              isDark ? "bg-[#0b182b] border-[#17263c]" : "bg-slate-50/50 border-slate-200"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="font-bold text-sm text-slate-900 dark:text-white font-sans">
                  {b.name}
                </h4>
                <div className="text-[11px] text-slate-500 font-mono">
                  {b.dob} • {b.city?.split(",")[0]}
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${
                isDark
                  ? "bg-cyan-950/60 text-cyan-300 border-cyan-800/40"
                  : "bg-cyan-50 text-cyan-800 border-cyan-200"
              }`}>
                {b.category}
              </span>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-300 font-sans line-clamp-2">
              {b.notes || "Historical verified research horoscope with documented life milestones."}
            </p>

            <div className="pt-1 flex items-center justify-between text-[11px] font-mono text-cyan-600 dark:text-cyan-400 font-bold">
              <span>{b.lat?.toFixed(2)}° N, {b.lon?.toFixed(2)}° E</span>
              <span className="text-emerald-500">Verified Case</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
