"use client";

import React, { useState } from "react";

interface WorkerMetric {
  worker_id: string;
  processed_count: number;
  active_chunk_index: number;
  throughput_charts_per_sec: number;
  memory_mb: number;
  cpu_utilization_percent: number;
}

interface BatchReport {
  job_id: string;
  dataset_id: string;
  target_objective: string;
  status: string;
  total_subjects_evaluated: number;
  total_runtime_seconds: number;
  average_throughput_charts_per_sec: number;
  cache_hit_rate_percent: number;
  aggregate_brier_score: number;
  aggregate_log_loss: number;
  aggregate_roc_auc: number;
  aggregate_hit_rate: number;
  checkpoints_saved: number;
  worker_metrics: WorkerMetric[];
  started_at: string;
  completed_at?: string;
}

interface CheckpointItem {
  checkpoint_id: string;
  job_id: string;
  chunk_index: number;
  processed_subjects: number;
  running_brier_sum: number;
  running_log_loss_sum: number;
  running_hits_count: number;
  checkpoint_sha256_hash: string;
  timestamp: string;
}

export function BatchResearchOptimizationStudio() {
  const [datasetId, setDatasetId] = useState<string>("ds-marriage-28");
  const [targetObjective, setTargetObjective] = useState<string>("marriage");
  const [totalSubjects, setTotalSubjects] = useState<number>(1000);
  const [chunkSize, setChunkSize] = useState<number>(250);
  const [workersCount, setWorkersCount] = useState<number>(4);
  const [report, setReport] = useState<BatchReport | null>(null);
  const [checkpoints, setCheckpoints] = useState<CheckpointItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"workers" | "checkpoints" | "metrics">("workers");

  const handleLaunchBatchJob = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/batch/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: datasetId,
          target_objective: targetObjective,
          total_subjects_target: totalSubjects,
          chunk_size: chunkSize,
          max_workers: workersCount,
          enable_ephemeris_cache: true,
          checkpoint_interval_chunks: 2,
          monte_carlo_permutations: 50,
        }),
      });

      if (res.ok) {
        const data: BatchReport = await res.json();
        setReport(data);

        // Fetch checkpoints
        const chkRes = await fetch(`/api/v1/research/batch/jobs/${data.job_id}/checkpoints`);
        if (chkRes.ok) {
          const chkData = await chkRes.json();
          setCheckpoints(chkData);
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
              Priority 18: Large-Scale Distributed / Local Cohort Optimization
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              High-throughput multi-worker parallel execution, incremental chunk streaming, LRU ephemeris caching, and SHA-256 state checkpointing.
            </p>
          </div>
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
            Priority 18 Active
          </span>
        </div>
      </div>

      {/* Orchestration Parameters */}
      <div className="grid grid-cols-1 gap-4 rounded-xl border border-slate-800 bg-slate-900/40 p-5 sm:grid-cols-5">
        <div>
          <label className="text-xs font-medium text-slate-400">Cohort Benchmark</label>
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          >
            <option value="ds-marriage-28">Marriage Cohort (N=250)</option>
            <option value="ds-career-founders">Career Founders Cohort (N=180)</option>
            <option value="ds-longevity-80">Longevity Cohort (N=80)</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Target Natives (N)</label>
          <input
            type="number"
            value={totalSubjects}
            onChange={(e) => setTotalSubjects(Number(e.target.value))}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Chunk Size</label>
          <input
            type="number"
            value={chunkSize}
            onChange={(e) => setChunkSize(Number(e.target.value))}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-slate-400">Parallel Workers</label>
          <select
            value={workersCount}
            onChange={(e) => setWorkersCount(Number(e.target.value))}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          >
            <option value={2}>2 Workers</option>
            <option value={4}>4 Workers</option>
            <option value={8}>8 Workers</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={handleLaunchBatchJob}
            disabled={loading}
            className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-600/30 transition hover:bg-emerald-500 disabled:opacity-50"
          >
            {loading ? "Streaming Chunks..." : "Launch Batch Job"}
          </button>
        </div>
      </div>

      {report && (
        <div className="space-y-6">
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Total Evaluated</span>
              <div className="mt-1 text-3xl font-black text-emerald-400">{report.total_subjects_evaluated}</div>
              <span className="text-xs text-slate-500">{report.total_runtime_seconds}s Runtime</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Average Throughput</span>
              <div className="mt-1 text-3xl font-black text-cyan-400">
                {report.average_throughput_charts_per_sec}
              </div>
              <span className="text-xs text-cyan-400 font-medium">Charts / Sec</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Cache Hit Rate</span>
              <div className="mt-1 text-3xl font-black text-purple-400">{report.cache_hit_rate_percent}%</div>
              <span className="text-xs text-slate-500">Ephemeris Sub-Lord Caching</span>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
              <span className="text-xs font-medium text-slate-400">Aggregate ROC-AUC</span>
              <div className="mt-1 text-3xl font-black text-amber-400">{report.aggregate_roc_auc.toFixed(3)}</div>
              <span className="text-xs text-emerald-400 font-medium">Brier: {report.aggregate_brier_score.toFixed(4)}</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab("workers")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "workers"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Parallel Compute Workers ({report.worker_metrics.length})
            </button>
            <button
              onClick={() => setActiveTab("checkpoints")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "checkpoints"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              SHA-256 State Checkpoints ({checkpoints.length})
            </button>
            <button
              onClick={() => setActiveTab("metrics")}
              className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                activeTab === "metrics"
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              Online Stream Convergence Metrics
            </button>
          </div>

          {/* Tab 1: Worker Pool */}
          {activeTab === "workers" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {report.worker_metrics.map((w) => (
                <div
                  key={w.worker_id}
                  className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{w.worker_id}</span>
                    <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-400 font-mono">
                      Chunk #{w.active_chunk_index}
                    </span>
                  </div>
                  <div className="space-y-1 text-xs text-slate-300 font-mono">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Processed:</span>
                      <span>{w.processed_count} charts</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Speed:</span>
                      <span className="text-cyan-400">{w.throughput_charts_per_sec} /s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Memory:</span>
                      <span>{w.memory_mb.toFixed(1)} MB</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">CPU Load:</span>
                      <span>{w.cpu_utilization_percent.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 2: Checkpoints */}
          {activeTab === "checkpoints" && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <h2 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">
                Immutable SHA-256 Checkpoint Ledger
              </h2>
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-slate-800 bg-slate-900/80 font-semibold text-slate-400 uppercase">
                    <tr>
                      <th className="px-3 py-2">Checkpoint ID</th>
                      <th className="px-3 py-2">Chunk</th>
                      <th className="px-3 py-2">Processed</th>
                      <th className="px-3 py-2">SHA-256 State Hash</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/20 font-mono">
                    {checkpoints.map((c) => (
                      <tr key={c.checkpoint_id} className="hover:bg-slate-800/30">
                        <td className="px-3 py-2 font-bold text-white">{c.checkpoint_id}</td>
                        <td className="px-3 py-2 text-cyan-400">Chunk {c.chunk_index}</td>
                        <td className="px-3 py-2 text-emerald-400">{c.processed_subjects} natives</td>
                        <td className="px-3 py-2 text-[11px] text-slate-400 truncate max-w-xs">
                          {c.checkpoint_sha256_hash}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 3: Metrics */}
          {activeTab === "metrics" && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
              <h2 className="text-sm font-semibold text-purple-300 uppercase tracking-wider">
                Online Stream Aggregated Statistical Metrics
              </h2>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 font-mono text-xs">
                <div className="rounded bg-slate-950 p-4 border border-slate-800 space-y-1">
                  <div className="text-slate-500">Aggregate Log Loss</div>
                  <div className="text-lg font-bold text-white">{report.aggregate_log_loss.toFixed(4)}</div>
                </div>
                <div className="rounded bg-slate-950 p-4 border border-slate-800 space-y-1">
                  <div className="text-slate-500">Aggregate Hit Rate</div>
                  <div className="text-lg font-bold text-emerald-400">
                    {(report.aggregate_hit_rate * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="rounded bg-slate-950 p-4 border border-slate-800 space-y-1">
                  <div className="text-slate-500">Checkpoints Preserved</div>
                  <div className="text-lg font-bold text-cyan-400">{report.checkpoints_saved}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
