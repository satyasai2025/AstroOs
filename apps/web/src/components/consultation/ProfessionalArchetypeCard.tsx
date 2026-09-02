"use client";

import React, { useState } from "react";

export interface MatchedSignatureItem {
  signature_name: string;
  weight: number;
  proof: string;
  category?: string;
}

export interface ArchetypeAffinityItem {
  archetype_key: string;
  title: string;
  domain: string;
  affinity_score: number; // 0.0 to 100.0%
  empirical_lift: number;
  confidence_score: number;
  p_value_text: string;
  evidence_badge: string;
  matched_signatures: MatchedSignatureItem[];
  key_planetary_drivers: string[];
  rajya_dhana_yogas_active: string[];
  strategic_career_guidance: string;
}

export interface ProfessionalArchetypesData {
  dominant_archetype_key: string;
  dominant_title: string;
  dominant_score: number;
  dominant_badge: string;
  dominant_guidance: string;
  total_yogas_verified?: number;
  rajya_yogas_count?: number;
  dhana_yogas_count?: number;
  archetype_affinities: ArchetypeAffinityItem[];
}

interface ProfessionalArchetypeCardProps {
  data: ProfessionalArchetypesData;
  lang?: "en" | "hi";
}

const ARCHETYPE_ICONS: Record<string, string> = {
  POLITICIAN_LEADER: "👑",
  ACTOR_CINEMA: "🎬",
  SPORTS_ATHLETICS: "🏏",
  BUSINESS_WEALTH: "💼",
  SPIRITUAL_SAINT: "🧘",
};

const ARCHETYPE_COLORS: Record<
  string,
  { bg: string; border: string; text: string; bar: string; glow: string }
> = {
  POLITICIAN_LEADER: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    border: "border-amber-300 dark:border-amber-500/50",
    text: "text-amber-800 dark:text-amber-300",
    bar: "from-amber-500 to-yellow-400",
    glow: "shadow-amber-500/10",
  },
  ACTOR_CINEMA: {
    bg: "bg-pink-50 dark:bg-pink-950/30",
    border: "border-pink-300 dark:border-pink-500/50",
    text: "text-pink-800 dark:text-pink-300",
    bar: "from-pink-500 to-rose-400",
    glow: "shadow-pink-500/10",
  },
  SPORTS_ATHLETICS: {
    bg: "bg-red-50 dark:bg-red-950/30",
    border: "border-red-300 dark:border-red-500/50",
    text: "text-red-800 dark:text-red-300",
    bar: "from-red-500 to-orange-400",
    glow: "shadow-red-500/10",
  },
  BUSINESS_WEALTH: {
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    border: "border-emerald-300 dark:border-emerald-500/50",
    text: "text-emerald-800 dark:text-emerald-300",
    bar: "from-emerald-500 to-teal-400",
    glow: "shadow-emerald-500/10",
  },
  SPIRITUAL_SAINT: {
    bg: "bg-purple-50 dark:bg-purple-950/30",
    border: "border-purple-300 dark:border-purple-500/50",
    text: "text-purple-800 dark:text-purple-300",
    bar: "from-purple-500 to-indigo-400",
    glow: "shadow-purple-500/10",
  },
};

