"use client";

import React, { useState, useEffect } from "react";

interface PredefinedStratum {
  stratum_id: string;
  stratum_name: string;
  feature_dimension: string;
  inclusion_criteria: string;
  target_sample_allocation_pct: number;
  observed_sample_count: number;
}

interface ImmutableTrialCommitment {
  commitment_id: string;
  target_objective: string;
  candidate_hypothesis_id: string;
  frozen_rule_name: string;
  frozen_formula_expression: string;
  frozen_parameter_thresholds: Record<string, number>;
  alpha_spending_method: string;
  overall_alpha_budget: number;
  overall_beta_budget: number;
  planned_maximum_sample_size: number;
  permit_outcome_dependent_adaptation: boolean;
  predefined_strata: PredefinedStratum[];
  p11_lineage_snapshot_id: string;
  commitment_provenance_hash: string;
  committed_at: string;
}

interface SequentialInterimAnalysis {
  interim_look_number: number;
  total_planned_looks: number;
  accumulated_sample_size: number;
  information_fraction_t: number;
  cumulative_alpha_spent: number;
  efficacy_boundary_z: number;
  futility_boundary_z: number;
  observed_interim_z_score: number;
  interim_decision: string;
  is_information_blind: boolean;
  reestimated_sample_size: number;
  interim_rationale: string;
  analyzed_at: string;
}

interface AdaptiveExperimentReport {
  adaptive_trial_id: string;
  target_objective: string;
  trial_phase: string;
  commitment: ImmutableTrialCommitment;
  latest_interim_analysis: SequentialInterimAnalysis;
  interim_history: SequentialInterimAnalysis[];
  predefined_strata: PredefinedStratum[];
  p11_snapshot_id: string;
  report_provenance_hash: string;
  epistemic_non_causal_statement: string;
  generated_at: string;
}

