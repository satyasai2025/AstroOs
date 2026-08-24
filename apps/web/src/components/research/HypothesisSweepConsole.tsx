"use client";

import { useState, useEffect, useId } from "react";
import { api } from "@/lib/api";

export interface HypothesisDefinition {
  id: string;
  title: string;
  category: string;
  exposure_rule: {
    rule_type: string;
    parameters: Record<string, unknown>;
    description?: string;
  };
  target_outcome: string;
  description: string;
  pre_registered: boolean;
  classical_reference?: string | null;
}

export interface ContingencyTableData {
  a_exposed_cases: number;
  b_exposed_controls: number;
  c_unexposed_cases: number;
  d_unexposed_controls: number;
  total_n: number;
  total_exposed: number;
  total_unexposed: number;
  total_cases: number;
  total_controls: number;
  exposure_rate_cases: number;
  exposure_rate_controls: number;
}

export interface HypothesisResult {
  hypothesis: HypothesisDefinition;
  contingency_table: ContingencyTableData;
  sample_size_n: number;
  odds_ratio: number;
  odds_ratio_ci_lower: number;
  odds_ratio_ci_upper: number;
  relative_risk: number;
  relative_risk_ci_lower: number;
  relative_risk_ci_upper: number;
  cohen_w_effect_size: number;
  cramers_v: number;
  chi_square_stat: number;
  chi_square_p_value: number;
  fisher_exact_p_value: number;
  is_significant_nominal: boolean;
  bonferroni_adjusted_alpha: number;
  is_significant_bonferroni: boolean;
  fdr_q_value: number;
  is_significant_fdr: boolean;
  has_small_sample_warning: boolean;
  statistical_power_estimate: number;
  verdict: string;
  audit_trace: string[];
}

export interface MultiSweepResponse {
  sweep_id: string;
  cohort_tag: string;
  total_cohort_size: number;
  hypotheses_tested_count: number;
  bonferroni_alpha: number;
  nominal_significant_count: number;
  fdr_significant_count: number;
  bonferroni_significant_count: number;
  results: HypothesisResult[];
  generated_at: string;
}

const SAMPLE_COHORT = [
  {
    planets: [
      { planet: "Venus", house_number: 7 },
      { planet: "Sun", house_number: 10 },
      { planet: "Jupiter", house_number: 2 },
      { planet: "Mercury", house_number: 5 },
      { planet: "Saturn", house_number: 11 },
      { planet: "Rahu", house_number: 6 },
    ],
    outcomes: {
      marriage_before_30: true,
      executive_leadership: true,
      top_quartile_wealth: true,
      longevity_over_75: true,
      advanced_academic_degree: true,
      chronic_health_issue: false,
    },
  },
  {
    planets: [
      { planet: "Venus", house_number: 1 },
      { planet: "Sun", house_number: 1 },
      { planet: "Jupiter", house_number: 9 },
      { planet: "Mercury", house_number: 9 },
      { planet: "Saturn", house_number: 8 },
      { planet: "Rahu", house_number: 12 },
    ],
    outcomes: {
      marriage_before_30: true,
      executive_leadership: true,
      top_quartile_wealth: true,
      longevity_over_75: true,
      advanced_academic_degree: true,
      chronic_health_issue: true,
    },
  },
  {
    planets: [
      { planet: "Venus", house_number: 4 },
      { planet: "Sun", house_number: 11 },
      { planet: "Jupiter", house_number: 5 },
      { planet: "Mercury", house_number: 4 },
      { planet: "Saturn", house_number: 6 },
      { planet: "Rahu", house_number: 8 },
    ],
    outcomes: {
      marriage_before_30: true,
      executive_leadership: false,
      top_quartile_wealth: true,
      longevity_over_75: true,
      advanced_academic_degree: true,
      chronic_health_issue: false,
    },
  },
  {
    planets: [
      { planet: "Venus", house_number: 8 },
      { planet: "Sun", house_number: 6 },
      { planet: "Jupiter", house_number: 6 },
      { planet: "Mercury", house_number: 8 },
      { planet: "Saturn", house_number: 1 },
      { planet: "Rahu", house_number: 10 },
    ],
    outcomes: {
      marriage_before_30: false,
      executive_leadership: false,
      top_quartile_wealth: false,
      longevity_over_75: false,
      advanced_academic_degree: false,
      chronic_health_issue: false,
    },
  },
  {
    planets: [
      { planet: "Venus", house_number: 12 },
      { planet: "Sun", house_number: 4 },
      { planet: "Jupiter", house_number: 8 },
      { planet: "Mercury", house_number: 12 },
      { planet: "Saturn", house_number: 4 },
      { planet: "Rahu", house_number: 7 },
    ],
    outcomes: {
      marriage_before_30: false,
      executive_leadership: false,
      top_quartile_wealth: false,
      longevity_over_75: false,
      advanced_academic_degree: false,
      chronic_health_issue: false,
    },
  },
];

