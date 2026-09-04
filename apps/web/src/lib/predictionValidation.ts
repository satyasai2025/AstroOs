/**
 * AstroOS — Prediction Validation API Client & TypeScript Types (Module 22, Priority 7)
 */

import { api } from "@/lib/api";

export type PredictionCategory =
  | "career"
  | "marriage"
  | "finance"
  | "health"
  | "relocation"
  | "education"
  | "spiritual"
  | "general";

export type OutcomeStatus = "UNVERIFIED" | "VERIFIED_HISTORICAL" | "OBSERVED_PROSPECTIVE";

export type ValidationVerdict =
  | "MATCHED"
  | "PARTIALLY_MATCHED"
  | "MISSED"
  | "CONTRADICTED"
  | "INCONCLUSIVE"
  | "UNRESOLVED";

export type TemporalSplitType = "RESEARCH_TRAIN" | "VALIDATION" | "TEST_OUT_OF_SAMPLE";

export interface PredictionItem {
  prediction_id: string;
  chart_id: string;
  subject_name: string;
  technique: string;
  category: PredictionCategory;
  predicted_event: string;
  expected_direction: string;
  prediction_timestamp: string;
  horizon_days: number;
  expected_date_start: string;
  expected_date_end: string;
  evidence_ids: string[];
  evidence_hash: string;
  engine_version: string;
}

export interface OutcomeItem {
  outcome_id: string;
  chart_id: string;
  subject_name: string;
  category: PredictionCategory;
  observed_date: string;
  actual_outcome_description: string;
  observed_direction: string;
  verification_status: OutcomeStatus;
  source_reference: string;
  notes: string;
  outcome_hash: string;
}

export interface MatchResult {
  match_id: string;
  prediction_id: string;
  outcome_id?: string;
  verdict: ValidationVerdict;
  category_matched: boolean;
  temporal_error_days?: number;
  direction_matched: boolean;
  predicate_traces: string[];
  evidence_provenance_ids: string[];
}

export interface ConfusionMatrixData {
  true_positive: number;
  false_positive: number;
  true_negative: number;
  false_negative: number;
  total: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
}

export interface BacktestRun {
  backtest_id: string;
  dataset_name: string;
  technique_filter?: string;
  category_filter?: string;
  temporal_split: TemporalSplitType;
  total_predictions: number;
  resolved_predictions: number;
  unresolved_predictions: number;
  matched_count: number;
  partial_count: number;
  missed_count: number;
  contradicted_count: number;
  inconclusive_count: number;
  hit_rate: number;
  confusion_matrix: ConfusionMatrixData;
  confidence_interval_95: number[];
  temporal_leakage_detected: boolean;
  leakage_reasons: string[];
  result_hash: string;
  evaluations: MatchResult[];
}

export interface TechniqueSummary {
  technique: string;
  total_predictions: number;
  resolved_predictions: number;
  matched_count: number;
  partial_count: number;
  missed_count: number;
  contradicted_count: number;
  hit_rate: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  ci_95_low: number;
  ci_95_high: number;
}

export interface PredictionAuditTrail {
  prediction: {
    prediction_id: string;
    subject_name: string;
    technique: string;
    category: string;
    predicted_event: string;
    expected_direction: string;
    prediction_timestamp: string;
    expected_date_start: string;
    expected_date_end: string;
    evidence_hash: string;
    engine_version: string;
  };
  evidence_snapshot: {
    evidence_ids: string[];
    dasha: Record<string, any>;
    transit: Record<string, any>;
    kp: Record<string, any>;
    sbc: Record<string, any>;
    classical: Record<string, any>;
    varga: Record<string, any>;
    ashtakavarga: Record<string, any>;
  };
  outcome?: {
    outcome_id?: string;
    observed_date?: string;
    actual_outcome?: string;
    verification_status?: string;
    source?: string;
    outcome_hash?: string;
  };
  verdict_trace: {
    verdict: string;
    category_matched: boolean;
    temporal_error_days?: number;
    direction_matched: boolean;
    predicate_traces: string[];
  };
}

export async function fetchPredictions(
  technique?: string,
  category?: string
): Promise<PredictionItem[]> {
  const params = new URLSearchParams();
  if (technique) params.set("technique", technique);
  if (category) params.set("category", category);
  const path = `/api/v1/prediction-validation/predictions${params.toString() ? `?${params.toString()}` : ""}`;
  return api.get<PredictionItem[]>(path);
}

export async function createPredictionSnapshot(data: Partial<PredictionItem>): Promise<PredictionItem> {
  return api.post<PredictionItem>("/api/v1/prediction-validation/predictions", data);
}

export async function fetchOutcomes(category?: string): Promise<OutcomeItem[]> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  const path = `/api/v1/prediction-validation/outcomes${params.toString() ? `?${params.toString()}` : ""}`;
  return api.get<OutcomeItem[]>(path);
}

export async function registerOutcome(data: Partial<OutcomeItem>): Promise<OutcomeItem> {
  return api.post<OutcomeItem>("/api/v1/prediction-validation/outcomes", data);
}

export async function evaluateMatch(
  predictionId: string,
  outcomeId?: string
): Promise<MatchResult> {
  return api.post<MatchResult>("/api/v1/prediction-validation/match", {
    prediction_id: predictionId,
    outcome_id: outcomeId,
  });
}

export async function runBacktest(options: {
  dataset_name?: string;
  technique_filter?: string;
  category_filter?: string;
  temporal_split?: TemporalSplitType;
}): Promise<BacktestRun> {
  return api.post<BacktestRun>("/api/v1/prediction-validation/backtest", options);
}

export async function fetchTechniqueSummaries(): Promise<TechniqueSummary[]> {
  return api.get<TechniqueSummary[]>("/api/v1/prediction-validation/techniques");
}

export async function fetchPredictionAudit(predictionId: string): Promise<PredictionAuditTrail> {
  return api.get<PredictionAuditTrail>(`/api/v1/prediction-validation/audit/${predictionId}`);
}
