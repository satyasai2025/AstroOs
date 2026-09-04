/**
 * AstroOS — Unified Multi-System Event Timing API Client & React Query Hooks
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

export type UnifiedEventType =
  | "marriage"
  | "career"
  | "wealth"
  | "property"
  | "foreign_travel"
  | "health"
  | "childbirth"
  | "education";

export interface DashaPeriodItem {
  level: string;
  lord: string;
  start_date: string;
  end_date: string;
}

export interface DashaEvidence {
  active_chain: DashaPeriodItem[];
  significator_lords: string[];
  is_dasha_active: boolean;
  active_level?: string | null;
  active_lord?: string | null;
  score: number;
  detail: string;
}

export interface GocharaTransitItem {
  planet: string;
  rashi: string;
  house_from_lagna: number;
  house_from_moon: number;
  is_retrograde: boolean;
  is_favorable: boolean;
  aspects: string[];
}

export interface GocharaEvidence {
  key_transits: GocharaTransitItem[];
  gochara_vedha_clear: boolean;
  ashtakavarga_support: number;
  sade_sati_status?: string | null;
  score: number;
  detail: string;
}

export interface SBCVedhaHitItem {
  transiting_planet: string;
  ray_direction: string;
  from_nakshatra: string;
  target_point: string;
  target_name: string;
  nature: "benefic" | "malefic";
  impact: string;
}

export interface SBCVedhaEvidence {
  janma_hits: SBCVedhaHitItem[];
  relevant_sangya_hits: SBCVedhaHitItem[];
  benefic_count: number;
  malefic_count: number;
  net_protection: number;
  score: number;
  detail: string;
}

export interface KPTransitTriggerItem {
  transit_planet: string;
  transit_sign: string;
  transit_nakshatra_lord: string;
  transit_sub_lord: string;
  trigger_type: string;
  significator_matched: string;
  detail: string;
}

export interface KPEvidence {
  primary_cusp: number;
  csl: string;
  csl_star_lord: string;
  csl_signifies: number[];
  required_houses: number[];
  active_transit_triggers: KPTransitTriggerItem[];
  rp_triggers: string[];
  dusthana_veto: boolean;
  fructification: "OPEN" | "PARTIAL" | "CLOSED";
  score: number;
  detail: string;
}

export interface UnifiedTimingSnapshot {
  evaluated_datetime_utc: string;
  event_type: string;
  dasha: DashaEvidence;
  gochara: GocharaEvidence;
  sbc: SBCVedhaEvidence;
  kp: KPEvidence;
  confluence_score: number;
  confidence_tier: "VERY_HIGH" | "HIGH" | "MODERATE" | "LOW" | "UNFAVORABLE";
  system_weights: Record<string, number>;
  primary_positive_triggers: string[];
  primary_inhibiting_factors: string[];
  summary_narrative: string;
}

export interface TimelineSamplePoint {
  date: string;
  confluence_score: number;
  dasha_score: number;
  gochara_score: number;
  sbc_score: number;
  kp_score: number;
  peak_flag: boolean;
}

export interface UnifiedEventTimingWindow {
  window_id: string;
  event_type: string;
  start_date: string;
  end_date: string;
  peak_date: string;
  peak_score: number;
  confluence_status: "HIGH_CONFLUENCE" | "MODERATE_CONFLUENCE" | "PARTIAL_WINDOW" | "INHIBITED";
  system_scores: Record<string, number>;
  primary_drivers: string[];
  inhibiting_factors: string[];
  narrative: string;
}

export interface UnifiedEventTimingAnalyzeRequest {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa?: string;
  house_system?: string;
  event_type: string;
  start_date?: string;
  end_date?: string;
  evaluation_datetime_utc?: string;
  step_days?: number;
  chart_id?: string;
}

export interface UnifiedEventTimingAnalyzeResponse {
  chart_id?: string | null;
  event_type: string;
  start_date: string;
  end_date: string;
  evaluated_moment_snapshot: UnifiedTimingSnapshot;
  candidate_windows: UnifiedEventTimingWindow[];
  time_series: TimelineSamplePoint[];
  confluence_summary: string;
}

export interface UnifiedMomentEvaluationRequest {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa?: string;
  house_system?: string;
  event_type: string;
  target_datetime_utc: string;
  chart_id?: string;
}

export interface UnifiedMomentEvaluationResponse {
  chart_id?: string | null;
  event_type: string;
  snapshot: UnifiedTimingSnapshot;
}

export async function fetchEventTimingAnalysis(
  payload: UnifiedEventTimingAnalyzeRequest
): Promise<UnifiedEventTimingAnalyzeResponse> {
  return api.post<UnifiedEventTimingAnalyzeResponse>(
    "/api/v1/event-timing/analyze",
    payload
  );
}

export async function evaluateTimingMoment(
  payload: UnifiedMomentEvaluationRequest
): Promise<UnifiedMomentEvaluationResponse> {
  return api.post<UnifiedMomentEvaluationResponse>(
    "/api/v1/event-timing/moment",
    payload
  );
}

export function useUnifiedTimingAnalysis(payload: UnifiedEventTimingAnalyzeRequest | null) {
  return useQuery({
    queryKey: [
      "event-timing-analysis",
      payload?.birth_datetime_utc,
      payload?.event_type,
      payload?.start_date,
      payload?.end_date,
    ],
    queryFn: () => {
      if (!payload) throw new Error("Payload required");
      return fetchEventTimingAnalysis(payload);
    },
    enabled: Boolean(payload?.birth_datetime_utc),
    staleTime: 5 * 60 * 1000,
  });
}
