"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { ResearchPatternsShell } from "@/components/research/ResearchPatternsShell";

// Mock Fallback Indicators per user request ("filhal placeholders rakho and likho mock data agar vahan kuchh nahi hai to")
function MockDataBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
      ⚠️ MOCK / PREVIEW DATA
    </span>
  );
}

export default function PatternDiscoveryPage() {
  // Filters state
  const [eventType, setEventType] = useState("Marriage");
  const [minConfidence, setMinConfidence] = useState("Any");
  const [minSupport, setMinSupport] = useState("Any");
  const [chartType, setChartType] = useState("All Charts");
  const [groupBy, setGroupBy] = useState("Auto");
  const [factorTab, setFactorTab] = useState<"planets" | "houses" | "yogas" | "dashas">("planets");

  // Top Contributing Factors
  const factorsData = {
    planets: [
      { name: "Jupiter", symbol: "♃", pct: 78, count: "10,032", color: "bg-amber-400" },
      { name: "Venus", symbol: "♀", pct: 74, count: "9,501", color: "bg-amber-400" },
      { name: "Moon", symbol: "☽", pct: 48, count: "6,167", color: "bg-emerald-400" },
      { name: "Saturn", symbol: "♄", pct: 41, count: "5,257", color: "bg-emerald-400" },
      { name: "Sun", symbol: "☉", pct: 34, count: "4,415", color: "bg-cyan-400" },
      { name: "Mercury", symbol: "☿", pct: 29, count: "3,721", color: "bg-cyan-400" },
      { name: "Mars", symbol: "♂", pct: 27, count: "3,462", color: "bg-cyan-400" },
      { name: "Rahu", symbol: "☊", pct: 21, count: "2,698", color: "bg-violet-400" },
      { name: "Ketu", symbol: "☋", pct: 18, count: "2,313", color: "bg-violet-400" },
    ],
    houses: [
      { name: "7th House", symbol: "H7", pct: 84, count: "10,787", color: "bg-amber-400" },
      { name: "1st House", symbol: "H1", pct: 62, count: "7,962", color: "bg-emerald-400" },
      { name: "5th House", symbol: "H5", pct: 55, count: "7,063", color: "bg-emerald-400" },
      { name: "9th House", symbol: "H9", pct: 49, count: "6,292", color: "bg-cyan-400" },
      { name: "10th House", symbol: "H10", pct: 38, count: "4,880", color: "bg-cyan-400" },
    ],
    yogas: [
      { name: "Gaja Kesari Yoga", symbol: "Y1", pct: 68, count: "8,732", color: "bg-amber-400" },
      { name: "Dhana Yoga", symbol: "Y2", pct: 59, count: "7,576", color: "bg-emerald-400" },
      { name: "Raja Yoga", symbol: "Y3", pct: 45, count: "5,778", color: "bg-cyan-400" },
    ],
    dashas: [
      { name: "Venus Mahadasha", symbol: "D1", pct: 81, count: "10,402", color: "bg-amber-400" },
      { name: "Jupiter Antardasha", symbol: "D2", pct: 72, count: "9,246", color: "bg-amber-400" },
      { name: "Moon Antardasha", symbol: "D3", pct: 51, count: "6,549", color: "bg-emerald-400" },
    ],
  };

  // Top Patterns Table Data
  const topPatterns = [
    { rank: 1, pattern: "Jupiter + Venus + D9 7th House Activation", badge: "D9 7th House", support: "4,550 / 5,248", conf: "87%", confLabel: "Very High", lift: "3.42", liftLabel: "Very High", confColor: "text-emerald-400 bg-emerald-500/20" },
    { rank: 2, pattern: "Venus in Kendra + Jupiter Aspect", badge: "D1 Aspect", support: "3,842 / 5,248", conf: "73%", confLabel: "High", lift: "2.81", liftLabel: "High", confColor: "text-emerald-400 bg-emerald-500/20" },
    { rank: 3, pattern: "7th Lord Strong + Jupiter Dasha", badge: "D1 Dasha", support: "3,105 / 5,248", conf: "59%", confLabel: "High", lift: "2.32", liftLabel: "High", confColor: "text-amber-400 bg-amber-500/20" },
    { rank: 4, pattern: "Venus + Moon Combination", badge: "D1 Conjunction", support: "2,798 / 5,248", conf: "53%", confLabel: "Medium", lift: "1.95", liftLabel: "Medium", confColor: "text-amber-400 bg-amber-500/20" },
    { rank: 5, pattern: "Jupiter Transit in 7th from Lagna", badge: "Transit 7th House", support: "2,642 / 5,248", conf: "50%", confLabel: "Medium", lift: "1.88", liftLabel: "Medium", confColor: "text-amber-400 bg-amber-500/20" },
    { rank: 6, pattern: "D9 Lagna Lord Strong + Venus", badge: "D9 Strength", support: "2,213 / 5,248", conf: "42%", confLabel: "Medium", lift: "1.63", liftLabel: "Medium", confColor: "text-amber-400 bg-amber-500/20" },
    { rank: 7, pattern: "Shukra Dasha + 7th House Activated", badge: "Dasha 7th House", support: "1,987 / 5,248", conf: "38%", confLabel: "Low", lift: "1.41", liftLabel: "Low", confColor: "text-rose-400 bg-rose-500/20" },
    { rank: 8, pattern: "Rahu in 7th + Venus Aspect", badge: "D1 Rahu", support: "1,642 / 5,248", conf: "31%", confLabel: "Low", lift: "1.22", liftLabel: "Low", confColor: "text-rose-400 bg-rose-500/20" },
  ];

  return (
    <ResearchPatternsShell
      title="Research Patterns"
      subtitle="Discover recurring astrological patterns across verified life events"
    >
      <div className="space-y-4 text-slate-100 font-sans">
        {/* ── Top Row: 5 KPI Cards ── */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {/* Card 1 */}
          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-3 shadow-md">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-violet-500/20 text-violet-400 font-bold text-lg">
              🗄️
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Events Analyzed</p>
              <h3 className="text-lg font-extrabold text-white">12,842</h3>
              <p className="text-[10px] text-slate-400">Across 5,248 cases <MockDataBadge /></p>
            </div>
          </div>

          {/* Card 2 */}
          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-3 shadow-md">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 font-bold text-lg">
              🌐
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Patterns Discovered</p>
              <h3 className="text-lg font-extrabold text-white">1,248</h3>
              <p className="text-[10px] text-slate-400">Unique significant patterns</p>
            </div>
          </div>

          {/* Card 3 */}
          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-3 shadow-md">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 font-bold text-lg">
              🛡️
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">High Confidence Patterns</p>
              <h3 className="text-lg font-extrabold text-white">236</h3>
              <p className="text-[10px] text-slate-400">Confidence ≥ 75%</p>
            </div>
          </div>

          {/* Card 4 */}
          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-3 shadow-md">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 font-bold text-lg">
              ⭐
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Strongest Pattern</p>
              <h3 className="text-lg font-extrabold text-amber-400">87%</h3>
              <p className="text-[10px] text-slate-400 truncate max-w-[140px]">Jupiter + Venus + D9(7th)</p>
            </div>
          </div>

          {/* Card 5 */}
          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center gap-3 shadow-md">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 font-bold text-lg">
              📊
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Avg Confidence Score</p>
              <h3 className="text-lg font-extrabold text-white">68.4%</h3>
              <p className="text-[10px] text-slate-400">Across all patterns</p>
            </div>
          </div>
        </div>

        {/* ── Filter Bar ── */}
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-bold">Event Type:</span>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 font-bold focus:outline-none focus:border-cyan-500"
            >
              <option value="Marriage">Marriage</option>
              <option value="Career Promotion">Career Promotion</option>
              <option value="Business Success">Business Success</option>
              <option value="Property Purchase">Property Purchase</option>
              <option value="Education Success">Education Success</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-bold">Min Confidence:</span>
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="Any">Any</option>
              <option value="50%">50%+</option>
              <option value="75%">75%+</option>
              <option value="90%">90%+</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-bold">Min Support (Cases):</span>
            <select
              value={minSupport}
              onChange={(e) => setMinSupport(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="Any">Any</option>
              <option value="1000">1,000+</option>
              <option value="2500">2,500+</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-bold">Chart Type:</span>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="All Charts">All Charts</option>
              <option value="D1 Natal">D1 Natal</option>
              <option value="D9 Navamsha">D9 Navamsha</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-bold">Group By:</span>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="Auto">Auto</option>
              <option value="Planets">Planets</option>
              <option value="Houses">Houses</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => {
              setEventType("Marriage");
              setMinConfidence("Any");
              setMinSupport("Any");
              setChartType("All Charts");
              setGroupBy("Auto");
            }}
            className="ml-auto text-xs text-cyan-400 font-bold hover:underline cursor-pointer flex items-center gap-1"
          >
            ↻ Reset Filters
          </button>
        </div>

        {/* ── Main 3-Column Grid ── */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 items-start">
          {/* ── Left Column (lg:col-span-3 ~25%) ── */}
          <div className="lg:col-span-3 space-y-4">
            {/* Top Contributing Factors Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Top Contributing Factors
                </h3>
                <MockDataBadge />
              </div>

              {/* Sub-tabs */}
              <div className="flex items-center gap-2 pb-1.5 border-b border-slate-800 text-[11px] font-mono">
                {(["planets", "houses", "yogas", "dashas"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setFactorTab(tab)}
                    className={`capitalize transition cursor-pointer ${
                      factorTab === tab
                        ? "text-cyan-400 font-bold underline underline-offset-4"
                        : "text-slate-500 hover:text-slate-300"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Factors Progress Bars */}
              <div className="space-y-2 text-xs">
                {factorsData[factorTab].map((f) => (
                  <div key={f.name} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-slate-300 flex items-center gap-1.5">
                        <span className="text-slate-500">{f.symbol}</span> {f.name}
                      </span>
                      <span className="font-mono text-slate-400">{f.pct}% ({f.count})</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-950 overflow-hidden">
                      <div className={`h-full ${f.color}`} style={{ width: `${f.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-slate-800 text-[11px]">
                <Link href="/research/projects" className="text-cyan-400 font-bold hover:underline">
                  View All Factors →
                </Link>
              </div>
            </div>

            {/* Event Type Distribution Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                  Event Type Distribution
                  <span className="text-slate-500 cursor-help" title="Distribution across total events">ⓘ</span>
                </h3>
                <MockDataBadge />
              </div>

              {/* Donut Simulation */}
              <div className="flex flex-col items-center justify-center py-2">
                <div className="relative w-28 h-28 rounded-full border-8 border-cyan-500 border-t-amber-400 border-r-emerald-400 border-b-violet-500 flex items-center justify-center text-center">
                  <div>
                    <span className="block text-[10px] text-slate-400 font-mono uppercase">Total Events</span>
                    <span className="text-xs font-extrabold text-white">12,842</span>
                  </div>
                </div>
              </div>

              {/* Legend List */}
              <div className="space-y-1.5 text-[11px] font-mono">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" /> Marriage
                  </span>
                  <span className="text-slate-400">5,248 (40.9%)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Career Promotion
                  </span>
                  <span className="text-slate-400">3,105 (24.1%)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Business Success
                  </span>
                  <span className="text-slate-400">1,987 (15.5%)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded-full bg-violet-400" /> Property Purchase
                  </span>
                  <span className="text-slate-400">1,456 (11.3%)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-400" /> Education Success
                  </span>
                  <span className="text-slate-400">1,046 (8.1%)</span>
                </div>
              </div>
            </div>
          </div>

          {/* ── Middle Column: Top Patterns (Marriage) (lg:col-span-6 ~50%) ── */}
          <div className="lg:col-span-6 space-y-4">
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                  Top Patterns ({eventType})
                  <span className="text-slate-500 cursor-help" title="Top recurring patterns for selected event type">ⓘ</span>
                </h3>
                <MockDataBadge />
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-800 text-[10px] text-slate-500 uppercase tracking-wider">
                      <th className="pb-2">Rank</th>
                      <th className="pb-2">Pattern</th>
                      <th className="pb-2">Support (Cases)</th>
                      <th className="pb-2">Confidence</th>
                      <th className="pb-2">Lift Score</th>
                      <th className="pb-2">Trend</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {topPatterns.map((p) => (
                      <tr key={p.rank} className="hover:bg-slate-850/50 transition">
                        <td className="py-2.5 pr-2">
                          <span className="flex items-center justify-center w-5 h-5 rounded-full bg-slate-800 text-slate-300 font-bold text-[10px]">
                            {p.rank}
                          </span>
                        </td>
                        <td className="py-2.5 pr-2">
                          <p className="font-bold text-slate-200">{p.pattern}</p>
                          <span className="inline-block mt-0.5 px-1.5 py-0.2 rounded text-[9px] bg-slate-950 text-cyan-400 border border-slate-800">
                            {p.badge}
                          </span>
                        </td>
                        <td className="py-2.5 pr-2 text-slate-400">{p.support}</td>
                        <td className="py-2.5 pr-2">
                          <span className={`px-1.5 py-0.5 rounded font-bold ${p.confColor}`}>
                            {p.conf}
                          </span>
                          <span className="block text-[9px] text-slate-500 mt-0.5">{p.confLabel}</span>
                        </td>
                        <td className="py-2.5 pr-2">
                          <span className="font-bold text-slate-200">{p.lift}</span>
                          <span className="block text-[9px] text-slate-500">{p.liftLabel}</span>
                        </td>
                        <td className="py-2.5 text-emerald-400 font-bold text-sm">📈</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-mono text-[10px]">Showing 8 of 1,248 patterns</span>
                <Link href="/research/projects" className="text-cyan-400 font-bold hover:underline">
                  View All Patterns →
                </Link>
              </div>
            </div>
          </div>

          {/* ── Right Column (lg:col-span-3 ~25%) ── */}
          <div className="lg:col-span-3 space-y-4">
            {/* Confidence Score Distribution */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                  Confidence Score Distribution
                  <span className="text-slate-500 cursor-help" title="Distribution of confidence scores">ⓘ</span>
                </h3>
                <MockDataBadge />
              </div>

              {/* Histogram Bar Simulation */}
              <div className="h-28 flex items-end justify-between gap-2 pt-4 px-2 border-b border-slate-800 text-[10px] font-mono">
                <div className="flex flex-col items-center flex-1">
                  <span className="text-[9px] text-slate-400">45</span>
                  <div className="w-full bg-slate-700 h-3 rounded-t" />
                  <span className="text-[9px] text-slate-500 mt-1">0-20</span>
                </div>
                <div className="flex flex-col items-center flex-1">
                  <span className="text-[9px] text-slate-400">128</span>
                  <div className="w-full bg-amber-500/80 h-8 rounded-t" />
                  <span className="text-[9px] text-slate-500 mt-1">20-40</span>
                </div>
                <div className="flex flex-col items-center flex-1">
                  <span className="text-[9px] text-slate-400">312</span>
                  <div className="w-full bg-amber-400 h-16 rounded-t" />
                  <span className="text-[9px] text-slate-500 mt-1">40-60</span>
                </div>
                <div className="flex flex-col items-center flex-1">
                  <span className="text-[9px] text-slate-400">468</span>
                  <div className="w-full bg-emerald-500 h-22 rounded-t" />
                  <span className="text-[9px] text-slate-500 mt-1">60-80</span>
                </div>
                <div className="flex flex-col items-center flex-1">
                  <span className="text-[9px] text-slate-400">295</span>
                  <div className="w-full bg-emerald-400 h-14 rounded-t" />
                  <span className="text-[9px] text-slate-500 mt-1">80-100</span>
                </div>
              </div>
            </div>

            {/* Pattern Strength (Lift Score) Card */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                  Pattern Strength (Lift Score)
                  <span className="text-slate-500 cursor-help" title="Lift score distribution">ⓘ</span>
                </h3>
                <MockDataBadge />
              </div>

              <div className="flex items-center justify-between text-xs font-mono">
                <div className="relative w-20 h-20 rounded-full border-4 border-emerald-500 border-t-amber-400 border-r-cyan-400 border-b-rose-500 flex items-center justify-center text-center">
                  <div>
                    <span className="text-xs font-extrabold text-white">1,248</span>
                    <span className="block text-[8px] text-slate-400 uppercase">Total</span>
                  </div>
                </div>

                <div className="space-y-1 text-[10px]">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span className="text-slate-300">Very High (≥ 2.0)</span>
                    <span className="text-slate-400 font-bold">28% (349)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400" />
                    <span className="text-slate-300">High (1.5 - 2.0)</span>
                    <span className="text-slate-400 font-bold">32% (399)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    <span className="text-slate-300">Medium (1.0 - 1.5)</span>
                    <span className="text-slate-400 font-bold">25% (312)</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    <span className="text-slate-300">Low (&lt; 1.0)</span>
                    <span className="text-slate-400 font-bold">15% (188)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Significant Patterns */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Recent Significant Patterns
                </h3>
                <MockDataBadge />
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="p-2 rounded bg-slate-950 border border-slate-800/80 space-y-0.5">
                  <p className="font-bold text-slate-200 flex items-center gap-1">
                    <span>♄ ♃</span> Saturn + Jupiter + 10th House
                  </p>
                  <p className="text-[10px] text-slate-400 flex items-center justify-between">
                    <span>Discovered</span>
                    <span>15 May 2024</span>
                  </p>
                </div>

                <div className="p-2 rounded bg-slate-950 border border-slate-800/80 space-y-0.5">
                  <p className="font-bold text-slate-200 flex items-center gap-1">
                    <span>☿</span> Mercury Strong + Education
                  </p>
                  <p className="text-[10px] text-slate-400 flex items-center justify-between">
                    <span>Discovered</span>
                    <span>14 May 2024</span>
                  </p>
                </div>

                <div className="p-2 rounded bg-slate-950 border border-slate-800/80 space-y-0.5">
                  <p className="font-bold text-slate-200 flex items-center gap-1">
                    <span>♂ ☊</span> Mars + Rahu + Property Purchase
                  </p>
                  <p className="text-[10px] text-slate-400 flex items-center justify-between">
                    <span>Discovered</span>
                    <span>13 May 2024</span>
                  </p>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 text-[11px] text-right">
                <Link href="/research/projects" className="text-cyan-400 font-bold hover:underline">
                  View All Recent ↗
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* ── Bottom Row: Pattern Insights (4 Cards Grid) ── */}
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>Pattern Insights</span>
            <MockDataBadge />
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-pink-500/20 text-pink-400 font-bold text-sm shrink-0">
                ♀
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                <strong className="text-white">Jupiter &amp; Venus</strong> are the most influential for Marriage events. Present in 87% of high confidence patterns.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 font-bold text-sm shrink-0">
                🏠
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                <strong className="text-white">7th House activation in D9</strong> chart shows 3.42x higher lift for marriage events.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 font-bold text-sm shrink-0">
                ♀
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                <strong className="text-white">Shukra (Venus)</strong> related dashas show 2.1x higher success rate.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 font-bold text-sm shrink-0">
                📈
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Patterns with <strong className="text-white">Jupiter involvement</strong> have 68% higher confidence scores.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ResearchPatternsShell>
  );
}
