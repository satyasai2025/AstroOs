"use client";

import { useState } from "react";
import { HouseDependencyNetwork, type EdgeKind } from "@/components/charts/HouseDependencyNetwork";
import { Card } from "@/components/ui";
import type { WorkflowAnalysisResponse, HouseCuspSchema, PlanetPositionSchema, PlanetStrengthSchema } from "@/lib/types";

export default function HouseDependency2Page() {
  // In a real app, this would come from the workflow store or a selected chart
  const [selectedHouse, setSelectedHouse] = useState<number | null>(10); // Default to 10th house

  // Filter state shared with component
  const [activeKinds, setActiveKinds] = useState<Set<EdgeKind>>(new Set([
    "lordship", "aspect", "parivartana", "argala", "trinal", "angular", "dusthana", "functional", "maraka"
  ]));

  // Mock chart data for demonstration - in real app this comes from workflow store
  const mockHouses: HouseCuspSchema[] = Array.from({ length: 12 }, (_, i) => ({
    house_number: i + 1,
    longitude: i * 30,
    sidereal_longitude: i * 30,
    rashi: ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"][i] ?? "Aries",
    nakshatra_lord: "Ketu",
    sub_lord: "Venus",
    sub_sub_lord: "Sun",
  }));

  const mockPlanets: PlanetPositionSchema[] = [
    { planet: "Sun", house_number: 10, rashi: "Capricorn", rashi_degree: 18.4, sidereal_longitude: 288.4, dignity: "neutral", is_retrograde: false, is_combust: false, combustion_orb: null, nakshatra: "Shravana", pada: 1, nakshatra_lord: "Moon", sub_lord: "Mercury", sub_sub_lord: "Venus", rashi_house_number: 10 },
    { planet: "Moon", house_number: 4, rashi: "Cancer", rashi_degree: 12.3, sidereal_longitude: 102.3, dignity: "own", is_retrograde: false, is_combust: false, combustion_orb: null, nakshatra: "Pushya", pada: 2, nakshatra_lord: "Saturn", sub_lord: "Rahu", sub_sub_lord: "Jupiter", rashi_house_number: 4 },
    { planet: "Mars", house_number: 7, rashi: "Libra", rashi_degree: 5.7, sidereal_longitude: 185.7, dignity: "neutral", is_retrograde: false, is_combust: false, combustion_orb: null, nakshatra: "Chitra", pada: 3, nakshatra_lord: "Mars", sub_lord: "Sun", sub_sub_lord: "Moon", rashi_house_number: 7 },
    { planet: "Mercury", house_number: 10, rashi: "Capricorn", rashi_degree: 22.1, sidereal_longitude: 292.1, dignity: "neutral", is_retrograde: false, is_combust: false, combustion_orb: null, nakshatra: "Dhanishta", pada: 1, nakshatra_lord: "Mars", sub_lord: "Mercury", sub_sub_lord: "Saturn", rashi_house_number: 10 },
    { planet: "Jupiter", house_number: 9, rashi: "Sagittarius", rashi_degree: 15.6, sidereal_longitude: 255.6, dignity: "own", is_retrograde: false, is_combust: false, combustion_orb: null, nakshatra: "Purva Ashadha", pada: 2, nakshatra_lord: "Venus", sub_lord: "Sun", sub_sub_lord: "Rahu", rashi_house_number: 9 },
    { planet: "Venus", house_number: 9, rashi: "Sagittarius", rashi_degree: 8.2, sidereal_longitude: 248.2, dignity: "neutral", is_retrograde: false, is_combust: false, combustion_orb: null, nakshatra: "Mula", pada: 4, nakshatra_lord: "Ketu", sub_lord: "Jupiter", sub_sub_lord: "Saturn", rashi_house_number: 9 },
    { planet: "Saturn", house_number: 10, rashi: "Capricorn", rashi_degree: 3.9, sidereal_longitude: 273.9, dignity: "own", is_retrograde: false, is_combust: false, combustion_orb: null, nakshatra: "Uttara Ashadha", pada: 1, nakshatra_lord: "Sun", sub_lord: "Saturn", sub_sub_lord: "Venus", rashi_house_number: 10 },
    { planet: "Rahu", house_number: 2, rashi: "Taurus", rashi_degree: 11.5, sidereal_longitude: 41.5, dignity: "exalted", is_retrograde: true, is_combust: false, combustion_orb: null, nakshatra: "Rohini", pada: 2, nakshatra_lord: "Moon", sub_lord: "Mars", sub_sub_lord: "Rahu", rashi_house_number: 2 },
    { planet: "Ketu", house_number: 8, rashi: "Scorpio", rashi_degree: 11.5, sidereal_longitude: 221.5, dignity: "debilitated", is_retrograde: true, is_combust: false, combustion_orb: null, nakshatra: "Jyeshtha", pada: 4, nakshatra_lord: "Mercury", sub_lord: "Rahu", sub_sub_lord: "Jupiter", rashi_house_number: 8 },
  ];

  const mockPlanetStrengths: PlanetStrengthSchema[] = [
    { planet: "Sun", strength_score: 6.2, dignity: "neutral", is_retrograde: false, is_combust: false, house_number: 10, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false },
    { planet: "Moon", strength_score: 8.5, dignity: "own", is_retrograde: false, is_combust: false, house_number: 4, is_in_own_sign: true, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false },
    { planet: "Mars", strength_score: 5.8, dignity: "neutral", is_retrograde: false, is_combust: false, house_number: 7, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false },
    { planet: "Mercury", strength_score: 6.5, dignity: "neutral", is_retrograde: false, is_combust: false, house_number: 10, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false },
    { planet: "Jupiter", strength_score: 9.1, dignity: "own", is_retrograde: false, is_combust: false, house_number: 9, is_in_own_sign: true, is_exalted: false, is_debilitated: false, is_in_kendra: false, is_in_trikona: true, is_in_dusthana: false },
    { planet: "Venus", strength_score: 7.3, dignity: "neutral", is_retrograde: false, is_combust: false, house_number: 9, is_in_own_sign: false, is_exalted: false, is_debilitated: false, is_in_kendra: false, is_in_trikona: true, is_in_dusthana: false },
    { planet: "Saturn", strength_score: 8.8, dignity: "own", is_retrograde: false, is_combust: false, house_number: 10, is_in_own_sign: true, is_exalted: false, is_debilitated: false, is_in_kendra: true, is_in_trikona: false, is_in_dusthana: false },
    { planet: "Rahu", strength_score: 7.9, dignity: "exalted", is_retrograde: true, is_combust: false, house_number: 2, is_in_own_sign: false, is_exalted: true, is_debilitated: false, is_in_kendra: false, is_in_trikona: false, is_in_dusthana: false },
    { planet: "Ketu", strength_score: 4.2, dignity: "debilitated", is_retrograde: true, is_combust: false, house_number: 8, is_in_own_sign: false, is_exalted: false, is_debilitated: true, is_in_kendra: false, is_in_trikona: false, is_in_dusthana: true },
  ];

  return (
    <>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
              House Dependency Network
            </h1>
            <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
              Interactive visualization of inter-house relationships and dependencies
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <input
                type="text"
                placeholder="Search houses, significations..."
                className="obsidian-input pl-9 pr-4 py-2 text-sm"
                style={{ width: "280px" }}
              />
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--text-muted)"
                strokeWidth="2"
              >
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500 border border-gray-700 rounded px-1.5 py-0.5">
                Ctrl K
              </span>
            </div>
          </div>
        </div>

        {/* Filter chips */}
        <div className="flex flex-wrap items-center gap-2">
          {[
            { key: "all", label: "All Relationships" },
            { key: "lordship", label: "Lordship" },
            { key: "aspect", label: "Aspects" },
            { key: "parivartana", label: "Parivartana" },
            { key: "argala", label: "Argala" },
            { key: "trinal", label: "Trinal (1-5-9)" },
            { key: "angular", label: "Angular (1-4-7-10)" },
            { key: "dusthana", label: "Dusthana (6-8-12)" },
            { key: "maraka", label: "Maraka" },
          ].map((filter) => {
            const isAll = filter.key === "all";
            const isActive = isAll
              ? activeKinds.size === 9 // all 9 kinds
              : activeKinds.has(filter.key as EdgeKind);
            return (
              <button
                key={filter.key}
                type="button"
                onClick={() => {
                  if (isAll) {
                    setActiveKinds(isActive ? new Set() : new Set([
                      "lordship", "aspect", "parivartana", "argala", "trinal", "angular", "dusthana", "functional", "maraka"
                    ]));
                  } else {
                    setActiveKinds((prev) => {
                      const next = new Set(prev);
                      if (next.has(filter.key as EdgeKind)) next.delete(filter.key as EdgeKind);
                      else next.add(filter.key as EdgeKind);
                      return next;
                    });
                  }
                }}
                className="px-3 py-1.5 text-xs font-medium rounded-lg border transition-all"
                style={{
                  backgroundColor: isActive ? "rgba(6, 207, 255, 0.15)" : "transparent",
                  borderColor: isActive ? "var(--accent)" : "var(--border-primary)",
                  color: isActive ? "var(--accent)" : "var(--text-secondary)",
                }}
              >
                {filter.label}
              </button>
            );
          })}
          <button
            type="button"
            className="px-3 py-1.5 text-xs font-medium rounded-lg border flex items-center gap-1.5"
            style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
            </svg>
            Filters
          </button>
        </div>

        {/* Main content: Graph + Detail Panel */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_380px]">
          {/* Left: Network Graph */}
          <div className="space-y-4">
            <HouseDependencyNetwork
              houses={mockHouses}
              planetStrengths={mockPlanetStrengths}
              planets={mockPlanets}
              activeKinds={activeKinds}
              onFilterChange={setActiveKinds}
            />

            {/* Bottom: Dasha & Transit Timeline */}
            <Card padding="0" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <div className="p-4 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    Dasha & Transit Timeline Impact on 10th House
                  </h3>
                  <span className="text-xs text-gray-500">ⓘ</span>
                </div>
              </div>
              <div className="p-4">
                {/* Timeline chart placeholder */}
                <div className="space-y-3">
                  {/* Dasha periods */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="h-8 rounded-lg bg-gradient-to-r from-purple-900/40 to-purple-800/40 border border-purple-500/30 flex items-center px-3" style={{ width: "100%" }}>
                        <span className="text-xs font-mono text-purple-300">Mercury MD</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-8 rounded-lg bg-gradient-to-r from-amber-900/40 to-amber-800/40 border border-amber-500/30 flex items-center px-3" style={{ width: "100%" }}>
                        <span className="text-xs font-mono text-amber-300">Ketu MD</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-8 rounded-lg bg-gradient-to-r from-pink-900/40 to-pink-800/40 border border-pink-500/30 flex items-center px-3" style={{ width: "100%" }}>
                        <span className="text-xs font-mono text-pink-300">Venus MD</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-8 rounded-lg bg-gradient-to-r from-yellow-900/40 to-yellow-800/40 border border-yellow-500/30 flex items-center px-3" style={{ width: "100%" }}>
                        <span className="text-xs font-mono text-yellow-300">Sun MD</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-8 rounded-lg bg-gradient-to-r from-gray-800/40 to-gray-700/40 border border-gray-500/30 flex items-center px-3" style={{ width: "100%" }}>
                        <span className="text-xs font-mono text-gray-300">Moon MD</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-8 rounded-lg bg-gradient-to-r from-red-900/40 to-red-800/40 border border-red-500/30 flex items-center px-3" style={{ width: "100%" }}>
                        <span className="text-xs font-mono text-red-300">Mars MD</span>
                      </div>
                    </div>
                  </div>

                  {/* Year markers */}
                  <div className="flex justify-between text-xs text-gray-500 font-mono pt-2 border-t border-gray-800">
                    <span>2020</span>
                    <span>2022</span>
                    <span>2024</span>
                    <span>2026</span>
                    <span>2028</span>
                    <span>2030</span>
                    <span>2032</span>
                  </div>

                  {/* Transit impact line */}
                  <div className="relative pt-4">
                    <div className="flex items-center gap-4 mb-2">
                      <span className="text-xs text-gray-400">Transit Impact</span>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-green-400"></span>
                          Positive
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                          Neutral
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-red-400"></span>
                          Challenging
                        </span>
                      </div>
                    </div>
                    <div className="h-12 border border-gray-800 rounded-lg bg-gray-900/30 relative overflow-hidden">
                      {/* Impact waveform */}
                      <svg className="absolute inset-0 w-full h-full">
                        <path
                          d="M 0 30 Q 50 20, 100 30 T 200 30 T 300 20 T 400 30 T 500 25 T 600 30 T 700 20 T 800 30"
                          fill="none"
                          stroke="var(--accent)"
                          strokeWidth="2"
                          opacity="0.6"
                        />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right: House Detail Panel */}
          <div
            className="rounded-xl border border-gray-800 bg-[var(--bg-card)] p-5 overflow-y-auto"
            style={{ maxHeight: "calc(100vh - 200px)" }}
          >
            {selectedHouse && (
              <>
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-1 text-xs font-bold rounded-md bg-cyan-900/40 text-cyan-300 border border-cyan-600/40">
                        {selectedHouse}th House
                      </span>
                    </div>
                    <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                      Karma Bhava
                    </h2>
                    <p className="text-xs text-gray-400 font-mono mt-1">
                      Career, Status, Authority
                    </p>
                  </div>
                  <button className="text-gray-400 hover:text-white transition">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 6L6 18M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Basic Details */}
                <div className="space-y-3 mb-4 pb-4 border-b border-gray-800">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Lord</span>
                    <span className="font-mono" style={{ color: "var(--text-primary)" }}>Venus ♀</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Occupants</span>
                    <span className="font-mono" style={{ color: "var(--text-primary)" }}>Sun, Mercury ☿</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Sign on Cusp</span>
                    <span className="font-mono" style={{ color: "var(--text-primary)" }}>Capricorn ♑ 18° 24'</span>
                  </div>
                  <div className="flex justify-between text-xs items-center">
                    <span className="text-gray-400">Strength</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                        <div className="h-full bg-cyan-400" style={{ width: "82%" }} />
                      </div>
                      <span className="font-mono text-cyan-400">82%</span>
                    </div>
                  </div>
                </div>

                {/* Significations */}
                <div className="mb-4 pb-4 border-b border-gray-800">
                  <h3 className="text-xs font-bold uppercase tracking-wide mb-3" style={{ color: "var(--accent)" }}>
                    Significations
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {["Career", "Profession", "Authority", "Status", "Reputation", "Father", "Government", "Karma"].map((sig) => (
                      <span
                        key={sig}
                        className="px-2 py-1 text-xs rounded-md border border-gray-700 bg-gray-800/50 text-gray-300"
                      >
                        {sig}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Dependencies */}
                <div className="mb-4 pb-4 border-b border-gray-800">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                      Dependencies (8)
                    </h3>
                  </div>
                  <div className="space-y-2">
                    {[
                      { house: "4th House", type: "Angular Link", direction: "→" },
                      { house: "7th House", type: "Angular Link", direction: "→" },
                      { house: "9th House", type: "Trinal Link", direction: "→" },
                      { house: "5th House", type: "Trinal Link", direction: "→" },
                      { house: "2nd House", type: "Maraka Influence", direction: "→" },
                      { house: "6th House", type: "Dusthana Influence", direction: "→" },
                      { house: "8th House", type: "Dusthana Influence", direction: "→" },
                      { house: "3rd House", type: "Upachaya Support", direction: "→" },
                    ].map((dep, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="text-gray-300">{dep.house}</span>
                        <span className="text-gray-500">{dep.type}</span>
                        <span className="text-cyan-400">{dep.direction}</span>
                      </div>
                    ))}
                  </div>
                  <button className="text-xs text-cyan-400 hover:underline mt-2">
                    View All Relationships →
                  </button>
                </div>

                {/* AI Insights */}
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wide mb-3" style={{ color: "var(--accent)" }}>
                    AI Insights
                  </h3>
                  <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/20 p-4">
                    <p className="text-xs text-gray-300 leading-relaxed mb-3">
                      The 10th house is strongly supported by trinal (5th, 9th) and angular (1st, 4th, 7th) houses,
                      indicating potential for career growth and recognition. Lord Venus placed in 9th house creates a Dharma-Karma connection.
                    </p>
                    <button className="flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg border border-cyan-500/30 bg-cyan-900/20 text-cyan-300 hover:bg-cyan-900/30 transition">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
                      </svg>
                      Explain with AI
                    </button>
                  </div>
                </div>

                {/* Current Transit */}
                <div className="mt-4 pt-4 border-t border-gray-800">
                  <h3 className="text-xs font-bold uppercase tracking-wide mb-3 text-gray-400">
                    Current Transit (May 2025)
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Saturn in 10th</span>
                      <span className="text-green-400">Neutral</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Jupiter in 2nd</span>
                      <span className="text-green-400">Supportive</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Rahu in 2nd</span>
                      <span className="text-red-400">Challenging</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Ketu in 8th</span>
                      <span className="text-purple-400">Transformative</span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}