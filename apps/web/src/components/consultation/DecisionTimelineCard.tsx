"use client";

import React, { useState, useMemo } from "react";

export interface DecisionTimelineWindow {
  window_start: string;
  window_end: string;
  mahadasha: string;
  antardasha: string;
  probability: number;
  decision_tier: "PRATYAKSHA_PHALA" | "SUSHUPTA_BEEJA" | "ALPA_PHALA" | "SAMANYA_KAL";
  confidence_level: string;
  verdict: string;
  polarity: string;
  polarity_logic: string;
  varga_fusion_score: number;
  is_bhavottama_active: boolean;
  scd_annual_house: number;
  scd_composite_score: number;
  sav_10th_bindus: number;
  double_transit: boolean;
  amatyakaraka?: string;
  confluence_level?: "TRIPLE_CONFLUENCE" | "DUAL_CONFLUENCE" | "SINGLE_ALIGNMENT";
  chara_dasha_rashi?: string;
  confluence_synthesis_hi?: string;
  confluence_synthesis_en?: string;
  empirical_match?: {
    is_matched: boolean;
    evidence_badge: string;
    sample_size: number;
    lift_ratio: number;
    confidence_percentage: number;
    pattern_description: string;
  };
  explanation_hi?: string;
  explanation_en?: string;
}

interface DecisionTimelineCardProps {
  timeline: DecisionTimelineWindow[];
  scanHorizon: string;
  lang?: "hi" | "en";
}

const TIER_META = {
  PRATYAKSHA_PHALA: {
    labelEn: "Pratyaksha Phala (Direct Manifestation)",
    labelHi: "प्रत्यक्ष फल (सर्वोच्च सिद्धि एवं युगांतरकारी घटना)",
    badgeClass: "bg-emerald-500 text-slate-950 font-black shadow-md",
    cardBorder: "border-emerald-300 dark:border-emerald-500/50 bg-gradient-to-r from-emerald-50/80 via-white to-white dark:from-emerald-950/25 dark:via-slate-950 dark:to-slate-950",
    icon: "🌟",
    descEn: "High Dasha potential aligned with decisive Transit (Gochara) support & Double Transit.",
    descHi: "उच्च दशा सामर्थ्य + अनुकूल गोचर + द्वि-गोचर (Double Transit) का पूर्ण संयोग।",
  },
  SUSHUPTA_BEEJA: {
    labelEn: "Sushupta Beeja (Latent Potential)",
    labelHi: "सुषुप्त बीज (सुप्त सामर्थ्य — गोचर की प्रतीक्षा)",
    badgeClass: "bg-blue-100 dark:bg-blue-500/20 text-blue-800 dark:text-blue-300 border border-blue-300 dark:border-blue-500/40 font-bold",
    cardBorder: "border-blue-300 dark:border-blue-500/40 bg-gradient-to-r from-blue-50/80 via-white to-white dark:from-blue-950/20 dark:via-slate-950 dark:to-slate-950",
    icon: "🌱",
    descEn: "Strong internal dasha promises, but awaiting a triggering transit window.",
    descHi: "दशा में पूर्ण बीज सामर्थ्य है, परंतु गोचर का तात्कालिक ट्रिगर अभी सुप्त है।",
  },
  ALPA_PHALA: {
    labelEn: "Alpa Phala (Transient Minor Trigger)",
    labelHi: "अल्प फल (अल्पकालिक गोचर हलचल)",
    badgeClass: "bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40 font-bold",
    cardBorder: "border-amber-300 dark:border-amber-500/30 bg-gradient-to-r from-amber-50/80 via-white to-white dark:from-amber-950/15 dark:via-slate-950 dark:to-slate-950",
    icon: "⚡",
    descEn: "Strong transit stimulation without corresponding Mahadasha seed authorization.",
    descHi: "गोचर सक्रिय है, परंतु मुख्य दशा का बीज अधिकार न होने से प्रभाव अल्पकालिक रहेगा।",
  },
  SAMANYA_KAL: {
    labelEn: "Samanya Kal (Routine / Neutral)",
    labelHi: "सामान्य काल (संतुलित एवं सामान्य कालखंड)",
    badgeClass: "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-400 font-medium",
    cardBorder: "border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-950/50",
    icon: "⏳",
    descEn: "Baseline steady period with no major structural disruptions.",
    descHi: "सामान्य दिनचर्या एवं नियमित कर्म का स्थिर समय।",
  },
};

