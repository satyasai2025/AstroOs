/**
 * AstroOS — Shared TypeScript Types
 *
 * Mirror of the FastAPI response schemas.
 * Keep in sync with apps/api/schemas/*.py manually until an
 * OpenAPI codegen step is added in a later module.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "guest" | "researcher" | "admin";
  status: "active" | "suspended" | "pending_verification";
  created_at: string;
  last_login_at: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "Bearer";
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface RegisterPayload {
  email: string;
  display_name: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

// ── API Error ─────────────────────────────────────────────────────────────────

export interface ApiErrorBody {
  detail: string;
}

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
}

// ── Workflow Orchestrator (v2 Phase A) ────────────────────────────────────────
// Mirror of apps/api/schemas/workflow.py and the response schemas it reuses
// (horoscope/divisional/dasha/yoga/ashtakavarga/transit/knowledge/report).

export type AyanamsaCode =
  | "lahiri"
  | "kp"
  | "raman"
  | "yukteshwar"
  | "fagan_bradley"
  | "true_chitra";
export type HouseSystemCode = "W" | "P" | "K" | "E";
export type DashaSystemCode =
  | "vimshottari"
  | "yogini"
  | "ashtottari"
  | "kalachakra"
  | "chara"
  | "narayana";

export interface WorkflowAnalysisRequest {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: AyanamsaCode;
  house_system: HouseSystemCode;
  dasha_system: DashaSystemCode;
  transit_datetime_utc?: string | null;
  include_vargas: boolean;
  subject_name: string;
  generated_by?: string | null;
  research_project_id?: string | null;
}

// ── Chart (D1) ──────────────────────────────────────────────────────────────

export interface AscendantSchema {
  longitude: number;
  sidereal_longitude: number;
  rashi: string;
  rashi_degree: number;
  nakshatra: string;
  pada: number;
}

export interface HouseCuspSchema {
  house_number: number;
  longitude: number;
  sidereal_longitude: number;
  rashi: string;
}

export interface PlanetPositionSchema {
  planet: string;
  sidereal_longitude: number;
  rashi: string;
  rashi_degree: number;
  house_number: number;
  nakshatra: string;
  pada: number;
  is_retrograde: boolean;
  is_combust: boolean;
  combustion_orb: number | null;
  dignity: string | null;
}

export interface AspectSchema {
  from_planet: string;
  to_planet: string;
  aspect_type: string;
  orb_degrees: number;
  is_applying: boolean;
}

export interface PlanetStrengthSchema {
  planet: string;
  dignity: string | null;
  is_retrograde: boolean;
  is_combust: boolean;
  house_number: number;
  is_in_own_sign: boolean;
  is_exalted: boolean;
  is_debilitated: boolean;
  is_in_kendra: boolean;
  is_in_trikona: boolean;
  is_in_dusthana: boolean;
  strength_score: number;
}

export interface PanchangaSchema {
  tithi: { number: number; name: string; paksha: string; completion_percent: number };
  nakshatra: {
    nakshatra: string;
    nakshatra_number: number;
    pada: number;
    lord: string;
    degree_in_nakshatra: number;
    degree_in_pada: number;
  };
  yoga: { number: number; name: string; completion_percent: number };
  karana: { number: number; name: string; is_fixed: boolean };
  vara: { number: number; name: string; lord: string };
  julian_day: number;
  ayanamsa_deg: number;
}

export interface D1ChartResponse {
  ascendant: AscendantSchema;
  houses: HouseCuspSchema[];
  planets: PlanetPositionSchema[];
  aspects: AspectSchema[];
  planet_strengths: PlanetStrengthSchema[];
  panchanga: PanchangaSchema;
  ayanamsa_system: string;
  house_system: string;
  julian_day: number;
  ayanamsa_value: number;
}

// ── Vargas ────────────────────────────────────────────────────────────────────

export interface VargaAscendantResponse {
  d1_sidereal_longitude: number;
  d1_rashi: string;
  d1_rashi_degree: number;
  varga_rashi: string;
  varga_rashi_degree: number;
}

export interface VargaPlanetResponse {
  planet: string;
  d1_sidereal_longitude: number;
  d1_rashi: string;
  d1_rashi_degree: number;
  varga_rashi: string;
  varga_rashi_degree: number;
  varga_house_number: number;
  nakshatra: string;
  pada: number;
  is_retrograde: boolean;
  is_combust: boolean;
}

export interface VargaChartResponse {
  varga: string;
  divisor: number;
  ascendant: VargaAscendantResponse;
  planet_positions: VargaPlanetResponse[];
  ayanamsa_system: string;
  julian_day: number;
}

export interface AllVargaChartsResponse {
  charts: Record<string, VargaChartResponse>;
  julian_day: number;
  ayanamsa_system: string;
}

// ── Dasha ─────────────────────────────────────────────────────────────────────

export interface DashaPeriodResponse {
  lord: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  level: number;
  children: DashaPeriodResponse[];
}

export interface DashaTreeResponse {
  system: string;
  birth_date: string;
  trigger_planet: string;
  trigger_nakshatra: string;
  trigger_nakshatra_number: number;
  mahadashas: DashaPeriodResponse[];
  max_depth: number;
  total_cycle_years: number;
}

// ── Yoga ──────────────────────────────────────────────────────────────────────

export interface YogaResultResponse {
  yoga_id: string;
  name: string;
  category: string;
  source_text: string;
  rule_version: string;
  is_present: boolean;
  strength: string | null;
  involved_planets: string[];
  involved_houses: number[];
  satisfied: string[];
  missing: string[];
  trace: string[];
}

export interface YogaEvaluationResponse {
  results: YogaResultResponse[];
  total_evaluated: number;
  total_present: number;
}

// ── Ashtakavarga ──────────────────────────────────────────────────────────────

export interface BhinnashtakavargaResponse {
  target_planet: string;
  bindus_by_rashi: number[];
  total_bindus: number;
  rule_version: string;
}

export interface SarvashtakavargaResponse {
  bindus_by_rashi: number[];
  total_bindus: number;
  rule_version: string;
  checksum_valid: boolean;
}

export interface AllAshtakavargaResponse {
  bhinnashtakavarga: BhinnashtakavargaResponse[];
  bhinnashtakavarga_reduced: BhinnashtakavargaResponse[];
  sarvashtakavarga: SarvashtakavargaResponse;
}

// ── Transit ───────────────────────────────────────────────────────────────────

export interface TransitPlanetResponse {
  planet: string;
  transit_rashi: string;
  house_from_natal_moon: number;
  ashtakavarga_bindus: number | null;
  is_sade_sati: boolean;
  is_ashtama_shani: boolean;
  is_good_house: boolean | null;
  has_vedha: boolean;
  has_vipreet_vedha: boolean;
  vedha_planet: string | null;
  rule_version: string;
}

export interface TransitResponse {
  transit_datetime_utc: string;
  natal_moon_rashi: string;
  planets: TransitPlanetResponse[];
}

// ── Rule Engine / Verification / Benchmark (new in the Workflow response) ────

export interface RuleResultResponse {
  rule_id: string;
  rule_name: string;
  rule_category: string;
  matched: boolean;
  matched_conditions: string[];
  failed_conditions: string[];
  explanation: string;
}

export interface ShadbalaTotalResponse {
  planet: string;
  total_rupas: number;
}

export interface VerificationPairSummaryResponse {
  rule_id: string;
  rule_name: string;
  event_id: string;
  event_title: string;
  event_date: string;
  alignment: string;
  strength: string;
}

export interface VerificationSummaryResponse {
  total_events: number;
  total_rules_evaluated: number;
  total_pairs: number;
  pairs: VerificationPairSummaryResponse[];
  confidence_score: number;
}

export interface PlanetBenchmarkResponse {
  planet: string;
  computed_longitude: number;
  expected_longitude: number;
  error_degrees: number;
  within_tolerance: boolean;
}

export interface BenchmarkResponse {
  status: "passed" | "failed" | "not_applicable";
  reference_id: string;
  reference_name: string;
  chart_count: number;
  mean_error: number;
  max_error: number;
  tolerance: number;
  planets: PlanetBenchmarkResponse[];
  detail: string;
}

// ── Knowledge ─────────────────────────────────────────────────────────────────

export interface KnowledgeSearchResultResponse {
  entity_type: string;
  entity_id: string;
  title: string;
  snippet: string;
  relevance: number;
  book_title: string | null;
  tradition: string | null;
}

// ── Report ────────────────────────────────────────────────────────────────────

export interface ReportSectionResponse {
  title: string;
  section_type: string;
  data: Record<string, unknown>;
  order: number;
}

export interface ReportMetadataResponse {
  report_id: string;
  report_type: string;
  report_version: string;
  generated_at: string;
  engine_versions: Record<string, string>;
  chart_id: string | null;
  research_project_id: string | null;
  generated_by: string | null;
}

export interface ChartReportResponse {
  metadata: ReportMetadataResponse;
  title: string;
  subject_name: string;
  sections: ReportSectionResponse[];
}

// ── Top-level Workflow response ───────────────────────────────────────────────

export interface WorkflowAnalysisResponse {
  chart_id: string;
  chart: D1ChartResponse;
  vargas: AllVargaChartsResponse | null;
  dasha: DashaTreeResponse;
  yogas: YogaEvaluationResponse;
  shadbala: ShadbalaTotalResponse[];
  ashtakavarga: AllAshtakavargaResponse;
  transits: TransitResponse;
  rule_results: RuleResultResponse[];
  knowledge_citations: KnowledgeSearchResultResponse[];
  verification: VerificationSummaryResponse | null;
  benchmark: BenchmarkResponse;
  report: ChartReportResponse;
  research_snapshot_id: string | null;
}

// ── AI / Explanation (Phase D) ────────────────────────────────────────────────
// Mirror of apps/api/schemas/explanation.py and apps/api/schemas/ai.py.

export interface ConditionExplanationResponse {
  condition_text: string;
  satisfied: boolean;
  fact_key: string;
  actual_value: string;
  expected_value: string;
  operator: string;
}

export interface ExplanationResponse {
  rule_id: string;
  rule_name: string;
  rule_category: string;
  summary: string;
  matched: boolean;
  conditions: ConditionExplanationResponse[];
  derived_facts: Record<string, unknown>;
  derived_fact_sources: Record<string, string>;
  locked_facts: string[];
  confidence: string;
  explanation_text: string;
}

export interface FailureAnalysisResponse {
  rule_id: string;
  rule_name: string;
  summary: string;
  failed_conditions: ConditionExplanationResponse[];
  passed_conditions: ConditionExplanationResponse[];
  suggested_conditions: string[];
}

export interface CitationResponse {
  source: string;
  reference: string;
  text: string;
  relevance: number;
}

export interface AIResponseSchema {
  response_type: string;
  title: string;
  summary: string;
  body: string;
  citations: CitationResponse[];
  sources: string[];
  recommendations: string[];
  confidence: string;
  version: string;
}

// ── Geocoding (v2 Platform Alpha Stabilization) ───────────────────────────────
// Mirror of apps/api/schemas/geocoding.py.

export interface PlaceResultResponse {
  display_name: string;
  latitude: number;
  longitude: number;
  country: string | null;
  state: string | null;
}

export interface PlaceSearchResponse {
  results: PlaceResultResponse[];
}

export interface TimezoneResolutionResponse {
  iana_name: string;
  utc_offset_minutes: number;
  is_dst: boolean;
}

// ── Phase E — AI Layer (Chart Comparison, Research, Hypothesis, Enhanced QA) ──

export interface ComparisonDimensionResponse {
  dimension: string;
  chart_a_value: string;
  chart_b_value: string;
  similarity: number;
  significance: string;
  commentary: string;
}

export interface ChartComparisonResponse {
  summary: string;
  overall_similarity: number;
  key_differences: ComparisonDimensionResponse[];
  key_similarities: ComparisonDimensionResponse[];
  compatibility_notes: string;
  relationship_potential: string;
  timing_synergies: string;
}

export interface ResearchEvidenceResponse {
  source: string;
  reference: string;
  text: string;
  relevance: number;
  entity_type: string;
  tradition: string | null;
}

export interface ResearchAnswerResponse {
  question: string;
  summary: string;
  body: string;
  evidence: ResearchEvidenceResponse[];
  related_conflicts: string[];
  confidence: string;
  unanswered_aspects: string[];
}

export interface AvailableDomainResponse {
  id: string;
  name: string;
  description: string;
}

export interface AvailableDomainsResponse {
  domains: AvailableDomainResponse[];
}

export interface HypothesisTemplateResponse {
  hypothesis_id: string;
  title: string;
  description: string;
  domain: string;
  conditions: string[];
  expected_outcome: string;
  test_method: string;
  classical_references: string[];
  priority: number;
}

export interface GeneratedHypothesisResponse {
  hypothesis_id: string;
  title: string;
  description: string;
  domain: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  testable_prediction: string;
  suggested_dataset: string;
  priority: number;
  related_rules: string[];
  related_yogas: string[];
  confidence: string;
}

export interface HypothesisTemplatesResponse {
  templates: HypothesisTemplateResponse[];
  total: number;
}

export interface HypothesisListResponse {
  hypotheses: GeneratedHypothesisResponse[];
  total: number;
}
