"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";

interface BenchmarkDefinition {
  benchmark_id: string;
  name: string;
  event_type: string;
  description: string;
  standard_tolerance_days: number;
  is_locked: boolean;
  locked_version?: string;
  locked_event_count?: number;
  content_hash_sha256?: string;
}

interface ProfileComparisonRow {
  profile_id: string;
  profile_name: string;
  calibration_sample_size_n: number;
  holdout_sample_size_n: number;
  holdout_precision: number;
  holdout_recall: number;
  holdout_f1_score: number;
  holdout_hit_rate_pct: number;
  holdout_brier_score: number;
  holdout_mae_peak_days: number;
  holdout_median_peak_offset_days: number;
  holdout_p90_peak_offset_days: number;
  calibration_method: string;
}

interface BaselineDelta {
  profile_id: string;
  baseline_profile_id: string;
  delta_hit_rate_pct: number;
  delta_brier_score: number;
  delta_f1_score: number;
  delta_mae_peak_days: number;
  is_statistically_superior: boolean;
  p_value: number;
  odds_ratio: number;
  verdict: string;
}

interface BenchmarkComparisonResponse {
  experiment_id: string;
  benchmark_id: string;
  benchmark_version: string;
  content_hash_sha256: string;
  split_seed: number;
  split_train_ratio: number;
  tolerance_days: number;
  total_benchmark_events: number;
  train_events_count: number;
  holdout_events_count: number;
  rows: ProfileComparisonRow[];
  baseline_comparisons: BaselineDelta[];
}

interface CalibrationBin {
  score_range: string;
  min_score: number;
  max_score: number;
  sample_size_n: number;
  observed_hits: number;
  empirical_hit_rate_pct: number;
  rate_ci_95: number[];
  has_small_n_warning: boolean;
}

interface CalibrationCurveReport {
  benchmark_id: string;
  version: string;
  profile_id: string;
  total_train_n: number;
  brier_score: number;
  bins: CalibrationBin[];
}

interface ExperimentSummary {
  experiment_id: string;
  benchmark_id: string;
  benchmark_version: string;
  status: string;
  split_seed: number;
  split_train_ratio: number;
  tolerance_days: number;
  profile_ids: string[];
  results_hash_sha256: string;
  duration_ms: number;
  created_at?: string;
}

interface McNemarTest {
  contingency_table: number[];
  b_discordant_baseline_only: number;
  c_discordant_candidate_only: number;
  statistic: number;
  p_value: number;
  odds_ratio: number;
  is_significant: boolean;
}

interface BootstrapCI {
  metric_name: string;
  point_estimate: number;
  ci_lower: number;
  ci_upper: number;
  confidence_level: number;
  standard_error: number;
}

interface ProfileSignificance {
  profile_id: string;
  baseline_profile_id: string;
  mcnemar_test: McNemarTest;
  brier_permutation_p_value: number;
  delta_hit_rate_pct: number;
  delta_brier_score: number;
  delta_mae_peak_days: number;
  bootstrap_cis: Record<string, BootstrapCI>;
  verdict: string;
}

interface SignificanceResponse {
  experiment_id: string;
  benchmark_id: string;
  benchmark_version: string;
  reports: ProfileSignificance[];
}

interface DecisionRecommendation {
  status: string;
  recommended_profile_id: string;
  baseline_profile_id: string;
  confidence_score: number;
  key_evidence_drivers: string[];
  risk_factors: string[];
  sample_size_adequate: boolean;
  requires_human_signoff: boolean;
}

interface ReportResponse {
  experiment_id: string;
  benchmark_id: string;
  benchmark_version: string;
  decision: DecisionRecommendation;
  executive_summary: string;
  markdown_content: string;
  json_content: Record<string, unknown>;
}

interface ProductionProfile {
  profile_id: string;
  version: string;
  benchmark_id: string;
  is_active_baseline: boolean;
  promoted_from_experiment_id?: string;
  approved_by?: string;
  promoted_at?: string;
  notes?: string;
}

interface SignoffRecord {
  signoff_id: string;
  experiment_id: string;
  status: string;
  reviewer_id: string;
  notes: string;
  signed_at: string;
}

interface ReproducibilityAuditResponse {
  experiment_id: string;
  is_bit_for_bit_identical: boolean;
  expected_results_hash: string;
  actual_results_hash: string;
  verified_at: string;
  audit_notes: string;
}

// Continuous Monitoring Interfaces
interface MonitoringSchedule {
  schedule_id: string;
  benchmark_id: string;
  interval_seconds: number;
  is_active: boolean;
  tolerance_days: number;
  split_seed: number;
  last_run_at?: string;
  next_run_at?: string;
}

interface RegressionAlert {
  alert_id: string;
  benchmark_id: string;
  experiment_id: string;
  severity: string;
  title: string;
  description: string;
  metrics_impact: Record<string, number>;
  is_acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  created_at: string;
}

interface GovernanceAuditLog {
  audit_id: string;
  event_type: string;
  benchmark_id: string;
  experiment_id?: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: string;
}

interface CorpusVersionEvent {
  benchmark_id: string;
  detected_version: string;
  previous_version?: string;
  content_hash_sha256: string;
  verified_events_count: number;
  is_new_version: boolean;
  detected_at: string;
}

// Intelligence & Trends Interfaces
interface TrendPoint {
  experiment_id: string;
  timestamp: string;
  profile_id: string;
  profile_name: string;
  tolerance_days: number;
  split_seed: number;
  holdout_sample_size_n: number;
  holdout_hit_rate_pct: number;
  holdout_brier_score: number;
  holdout_mae_days: number;
  holdout_f1_score: number;
  delta_hit_rate_pct: number;
  delta_brier_score: number;
  p_value?: number;
  verdict?: string;
}

interface ProfileSummary {
  profile_id: string;
  profile_name: string;
  total_evaluations: number;
  mean_hit_rate_pct: number;
  mean_brier_score: number;
  mean_mae_days: number;
  mean_f1_score: number;
  std_hit_rate_pct: number;
  std_brier_score: number;
  min_hit_rate_pct: number;
  max_hit_rate_pct: number;
  min_brier_score: number;
  max_brier_score: number;
  trajectory: TrendPoint[];
}

interface CorpusDemographics {
  benchmark_id: string;
  current_version: string;
  total_verified_events: number;
  content_hash_sha256: string;
  birth_confidence_distribution: Record<string, number>;
  event_verification_distribution: Record<string, number>;
  date_confidence_distribution: Record<string, number>;
}

interface StabilityBreakdown {
  hit_rate_stability_component: number;
  brier_stability_component: number;
  regression_free_component: number;
  composite_stability_index: number;
  total_runs_evaluated: number;
  std_hit_rate: number;
  std_brier: number;
  regression_free_runs_ratio: number;
}

interface IntelligenceReport {
  benchmark_id: string;
  active_baseline_profile_id: string;
  total_experiments: number;
  stability: StabilityBreakdown;
  profile_summaries: Record<string, ProfileSummary>;
  corpus_demographics: CorpusDemographics;
  alert_frequency_summary: Record<string, number>;
  generated_at: string;
}

