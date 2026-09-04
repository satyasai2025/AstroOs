"use client";

import React, { useState, useEffect } from "react";
import {
  synthesizePrediction,
  scanConfluenceDomains,
  freezeToP7Validation,
  type UnifiedPredictionSynthesis,
  type PredictionCategory,
  type SystemContribution,
  type FreezeToP7Response,
} from "@/lib/predictionConfluence";

const CANONICAL_DOMAINS: { key: PredictionCategory; label: string; icon: string }[] = [
  { key: "career", label: "Career & Status", icon: "💼" },
  { key: "marriage", label: "Marriage & Alliances", icon: "💍" },
  { key: "finance", label: "Finance & Wealth", icon: "💰" },
  { key: "health", label: "Health & Vitality", icon: "🩺" },
  { key: "relocation", label: "Relocation & Travel", icon: "✈️" },
  { key: "education", label: "Education & Intellect", icon: "🎓" },
  { key: "spiritual", label: "Spiritual & Sadhana", icon: "🧘" },
];

export function PredictionConfluenceWorkspace() {
  const [selectedDomain, setSelectedDomain] = useState<PredictionCategory>("career");
  const [horizonMonths, setHorizonMonths] = useState<number>(12);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [synthesis, setSynthesis] = useState<UnifiedPredictionSynthesis | null>(null);

  // Freeze Modal state
  const [isFreezing, setIsFreezing] = useState<boolean>(false);
  const [freezeResult, setFreezeResult] = useState<FreezeToP7Response | null>(null);
  const [activeProvenanceTab, setActiveProvenanceTab] = useState<string>("CALCULATED_EPHEMERIS");

  const loadSynthesis = async (category: PredictionCategory, horizon: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await synthesizePrediction({
        category,
        horizon_months: horizon,
      });
      setSynthesis(res.synthesis);
    } catch (err: any) {
      setError(err?.message || "Failed to load multi-system prediction synthesis.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSynthesis(selectedDomain, horizonMonths);
  }, [selectedDomain, horizonMonths]);

  const handleFreezeToP7 = async () => {
    if (!synthesis) return;
    setIsFreezing(true);
    try {
      const res = await freezeToP7Validation({
        synthesis_id: synthesis.synthesis_id,
        synthesis_payload: synthesis,
        target_split_type: "VALIDATION",
      });
      setFreezeResult(res);
    } catch (err: any) {
      alert(`Freeze failed: ${err.message}`);
    } finally {
      setIsFreezing(false);
    }
  };

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case "UNANIMOUS_CONFLUENCE":
        return { text: "Unanimous Confluence (6/6)", bg: "bg-emerald-100 text-emerald-800 border-emerald-300" };
      case "STRONG_CONFLUENCE":
        return { text: "Strong Confluence (>= 75%)", bg: "bg-indigo-100 text-indigo-800 border-indigo-300" };
      case "MODERATE_CONFLUENCE":
        return { text: "Moderate Confluence (>= 50%)", bg: "bg-blue-100 text-blue-800 border-blue-300" };
      case "CONFLICTED_VETO":
        return { text: "Active Veto / Conflicted", bg: "bg-red-100 text-red-800 border-red-300 font-bold" };
      default:
        return { text: "Weak / Unconverged", bg: "bg-slate-100 text-slate-700 border-slate-300" };
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUPPORTING":
        return <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200">Supporting</span>;
      case "CONTRADICTING_VETO":
        return <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-bold text-red-800 border border-red-200">Active Veto</span>;
      case "NEUTRAL":
        return <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700 border border-slate-200">Neutral / Inconclusive</span>;
      default:
        return <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-500">Unavailable</span>;
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-12">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🔮</span>
              <h1 className="text-2xl font-bold text-slate-900">
                Unified Multi-System Prediction Synthesis
              </h1>
              <span className="rounded-md bg-indigo-50 px-2.5 py-0.5 text-xs font-bold text-indigo-700 border border-indigo-200">
                Priority 8 Confluence Engine
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-600">
              Deterministic cross-system evaluation of Dasha, KP Cuspal Sub-Lords, SBC Vedha Rays, Classical Yogas, and P7 Empirical Backtests with zero black-box scoring.
            </p>
          </div>

          {/* Freeze Action */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleFreezeToP7}
              disabled={loading || !synthesis || isFreezing}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-indigo-700 disabled:opacity-50 transition cursor-pointer"
            >
              <span>🔒</span>
              {isFreezing ? "Freezing..." : "Freeze to P7 Validation Registry"}
            </button>
          </div>
        </div>

        {/* Domain Selector & Horizon Slider */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-4">
          <div className="flex flex-wrap gap-2">
            {CANONICAL_DOMAINS.map((dom) => {
              const active = selectedDomain === dom.key;
              return (
                <button
                  key={dom.key}
                  onClick={() => setSelectedDomain(dom.key)}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition cursor-pointer ${
                    active
                      ? "bg-indigo-600 text-white shadow-xs"
                      : "bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200"
                  }`}
                >
                  <span>{dom.icon}</span>
                  {dom.label}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs font-semibold text-slate-600">
              Prediction Horizon:
            </label>
            <select
              value={horizonMonths}
              onChange={(e) => setHorizonMonths(Number(e.target.value))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-800 shadow-2xs"
            >
              <option value={3}>3 Months (Immediate)</option>
              <option value={6}>6 Months (Near-Term)</option>
              <option value={12}>12 Months (1 Year)</option>
              <option value={24}>24 Months (2 Years)</option>
            </select>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-xl border border-slate-200 bg-white p-8">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-r-transparent"></div>
            <p className="mt-3 text-sm font-semibold text-slate-700">Synthesizing 6 Astrological & Empirical Systems...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Freeze Confirmation Alert */}
      {freezeResult && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-sm font-bold text-emerald-900 flex items-center gap-1.5">
                <span>✅</span> Prediction Successfully Frozen into P7 Validation Registry
              </h2>
              <p className="mt-1 text-xs text-emerald-800">
                Immutable Snapshot ID: <code className="font-mono font-bold text-emerald-950">{freezeResult.prediction_id}</code>
              </p>
              <p className="mt-0.5 text-xs text-emerald-700 font-mono break-all">
                SHA-256 Evidence Hash: {freezeResult.evidence_hash}
              </p>
            </div>
            <button
              onClick={() => setFreezeResult(null)}
              className="text-xs font-semibold text-emerald-800 hover:text-emerald-950"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {!loading && synthesis && (
        <>
          {/* Section 1: Master Confluence Matrix Banner */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Target Event Synthesis
                </span>
                <h2 className="text-lg font-bold text-slate-900">
                  {synthesis.synthesized_event_description}
                </h2>
                <p className="text-xs text-slate-600 mt-0.5">
                  Native: <strong className="text-slate-800">{synthesis.subject_name}</strong> • Chart ID: <span className="font-mono text-slate-700">{synthesis.chart_id}</span>
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-2xl font-black text-slate-900">
                    {synthesis.confluence_matrix.supporting_count} / {synthesis.confluence_matrix.total_systems}
                  </div>
                  <span className="text-[11px] font-semibold text-slate-500">
                    Systems Supporting ({Math.round(synthesis.confluence_matrix.confluence_ratio * 100)}% Agreement)
                  </span>
                </div>
                <div className={`rounded-lg border px-3 py-2 text-xs font-semibold ${getVerdictBadge(synthesis.confluence_matrix.synthesized_verdict).bg}`}>
                  {getVerdictBadge(synthesis.confluence_matrix.synthesized_verdict).text}
                </div>
              </div>
            </div>

            {/* Veto Alert Box if any active vetoes */}
            {synthesis.confluence_matrix.active_vetoes.length > 0 && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <h2 className="text-xs font-bold text-red-900 flex items-center gap-1.5">
                  <span>⚠️</span> Active Astrological Vetoes / Obstructions ({synthesis.confluence_matrix.veto_count})
                </h2>
                <ul className="mt-2 list-disc pl-5 text-xs text-red-800 space-y-1 font-medium">
                  {synthesis.confluence_matrix.active_vetoes.map((v, idx) => (
                    <li key={idx}>{v}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="rounded-lg border border-slate-100 bg-slate-50 p-3.5 text-xs text-slate-700">
              <strong className="font-semibold text-slate-900">Synthesis Rationale: </strong>
              {synthesis.confluence_matrix.verdict_rationale}
            </div>
          </div>

          {/* Section 2: 6 Independent Systems Deep-Dive Grid */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              6-System Evidence & Agreement Matrix
            </h3>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {synthesis.system_contributions.map((sys: SystemContribution) => (
                <div
                  key={sys.system_id}
                  className={`rounded-xl border p-4 shadow-2xs space-y-3 bg-white ${
                    sys.support_status === "CONTRADICTING_VETO"
                      ? "border-red-300 ring-1 ring-red-300/30"
                      : sys.support_status === "SUPPORTING"
                      ? "border-emerald-200"
                      : "border-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h2 className="text-xs font-bold text-slate-900">
                      {sys.system_name}
                    </h2>
                    {getStatusBadge(sys.support_status)}
                  </div>

                  <div className="space-y-1">
                    <div className="text-[11px] font-semibold text-indigo-700">
                      Factor: {sys.rule_or_factor}
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed font-normal">
                      {sys.rationale}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-between border-t border-slate-100 pt-2 text-[10px] text-slate-500">
                    <span>
                      Provenance: <strong className="font-mono text-slate-700">{sys.provenance_type}</strong>
                    </span>
                    {sys.primary_houses.length > 0 && (
                      <span>
                        Bhavas: <strong className="text-slate-700">{sys.primary_houses.join(", ")}</strong>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Peak Timing Window Intersection */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Synthesized Timing Window
                </span>
                <h3 className="text-base font-bold text-slate-900">
                  Peak Fructification Date:{" "}
                  <span className="text-indigo-600">
                    {new Date(synthesis.synthesized_timing_window.peak_fructification_date).toLocaleDateString(undefined, {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </h3>
              </div>

              <div className="text-xs font-medium text-slate-600 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
                Window: {new Date(synthesis.synthesized_timing_window.window_start).toLocaleDateString()} — {new Date(synthesis.synthesized_timing_window.window_end).toLocaleDateString()}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3 border-t border-slate-100 pt-3">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-1">
                <span className="text-[11px] font-bold text-slate-700">Dasha Trigger</span>
                <p className="text-xs text-slate-600">
                  Sub-Period: <strong className="text-slate-800">{synthesis.synthesized_timing_window.dasha_sub_period}</strong>
                </p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-1">
                <span className="text-[11px] font-bold text-slate-700">Transit Trigger</span>
                <p className="text-xs text-slate-600">
                  {synthesis.synthesized_timing_window.transit_trigger}
                </p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 space-y-1">
                <span className="text-[11px] font-bold text-slate-700">SBC Contact Trigger</span>
                <p className="text-xs text-slate-600">
                  {synthesis.synthesized_timing_window.sbc_trigger_moment}
                </p>
              </div>
            </div>
          </div>

          {/* Section 4: 3-Tier Evidence Provenance Explorer */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Evidence Provenance Isolation
                </span>
                <h2 className="text-base font-bold text-slate-900">
                  Auditable 3-Way Evidence Categorization
                </h2>
              </div>

              <div className="flex gap-1.5 rounded-lg bg-slate-100 p-1 border border-slate-200">
                <button
                  onClick={() => setActiveProvenanceTab("CALCULATED_EPHEMERIS")}
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition cursor-pointer ${
                    activeProvenanceTab === "CALCULATED_EPHEMERIS"
                      ? "bg-white text-indigo-700 shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Calculated (Ephemeris)
                </button>
                <button
                  onClick={() => setActiveProvenanceTab("CLASSICAL_LITERATURE")}
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition cursor-pointer ${
                    activeProvenanceTab === "CLASSICAL_LITERATURE"
                      ? "bg-white text-indigo-700 shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Classical (Literature)
                </button>
                <button
                  onClick={() => setActiveProvenanceTab("EMPIRICAL_BACKTEST")}
                  className={`rounded-md px-3 py-1 text-xs font-semibold transition cursor-pointer ${
                    activeProvenanceTab === "EMPIRICAL_BACKTEST"
                      ? "bg-white text-indigo-700 shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Empirical (P7 Backtest)
                </button>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2">
              <h3 className="text-xs font-bold text-slate-800">
                {activeProvenanceTab === "CALCULATED_EPHEMERIS" && "🔭 Exact Astronomical Longitudes & Mathematical Computations"}
                {activeProvenanceTab === "CLASSICAL_LITERATURE" && "📜 Foundational Sanskrit Treatises & Canonical Verses"}
                {activeProvenanceTab === "EMPIRICAL_BACKTEST" && "📊 Historical Validation Cohorts & Wilson Confidence Intervals"}
              </h3>

              <ul className="space-y-2">
                {synthesis.provenance_breakdown[activeProvenanceTab]?.map((item, idx) => (
                  <li key={idx} className="rounded-md bg-white border border-slate-200 p-2.5 text-xs text-slate-700 font-mono leading-relaxed">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Section 5: P7 Empirical Track Record & SHA-256 Audit Seal */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Empirical Track Record */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  P7 Empirical Track Record
                </h3>
                <span className="text-[11px] font-semibold text-slate-500">
                  Cohort: {synthesis.empirical_track_record.matched_cohort_name}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">Sample Size (n)</span>
                  <div className="text-lg font-black text-slate-900">
                    {synthesis.empirical_track_record.sample_size}
                  </div>
                </div>
                <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">Historical Hit-Rate</span>
                  <div className="text-lg font-black text-emerald-700">
                    {Math.round(synthesis.empirical_track_record.historical_hit_rate * 100)}%
                  </div>
                </div>
                <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">Wilson 95% CI</span>
                  <div className="text-xs font-bold text-indigo-700 mt-1">
                    [{synthesis.empirical_track_record.wilson_95_ci[0].toFixed(2)}, {synthesis.empirical_track_record.wilson_95_ci[1].toFixed(2)}]
                  </div>
                </div>
              </div>

              {synthesis.empirical_track_record.sample_size_warning && (
                <div className="rounded-md bg-amber-50 border border-amber-200 p-2 text-xs text-amber-900">
                  ⚠️ {synthesis.empirical_track_record.sample_size_warning}
                </div>
              )}

              <p className="text-[11px] text-slate-500 italic">
                * Note: Historical empirical metrics represent technique performance on verified benchmark datasets and are never converted into individual prediction probability.
              </p>
            </div>

            {/* SHA-256 Audit Seal */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  SHA-256 Synthesis Audit Hash
                </h3>
                <span className="rounded-full bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 text-[10px] font-bold text-indigo-700">
                  IMMUTABLE PROVENANCE
                </span>
              </div>

              <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 font-mono text-xs text-slate-800 break-all select-all">
                {synthesis.synthesis_hash}
              </div>

              <p className="text-xs text-slate-600">
                This checksum guarantees zero lookahead leakage, freezes exact ephemeris calculation states, and locks all 6 analytical contributions before outcome observation.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
