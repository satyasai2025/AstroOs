/**
 * AstroOS — Research Case API Client (Module 27)
 *
 * Client-side wrappers for the Research Case pipeline endpoints:
 * - GET  /research/cases/import/schema — JSON schema for validation
 * - POST /research/cases/validate      — validate a batch without persisting
 * - POST /research/cases/import        — validate + snapshot-compute + persist
 * - GET  /research/cases               — list imported cases
 * - POST /research/cases/features/extract        — normalise snapshots into features
 * - POST /research/cases/patterns/discover       — find significant patterns
 * - POST /research/cases/patterns/hypothesis     — test a custom hypothesis
 *
 * Pattern Discovery Dashboard (Phase 3c) — reads over persisted patterns,
 * never recompute: getPatternSummary/listPatterns/getPatternDetail/
 * getTopFactors/getConfidenceDistribution/getPatternGraph/getPatternTrend.
 * explainPattern is the ONLY method that ever calls the real OpenAI-backed
 * endpoint — getPatternDetail is strictly read-only.
 */

"use client";

import { api } from "./api";
import type {
  ConfidenceDistributionResponse,
  DatasetValidationReport,
  EvidenceRecalculationResult,
  FeatureExtractionResponse,
  PatternDetail,
  PatternDiscoveryRequest,
  PatternDiscoveryResponse,
  PatternExploreRequest,
  PatternQuestionRequest,
  PatternQuestionResponse,
  PatternExplainAllResponse,
  PatternExplainResponse,
  PatternGraphResponse,
  PatternHypothesisRequest,
  PatternHypothesisResponse,
  PatternListFilters,
  PatternListResponse,
  PatternSummary,
  PatternTrendResponse,
  ResearchCaseBatchImport,
  ResearchCaseBatchValidation,
  ResearchCaseDetail,
  ResearchCaseImportResponse,
  ResearchCaseListResponse,
  ResearchQueryRequest,
  ResearchQueryResponse,
  SnapshotRebuildResult,
  TopFactorsResponse,
} from "./types";