export function BenchmarkLab() {
  const [activeTab, setActiveTab] = useState<"corpus" | "comparison" | "decision" | "governance" | "monitoring" | "trends" | "significance" | "reliability" | "timing" | "audit" | "experiments">("corpus");
  const [benchmarks, setBenchmarks] = useState<BenchmarkDefinition[]>([]);
  const [selectedBenchmarkId, setSelectedBenchmarkId] = useState<string>("BENCH-CAREER-001");
  const [toleranceDays, setToleranceDays] = useState<number>(30);
  const [splitSeed, setSplitSeed] = useState<number>(42);
  const [loading, setLoading] = useState<boolean>(false);
  const [comparisonData, setComparisonData] = useState<BenchmarkComparisonResponse | null>(null);
  const [curveData, setCurveData] = useState<CalibrationCurveReport | null>(null);
  const [significanceData, setSignificanceData] = useState<SignificanceResponse | null>(null);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [copiedReport, setCopiedReport] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Production Governance State
  const [productionProfiles, setProductionProfiles] = useState<ProductionProfile[]>([]);
  const [currentSignoff, setCurrentSignoff] = useState<SignoffRecord | null>(null);
  const [reviewerName, setReviewerName] = useState<string>("Lead Astrological Scientist");
  const [signoffNotes, setSignoffNotes] = useState<string>("");
  const [submittingSignoff, setSubmittingSignoff] = useState<boolean>(false);
  const [auditResult, setAuditResult] = useState<ReproducibilityAuditResponse | null>(null);
  const [verifyingAudit, setVerifyingAudit] = useState<boolean>(false);
  const [promotionSuccess, setPromotionSuccess] = useState<string | null>(null);

  // Continuous Monitoring & Alerts State
  const [schedules, setSchedules] = useState<MonitoringSchedule[]>([]);
  const [alerts, setAlerts] = useState<RegressionAlert[]>([]);
  const [auditLogs, setAuditLogs] = useState<GovernanceAuditLog[]>([]);
  const [corpusEvents, setCorpusEvents] = useState<CorpusVersionEvent[]>([]);
  const [triggeringSchedule, setTriggeringSchedule] = useState<string | null>(null);

  // Benchmark Intelligence & Trends State
  const [intelligenceReport, setIntelligenceReport] = useState<IntelligenceReport | null>(null);
  const [loadingIntelligence, setLoadingIntelligence] = useState<boolean>(false);

  // Persisted experiment history & diffing
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);
  const [diffRunA, setDiffRunA] = useState<string>("");
  const [diffRunB, setDiffRunB] = useState<string>("");
  const [diffDataA, setDiffDataA] = useState<BenchmarkComparisonResponse | null>(null);
  const [diffDataB, setDiffDataB] = useState<BenchmarkComparisonResponse | null>(null);

  const fetchBenchmarks = async () => {
    try {
      const res = await api.get<BenchmarkDefinition[]>("/api/v1/benchmarks");
      setBenchmarks(res);
      if (res.length > 0 && !selectedBenchmarkId) {
        setSelectedBenchmarkId(res[0].benchmark_id);
      }
    } catch (err: unknown) {
      console.error("Failed to fetch benchmarks:", err);
    }
  };

  const fetchExperimentHistory = useCallback(async (benchmarkId: string) => {
    if (!benchmarkId) return;
    setLoadingHistory(true);
    try {
      const res = await api.get<ExperimentSummary[]>(`/api/v1/benchmarks/${benchmarkId}/experiments`);
      setExperiments(res);
    } catch (err: unknown) {
      console.error("Failed to fetch experiment history:", err);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const fetchProductionProfiles = useCallback(async (benchmarkId: string) => {
    if (!benchmarkId) return;
    try {
      const res = await api.get<ProductionProfile[]>(`/api/v1/governance/benchmarks/${benchmarkId}/production-profiles`);
      setProductionProfiles(res);
    } catch (err: unknown) {
      console.error("Failed to fetch production profiles:", err);
    }
  }, []);

  const fetchMonitoringData = useCallback(async (benchmarkId: string) => {
    try {
      const [schedRes, alertsRes, logsRes] = await Promise.all([
        api.get<MonitoringSchedule[]>("/api/v1/monitoring/schedules"),
        api.get<RegressionAlert[]>(`/api/v1/monitoring/alerts?benchmark_id=${benchmarkId}`),
        api.get<GovernanceAuditLog[]>(`/api/v1/monitoring/audit-logs?benchmark_id=${benchmarkId}&limit=25`),
      ]);
      setSchedules(schedRes);
      setAlerts(alertsRes);
      setAuditLogs(logsRes);
    } catch (err: unknown) {
      console.error("Failed to fetch continuous monitoring data:", err);
    }
  }, []);

  const fetchIntelligenceData = useCallback(async (benchmarkId: string) => {
    if (!benchmarkId) return;
    setLoadingIntelligence(true);
    try {
      const res = await api.get<IntelligenceReport>(`/api/v1/intelligence/benchmarks/${benchmarkId}/report`);
      setIntelligenceReport(res);
    } catch (err: unknown) {
      console.error("Failed to fetch intelligence report:", err);
    } finally {
      setLoadingIntelligence(false);
    }
  }, []);

  const fetchSignoff = async (experimentId: string) => {
    if (!experimentId) return;
    try {
      const res = await api.get<SignoffRecord | null>(`/api/v1/governance/experiments/${experimentId}/signoff`);
      setCurrentSignoff(res);
    } catch (err: unknown) {
      console.error("Failed to fetch signoff:", err);
    }
  };

  useEffect(() => {
    fetchBenchmarks();
  }, []);

  useEffect(() => {
    if (selectedBenchmarkId) {
      fetchExperimentHistory(selectedBenchmarkId);
      fetchProductionProfiles(selectedBenchmarkId);
      fetchMonitoringData(selectedBenchmarkId);
      fetchIntelligenceData(selectedBenchmarkId);
    }
  }, [selectedBenchmarkId, fetchExperimentHistory, fetchProductionProfiles, fetchMonitoringData, fetchIntelligenceData]);

  const handleRunComparison = async () => {
    setLoading(true);
    setError(null);
    setAuditResult(null);
    setPromotionSuccess(null);
    try {
      const payload = {
        version: "1.0.0",
        profile_ids: ["parashari_standard_v1", "empirical_research_v1"],
        baseline_profile_id: "parashari_standard_v1",
        tolerance_days: toleranceDays,
        split_seed: splitSeed,
        split_train_ratio: 0.70,
      };

      const res = await api.post<BenchmarkComparisonResponse>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/compare`,
        payload
      );
      setComparisonData(res);
      setActiveTab("comparison");

      // Refresh experiment history, monitoring & intelligence
      fetchExperimentHistory(selectedBenchmarkId);
      fetchProductionProfiles(selectedBenchmarkId);
      fetchMonitoringData(selectedBenchmarkId);
      fetchIntelligenceData(selectedBenchmarkId);
      fetchSignoff(res.experiment_id);

      // Fetch calibration curve
      const curveRes = await api.get<CalibrationCurveReport>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/calibration-curve?profile_id=parashari_standard_v1&seed=${splitSeed}&tolerance_days=${toleranceDays}`
      );
      setCurveData(curveRes);

      // Fetch significance analysis
      const sigRes = await api.get<SignificanceResponse>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/experiments/${res.experiment_id}/significance`
      );
      setSignificanceData(sigRes);

      // Fetch formal report & decision
      const repRes = await api.get<ReportResponse>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/experiments/${res.experiment_id}/report`
      );
      setReportData(repRes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to run benchmark experiment";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerSchedule = async (scheduleId: string) => {
    setTriggeringSchedule(scheduleId);
    try {
      await api.post(`/api/v1/monitoring/schedules/${scheduleId}/trigger`, {});
      fetchMonitoringData(selectedBenchmarkId);
      fetchExperimentHistory(selectedBenchmarkId);
      fetchIntelligenceData(selectedBenchmarkId);
    } catch (err: unknown) {
      console.error("Failed to trigger schedule:", err);
    } finally {
      setTriggeringSchedule(null);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await api.post(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, {
        reviewer_id: reviewerName,
      });
      fetchMonitoringData(selectedBenchmarkId);
    } catch (err: unknown) {
      console.error("Failed to acknowledge alert:", err);
    }
  };

  const handleScanCorpusChanges = async () => {
    try {
      const res = await api.post<CorpusVersionEvent[]>("/api/v1/monitoring/corpus/detect-changes", {});
      setCorpusEvents(res);
      fetchMonitoringData(selectedBenchmarkId);
      fetchIntelligenceData(selectedBenchmarkId);
    } catch (err: unknown) {
      console.error("Failed to scan corpus changes:", err);
    }
  };

  const handleLoadExperiment = async (expId: string) => {
    setLoading(true);
    setError(null);
    setAuditResult(null);
    setPromotionSuccess(null);
    try {
      const res = await api.get<BenchmarkComparisonResponse>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/experiments/${expId}`
      );
      setComparisonData(res);
      setToleranceDays(res.tolerance_days);
      setSplitSeed(res.split_seed);
      setActiveTab("comparison");

      fetchSignoff(expId);

      // Fetch calibration curve
      const curveRes = await api.get<CalibrationCurveReport>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/calibration-curve?profile_id=parashari_standard_v1&seed=${res.split_seed}&tolerance_days=${res.tolerance_days}`
      );
      setCurveData(curveRes);

      // Fetch significance analysis
      const sigRes = await api.get<SignificanceResponse>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/experiments/${res.experiment_id}/significance`
      );
      setSignificanceData(sigRes);

      // Fetch formal report & decision
      const repRes = await api.get<ReportResponse>(
        `/api/v1/benchmarks/${selectedBenchmarkId}/experiments/${res.experiment_id}/report`
      );
      setReportData(repRes);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load experiment";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSignoff = async (status: "APPROVED" | "REJECTED") => {
    if (!comparisonData) return;
    setSubmittingSignoff(true);
    try {
      const res = await api.post<SignoffRecord>(
        `/api/v1/governance/experiments/${comparisonData.experiment_id}/signoff`,
        {
          status,
          reviewer_id: reviewerName,
          notes: signoffNotes || `Signed off as ${status} by ${reviewerName}`,
        }
      );
      setCurrentSignoff(res);
      fetchMonitoringData(selectedBenchmarkId);
    } catch (err: unknown) {
      console.error("Signoff error:", err);
    } finally {
      setSubmittingSignoff(false);
    }
  };

  const handlePromoteToProduction = async () => {
    if (!comparisonData) return;
    setSubmittingSignoff(true);
    setPromotionSuccess(null);
    try {
      const res = await api.post<ProductionProfile>(
        `/api/v1/governance/experiments/${comparisonData.experiment_id}/promote`,
        {
          version: "1.1.0",
          reviewer_id: reviewerName,
          notes: signoffNotes || `Promoted to active production baseline by ${reviewerName}`,
        }
      );
      fetchProductionProfiles(selectedBenchmarkId);
      fetchMonitoringData(selectedBenchmarkId);
      fetchIntelligenceData(selectedBenchmarkId);
      setPromotionSuccess(`Successfully promoted ${res.profile_id} (v${res.version}) to active production baseline.`);
    } catch (err: unknown) {
      console.error("Promotion error:", err);
    } finally {
      setSubmittingSignoff(false);
    }
  };

  const handleVerifyReproducibility = async () => {
    if (!comparisonData) return;
    setVerifyingAudit(true);
    try {
      const res = await api.post<ReproducibilityAuditResponse>(
        `/api/v1/governance/experiments/${comparisonData.experiment_id}/verify-reproducibility`,
        {}
      );
      setAuditResult(res);
    } catch (err: unknown) {
      console.error("Audit error:", err);
    } finally {
      setVerifyingAudit(false);
    }
  };

  const handleLoadDiffRuns = async () => {
    if (!diffRunA || !diffRunB) return;
    try {
      const [resA, resB] = await Promise.all([
        api.get<BenchmarkComparisonResponse>(`/api/v1/benchmarks/${selectedBenchmarkId}/experiments/${diffRunA}`),
        api.get<BenchmarkComparisonResponse>(`/api/v1/benchmarks/${selectedBenchmarkId}/experiments/${diffRunB}`),
      ]);
      setDiffDataA(resA);
      setDiffDataB(resB);
    } catch (err: unknown) {
      console.error("Failed to load runs for diff:", err);
    }
  };

  const handleCopyMarkdown = () => {
    if (reportData?.markdown_content) {
      navigator.clipboard.writeText(reportData.markdown_content);
      setCopiedReport(true);
      setTimeout(() => setCopiedReport(false), 2500);
    }
  };

  const handleDownloadMarkdown = () => {
    if (!reportData) return;
    const blob = new Blob([reportData.markdown_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `AstroOS_Research_Report_${reportData.experiment_id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const activeBaseline = productionProfiles.find((p) => p.is_active_baseline);
  const unacknowledgedAlerts = alerts.filter((a) => !a.is_acknowledged);

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div
        className="glass-card p-5"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-primary)",
          borderRadius: "0.75rem",
        }}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
              AstroOS Research Benchmark Lab
            </h3>
            <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
              Longitudinal trend analytics, mathematical stability indices, continuous monitoring &amp; governance.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunComparison}
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold rounded transition shadow"
              style={{
                background: loading ? "var(--bg-muted)" : "var(--primary-color, #3b82f6)",
                color: "#fff",
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Evaluating &amp; Governing..." : "Run Locked Benchmark Comparison"}
            </button>
          </div>
        </div>

        {/* Global Control Toolbar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 pt-4" style={{ borderTop: "1px solid var(--border-subtle, #333)" }}>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Canonical Benchmark Problem
            </label>
            <select
              value={selectedBenchmarkId}
              onChange={(e) => setSelectedBenchmarkId(e.target.value)}
              className="w-full text-xs p-2 rounded bg-black/20"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
            >
              {benchmarks.map((b) => (
                <option key={b.benchmark_id} value={b.benchmark_id}>
                  {b.benchmark_id}: {b.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Evaluation Tolerance Window
            </label>
            <select
              value={toleranceDays}
              onChange={(e) => setToleranceDays(Number(e.target.value))}
              className="w-full text-xs p-2 rounded bg-black/20"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
            >
              <option value={15}>± 15 Days (Strict)</option>
              <option value={30}>± 30 Days (Standard)</option>
              <option value={45}>± 45 Days (Meso)</option>
              <option value={60}>± 60 Days (Macro)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Deterministic Partition Seed
            </label>
            <input
              type="number"
              value={splitSeed}
              onChange={(e) => setSplitSeed(Number(e.target.value))}
              className="w-full text-xs p-2 rounded bg-black/20"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Active Production Baseline
            </label>
            <div className="text-xs p-2 rounded bg-black/30 font-mono flex items-center justify-between">
              <span className="text-blue-400 font-bold">{activeBaseline ? `${activeBaseline.profile_id} (v${activeBaseline.version})` : "parashari_standard_v1"}</span>
              <span className="text-[10px] text-emerald-400 font-bold">ACTIVE</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mt-4 pt-3 overflow-x-auto" style={{ borderTop: "1px solid var(--border-subtle, #333)" }}>
          {(["corpus", "comparison", "decision", "governance", "monitoring", "trends", "significance", "reliability", "timing", "audit", "experiments"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider rounded transition flex items-center gap-1.5"
              style={{
                background: activeTab === tab ? "rgba(59, 130, 246, 0.2)" : "transparent",
                color: activeTab === tab ? "#60a5fa" : "var(--text-secondary)",
                border: activeTab === tab ? "1px solid #3b82f6" : "1px solid transparent",
              }}
            >
              <span>{tab === "trends" ? "Intelligence & Trends" : tab}</span>
              {tab === "monitoring" && unacknowledgedAlerts.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-red-900/80 text-red-200 font-mono font-bold animate-pulse">
                  {unacknowledgedAlerts.length}
                </span>
              )}
              {tab === "governance" && currentSignoff && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${currentSignoff.status === "APPROVED" ? "bg-emerald-900/60 text-emerald-300" : "bg-red-900/60 text-red-300"}`}>
                  {currentSignoff.status}
                </span>
              )}
              {tab === "experiments" && experiments.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-blue-900/60 text-blue-300 font-mono">
                  {experiments.length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded text-xs bg-red-900/20 text-red-400 border border-red-800">
          {error}
        </div>
      )}

      {/* Tab 1: Corpus Explorer */}
      {activeTab === "corpus" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {benchmarks.map((b) => (
              <div
                key={b.benchmark_id}
                className="p-5 rounded-lg transition glass-card"
                style={{
                  border: b.benchmark_id === selectedBenchmarkId ? "1px solid #3b82f6" : "1px solid var(--border-primary)",
                  background: "var(--bg-card)",
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-blue-400">{b.benchmark_id}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-emerald-900/40 text-emerald-300 border border-emerald-800">
                    {b.is_locked ? "LOCKED v1.0.0" : "DRAFT"}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-zinc-100 mt-2">{b.name}</h4>
                <p className="text-xs text-zinc-400 mt-1">{b.description}</p>
                <div className="mt-4 pt-3 flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400 border-t border-zinc-800">
                  <div>Verified Records: <span className="font-semibold text-zinc-200">{b.locked_event_count ?? "—"}</span></div>
                  <div>Standard Tol: <span className="font-semibold text-zinc-200">±{b.standard_tolerance_days}d</span></div>
                </div>
                {b.content_hash_sha256 && (
                  <div className="mt-2 text-[10px] font-mono text-zinc-500 truncate">
                    SHA-256: {b.content_hash_sha256}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Profile Comparison Matrix */}
      {activeTab === "comparison" && (
        <div className="space-y-4">
          {comparisonData ? (
            <div className="glass-card p-5 rounded-lg overflow-x-auto" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <div>
                  <h4 className="text-sm font-semibold text-zinc-100">
                    Empirical Profile Comparison Matrix: [{comparisonData.benchmark_id} v{comparisonData.benchmark_version}]
                  </h4>
                  <p className="text-xs text-zinc-400">
                    Evaluated on locked split (Seed: {comparisonData.split_seed}, Train N: {comparisonData.train_events_count}, Holdout N: {comparisonData.holdout_events_count}, Tol: ±{comparisonData.tolerance_days}d).
                  </p>
                </div>
                <div className="text-[11px] font-mono text-zinc-400">
                  Experiment ID: <span className="text-blue-400 font-bold">{comparisonData.experiment_id}</span>
                </div>
              </div>

              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[10px]">
                    <th className="p-2">Predictive Profile</th>
                    <th className="p-2 text-center">Holdout N</th>
                    <th className="p-2 text-center">Hit Rate %</th>
                    <th className="p-2 text-center">Precision</th>
                    <th className="p-2 text-center">Recall</th>
                    <th className="p-2 text-center">F1 Score</th>
                    <th className="p-2 text-center">Holdout Brier</th>
                    <th className="p-2 text-center">MAE (Days)</th>
                    <th className="p-2 text-center">Median (Days)</th>
                    <th className="p-2 text-center">P90 (Days)</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.rows.map((r, idx) => (
                    <tr key={r.profile_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/20">
                      <td className="p-2 font-semibold text-zinc-200">
                        {r.profile_name}
                        {idx === 0 && <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">BASELINE</span>}
                      </td>
                      <td className="p-2 text-center font-mono">{r.holdout_sample_size_n}</td>
                      <td className="p-2 text-center font-bold text-emerald-400">{r.holdout_hit_rate_pct}%</td>
                      <td className="p-2 text-center font-mono">{r.holdout_precision}</td>
                      <td className="p-2 text-center font-mono">{r.holdout_recall}</td>
                      <td className="p-2 text-center font-mono font-semibold text-blue-400">{r.holdout_f1_score}</td>
                      <td className="p-2 text-center font-mono text-amber-300">{r.holdout_brier_score}</td>
                      <td className="p-2 text-center font-mono">{r.holdout_mae_peak_days}d</td>
                      <td className="p-2 text-center font-mono">{r.holdout_median_peak_offset_days}d</td>
                      <td className="p-2 text-center font-mono">{r.holdout_p90_peak_offset_days}d</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Baseline Comparison Deltas & p-values */}
              {comparisonData.baseline_comparisons.length > 0 && (
                <div className="mt-5 pt-4 border-t border-zinc-800">
                  <h5 className="text-xs font-semibold text-zinc-300 mb-2 uppercase tracking-wider">
                    Relative Improvement &amp; Significance vs Baseline
                  </h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {comparisonData.baseline_comparisons.map((b) => (
                      <div key={b.profile_id} className="p-3 rounded bg-black/30 border border-zinc-800 flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-zinc-200">{b.profile_id}</span>
                            <span className="text-[10px] font-mono text-zinc-400">
                              (McNemar p = {b.p_value})
                            </span>
                          </div>
                          <div className="text-[11px] text-zinc-400 mt-0.5">
                            Δ Hit Rate: <span className={b.delta_hit_rate_pct >= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>{b.delta_hit_rate_pct >= 0 ? `+${b.delta_hit_rate_pct}` : b.delta_hit_rate_pct}%</span> |
                            Δ Brier: <span className={b.delta_brier_score <= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>{b.delta_brier_score}</span> |
                            Odds Ratio: <span className="font-mono text-zinc-200">{b.odds_ratio}</span>
                          </div>
                        </div>
                        <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${b.verdict === "STATISTICALLY_SIGNIFICANT_SUPERIOR" ? "bg-emerald-900/40 text-emerald-300 border border-emerald-800" : "bg-zinc-800 text-zinc-400"}`}>
                          {b.verdict === "STATISTICALLY_SIGNIFICANT_SUPERIOR" ? "SUPERIOR (p < 0.05)" : "EQUIVALENT"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-zinc-500 glass-card">
              Click &quot;Run Locked Benchmark Comparison&quot; or load a previous experiment from the &quot;Experiments&quot; tab.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Formal Production Decision & Publication Report */}
      {activeTab === "decision" && (
        <div className="space-y-6">
          {reportData ? (
            <div className="space-y-5">
              {/* Decision Banner Card */}
              <div
                className="p-5 rounded-lg border glass-card"
                style={{
                  borderColor:
                    reportData.decision.status === "PROMOTE_TO_PRODUCTION"
                      ? "#10b981"
                      : reportData.decision.status === "REJECT_REGRESSION"
                      ? "#ef4444"
                      : "#3b82f6",
                  background: "var(--bg-card)",
                }}
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                      Automated Scientific Decision Verdict
                    </span>
                    <h3
                      className="text-lg font-bold mt-0.5"
                      style={{
                        color:
                          reportData.decision.status === "PROMOTE_TO_PRODUCTION"
                            ? "#34d399"
                            : reportData.decision.status === "REJECT_REGRESSION"
                            ? "#f87171"
                            : "#60a5fa",
                      }}
                    >
                      {reportData.decision.status}
                    </h3>
                  </div>

                  <div className="text-right">
                    <span className="text-xs font-mono text-zinc-400">Recommended Profile</span>
                    <div className="text-sm font-bold text-zinc-100 font-mono">
                      {reportData.decision.recommended_profile_id}
                    </div>
                    <span className="text-[10px] text-zinc-400">
                      Confidence: {Math.round(reportData.decision.confidence_score * 100)}%
                    </span>
                  </div>
                </div>

                {/* Evidence Drivers & Risks */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-zinc-800 text-xs">
                  <div>
                    <h5 className="font-semibold text-zinc-300 mb-1.5 uppercase tracking-wider text-[11px]">
                      Key Evidence Drivers
                    </h5>
                    <ul className="space-y-1 text-zinc-400">
                      {reportData.decision.key_evidence_drivers.map((ev, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-emerald-400 font-bold">✓</span>
                          <span>{ev}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h5 className="font-semibold text-zinc-300 mb-1.5 uppercase tracking-wider text-[11px]">
                      Risk Factors &amp; Cautions
                    </h5>
                    {reportData.decision.risk_factors.length > 0 ? (
                      <ul className="space-y-1 text-zinc-400">
                        {reportData.decision.risk_factors.map((rf, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-amber-400 font-bold">⚠</span>
                            <span>{rf}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-zinc-500 italic">No critical risk factors flagged.</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Publication Report Preview & Actions */}
              <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-semibold text-zinc-100">
                      Publication-Grade Markdown Research Report
                    </h4>
                    <p className="text-xs text-zinc-400">
                      Self-contained document for peer review, dataset citations, and audit logs.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCopyMarkdown}
                      className="px-3 py-1.5 text-xs font-semibold rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 transition"
                    >
                      {copiedReport ? "✓ Copied to Clipboard!" : "Copy Markdown"}
                    </button>
                    <button
                      onClick={handleDownloadMarkdown}
                      className="px-3 py-1.5 text-xs font-semibold rounded bg-blue-600 hover:bg-blue-500 text-white transition shadow"
                    >
                      Download .md Artifact
                    </button>
                  </div>
                </div>

                <div className="p-4 rounded bg-black/50 border border-zinc-800 font-mono text-[11px] text-zinc-300 max-h-96 overflow-y-auto whitespace-pre-wrap">
                  {reportData.markdown_content}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-zinc-500 glass-card">
              Run benchmark comparison first to generate automated production decisions and research reports.
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Production Governance & Sign-off */}
      {activeTab === "governance" && (
        <div className="space-y-6">
          {/* Active Production Profile & Version History */}
          <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h4 className="text-sm font-semibold text-zinc-100">
                  Production Profile Registry: [{selectedBenchmarkId}]
                </h4>
                <p className="text-xs text-zinc-400">
                  Versioned baseline profiles certified for active live chart predictions.
                </p>
              </div>
              <button
                onClick={() => fetchProductionProfiles(selectedBenchmarkId)}
                className="px-3 py-1 text-xs rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition"
              >
                Refresh Profiles
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {productionProfiles.map((p) => (
                <div
                  key={`${p.profile_id}-${p.version}`}
                  className="p-4 rounded border bg-black/30"
                  style={{
                    borderColor: p.is_active_baseline ? "#10b981" : "var(--border-primary)",
                  }}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-zinc-100">
                      {p.profile_id} <span className="text-blue-400">v{p.version}</span>
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                        p.is_active_baseline
                          ? "bg-emerald-900/40 text-emerald-300 border border-emerald-800"
                          : "bg-zinc-800 text-zinc-400"
                      }`}
                    >
                      {p.is_active_baseline ? "ACTIVE BASELINE" : "ARCHIVED"}
                    </span>
                  </div>
                  <div className="mt-2 text-xs text-zinc-400 space-y-0.5">
                    <div>Approved By: <span className="text-zinc-200">{p.approved_by ?? "SYSTEM_GENESIS"}</span></div>
                    {p.promoted_from_experiment_id && (
                      <div>Promoted From: <span className="font-mono text-zinc-300">{p.promoted_from_experiment_id}</span></div>
                    )}
                    {p.notes && <div className="text-[11px] text-zinc-500 italic mt-1">{p.notes}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Human Review Sign-Off & Promotion Panel */}
          {comparisonData ? (
            <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h4 className="text-sm font-semibold text-zinc-100">
                    Human Reviewer Sign-Off &amp; Production Promotion
                  </h4>
                  <p className="text-xs text-zinc-400">
                    Active Experiment: <span className="font-mono text-blue-400 font-bold">{comparisonData.experiment_id}</span>
                  </p>
                </div>

                {currentSignoff && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-400">Current Status:</span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded font-bold uppercase ${
                        currentSignoff.status === "APPROVED"
                          ? "bg-emerald-900/40 text-emerald-300 border border-emerald-800"
                          : "bg-red-900/40 text-red-300 border border-red-800"
                      }`}
                    >
                      {currentSignoff.status} (by {currentSignoff.reviewer_id})
                    </span>
                  </div>
                )}
              </div>

              {promotionSuccess && (
                <div className="p-3 rounded text-xs bg-emerald-900/20 text-emerald-300 border border-emerald-800">
                  {promotionSuccess}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">Reviewer Name / Role</label>
                  <input
                    type="text"
                    value={reviewerName}
                    onChange={(e) => setReviewerName(e.target.value)}
                    className="w-full text-xs p-2 rounded bg-black/20"
                    style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
                  />
                </div>

                <div>
                  <label className="block text-xs text-zinc-400 mb-1">Sign-Off Justification / Notes</label>
                  <input
                    type="text"
                    value={signoffNotes}
                    placeholder="Enter peer review justification..."
                    onChange={(e) => setSignoffNotes(e.target.value)}
                    className="w-full text-xs p-2 rounded bg-black/20"
                    style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-zinc-800">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleSignoff("APPROVED")}
                    disabled={submittingSignoff}
                    className="px-4 py-1.5 text-xs font-semibold rounded bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50"
                  >
                    {submittingSignoff ? "Submitting..." : "Approve Experiment"}
                  </button>
                  <button
                    onClick={() => handleSignoff("REJECTED")}
                    disabled={submittingSignoff}
                    className="px-4 py-1.5 text-xs font-semibold rounded bg-red-600 hover:bg-red-500 text-white transition disabled:opacity-50"
                  >
                    Reject Experiment
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleVerifyReproducibility}
                    disabled={verifyingAudit}
                    className="px-3 py-1.5 text-xs font-semibold rounded bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 border border-purple-500/50 transition"
                  >
                    {verifyingAudit ? "Re-running Seed..." : "Verify Bit-for-Bit Reproducibility"}
                  </button>
                  <button
                    onClick={handlePromoteToProduction}
                    disabled={submittingSignoff}
                    className="px-4 py-1.5 text-xs font-semibold rounded bg-blue-600 hover:bg-blue-500 text-white transition shadow disabled:opacity-50"
                  >
                    Promote to Production Baseline (v1.1.0)
                  </button>
                </div>
              </div>

              {/* Reproducibility Audit Result Card */}
              {auditResult && (
                <div className="p-4 rounded bg-black/40 border border-zinc-800 space-y-1.5 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-300 font-bold">Reproducibility Verification Audit</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${auditResult.is_bit_for_bit_identical ? "bg-emerald-900/40 text-emerald-300" : "bg-red-900/40 text-red-300"}`}>
                      {auditResult.is_bit_for_bit_identical ? "100% BIT-FOR-BIT IDENTICAL" : "CHECKSUM MISMATCH"}
                    </span>
                  </div>
                  <div className="text-[11px] text-zinc-400 truncate">Expected SHA: {auditResult.expected_results_hash}</div>
                  <div className="text-[11px] text-zinc-400 truncate">Actual SHA: {auditResult.actual_results_hash}</div>
                  <div className="text-[11px] text-emerald-400 pt-1">{auditResult.audit_notes}</div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-zinc-500 glass-card">
              Run or load an experiment first to review governance and sign-off.
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Continuous Monitoring & Automated Alerts */}
      {activeTab === "monitoring" && (
        <div className="space-y-6">
          {/* Active Regression Alerts Feed */}
          <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h4 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                  <span>Automated Regression Alerts Inbox</span>
                  {unacknowledgedAlerts.length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/80 text-red-200 font-bold animate-pulse">
                      {unacknowledgedAlerts.length} Action Required
                    </span>
                  )}
                </h4>
                <p className="text-xs text-zinc-400">
                  Real-time alerts triggered by continuous benchmark evaluations against active production baselines.
                </p>
              </div>
              <button
                onClick={() => fetchMonitoringData(selectedBenchmarkId)}
                className="px-3 py-1 text-xs rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition"
              >
                Refresh Alerts
              </button>
            </div>

            {alerts.length > 0 ? (
              <div className="space-y-3">
                {alerts.map((al) => (
                  <div
                    key={al.alert_id}
                    className="p-4 rounded border bg-black/30 space-y-2"
                    style={{
                      borderColor: al.severity === "CRITICAL_REGRESSION" ? "#ef4444" : "#f59e0b",
                    }}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${al.severity === "CRITICAL_REGRESSION" ? "bg-red-900/60 text-red-300 border border-red-800" : "bg-amber-900/60 text-amber-300 border border-amber-800"}`}>
                          {al.severity}
                        </span>
                        <span className="text-xs font-semibold text-zinc-100">{al.title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {al.is_acknowledged ? (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono">
                            ✓ ACK by {al.acknowledged_by}
                          </span>
                        ) : (
                          <button
                            onClick={() => handleAcknowledgeAlert(al.alert_id)}
                            className="px-2.5 py-0.5 text-[10px] font-semibold rounded bg-blue-600/40 text-blue-200 hover:bg-blue-600/60 border border-blue-500/50 transition"
                          >
                            Acknowledge Alert
                          </button>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-zinc-400">{al.description}</p>
                    <div className="flex flex-wrap items-center gap-4 text-[11px] text-zinc-500 font-mono pt-1">
                      <div>Experiment: <span className="text-blue-400">{al.experiment_id}</span></div>
                      {al.metrics_impact && Object.keys(al.metrics_impact).length > 0 && (
                        <div>Metrics Impact: <span className="text-zinc-300">{JSON.stringify(al.metrics_impact)}</span></div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-zinc-500 bg-black/20 rounded">
                ✓ No active regression alerts. All predictive profiles within safe baseline thresholds.
              </div>
            )}
          </div>

          {/* Continuous Benchmark Schedules */}
          <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h4 className="text-sm font-semibold text-zinc-100">
                  Continuous Benchmark Evaluation Schedules
                </h4>
                <p className="text-xs text-zinc-400">
                  Configured recurring benchmark jobs executing baseline regression guardrails.
                </p>
              </div>
              <button
                onClick={handleScanCorpusChanges}
                className="px-3 py-1.5 text-xs rounded bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 border border-purple-500/50 transition"
              >
                Scan &amp; Detect Corpus Changes
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {schedules.map((sc) => (
                <div key={sc.schedule_id} className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-blue-400">{sc.benchmark_id}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${sc.is_active ? "bg-emerald-900/40 text-emerald-300 border border-emerald-800" : "bg-zinc-800 text-zinc-400"}`}>
                      {sc.is_active ? "ACTIVE (DAILY)" : "PAUSED"}
                    </span>
                  </div>
                  <div className="text-xs text-zinc-400 space-y-0.5">
                    <div>Tolerance Window: <span className="text-zinc-200 font-mono">±{sc.tolerance_days}d</span> | Seed: <span className="font-mono text-zinc-200">{sc.split_seed}</span></div>
                    <div>Last Run: <span className="text-zinc-300">{sc.last_run_at ? new Date(sc.last_run_at).toLocaleString() : "Never"}</span></div>
                  </div>
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => handleTriggerSchedule(sc.schedule_id)}
                      disabled={triggeringSchedule === sc.schedule_id}
                      className="px-3 py-1 text-xs font-semibold rounded bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-50"
                    >
                      {triggeringSchedule === sc.schedule_id ? "Running Daemon..." : "Trigger Scheduled Run Now"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Newly Detected Corpus Changes */}
          {corpusEvents.length > 0 && (
            <div className="glass-card p-5 rounded-lg space-y-3" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <h4 className="text-sm font-semibold text-zinc-100">
                Corpus Version Watcher Scan Results
              </h4>
              <div className="space-y-2">
                {corpusEvents.map((evt) => (
                  <div key={evt.benchmark_id} className="p-3 rounded bg-black/40 border border-zinc-800 text-xs flex items-center justify-between">
                    <div>
                      <span className="font-mono font-bold text-blue-400">{evt.benchmark_id}</span> (v{evt.detected_version})
                      <div className="text-[11px] text-zinc-400 font-mono truncate max-w-md">SHA-256: {evt.content_hash_sha256}</div>
                    </div>
                    <div className="text-right text-zinc-300">
                      <div>Verified Records: <span className="font-bold text-zinc-100">{evt.verified_events_count}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Governance & Monitoring Audit Log Explorer */}
          <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
            <h4 className="text-sm font-semibold text-zinc-100">
              Governance &amp; Continuous Monitoring Audit Log
            </h4>
            <p className="text-xs text-zinc-400">
              Immutable chronological record of scheduled executions, regressions, promotions, and human sign-offs.
            </p>

            <div className="overflow-x-auto max-h-80 overflow-y-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[10px]">
                    <th className="p-2">Timestamp</th>
                    <th className="p-2">Event Type</th>
                    <th className="p-2">Benchmark</th>
                    <th className="p-2">Actor</th>
                    <th className="p-2">Experiment / Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.audit_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/20 font-mono text-[11px]">
                      <td className="p-2 text-zinc-400 whitespace-nowrap">{new Date(log.timestamp).toLocaleTimeString()}</td>
                      <td className="p-2 font-semibold text-zinc-200">
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300">
                          {log.event_type}
                        </span>
                      </td>
                      <td className="p-2 text-blue-400 font-bold">{log.benchmark_id}</td>
                      <td className="p-2 text-zinc-300">{log.actor}</td>
                      <td className="p-2 text-zinc-400 truncate max-w-xs" title={JSON.stringify(log.details)}>
                        {log.experiment_id ? `[${log.experiment_id}] ` : ""}{JSON.stringify(log.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 6: Benchmark Intelligence & Descriptive Trends */}
      {activeTab === "trends" && (
        <div className="space-y-6">
          {intelligenceReport ? (
            <div className="space-y-6">
              {/* System Stability & Reliability KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-black/40 border border-blue-500/40 glass-card">
                  <span className="text-[10px] font-mono uppercase text-zinc-400">System Stability Index</span>
                  <div className="text-2xl font-bold font-mono text-blue-400 mt-1">
                    {Math.round(intelligenceReport.stability.composite_stability_index * 100)}%
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-1 font-mono">
                    Score: {intelligenceReport.stability.composite_stability_index} / 1.0
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-black/40 border border-zinc-800 glass-card">
                  <span className="text-[10px] font-mono uppercase text-zinc-400">Historical Evaluations</span>
                  <div className="text-2xl font-bold font-mono text-zinc-100 mt-1">
                    {intelligenceReport.total_experiments}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-1">
                    Across locked holdout splits
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-black/40 border border-zinc-800 glass-card">
                  <span className="text-[10px] font-mono uppercase text-zinc-400">Regression-Free Ratio</span>
                  <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                    {Math.round(intelligenceReport.stability.regression_free_runs_ratio * 100)}%
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-1">
                    Runs meeting baseline thresholds
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-black/40 border border-zinc-800 glass-card">
                  <span className="text-[10px] font-mono uppercase text-zinc-400">Metric Variance (Std Dev)</span>
                  <div className="text-sm font-bold font-mono text-amber-300 mt-1">
                    σ(Hit) = ±{intelligenceReport.stability.std_hit_rate}%
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-0.5 font-mono">
                    σ(Brier) = ±{intelligenceReport.stability.std_brier}
                  </div>
                </div>
              </div>

              {/* Mathematical Stability Formula Banner */}
              <div className="p-4 rounded bg-black/30 border border-zinc-800 text-xs text-zinc-400 space-y-1 font-mono">
                <div className="text-zinc-200 font-bold uppercase text-[11px]">
                  Mathematical Formulation: System Stability Index
                </div>
                <div>
                  Stability Index = 0.40 × S_hit ({intelligenceReport.stability.hit_rate_stability_component}) + 0.30 × S_brier ({intelligenceReport.stability.brier_stability_component}) + 0.30 × S_clean ({intelligenceReport.stability.regression_free_component}) = <span className="text-blue-400 font-bold">{intelligenceReport.stability.composite_stability_index}</span>
                </div>
                <div className="text-[10px] text-zinc-500 italic pt-1">
                  Note: Analytics are purely descriptive and observational. They summarize empirical performance without asserting causality.
                </div>
              </div>

              {/* Profile Evolution & Summary Statistics Grid */}
              <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <h4 className="text-sm font-semibold text-zinc-100">
                  Descriptive Profile Performance Summary
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.values(intelligenceReport.profile_summaries).map((ps) => (
                    <div key={ps.profile_id} className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-zinc-200 font-mono">{ps.profile_name}</span>
                        <span className="text-[10px] font-mono text-zinc-400">{ps.total_evaluations} evaluations</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 pt-2 text-center font-mono">
                        <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                          <div className="text-[10px] text-zinc-400 uppercase">Mean Hit Rate</div>
                          <div className="text-sm font-bold text-emerald-400 mt-0.5">{ps.mean_hit_rate_pct}%</div>
                          <div className="text-[9px] text-zinc-500">σ = ±{ps.std_hit_rate_pct}%</div>
                        </div>
                        <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                          <div className="text-[10px] text-zinc-400 uppercase">Mean Brier</div>
                          <div className="text-sm font-bold text-amber-300 mt-0.5">{ps.mean_brier_score}</div>
                          <div className="text-[9px] text-zinc-500">σ = ±{ps.std_brier_score}</div>
                        </div>
                        <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                          <div className="text-[10px] text-zinc-400 uppercase">Mean MAE</div>
                          <div className="text-sm font-bold text-blue-400 mt-0.5">{ps.mean_mae_days}d</div>
                          <div className="text-[9px] text-zinc-500">F1: {ps.mean_f1_score}</div>
                        </div>
                      </div>
                      <div className="text-[10px] text-zinc-400 pt-1 flex justify-between font-mono">
                        <span>Range: [{ps.min_hit_rate_pct}% – {ps.max_hit_rate_pct}%]</span>
                        <span>Brier Range: [{ps.min_brier_score} – {ps.max_brier_score}]</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Longitudinal Performance Trajectory Table */}
              <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <h4 className="text-sm font-semibold text-zinc-100">
                  Longitudinal Observational Trajectory
                </h4>
                <p className="text-xs text-zinc-400">
                  Chronological record of empirical holdout metrics observed across historical benchmark runs.
                </p>

                <div className="overflow-x-auto max-h-80 overflow-y-auto">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[10px]">
                        <th className="p-2">Run ID</th>
                        <th className="p-2">Profile</th>
                        <th className="p-2 text-center">Tol</th>
                        <th className="p-2 text-center">Seed</th>
                        <th className="p-2 text-center">Hit Rate %</th>
                        <th className="p-2 text-center">Brier</th>
                        <th className="p-2 text-center">MAE</th>
                        <th className="p-2 text-center">Δ Hit</th>
                        <th className="p-2 text-center">Δ Brier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.values(intelligenceReport.profile_summaries).flatMap((ps) =>
                        ps.trajectory.map((pt) => (
                          <tr key={`${pt.experiment_id}-${pt.profile_id}`} className="border-b border-zinc-800/50 hover:bg-zinc-800/20 font-mono text-[11px]">
                            <td className="p-2 text-blue-400 font-bold">{pt.experiment_id.slice(-10)}</td>
                            <td className="p-2 text-zinc-200">{pt.profile_id}</td>
                            <td className="p-2 text-center text-zinc-400">±{pt.tolerance_days}d</td>
                            <td className="p-2 text-center text-zinc-400">{pt.split_seed}</td>
                            <td className="p-2 text-center font-bold text-emerald-400">{pt.holdout_hit_rate_pct}%</td>
                            <td className="p-2 text-center text-amber-300">{pt.holdout_brier_score}</td>
                            <td className="p-2 text-center text-zinc-300">{pt.holdout_mae_days}d</td>
                            <td className="p-2 text-center">
                              <span className={pt.delta_hit_rate_pct >= 0 ? "text-emerald-400" : "text-red-400"}>
                                {pt.delta_hit_rate_pct >= 0 ? `+${pt.delta_hit_rate_pct}` : pt.delta_hit_rate_pct}%
                              </span>
                            </td>
                            <td className="p-2 text-center">
                              <span className={pt.delta_brier_score <= 0 ? "text-emerald-400" : "text-red-400"}>
                                {pt.delta_brier_score}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Corpus Demographic & Quality Composition */}
              <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <h4 className="text-sm font-semibold text-zinc-100">
                  Corpus Quality &amp; Demographic Composition: [{intelligenceReport.corpus_demographics.benchmark_id}]
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2 text-xs">
                    <div className="font-bold text-zinc-300 uppercase text-[11px]">Rodden Rating Distribution</div>
                    <div className="space-y-1 pt-1 font-mono">
                      {Object.entries(intelligenceReport.corpus_demographics.birth_confidence_distribution).map(([rating, count]) => (
                        <div key={rating} className="flex justify-between text-zinc-300">
                          <span>Grade {rating}:</span>
                          <span className="font-bold text-blue-400">{count} events ({Math.round((count / intelligenceReport.corpus_demographics.total_verified_events) * 100)}%)</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2 text-xs">
                    <div className="font-bold text-zinc-300 uppercase text-[11px]">Event Date Precision</div>
                    <div className="space-y-1 pt-1 font-mono">
                      {Object.entries(intelligenceReport.corpus_demographics.date_confidence_distribution).map(([dconf, count]) => (
                        <div key={dconf} className="flex justify-between text-zinc-300">
                          <span>{dconf}:</span>
                          <span className="font-bold text-emerald-400">{count} events</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2 text-xs">
                    <div className="font-bold text-zinc-300 uppercase text-[11px]">Source Verification</div>
                    <div className="space-y-1 pt-1 font-mono">
                      {Object.entries(intelligenceReport.corpus_demographics.event_verification_distribution).map(([vtype, count]) => (
                        <div key={vtype} className="flex justify-between text-zinc-300">
                          <span>{vtype}:</span>
                          <span className="font-bold text-purple-400">{count} events</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-zinc-500 glass-card">
              {loadingIntelligence ? "Loading intelligence report &amp; trend analytics..." : "Run benchmark comparison first to generate trend analytics."}
            </div>
          )}
        </div>
      )}

      {/* Tab 7: Statistical Significance & Confidence Analysis */}
      {activeTab === "significance" && (
        <div className="space-y-4">
          {significanceData && significanceData.reports.length > 0 ? (
            <div className="space-y-4">
              {significanceData.reports.map((rep) => (
                <div key={rep.profile_id} className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <h4 className="text-sm font-semibold text-zinc-100">
                        Inferential Significance: [{rep.profile_id}] vs [{rep.baseline_profile_id}]
                      </h4>
                      <p className="text-xs text-zinc-400">
                        Paired hypothesis testing &amp; B=1000 empirical bootstrap resampling on identical locked holdout partition.
                      </p>
                    </div>
                    <span className={`text-xs px-3 py-1 rounded font-bold uppercase ${rep.verdict === "STATISTICALLY_SIGNIFICANT_SUPERIOR" ? "bg-emerald-900/40 text-emerald-300 border border-emerald-800" : "bg-zinc-800 text-zinc-400"}`}>
                      {rep.verdict}
                    </span>
                  </div>

                  {/* McNemar & Permutation Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2">
                      <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">McNemar's Exact Paired Test</div>
                      <div className="text-lg font-mono font-bold text-blue-400">
                        p = {rep.mcnemar_test.p_value}
                      </div>
                      <div className="text-xs text-zinc-400">
                        Odds Ratio: <span className="text-zinc-200 font-bold">{rep.mcnemar_test.odds_ratio}</span> | Chi-sq: <span className="font-mono">{rep.mcnemar_test.statistic}</span>
                      </div>
                      <div className="pt-2 text-[11px] text-zinc-400 border-t border-zinc-800/80">
                        Discordant Pairs: Baseline-only = {rep.mcnemar_test.b_discordant_baseline_only}, Candidate-only = {rep.mcnemar_test.c_discordant_candidate_only}
                      </div>
                    </div>

                    <div className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2">
                      <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">2000-Permutation Brier Test</div>
                      <div className="text-lg font-mono font-bold text-purple-400">
                        p = {rep.brier_permutation_p_value}
                      </div>
                      <div className="text-xs text-zinc-400">
                        Δ Brier Score: <span className="font-mono text-zinc-200">{rep.delta_brier_score}</span>
                      </div>
                      <div className="pt-2 text-[11px] text-zinc-400 border-t border-zinc-800/80">
                        Tests H0: No probabilistic calibration advantage
                      </div>
                    </div>

                    <div className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2">
                      <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">2x2 Paired Contingency Matrix</div>
                      <div className="grid grid-cols-2 gap-1 text-center font-mono text-xs pt-1">
                        <div className="p-1.5 rounded bg-zinc-900 border border-zinc-800" title="Both Hit">
                          Both Hit: <span className="text-emerald-400 font-bold">{rep.mcnemar_test.contingency_table[0]}</span>
                        </div>
                        <div className="p-1.5 rounded bg-zinc-900 border border-zinc-800" title="Base Hit, Cand Miss">
                          Base Only: <span className="text-amber-400 font-bold">{rep.mcnemar_test.contingency_table[1]}</span>
                        </div>
                        <div className="p-1.5 rounded bg-zinc-900 border border-zinc-800" title="Base Miss, Cand Hit">
                          Cand Only: <span className="text-blue-400 font-bold">{rep.mcnemar_test.contingency_table[2]}</span>
                        </div>
                        <div className="p-1.5 rounded bg-zinc-900 border border-zinc-800" title="Both Missed">
                          Both Miss: <span className="text-zinc-400 font-bold">{rep.mcnemar_test.contingency_table[3]}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Bootstrap 95% Confidence Intervals */}
                  {rep.bootstrap_cis && Object.keys(rep.bootstrap_cis).length > 0 && (
                    <div className="mt-4 pt-3 border-t border-zinc-800 space-y-2">
                      <h5 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                        1000-Iteration Empirical Bootstrap 95% Confidence Intervals
                      </h5>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {Object.entries(rep.bootstrap_cis).map(([key, ci]) => (
                          <div key={key} className="p-3 rounded bg-black/40 border border-zinc-800">
                            <div className="text-[11px] text-zinc-400 uppercase font-medium">{ci.metric_name}</div>
                            <div className="text-sm font-bold text-zinc-100 mt-0.5">
                              {ci.point_estimate} {key.includes("pct") ? "%" : key.includes("days") ? "days" : ""}
                            </div>
                            <div className="text-[10px] font-mono text-blue-400 mt-1">
                              95% CI: [{ci.ci_lower}, {ci.ci_upper}] (SE: {ci.standard_error})
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-zinc-500 glass-card">
              Run benchmark comparison first to compute inferential significance tests and bootstrap confidence intervals.
            </div>
          )}
        </div>
      )}

      {/* Tab 8: Reliability Diagrams & Calibration Curves */}
      {activeTab === "reliability" && (
        <div className="space-y-4">
          {curveData ? (
            <div className="glass-card p-5 rounded-lg" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <div>
                  <h4 className="text-sm font-semibold text-zinc-100">
                    Reliability Diagram &amp; Calibration Pools: [{curveData.profile_id}]
                  </h4>
                  <p className="text-xs text-zinc-400">
                    Observed empirical hit rates vs predicted probability bins with Wilson 95% confidence intervals.
                  </p>
                </div>
                <div className="text-xs font-mono text-amber-400">
                  Holdout Brier Score: {curveData.brier_score}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {curveData.bins.map((bin) => (
                  <div key={bin.score_range} className="p-3.5 rounded bg-black/30 border border-zinc-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-blue-400">Score [{bin.score_range}]</span>
                      <span className="text-[10px] font-mono text-zinc-400">N = {bin.sample_size_n}</span>
                    </div>
                    <div className="text-lg font-bold text-zinc-100">
                      {bin.empirical_hit_rate_pct}% <span className="text-xs font-normal text-zinc-400">observed</span>
                    </div>
                    <div className="text-[10px] text-zinc-400 font-mono">
                      Wilson 95% CI: [{Math.round(bin.rate_ci_95[0] * 100)}%, {Math.round(bin.rate_ci_95[1] * 100)}%]
                    </div>
                    {bin.has_small_n_warning && (
                      <div className="text-[10px] text-amber-400 font-semibold">
                        ⚠ Small-N Warning (N &lt; 30)
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-zinc-500 glass-card">
              Run benchmark comparison or load an experiment first to inspect calibration curves.
            </div>
          )}
        </div>
      )}

      {/* Tab 9: Timing Accuracy & Error Offsets */}
      {activeTab === "timing" && (
        <div className="space-y-4">
          {comparisonData ? (
            <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <h4 className="text-sm font-semibold text-zinc-100">
                Timing Distribution &amp; Offset Accuracy
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {comparisonData.rows.map((r) => (
                  <div key={r.profile_id} className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2">
                    <div className="font-semibold text-xs text-zinc-200">{r.profile_name}</div>
                    <div className="grid grid-cols-3 gap-2 text-center pt-2">
                      <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                        <div className="text-[10px] uppercase text-zinc-400">MAE Peak</div>
                        <div className="text-sm font-bold text-zinc-100 mt-1">{r.holdout_mae_peak_days}d</div>
                      </div>
                      <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                        <div className="text-[10px] uppercase text-zinc-400">Median Offset</div>
                        <div className="text-sm font-bold text-blue-400 mt-1">{r.holdout_median_peak_offset_days}d</div>
                      </div>
                      <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                        <div className="text-[10px] uppercase text-zinc-400">P90 Tail</div>
                        <div className="text-sm font-bold text-amber-400 mt-1">{r.holdout_p90_peak_offset_days}d</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-zinc-500 glass-card">
              Run benchmark comparison first to inspect timing accuracy.
            </div>
          )}
        </div>
      )}

      {/* Tab 10: QC Rejection & Audit Log */}
      {activeTab === "audit" && (
        <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
          <h4 className="text-sm font-semibold text-zinc-100">
            Quality Control &amp; Rejection Audit Policy
          </h4>
          <p className="text-xs text-zinc-400">
            AstroOS enforces a strict audit trail. Zero research records are silently dropped.
          </p>
          <div className="p-4 rounded bg-black/30 border border-zinc-800 space-y-2 text-xs text-zinc-300">
            <div className="flex items-center gap-2">
              <span className="text-emerald-400 font-bold">✓ HARD_DUPLICATE_COLLISION:</span> Rejects identical coordinate + timestamp + subject collision.
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-400 font-bold">✓ CONFLICTING_RECORD_COLLISION:</span> Rejects same subject/event with differing birth data.
            </div>
            <div className="flex items-center gap-2">
              <span className="text-blue-400 font-bold">✓ POSSIBLE_DUPLICATE_WARNING:</span> Flags events within 30 days for subject review without rejection.
            </div>
          </div>
        </div>
      )}

      {/* Tab 11: Persisted Experiments History, Diffing & Provenance */}
      {activeTab === "experiments" && (
        <div className="space-y-6">
          {/* Persisted Experiment Runs Table */}
          <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h4 className="text-sm font-semibold text-zinc-100">
                  Archived Benchmark Experiments: [{selectedBenchmarkId}]
                </h4>
                <p className="text-xs text-zinc-400">
                  Durable experiment runs stored in PostgreSQL with locked seeds, split IDs, and results SHA-256 hashes.
                </p>
              </div>
              <button
                onClick={() => fetchExperimentHistory(selectedBenchmarkId)}
                className="px-3 py-1 text-xs rounded bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition"
              >
                {loadingHistory ? "Refreshing..." : "Refresh History"}
              </button>
            </div>

            {experiments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[10px]">
                      <th className="p-2">Experiment ID</th>
                      <th className="p-2 text-center">Status</th>
                      <th className="p-2 text-center">Seed</th>
                      <th className="p-2 text-center">Tolerance</th>
                      <th className="p-2 text-center">Profiles</th>
                      <th className="p-2 text-center">Duration</th>
                      <th className="p-2 text-center">Results Hash</th>
                      <th className="p-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {experiments.map((exp) => (
                      <tr key={exp.experiment_id} className="border-b border-zinc-800/50 hover:bg-zinc-800/20">
                        <td className="p-2 font-mono font-semibold text-blue-400">{exp.experiment_id}</td>
                        <td className="p-2 text-center">
                          <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-emerald-900/40 text-emerald-300 border border-emerald-800">
                            {exp.status}
                          </span>
                        </td>
                        <td className="p-2 text-center font-mono">{exp.split_seed}</td>
                        <td className="p-2 text-center font-mono">±{exp.tolerance_days}d</td>
                        <td className="p-2 text-center font-mono text-zinc-300">{exp.profile_ids.length}</td>
                        <td className="p-2 text-center font-mono">{exp.duration_ms}ms</td>
                        <td className="p-2 text-center font-mono text-[10px] text-zinc-400 truncate max-w-[120px]" title={exp.results_hash_sha256}>
                          {exp.results_hash_sha256.slice(0, 12)}...
                        </td>
                        <td className="p-2 text-right">
                          <button
                            onClick={() => handleLoadExperiment(exp.experiment_id)}
                            className="px-2.5 py-1 text-[11px] font-semibold rounded bg-blue-600/30 text-blue-300 hover:bg-blue-600/50 border border-blue-500/50 transition"
                          >
                            Open Run
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-zinc-500">
                No archived experiments found for this benchmark. Run a benchmark comparison to persist an experiment.
              </div>
            )}
          </div>

          {/* Experiment Run Diffing Tool */}
          {experiments.length >= 2 && (
            <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <h4 className="text-sm font-semibold text-zinc-100">
                Compare Two Benchmark Runs (Run Diffing)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">Baseline Run (A)</label>
                  <select
                    value={diffRunA}
                    onChange={(e) => setDiffRunA(e.target.value)}
                    className="w-full text-xs p-2 rounded bg-black/20"
                    style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
                  >
                    <option value="">Select Run A</option>
                    {experiments.map((e) => (
                      <option key={e.experiment_id} value={e.experiment_id}>
                        {e.experiment_id} (Tol: ±{e.tolerance_days}d, Seed: {e.split_seed})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-zinc-400 mb-1">Comparison Run (B)</label>
                  <select
                    value={diffRunB}
                    onChange={(e) => setDiffRunB(e.target.value)}
                    className="w-full text-xs p-2 rounded bg-black/20"
                    style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
                  >
                    <option value="">Select Run B</option>
                    {experiments.map((e) => (
                      <option key={e.experiment_id} value={e.experiment_id}>
                        {e.experiment_id} (Tol: ±{e.tolerance_days}d, Seed: {e.split_seed})
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={handleLoadDiffRuns}
                  disabled={!diffRunA || !diffRunB}
                  className="px-4 py-2 text-xs font-semibold rounded bg-purple-600 hover:bg-purple-500 text-white transition disabled:opacity-50"
                >
                  Compare Runs Side-by-Side
                </button>
              </div>

              {diffDataA && diffDataB && (
                <div className="mt-4 pt-4 border-t border-zinc-800 overflow-x-auto">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[10px]">
                        <th className="p-2">Metric</th>
                        <th className="p-2 text-center">Run A ({diffDataA.experiment_id.slice(-8)})</th>
                        <th className="p-2 text-center">Run B ({diffDataB.experiment_id.slice(-8)})</th>
                        <th className="p-2 text-center">Variance / Delta (B - A)</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-zinc-800/50">
                        <td className="p-2 font-medium text-zinc-300">Tolerance Window</td>
                        <td className="p-2 text-center font-mono">±{diffDataA.tolerance_days}d</td>
                        <td className="p-2 text-center font-mono">±{diffDataB.tolerance_days}d</td>
                        <td className="p-2 text-center font-mono text-zinc-400">{diffDataB.tolerance_days - diffDataA.tolerance_days}d</td>
                      </tr>
                      <tr className="border-b border-zinc-800/50">
                        <td className="p-2 font-medium text-zinc-300">Partition Seed</td>
                        <td className="p-2 text-center font-mono">{diffDataA.split_seed}</td>
                        <td className="p-2 text-center font-mono">{diffDataB.split_seed}</td>
                        <td className="p-2 text-center font-mono text-zinc-400">{diffDataA.split_seed === diffDataB.split_seed ? "SAME" : "DIFFERENT"}</td>
                      </tr>
                      {diffDataA.rows.map((rowA) => {
                        const rowB = diffDataB.rows.find((r) => r.profile_id === rowA.profile_id);
                        if (!rowB) return null;
                        const dHit = roundDiff(rowB.holdout_hit_rate_pct - rowA.holdout_hit_rate_pct);
                        const dBrier = roundDiff(rowB.holdout_brier_score - rowA.holdout_brier_score, 4);
                        return (
                          <tr key={rowA.profile_id} className="border-b border-zinc-800/50 bg-black/20">
                            <td className="p-2 font-semibold text-blue-400">[{rowA.profile_name}] Hit Rate / Brier</td>
                            <td className="p-2 text-center font-mono">{rowA.holdout_hit_rate_pct}% / {rowA.holdout_brier_score}</td>
                            <td className="p-2 text-center font-mono">{rowB.holdout_hit_rate_pct}% / {rowB.holdout_brier_score}</td>
                            <td className="p-2 text-center font-mono font-bold">
                              <span className={dHit >= 0 ? "text-emerald-400" : "text-red-400"}>{dHit >= 0 ? `+${dHit}` : dHit}%</span> |{" "}
                              <span className={dBrier <= 0 ? "text-emerald-400" : "text-red-400"}>{dBrier}</span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Active Experiment Provenance Card */}
          {comparisonData && (
            <div className="glass-card p-5 rounded-lg space-y-4" style={{ background: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-zinc-100">
                  Active Experiment Provenance &amp; Cryptographic Checksums
                </h4>
                <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-emerald-900/40 text-emerald-300 border border-emerald-800">
                  VERIFIED_REPRODUCIBLE
                </span>
              </div>
              <div className="p-4 rounded bg-black/40 border border-zinc-800 space-y-2 font-mono text-xs text-zinc-300">
                <div>Experiment ID: <span className="text-blue-400 font-bold">{comparisonData.experiment_id}</span></div>
                <div>Benchmark Corpus: <span className="text-zinc-100">{comparisonData.benchmark_id} v{comparisonData.benchmark_version}</span></div>
                <div>Dataset Content SHA-256: <span className="text-zinc-400 break-all">{comparisonData.content_hash_sha256}</span></div>
                <div>Partition Seed: <span className="text-zinc-100">{comparisonData.split_seed}</span></div>
                <div>Train / Holdout Ratio: <span className="text-zinc-100">{Math.round(comparisonData.split_train_ratio * 100)}% / {Math.round((1 - comparisonData.split_train_ratio) * 100)}%</span></div>
                <div>Tolerance Window: <span className="text-zinc-100">±{comparisonData.tolerance_days} days</span></div>
                <div>Events Count: <span className="text-zinc-100">Train: {comparisonData.train_events_count}, Holdout: {comparisonData.holdout_events_count} (Total: {comparisonData.total_benchmark_events})</span></div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function roundDiff(num: number, dec: number = 1): number {
  const factor = Math.pow(10, dec);
  return Math.round(num * factor) / factor;
}
