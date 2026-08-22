/**
 * AstroOS — Advanced KP & SBC Analysis Client Library
 *
 * Provides API clients and types for:
 * 1. KP 4-Tier Significator Matrix & Cuspal Sub-Lord Decision Tree
 * 2. SBC 10-Sangya Transit-to-Natal Vedha Ray Matrix
 * 3. Unified Cross-Link Confluence Analysis
 */

import { api } from "@/lib/api";

export interface KPTierSignificators {
  house_number: number;
  tier_a_planets: string[];
  tier_b_planets: string[];
  tier_c_planets: string[];
  tier_d_planets: string[];
}

export interface KPCuspalSubLordDecisionNode {
  house_number: number;
  cusp_degree: number;
  cusp_rashi: string;
  sign_lord: string;
  star_lord: string;
  sub_lord: string;
  sub_sub_lord: string;
  sub_lord_star_lord: string;
  primary_houses_signified: number[];
  supporting_houses_signified: number[];
  negating_houses_signified: number[];
  is_veto_active: boolean;
  verdict: "PROMISED_FRUCTIFY" | "DELAYED_MODERATE" | "VETOED_NEGATED" | "DENIED";
  verdict_explanation: string;
  audit_chain: string[];
}

export interface KPEventDecisionTreeResult {
  event_domain: string;
  primary_cusp: number;
  supporting_cusps: number[];
  negating_cusps: number[];
  cusp_node: KPCuspalSubLordDecisionNode;
  supporting_significators: string[];
  ruling_planets_agreement: string[];
  fructification_verdict: "PROMISED_FRUCTIFY" | "DELAYED_MODERATE" | "VETOED_NEGATED" | "DENIED";
  summary_verdict: string;
  technical_calculation_steps: string[];
}

export interface KPCuspalDecisionTreeResponse {
  four_tier_significator_matrix: {
    house_number: number;
    tier_a_planets: string[];
    tier_b_planets: string[];
    tier_c_planets: string[];
    tier_d_planets: string[];
  }[];
  cuspal_decision_nodes: KPCuspalSubLordDecisionNode[];
  event_decision_trees: KPEventDecisionTreeResult[];
  total_cusps_evaluated: number;
}

export interface SBCGridCoordinate {
  row: number;
  col: number;
  cell_id: number;
  element_type: string;
  element_name: string;
  element_value: string;
}

export interface SBCRayCollision {
  transit_planet: string;
  is_retrograde: boolean;
  speed_deg_day: number;
  ray_direction: string;
  source_cell: SBCGridCoordinate;
  target_cell: SBCGridCoordinate;
  target_sangya?: string | null;
  nature: "Natural Benefic" | "Natural Malefic";
  raw_impact_score: number;
  ray_path_coordinates: number[][];
}

export interface SangyaVedhaStatus {
  sangya_key: string;
  sangya_name: string;
  domain: string;
  natal_nakshatra: string;
  natal_nakshatra_number: number;
  grid_coord: SBCGridCoordinate;
  benefic_hits: SBCRayCollision[];
  malefic_hits: SBCRayCollision[];
  net_score: number;
  is_obstructed: boolean;
  verdict: string;
  audit_trace: string[];
}

export interface SBCSangyaRayMatrixResponse {
  natal_moon_nakshatra: string;
  transit_datetime_iso: string;
  sangya_statuses: SangyaVedhaStatus[];
  all_ray_collisions: SBCRayCollision[];
  overall_sbc_confluence_score: number;
  kp_cross_link_summary: string;
  audit_trail: string[];
}

export async function evaluateKPCuspalDecisionTree(
  chart: Record<string, unknown>,
  params?: { house_numbers?: number[]; event_domain?: string }
): Promise<KPCuspalDecisionTreeResponse> {
  return api.post<KPCuspalDecisionTreeResponse>("/api/v1/kp/cuspal-decision-tree", {
    chart,
    house_numbers: params?.house_numbers,
    event_domain: params?.event_domain,
  });
}

export async function evaluateSBCSangyaRayMatrix(
  natal_chart: Record<string, unknown>,
  params?: { transit_planets?: Record<string, unknown>[]; transit_datetime_iso?: string }
): Promise<SBCSangyaRayMatrixResponse> {
  return api.post<SBCSangyaRayMatrixResponse>("/api/v1/sbc/sangya-ray-matrix", {
    natal_chart,
    transit_planets: params?.transit_planets,
    transit_datetime_iso: params?.transit_datetime_iso,
  });
}
