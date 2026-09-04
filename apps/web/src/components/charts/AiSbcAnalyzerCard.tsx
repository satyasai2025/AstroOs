"use client";

import React, { useState } from "react";
import {
  SBCReport,
  AISBCEventType,
  AISBCAnalysisResponse,
} from "@/lib/sbc";
import { api } from "@/lib/api";

interface AiSbcAnalyzerCardProps {
  report: SBCReport | null;
  referenceNakshatra: string;
  transitDate?: string | null;
}

const EVENT_TABS: { id: AISBCEventType; label: string; icon: string; desc: string }[] = [
  {
    id: "market",
    label: "Market & Financial",
    icon: "📈",
    desc: "Capital safety, volatility & liquidity shields",
  },
  {
    id: "life_events",
    label: "Major Life Events",
    icon: "⚡",
    desc: "Career moves, health, relationships & moves",
  },
  {
    id: "muhurta",
    label: "Auspicious Timings",
    icon: "🔮",
    desc: "Launch timing & obstacle-free windows",
  },
  {
    id: "general",
    label: "Full Synthesis",
    icon: "✨",
    desc: "Complete 10 Sangyas plain-language summary",
  },
];

export function AiSbcAnalyzerCard({
  report,
  referenceNakshatra,
  transitDate,
}: AiSbcAnalyzerCardProps) {
  const [selectedEventType, setSelectedEventType] = useState<AISBCEventType>("market");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<AISBCAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"structured" | "markdown">("structured");
  const [copied, setCopied] = useState<boolean>(false);

  const handleGenerate = async (eventTypeToRun?: AISBCEventType) => {
    const targetType = eventTypeToRun || selectedEventType;
    if (eventTypeToRun) setSelectedEventType(eventTypeToRun);

    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        reference_nakshatra: referenceNakshatra || report?.janma_nakshatra || "mrigashira",
        transit_date: transitDate || report?.moment_utc || new Date().toISOString(),
        event_type: targetType,
        malefic_vedhas: report?.malefic_vedhas || [],
        benefic_vedhas: report?.benefic_vedhas || [],
        active_sangyas: report?.sensitive_points || [],
      };

      const res = await api.post<AISBCAnalysisResponse>("/api/v1/ai/sbc-analysis", payload);
      setAnalysisResult(res);
    } catch (err: any) {
      console.error("AI SBC Analysis failed:", err);
      // Fallback endpoint
      try {
        const payload = {
          reference_nakshatra: referenceNakshatra || report?.janma_nakshatra || "mrigashira",
          transit_date: transitDate || report?.moment_utc || new Date().toISOString(),
          event_type: targetType,
          malefic_vedhas: report?.malefic_vedhas || [],
          benefic_vedhas: report?.benefic_vedhas || [],
          active_sangyas: report?.sensitive_points || [],
        };
        const fallbackRes = await api.post<AISBCAnalysisResponse>("/api/v1/sbc/ai-analysis", payload);
        setAnalysisResult(fallbackRes);
      } catch (fallbackErr: any) {
        setError(fallbackErr?.message || err?.message || "Failed to generate AI insights. Please verify backend connection.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (!analysisResult?.markdown_report) return;
    navigator.clipboard.writeText(analysisResult.markdown_report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderVerdictBadge = (badge: string) => {
    switch (badge) {
      case "high_risk":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-100 text-rose-900 border border-rose-600/40 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-600/40 font-bold px-3 py-1 text-xs shadow-xs">
            <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
            HIGH RISK / PROCEED WITH CAUTION
          </span>
        );
      case "caution":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 text-amber-900 border border-amber-600/40 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-600/40 font-bold px-3 py-1 text-xs shadow-xs">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            MODERATE / WAIT & WATCH
          </span>
        );
      case "auspicious":
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-600/40 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-600/40 font-bold px-3 py-1 text-xs shadow-xs">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            HIGHLY AUSPICIOUS / GREEN LIGHT
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-cyan-100 text-cyan-900 border border-cyan-600/40 dark:bg-cyan-950/40 dark:text-cyan-300 dark:border-cyan-600/40 font-bold px-3 py-1 text-xs shadow-xs">
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            STABLE / NEUTRAL CONDITIONS
          </span>
        );
    }
  };

  return (
    <div
      className="rounded-2xl border p-5 sm:p-6 shadow-md space-y-6"
      style={{
        borderColor: "var(--border-primary)",
        background: "var(--bg-card, var(--bg-secondary))",
      }}
    >
      {/* ── Top Header ────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-4" style={{ borderColor: "var(--border-primary)" }}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold text-xl shadow-sm">
            ✨
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                SBC AI Event Prediction & Guidance
              </h3>
              <span className="rounded-md bg-indigo-500/15 border border-indigo-500/30 px-2 py-0.5 text-[10px] font-semibold text-indigo-400">
                Story Mode
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Clear, practical results you will experience based on active Sarvatobhadra Chakra rays
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          {analysisResult && (
            <div className="flex rounded-lg border p-0.5 text-xs" style={{ borderColor: "var(--border-primary)" }}>
              <button
                type="button"
                onClick={() => setViewMode("structured")}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  viewMode === "structured"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Visual Insights
              </button>
              <button
                type="button"
                onClick={() => setViewMode("markdown")}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  viewMode === "markdown"
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Markdown
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={() => handleGenerate()}
            disabled={isLoading}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 px-4 py-2 text-xs font-bold text-white shadow-md transition-all active:scale-[0.98]"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                <span>Analyzing Transit Story...</span>
              </>
            ) : (
              <>
                <span>✨</span>
                <span>{analysisResult ? "Update AI Story" : "Generate AI Event Insights"}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Event Category Selector Tabs ─────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {EVENT_TABS.map((tab) => {
          const isSelected = selectedEventType === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => {
                setSelectedEventType(tab.id);
                handleGenerate(tab.id);
              }}
              className={`flex flex-col items-start p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                isSelected
                  ? "border-indigo-500 bg-indigo-500/10 shadow-sm ring-2 ring-indigo-500/30"
                  : "border-border hover:border-indigo-500/40 bg-background/50 hover:bg-background/80"
              }`}
            >
              <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                <span className="text-sm">{tab.icon}</span>
                <span>{tab.label}</span>
              </div>
              <span className="text-[11px] text-muted-foreground mt-1 line-clamp-1">
                {tab.desc}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── Error Banner ─────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 p-3.5 text-xs text-rose-400 flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => handleGenerate()}
            className="underline font-bold ml-2 hover:text-rose-300 cursor-pointer"
          >
            Retry Analysis
          </button>
        </div>
      )}

      {/* ── Analysis Content ─────────────────────────────────────────────── */}
      {analysisResult ? (
        viewMode === "structured" ? (
          <div className="space-y-5">
            {/* 1. 🎯 Bottom Line Verdict Hero Card */}
            <div className="rounded-xl border p-4 sm:p-5 bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800 text-slate-100 shadow-sm space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                  <span>🎯</span>
                  <span>Bottom Line Verdict</span>
                </div>
                <div>{renderVerdictBadge(analysisResult.verdict_badge)}</div>
              </div>

              <div className="text-base sm:text-lg font-bold text-white tracking-tight">
                {analysisResult.verdict || analysisResult.title}
              </div>

              {/* Quick visual chips */}
              {analysisResult.quick_chips && analysisResult.quick_chips.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {analysisResult.quick_chips.map((chip, idx) => (
                    <span
                      key={idx}
                      className="rounded-lg bg-slate-800/90 border border-slate-700/60 px-2.5 py-1 text-xs font-semibold text-slate-200"
                    >
                      {chip}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* 2. 📖 The Complete Story (Plain English Results) */}
            <div className="rounded-xl border p-4 sm:p-5 bg-indigo-500/5 border-indigo-500/20 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-400">
                <span>📖</span>
                <span>The Story: What Results You Will Experience</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                {analysisResult.the_story || analysisResult.executive_summary}
              </p>
            </div>

            {/* 3. Two-Column Layout: Major Warnings vs Safe Zones */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 🚨 Major Warning Points */}
              <div className="rounded-xl border p-4 bg-rose-500/5 border-rose-500/25 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-400">
                  <span>🚨</span>
                  <span>Major Warning Points (What NOT to Do)</span>
                </div>

                <div className="space-y-2.5">
                  {analysisResult.major_warnings && analysisResult.major_warnings.length > 0 ? (
                    analysisResult.major_warnings.map((w, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-background/80 border border-rose-500/20 p-3 space-y-1.5"
                      >
                        <div className="text-xs font-bold text-rose-500 flex items-start gap-1.5">
                          <span className="mt-0.5 text-xs">🛑</span>
                          <span>{w.headline}</span>
                        </div>
                        <p className="text-xs text-slate-900 dark:text-slate-100 font-medium">
                          <strong className="text-rose-500 font-bold">Avoid:</strong> {w.what_not_to_do}
                        </p>
                        <div className="text-[10px] text-muted-foreground">
                          <strong>Area:</strong> {w.affected_area}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-muted-foreground p-2">
                      No critical warning alerts detected for this transit window.
                    </div>
                  )}
                </div>
              </div>

              {/* 🛡️ Safe Zones & Active Protections */}
              <div className="rounded-xl border p-4 bg-emerald-500/5 border-emerald-500/25 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                  <span>🛡️</span>
                  <span>Safe Zones & Active Protections</span>
                </div>

                <div className="space-y-2.5">
                  {analysisResult.safe_zones && analysisResult.safe_zones.length > 0 ? (
                    analysisResult.safe_zones.map((s, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-background/80 border border-emerald-500/20 p-3 space-y-1.5"
                      >
                        <div className="text-xs font-bold text-emerald-500 flex items-start gap-1.5">
                          <span className="mt-0.5 text-xs">✔</span>
                          <span>{s.plain_title}</span>
                        </div>
                        <p className="text-xs text-slate-700 dark:text-slate-300">
                          {s.benefit}
                        </p>
                        <div className="text-[10px] text-muted-foreground">
                          <strong>Protected Anchor:</strong> {s.area_name}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-muted-foreground p-2">
                      Standard natal baseline protection remains active.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 4. 💡 Direct Practical Advice (Action Steps) */}
            {analysisResult.practical_steps && analysisResult.practical_steps.length > 0 && (
              <div className="rounded-xl border p-4 sm:p-5 bg-amber-500/5 border-amber-500/20 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
                  <span>💡</span>
                  <span>Direct Practical Action Steps</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {analysisResult.practical_steps.map((step, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg bg-background/80 border border-amber-500/20 p-3 space-y-2"
                    >
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold">
                          {idx + 1}
                        </span>
                        <h5 className="text-xs font-bold text-foreground">
                          {step.action}
                        </h5>
                      </div>
                      <p className="text-xs text-slate-700 dark:text-slate-300">
                        <strong>Why:</strong> {step.why}
                      </p>
                      <div className="text-[10px] text-amber-400/90 font-medium">
                        ⏱️ <strong>Tip:</strong> {step.timing_tip}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. 🏛️ 10 Sensitive Points Real-time Status Cards */}
            {analysisResult.sangya_breakdown && analysisResult.sangya_breakdown.length > 0 && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h5 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    Sensitive Life Pillars Real-Time Status
                  </h5>
                  <span className="text-[10px] text-muted-foreground">
                    10 Sangyas Matrix
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
                  {analysisResult.sangya_breakdown.map((item) => {
                    const isAff = item.status === "afflicted";
                    const isAct = item.status === "activated";
                    const isMix = item.status === "mixed";
                    return (
                      <div
                        key={item.sangya_key}
                        className={`rounded-xl p-3 border text-xs flex flex-col justify-between transition-all ${
                          isAff
                            ? "border-rose-500/40 bg-rose-500/10 shadow-xs"
                            : isAct
                            ? "border-emerald-500/40 bg-emerald-500/10 shadow-xs"
                            : isMix
                            ? "border-amber-500/40 bg-amber-500/10"
                            : "border-border bg-background/50"
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between font-bold">
                            <span className="text-foreground">{item.sangya_name}</span>
                            <span
                              className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold uppercase ${
                                isAff
                                  ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                  : isAct
                                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                  : isMix
                                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                                  : "text-muted-foreground"
                              }`}
                            >
                              {item.status}
                            </span>
                          </div>
                          <p className="text-[10px] text-muted-foreground mt-0.5">{item.nakshatra_name}</p>
                        </div>
                        <p className="text-[10px] text-slate-700 dark:text-slate-300 mt-2 line-clamp-2">
                          {item.domain}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* ── Markdown View ──────────────────────────────────────────────── */
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Formatted Markdown Export</span>
              <button
                type="button"
                onClick={handleCopyMarkdown}
                className="rounded-lg border px-3 py-1 text-xs font-semibold text-foreground hover:bg-muted cursor-pointer transition-colors"
                style={{ borderColor: "var(--border-primary)" }}
              >
                {copied ? "Copied to Clipboard! ✓" : "Copy Markdown"}
              </button>
            </div>
            <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 sm:p-5 text-xs text-slate-200 font-mono leading-relaxed border border-slate-800">
              {analysisResult.markdown_report}
            </pre>
          </div>
        )
      ) : (
        /* ── Empty State Call to Action ──────────────────────────────────── */
        <div
          className="rounded-xl border border-dashed p-8 text-center space-y-3 bg-muted/10"
          style={{ borderColor: "var(--border-primary)" }}
        >
          <span className="text-3xl">🔮</span>
          <h4 className="text-sm font-bold text-foreground">
            Generate Plain-Language AI Insights
          </h4>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Choose an event category tab above or click <strong>Generate AI Event Insights</strong> to see your bottom line verdict, major warnings, and protected safe zones.
          </p>
        </div>
      )}
    </div>
  );
}