export function ProfessionalArchetypeCard({
  data,
  lang = "en",
}: ProfessionalArchetypeCardProps) {
  const [selectedKey, setSelectedKey] = useState<string>(
    data.dominant_archetype_key || data.archetype_affinities[0]?.archetype_key || "POLITICIAN_LEADER"
  );

  const activeArchetype =
    data.archetype_affinities.find((a) => a.archetype_key === selectedKey) ||
    data.archetype_affinities[0];

  const dominantColors =
    ARCHETYPE_COLORS[data.dominant_archetype_key] || ARCHETYPE_COLORS.POLITICIAN_LEADER;

  return (
    <div className="space-y-6 text-slate-900 dark:text-slate-100">
      {/* Dominant Archetype Hero Banner */}
      <div
        className={`p-6 rounded-3xl border ${dominantColors.border} ${dominantColors.bg} shadow-xl relative overflow-hidden backdrop-blur-sm`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 bg-amber-100 dark:bg-amber-500/20 text-amber-900 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                <span>⭐</span>
                <span>
                  {lang === "hi"
                    ? "सर्वोच्च आजीविका एवं अधिकार प्रारूप (Dominant Archetype)"
                    : "Dominant Career Archetype"}
                </span>
              </span>
              <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-900 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded-full text-xs font-bold">
                {data.dominant_badge}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-3xl">
                {ARCHETYPE_ICONS[data.dominant_archetype_key] || "🎯"}
              </span>
              <h2 className="text-xl md:text-2xl font-black text-slate-900 dark:text-white">
                {data.dominant_title}
              </h2>
            </div>

            <p className="text-xs text-slate-700 dark:text-slate-300 max-w-3xl leading-relaxed font-medium">
              {data.dominant_guidance}
            </p>
          </div>

          <div className="flex items-center gap-4 self-start md:self-auto bg-white/90 dark:bg-slate-950/80 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="text-right">
              <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-wider">
                {lang === "hi" ? "आत्मीयता स्कोर" : "Affinity Score"}
              </div>
              <div className={`text-3xl font-black ${dominantColors.text}`}>
                {data.dominant_score.toFixed(1)}%
              </div>
            </div>
            <div className="h-10 w-[1px] bg-slate-200 dark:bg-slate-800" />
            <div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-wider">
                {lang === "hi" ? "सत्यापित योग" : "Verified Yogas"}
              </div>
              <div className="text-base font-bold text-slate-800 dark:text-slate-200">
                <span className="text-amber-700 dark:text-amber-400">{data.rajya_yogas_count || 0} Rajya</span> +{" "}
                <span className="text-emerald-700 dark:text-emerald-400">{data.dhana_yogas_count || 0} Dhana</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5 Archetypes Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {data.archetype_affinities.map((arch) => {
          const isSelected = arch.archetype_key === selectedKey;
          const colors = ARCHETYPE_COLORS[arch.archetype_key] || ARCHETYPE_COLORS.POLITICIAN_LEADER;
          const icon = ARCHETYPE_ICONS[arch.archetype_key] || "🎯";

          return (
            <button
              key={arch.archetype_key}
              onClick={() => setSelectedKey(arch.archetype_key)}
              className={`p-4 rounded-2xl text-left border transition-all transform hover:-translate-y-0.5 shadow-sm ${
                isSelected
                  ? `${colors.bg} ${colors.border} shadow-lg ${colors.glow}`
                  : "bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700 text-slate-600 dark:text-slate-400"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg">{icon}</span>
                <span className={`text-xs font-black ${colors.text}`}>
                  {arch.affinity_score.toFixed(1)}%
                </span>
              </div>

              <div className="text-xs font-bold text-slate-900 dark:text-slate-200 line-clamp-1 mb-1">
                {arch.title.split("(")[0].trim()}
              </div>

              <div className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-semibold">
                {arch.empirical_lift.toFixed(2)}x Lift (p &lt; 0.0001)
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-200 dark:bg-slate-950 h-1.5 rounded-full overflow-hidden mt-3">
                <div
                  style={{ width: `${arch.affinity_score}%` }}
                  className={`bg-gradient-to-r ${colors.bar} h-full rounded-full`}
                />
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Archetype Detailed Shastric Dossier */}
      {activeArchetype && (
        <div className="p-6 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-3xl space-y-6 shadow-xl text-slate-900 dark:text-slate-100">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl">
                  {ARCHETYPE_ICONS[activeArchetype.archetype_key] || "✨"}
                </span>
                <h3 className="text-lg font-black text-slate-900 dark:text-white">
                  {activeArchetype.title}
                </h3>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                🌐 <strong className="text-slate-800 dark:text-slate-300">Domain:</strong> {activeArchetype.domain}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-cyan-800 dark:text-cyan-300 rounded-xl text-xs font-mono font-bold">
                Affinity: {activeArchetype.affinity_score.toFixed(1)}%
              </span>
              <span className="px-3 py-1 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-emerald-800 dark:text-emerald-400 rounded-xl text-xs font-mono font-bold">
                Statistical Lift: {activeArchetype.empirical_lift.toFixed(2)}x
              </span>
            </div>
          </div>

          {/* Active Rajya & Dhana Yogas Verified */}
          {activeArchetype.rajya_dhana_yogas_active.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                <span>⚜️</span>
                <span>
                  {lang === "hi"
                    ? "सत्यापित राजयोग एवं धनयोग संयोजन (Verified Shastric Yogas)"
                    : "Verified Classical Rajya & Dhana Yogas"}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {activeArchetype.rajya_dhana_yogas_active.map((y, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-500/40 text-amber-900 dark:text-amber-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                  >
                    <span>✨</span>
                    <span>{y}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Key Planetary Drivers */}
          {activeArchetype.key_planetary_drivers.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <span>🪐</span>
                <span>
                  {lang === "hi"
                    ? "प्रमुख ग्रह चालक एवं स्थिति (Primary Graha Drivers)"
                    : "Primary Planetary Drivers & Karakatva"}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {activeArchetype.key_planetary_drivers.map((drv, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-lg text-xs font-bold"
                  >
                    {drv}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Matched Shastric Signatures List */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center justify-between">
              <span>📊 Matched Planetary Signatures &amp; Shastric Proofs</span>
              <span className="text-[11px] font-normal text-slate-500 dark:text-slate-400 font-mono">
                {activeArchetype.matched_signatures.length} Signatures Fired
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {activeArchetype.matched_signatures.map((sig, sIdx) => (
                <div
                  key={sIdx}
                  className="p-3.5 bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/80 rounded-2xl space-y-1.5 flex flex-col justify-between shadow-sm"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
                      <span>▪</span>
                      <span>{sig.signature_name}</span>
                    </span>
                    <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded text-[10px] font-mono font-bold">
                      +{sig.weight} pts
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
                    {sig.proof}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Strategic Career Guidance Banner */}
          <div className="p-4 bg-gradient-to-r from-cyan-50/70 to-white dark:from-slate-950 dark:to-slate-900 border border-cyan-200 dark:border-slate-800 rounded-2xl space-y-1.5">
            <div className="text-xs font-bold text-cyan-800 dark:text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>🎯</span>
              <span>
                {lang === "hi"
                  ? "सामरिक कार्यक्षेत्र एवं परामर्श (Strategic Vocational Guidance)"
                  : "Strategic Vocational Guidance"}
              </span>
            </div>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
              {activeArchetype.strategic_career_guidance}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
