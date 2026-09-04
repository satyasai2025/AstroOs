"use client";

import React from "react";

export interface ExecutiveLifeStoryData {
  native_name: string;
  domain: string;
  headline: string;
  act_1_blueprint: string;
  act_2_current_phase: string;
  act_3_golden_roadmap: string;
  key_turning_points: Array<{
    timeframe: string;
    dasha: string;
    verdict: string;
  }>;
  dos: string[];
  donts: string[];
  empirical_validation_summary: string;
  medical_vulnerability?: {
    vitality_index: number;
    highest_risk_name: string;
    risk_level: string;
    evidence_badge: string;
    organ_system: string;
  };
  archetype_resonance?: {
    dominant_archetype: string;
    resonance_score: number;
    evidence_badge: string;
    guidance: string;
  };
}

interface PlainEnglishStoryViewProps {
  story: ExecutiveLifeStoryData;
  lang?: "hi" | "en";
}

export function PlainEnglishStoryView({ story }: PlainEnglishStoryViewProps) {
  return (
    <div className="space-y-6">
      {/* Hero Narrative Banner */}
      <div className="p-6 bg-gradient-to-br from-amber-50 via-white to-cyan-50 dark:from-amber-950/40 dark:via-slate-900 dark:to-cyan-950/40 border border-amber-200 dark:border-amber-500/30 rounded-3xl shadow-xl relative overflow-hidden text-slate-900 dark:text-white">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="px-3 py-1 bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40 rounded-full text-xs font-bold uppercase tracking-wider">
            📖 Plain English Life Story
          </span>
          <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded-full text-xs font-bold">
            ✨ 100% Deterministic & Grounded
          </span>
        </div>

        <h2 className="text-xl md:text-2xl font-black text-slate-900 dark:text-white leading-snug">
          {story.headline}
        </h2>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
          {story.empirical_validation_summary}
        </p>

        {/* Empirical Evidence Badges & Insights */}
        {(story.medical_vulnerability || story.archetype_resonance) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 pt-4 border-t border-amber-200 dark:border-amber-500/20">
            {story.medical_vulnerability && (
              <div className="p-3 bg-white/80 dark:bg-slate-950/80 border border-rose-200 dark:border-rose-500/30 rounded-xl space-y-1 shadow-sm">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-rose-700 dark:text-rose-300 flex items-center gap-1.5">
                    <span>🩺</span>
                    <span>Medical Vitality Index:</span>
                  </span>
                  <span className="font-mono text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-slate-900 px-2 py-0.5 rounded border border-emerald-200 dark:border-slate-800 font-bold">
                    {story.medical_vulnerability.vitality_index}/100
                  </span>
                </div>
                <div className="text-[11px] text-slate-700 dark:text-slate-300">
                  Target Organ: <strong className="text-slate-900 dark:text-white">{story.medical_vulnerability.organ_system}</strong> ({story.medical_vulnerability.risk_level} Risk)
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                  {story.medical_vulnerability.evidence_badge}
                </div>
              </div>
            )}

            {story.archetype_resonance && (
              <div className="p-3 bg-white/80 dark:bg-slate-950/80 border border-purple-200 dark:border-purple-500/30 rounded-xl space-y-1 shadow-sm">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-purple-700 dark:text-purple-300 flex items-center gap-1.5">
                    <span>🎭</span>
                    <span>Dominant Vocational Archetype:</span>
                  </span>
                  <span className="font-mono text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-slate-900 px-2 py-0.5 rounded border border-purple-200 dark:border-slate-800 font-bold">
                    {story.archetype_resonance.resonance_score}% Match
                  </span>
                </div>
                <div className="text-[11px] text-slate-900 dark:text-white font-semibold">
                  {story.archetype_resonance.dominant_archetype}
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                  {story.archetype_resonance.evidence_badge}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3-Act Life Story Journey */}
      <div className="grid grid-cols-1 gap-4">
        {/* Act 1 */}
        <div className="p-5 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-2xl space-y-2 hover:border-amber-300 dark:hover:border-slate-700 transition shadow-sm">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-400 flex items-center justify-center font-bold text-xs">
              1
            </span>
            <h3 className="text-sm font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider">
              Act I: The Core Blueprint & Life Architecture
            </h3>
          </div>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed pl-8 font-medium">
            {story.act_1_blueprint}
          </p>
        </div>

        {/* Act 2 */}
        <div className="p-5 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-2xl space-y-2 hover:border-cyan-300 dark:hover:border-slate-700 transition shadow-sm">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-cyan-100 dark:bg-cyan-500/20 text-cyan-800 dark:text-cyan-400 flex items-center justify-center font-bold text-xs">
              2
            </span>
            <h3 className="text-sm font-bold text-cyan-700 dark:text-cyan-300 uppercase tracking-wider">
              Act II: Where You Stand Right Now (Current Reality)
            </h3>
          </div>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed pl-8 font-medium">
            {story.act_2_current_phase}
          </p>
        </div>

        {/* Act 3 */}
        <div className="p-5 bg-gradient-to-r from-purple-50/50 to-white dark:from-purple-950/20 dark:to-slate-900 border border-purple-200 dark:border-purple-800/60 rounded-2xl space-y-2 hover:border-purple-400 dark:hover:border-purple-600 transition shadow-sm">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-500/20 text-purple-800 dark:text-purple-400 flex items-center justify-center font-bold text-xs">
              3
            </span>
            <h3 className="text-sm font-bold text-purple-700 dark:text-purple-300 uppercase tracking-wider">
              Act III: The Golden Milestone Horizon
            </h3>
          </div>
          <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed pl-8 font-medium">
            {story.act_3_golden_roadmap}
          </p>
        </div>
      </div>

      {/* Strategic Milestones & Do's / Don'ts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Key Turning Points */}
        <div className="lg:col-span-6 p-5 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl space-y-3 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <span>🧭</span>
            <span>Key Turning Point Windows</span>
          </h3>
          <div className="space-y-2">
            {story.key_turning_points.map((tp, idx) => (
              <div
                key={idx}
                className="p-3 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800/80 rounded-xl flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-bold text-amber-700 dark:text-amber-300">{tp.timeframe}</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">{tp.dasha}</div>
                </div>
                <div className="text-right">
                  <span className="px-2.5 py-1 bg-emerald-100 dark:bg-emerald-500/10 border border-emerald-300 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300 text-[10px] font-bold rounded-lg">
                    {tp.verdict}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Practical Action Playbook */}
        <div className="lg:col-span-6 p-5 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl space-y-4 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <span>📋</span>
            <span>Practical Action Playbook (Strategic Execution)</span>
          </h3>

          <div className="space-y-2">
            <div className="text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
              <span>🟢</span>
              <span>Recommended Strategic Actions (Do&apos;s):</span>
            </div>
            <ul className="space-y-1.5 pl-6 list-disc text-xs text-slate-700 dark:text-slate-300">
              {story.dos.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
            <div className="text-xs font-bold text-rose-700 dark:text-rose-400 flex items-center gap-1.5">
              <span>🔴</span>
              <span>Pitfalls to Avoid (Don&apos;ts):</span>
            </div>
            <ul className="space-y-1.5 pl-6 list-disc text-xs text-slate-700 dark:text-slate-300">
              {story.donts.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