export function HypothesisSweepConsole() {
  const [activeTab, setActiveTab] = useState<"single" | "multi">("single");
  const [standardHypotheses, setStandardHypotheses] = useState<HypothesisDefinition[]>([]);
  const [selectedHypothesisId, setSelectedHypothesisId] = useState<string>("HYP-MARRIAGE-01");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Manual 2x2 table override state
  const [cellA, setCellA] = useState<number>(45);
  const [cellB, setCellB] = useState<number>(12);
  const [cellC, setCellC] = useState<number>(15);
  const [cellD, setCellD] = useState<number>(38);

  const [singleResult, setSingleResult] = useState<HypothesisResult | null>(null);
  const [multiResult, setMultiResult] = useState<MultiSweepResponse | null>(null);

  const cellAId = useId();
  const cellBId = useId();
  const cellCId = useId();
  const cellDId = useId();

  // Load standard hypotheses on mount
  useEffect(() => {
    async function fetchStandards() {
      try {
        const data = await api.get<{ total_count: number; hypotheses: HypothesisDefinition[] }>(
          "/api/v1/research/sweeps/standard-hypotheses"
        );
        setStandardHypotheses(data.hypotheses);
        if (data.hypotheses.length > 0) {
          setSelectedHypothesisId(data.hypotheses[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch standard hypotheses:", err);
      }
    }
    fetchStandards();
  }, []);

  const handleEvaluateSingle = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        hypothesis_id: selectedHypothesisId,
        contingency_table: {
          a_exposed_cases: Number(cellA),
          b_exposed_controls: Number(cellB),
          c_unexposed_cases: Number(cellC),
          d_unexposed_controls: Number(cellD),
          total_n: Number(cellA) + Number(cellB) + Number(cellC) + Number(cellD),
          total_exposed: Number(cellA) + Number(cellB),
          total_unexposed: Number(cellC) + Number(cellD),
          total_cases: Number(cellA) + Number(cellC),
          total_controls: Number(cellB) + Number(cellD),
          exposure_rate_cases: 0,
          exposure_rate_controls: 0,
        },
        total_hypotheses_in_sweep: 1,
        nominal_alpha: 0.05,
      };
      const res = await api.post<HypothesisResult>("/api/v1/research/sweeps/evaluate-hypothesis", payload);
      setSingleResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to evaluate hypothesis.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunMultiSweep = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        cohort_tag: "Empirical_Research_Cohort_2026",
        cohort_records: SAMPLE_COHORT,
        nominal_alpha: 0.05,
      };
      const res = await api.post<MultiSweepResponse>("/api/v1/research/sweeps/multi-sweep", payload);
      setMultiResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to run multi-hypothesis sweep.");
    } finally {
      setLoading(false);
    }
  };

  const currentHypothesis = standardHypotheses.find((h) => h.id === selectedHypothesisId);

  return (
    <div
      className="rounded-2xl border p-6 glass-card shadow-xl space-y-6"
      style={{
        borderColor: "var(--border-primary, #334155)",
        backgroundColor: "var(--bg-card, rgba(15, 23, 42, 0.75))",
      }}
    >
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-700/50">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-600 font-bold text-sm">
              🔬
            </span>
            <h2 className="text-lg font-bold text-slate-100 tracking-tight">
              Hypothesis-First Statistical Sweeps Engine
            </h2>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Module 17 · Phase 2
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Pre-registered $H_1$ testing, $2\times 2$ contingency matrices, Odds Ratio (95% CI), Fisher Exact, Bonferroni &amp; Benjamini-Hochberg FDR adjustments.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-900/60 rounded-xl border border-slate-800 self-start md:self-auto">
          <button
            type="button"
            onClick={() => setActiveTab("single")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "single"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Single Hypothesis Deep Dive
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("multi");
              if (!multiResult) handleRunMultiSweep();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "multi"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Multi-Hypothesis Battery Sweep
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300 flex items-center justify-between">
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)} className="underline ml-2">
            Dismiss
          </button>
        </div>
      )}

      {/* SINGLE HYPOTHESIS VIEW */}
      {activeTab === "single" && (
        <div className="space-y-6">
          {/* Hypothesis Selector & Description */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1 space-y-3">
              <label className="block text-xs font-semibold text-slate-300">
                Pre-Registered Classical Hypothesis:
              </label>
              <select
                value={selectedHypothesisId}
                onChange={(e) => setSelectedHypothesisId(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs text-slate-200 outline-none focus:border-indigo-500"
              >
                {standardHypotheses.map((h) => (
                  <option key={h.id} value={h.id}>
                    [{h.category.toUpperCase()}] {h.title}
                  </option>
                ))}
              </select>

              {currentHypothesis && (
                <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-indigo-600">Target Outcome</span>
                    <span className="font-mono text-slate-300 text-[11px]">{currentHypothesis.target_outcome}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-amber-400">Exposure Rule</span>
                    <span className="font-mono text-slate-300 text-[11px]">{currentHypothesis.exposure_rule.rule_type}</span>
                  </div>
                  {currentHypothesis.classical_reference && (
                    <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-1.5 italic">
                      📜 {currentHypothesis.classical_reference}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 2x2 Contingency Input Grid */}
            <div className="lg:col-span-2 space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300">
                  $2 \times 2$ Contingency Matrix Sample Input:
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setCellA(45);
                      setCellB(12);
                      setCellC(15);
                      setCellD(38);
                    }}
                    className="text-[10px] text-slate-400 hover:text-slate-200 underline"
                  >
                    Load Classical Example (N=110)
                  </button>
                  <button
                    type="button"
                    onClick={handleEvaluateSingle}
                    disabled={loading}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all disabled:opacity-50"
                  >
                    {loading ? "Calculating…" : "Run Hypothesis Test"}
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                <table className="w-full text-xs text-center border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="p-2 text-left font-medium">Astrological Exposure</th>
                      <th className="p-2 font-medium text-emerald-400">Case (Outcome +)</th>
                      <th className="p-2 font-medium text-amber-400">Control (Outcome -)</th>
                      <th className="p-2 font-medium text-slate-300">Row Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-slate-800/60">
                      <td className="p-2 text-left font-semibold text-indigo-300">Exposed (+)</td>
                      <td className="p-2">
                        <label htmlFor={cellAId} className="sr-only">Exposed Case Count</label>
                        <input 
                          id={cellAId}
                          type="number"
                          value={cellA}
                          onChange={(e) => setCellA(Math.max(0, parseInt(e.target.value) || 0))}
                          aria-label="Exposed Case Count"
                          className="w-20 rounded border border-indigo-500/40 bg-indigo-950/30 px-2 py-1 text-center font-mono text-emerald-300 font-bold outline-none"
                        />
                      </td>
                      <td className="p-2">
                        <label htmlFor={cellBId} className="sr-only">Exposed Control Count</label>
                        <input 
                          id={cellBId}
                          type="number"
                          value={cellB}
                          onChange={(e) => setCellB(Math.max(0, parseInt(e.target.value) || 0))}
                          aria-label="Exposed Control Count"
                          className="w-20 rounded border border-indigo-500/40 bg-indigo-950/30 px-2 py-1 text-center font-mono text-amber-300 font-bold outline-none"
                        />
                      </td>
                      <td className="p-2 font-mono font-semibold text-slate-300">{cellA + cellB}</td>
                    </tr>
                    <tr className="border-b border-slate-800/60">
                      <td className="p-2 text-left font-semibold text-slate-400">Unexposed (-)</td>
                      <td className="p-2">
                        <label htmlFor={cellCId} className="sr-only">Unexposed Case Count</label>
                        <input 
                          id={cellCId}
                          type="number"
                          value={cellC}
                          onChange={(e) => setCellC(Math.max(0, parseInt(e.target.value) || 0))}
                          aria-label="Unexposed Case Count"
                          className="w-20 rounded border border-slate-700 bg-slate-900/60 px-2 py-1 text-center font-mono text-emerald-300 font-bold outline-none"
                        />
                      </td>
                      <td className="p-2">
                        <label htmlFor={cellDId} className="sr-only">Unexposed Control Count</label>
                        <input 
                          id={cellDId}
                          type="number"
                          value={cellD}
                          onChange={(e) => setCellD(Math.max(0, parseInt(e.target.value) || 0))}
                          aria-label="Unexposed Control Count"
                          className="w-20 rounded border border-slate-700 bg-slate-900/60 px-2 py-1 text-center font-mono text-amber-300 font-bold outline-none"
                        />
                      </td>
                      <td className="p-2 font-mono font-semibold text-slate-300">{cellC + cellD}</td>
                    </tr>
                    <tr className="text-slate-400 font-semibold bg-slate-900/40">
                      <td className="p-2 text-left text-slate-300">Column Total</td>
                      <td className="p-2 font-mono text-emerald-400">{cellA + cellC}</td>
                      <td className="p-2 font-mono text-amber-400">{cellB + cellD}</td>
                      <td className="p-2 font-mono text-indigo-600 font-bold">{cellA + cellB + cellC + cellD} (N)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* RESULTS CARD */}
          {singleResult && (
            <div className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-5 space-y-5">
              {/* Verdict banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-indigo-500/20">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400">Scientific Verdict:</span>
                  <span
                    className={`text-xs uppercase tracking-wider font-bold px-2.5 py-1 rounded-full border ${
                      singleResult.verdict === "CONFIRMED_SIGNIFICANT"
                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                        : singleResult.verdict === "TREND_SUGGESTIVE"
                        ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                        : singleResult.verdict === "INVERSE_CORRELATION"
                        ? "bg-purple-500/20 text-purple-300 border-purple-500/40"
                        : "bg-slate-700/30 text-slate-400 border-slate-600/40"
                    }`}
                  >
                    {singleResult.verdict.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span>Sample Size: <strong className="text-slate-200">{singleResult.sample_size_n}</strong></span>
                  <span>Power Estimate: <strong className="text-slate-200">{(singleResult.statistical_power_estimate * 100).toFixed(0)}%</strong></span>
                </div>
              </div>

              {/* Key Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-3 text-center">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Odds Ratio (OR)</div>
                  <div className="text-xl font-mono font-bold text-indigo-600 mt-1">{singleResult.odds_ratio}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                    95% CI: [{singleResult.odds_ratio_ci_lower}, {singleResult.odds_ratio_ci_upper}]
                  </div>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-3 text-center">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Fisher Exact p-value</div>
                  <div className={`text-xl font-mono font-bold mt-1 ${singleResult.fisher_exact_p_value < 0.05 ? "text-emerald-400" : "text-slate-300"}`}>
                    {singleResult.fisher_exact_p_value < 0.0001 ? "< 0.0001" : singleResult.fisher_exact_p_value}
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                    {singleResult.is_significant_nominal ? "Nominally Sig (p < 0.05)" : "Not Significant"}
                  </div>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-3 text-center">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Pearson Chi-Square</div>
                  <div className="text-xl font-mono font-bold text-cyan-400 mt-1">{singleResult.chi_square_stat}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                    Yates p = {singleResult.chi_square_p_value}
                  </div>
                </div>

                <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-3 text-center">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Effect Size (Cohen&apos;s w)</div>
                  <div className="text-xl font-mono font-bold text-amber-400 mt-1">{singleResult.cohen_w_effect_size}</div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                    {singleResult.cohen_w_effect_size >= 0.5 ? "Large Effect" : singleResult.cohen_w_effect_size >= 0.3 ? "Medium Effect" : "Small Effect"}
                  </div>
                </div>
              </div>

              {/* Audit trace logs */}
              <div className="rounded-lg bg-slate-950/70 border border-slate-800/80 p-3 space-y-1">
                <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Methodology &amp; Calculation Audit Trace</div>
                <div className="space-y-1 mt-1">
                  {singleResult.audit_trace.map((line, idx) => (
                    <div key={idx} className="text-[11px] font-mono text-slate-300 flex items-start gap-1.5">
                      <span className="text-indigo-600">•</span>
                      <span>{line}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* MULTI-HYPOTHESIS SWEEP VIEW */}
      {activeTab === "multi" && (
        <div className="space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold text-slate-200">
                Standard Battery Multi-Hypothesis Sweep
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates all pre-registered classical Vedic hypotheses simultaneously with Bonferroni and Benjamini-Hochberg False Discovery Rate corrections.
              </p>
            </div>

            <button
              type="button"
              onClick={handleRunMultiSweep}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all disabled:opacity-50 self-start sm:self-auto"
            >
              {loading ? "Sweeping Cohort…" : "Re-run Multi-Sweep Battery"}
            </button>
          </div>

          {multiResult && (
            <div className="space-y-4">
              {/* Summary Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-3">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Hypotheses Tested</span>
                  <div className="text-lg font-mono font-bold text-slate-100 mt-1">{multiResult.hypotheses_tested_count}</div>
                </div>
                <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-3">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Bonferroni Adjusted α</span>
                  <div className="text-lg font-mono font-bold text-amber-400 mt-1">{multiResult.bonferroni_alpha}</div>
                </div>
                <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-3">
                  <span className="text-[10px] uppercase font-bold text-slate-400">FDR Sig Discoveries</span>
                  <div className="text-lg font-mono font-bold text-emerald-400 mt-1">{multiResult.fdr_significant_count}</div>
                </div>
                <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-3">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Bonferroni Confirmed</span>
                  <div className="text-lg font-mono font-bold text-indigo-600 mt-1">{multiResult.bonferroni_significant_count}</div>
                </div>
              </div>

              {/* Table of Results */}
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/40">
                      <th className="p-3 font-semibold">Hypothesis / Category</th>
                      <th className="p-3 font-semibold text-center">Odds Ratio (95% CI)</th>
                      <th className="p-3 font-semibold text-center">Nominal p</th>
                      <th className="p-3 font-semibold text-center">FDR q-value</th>
                      <th className="p-3 font-semibold text-center">Bonferroni Sig</th>
                      <th className="p-3 font-semibold text-right">Verdict</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {multiResult.results.map((res) => (
                      <tr key={res.hypothesis.id} className="hover:bg-slate-900/30 transition-colors">
                        <td className="p-3">
                          <div className="font-semibold text-slate-200">{res.hypothesis.title}</div>
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                            [{res.hypothesis.category.toUpperCase()}] {res.hypothesis.exposure_rule.description}
                          </div>
                        </td>
                        <td className="p-3 text-center font-mono">
                          <span className="font-bold text-indigo-300">{res.odds_ratio}</span>
                          <span className="text-[10px] text-slate-400 block">[{res.odds_ratio_ci_lower}, {res.odds_ratio_ci_upper}]</span>
                        </td>
                        <td className="p-3 text-center font-mono">
                          <span className={res.fisher_exact_p_value < 0.05 ? "text-emerald-400 font-bold" : "text-slate-400"}>
                            {res.fisher_exact_p_value}
                          </span>
                        </td>
                        <td className="p-3 text-center font-mono">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            res.is_significant_fdr ? "bg-emerald-500/20 text-emerald-300" : "text-slate-400"
                          }`}>
                            {res.fdr_q_value}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          {res.is_significant_bonferroni ? (
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-[10px]">
                              PASS
                            </span>
                          ) : (
                            <span className="text-slate-400 text-[10px]">Fail</span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          <span
                            className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                              res.verdict === "CONFIRMED_SIGNIFICANT"
                                ? "bg-emerald-500/20 text-emerald-300"
                                : res.verdict === "TREND_SUGGESTIVE"
                                ? "bg-cyan-500/20 text-cyan-300"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {res.verdict.replace(/_/g, " ")}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
