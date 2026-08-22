/**
 * AstroOS — Priority 8: Unified Multi-System Prediction Synthesis & Confluence Client
 *
 * Provides typed interfaces and API communication for:
 * 1. Multi-System Confluence evaluation (k/N agreement, veto inspection)
 * 2. 3-Tier Evidence Provenance (Calculated, Classical, Empirical)
 * 3. Timing Window Intersection (Dasha + Transit + SBC)
 * 4. 1-Click Freeze to P7 Validation Registry
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export type ProvenanceType =
  | "CALCULATED_EPHEMERIS"
  | "CLASSICAL_LITERATURE"
  | "EMPIRICAL_BACKTEST";

export type SystemSupportStatus =
  | "SUPPORTING"
  | "CONTRADICTING_VETO"
  | "NEUTRAL"
  | "UNAVAILABLE";

export type SynthesizedVerdict =
  | "UNANIMOUS_CONFLUENCE"
  | "STRONG_CONFLUENCE"
  | "MODERATE_CONFLUENCE"
  | "CONFLICTED_VETO"
  | "WEAK_UNCONVERGED";

export type PredictionCategory =
  | "career"
  | "marriage"
  | "finance"
  | "health"
  | "relocation"
  | "education"
  | "spiritual"
  | "general";

export interface SystemContribution {
  system_id: string;
  system_name: string;
  support_status: SystemSupportStatus;
  provenance_type: ProvenanceType;
  primary_houses: number[];
  active_significators: string[];
  rule_or_factor: string;
  rationale: string;
  veto_reason?: string | null;
  evidence_snapshot: Record<string, unknown>;
}

export interface ConfluenceMatrix {
  supporting_count: number;
  veto_count: number;
  neutral_count: number;
  total_systems: number;
  confluence_ratio: number;
  active_vetoes: string[];
  synthesized_verdict: SynthesizedVerdict;
  verdict_rationale: string;
}

export interface SynthesizedTimingWindow {
  window_start: string;
  window_end: string;
  peak_fructification_date: string;
  dasha_sub_period: string;
  transit_trigger: string;
  sbc_trigger_moment: string;
}

export interface EmpiricalTrackRecord {
  historical_hit_rate: number;
  historical_precision?: number | null;
  sample_size: number;
  wilson_95_ci: [number, number];
  sample_size_warning?: string | null;
  matched_cohort_name: string;
}

export interface UnifiedPredictionSynthesis {
  synthesis_id: string;
  chart_id: string;
  subject_name: string;
  category: PredictionCategory;
  synthesized_event_description: string;
  confluence_matrix: ConfluenceMatrix;
  system_contributions: SystemContribution[];
  synthesized_timing_window: SynthesizedTimingWindow;
  empirical_track_record: EmpiricalTrackRecord;
  provenance_breakdown: Record<string, string[]>;
  synthesis_timestamp: string;
  synthesis_hash: string;
}

export interface ConfluenceSynthesisRequest {
  chart_id?: string;
  chart_data?: Record<string, unknown>;
  category: PredictionCategory;
  target_datetime?: string;
  horizon_months?: number;
}

export interface ConfluenceSynthesisResponse {
  synthesis: UnifiedPredictionSynthesis;
}

export interface DomainScanItem {
  category: PredictionCategory;
  event_description: string;
  confluence_verdict: SynthesizedVerdict;
  confluence_ratio: number;
  supporting_count: number;
  veto_count: number;
  active_vetoes: string[];
  peak_timing: string;
}

export interface ConfluenceDomainScanResponse {
  chart_id: string;
  subject_name: string;
  scanned_domains: DomainScanItem[];
  scan_timestamp: string;
}

export interface FreezeToP7Request {
  synthesis_id: string;
  synthesis_payload?: UnifiedPredictionSynthesis;
  target_split_type?: "RESEARCH_TRAIN" | "VALIDATION" | "TEST_OUT_OF_SAMPLE";
}

export interface FreezeToP7Response {
  prediction_id: string;
  chart_id: string;
  subject_name: string;
  technique: string;
  category: PredictionCategory;
  evidence_hash: string;
  frozen_timestamp: string;
  status: string;
  message: string;
}

import { api } from "@/lib/api";

export async function synthesizePrediction(
  req: ConfluenceSynthesisRequest
): Promise<ConfluenceSynthesisResponse> {
  return api.post<ConfluenceSynthesisResponse>("/api/v1/predictions/confluence/synthesize", req);
}

export async function scanConfluenceDomains(
  req: { chart_id?: string; chart_data?: Record<string, unknown>; horizon_months?: number }
): Promise<ConfluenceDomainScanResponse> {
  return api.post<ConfluenceDomainScanResponse>("/api/v1/predictions/confluence/scan", req);
}

export async function freezeToP7Validation(
  req: FreezeToP7Request
): Promise<FreezeToP7Response> {
  return api.post<FreezeToP7Response>("/api/v1/predictions/confluence/freeze-to-p7", req);
}