const PLANET_SYMBOLS: Record<string, string> = {
  SUN: "☉",
  MOON: "☽",
  MARS: "♂",
  MERCURY: "☿",
  JUPITER: "♃",
  VENUS: "♀",
  SATURN: "♄",
  RAHU: "☊",
  KETU: "☋",
};

export function DecisionTimelineCard({ timeline, scanHorizon, lang = "hi" }: DecisionTimelineCardProps) {
  const [selectedTier, setSelectedTier] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<"date" | "prob" | "sav">("date");
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Filter and Sort windows
  const filteredWindows = useMemo(() => {
    let list = [...timeline];

    if (selectedTier !== "ALL") {
      list = list.filter((w) => w.decision_tier === selectedTier);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(
        (w) =>
          w.mahadasha.toLowerCase().includes(q) ||
          w.antardasha.toLowerCase().includes(q) ||
          w.verdict.toLowerCase().includes(q)
      );
    }

    if (sortBy === "prob") {
      list.sort((a, b) => b.probability - a.probability);
    } else if (sortBy === "sav") {
      list.sort((a, b) => b.sav_10th_bindus - a.sav_10th_bindus);
    }

    return list;
  }, [timeline, selectedTier, searchQuery, sortBy]);

  const toggleExpand = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl space-y-6 text-slate-900 dark:text-slate-100">
      {/* Header & Meta */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">⚖️</span>
            <h3 className="text-base md:text-lg font-bold text-slate-900 dark:bg-gradient-to-r dark:from-emerald-200 dark:via-teal-300 dark:to-cyan-300 dark:bg-clip-text dark:text-transparent">
              {lang === "hi"
                ? `4-स्तरीय निर्णय संप्रभु टाइमलाइन (Scan Horizon: ${scanHorizon})`
                : `4-Tier Supervisory Decision Timeline (${scanHorizon})`}
            </h3>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
            {lang === "hi"
              ? "प्रत्यक्ष फल (Landmark Manifestation) ↔ सुषुप्त बीज (Latent Seed) ↔ अल्प फल ↔ सामान्य काल"
              : "Autonomous Governor filtering Dasha-Gochara-SAV-DoubleTransit synthesis into 4 decisive tiers."}
          </p>
        </div>

        {/* Tier Count Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto text-xs pb-1 sm:pb-0">
          <button
            onClick={() => setSelectedTier("ALL")}
            className={`px-3 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              selectedTier === "ALL"
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-950 shadow"
                : "bg-slate-100 dark:bg-slate-950 text-slate-700 dark:text-slate-400 border border-slate-200 dark:border-slate-800 hover:bg-slate-200"
            }`}
          >
            All ({timeline.length})
          </button>
          <button
            onClick={() => setSelectedTier("PRATYAKSHA_PHALA")}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              selectedTier === "PRATYAKSHA_PHALA"
                ? "bg-emerald-500 text-slate-950 shadow"
                : "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/40 hover:bg-emerald-100"
            }`}
          >
            🌟 Pratyaksha ({timeline.filter((w) => w.decision_tier === "PRATYAKSHA_PHALA").length})
          </button>
          <button
            onClick={() => setSelectedTier("SUSHUPTA_BEEJA")}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              selectedTier === "SUSHUPTA_BEEJA"
                ? "bg-blue-500 text-slate-950 shadow"
                : "bg-blue-50 dark:bg-blue-950/30 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800/40 hover:bg-blue-100"
            }`}
          >
            🌱 Sushupta ({timeline.filter((w) => w.decision_tier === "SUSHUPTA_BEEJA").length})
          </button>
          <button
            onClick={() => setSelectedTier("ALPA_PHALA")}
            className={`px-2.5 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
              selectedTier === "ALPA_PHALA"
                ? "bg-amber-500 text-slate-950 shadow"
                : "bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/40 hover:bg-amber-100"
            }`}
          >
            ⚡ Alpa ({timeline.filter((w) => w.decision_tier === "ALPA_PHALA").length})
          </button>
        </div>
      </div>

      {/* Search & Sort Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-200 dark:border-slate-800 text-xs">
        <div className="w-full sm:w-72 relative">
          <input
            type="text"
            placeholder="Search lord, planet or verdict..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-amber-500"
          />
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <span className="text-slate-600 dark:text-slate-500 font-semibold">Sort:</span>
          <select
            value={sortBy}
            onChange={(e: any) => setSortBy(e.target.value)}
            className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-800 dark:text-slate-300 focus:outline-none focus:border-amber-500 font-medium"
          >
            <option value="date">Chronological (Date)</option>
            <option value="prob">Calibrated Probability</option>
            <option value="sav">10th House SAV Bindus</option>
          </select>
        </div>
      </div>

      {/* Decision Windows List */}
      <div className="space-y-3.5">
        {filteredWindows.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-xs">
            No decision windows matching the selected filter criteria.
          </div>
        ) : (
          filteredWindows.map((win, idx) => {
            const meta = TIER_META[win.decision_tier] || TIER_META.SAMANYA_KAL;
            const isExpanded = expandedIndex === idx;
            const probPercent = Math.round(win.probability * 100);

            const mdGlyph = PLANET_SYMBOLS[win.mahadasha.toUpperCase()] || "✦";
            const adGlyph = PLANET_SYMBOLS[win.antardasha.toUpperCase()] || "✦";

            return (
              <div
                key={idx}
                className={`border rounded-xl p-4 transition-all duration-200 shadow-sm ${meta.cardBorder}`}
              >
                {/* Header row: Tier Badge + Dasha Lords + Date + SAV */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2.5 border-b border-slate-200 dark:border-slate-800/80">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs px-2.5 py-0.5 rounded-full ${meta.badgeClass}`}>
                      {meta.icon} {meta.labelEn}
                    </span>

                    <div className="flex items-center gap-1.5 font-mono text-sm font-bold text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-950/80 px-2.5 py-0.5 rounded-lg border border-slate-200 dark:border-slate-800">
                      <span className="text-amber-700 dark:text-amber-400">{mdGlyph} {win.mahadasha}</span>
                      <span className="text-slate-400">→</span>
                      <span className="text-cyan-700 dark:text-cyan-400">{adGlyph} {win.antardasha}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400 font-medium">
                    <span className="font-mono bg-white dark:bg-slate-950 px-2 py-1 rounded border border-slate-200 dark:border-slate-800 text-[11px]">
                      📅 {win.window_start.slice(0, 10)} to {win.window_end.slice(0, 10)}
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white font-mono bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded border border-slate-200 dark:border-slate-700">
                      {probPercent}% Prob
                    </span>
                  </div>
                </div>

                {/* Metrics 4-Col Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 my-3 text-xs">
                  {/* Double Transit */}
                  <div className="bg-slate-50 dark:bg-slate-950/70 p-2 rounded-lg border border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] text-slate-500">Double Transit:</span>
                    <span
                      className={`font-bold text-[11px] ${
                        win.double_transit ? "text-emerald-700 dark:text-emerald-400" : "text-slate-400"
                      }`}
                    >
                      {win.double_transit ? "✅ Active (Jup+Sat)" : "❌ Inactive"}
                    </span>
                  </div>

                  {/* 10th SAV Bindus */}
                  <div className="bg-slate-50 dark:bg-slate-950/70 p-2 rounded-lg border border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] text-slate-500">10H SAV Bindus:</span>
                    <span
                      className={`font-bold text-[11px] ${
                        win.sav_10th_bindus >= 28 ? "text-cyan-700 dark:text-cyan-400" : "text-amber-700 dark:text-amber-400"
                      }`}
                    >
                      {win.sav_10th_bindus} / 56
                    </span>
                  </div>

                  {/* Polarity Status */}
                  <div className="bg-slate-50 dark:bg-slate-950/70 p-2 rounded-lg border border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] text-slate-500">Gochara Polarity:</span>
                    <span
                      className={`font-bold text-[10px] px-1.5 py-0.5 rounded ${
                        win.polarity === "CONDUCIVE"
                          ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800"
                          : win.polarity === "OBSTRUCTIVE"
                          ? "bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
                          : "bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400"
                      }`}
                    >
                      {win.polarity}
                    </span>
                  </div>

                  {/* Bhāvottama / SCD House */}
                  <div className="bg-slate-50 dark:bg-slate-950/70 p-2 rounded-lg border border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
                    <span className="text-[10px] text-slate-500">SCD Annual:</span>
                    <span className="font-bold text-[11px] text-purple-700 dark:text-purple-300">
                      House {win.scd_annual_house}
                      {win.is_bhavottama_active && " ⭐"}
                    </span>
                  </div>
                </div>

                {/* Triple Confluence Banner */}
                {win.confluence_level === "TRIPLE_CONFLUENCE" && (
                  <div className="bg-gradient-to-r from-amber-100/70 via-purple-100/70 to-emerald-100/70 dark:from-amber-500/20 dark:via-purple-500/20 dark:to-emerald-500/20 border border-amber-300 dark:border-amber-500/50 rounded-xl p-2.5 my-2.5 flex items-center justify-between text-xs shadow-inner">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🌟</span>
                      <div>
                        <div className="font-bold text-amber-900 dark:text-amber-300 flex items-center gap-1.5">
                          <span>Infallible Triple-Dasha Confluence</span>
                          {win.chara_dasha_rashi && (
                            <span className="text-[10px] text-purple-900 dark:text-purple-300 font-mono bg-purple-100 dark:bg-purple-950/80 px-1.5 py-0.5 rounded border border-purple-300 dark:border-purple-800/60">
                              Jaimini: {win.chara_dasha_rashi}
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-800 dark:text-slate-200 mt-0.5 font-medium">
                          {win.confluence_synthesis_en || win.confluence_synthesis_hi}
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] uppercase font-black px-2 py-0.5 bg-amber-400 text-slate-950 rounded-md shadow-sm shrink-0">
                      100% Infallible
                    </span>
                  </div>
                )}

                {/* Empirical Evidence Banner */}
                {win.empirical_match?.is_matched && (
                  <div className="bg-cyan-50 dark:bg-cyan-950/30 border border-cyan-200 dark:border-cyan-500/40 rounded-xl p-2.5 my-2 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-base">🔬</span>
                      <div>
                        <div className="font-bold text-cyan-900 dark:text-cyan-300 flex items-center gap-1.5">
                          <span>Empirically Proven Signature</span>
                          <span className="text-[10px] text-cyan-700 dark:text-cyan-400 font-mono">
                            (Validated across {win.empirical_match.sample_size.toLocaleString()} historical cases)
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-700 dark:text-slate-300 mt-0.5">
                          {win.empirical_match.pattern_description}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
                      <span className="text-[10px] font-mono px-2 py-0.5 bg-white dark:bg-slate-950 text-cyan-800 dark:text-cyan-300 rounded border border-cyan-200 dark:border-cyan-800 font-bold">
                        Lift: {win.empirical_match.lift_ratio}x
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 rounded border border-emerald-300 dark:border-emerald-500/40">
                        {win.empirical_match.confidence_percentage}% Confidence
                      </span>
                    </div>
                  </div>
                )}

                {/* Verdict Commentary */}
                <div className="bg-slate-50 dark:bg-slate-950/90 p-3 rounded-xl border border-slate-200 dark:border-slate-800/80 mt-2 shadow-sm">
                  <div className="text-[10px] text-amber-700 dark:text-amber-400 font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <span>📜</span>
                    <span>Shastric Actionable Verdict</span>
                  </div>
                  <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                    {win.explanation_en || win.explanation_hi || win.verdict}
                  </p>
                </div>

                {/* Expand / Collapse Rationale Button */}
                <div className="mt-3 flex items-center justify-between pt-1">
                  <button
                    onClick={() => toggleExpand(idx)}
                    className="text-[11px] text-slate-600 dark:text-slate-400 hover:text-amber-600 dark:hover:text-amber-300 font-semibold flex items-center gap-1 transition"
                  >
                    <span>{isExpanded ? "▲ Collapse Details" : "▼ View Shastric Attributions & Vectors"}</span>
                  </button>

                  {win.is_bhavottama_active && (
                    <span className="text-[10px] font-bold text-amber-800 dark:text-amber-300 bg-amber-100 dark:bg-amber-500/10 px-2 py-0.5 rounded border border-amber-300 dark:border-amber-500/30">
                      ⭐ Bhāvottama Active
                    </span>
                  )}
                </div>

                {/* Expanded Deep-Dive Details */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">Polarity Reasoning</div>
                      <div className="text-slate-700 dark:text-slate-300 text-[11px]">{win.polarity_logic}</div>
                    </div>

                    <div className="p-2.5 bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
                      <div className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">Multidimensional Alignment</div>
                      <div className="text-slate-700 dark:text-slate-300 text-[11px] flex items-center justify-between">
                        <span>Varga Fusion Score:</span>
                        <span className="font-bold text-slate-900 dark:text-white">{win.varga_fusion_score.toFixed(2)}</span>
                      </div>
                      <div className="text-slate-700 dark:text-slate-300 text-[11px] flex items-center justify-between">
                        <span>SCD Tri-Harmony:</span>
                        <span className="font-bold text-slate-900 dark:text-white">{win.scd_composite_score.toFixed(2)}</span>
                      </div>
                      {win.amatyakaraka && (
                        <div className="text-slate-700 dark:text-slate-300 text-[11px] flex items-center justify-between">
                          <span>Amatyakaraka (AmK):</span>
                          <span className="font-bold text-amber-700 dark:text-amber-300">{win.amatyakaraka}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
