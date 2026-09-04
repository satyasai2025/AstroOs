"use client";

import React, { useState, useEffect } from "react";

interface StatisticalDegradationTest {
  baseline_prospective_hit_rate: number;
  longitudinal_rolling_hit_rate: number;
  delta_hit_rate: number;
  sample_size_longitudinal: number;
  z_statistic: number;
  degradation_p_value: number;
  is_degradation_statistically_significant: boolean;
  test_interpretation: string;
}

interface LongitudinalTimeSeriesInterval {
  interval_id: string;
  interval_start: string;
  interval_end: string;
  sample_size_n: number;
  confirmed_hits: number;
  confirmed_misses: number;
  interval_hit_rate: number;
  rolling_brier_score: number;
  interval_psi: number;
  distribution_drift_status: string;
}

interface LongitudinalTrackingReport {
  report_id: string;
  rule_id: string;
  rule_name: string;
  target_objective: string;
  total_subjects_tracked: number;
  confirmed_hits_count: number;
  confirmed_misses_count: number;
  ambiguous_count: number;
  outside_window_count: number;
  cumulative_hit_rate: number;
  cumulative_brier_score: number;
  population_distribution_drift: string;
  population_stability_index: number;
  statistical_degradation_test: StatisticalDegradationTest;
  time_series_intervals: LongitudinalTimeSeriesInterval[];
  p11_lineage_snapshot_id: string;
  report_provenance_hash: string;
  epistemic_non_causal_statement: string;
  evaluated_at: string;
}

const DEFAULT_REPORT: LongitudinalTrackingReport = {
  report_id: "long-marriage-2026-eval",
  rule_id: "hyp-m1",
  rule_name: "7th Lord Dasha + Jupiter Aspect Rule",
  target_objective: "marriage",
  total_subjects_tracked: 50,
  confirmed_hits_count: 43,
  confirmed_misses_count: 6,
  ambiguous_count: 1,
  outside_window_count: 0,
  cumulative_hit_rate: 0.8776,
  cumulative_brier_score: 0.0245,
  population_distribution_drift: "STABLE_CONGRUENT",
  population_stability_index: 0.041,
  statistical_degradation_test: {
    baseline_prospective_hit_rate: 0.820,
    longitudinal_rolling_hit_rate: 0.8776,
    delta_hit_rate: 0.0576,
    sample_size_longitudinal: 49,
    z_statistic: 1.124,
    degradation_p_value: 0.8695,
    is_degradation_statistically_significant: false,
    test_interpretation: "NO_DEGRADATION: Longitudinal hit rate (87.8%) exceeds baseline prospective rate (82.0%), Delta = +5.8%.",
  },
  time_series_intervals: [
    {
      interval_id: "2026-Q1",
      interval_start: "2026-01-01",
      interval_end: "2026-03-31",
      sample_size_n: 25,
      confirmed_hits: 22,
      confirmed_misses: 3,
      interval_hit_rate: 0.8800,
      rolling_brier_score: 0.0240,
      interval_psi: 0.032,
      distribution_drift_status: "STABLE_CONGRUENT",
    },
    {
      interval_id: "2026-Q2",
      interval_start: "2026-04-01",
      interval_end: "2026-06-30",
      sample_size_n: 25,
      confirmed_hits: 21,
      confirmed_misses: 3,
      interval_hit_rate: 0.8750,
      rolling_brier_score: 0.0245,
      interval_psi: 0.041,
      distribution_drift_status: "STABLE_CONGRUENT",
    },
  ],
  p11_lineage_snapshot_id: "snap-p11-frozen-root",
  report_provenance_hash: "c7d8e9f1a2b3c4d5",
  epistemic_non_causal_statement: "LONGITUDINAL_TRACKING_ONLY: Real-world outcome tracking evaluates empirical temporal co-occurrence and calibration consistency without asserting physical causality.",
  evaluated_at: "2026-08-22T09:35:00Z",
};

