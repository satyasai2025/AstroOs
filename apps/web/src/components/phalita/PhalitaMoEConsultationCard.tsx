'use client';

import React from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import { PhalitaMoEConsultationResponse } from "@/lib/phalitaApi";
import { CognitiveScoreGauge } from "./CognitiveScoreGauge";
import { Cpu, Activity, ShieldCheck, Sparkles, AlertTriangle, CheckCircle2 } from "./Icons";

interface PhalitaMoEConsultationCardProps {
  verdict: PhalitaMoEConsultationResponse;
  loading?: boolean;
}

export const PhalitaMoEConsultationCard: React.FC<PhalitaMoEConsultationCardProps> = ({
  verdict,
  loading = false,
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  if (loading) {
    return (
      <div className={`p-6 rounded-2xl border animate-pulse ${
        isDark ? "bg-[#0a101d] border-[#17263c]" : "bg-white border-slate-200"
      }`}>
        <div className="h-6 w-48 bg-slate-700/30 rounded mb-4"></div>
        <div className="h-32 bg-slate-700/20 rounded"></div>
      </div>
    );
  }

  const {
    domain,
    final_cognitive_score,
    is_probable,
    gating_weights,
    expert_breakdown,
    conflict_resolution,
    consensus_summary,
    actionable_recommendation,
  } = verdict;

  const expertIcons: Record<string, React.ReactNode> = {
    NatalStructuralExpert: <Cpu className="w-4 h-4 text-cyan-400" />,
    DivisionalYogaExpert: <Sparkles className="w-4 h-4 text-purple-400" />,
    TemporalDashaExpert: <Activity className="w-4 h-4 text-amber-400" />,
    UpagrahaShadowExpert: <ShieldCheck className="w-4 h-4 text-rose-400" />,
  };

  return (
    <div className={`p-6 rounded-2xl border space-y-6 ${
      isDark ? "bg-[#0a101d] border-[#17263c]" : "bg-white border-slate-200 shadow-sm"
    }`}>
      {/* Header */}
      <div className={`flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4 ${
        isDark ? "border-slate-800" : "border-slate-200"
      }`}>
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-500" />
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Phalita Mixture of Experts (MoE) Consultation
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            4-Expert Shastric Gating + Evidence Fusion + Parashari Conflict Arbitration
          </p>
        </div>

        <span className="self-start md:self-auto text-xs px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border border-indigo-500/20 font-bold">
          Domain: {domain.toUpperCase()}
        </span>
      </div>

      {/* Main Score & Attention Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
        {/* Score Gauge */}
        <div className="md:col-span-1">
          <CognitiveScoreGauge
            score={final_cognitive_score}
            isProbable={is_probable}
            domain={domain}
          />
        </div>

        {/* Softmax Attention Gating Weights */}
        <div className={`md:col-span-2 p-4 rounded-xl border ${
          isDark ? "bg-[#0c1421] border-[#1e2e42]" : "bg-slate-50 border-slate-200"
        }`}>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500" />
            Softmax Gating Attention Distribution (MoE Router)
          </h3>
          <div className="space-y-3">
            {Object.entries(gating_weights).map(([expName, weight]) => {
              const pct = (weight * 100).toFixed(1);
              return (
                <div key={expName} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-800 dark:text-slate-300 flex items-center gap-1.5 font-sans">
                      {expertIcons[expName] || <Cpu className="w-3 h-3" />}
                      {expName.replace("Expert", "")}
                    </span>
                    <span className="text-slate-500 dark:text-slate-400 font-mono">{pct}% weight</span>
                  </div>
                  <div className={`w-full h-2 rounded-full overflow-hidden ${
                    isDark ? "bg-slate-800" : "bg-slate-200"
                  }`}>
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 4 Expert Findings Breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(expert_breakdown).map(([name, exp]) => (
          <div
            key={name}
            className={`p-3.5 rounded-xl border flex flex-col justify-between ${
              isDark ? "bg-[#0d1624] border-[#1b2b3f]" : "bg-slate-50 border-slate-200"
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-200 flex items-center gap-1.5">
                  {expertIcons[name]}
                  {exp.expert_name.replace("Expert", "")}
                </span>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">
                  {exp.expert_score.toFixed(1)}/9
                </span>
              </div>
              <ul className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1 mt-2">
                {exp.key_findings.slice(0, 2).map((kf, i) => (
                  <li key={i} className="line-clamp-2">• {kf}</li>
                ))}
              </ul>
            </div>
            <div className={`mt-3 pt-2 border-t text-[10px] flex justify-between ${
              isDark ? "border-slate-800 text-slate-500" : "border-slate-200 text-slate-500"
            }`}>
              <span>Confidence</span>
              <span className="font-semibold text-slate-800 dark:text-slate-300">{(exp.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>

      {/* Conflict Resolution Banner */}
      {conflict_resolution.has_conflict && (
        <div className={`p-4 rounded-xl border flex items-start gap-3 ${
          isDark ? "border-amber-500/30 bg-amber-950/20" : "border-amber-300 bg-amber-50"
        }`}>
          <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-bold text-amber-800 dark:text-amber-300">
              Parashari Conflict Resolution Applied: {conflict_resolution.precedence_rule_applied}
            </p>
            <p className="text-slate-700 dark:text-slate-400 leading-relaxed">
              {conflict_resolution.resolution_narrative}
            </p>
          </div>
        </div>
      )}

      {/* Narrative & Actionable Recommendation */}
      <div className={`p-4 rounded-xl border space-y-3 ${
        isDark ? "bg-[#0b1320] border-[#18273a]" : "bg-indigo-50/60 border-indigo-200"
      }`}>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          <h3 className="text-xs font-bold text-slate-900 dark:text-slate-200 uppercase tracking-wider">
            Consensus Synthesis &amp; Strategic Guidance
          </h3>
        </div>
        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
          {consensus_summary}
        </p>
        <div className={`pt-2 border-t ${isDark ? "border-slate-800" : "border-indigo-200/60"}`}>
          <p className="text-xs font-semibold text-indigo-700 dark:text-indigo-400">
            Actionable Guidance: <span className="font-normal text-slate-800 dark:text-slate-300">{actionable_recommendation}</span>
          </p>
        </div>
      </div>
    </div>
  );
};
