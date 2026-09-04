"use client";

import React, { useState } from "react";

interface PreRegistration {
  registration_id: string;
  hypothesis_id: string;
  rule_name: string;
  target_objective: string;
  frozen_formula: string;
  frozen_thresholds: Record<string, number>;
  sha256_registration_hash: string;
  registered_at: string;
  lineage_snapshot_id: string;
  author: string;
}

interface DriftAnalysis {
  psi_drift_score: number;
  is_significant_drift: boolean;
  drift_diagnosis: string;
}

interface ProspectiveReport {
  evaluation_id: string;
  registration_id: string;
  target_objective: string;
  total_prospective_subjects: number;
  positive_outcomes_count: number;
  brier_score: number;
  log_loss: number;
  roc_auc: number;
  pr_auc: number;
  precision: number;
  recall: number;
  statistical_lift: number;
  confidence_interval_95_roc: number[];
  drift_analysis: DriftAnalysis;
  final_lifecycle_status: string;
  epistemic_classification: string;
  evaluated_at: string;
}

export function ProspectiveValidationStudio() {
  const [ruleName, setRuleName] = useState<string>("Prospective 7th Lord Dasha + Jupiter Aspect Rule");
  const [targetObjective, setTargetObjective] = useState<string>("marriage");
  const [formula, setFormula] = useState<string>('DASHA == "7th_Lord" AND TRANSIT_ASPECT("Jupiter", 7) AND SAV_SCORE >= 30');
  const [totalSubjects, setTotalSubjects] = useState<number>(150);
  const [positivePrevalence, setPositivePrevalence] = useState<number>(0.52);

  const [registration, setRegistration] = useState<PreRegistration | null>(null);
  const [report, setReport] = useState<ProspectiveReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"metrics" | "drift" | "preregistration">("metrics");

  const handlePreRegisterAndEvaluate = async () => {
    setLoading(true);
    try {
      // 1. Pre-register
      const regRes = await fetch("/api/v1/research/prospective/pre-register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hypothesis_id: "hypo-19-top",
          rule_name: ruleName,
          target_objective: targetObjective,
          formula_expression: formula,
          thresholds: { min_lift: 1.35, min_sav: 30.0 },
          author: "PrincipalAstrologicalScientist",
        }),
      });

      if (regRes.ok) {
        const regData: PreRegistration = await regRes.json();
        setRegistration(regData);

        // 2. Blind Forward Evaluation
        const evalRes = await fetch("/api/v1/research/prospective/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            registration_id: regData.registration_id,
            total_subjects: totalSubjects,
            positive_prevalence: positivePrevalence,
          }),
        });

        if (evalRes.ok) {
          const evalData: ProspectiveReport = await evalRes.json();
          setReport(evalData);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-6 backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Priority 20: Prospective Research Validation & Rule Lifecycle Engine
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Immutable pre-registration, forward-only blind prediction tracking, and empirical lifecycle promotion.
            </p>
          </div>
          <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs font-semibold text-sky-400">
            Priority 20 Active
          </span>
        </div>
      </div>

      {/* Prospective Console */}
      <div className="grid grid-cols-1 gap-4 rounded-xl border border-slate-800 bg-slate-900/40 p-5 sm:grid-cols-4">
        <div>
          <label className="text-xs font-medium text-slate-400">Rule Name</label>
          <input
            type="text"
            value={ruleName}
            onChange={(e) => setRuleName(e.target.value)}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Prospective Sample (N)</label>
          <input
            type="number"
            value={totalSubjects}
            onChange={(e) => setTotalSubjects(Number(e.target.value))}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Observed Prevalence</label>
          <input
            type="number"
            step="0.01"
            value={positivePrevalence}
            onChange={(e) => setPositivePrevalence(Number(e.target.value))}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={handlePreRegisterAndEvaluate}
            disabled={loading}
            className="w-full rounded-lg bg-sky-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-sky-600/30 transition hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? "Pre-Registering & Evaluating..." : "Run Prospective Validation"}
          </button>
        </div>
      </div>

      {report && (
        <div className="space-y-6">
          {/* Top Performance Metric Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Prospective ROC-AUC</span>
              <div className="mt-1 text-3xl font-black text-sky-400">{report.roc_auc.toFixed(3)}</div>
              <span className="text-xs text-slate-500">
                95% CI: [{report.confidence_interval_95_roc[0].toFixed(3)}, {report.confidence_interval_95_roc[1].toFixed(3)}]
              </span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Brier & Log Loss</span>
              <div className="mt-1 text-3xl font-black text-emerald-400">{report.brier_score.toFixed(3)}</div>
              <span className="text-xs text-emerald-400 font-medium">Log Loss: {report.log_loss.toFixed(3)}</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Empirical Lift</span>
              <div className="mt-1 text-3xl font-black text-purple-400">{report.statistical_lift.toFixed(2)}x</div>
              <span className="text-xs text-slate-500">Precision: {(report.precision * 100).toFixed(1)}%</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Lifecycle Classification</span>
              <div className="mt-2 text-sm font-black text-emerald-400 uppercase tracking-wider">
                {report.final_lifecycle_status}
              </div>
              <span className="text-[11px] text-slate-400 truncate block mt-1">
                {report.drift_analysis.drift_diagnosis}
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab("metrics")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "metrics"
                  ? "border-sky-500 text-sky-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Prospective Validation Metrics
            </button>
            <button
              onClick={() => setActiveTab("drift")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "drift"
                  ? "border-sky-500 text-sky-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Temporal & Cohort Drift Analysis (PSI)
            </button>
            <button
              onClick={() => setActiveTab("preregistration")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "preregistration"
                  ? "border-sky-500 text-sky-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Immutable Pre-Registration Ledger
            </button>
          </div>

          {/* Tab 1: Metrics */}
          {activeTab === "metrics" && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4 font-mono text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                <span className="text-sm font-bold text-white uppercase">Evaluation ID: {report.evaluation_id}</span>
                <span className="rounded bg-emerald-500/20 px-2.5 py-1 text-emerald-400 font-bold">
                  N = {report.total_prospective_subjects} Natives
                </span>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="p-3 bg-slate-950 rounded border border-slate-800">
                  <div className="text-slate-400">PR-AUC</div>
                  <div className="text-lg font-bold text-cyan-400">{report.pr_auc.toFixed(3)}</div>
                </div>
                <div className="p-3 bg-slate-950 rounded border border-slate-800">
                  <div className="text-slate-400">Precision (PPV)</div>
                  <div className="text-lg font-bold text-emerald-400">{(report.precision * 100).toFixed(1)}%</div>
                </div>
                <div className="p-3 bg-slate-950 rounded border border-slate-800">
                  <div className="text-slate-400">Recall (Sensitivity)</div>
                  <div className="text-lg font-bold text-purple-400">{(report.recall * 100).toFixed(1)}%</div>
                </div>
              </div>
              <div className="p-3 bg-slate-950 rounded border border-slate-800">
                <span className="text-slate-400 block mb-1 font-bold">Epistemic Status:</span>
                <span className="text-slate-200">{report.epistemic_classification}</span>
              </div>
            </div>
          )}

          {/* Tab 2: Drift */}
          {activeTab === "drift" && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <h2 className="text-sm font-semibold text-purple-300 uppercase tracking-wider">
                Population & Temporal Stability Index (PSI) Drift Diagnosis
              </h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 font-mono text-xs">
                <div className="p-4 bg-slate-950 rounded border border-slate-800 space-y-2">
                  <div className="text-slate-400">PSI Stability Metric</div>
                  <div className="text-2xl font-bold text-emerald-400">
                    {report.drift_analysis.psi_drift_score.toFixed(4)}
                  </div>
                  <p className="text-[11px] text-slate-500">
                    PSI &lt; 0.10: Stable Distribution | PSI 0.10–0.20: Moderate Drift | PSI &ge; 0.20: Significant Drift
                  </p>
                </div>
                <div className="p-4 bg-slate-950 rounded border border-slate-800 space-y-2">
                  <div className="text-slate-400">Drift Verification Status</div>
                  <div className="text-2xl font-bold text-sky-400">
                    {report.drift_analysis.drift_diagnosis}
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Significant Drift: {report.drift_analysis.is_significant_drift ? "YES (Refutation Risk)" : "NO (Cohort Stable)"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Pre-Registration */}
          {activeTab === "preregistration" && registration && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4 font-mono text-xs">
              <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                <span className="text-sm font-bold text-white">Pre-Registration: {registration.registration_id}</span>
                <span className="rounded bg-sky-500/20 px-2.5 py-1 text-sky-400 font-bold">
                  Lineage Snapshot: {registration.lineage_snapshot_id}
                </span>
              </div>
              <div className="space-y-2 bg-slate-950 p-4 rounded border border-slate-800">
                <div>
                  <span className="text-slate-500">Frozen Rule: </span>
                  <span className="text-white font-bold">{registration.rule_name}</span>
                </div>
                <div>
                  <span className="text-slate-500">Frozen Formula: </span>
                  <span className="text-cyan-400">{registration.frozen_formula}</span>
                </div>
                <div>
                  <span className="text-slate-500">SHA-256 Hash: </span>
                  <span className="text-amber-400 truncate block">{registration.sha256_registration_hash}</span>
                </div>
                <div>
                  <span className="text-slate-500">Author: </span>
                  <span className="text-slate-300">{registration.author}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
