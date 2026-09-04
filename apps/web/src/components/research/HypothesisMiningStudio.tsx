"use client";

import React, { useState } from "react";

interface PatternPrimitive {
  dimension: string;
  operator: string;
  value: string;
  description: string;
}

interface ReplicationRecord {
  holdout_dataset_id: string;
  holdout_sample_size: number;
  holdout_support_percent: number;
  holdout_confidence_percent: number;
  holdout_statistical_lift: number;
  holdout_fdr_q_value: number;
  is_replication_confirmed: boolean;
  replicated_at: string;
}

interface DiscoveredHypothesis {
  hypothesis_id: string;
  name: string;
  target_objective: string;
  pattern_primitives: PatternPrimitive[];
  discovery_dataset_id: string;
  discovery_sample_size: number;
  discovery_support_percent: number;
  discovery_confidence_percent: number;
  discovery_statistical_lift: number;
  discovery_raw_p_value: number;
  discovery_fdr_q_value: number;
  status: string;
  replication_records: ReplicationRecord[];
  lineage_snapshot_id: string;
  discovered_at: string;
  classical_provenance_note: string;
}

interface MiningReport {
  mining_run_id: string;
  discovery_dataset_id: string;
  holdout_dataset_id: string;
  target_objective: string;
  total_combinations_evaluated: number;
  candidate_hypotheses_count: number;
  replicated_validated_count: number;
  rejected_fdr_count: number;
  top_hypotheses: DiscoveredHypothesis[];
  execution_time_seconds: number;
  mined_at: string;
}

