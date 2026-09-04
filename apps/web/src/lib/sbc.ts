/**
 * AstroOS — Sarvatobhadra Chakra (SBC) API call (TanStack Query integration)
 *
 * POST /api/v1/sbc/report — full 9x9 grid snapshot (all 9 grahas' current
 * SBC nakshatra/cell) at a moment, plus (optionally) the Vedha result onto
 * a specified Janma element. See apps/api/services/sbc_vedha_engine.py for
 * the underlying mechanism (benefic-only casting, motion-based direction,
 * dignity-based scoring) — sourced from a real SBC tool's VBA and
 * cross-checked against live Classical Vedic screenshots for Dhanishtha/Shatabhisha.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";

export interface SBCGridPlanet {
  planet: string;
  nakshatra: string;
  pada: number;
  cellnum: number;
  rashi: string;
  rashi_degree: number;
  is_retrograde: boolean;
  is_combust: boolean;
  speed_deg_per_day: number;
  motion: string; // "Normal" | "Retrograde" | "Fast" | "Stationary"
  ray_direction: string; // "Front" | "Right" | "Left" | "All 3"
}

export interface SBCVedhaHit {
  planet: string;
  direction: string;
  from_nakshatra: string;
  score: number;
}

export interface SBCVedhaResult {
  hits: SBCVedhaHit[];
  total_score: number;
  zeroed_by_malefic_conjunction: boolean;
}

export interface SBCNatalAttributes {
  nama_akshara: string;
  janma_rashi: string;
  janma_rashi_icon: string;
  tithi_name: string;
  tithi_group: string;
  tithi_number: number;
  vara_name: string;
  vara_lord: string;
}

export interface SBCSensitivePoint {
  key: string;
  name: string;
  nakshatra_number: number;
  nakshatra_token: string;
  nakshatra_name: string;
  status: "activated" | "afflicted" | "mixed" | "neutral";
  vedhas_received: string[];
  benefic_hits: string[];
  malefic_hits: string[];
}

export interface SBCRawVedhaHit {
  planet: string;
  direction: string;
  from_nakshatra: string;
  target_type: string;
  target_key: string;
  target_name: string;
  nature: "benefic" | "malefic";
  strength_factors: {
    is_retrograde?: boolean;
    is_combust?: boolean;
    speed_deg_day?: number;
    gati?: string;
    dignity?: string;
    paksha_bala?: string | null;
    conjunctions?: string[];
  };
  source_convention: string;
}

export interface SBCVedhaEntry {
  planet: string;
  direction: string;
  from_nakshatra: string;
  target_points: string[];
  score: number;
  nature: "benefic" | "malefic";
  strength_factors?: {
    is_retrograde?: boolean;
    is_combust?: boolean;
    speed_deg_day?: number;
    gati?: string;
    dignity?: string;
    paksha_bala?: string | null;
    conjunctions?: string[];
  };
}

export interface SBCRiskItem {
  sangya_key: string;
  sangya_name: string;
  sangya_offset: number;
  nakshatra_name: string;
  transiting_planet: string;
  transiting_nakshatra: string;
  aspect_ray: string;
  domain: string;
  impact: string;
}

export interface SBCProtectionItem {
  sangya_key: string;
  sangya_name: string;
  sangya_offset: number;
  nakshatra_name: string;
  transiting_planet: string;
  transiting_nakshatra: string;
  aspect_ray: string;
  domain: string;
  impact: string;
}

export interface SBCSynthesis {
  high_risk_areas: SBCRiskItem[];
  protective_shields: SBCProtectionItem[];
  executive_summary: string;
  saving_grace: string;
  practical_advice: string[];
}

export interface SBCReport {
  moment_utc: string;
  tithi_number: number;
  positions: SBCGridPlanet[];
  janma_nakshatra: string | null;
  natal_attributes: SBCNatalAttributes | null;
  sensitive_points: SBCSensitivePoint[];
  benefic_vedhas: SBCVedhaEntry[];
  malefic_vedhas: SBCVedhaEntry[];
  raw_hits: SBCRawVedhaHit[];
  synthesis?: SBCSynthesis | null;
  convention_used: string;
  total_benefic_score: number;
  total_malefic_score: number;
  vedha_result: SBCVedhaResult | null;
}



export interface SBCReportPayload {
  moment_utc?: string | null;
  janma_nakshatra?: string | null;
  birth_datetime_utc?: string | null;
  birth_latitude?: number | null;
  birth_longitude?: number | null;
  ayanamsa?: string;
  chart_id?: string | null;
}

export type AISBCEventType = "market" | "life_events" | "muhurta" | "general";

export interface AISBCAnalysisRequest {
  reference_nakshatra: string;
  transit_date?: string | null;
  event_type: AISBCEventType;
  malefic_vedhas?: any[];
  benefic_vedhas?: any[];
  active_sangyas?: any[];
  custom_context?: string | null;
}

export interface AISBCSangyaBreakdownItem {
  sangya_key: string;
  sangya_name: string;
  nakshatra_name: string;
  status: "afflicted" | "activated" | "mixed" | "neutral" | string;
  domain: string;
  grahas_involved: string[];
  interpretation: string;
}

export interface AISBCWarningItem {
  headline: string;
  what_not_to_do: string;
  affected_area: string;
  severity: "critical" | "warning" | "caution" | string;
}

export interface AISBCSafeZoneItem {
  area_name: string;
  plain_title: string;
  description: string;
  benefit: string;
}

export interface AISBCPracticalStep {
  action: string;
  why: string;
  timing_tip: string;
}

export interface AISBCAnalysisResponse {
  event_type: string;
  title: string;
  verdict: string;
  verdict_badge: "high_risk" | "caution" | "favorable" | "auspicious" | string;
  the_story: string;
  executive_summary: string;
  risk_level: "high" | "moderate" | "low" | "auspicious" | string;
  quick_chips?: string[];
  major_warnings?: AISBCWarningItem[];
  safe_zones?: AISBCSafeZoneItem[];
  practical_steps?: AISBCPracticalStep[];
  sangya_breakdown: AISBCSangyaBreakdownItem[];
  predictions?: string[];
  protective_shields?: string[];
  actionable_remedies?: string[];
  markdown_report: string;
  confidence: number;
  version: string;
}


export const sbcKeys = {
  report: (payload: SBCReportPayload) => ["sbc", "report", payload] as const,
};

export function useSBCReport(payload: SBCReportPayload) {
  return useQuery<SBCReport>({
    queryKey: sbcKeys.report(payload),
    queryFn: () => api.post<SBCReport>("/api/v1/sbc/report", payload),
    enabled: !!tokenStore.getAccess(),
    staleTime: 60_000,
  });
}


