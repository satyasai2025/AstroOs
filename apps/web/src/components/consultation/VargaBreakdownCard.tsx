"use client";

import React, { useState } from "react";

export interface VargaFusionData {
  overall_varga_harmony: number;
  fused_domain_scores: Record<string, number>;
  bhavottama_planets: string[];
  vargottama_planets: string[];
}

interface VargaBreakdownCardProps {
  data: VargaFusionData;
  lang?: "hi" | "en";
}

const DOMAIN_LABELS: Record<string, { en: string; hi: string; icon: string }> = {
  career: { en: "Career & Authority (D10 / Rajya)", hi: "आजीविका एवं राजसत्ता (D10)", icon: "💼" },
  wealth: { en: "Wealth & Dhana (D2 / D4)", hi: "धन एवं स्थायी संपत्ति", icon: "💰" },
  health: { en: "Vitality & Longevity (Deha)", hi: "स्वास्थ्य एवं जीवन शक्ति", icon: "🛡️" },
  marriage: { en: "Relationships & Sustenance (D9)", hi: "वैवाहिक सुख एवं धर्म (D9)", icon: "🤝" },
  spirituality: { en: "Spiritual Fruits & Moksha (D20/D60)", hi: "आध्यात्मिक सिद्धि एवं मोक्ष", icon: "🕉️" },
};

