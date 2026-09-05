"use client";

import React, { useState } from "react";
import { ExplainabilityHelpGuide } from "./ExplainabilityHelpGuide";

interface AtomicFactor {
  factor_id: string;
  name: string;
  layer: string;
  raw_value: number;
  calibrated_weight: number;
  contribution_percent: number;
  attribution_type: string;
  direction: string;
  classical_citation: string;
  citation_verified: boolean;
  epistemic_grade: string;
  description: string;
}

interface Counterfactual {
  scenario_id: string;
  perturbed_parameter: string;
  parameter_value: string;
  baseline_score: number;
  simulated_score: number;
  score_delta_percent: number;
  divergence_reason: string;
  recalculation_engine_used: string;
}

interface ExplanationReport {
  explanation_id: string;
  target_objective: string;
  event_window_start: string;
  event_window_end: string;
  composite_confidence_score: number;
  plain_summary: string;
  classical_justification: string;
  empirical_synthesis: string;
  provenance_lineage: string[];
  atomic_factors: AtomicFactor[];
  counterfactuals: Counterfactual[];
  generated_at: string;
}

export function PredictionExplainabilityStudio() {
  const [objective, setObjective] = useState<string>("marriage");
  const [report, setReport] = useState<ExplanationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [showHelp, setShowHelp] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"waterfall" | "classical" | "counterfactuals">("waterfall");
  const [selectedFactor, setSelectedFactor] = useState<AtomicFactor | null>(null);

  // Counterfactual custom simulator state
  const [customParam, setCustomParam] = useState<string>("birth_time_shift_minutes");
  const [customVal, setCustomVal] = useState<string>("-3 min");
  const [customResult, setCustomResult] = useState<Counterfactual | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/explain/prediction", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_objective: objective,
          event_window_start: "2026-04-01",
          event_window_end: "2026-09-30",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setReport(data);
        if (data.atomic_factors && data.atomic_factors.length > 0) {
          setSelectedFactor(data.atomic_factors[0]);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRunCounterfactual = async () => {
    if (!report) return;
    setSimulating(true);
    try {
      const res = await fetch("/api/v1/research/explain/counterfactual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_objective: objective,
          perturbed_parameter: customParam,
          parameter_value: customVal,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setCustomResult(data);
      }
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-6 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Priority 17: Research & Prediction Explainability Engine
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Multi-modal astronomical decomposition, verified classical canonical citations, and genuine engine recalculation counterfactual sensitivity analysis.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHelp(!showHelp)}
              className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition border ${
                showHelp
                  ? "bg-purple-600 text-white border-purple-500 shadow-md shadow-purple-600/30"
                  : "bg-slate-800 text-purple-300 border-purple-500/30 hover:bg-slate-700 hover:text-white"
              }`}
            >
              <span>📖</span>
              <span>{showHelp ? "Close Guide" : "Explainability Guide / Help"}</span>
            </button>
            <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-semibold text-purple-400">
              Priority 17 Certified
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Help Guide Section */}
      {showHelp && (
        <div className="transition duration-300">
          <ExplainabilityHelpGuide />
        </div>
      )}

      {/* Query Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900/40 p-5">
        <div>
          <label className="text-xs font-medium text-slate-400">Target Objective</label>
          <select
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            className="mt-1 block rounded border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none"
          >
            <option value="marriage">Marriage Timing Window (2026-04 to 2026-09)</option>
            <option value="career">Executive Promotion Window (2026-06 to 2026-12)</option>
            <option value="health">Longevity & Health Window (2027-01 to 2027-06)</option>
          </select>
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="rounded-lg bg-purple-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-purple-600/30 transition hover:bg-purple-500 disabled:opacity-50"
        >
          {loading ? "Deconstructing Prediction Lineage..." : "Deconstruct & Explain Prediction"}
        </button>
      </div>

      {report && (
        <div className="space-y-6">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Confidence Score</span>
              <div className="mt-1 text-3xl font-black text-purple-400">
                {(report.composite_confidence_score * 100).toFixed(1)}%
              </div>
              <span className="text-xs text-slate-500">Associational Composite</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Atomic Factors</span>
              <div className="mt-1 text-3xl font-black text-emerald-400">{report.atomic_factors.length}</div>
              <span className="text-xs text-emerald-400 font-medium">100% Normalized Attribution</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Canonical Citations</span>
              <div className="mt-1 text-3xl font-black text-cyan-400">
                {report.atomic_factors.filter((f) => f.citation_verified).length}
              </div>
              <span className="text-xs text-cyan-400 font-medium">Strictly Verified</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Recalculated Scenarios</span>
              <div className="mt-1 text-3xl font-black text-amber-400">{report.counterfactuals.length}</div>
              <span className="text-xs text-slate-500">Engine Rerun Provenance</span>
            </div>
          </div>

          {/* Plain English Summary */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-2">
            <h2 className="text-sm font-semibold text-purple-300 uppercase tracking-wider">
              Plain English Narrative Synthesis
            </h2>
            <p className="text-sm text-slate-200 font-mono bg-slate-950 p-3 rounded-lg border border-slate-800">
              {report.plain_summary}
            </p>
          </div>

          {/* Lineage Provenance Trace */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Traceable P1–P16 Lineage Provenance Chain
            </h2>
            <div className="flex flex-wrap items-center gap-2">
              {report.provenance_lineage.map((p, idx) => (
                <React.Fragment key={idx}>
                  <span className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 border border-slate-700">
                    {p}
                  </span>
                  {idx < report.provenance_lineage.length - 1 && (
                    <span className="text-slate-600">→</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab("waterfall")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "waterfall"
                  ? "border-purple-500 text-purple-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Mathematical Factor Decomposition (Attribution %)
            </button>
            <button
              onClick={() => setActiveTab("classical")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "classical"
                  ? "border-purple-500 text-purple-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Canonical Classical Shloka Provenance
            </button>
            <button
              onClick={() => setActiveTab("counterfactuals")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "counterfactuals"
                  ? "border-purple-500 text-purple-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Counterfactual Sensitivity Analysis (Engine Rerun)
            </button>
          </div>

          {/* Tab 1: Waterfall Breakdown */}
          {activeTab === "waterfall" && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                    Model Factor Attribution Waterfall
                  </h2>
                  <span className="text-xs text-amber-400 font-mono">
                    * Associational Mathematical Attribution
                  </span>
                </div>
                <div className="space-y-3">
                  {report.atomic_factors.map((f) => (
                    <div
                      key={f.factor_id}
                      onClick={() => setSelectedFactor(f)}
                      className={`cursor-pointer rounded-lg border p-3 transition ${
                        selectedFactor?.factor_id === f.factor_id
                          ? "border-purple-500 bg-purple-950/20"
                          : "border-slate-800 bg-slate-900/60 hover:bg-slate-800/40"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-white">{f.name}</span>
                        <span className="font-mono font-bold text-purple-400">
                          {f.contribution_percent.toFixed(1)}% Contribution
                        </span>
                      </div>
                      <div className="mt-2 h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-emerald-400 rounded-full"
                          style={{ width: `${f.contribution_percent}%` }}
                        />
                      </div>
                      <div className="mt-1 flex justify-between text-[11px] text-slate-400 font-mono">
                        <span>Layer: {f.layer}</span>
                        <span>Raw Score: {f.raw_value.toFixed(3)}</span>
                        <span>Weight: {f.calibrated_weight.toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Selected Factor Detail */}
              {selectedFactor && (
                <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                  <h2 className="text-sm font-semibold text-purple-300 uppercase tracking-wider">
                    Factor Context & Provenance
                  </h2>
                  <div className="text-xs font-bold text-white">{selectedFactor.name}</div>
                  <p className="text-xs text-slate-400">{selectedFactor.description}</p>
                  <div className="rounded bg-slate-950 p-2.5 border border-slate-800 text-xs font-mono text-slate-300">
                    <span className="text-slate-500">Citation:</span> {selectedFactor.classical_citation}
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Grade: {selectedFactor.epistemic_grade}</span>
                    <span>Status: {selectedFactor.attribution_type}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Classical Shloka */}
          {activeTab === "classical" && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <h2 className="text-sm font-semibold text-cyan-300 uppercase tracking-wider">
                Canonical Classical Text Citations & Astrological Rules
              </h2>
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-slate-800 bg-slate-900/80 font-semibold text-slate-400 uppercase">
                    <tr>
                      <th className="px-3 py-2">Factor</th>
                      <th className="px-3 py-2">Canonical Text / Verse</th>
                      <th className="px-3 py-2">Verification Status</th>
                      <th className="px-3 py-2">Rule Logic</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/20">
                    {report.atomic_factors.map((f) => (
                      <tr key={f.factor_id} className="hover:bg-slate-800/30">
                        <td className="px-3 py-2 font-medium text-white">{f.name}</td>
                        <td className="px-3 py-2 font-mono text-cyan-300">{f.classical_citation}</td>
                        <td className="px-3 py-2">
                          {f.citation_verified ? (
                            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-400">
                              VERIFIED CANONICAL
                            </span>
                          ) : (
                            <span className="rounded bg-amber-500/20 px-2 py-0.5 text-xs font-semibold text-amber-400">
                              PROVENANCE NOT VERIFIED
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-slate-400">{f.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 3: Counterfactual Analysis */}
          {activeTab === "counterfactuals" && (
            <div className="space-y-6">
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <h2 className="text-sm font-semibold text-amber-300 uppercase tracking-wider">
                  Pre-Computed Engine Recalculation Scenarios
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  {report.counterfactuals.map((cf) => (
                    <div
                      key={cf.scenario_id}
                      className="rounded-lg border border-slate-800 bg-slate-950 p-4 text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between font-mono">
                        <span className="font-semibold text-white">{cf.perturbed_parameter}</span>
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[11px] text-purple-300">
                          {cf.parameter_value}
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between font-mono">
                        <span className="text-slate-400">
                          {(cf.baseline_score * 100).toFixed(1)}% → {(cf.simulated_score * 100).toFixed(1)}%
                        </span>
                        <span className="font-bold text-rose-400">{cf.score_delta_percent.toFixed(1)}% Delta</span>
                      </div>
                      <p className="text-slate-300 text-[11px]">{cf.divergence_reason}</p>
                      <div className="text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-800">
                        Engine: {cf.recalculation_engine_used}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Interactive Simulator */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <h2 className="text-sm font-semibold text-purple-300 uppercase tracking-wider">
                  Interactive Counterfactual Playground (Live Engine Recalculation)
                </h2>
                <div className="flex flex-wrap items-center gap-4">
                  <div>
                    <label className="text-xs text-slate-400">Perturb Parameter</label>
                    <select
                      value={customParam}
                      onChange={(e) => setCustomParam(e.target.value)}
                      className="mt-1 block rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-white"
                    >
                      <option value="birth_time_shift_minutes">Birth Time Shift (Minutes)</option>
                      <option value="dasha_lord_combustion">Dasha Lord Combustion</option>
                      <option value="gochara_vedha_active">Transit Gochara Vedha</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Perturbation Value</label>
                    <input
                      type="text"
                      value={customVal}
                      onChange={(e) => setCustomVal(e.target.value)}
                      className="mt-1 block rounded border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-white"
                    />
                  </div>
                  <button
                    onClick={handleRunCounterfactual}
                    disabled={simulating}
                    className="mt-4 rounded bg-purple-600 px-4 py-2 text-xs font-semibold text-white hover:bg-purple-500 disabled:opacity-50"
                  >
                    {simulating ? "Rerunning Engines..." : "Simulate Perturbation"}
                  </button>
                </div>

                {customResult && (
                  <div className="rounded-lg border border-purple-800/50 bg-purple-950/20 p-4 text-xs font-mono space-y-2">
                    <div className="flex justify-between font-bold text-white">
                      <span>Parameter: {customResult.perturbed_parameter} ({customResult.parameter_value})</span>
                      <span className="text-rose-400">{customResult.score_delta_percent.toFixed(2)}% Delta</span>
                    </div>
                    <div className="text-slate-300">
                      Score: {(customResult.baseline_score * 100).toFixed(1)}% → {(customResult.simulated_score * 100).toFixed(1)}%
                    </div>
                    <div className="text-slate-400">{customResult.divergence_reason}</div>
                    <div className="text-slate-500 text-[11px]">Recalculated by: {customResult.recalculation_engine_used}</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