export function HypothesisMiningStudio() {
  const [discoveryDataset, setDiscoveryDataset] = useState<string>("ds-marriage-28");
  const [holdoutDataset, setHoldoutDataset] = useState<string>("ds-marriage-100");
  const [objective, setObjective] = useState<string>("marriage");
  const [minSupport, setMinSupport] = useState<number>(15.0);
  const [minLift, setMinLift] = useState<number>(1.35);
  const [report, setReport] = useState<MiningReport | null>(null);
  const [selectedHypo, setSelectedHypo] = useState<DiscoveredHypothesis | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"leaderboard" | "primitives" | "replication">("leaderboard");

  const handleRunMining = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/mining/mine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          discovery_dataset_id: discoveryDataset,
          holdout_dataset_id: holdoutDataset,
          target_objective: objective,
          min_support_percent: minSupport,
          min_statistical_lift: minLift,
          max_fdr_q_value: 0.05,
        }),
      });

      if (res.ok) {
        const data: MiningReport = await res.json();
        setReport(data);
        if (data.top_hypotheses && data.top_hypotheses.length > 0) {
          setSelectedHypo(data.top_hypotheses[0]);
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
              Priority 19: Research Discovery & Hypothesis Mining Engine
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Automated astrological pattern discovery, Benjamini-Hochberg FDR control, and multi-criteria independent holdout cohort replication.
            </p>
          </div>
          <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-400">
            Priority 19 Active
          </span>
        </div>
      </div>

      {/* Mining Configuration Console */}
      <div className="grid grid-cols-1 gap-4 rounded-xl border border-slate-800 bg-slate-900/40 p-5 sm:grid-cols-5">
        <div>
          <label className="text-xs font-medium text-slate-400">Discovery Cohort</label>
          <select
            value={discoveryDataset}
            onChange={(e) => setDiscoveryDataset(e.target.value)}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          >
            <option value="ds-marriage-28">Marriage Discovery (N=250)</option>
            <option value="ds-career-founders">Career Founders (N=180)</option>
            <option value="ds-longevity-80">Longevity Cohort (N=80)</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Independent Holdout</label>
          <select
            value={holdoutDataset}
            onChange={(e) => setHoldoutDataset(e.target.value)}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          >
            <option value="ds-marriage-100">Marriage Holdout (N=100)</option>
            <option value="ds-career-validation">Career Holdout (N=75)</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Min Support (%)</label>
          <input
            type="number"
            value={minSupport}
            onChange={(e) => setMinSupport(Number(e.target.value))}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Min Lift Threshold</label>
          <input
            type="number"
            step="0.05"
            value={minLift}
            onChange={(e) => setMinLift(Number(e.target.value))}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={handleRunMining}
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "Mining Patterns..." : "Run Discovery Engine"}
          </button>
        </div>
      </div>

      {report && (
        <div className="space-y-6">
          {/* Metric Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Combinations Evaluated</span>
              <div className="mt-1 text-3xl font-black text-indigo-400">
                {report.total_combinations_evaluated}
              </div>
              <span className="text-xs text-slate-500">{report.execution_time_seconds}s Processing</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Candidate Hypotheses</span>
              <div className="mt-1 text-3xl font-black text-cyan-400">
                {report.candidate_hypotheses_count}
              </div>
              <span className="text-xs text-cyan-400 font-medium">Support ≥ {minSupport}%</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Replicated & Validated</span>
              <div className="mt-1 text-3xl font-black text-emerald-400">
                {report.replicated_validated_count}
              </div>
              <span className="text-xs text-emerald-400 font-medium">Holdout FDR q &lt; 0.05</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">FDR Rejected</span>
              <div className="mt-1 text-3xl font-black text-rose-400">{report.rejected_fdr_count}</div>
              <span className="text-xs text-slate-500">False Discovery Filter</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab("leaderboard")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "leaderboard"
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Discovered Hypotheses Leaderboard ({report.top_hypotheses.length})
            </button>
            <button
              onClick={() => setActiveTab("primitives")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "primitives"
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Pattern Primitives & Astrological Decomposition
            </button>
            <button
              onClick={() => setActiveTab("replication")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "replication"
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Independent Holdout Replication Matrix
            </button>
          </div>

          {/* Tab 1: Leaderboard */}
          {activeTab === "leaderboard" && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                Mined Astrological Hypotheses Ranked by Statistical Lift
              </h2>
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-slate-800 bg-slate-900/80 font-semibold text-slate-400 uppercase">
                    <tr>
                      <th className="px-3 py-2">Hypothesis Name</th>
                      <th className="px-3 py-2">Support %</th>
                      <th className="px-3 py-2">Confidence %</th>
                      <th className="px-3 py-2">Statistical Lift</th>
                      <th className="px-3 py-2">FDR q-value</th>
                      <th className="px-3 py-2">Epistemic Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/20 font-mono">
                    {report.top_hypotheses.map((h) => (
                      <tr
                        key={h.hypothesis_id}
                        onClick={() => setSelectedHypo(h)}
                        className={`cursor-pointer hover:bg-slate-800/30 ${
                          selectedHypo?.hypothesis_id === h.hypothesis_id ? "bg-indigo-950/30" : ""
                        }`}
                      >
                        <td className="px-3 py-2 font-bold text-white">{h.name}</td>
                        <td className="px-3 py-2 text-slate-300">{h.discovery_support_percent}%</td>
                        <td className="px-3 py-2 text-cyan-300">{h.discovery_confidence_percent}%</td>
                        <td className="px-3 py-2 text-emerald-400 font-bold">{h.discovery_statistical_lift.toFixed(2)}x</td>
                        <td className="px-3 py-2 text-amber-400">q = {h.discovery_fdr_q_value}</td>
                        <td className="px-3 py-2">
                          {h.status === "REPLICATED_VALIDATED" ? (
                            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[11px] font-bold text-emerald-400">
                              REPLICATED VALIDATED
                            </span>
                          ) : h.status === "CANDIDATE_DISCOVERY" ? (
                            <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[11px] font-bold text-amber-400">
                              CANDIDATE DISCOVERY
                            </span>
                          ) : (
                            <span className="rounded bg-rose-500/20 px-2 py-0.5 text-[11px] font-bold text-rose-400">
                              REJECTED FDR
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 2: Primitives */}
          {activeTab === "primitives" && selectedHypo && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-sm font-semibold text-indigo-300 uppercase tracking-wider">
                  Pattern Primitives for: {selectedHypo.name}
                </h2>
                <span className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 border border-slate-700">
                  Lineage: {selectedHypo.lineage_snapshot_id}
                </span>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {selectedHypo.pattern_primitives.map((p, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-slate-800 bg-slate-950 p-4 text-xs space-y-2"
                  >
                    <div className="flex justify-between font-mono">
                      <span className="font-bold text-indigo-400">{p.dimension}</span>
                      <span className="text-slate-400">{p.operator}</span>
                    </div>
                    <div className="text-white font-bold">{p.value}</div>
                    <p className="text-slate-400 text-[11px]">{p.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 3: Replication */}
          {activeTab === "replication" && selectedHypo && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <h2 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">
                Independent Holdout Replication Records
              </h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {selectedHypo.replication_records.map((r, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-slate-800 bg-slate-950 p-4 text-xs font-mono space-y-2"
                  >
                    <div className="flex justify-between font-bold text-white">
                      <span>Holdout Dataset: {r.holdout_dataset_id}</span>
                      <span className={r.is_replication_confirmed ? "text-emerald-400" : "text-rose-400"}>
                        {r.is_replication_confirmed ? "CONFIRMED REPLICATION" : "REPLICATION FAILED"}
                      </span>
                    </div>
                    <div className="text-slate-400">Sample Size: N = {r.holdout_sample_size}</div>
                    <div className="flex justify-between text-slate-300">
                      <span>Holdout Lift: {r.holdout_statistical_lift.toFixed(2)}x</span>
                      <span>Holdout FDR q: {r.holdout_fdr_q_value}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Support: {r.holdout_support_percent}%</span>
                      <span>Confidence: {r.holdout_confidence_percent}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