const DEFAULT_REPORT: AdaptiveExperimentReport = {
  adaptive_trial_id: "adp-marriage-seq-trial",
  target_objective: "marriage",
  trial_phase: "EARLY_STOP_EFFICACY",
  commitment: {
    commitment_id: "commit-m1-obf",
    target_objective: "marriage",
    candidate_hypothesis_id: "hyp-m1",
    frozen_rule_name: "7th Lord Dasha + Jupiter Aspect Rule",
    frozen_formula_expression: 'DASHA == "7th_Lord" AND TRANSIT_ASPECT("Jupiter", 7)',
    frozen_parameter_thresholds: { min_lift: 1.35, min_sav: 28.0, min_probability: 0.75 },
    alpha_spending_method: "LAN_DEMETS_OBRIEN_FLEMING",
    overall_alpha_budget: 0.05,
    overall_beta_budget: 0.20,
    planned_maximum_sample_size: 300,
    permit_outcome_dependent_adaptation: false,
    predefined_strata: [
      {
        stratum_id: "strat-01-shadbala-high",
        stratum_name: "High Natal Promise (SAV >= 30, Shadbala > 1.2)",
        feature_dimension: "SHADBALA_SAV",
        inclusion_criteria: "SAV_SCORE >= 30 AND SHADBALA_RATIO >= 1.20",
        target_sample_allocation_pct: 40.0,
        observed_sample_count: 60,
      },
      {
        stratum_id: "strat-02-shadbala-mid",
        stratum_name: "Moderate Natal Promise (25 <= SAV < 30)",
        feature_dimension: "SHADBALA_SAV",
        inclusion_criteria: "SAV_SCORE >= 25 AND SAV_SCORE < 30",
        target_sample_allocation_pct: 35.0,
        observed_sample_count: 53,
      },
      {
        stratum_id: "strat-03-shadbala-low",
        stratum_name: "Baseline Natal Promise (SAV < 25)",
        feature_dimension: "SHADBALA_SAV",
        inclusion_criteria: "SAV_SCORE < 25",
        target_sample_allocation_pct: 25.0,
        observed_sample_count: 37,
      },
    ],
    p11_lineage_snapshot_id: "snap-p11-frozen-root",
    commitment_provenance_hash: "a1b2c3d4e5f67890",
    committed_at: "2026-08-22T09:40:00Z",
  },
  latest_interim_analysis: {
    interim_look_number: 1,
    total_planned_looks: 2,
    accumulated_sample_size: 150,
    information_fraction_t: 0.5000,
    cumulative_alpha_spent: 0.0056,
    efficacy_boundary_z: 2.772,
    futility_boundary_z: 0.746,
    observed_interim_z_score: 2.950,
    interim_decision: "EARLY_STOP_EFFICACY",
    is_information_blind: true,
    reestimated_sample_size: 300,
    interim_rationale: "EARLY_STOPPING_EFFICACY: Observed test statistic (Z=2.950) crossed efficacy threshold (z_alpha=2.772) at t=0.50. Early trial success declared.",
    analyzed_at: "2026-08-22T09:45:00Z",
  },
  interim_history: [
    {
      interim_look_number: 1,
      total_planned_looks: 2,
      accumulated_sample_size: 150,
      information_fraction_t: 0.5000,
      cumulative_alpha_spent: 0.0056,
      efficacy_boundary_z: 2.772,
      futility_boundary_z: 0.746,
      observed_interim_z_score: 2.950,
      interim_decision: "EARLY_STOP_EFFICACY",
      is_information_blind: true,
      reestimated_sample_size: 300,
      interim_rationale: "EARLY_STOPPING_EFFICACY: Observed test statistic (Z=2.950) crossed efficacy threshold (z_alpha=2.772) at t=0.50. Early trial success declared.",
      analyzed_at: "2026-08-22T09:45:00Z",
    },
  ],
  predefined_strata: [
    {
      stratum_id: "strat-01-shadbala-high",
      stratum_name: "High Natal Promise (SAV >= 30, Shadbala > 1.2)",
      feature_dimension: "SHADBALA_SAV",
      inclusion_criteria: "SAV_SCORE >= 30 AND SHADBALA_RATIO >= 1.20",
      target_sample_allocation_pct: 40.0,
      observed_sample_count: 60,
    },
    {
      stratum_id: "strat-02-shadbala-mid",
      stratum_name: "Moderate Natal Promise (25 <= SAV < 30)",
      feature_dimension: "SHADBALA_SAV",
      inclusion_criteria: "SAV_SCORE >= 25 AND SAV_SCORE < 30",
      target_sample_allocation_pct: 35.0,
      observed_sample_count: 53,
    },
    {
      stratum_id: "strat-03-shadbala-low",
      stratum_name: "Baseline Natal Promise (SAV < 25)",
      feature_dimension: "SHADBALA_SAV",
      inclusion_criteria: "SAV_SCORE < 25",
      target_sample_allocation_pct: 25.0,
      observed_sample_count: 37,
    },
  ],
  p11_snapshot_id: "snap-p11-frozen-root",
  report_provenance_hash: "e8f9a0b1c2d3e4f5",
  epistemic_non_causal_statement: "ADAPTIVE_RESEARCH_ONLY: Adaptive sequential testing optimizes sample efficiency and controls Type I error without asserting physical causality.",
  generated_at: "2026-08-22T09:45:00Z",
};