export function VargaBreakdownCard({ data, lang = "hi" }: VargaBreakdownCardProps) {
  const harmonyPercent = Math.round((data.overall_varga_harmony || 0) * 100);

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl space-y-6 text-slate-900 dark:text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">✨</span>
            <h3 className="text-base md:text-lg font-bold text-slate-900 dark:bg-gradient-to-r dark:from-purple-200 dark:via-pink-300 dark:to-amber-300 dark:bg-clip-text dark:text-transparent">
              {lang === "hi"
                ? "वर्ग समन्वय एवं भावोत्तम सुपर-एम्प्लीफिकेशन (Varga Fusion Engine)"
                : "Multidimensional Varga Fusion & Bhāvottama Engine"}
            </h3>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
            {lang === "hi"
              ? "D1 (स्थूल) + D9 (धर्म) + D10 (कर्म) + D60 (संस्कार) का हस्ताक्षरित योग (Signed Addition)"
              : "D1 + D9 + D10 + D60 Signed Vector Addition with Bhāvottama (1.5x–2.0x) Multipliers"}
          </p>
        </div>

        {/* Overall Harmony Pill */}
        <div className="bg-purple-50 dark:bg-slate-950 px-4 py-2 rounded-xl border border-purple-200 dark:border-purple-900/40 flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] text-purple-700 dark:text-slate-400 font-semibold uppercase">Overall Harmony</div>
            <div className="text-base font-black text-purple-900 dark:text-purple-300">{harmonyPercent}%</div>
          </div>
          <div className="w-9 h-9 rounded-full bg-purple-100 dark:bg-purple-950 border border-purple-300 dark:border-purple-500/50 flex items-center justify-center font-bold text-xs text-purple-900 dark:text-purple-300">
            {data.overall_varga_harmony.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Highlights: Bhāvottama & Vargottama Badges */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Bhāvottama Super-Amplification Card */}
        <div className="bg-gradient-to-br from-amber-50/80 to-white dark:from-amber-950/25 dark:to-slate-950 border border-amber-200 dark:border-amber-500/30 rounded-xl p-4 space-y-2 relative overflow-hidden shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-base">⚡</span>
              <h4 className="text-xs font-bold text-amber-800 dark:text-amber-400 uppercase tracking-wider">
                {lang === "hi" ? "भावोत्तम ग्रह (1.5x - 2.0x Amplification)" : "Bhāvottama Planets (1.5x - 2.0x)"}
              </h4>
            </div>
            <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40">
              D1 ↔ D9 Same Bhava
            </span>
          </div>

          <p className="text-[11px] text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
            {lang === "hi"
              ? "जब कोई ग्रह D1 (राशि) और D9 (नवांश) में एक ही भाव में स्थित होता है, तो उसका फलादेश 1.5x से 2.0x बढ़ जाता है।"
              : "When a planet occupies the exact same house in D1 and D9, its tangible manifestation power super-amplifies."}
          </p>

          <div className="flex flex-wrap gap-2 pt-2">
            {data.bhavottama_planets && data.bhavottama_planets.length > 0 ? (
              data.bhavottama_planets.map((planet) => (
                <span
                  key={planet}
                  className="px-3 py-1 bg-amber-100 dark:bg-amber-500/20 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-500/50 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm"
                >
                  <span>⭐</span>
                  <span>{planet}</span>
                  <span className="text-[10px] text-amber-700 dark:text-amber-400/80">(Bhāvottama)</span>
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-400 italic">No Bhāvottama planets detected</span>
            )}
          </div>
        </div>

        {/* Vargottama Planets Card */}
        <div className="bg-gradient-to-br from-purple-50/80 to-white dark:from-purple-950/25 dark:to-slate-950 border border-purple-200 dark:border-purple-500/30 rounded-xl p-4 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-base">👑</span>
              <h4 className="text-xs font-bold text-purple-800 dark:text-purple-400 uppercase tracking-wider">
                {lang === "hi" ? "वर्गोत्तम ग्रह (Vargottama Rashi)" : "Vargottama Planets"}
              </h4>
            </div>
            <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-500/20 text-purple-800 dark:text-purple-300 border border-purple-300 dark:border-purple-500/40">
              D1 ↔ D9 Same Rashi
            </span>
          </div>

          <p className="text-[11px] text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
            {lang === "hi"
              ? "नवांश में समान राशि प्राप्त होने से ग्रह की आंतरिक शक्ति और स्थिरता अत्यंत सुदृढ़ हो जाती है।"
              : "Attaining the identical sign in D1 and D9 stabilizes inherent strength and natural benevolence."}
          </p>

          <div className="flex flex-wrap gap-2 pt-2">
            {data.vargottama_planets && data.vargottama_planets.length > 0 ? (
              data.vargottama_planets.map((planet) => (
                <span
                  key={planet}
                  className="px-3 py-1 bg-purple-100 dark:bg-purple-500/20 text-purple-900 dark:text-purple-200 border border-purple-300 dark:border-purple-500/50 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm"
                >
                  <span>💎</span>
                  <span>{planet}</span>
                  <span className="text-[10px] text-purple-700 dark:text-purple-400/80">(Vargottama)</span>
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-400 italic">No Vargottama planets detected</span>
            )}
          </div>
        </div>
      </div>

      {/* Fused Domain Scores Grid */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <span>📊</span>
          <span>{lang === "hi" ? "वर्ग-समन्वित क्षेत्र फलादेश (Fused Domain Scores)" : "Fused Dimensional Domain Scores"}</span>
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(data.fused_domain_scores || {}).map(([dom, score]) => {
            const domInfo = DOMAIN_LABELS[dom] || {
              en: dom.toUpperCase(),
              hi: dom.toUpperCase(),
              icon: "📌",
            };
            const scoreNum = typeof score === "number" ? score : 0;
            const scoreClamped = Math.max(-1.0, Math.min(1.0, scoreNum));
            const positivePercent = Math.round(((scoreClamped + 1) / 2) * 100);

            const isStrong = scoreNum > 0.3;
            const isChallenging = scoreNum < -0.2;

            return (
              <div
                key={dom}
                className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 space-y-2.5 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>{domInfo.icon}</span>
                    <span className="text-xs font-bold text-slate-900 dark:text-white">
                      {lang === "hi" ? domInfo.hi : domInfo.en}
                    </span>
                  </div>
                  <span
                    className={`text-xs font-extrabold ${
                      isStrong
                        ? "text-emerald-700 dark:text-emerald-400"
                        : isChallenging
                        ? "text-rose-700 dark:text-rose-400"
                        : "text-amber-700 dark:text-amber-400"
                    }`}
                  >
                    {scoreNum > 0 ? `+${scoreNum.toFixed(2)}` : scoreNum.toFixed(2)}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-slate-200 dark:bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-300 dark:border-slate-800">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isStrong
                        ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                        : isChallenging
                        ? "bg-gradient-to-r from-rose-500 to-orange-500"
                        : "bg-gradient-to-r from-amber-500 to-yellow-400"
                    }`}
                    style={{ width: `${positivePercent}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span>-1.0 (Debilitated)</span>
                  <span>+1.0 (Exalted)</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
