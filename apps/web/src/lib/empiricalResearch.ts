/**
 * AstroOS — Empirical Research Engine Client Library
 *
 * Provides API clients and statistical formatting helpers for:
 * 1. Benchmark & custom cohort dataset sweeps
 * 2. Pre-registered classical Jyotish hypothesis testing
 * 3. Exact 2x2 contingency tables, Odds Ratios, Relative Risk, Yates Chi2, Fisher's Exact, FDR q-values
 */

import { api } from "@/lib/api";

export interface AstrologicalExposureRule {
  rule_type: string;
  parameters: Record<string, unknown>;
  description?: string;
}

export interface HypothesisDefinition {
  id: string;
  title: string;
  category: string;
  exposure_rule: AstrologicalExposureRule;
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
  verdict: "CONFIRMED_SIGNIFICANT" | "TREND_SUGGESTIVE" | "NULL_INSUFFICIENT_EVIDENCE" | "INVERSE_CORRELATION";
  audit_trace: string[];
}

export interface BenchmarkCohortDataset {
  cohort_id: string;
  title: string;
  description: string;
  sample_size: number;
  rodden_rating: string;
  target_outcomes: string[];
  records: Array<Record<string, unknown>>;
}

export interface CohortSweepResponse {
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
  epistemological_disclaimer: string;
}

export async function fetchBenchmarkDatasets(): Promise<BenchmarkCohortDataset[]> {
  const res = await api.get<{ total_datasets: number; datasets: BenchmarkCohortDataset[] }>(
    "/api/v1/research/sweeps/benchmark-datasets"
  );
  return res.datasets || [];
}

export async function fetchStandardHypotheses(): Promise<HypothesisDefinition[]> {
  const res = await api.get<{ total_count: number; hypotheses: HypothesisDefinition[] }>(
    "/api/v1/research/sweeps/standard-hypotheses"
  );
  return res.hypotheses || [];
}

export async function runCohortSweep(payload: {
  cohort_id?: string;
  cohort_tag?: string;
  cohort_records?: Array<Record<string, unknown>>;
  hypothesis_ids?: string[];
  category?: string;
  nominal_alpha?: number;
}): Promise<CohortSweepResponse> {
  return api.post<CohortSweepResponse>("/api/v1/research/sweeps/cohort-sweep", payload);
}

export function exportResultsToCsv(sweep: CohortSweepResponse): string {
  const headers = [
    "Hypothesis ID",
    "Title",
    "Category",
    "Sample Size (N)",
    "Exposed Cases (a)",
    "Exposed Controls (b)",
    "Unexposed Cases (c)",
    "Unexposed Controls (d)",
    "Odds Ratio",
    "OR 95% CI Lower",
    "OR 95% CI Upper",
    "Relative Risk",
    "Yates Chi2 Stat",
    "Chi2 p-value",
    "Fisher Exact p-value",
    "FDR q-value",
    "FDR Significant",
    "Bonferroni Significant",
    "Cohen w Effect Size",
    "Verdict",
    "Classical Reference",
  ];

  const rows = sweep.results.map((r) => [
    `"${r.hypothesis.id}"`,
    `"${r.hypothesis.title.replace(/"/g, '""')}"`,
    `"${r.hypothesis.category}"`,
    r.sample_size_n,
    r.contingency_table.a_exposed_cases,
    r.contingency_table.b_exposed_controls,
    r.contingency_table.c_unexposed_cases,
    r.contingency_table.d_unexposed_controls,
    r.odds_ratio.toFixed(3),
    r.odds_ratio_ci_lower.toFixed(3),
    r.odds_ratio_ci_upper.toFixed(3),
    r.relative_risk.toFixed(3),
    r.chi_square_stat.toFixed(3),
    r.chi_square_p_value.toExponential(3),
    r.fisher_exact_p_value.toExponential(3),
    r.fdr_q_value.toExponential(3),
    r.is_significant_fdr ? "YES" : "NO",
    r.is_significant_bonferroni ? "YES" : "NO",
    r.cohen_w_effect_size.toFixed(3),
    `"${r.verdict}"`,
    `"${(r.hypothesis.classical_reference || "N/A").replace(/"/g, '""')}"`,
  ]);

  return [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
}
