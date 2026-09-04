"use client";

import { useEffect, useState } from "react";
import {
  fetchPredictions,
  fetchOutcomes,
  runBacktest,
  fetchTechniqueSummaries,
  fetchPredictionAudit,
  evaluateMatch,
  type PredictionItem,
  type OutcomeItem,
  type BacktestRun,
  type TechniqueSummary,
  type PredictionAuditTrail,
  type MatchResult,
  type TemporalSplitType,
} from "@/lib/predictionValidation";

export function PredictionValidationWorkbench() {
  const [activeTab, setActiveTab] = useState<"overview" | "ledger" | "inspector" | "backtest" | "techniques" | "temporal">("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [predictions, setPredictions] = useState<PredictionItem[]>([]);
  const [outcomes, setOutcomes] = useState<OutcomeItem[]>([]);
  const [backtestRun, setBacktestRun] = useState<BacktestRun | null>(null);
  const [techniqueSummaries, setTechniqueSummaries] = useState<TechniqueSummary[]>([]);
  const [selectedPredictionId, setSelectedPredictionId] = useState<string>("pred_raman_1936");
  const [auditTrail, setAuditTrail] = useState<PredictionAuditTrail | null>(null);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);

  // Backtest controls
  const [datasetName, setDatasetName] = useState<string>("Canonical Research Cohort");
  const [techniqueFilter, setTechniqueFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [temporalSplit, setTemporalSplit] = useState<TemporalSplitType>("VALIDATION");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [preds, outs, bkt, techs] = await Promise.all([
        fetchPredictions(),
        fetchOutcomes(),
        runBacktest({ dataset_name: datasetName, temporal_split: temporalSplit }),
        fetchTechniqueSummaries(),
      ]);
      setPredictions(preds);
      setOutcomes(outs);
      setBacktestRun(bkt);
      setTechniqueSummaries(techs);

      if (preds.length > 0) {
        const audit = await fetchPredictionAudit(preds[0].prediction_id);
        setAuditTrail(audit);
        setSelectedPredictionId(preds[0].prediction_id);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load validation workbench data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectPrediction = async (pid: string) => {
    try {
      setSelectedPredictionId(pid);
      const audit = await fetchPredictionAudit(pid);
      setAuditTrail(audit);
      const match = await evaluateMatch(pid);
      setMatchResult(match);
      setActiveTab("inspector");
    } catch (err: any) {
      setError(err?.message || "Failed to inspect prediction");
    }
  };

  const handleRunBacktest = async () => {
    try {
      setLoading(true);
      const bkt = await runBacktest({
        dataset_name: datasetName,
        technique_filter: techniqueFilter || undefined,
        category_filter: categoryFilter || undefined,
        temporal_split: temporalSplit,
      });
      setBacktestRun(bkt);
    } catch (err: any) {
      setError(err?.message || "Failed to execute backtest");
    } finally {
      setLoading(false);
    }
  };

  if (loading && predictions.length === 0) {
    return (
      <div className="p-8 text-center" data-testid="workbench-loading">
        <div className="inline-block animate-spin h-8 w-8 border-4 border-indigo-500 border-t-transparent rounded-full mb-3" />
        <p className="text-sm text-neutral-400">Loading Prediction Validation Workbench...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6" data-testid="prediction-validation-workbench">
      {/* Top Banner */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-950 text-indigo-600 border border-indigo-800">
                Module 22 · Priority 7
              </span>
              <span className="text-xs text-neutral-400 font-mono">Deterministic Ground-Truth Laboratory</span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Prediction Validation & Empirical Outcome Backtesting Workbench
            </h1>
            <p className="text-sm text-neutral-400 mt-1 max-w-3xl">
              Freeze prediction evidence snapshots with immutable SHA-256 hashes, compare against ground-truth life events,
              and calculate statistically defensible confusion matrices, Wilson score confidence intervals, and temporal leakage checks.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              className="px-3.5 py-2 text-xs font-medium bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-lg border border-neutral-700 transition"
              data-testid="refresh-btn"
            >
              ↻ Refresh Workbench
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-950/60 border border-red-800 text-red-300 text-xs rounded-lg">
            {error}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-2 mt-6 border-b border-neutral-800 pb-2">
          {[
            { id: "overview", label: "A. Overview" },
            { id: "ledger", label: "B. Prediction Ledger" },
            { id: "inspector", label: "C. Prediction Inspector" },
            { id: "backtest", label: "D. Backtest Workspace" },
            { id: "techniques", label: "E. Technique Comparison" },
            { id: "temporal", label: "F. Temporal Validation" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-1.5 text-xs font-semibold rounded-md transition ${
                activeTab === tab.id
                  ? "bg-indigo-600 text-white shadow"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
              }`}
              data-testid={`tab-${tab.id}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* SECTION A: OVERVIEW */}
      {activeTab === "overview" && backtestRun && (
        <div className="space-y-6" data-testid="section-overview">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
              <div className="text-xs text-neutral-400 font-medium">Total Predictions</div>
              <div className="text-2xl font-bold text-white mt-1" data-testid="stat-total-preds">
                {backtestRun.total_predictions}
              </div>
            </div>
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
              <div className="text-xs text-neutral-400 font-medium">Resolved</div>
              <div className="text-2xl font-bold text-indigo-600 mt-1">
                {backtestRun.resolved_predictions}
              </div>
            </div>
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
              <div className="text-xs text-neutral-400 font-medium">Matched (Hits)</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1" data-testid="stat-matched-count">
                {backtestRun.matched_count}
              </div>
            </div>
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
              <div className="text-xs text-neutral-400 font-medium">Missed / Contradicted</div>
              <div className="text-2xl font-bold text-rose-400 mt-1">
                {backtestRun.missed_count + backtestRun.contradicted_count}
              </div>
            </div>
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
              <div className="text-xs text-neutral-400 font-medium">Hit Rate</div>
              <div className="text-2xl font-bold text-amber-400 mt-1" data-testid="stat-hit-rate">
                {(backtestRun.hit_rate * 100).toFixed(1)}%
              </div>
            </div>
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4">
              <div className="text-xs text-neutral-400 font-medium">Wilson 95% CI</div>
              <div className="text-sm font-mono text-neutral-300 mt-2">
                [{(backtestRun.confidence_interval_95[0] * 100).toFixed(0)}% – {(backtestRun.confidence_interval_95[1] * 100).toFixed(0)}%]
              </div>
            </div>
          </div>

          {/* Core Principles Alert */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-neutral-200 mb-2">Deterministic Evaluation Invariants</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-neutral-400">
              <div className="p-3 bg-neutral-950/60 rounded-lg border border-neutral-800">
                <span className="font-semibold text-neutral-200 block mb-1">1. Immutable Evidence Snapshots</span>
                Predictions freeze all Dasha, transit, KP CSL, SBC Vedhas, and classical rule evidence into a deterministic SHA-256 hash. No retroactive modification is permitted.
              </div>
              <div className="p-3 bg-neutral-950/60 rounded-lg border border-neutral-800">
                <span className="font-semibold text-neutral-200 block mb-1">2. Zero Subjective AI Scoring</span>
                Verdicts are assigned via explicit logical predicates (Category, Timing Window $\Delta t$, Directional Consistency) rather than opaque AI confidence scores.
              </div>
              <div className="p-3 bg-neutral-950/60 rounded-lg border border-neutral-800">
                <span className="font-semibold text-neutral-200 block mb-1">3. Temporal Leakage Protection</span>
                Evaluates timestamps to ensure no future information from after the observed event date was used during prediction synthesis.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SECTION B: PREDICTION LEDGER */}
      {activeTab === "ledger" && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 space-y-4" data-testid="section-ledger">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-white">Frozen Prediction Snapshot Ledger</h2>
            <span className="text-xs text-neutral-400 font-mono">{predictions.length} Total Snapshots</span>
          </div>

          <div className="overflow-x-auto border border-neutral-800 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-neutral-950 text-neutral-400 uppercase font-medium border-b border-neutral-800">
                <tr>
                  <th className="p-3">ID / Native</th>
                  <th className="p-3">Technique</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Predicted Event</th>
                  <th className="p-3">Expected Window</th>
                  <th className="p-3">SHA-256 Hash</th>
                  <th className="p-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {predictions.map((p) => (
                  <tr key={p.prediction_id} className="hover:bg-neutral-800/50 transition">
                    <td className="p-3">
                      <div className="font-semibold text-white">{p.subject_name}</div>
                      <div className="text-[11px] text-neutral-400 font-mono">{p.prediction_id}</div>
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 font-mono text-[11px] border border-indigo-800/50">
                        {p.technique}
                      </span>
                    </td>
                    <td className="p-3 capitalize text-neutral-300">{p.category}</td>
                    <td className="p-3 text-neutral-300 max-w-xs truncate">{p.predicted_event}</td>
                    <td className="p-3 text-neutral-400 font-mono">
                      {p.expected_date_start.slice(0, 10)} → {p.expected_date_end.slice(0, 10)}
                    </td>
                    <td className="p-3 font-mono text-[11px] text-neutral-400">
                      <span className="px-1.5 py-0.5 rounded bg-neutral-950 border border-neutral-800" title={p.evidence_hash}>
                        {p.evidence_hash.slice(0, 12)}...
                      </span>
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => handleSelectPrediction(p.prediction_id)}
                        className="px-2.5 py-1 text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded transition"
                        data-testid={`inspect-btn-${p.prediction_id}`}
                      >
                        Inspect Audit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SECTION C: PREDICTION INSPECTOR */}
      {activeTab === "inspector" && auditTrail && (
        <div className="space-y-6" data-testid="section-inspector">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-neutral-800 pb-4 gap-2">
              <div>
                <span className="text-xs text-indigo-600 font-mono uppercase tracking-wider">
                  Audit Provenance Trail · {auditTrail.prediction.technique}
                </span>
                <h2 className="text-xl font-bold text-white mt-1">
                  {auditTrail.prediction.subject_name} — {auditTrail.prediction.predicted_event}
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-neutral-400 font-mono">Evidence Hash:</span>
                <span className="px-2.5 py-1 rounded bg-neutral-950 font-mono text-xs text-emerald-400 border border-neutral-800" data-testid="inspector-hash">
                  {auditTrail.prediction.evidence_hash}
                </span>
              </div>
            </div>

            {/* Verdict Box */}
            <div className="p-4 rounded-xl border bg-neutral-950/80 border-neutral-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="text-xs text-neutral-400 font-medium">Evaluation Verdict</div>
                <div className="text-xl font-bold mt-1 text-emerald-400" data-testid="inspector-verdict">
                  {auditTrail.verdict_trace.verdict}
                </div>
              </div>
              <div className="text-xs text-neutral-400 font-mono">
                Category Match: <span className="text-emerald-400">{auditTrail.verdict_trace.category_matched ? "YES" : "NO"}</span> ·{" "}
                Direction Match: <span className="text-emerald-400">{auditTrail.verdict_trace.direction_matched ? "YES" : "NO"}</span> ·{" "}
                Temporal Error: <span className="text-neutral-200">{auditTrail.verdict_trace.temporal_error_days ?? "N/A"} days</span>
              </div>
            </div>

            {/* Predicate Trace */}
            <div className="space-y-2">
              <h2 className="text-xs font-semibold uppercase text-neutral-400 tracking-wider">Predicate Decision Trace</h2>
              <div className="p-3 bg-neutral-950 rounded-lg border border-neutral-800 font-mono text-xs space-y-1 text-neutral-300">
                {auditTrail.verdict_trace.predicate_traces.map((trace, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-indigo-600">[{idx + 1}]</span>
                    <span>{trace}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Comparison Grid: Prediction vs Ground Truth Outcome */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Prediction Evidence Snapshot */}
              <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-4 space-y-3">
                <h2 className="text-xs font-semibold uppercase text-indigo-600 tracking-wider">
                  Frozen Evidence Snapshot (Read-Only)
                </h2>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between border-b border-neutral-800 py-1">
                    <span className="text-neutral-400">Expected Direction</span>
                    <span className="font-mono text-neutral-200">{auditTrail.prediction.expected_direction}</span>
                  </div>
                  <div className="flex justify-between border-b border-neutral-800 py-1">
                    <span className="text-neutral-400">Predicted Window</span>
                    <span className="font-mono text-neutral-200">
                      {auditTrail.prediction.expected_date_start.slice(0, 10)} to {auditTrail.prediction.expected_date_end.slice(0, 10)}
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-neutral-800 py-1">
                    <span className="text-neutral-400">Evidence IDs</span>
                    <span className="font-mono text-neutral-300">{auditTrail.evidence_snapshot.evidence_ids.join(", ")}</span>
                  </div>
                  <div className="py-1">
                    <span className="text-neutral-400 block mb-1">Dasha & Transit Evidence</span>
                    <pre className="p-2 bg-neutral-900 rounded border border-neutral-800 text-[11px] font-mono text-neutral-300 overflow-x-auto">
                      {JSON.stringify(auditTrail.evidence_snapshot.dasha, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Ground-Truth Observed Outcome */}
              <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-4 space-y-3">
                <h2 className="text-xs font-semibold uppercase text-emerald-400 tracking-wider">
                  Ground-Truth Observed Outcome
                </h2>
                {auditTrail.outcome ? (
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between border-b border-neutral-800 py-1">
                      <span className="text-neutral-400">Observed Date</span>
                      <span className="font-mono text-emerald-400 font-semibold">{auditTrail.outcome.observed_date?.slice(0, 10)}</span>
                    </div>
                    <div className="flex justify-between border-b border-neutral-800 py-1">
                      <span className="text-neutral-400">Verification Status</span>
                      <span className="font-mono text-neutral-200">{auditTrail.outcome.verification_status}</span>
                    </div>
                    <div className="flex justify-between border-b border-neutral-800 py-1">
                      <span className="text-neutral-400">Source Reference</span>
                      <span className="text-neutral-300">{auditTrail.outcome.source}</span>
                    </div>
                    <div className="py-1">
                      <span className="text-neutral-400 block mb-1">Actual Manifested Event</span>
                      <p className="p-2.5 bg-neutral-900 rounded border border-neutral-800 text-neutral-200">
                        {auditTrail.outcome.actual_outcome}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center text-neutral-400 text-xs">
                    No ground-truth outcome recorded yet for this timeframe.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SECTION D: BACKTEST WORKSPACE */}
      {activeTab === "backtest" && backtestRun && (
        <div className="space-y-6" data-testid="section-backtest">
          {/* Controls */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-white mb-3">Cohort Backtesting Parameters</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-neutral-400 block mb-1">Dataset / Cohort</label>
                <input 
                  type="text"
                  aria-label="Dataset / Cohort"
                  value={datasetName}
                  onChange={(e) => setDatasetName(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-1.5 text-xs text-white"
                />
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-1">Technique Filter</label>
                <select
                  value={techniqueFilter}
                  onChange={(e) => setTechniqueFilter(e.target.value)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-1.5 text-xs text-white"
                >
                  <option value="">All Techniques</option>
                  <option value="KP_CSL">KP Cuspal Sub-Lord</option>
                  <option value="PARASHARI_DASHA_TRANSIT">Parashari Dasha + Transit</option>
                  <option value="SBC_VEDHA">Sarvatobhadra Chakra</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-neutral-400 block mb-1">Temporal Split</label>
                <select
                  value={temporalSplit}
                  onChange={(e) => setTemporalSplit(e.target.value as any)}
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-1.5 text-xs text-white"
                >
                  <option value="RESEARCH_TRAIN">Research / Training Split</option>
                  <option value="VALIDATION">Validation Split</option>
                  <option value="TEST_OUT_OF_SAMPLE">Out-of-Sample Test Split</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleRunBacktest}
                  className="w-full py-1.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-lg transition"
                  data-testid="execute-backtest-btn"
                >
                  ▶ Execute Backtest
                </button>
              </div>
            </div>
          </div>

          {/* Confusion Matrix & Statistical Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Confusion Matrix */}
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-4">
              <h2 className="text-sm font-semibold text-white">Confusion Matrix (Ground Truth vs Prediction)</h2>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-4 bg-neutral-950 rounded-xl border border-emerald-900/50">
                  <div className="text-xs text-emerald-400 font-medium">True Positive (TP)</div>
                  <div className="text-2xl font-bold text-white mt-1" data-testid="cm-tp">
                    {backtestRun.confusion_matrix.true_positive}
                  </div>
                  <div className="text-[10px] text-neutral-400 mt-1">Predicted & Observed</div>
                </div>
                <div className="p-4 bg-neutral-950 rounded-xl border border-rose-900/50">
                  <div className="text-xs text-rose-400 font-medium">False Positive (FP)</div>
                  <div className="text-2xl font-bold text-white mt-1" data-testid="cm-fp">
                    {backtestRun.confusion_matrix.false_positive}
                  </div>
                  <div className="text-[10px] text-neutral-400 mt-1">Predicted but Missed</div>
                </div>
                <div className="p-4 bg-neutral-950 rounded-xl border border-neutral-800">
                  <div className="text-xs text-neutral-400 font-medium">False Negative (FN)</div>
                  <div className="text-2xl font-bold text-white mt-1" data-testid="cm-fn">
                    {backtestRun.confusion_matrix.false_negative}
                  </div>
                  <div className="text-[10px] text-neutral-400 mt-1">Missed Occurrence</div>
                </div>
                <div className="p-4 bg-neutral-950 rounded-xl border border-neutral-800">
                  <div className="text-xs text-neutral-400 font-medium">True Negative (TN)</div>
                  <div className="text-2xl font-bold text-white mt-1" data-testid="cm-tn">
                    {backtestRun.confusion_matrix.true_negative}
                  </div>
                  <div className="text-[10px] text-neutral-400 mt-1">Inconclusive / Neutral</div>
                </div>
              </div>
            </div>

            {/* Quantitative Precision & Recall */}
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-4">
              <h2 className="text-sm font-semibold text-white">Statistical Validation Metrics</h2>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center p-3 bg-neutral-950 rounded-lg border border-neutral-800">
                  <span className="text-neutral-400">Precision (Positive Predictive Value)</span>
                  <span className="font-mono text-white font-semibold text-sm" data-testid="stat-precision">
                    {backtestRun.confusion_matrix.precision !== undefined ? `${(backtestRun.confusion_matrix.precision * 100).toFixed(1)}%` : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-neutral-950 rounded-lg border border-neutral-800">
                  <span className="text-neutral-400">Hit Rate (Resolved Cohort)</span>
                  <span className="font-mono text-emerald-400 font-semibold text-sm">
                    {(backtestRun.hit_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-neutral-950 rounded-lg border border-neutral-800">
                  <span className="text-neutral-400">Wilson 95% Confidence Interval</span>
                  <span className="font-mono text-amber-400 font-semibold text-sm">
                    [{(backtestRun.confidence_interval_95[0] * 100).toFixed(1)}% – {(backtestRun.confidence_interval_95[1] * 100).toFixed(1)}%]
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-neutral-950 rounded-lg border border-neutral-800">
                  <span className="text-neutral-400">Cohort Result SHA-256 Hash</span>
                  <span className="font-mono text-[11px] text-neutral-400" title={backtestRun.result_hash}>
                    {backtestRun.result_hash.slice(0, 16)}...
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SECTION E: TECHNIQUE COMPARISON */}
      {activeTab === "techniques" && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 space-y-4" data-testid="section-techniques">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-white">Cross-Technique Performance Matrix</h2>
            <span className="text-xs text-neutral-400 font-mono">Identical Ground-Truth Cohorts</span>
          </div>

          <div className="overflow-x-auto border border-neutral-800 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-neutral-950 text-neutral-400 uppercase font-medium border-b border-neutral-800">
                <tr>
                  <th className="p-3">Technique</th>
                  <th className="p-3">Total / Resolved</th>
                  <th className="p-3">Hits</th>
                  <th className="p-3">Misses</th>
                  <th className="p-3">Hit Rate</th>
                  <th className="p-3">Precision</th>
                  <th className="p-3">Wilson 95% CI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800">
                {techniqueSummaries.map((t) => (
                  <tr key={t.technique} className="hover:bg-neutral-800/50 transition">
                    <td className="p-3 font-semibold text-white font-mono">{t.technique}</td>
                    <td className="p-3 text-neutral-300 font-mono">
                      {t.total_predictions} / {t.resolved_predictions}
                    </td>
                    <td className="p-3 text-emerald-400 font-mono">{t.matched_count}</td>
                    <td className="p-3 text-rose-400 font-mono">{t.missed_count}</td>
                    <td className="p-3 font-semibold text-amber-400 font-mono">{(t.hit_rate * 100).toFixed(1)}%</td>
                    <td className="p-3 font-mono text-neutral-300">
                      {t.precision !== undefined ? `${(t.precision * 100).toFixed(1)}%` : "N/A"}
                    </td>
                    <td className="p-3 font-mono text-neutral-400 text-[11px]">
                      [{(t.ci_95_low * 100).toFixed(0)}% – {(t.ci_95_high * 100).toFixed(0)}%]
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SECTION F: TEMPORAL VALIDATION & LEAKAGE */}
      {activeTab === "temporal" && backtestRun && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 space-y-6" data-testid="section-temporal">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-white">Temporal Separation & Leakage Audit</h2>
              <p className="text-xs text-neutral-400 mt-1">
                Ensures predictive models are strictly evaluated out-of-sample with no lookahead bias.
              </p>
            </div>
            <span
              className={`px-3 py-1 text-xs font-semibold rounded-full border ${
                backtestRun.temporal_leakage_detected
                  ? "bg-rose-950 text-rose-400 border-rose-800"
                  : "bg-emerald-950 text-emerald-400 border-emerald-800"
              }`}
              data-testid="leakage-badge"
            >
              {backtestRun.temporal_leakage_detected ? "⚠ Temporal Leakage Detected" : "✓ Zero Leakage Verified"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-neutral-950 rounded-xl border border-neutral-800">
              <div className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">Research / Train Period</div>
              <div className="text-sm font-semibold text-white mt-1">Pre-1900 to 1920</div>
              <p className="text-xs text-neutral-400 mt-2">Historical rule calibration and parameter optimization.</p>
            </div>
            <div className="p-4 bg-neutral-950 rounded-xl border border-neutral-800">
              <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Validation Period</div>
              <div className="text-sm font-semibold text-white mt-1">1921 to 1950</div>
              <p className="text-xs text-neutral-400 mt-2">Active backtest evaluation on historical benchmark events.</p>
            </div>
            <div className="p-4 bg-neutral-950 rounded-xl border border-neutral-800">
              <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Out-of-Sample Test Period</div>
              <div className="text-sm font-semibold text-white mt-1">1951 to Present / Prospective</div>
              <p className="text-xs text-neutral-400 mt-2">Strict prospective validation with zero prior knowledge.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