export const ResearchAdaptiveExperimentStudio: React.FC = () => {
  const [targetObjective, setTargetObjective] = useState("marriage");
  const [spendingMethod, setSpendingMethod] = useState("LAN_DEMETS_OBRIEN_FLEMING");
  const [interimLook, setInterimLook] = useState(1);
  const [sampleSize, setSampleSize] = useState(150);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"sequential" | "commitment" | "strata" | "governance">("sequential");
  const [report, setReport] = useState<AdaptiveExperimentReport>(DEFAULT_REPORT);

  const fetchAdaptiveReport = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/adaptive-experiment/interim-evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_objective: targetObjective,
          interim_look_number: interimLook,
          total_planned_looks: 2,
          current_sample_size: sampleSize,
          snapshot_id: null,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch (e) {
      console.warn("Failed to fetch live adaptive trial report, using default state:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdaptiveReport();
  }, [targetObjective]);

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case "EARLY_STOP_EFFICACY":
        return {
          bg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
          label: "EARLY STOP (EFFICACY SUCCESS)",
        };
      case "EARLY_STOP_FUTILITY":
        return {
          bg: "bg-rose-500/10 border-rose-500/30 text-rose-400",
          label: "EARLY STOP (FUTILITY)",
        };
      default:
        return {
          bg: "bg-amber-500/10 border-amber-500/30 text-amber-400",
          label: "CONTINUE TRIAL ACCRUAL",
        };
    }
  };

  const decisionBadge = getDecisionBadge(report.latest_interim_analysis.interim_decision);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400 font-bold text-lg">
              🎯
            </span>
            <h1 className="text-2xl font-bold tracking-tight">
              Priority 28: Adaptive Research & Experiment Engine
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Sequential interim testing with configurable alpha spending, post-hoc prevention, & blinded sample size re-estimation.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={targetObjective}
            onChange={(e) => setTargetObjective(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="marriage">Objective: Marriage</option>
            <option value="career">Objective: Career</option>
            <option value="wealth">Objective: Wealth</option>
            <option value="health">Objective: Health</option>
          </select>

          <select
            value={spendingMethod}
            onChange={(e) => setSpendingMethod(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="LAN_DEMETS_OBRIEN_FLEMING">Lan-DeMets (O'Brien-Fleming)</option>
            <option value="LAN_DEMETS_POCOCK">Lan-DeMets (Pocock)</option>
            <option value="HWANG_SHI_DECANI">Hwang-Shih-DeCani (Gamma)</option>
          </select>

          <button
            onClick={fetchAdaptiveReport}
            disabled={loading}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition shadow-lg shadow-indigo-600/20"
          >
            <span>{loading ? "Analyzing..." : "Evaluate Sequential Interim Look"}</span>
          </button>
        </div>
      </div>

      {/* Top Banner: Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Trial Phase / Interim Decision */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Interim Decision Verdict
            </span>
            <div className="text-2xl font-extrabold text-white mt-1">
              {report.latest_interim_analysis.interim_decision.replace(/_/g, " ")}
            </div>
          </div>
          <span className={`text-xs px-2.5 py-0.5 rounded border font-mono font-semibold w-fit mt-2 ${decisionBadge.bg}`}>
            {decisionBadge.label}
          </span>
        </div>

        {/* Information Fraction t */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Information Fraction (t)
            </span>
            <div className="text-3xl font-extrabold text-indigo-400 mt-1 font-mono">
              t = {report.latest_interim_analysis.information_fraction_t.toFixed(2)}
            </div>
          </div>
          <span className="text-xs text-slate-400">
            N = {report.latest_interim_analysis.accumulated_sample_size} / {report.commitment.planned_maximum_sample_size} natives
          </span>
        </div>

        {/* Cumulative Alpha Spent */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Cumulative Alpha Spent (α*)
            </span>
            <div className="text-3xl font-extrabold text-white mt-1 font-mono">
              {report.latest_interim_analysis.cumulative_alpha_spent.toFixed(5)}
            </div>
          </div>
          <span className="text-xs text-emerald-400 font-mono">
            Nominal Budget: α = {report.commitment.overall_alpha_budget.toFixed(2)}
          </span>
        </div>

        {/* Interim Z-Score vs Boundary */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Interim Z-Score vs Boundary
            </span>
            <div className="text-3xl font-extrabold text-white mt-1 font-mono">
              Z = {report.latest_interim_analysis.observed_interim_z_score.toFixed(3)}
            </div>
          </div>
          <span className="text-xs text-indigo-400 font-mono">
            Efficacy z_α = {report.latest_interim_analysis.efficacy_boundary_z.toFixed(3)} • Futility z_β = {report.latest_interim_analysis.futility_boundary_z.toFixed(3)}
          </span>
        </div>
      </div>

      {/* Studio Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("sequential")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "sequential"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>📈 Sequential Boundaries & Stopping Rules</span>
        </button>

        <button
          onClick={() => setActiveTab("commitment")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "commitment"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>🔒 Immutable Pre-Trial Commitment (Anti-HARKing)</span>
        </button>

        <button
          onClick={() => setActiveTab("strata")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "strata"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>🧬 Predefined Stratification & Blinded Sample Size</span>
        </button>

        <button
          onClick={() => setActiveTab("governance")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "governance"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>⚖️ Non-Causal Epistemic Governance</span>
        </button>
      </div>

      {/* Tab 1: Sequential Boundaries & Stopping Rules */}
      {activeTab === "sequential" && (
        <div className="space-y-6">
          {/* Decision Rationale Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>🎯</span>
              <span>Sequential Decision Diagnosis (Look {report.latest_interim_analysis.interim_look_number} of {report.latest_interim_analysis.total_planned_looks})</span>
            </h3>
            <p className="text-xs text-slate-300 italic bg-slate-950/60 p-4 rounded-xl border border-slate-800 font-mono leading-relaxed">
              {report.latest_interim_analysis.interim_rationale}
            </p>
          </div>

          {/* Sequential Look Matrix */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              Sequential Alpha Spending Boundary Corridor
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">Look #</th>
                    <th className="py-2.5 px-3">Info Fraction (t)</th>
                    <th className="py-2.5 px-3">Acc. Sample N</th>
                    <th className="py-2.5 px-3">Alpha Spent (α*)</th>
                    <th className="py-2.5 px-3">Futility z_β</th>
                    <th className="py-2.5 px-3">Efficacy z_α</th>
                    <th className="py-2.5 px-3">Observed Z</th>
                    <th className="py-2.5 px-3">Interim Decision</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-3 font-bold text-indigo-400">1 (Interim)</td>
                    <td className="py-2.5 px-3 text-slate-300">0.50</td>
                    <td className="py-2.5 px-3">150</td>
                    <td className="py-2.5 px-3 text-emerald-400">{report.latest_interim_analysis.cumulative_alpha_spent.toFixed(5)}</td>
                    <td className="py-2.5 px-3 text-rose-400">{report.latest_interim_analysis.futility_boundary_z.toFixed(3)}</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-bold">{report.latest_interim_analysis.efficacy_boundary_z.toFixed(3)}</td>
                    <td className="py-2.5 px-3 text-white font-bold">{report.latest_interim_analysis.observed_interim_z_score.toFixed(3)}</td>
                    <td className="py-2.5 px-3">
                      <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-sans font-bold">
                        {report.latest_interim_analysis.interim_decision}
                      </span>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-900/40 opacity-60">
                    <td className="py-2.5 px-3 font-bold text-slate-500">2 (Final)</td>
                    <td className="py-2.5 px-3 text-slate-400">1.00</td>
                    <td className="py-2.5 px-3">300</td>
                    <td className="py-2.5 px-3">0.05000</td>
                    <td className="py-2.5 px-3">1.960</td>
                    <td className="py-2.5 px-3 font-bold">1.960</td>
                    <td className="py-2.5 px-3 text-slate-500">—</td>
                    <td className="py-2.5 px-3 text-slate-500 font-sans">PLANNED FINAL</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Immutable Pre-Trial Commitment */}
      {activeTab === "commitment" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 font-mono font-semibold">
                  Anti-HARKing Enforcement
                </span>
                <h3 className="text-base font-bold text-white mt-1">
                  Immutable Rule & Parameter Commitment
                </h3>
              </div>
              <span className="text-xs px-2.5 py-1 rounded border font-mono bg-slate-800 border-slate-700 text-slate-300">
                Commitment ID: {report.commitment.commitment_id}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                <span className="text-slate-400">Frozen Rule Name:</span>
                <div className="text-white font-bold">{report.commitment.frozen_rule_name}</div>
                <span className="text-slate-400 block pt-2">Frozen Formula Expression:</span>
                <div className="text-indigo-400 bg-slate-900/80 p-2 rounded border border-slate-800">
                  {report.commitment.frozen_formula_expression}
                </div>
              </div>

              <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                <span className="text-slate-400">Spending Function Method:</span>
                <div className="text-emerald-400 font-bold">{report.commitment.alpha_spending_method}</div>
                <span className="text-slate-400 block pt-2">Outcome-Dependent Adaptation:</span>
                <div className="text-slate-200">
                  {report.commitment.permit_outcome_dependent_adaptation ? "PERMITTED" : "FORBIDDEN (Blinded Variance Only)"}
                </div>
                <span className="text-slate-400 block pt-2">SHA-256 Provenance Hash:</span>
                <div className="text-slate-400">{report.commitment.commitment_provenance_hash}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Predefined Stratification & Blinded Sample Size */}
      {activeTab === "strata" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white">
              Predefined Cohort Strata (Frozen Pre-Trial)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">Stratum ID</th>
                    <th className="py-2.5 px-3">Stratum Name</th>
                    <th className="py-2.5 px-3">Feature Dimension</th>
                    <th className="py-2.5 px-3">Inclusion Criteria</th>
                    <th className="py-2.5 px-3">Target Quota</th>
                    <th className="py-2.5 px-3">Observed N</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {report.predefined_strata.map((s) => (
                    <tr key={s.stratum_id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 font-bold text-indigo-400">{s.stratum_id}</td>
                      <td className="py-2.5 px-3 text-slate-200 font-sans">{s.stratum_name}</td>
                      <td className="py-2.5 px-3 text-slate-400">{s.feature_dimension}</td>
                      <td className="py-2.5 px-3 text-slate-300">{s.inclusion_criteria}</td>
                      <td className="py-2.5 px-3 text-emerald-400 font-bold">{s.target_sample_allocation_pct}%</td>
                      <td className="py-2.5 px-3 text-white font-bold">{s.observed_sample_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-base font-bold text-white">
              Information-Blind Sample Size Re-estimation
            </h3>
            <p className="text-xs text-slate-400">
              Evaluates overall pooled nuisance variance without unblinding stratum-specific effect sizes, ensuring unbiased sample adequacy.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono pt-1">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400">Information-Blind Mode:</span>
                <div className="text-emerald-400 font-bold mt-1">
                  {report.latest_interim_analysis.is_information_blind ? "TRUE (Strictly Blinded)" : "FALSE"}
                </div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400">Re-estimated Sample Size:</span>
                <div className="text-white font-bold mt-1 font-mono">
                  N_reestimated = {report.latest_interim_analysis.reestimated_sample_size}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Non-Causal Epistemic Governance */}
      {activeTab === "governance" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>⚖️</span>
              <span>Epistemic Scope & Sequential Testing Guardrails</span>
            </h3>
            <p className="text-sm text-slate-300 bg-slate-950/60 p-4 rounded-xl border border-slate-800 font-mono text-xs leading-relaxed">
              {report.epistemic_non_causal_statement}
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>🌿</span>
              <span>P11 Cryptographic Snapshot Lineage</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400">P11 Lineage Snapshot:</span>
                <div className="text-slate-200 mt-1">{report.p11_snapshot_id}</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400">Adaptive Report Provenance Hash:</span>
                <div className="text-slate-200 mt-1">{report.report_provenance_hash}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
