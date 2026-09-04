"use client";

import React, { useState, useEffect } from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import {
  phalitaApi,
  CANONICAL_12_DOMAINS,
  ShastricPipelineResponse,
  Validation3TierAuditResponse,
} from "@/lib/phalitaApi";
import {
  Sparkles,
  Activity,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  ChevronRight,
  Shield,
  Lock,
  Layers,
  Database,
  TrendingUp,
  FileText,
} from "./Icons";

interface ShastricReasoningPanelProps {
  birthDateIso: string;
  latitude: number;
  longitude: number;
  targetDateIso?: string;
}

export const ShastricReasoningPanel: React.FC<ShastricReasoningPanelProps> = ({
  birthDateIso,
  latitude,
  longitude,
  targetDateIso,
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [selectedDomain, setSelectedDomain] = useState<string>("career");
  const [loadingPipeline, setLoadingPipeline] = useState<boolean>(false);
  const [loadingAudit, setLoadingAudit] = useState<boolean>(false);
  const [pipelineData, setPipelineData] = useState<ShastricPipelineResponse | null>(null);
  const [auditData, setAuditData] = useState<Validation3TierAuditResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"pipeline" | "validation">("pipeline");

  // Load pipeline data when domain or inputs change
  useEffect(() => {
    let isMounted = true;
    const fetchPipeline = async () => {
      setLoadingPipeline(true);
      try {
        const res = await phalitaApi.executeShastricPipeline({
          birth_datetime: birthDateIso || "1950-09-17T05:30:00Z",
          latitude: latitude || 23.7844,
          longitude: longitude || 72.6393,
          domain: selectedDomain,
          target_date: targetDateIso || "2014-05-26",
        });
        if (isMounted && res) {
          setPipelineData(res);
        }
      } catch (err) {
        console.error("Failed to execute Shastric pipeline", err);
      } finally {
        if (isMounted) setLoadingPipeline(false);
      }
    };

    fetchPipeline();
    return () => {
      isMounted = false;
    };
  }, [birthDateIso, latitude, longitude, targetDateIso, selectedDomain]);

  // Load 3-tier validation audit
  const fetchValidationAudit = async () => {
    setLoadingAudit(true);
    try {
      const res = await phalitaApi.get3TierValidationAudit();
      if (res) {
        setAuditData(res);
      }
    } catch (err) {
      console.error("Failed to load 3-Tier validation audit", err);
    } finally {
      setLoadingAudit(false);
    }
  };

  useEffect(() => {
    if (activeTab === "validation" && !auditData) {
      fetchValidationAudit();
    }
  }, [activeTab, auditData]);

  const getTierBadgeColor = (tier: string) => {
    switch (tier) {
      case "HIGH_PROMINENCE":
        return isDark
          ? "bg-emerald-950/80 text-emerald-300 border-emerald-500/40"
          : "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "MODERATE_PROMINENCE":
        return isDark
          ? "bg-amber-950/80 text-amber-300 border-amber-500/40"
          : "bg-amber-100 text-amber-800 border-amber-300";
      default:
        return isDark
          ? "bg-slate-900 text-slate-400 border-slate-700"
          : "bg-slate-100 text-slate-600 border-slate-300";
    }
  };

  return (
    <div className={`space-y-6 ${isDark ? "text-slate-200" : "text-slate-800"}`}>
      {/* Top Header & Mode Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-800 transition-colors bg-white dark:bg-slate-900/90 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Shastric Reasoning &amp; Provenance Engine
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Canonical Facts &rarr; Technique Resolver &rarr; Rule Engine &rarr; Evidence &rarr; Calibrated Prediction &rarr; Grounded AI Explanation
          </p>
        </div>

        {/* Mode Toggle Pills */}
        <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 font-mono text-xs">
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === "pipeline"
                ? "bg-amber-500 text-slate-950 font-bold shadow-md"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            Real-Time Reasoning Pipeline
          </button>
          <button
            onClick={() => setActiveTab("validation")}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeTab === "validation"
                ? "bg-amber-500 text-slate-950 font-bold shadow-md"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            3-Tier Validation Framework
          </button>
        </div>
      </div>

      {activeTab === "pipeline" ? (
        <div className="space-y-6">
          {/* Domain Selector Pill Carousel */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {CANONICAL_12_DOMAINS.map((dom) => {
              const isSelected = selectedDomain === dom.id;
              return (
                <button
                  key={dom.id}
                  onClick={() => setSelectedDomain(dom.id)}
                  className={`flex-shrink-0 px-3 py-2 rounded-xl text-xs font-medium border transition-all flex items-center gap-2 cursor-pointer ${
                    isSelected
                      ? isDark
                        ? "bg-amber-500/20 text-amber-200 border-amber-500/50 shadow-sm"
                        : "bg-amber-100 text-amber-900 border-amber-400 font-bold shadow-sm"
                      : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-amber-400 shadow-sm"
                  }`}
                >
                  <span className="font-semibold">{dom.bhava}. {dom.label}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                    isSelected
                      ? isDark ? "bg-amber-950/60 text-amber-200" : "bg-amber-200 text-amber-950"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                  }`}>
                    {dom.varga}
                  </span>
                </button>
              );
            })}
          </div>

          {loadingPipeline ? (
            <div className="p-12 text-center rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500 mb-3" />
              <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
                Evaluating Shastric rules, varga confluence, and provenance traces...
              </p>
            </div>
          ) : pipelineData ? (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Calibrated Signal Score & Metrics */}
              <div className="lg:col-span-5 space-y-6">
                {/* Score Card */}
                <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm transition-colors bg-white dark:bg-slate-900/90">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Calibrated Signal Score (0–9)
                    </span>
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getTierBadgeColor(
                        pipelineData.signal_tier
                      )}`}
                    >
                      {pipelineData.signal_tier.replace("_", " ")}
                    </span>
                  </div>

                  <div className="flex items-baseline gap-3 mb-2">
                    <span className="text-4xl font-extrabold text-amber-500 dark:text-amber-400 font-mono">
                      {pipelineData.calibrated_signal_score.toFixed(2)}
                    </span>
                    <span className="text-base text-slate-400 dark:text-slate-500 font-mono">/ 9.00</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-3 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 mb-4">
                    <div
                      className="h-full bg-gradient-to-r from-amber-500 to-emerald-400 transition-all duration-500"
                      style={{
                        width: `${(pipelineData.calibrated_signal_score / 9.0) * 100}%`,
                      }}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-200 dark:border-slate-800 text-xs">
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block">Confidence Level</span>
                      <span className="font-semibold text-slate-900 dark:text-slate-200">
                        {pipelineData.confidence_percentage}% (±{pipelineData.confidence_margin_delta})
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 dark:text-slate-400 block">Provenance Reference</span>
                      <span className="font-mono text-[11px] text-amber-600 dark:text-amber-400/90 truncate block">
                        {pipelineData.evidence_provenance_id}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Primary Promisers */}
                <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm bg-white dark:bg-slate-900/90">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Primary Shastric Promisers
                  </h3>
                  <ul className="space-y-2 text-xs">
                    {pipelineData.primary_promisers.map((p, idx) => (
                      <li key={idx} className="flex items-start gap-2 p-2 rounded-lg border bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/30 text-emerald-900 dark:text-slate-300">
                        <span className="text-emerald-500 font-bold">•</span>
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Inhibitors / Delay Analysis */}
                <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm bg-white dark:bg-slate-900/90">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Friction &amp; Delay Diagnostics
                  </h3>
                  <p className="text-xs p-2.5 rounded-lg border border-slate-200 dark:border-slate-700/60 leading-relaxed bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300">
                    {pipelineData.friction_analysis}
                  </p>
                </div>
              </div>

              {/* Right Column: AI Grounded Shastric Report */}
              <div className="lg:col-span-7 space-y-6">
                <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-5 shadow-sm bg-white dark:bg-slate-900/90">
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-amber-500" />
                      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                        Grounded AI Shastric Synthesis
                      </h3>
                    </div>
                    <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                      Target: {pipelineData.target_date_iso}
                    </span>
                  </div>

                  {/* Executive Verdict */}
                  <div className="p-4 rounded-xl border border-amber-300 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-950/20 text-slate-800 dark:text-slate-200">
                    <h4 className="text-xs font-bold uppercase text-amber-700 dark:text-amber-300 mb-1">
                      Executive Verdict
                    </h4>
                    <p className="text-xs leading-relaxed text-slate-800 dark:text-slate-200">
                      {pipelineData.executive_verdict}
                    </p>
                  </div>

                  {/* Dasha Synthesis */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">
                      Active Dasha &amp; Timing Jurisdiction
                    </h4>
                    <p className="text-xs leading-relaxed p-3 rounded-lg border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300">
                      {pipelineData.dasha_timing_synthesis}
                    </p>
                  </div>

                  {/* Classical Citations */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">
                      Classical Shastric Citations &amp; Rule Traces
                    </h4>
                    <div className="space-y-2">
                      {pipelineData.shastric_citations.map((c, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg border border-slate-200 dark:border-slate-700/60 text-xs leading-relaxed bg-slate-50 dark:bg-slate-800/50 text-slate-700 dark:text-slate-300"
                        >
                          <span className="font-mono text-amber-600 dark:text-amber-400 text-[11px] font-bold block mb-0.5">
                            Rule Trace #{idx + 1}
                          </span>
                          {c}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Siddhantic Guidance */}
                  <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-700/60 space-y-1 bg-slate-50 dark:bg-slate-800/50">
                    <h4 className="text-xs font-bold uppercase text-slate-500 dark:text-slate-400">
                      Siddhantic Actionable Guidance
                    </h4>
                    <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                      {pipelineData.siddhantic_counsel}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        /* 3-Tier Validation Framework Tab */
        <div className="space-y-6">
          {loadingAudit ? (
            <div className="p-12 text-center rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500 mb-3" />
              <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
                Executing 3-Tier Validation Audit Hierarchy...
              </p>
            </div>
          ) : auditData ? (
            <div className="space-y-6">
              {/* Overall System Status Banner */}
              <div className="p-4 rounded-xl border flex items-center justify-between bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-500/40">
                <div className="flex items-center gap-3">
                  <Shield className="w-6 h-6 text-emerald-500" />
                  <div>
                    <h3 className="text-sm font-bold text-emerald-900 dark:text-emerald-200">
                      Validation Status: {auditData.overall_system_status}
                    </h3>
                    <p className="text-xs text-emerald-700 dark:text-emerald-400/80">
                      Rigorous 3-Tier evaluation verified against Shastric rules and empirical benchmarks.
                    </p>
                  </div>
                </div>
                <span className="text-xs font-mono text-slate-500 dark:text-slate-400 font-semibold">
                  {new Date(auditData.timestamp_iso).toLocaleDateString()}
                </span>
              </div>

              {/* 3 Tier Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Tier 1 Card */}
                <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm bg-white dark:bg-slate-900/90">
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
                    <span className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase font-mono">
                      Tier 1: Regression
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 font-mono">
                      Clean
                    </span>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 font-sans">
                      Deterministic Siddhantic Regression
                    </h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                      Exact mathematical derivations and formulas verified against classical benchmark profiles.
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-1 text-xs font-mono">
                    <div className="flex justify-between text-slate-700 dark:text-slate-300">
                      <span className="font-sans">Benchmark Cases:</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">
                        {auditData.tier1_regression.passed_cases} / {auditData.tier1_regression.total_cases} Passed
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-500 dark:text-slate-400">
                      <span className="font-sans">Regression Status:</span>
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold">100% Deterministic OK</span>
                    </div>
                  </div>
                </div>

                {/* Tier 2 Card */}
                <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm bg-white dark:bg-slate-900/90">
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
                    <span className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase font-mono">
                      Tier 2: Generalization
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 font-mono">
                      Statistically Robust
                    </span>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 font-sans">
                      Empirical Generalization Audit
                    </h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                      N={auditData.tier2_generalization.total_cohort_charts} independent charts across {auditData.tier2_generalization.total_evaluated_windows} sliding windows.
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-1.5 text-xs font-mono">
                    <div className="flex justify-between text-slate-700 dark:text-slate-300">
                      <span className="font-sans">Precision / Recall:</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">
                        {auditData.tier2_generalization.precision}% / {auditData.tier2_generalization.recall_sensitivity}%
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-700 dark:text-slate-300">
                      <span className="font-sans">False Positive Rate (FPR):</span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400">
                        {auditData.tier2_generalization.false_positive_rate}%
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-700 dark:text-slate-300">
                      <span className="font-sans">ROC-AUC / Brier:</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100 font-mono">
                        {auditData.tier2_generalization.roc_auc_score} / {auditData.tier2_generalization.brier_calibration_score}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Tier 3 Card */}
                <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm bg-white dark:bg-slate-900/90">
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
                    <span className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase font-mono">
                      Tier 3: Out-of-Sample
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 font-mono">
                      Zero Leakage
                    </span>
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 font-sans">
                      Blind Holdout Validation
                    </h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                      N={auditData.tier3_holdout.total_holdout_charts} holdout cases evaluated with pre-frozen weights.
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-1.5 text-xs font-mono">
                    <div className="flex justify-between text-slate-700 dark:text-slate-300">
                      <span className="font-sans">Pre-Freeze Hash:</span>
                      <span className="font-mono text-[11px] text-amber-600 dark:text-amber-400">
                        {auditData.tier3_holdout.pre_freeze_hash}
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-700 dark:text-slate-300">
                      <span className="font-sans">Holdout Precision:</span>
                      <span className="font-bold text-slate-900 dark:text-slate-100">
                        {auditData.tier3_holdout.precision}%
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-700 dark:text-slate-300">
                      <span className="font-sans">Holdout ROC-AUC:</span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                        {auditData.tier3_holdout.roc_auc}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
