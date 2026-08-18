/**
 * AstroOS — Guru Research Layer API Client
 *
 * Client-side interface for evaluating planetary positions against
 * proprietary research degree-slice zones and retrieving rule configurations.
 */

"use client";

import { api } from "./api";

export interface PlanetPositionInput {
  planet: string;
  rashi: string;
  degree_in_rashi: number;
}

export interface ChartEvaluationRequest {
  positions: PlanetPositionInput[];
  custom_rules?: Record<string, unknown>;
}

export interface PlanetEvaluationResponse {
  planet: string;
  rashi: string;
  degree_in_rashi: number;
  classical_dignity: string | null;
  guru_zone_name: string;
  guru_zone_type: string;
  guru_zone_lord: string;
  guru_zone_range: string;
  is_ruler_match: boolean;
  is_dignity_agreement: boolean;
  notes: string;
}

export interface GuruChartEvaluationResponse {
  evaluations: PlanetEvaluationResponse[];
  agreements_count: number;
  deviations_count: number;
  summary_insights: string[];
}

export interface GuruRuleResponse {
  start_deg: number;
  end_deg: number;
  zone_type: string;
  ruling_planet: string;
  description: string;
  strength_weight: number;
}

export interface GuruRulesRegistryResponse {
  partitions: Record<string, GuruRuleResponse[]>;
}

export const guruResearchApi = {
  getRules: () =>
    api.get<GuruRulesRegistryResponse>("/api/v1/research/guru-layer/rules"),

  evaluate: (data: ChartEvaluationRequest) =>
    api.post<GuruChartEvaluationResponse>(
      "/api/v1/research/guru-layer/evaluate",
      data
    ),
};