export const researchCasesApi = {
  /** Fetch the backend's JSON Schema for a batch import payload. */
  getImportSchema: () =>
    api.get<Record<string, unknown>>("/api/v1/research/cases/import/schema"),

  /** Validate a batch without persisting anything. */
  validate: (payload: ResearchCaseBatchImport) =>
    api.post<ResearchCaseBatchValidation>("/api/v1/research/cases/validate", payload),

  /** Validate, snapshot-compute, and persist a batch of cases. */
  importCases: (payload: ResearchCaseBatchImport) =>
    api.post<ResearchCaseImportResponse>("/api/v1/research/cases/import", payload),

  /** Query real research cases by AND-combined conditions over the
   * canonical Fact vocabulary FactBuilder produces (e.g.
   * "planet.saturn.retrograde"="true") — powers the Query Builder page.
   * Not a mocked/illustrative result. */
  queryCases: (payload: ResearchQueryRequest) =>
    api.post<ResearchQueryResponse>("/api/v1/research/cases/query", payload),

  /** List imported research cases. */
  list: (params: { search?: string; limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.search) qs.set("search", params.search);
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.offset) qs.set("offset", String(params.offset));
    const query = qs.toString();
    return api.get<ResearchCaseListResponse>(`/api/v1/research/cases${query ? `?${query}` : ""}`);
  },

  /** One case's full life-event timeline, each with its astrological
   * snapshot (dasha/yogas/transits/house-lord dignity/nakshatras) — powers
   * the interactive event timeline chart. */
  getDetail: (researchCaseId: string) =>
    api.get<ResearchCaseDetail>(
      `/api/v1/research/cases/${encodeURIComponent(researchCaseId)}`
    ),

  /** Normalise every imported snapshot into flat research features. */
  extractFeatures: () =>
    api.post<FeatureExtractionResponse>("/api/v1/research/cases/features/extract", {}),

  /** Discover statistically significant astrological patterns. */
  discoverPatterns: (payload: PatternDiscoveryRequest = {}) =>
    api.post<PatternDiscoveryResponse>("/api/v1/research/cases/patterns/discover", payload),

  /** Personal "what-if" pattern search with custom thresholds — same
   * shared dataset/formulas, never persisted to the shared dashboard. */
  explorePatterns: (payload: PatternExploreRequest = {}) =>
    api.post<PatternDiscoveryResponse>("/api/v1/research/cases/patterns/explore", payload),

  /** Ask a plain-language question about the shared discovered patterns
   * (e.g. "what correlates with Marriage?"). Read-only, grounded in real
   * already-persisted patterns — never invents statistics. */
  askAboutPatterns: (payload: PatternQuestionRequest) =>
    api.post<PatternQuestionResponse>("/api/v1/research/cases/patterns/ask", payload),

  /** Test a custom dimension->value hypothesis against the snapshot data. */
  testHypothesis: (payload: PatternHypothesisRequest) =>
    api.post<PatternHypothesisResponse>("/api/v1/research/cases/patterns/hypothesis", payload),

  // ── Pattern Discovery Dashboard (read-only) ─────────────────────────────

  /** KPI numbers for the dashboard header. */
  getPatternSummary: () =>
    api.get<PatternSummary>("/api/v1/research/cases/patterns/summary"),

  /** List persisted patterns, filterable — never recomputes. */
  listPatterns: (filters: PatternListFilters = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== "") params.set(key, String(value));
    }
    const qs = params.toString();
    return api.get<PatternListResponse>(`/api/v1/research/cases/patterns${qs ? `?${qs}` : ""}`);
  },

  /** Strictly read-only pattern detail — never triggers an AI explanation call. */
  getPatternDetail: (patternId: string) =>
    api.get<PatternDetail>(`/api/v1/research/cases/patterns/${encodeURIComponent(patternId)}`),

  /** Confidence-over-time for one pattern across discovery runs. */
  getPatternTrend: (patternId: string) =>
    api.get<PatternTrendResponse>(`/api/v1/research/cases/patterns/trend/${encodeURIComponent(patternId)}`),

  /** Top contributing dimension values within a category (planet/yoga/dasha/house/...). */
  getTopFactors: (category: string) =>
    api.get<TopFactorsResponse>(`/api/v1/research/cases/patterns/top-factors?category=${encodeURIComponent(category)}`),

  /** Bucketed histogram of persisted pattern confidence scores. */
  getConfidenceDistribution: () =>
    api.get<ConfidenceDistributionResponse>("/api/v1/research/cases/patterns/confidence-distribution"),

  /** Pattern dimension co-occurrence network (radial layout, precomputed x/y). */
  getPatternGraph: () =>
    api.get<PatternGraphResponse>("/api/v1/research/cases/patterns/graph"),

  // ── AI Explanation (the only calls that ever hit OpenAI) ────────────────

  /** Generate (or regenerate) one pattern's AI explanation. */
  explainPattern: (patternId: string) =>
    api.post<PatternExplainResponse>(`/api/v1/research/cases/patterns/${encodeURIComponent(patternId)}/explain`, {}),

  /** Advanced Research: bulk-regenerate every pattern's AI explanation. */
  regenerateAllExplanations: () =>
    api.post<PatternExplainAllResponse>("/api/v1/research/cases/patterns/explanations/regenerate-all", {}),

  // ── Advanced Research tools ──────────────────────────────────────────────

  /** Dataset integrity report over already-imported data. */
  validateDataset: () =>
    api.get<DatasetValidationReport>("/api/v1/research/cases/dataset/validate"),

  /** Recompute snapshots for every imported case under the current engine version. */
  rebuildSnapshots: () =>
    api.post<SnapshotRebuildResult>("/api/v1/research/cases/snapshots/rebuild", {}),

  /** Refresh supporting/contradicting/lift for existing patterns (no new discovery). */
  recalculateEvidence: () =>
    api.post<EvidenceRecalculationResult>("/api/v1/research/cases/patterns/evidence/recalculate", {}),
} as const;