export const ResearchLongitudinalTrackingStudio: React.FC = () => {
  const [targetObjective, setTargetObjective] = useState("marriage");
  const [ruleId, setRuleId] = useState("");
  const [snapshotId, setSnapshotId] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"drift" | "intervals" | "stream" | "governance">("drift");
  const [report, setReport] = useState<LongitudinalTrackingReport>(DEFAULT_REPORT);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/longitudinal-tracking/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_objective: targetObjective,
          rule_id: ruleId || null,
          snapshot_id: snapshotId || null,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setReport(data);
      }
    } catch (e) {
      console.warn("Failed to fetch live longitudinal tracking report, using fallback state:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [targetObjective]);

  const getDriftBadge = (drift: string) => {
    switch (drift) {
      case "STABLE_CONGRUENT":
        return {
          bg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
          label: "STABLE CONGRUENT (PSI < 0.10)",
        };
      case "MILD_DRIFT_MONITOR":
        return {
          bg: "bg-amber-500/10 border-amber-500/30 text-amber-400",
          label: "MILD DRIFT (0.10 <= PSI < 0.25)",
        };
      default:
        return {
          bg: "bg-rose-500/10 border-rose-500/30 text-rose-400",
          label: "CRITICAL DEGRADATION (PSI >= 0.25)",
        };
    }
  };

  const driftBadge = getDriftBadge(report.population_distribution_drift);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400 font-bold text-lg">
              ⏱️
            </span>
            <h1 className="text-2xl font-bold tracking-tight">
              Priority 27: Longitudinal Outcome Tracking Engine
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Continuous real-world prospective observation recording, time-series calibration, & dual-drift diagnosis.
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

          <input
            type="text"
            placeholder="Optional Rule ID"
            value={ruleId}
            onChange={(e) => setRuleId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-44"
          />

          <button
            onClick={fetchReport}
            disabled={loading}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition shadow-lg shadow-indigo-600/20"
          >
            <span>{loading ? "Evaluating..." : "Evaluate Tracking Metrics"}</span>
          </button>
        </div>
      </div>

      {/* Top Banner: Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Cumulative Hit Rate */}
        <div className="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 flex flex-col justify-between">
          <div>
            <span className="text-xs uppercase tracking-wider font-semibold text-emerald-400">
              Cumulative Hit Rate
            </span>
            <div className="text-3xl font-extrabold text-white mt-1">
              {(report.cumulative_hit_rate * 100).toFixed(1)}%
            </div>
          </div>
          <span className="text-xs text-emerald-300 mt-2">
            Confirmed: {report.confirmed_hits_count} Hits • {report.confirmed_misses_count} Misses
          </span>
        </div>

        {/* Total Subjects Tracked */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Total Subjects Tracked
            </span>
            <div className="text-3xl font-extrabold text-white mt-1">
              {report.total_subjects_tracked} Records
            </div>
          </div>
          <span className="text-xs text-indigo-400">
            Ambiguous: {report.ambiguous_count} • Outside: {report.outside_window_count}
          </span>
        </div>

        {/* Population Stability Index (PSI) */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Population Stability (PSI)
            </span>
            <div className="text-3xl font-extrabold text-white mt-1 font-mono">
              {report.population_stability_index.toFixed(3)}
            </div>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded border font-mono font-semibold w-fit ${driftBadge.bg}`}>
            {driftBadge.label}
          </span>
        </div>

        {/* Statistical Degradation Test */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Degradation Significance (p)
            </span>
            <div className="text-3xl font-extrabold text-white mt-1 font-mono">
              {report.statistical_degradation_test.degradation_p_value.toFixed(4)}
            </div>
          </div>
          <span className="text-xs text-slate-300">
            {report.statistical_degradation_test.is_degradation_statistically_significant ? (
              <span className="text-rose-400 font-bold">⚠️ SIGNIFICANT DEGRADATION</span>
            ) : (
              <span className="text-emerald-400 font-bold">✓ NO SIGNIFICANT DEGRADATION</span>
            )}
          </span>
        </div>
      </div>

      {/* Studio Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("drift")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "drift"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>🔬 Dual-Mechanism Drift Diagnosis</span>
        </button>

        <button
          onClick={() => setActiveTab("intervals")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "intervals"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>📅 Quarterly Time-Series Intervals ({report.time_series_intervals.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("stream")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "stream"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>📡 Real-World Observation Stream</span>
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

      {/* Tab 1: Dual-Mechanism Drift Diagnosis */}
      {activeTab === "drift" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Mechanism 1: Population Stability Index */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 font-mono font-semibold">
                  Mechanism 1
                </span>
                <h3 className="text-base font-bold text-white mt-1">
                  Population Distribution Drift (PSI)
                </h3>
              </div>
              <span className={`text-xs px-2.5 py-1 rounded border font-mono font-semibold ${driftBadge.bg}`}>
                {driftBadge.label}
              </span>
            </div>

            <p className="text-xs text-slate-400">
              Measures shifts between baseline expected prediction distributions and active real-world longitudinal cohorts.
            </p>

            <div className="space-y-2 pt-2 text-xs">
              <div className="flex justify-between text-slate-300">
                <span>Calculated PSI Score:</span>
                <span className="font-mono font-bold text-white">{report.population_stability_index.toFixed(4)}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Stable Threshold:</span>
                <span className="font-mono text-emerald-400">PSI &lt; 0.10</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Warning Threshold:</span>
                <span className="font-mono text-amber-400">0.10 &le; PSI &lt; 0.25</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Critical Trigger:</span>
                <span className="font-mono text-rose-400">PSI &ge; 0.25</span>
              </div>
            </div>
          </div>

          {/* Mechanism 2: Formal Statistical Degradation Test */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 font-mono font-semibold">
                  Mechanism 2
                </span>
                <h3 className="text-base font-bold text-white mt-1">
                  Statistical Degradation Test (Two-Proportion Z-Test)
                </h3>
              </div>
              <span className="text-xs px-2.5 py-1 rounded border font-mono font-semibold bg-indigo-500/10 border-indigo-500/20 text-indigo-400">
                Z = {report.statistical_degradation_test.z_statistic.toFixed(3)}
              </span>
            </div>

            <p className="text-xs text-slate-300 italic bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              {report.statistical_degradation_test.test_interpretation}
            </p>

            <div className="space-y-2 pt-2 text-xs">
              <div className="flex justify-between text-slate-300">
                <span>Baseline Prospective Hit Rate:</span>
                <span className="font-mono text-slate-200">{(report.statistical_degradation_test.baseline_prospective_hit_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Longitudinal Rolling Hit Rate:</span>
                <span className="font-mono text-emerald-400 font-bold">{(report.statistical_degradation_test.longitudinal_rolling_hit_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Observed Hit Rate Delta (Δ):</span>
                <span className="font-mono font-bold text-white">
                  {report.statistical_degradation_test.delta_hit_rate >= 0 ? "+" : ""}
                  {(report.statistical_degradation_test.delta_hit_rate * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>One-Tailed Degradation p-value:</span>
                <span className="font-mono text-indigo-400 font-bold">{report.statistical_degradation_test.degradation_p_value.toFixed(5)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Quarterly Time-Series Intervals */}
      {activeTab === "intervals" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.time_series_intervals.map((interval) => (
              <div
                key={interval.interval_id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3"
              >
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-indigo-400 text-base">{interval.interval_id}</span>
                    <span className="text-xs text-slate-400">
                      ({interval.interval_start} to {interval.interval_end})
                    </span>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                    N={interval.sample_size_n}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs pt-1">
                  <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/60">
                    <span className="text-slate-400">Interval Hit Rate</span>
                    <div className="text-base font-bold text-emerald-400 mt-0.5">
                      {(interval.interval_hit_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/60">
                    <span className="text-slate-400">Rolling Brier</span>
                    <div className="text-base font-mono font-bold text-white mt-0.5">
                      {interval.rolling_brier_score.toFixed(4)}
                    </div>
                  </div>
                  <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/60">
                    <span className="text-slate-400">Interval PSI</span>
                    <div className="text-base font-mono font-bold text-indigo-400 mt-0.5">
                      {interval.interval_psi.toFixed(3)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Real-World Observation Stream */}
      {activeTab === "stream" && (
        <div className="space-y-4">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="font-semibold text-slate-200 text-sm">
              Continuous Prospective Stream: {report.rule_name}
            </h3>
            <p className="text-xs text-slate-400">
              Observational records ingested via standardized municipal registries with pre-registered timing window constraints.
            </p>
            <div className="overflow-x-auto pt-2">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">Native ID</th>
                    <th className="py-2.5 px-3">Predicted Window</th>
                    <th className="py-2.5 px-3">Actual Event Date</th>
                    <th className="py-2.5 px-3">Predicted Prob</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-3 font-mono font-bold text-indigo-400">subj-long-q1-001</td>
                    <td className="py-2.5 px-3 text-slate-300">2026-01-15 &rarr; 2026-03-31</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-mono">2026-02-14</td>
                    <td className="py-2.5 px-3 font-mono">88.0%</td>
                    <td className="py-2.5 px-3">
                      <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold">
                        CONFIRMED HIT
                      </span>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-3 font-mono font-bold text-indigo-400">subj-long-q1-023</td>
                    <td className="py-2.5 px-3 text-slate-300">2026-01-15 &rarr; 2026-03-31</td>
                    <td className="py-2.5 px-3 text-slate-500 font-mono">None (Elapsed)</td>
                    <td className="py-2.5 px-3 font-mono">88.0%</td>
                    <td className="py-2.5 px-3">
                      <span className="text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 font-bold">
                        CONFIRMED MISS
                      </span>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-900/40">
                    <td className="py-2.5 px-3 font-mono font-bold text-indigo-400">subj-long-q2-050</td>
                    <td className="py-2.5 px-3 text-slate-300">2026-04-01 &rarr; 2026-06-30</td>
                    <td className="py-2.5 px-3 text-amber-400 font-mono">2026-05-20 (Imprecise)</td>
                    <td className="py-2.5 px-3 font-mono">85.0%</td>
                    <td className="py-2.5 px-3">
                      <span className="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-bold">
                        AMBIGUOUS UNVERIFIED
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
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
              <span>Epistemic Scope & Longitudinal Observational Boundaries</span>
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
                <div className="text-slate-200 mt-1">{report.p11_lineage_snapshot_id}</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400">Report Provenance Hash:</span>
                <div className="text-slate-200 mt-1">{report.report_provenance_hash}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
