/**
 * AstroOS — AI API functions (Phase D + Phase E)
 *
 * Client-side wrappers for the AI explanation and Phase E endpoints.
 * All calls use the same `api` singleton as the rest of the codebase.
 */

"use client";

import { api } from "./api";
import type {
  AIResponseSchema,
  ExplanationResponse,
  ChartComparisonResponse,
  ResearchAnswerResponse,
  AvailableDomainsResponse,
  HypothesisTemplatesResponse,
  HypothesisListResponse,
} from "./types";

// Birth-data payload shared by all AI endpoints that need a chart.
export interface BirthDataInput {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: string;
  house_system: string;
}

export const aiApi = {
  /**
   * Explain why a specific rule fired (or didn't) for a given birth chart.
   * POST /api/v1/ai/explain-rule/{rule_id}
   */
  explainRule: (
    ruleId: string,
    birthData: BirthDataInput,
  ): Promise<ExplanationResponse> =>
    api.post<ExplanationResponse>(`/api/v1/ai/explain-rule/${ruleId}`, birthData),

  /**
   * Ask a natural-language question about a birth chart.
   * POST /api/v1/ai/answer-question
   */
  answerQuestion: (
    question: string,
    birthData: BirthDataInput,
  ): Promise<AIResponseSchema> =>
    api.post<AIResponseSchema>("/api/v1/ai/answer-question", {
      ...birthData,
      question,
    }),

  /**
   * Get a summary of a birth chart.
   * POST /api/v1/ai/chart-summary
   */
  chartSummary: (
    birthData: BirthDataInput,
    style: "concise" | "detailed" | "technical" = "concise",
  ): Promise<AIResponseSchema> =>
    api.post<AIResponseSchema>("/api/v1/ai/chart-summary", {
      ...birthData,
      style,
    }),

  // ── Phase E — Chart Comparison ──────────────────────────────────────────

  /**
   * Compare two birth charts side-by-side.
   * POST /api/v1/ai/compare-charts
   */
  compareCharts: (payload: {
    birth_datetime_utc_a: string;
    latitude_a: number;
    longitude_a: number;
    subject_name_a?: string;
    birth_datetime_utc_b: string;
    latitude_b: number;
    longitude_b: number;
    subject_name_b?: string;
    ayanamsa: string;
    house_system: string;
  }): Promise<ChartComparisonResponse> =>
    api.post<ChartComparisonResponse>("/api/v1/ai/compare-charts", payload),

  // ── Phase E — Research Assistant ────────────────────────────────────────

  /**
   * Ask a natural language research question over the knowledge base.
   * POST /api/v1/ai/research-query
   */
  researchQuery: (payload: {
    question: string;
    domain_filter?: string;
    max_results?: number;
  }): Promise<ResearchAnswerResponse> =>
    api.post<ResearchAnswerResponse>("/api/v1/ai/research-query", payload),

  /**
   * List available research domains.
   * GET /api/v1/ai/research-domains
   */
  listResearchDomains: (): Promise<AvailableDomainsResponse> =>
    api.get<AvailableDomainsResponse>("/api/v1/ai/research-domains"),

  // ── Phase E — Hypothesis Generation ─────────────────────────────────────

  /**
   * List all hypothesis templates.
   * GET /api/v1/ai/hypothesis-templates
   */
  listHypothesisTemplates: (): Promise<HypothesisTemplatesResponse> =>
    api.get<HypothesisTemplatesResponse>("/api/v1/ai/hypothesis-templates"),

  /**
   * Generate testable hypotheses from a birth chart.
   * POST /api/v1/ai/generate-hypotheses
   */
  generateHypotheses: (payload: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa: string;
    house_system: string;
    domain_filter?: string;
    max_hypotheses?: number;
  }): Promise<HypothesisListResponse> =>
    api.post<HypothesisListResponse>("/api/v1/ai/generate-hypotheses", payload),

  // ── Phase E — Enhanced QA ───────────────────────────────────────────────

  /**
   * Enhanced natural-language Q&A with full chart context.
   * POST /api/v1/ai/enhanced-qa
   */
  enhancedQA: (payload: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa: string;
    house_system: string;
    question: string;
    include_yogas?: boolean;
    include_dashas?: boolean;
    include_transits?: boolean;
    include_strengths?: boolean;
  }): Promise<AIResponseSchema> =>
    api.post<AIResponseSchema>("/api/v1/ai/enhanced-qa", payload),
};