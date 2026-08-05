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
  gender?: string | null;
  place_name?: string | null;
  generated_by?: string | null;
  research_project_id?: string | null;
  /** Set false to recompute an already-saved chart for display/comparison without saving a new row. Requires chart_id. */
  persist?: boolean;
  /** The existing saved chart this recompute belongs to. Required when persist is false. */
  chart_id?: string | null;
}

// ── Chart (D1) ──────────────────────────────────────────────────────────────

export interface AscendantSchema {
  longitude: number;
  sidereal_longitude: number;
  rashi: string;
  rashi_degree: number;
  nakshatra: string;
  pada: number;
  /** Star Lord (KP) */
  nakshatra_lord: string;
  /** Sub Lord (KP) */
  sub_lord: string;
  /** Sub Sub Lord (KP) */
  sub_sub_lord: string;
}

export interface HouseCuspSchema {
  house_number: number;
  longitude: number;
  sidereal_longitude: number;
  rashi: string;
  /** Star Lord (KP) */
  nakshatra_lord: string;
  /** Cuspal Sub Lord (KP) — the primary KP significator tool */
  sub_lord: string;
  /** Cuspal Sub Sub Lord (KP) */
  sub_sub_lord: string;
}

export interface PlanetPositionSchema {
  planet: string;
  sidereal_longitude: number;
  rashi: string;
  rashi_degree: number;
  /** Bhava Chalit (cuspal) house — real cusp-to-cusp span for the requested house_system */
  house_number: number;
  nakshatra: string;
  pada: number;
  is_retrograde: boolean;
  is_combust: boolean;
  combustion_orb: number | null;
  dignity: string | null;
  /** Star Lord (KP) */
  nakshatra_lord: string;
  /** Sub Lord (KP) */
  sub_lord: string;
  /** Sub Sub Lord (KP) */
  sub_sub_lord: string;
  /** Rashi (sign-counting) house — signs from the lagna's sign; can differ from house_number */
  rashi_house_number: number;
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

// ── Admin ────────────────────────────────────────────────────────────────────

export interface ModuleHealth {
  module_name: string;
  status: string;
  version: string;
  message: string;
}

export interface SystemStatus {
  status: string;
  modules: Record<string, ModuleHealth>;
  ephemeris_mode: string;
  version: string;
}

export interface ModuleRegistry {
  modules: Record<string, string>;
}

export interface AdminUserSummary {
  id: string;
  email: string;
  display_name: string;
  role: string;
  status: string;
  created_at: string | null;
  last_login_at: string | null;
}

export interface AdminUserListResponse {
  users: AdminUserSummary[];
  total: number;
}

// ── Saved charts ─────────────────────────────────────────────────────────────

export interface BirthChartSummary {
  id: string;
  subject_name: string;
  birth_datetime_utc: string;
  birth_latitude: number;
  birth_longitude: number;
  place_name: string | null;
  ayanamsa: string;
  house_system: string;
  lagna_rashi: string | null;
  moon_nakshatra: string | null;
  created_at: string;
  is_default: boolean;
}

export interface BirthChartListResponse {
  charts: BirthChartSummary[];
  total: number;
  limit: number;
  offset: number;
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
  sub_periods: DashaPeriodResponse[];
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
  is_favorable_house: boolean | null;
  has_vedha: boolean;
  has_vipreet_vedha: boolean;
  vedha_planet: string | null;
  /** 28-system (Abhijit-aware) Sarvatobhadra Chakra nakshatra — scoped only
   * to Nakshatra Vedha; every other nakshatra field in this app uses the
   * standard 27-system. */
  transit_nakshatra_sbc: string;
  has_nakshatra_vedha: boolean;
  nakshatra_vedha_planet: string | null;
  /** "forward" (direct motion) or "backward" (retrograde). */
  nakshatra_vedha_type: string | null;
  nakshatra_vedha_target: string | null;
  rule_version: string;
  transit_rashi_degree: number;
  /** Standard 27-system nakshatra at the transit moment (distinct from transit_nakshatra_sbc above). */
  transit_nakshatra: string;
  transit_pada: number;
  is_retrograde: boolean;
  /** Sidereal longitude speed, degrees/day; negative = retrograde. */
  speed_deg_per_day: number;
  /** Classical Ashta Gati speed state — see the backend's gati_classifier.py
   * for the classification rules and its accuracy caveats (Anuvakra/Kutila
   * aren't distinguishable from a single instantaneous position). */
  gati: "vakra" | "vikala" | "mandatara" | "manda" | "sama" | "chara" | "atichara";
}

export interface TransitResponse {
  transit_datetime_utc: string;
  natal_moon_rashi: string;
  planets: TransitPlanetResponse[];
}

export interface TransitRequest {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: AyanamsaCode;
  house_system: HouseSystemCode;
  transit_datetime_utc?: string | null;
}

// ── Transit Patterns (/api/v1/transit/patterns) ───────────────────────────────

export interface TransitPatternsRequest {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: AyanamsaCode;
  house_system: HouseSystemCode;
  transit_datetime_utc?: string | null;
  aspect_orb?: number;
  return_orb?: number;
}

export interface SadeSatiResponse {
  is_active: boolean;
  /** 'first_year' (house 12), 'peak' (house 1), 'third_year' (house 2). Null if not active. */
  phase: string | null;
  house_from_moon: number | null;
  start_date: string | null;
  end_date: string | null;
}

export interface AshtamaShaniResponse {
  is_active: boolean;
  house_from_moon: number | null;
  start_date: string | null;
  end_date: string | null;
}

export interface ReturnPeriodResponse {
  planet: string;
  is_at_return: boolean;
  orb: number;
  estimated_return_date: string | null;
}

export interface TransitAspectResponse {
  /** 'conjunction' | 'opposition' | 'trine' | 'square' | 'sextile'. */
  aspect_type: string;
  transiting_planet: string;
  natal_planet: string;
  orb: number;
}

export interface TransitPatternsResponse {
  transit_datetime_utc: string;
  natal_moon_rashi: string;
  sade_sati: SadeSatiResponse;
  ashtama_shani: AshtamaShaniResponse;
  return_periods: ReturnPeriodResponse[];
  aspects: TransitAspectResponse[];
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

// ── Bulk Import (CSV/JSON upload of birth data) ──────────────────────────────

export interface BulkImportRow {
  subject_name: string;
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  place_name?: string | null;
  ayanamsa?: AyanamsaCode;
  house_system?: HouseSystemCode;
}

export interface BulkImportRowResult {
  row_index: number;
  subject_name: string;
  success: boolean;
  chart_id: string | null;
  error: string | null;
}

export interface BulkImportResponse {
  total: number;
  succeeded: number;
  failed: number;
  results: BulkImportRowResult[];
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

// ── Research Case Import (Module 27) ──────────────────────────────────────────

export type ResearchEventType =
  | "Marriage" | "Divorce" | "Promotion" | "Job Change" | "Accident"
  | "Surgery" | "Hospitalization" | "Child Birth" | "Death of Parent"
  | "Death of Spouse" | "Foreign Travel" | "Education" | "Property"
  | "Vehicle" | "Finance" | "Business" | "Political" | "Spiritual"
  | "Awards" | "Litigation" | "Health" | "Other";

export interface ResearchPerson {
  name?: string | null;
  gender: "Male" | "Female" | "Other";
  dob: string; // YYYY-MM-DD
  tob?: string | null; // HH:MM (24h)
  place: string;
  latitude: number;
  longitude: number;
  timezone: string; // IANA, e.g. Asia/Kolkata
  source: string; // Interview, Certificate, Self-report, ...
  birth_time_confidence?: "high" | "medium" | "low";
  country?: string | null; // optional — enables the dashboard's Country filter
}

export interface ResearchEventSnapshot {
  snapshot_date: string;
  snapshot_version?: string;
  current_dasha?: {
    mahadasha: string;
    antardasha: string;
    pratyantar?: string | null;
  } | null;
  transits?: Record<string, boolean> | null;
  shadbala?: Record<string, number> | null;
  active_yogas?: string[];
  varga_activations?: Record<string, string>;
  nakshatra_activations?: string[];
  house_lord_statuses?: Record<string, string>;
}

export interface ResearchLifeEvent {
  id?: string | null;
  type: ResearchEventType;
  event_date: string; // YYYY-MM-DD
  event_time?: string | null; // HH:MM
  event_place?: string | null;
  severity?: "Major" | "Moderate" | "Minor";
  category?: string;
  verified?: boolean;
  confidence?: "high" | "medium" | "low";
  source?: string;
  description?: string | null;
  tags?: string[];
  event_window_days?: number;
  notes?: string | null;
  snapshots?: ResearchEventSnapshot[];
  attachments?: ResearchAttachment[];
}

export interface ResearchAttachment {
  type?: string;
  filename?: string;
  url?: string | null;
  content_type?: string | null;
}

export interface ResearchCasePayload {
  id?: string | null;
  person: ResearchPerson;
  ayanamsa?: string;
  house_system?: string;
  divisional_charts?: string[];
  rectified?: boolean;
  rectification_notes?: string | null;
  life_events: ResearchLifeEvent[];
  research_notes?: string | null;
  attachments?: ResearchAttachment[];
  source_batch?: string | null;
}

export interface ResearchCaseBatchImport {
  cases: ResearchCasePayload[];
  generate_ids?: boolean;
}

// ── Research Case responses ──────────────────────────────────────────────────

export interface ResearchCaseImportResult {
  research_case_id: string;
  person_name: string | null;
  dob: string;
  total_events: number;
  total_snapshots_created: number;
  duplicate: boolean;
  errors: string[];
}

export interface ResearchCaseImportResponse {
  total_cases: number;
  succeeded: number;
  failed: number;
  results: ResearchCaseImportResult[];
}

export interface ValidationIssue {
  field: string;
  message: string;
  severity: string; // error | warning | info
}

export interface ResearchCaseValidation {
  valid: boolean;
  research_case_id: string | null;
  person_dob: string | null;
  issues: ValidationIssue[];
  duplicate_case: boolean;
  duplicate_events: string[];
}

export interface ResearchCaseBatchValidation {
  validations: ResearchCaseValidation[];
  total_valid: number;
  total_invalid: number;
}

export interface ResearchCaseSummary {
  research_case_id: string;
  person_name: string | null;
  dob: string;
  gender?: string | null;
  total_events: number;
  validation_status: string;
  duplicate_of_id?: string | null;
  created_at?: string | null;
}

export interface ResearchCaseListResponse {
  total: number;
  cases: ResearchCaseSummary[];
}

export interface LifeEventSnapshot {
  mahadasha: string | null;
  antardasha: string | null;
  pratyantar: string | null;
  active_yogas: string[];
  transit_features: Record<string, boolean>;
  house_lord_statuses: Record<string, string>;
  nakshatra_activations: string[];
  snapshot_version: string;
}

export interface LifeEventDetail {
  id: string;
  event_type: string;
  event_date: string;
  event_time?: string | null;
  event_place?: string | null;
  category: string;
  severity: string;
  description: string | null;
  notes: string | null;
  tags: string[];
  snapshot: LifeEventSnapshot | null;
}

export interface ResearchCaseDetail {
  research_case_id: string;
  person_name: string | null;
  dob: string;
  gender?: string | null;
  life_events: LifeEventDetail[];
}

// ── Feature extraction (Module 27, Phase 3) ───────────────────────────────────

export interface ExtractedFeature {
  feature_name: string;
  feature_value: string | number | boolean;
  feature_category: string; // yoga | dasha | transit | shadbala | house | nakshatra | varga
  event_type: string;
  research_case_id: string;
  event_date: string;
  confidence: number;
}

export interface FeatureExtractionResponse {
  total_features: number;
  features_by_category: Record<string, number>;
  features: ExtractedFeature[];
}

// ── Pattern discovery (Module 27, Phase 3) ────────────────────────────────────

export interface PatternDimension {
  dimension: string;
  value: string;
  frequency: number;
  count: number;
  expected_by_chance: number;
  significance: number;
}

export interface DiscoveredPattern {
  event_type: string;
  pattern_id: string;
  dimensions: PatternDimension[];
  sample_size: number;
  confidence_score: number;
  description: string;
}

export interface PatternDiscoveryRequest {
  event_type?: string | null;
  top_combos?: number;
  date_from?: string | null; // YYYY-MM-DD
  date_to?: string | null; // YYYY-MM-DD
}

export interface PatternDiscoveryResponse {
  event_type: string;
  total_cases: number;
  total_events: number;
  patterns: DiscoveredPattern[];
  execution_time_ms: number;
}

/** A personal "what-if" pattern search with custom thresholds — never
 * persisted to the shared dashboard, same formulas + dataset. */
export interface PatternExploreRequest {
  event_type?: string | null;
  min_significance?: number; // 0.5-0.999, shared default 0.90
  min_frequency?: number; // 0.01-1.0, shared default 0.10
  wilson_z?: number; // 0-3, shared default 1.0
  top_combos?: number;
  date_from?: string | null;
  date_to?: string | null;
}

/** A plain-language question about the shared discovered patterns —
 * e.g. "what correlates with Marriage?". Read-only, grounded: the answer
 * can only quote patterns that were actually fetched from the database. */
export interface PatternQuestionRequest {
  question: string;
}

export interface PatternQuestionResponse {
  question: string;
  matched_event_type: string | null;
  answer: string;
  patterns: PatternListItem[];
  execution_time_ms: number;
}

export interface PatternHypothesisRequest {
  event_type: string;
  conditions: Record<string, string>;
  min_confidence?: number;
}

export interface PatternHypothesisResponse {
  event_type: string;
  hypothesis: Record<string, string>;
  matching_cases: number;
  total_cases: number;
  proportion: number;
  confidence_score: number;
  supporting_events: Array<{
    research_case_id: string;
    event_type: string;
    event_date: string;
    matched_features: Array<{ dimension: string; value: string }>;
  }>;
}

// ── Pattern discovery dashboard (Module 27, Phase 3c) ─────────────────────────
// Reads over the persisted discovered_patterns / pattern_discovery_runs
// tables — none of these trigger recomputation on the backend.

export interface PatternSummary {
  total_cases: number;
  total_events: number;
  total_snapshots: number;
  patterns_found: number;
  high_confidence_patterns: number;
  knowledge_records: number;
}

export interface PatternListItem {
  pattern_id: string;
  event_type: string;
  description: string;
  sample_size: number;
  confidence_score: number;
  lift_score: number;
  has_explanation: boolean;
  dimension_count: number;
  categories: string[];
  discovered_at?: string | null;
}

export interface PatternListResponse {
  total: number;
  patterns: PatternListItem[];
}

export interface PatternListFilters {
  event_type?: string;
  min_confidence?: number;
  min_support?: number;
  gender?: string;
  country?: string;
  dataset?: string;
  chart?: string;
  category?: string;
  min_dimensions?: number;
  dimension?: string;
  value?: string;
  sort?: string;
  limit?: number;
}

/** Strictly read-only — fetching this never triggers an AI explanation call. */
export interface PatternDetail {
  pattern_id: string;
  event_type: string;
  description: string;
  dimensions: PatternDimension[];
  sample_size: number;
  confidence_score: number;
  lift_score: number;
  supporting_case_ids: string[];
  contradicting_case_ids: string[];
  algorithm_version: string;
  feature_version: string;
  snapshot_versions: string[];
  explanation: string | null;
  explanation_generated_at?: string | null;
  classical_references: string[];
  discovered_at?: string | null;
}

/** Returned only by POST .../explain — the sole path that calls the LLM. */
export interface PatternExplainResponse {
  pattern_id: string;
  explanation: string;
  explanation_generated_at: string;
}

export interface PatternExplainAllResponse {
  total_patterns: number;
  succeeded: number;
  failed: number;
  errors: string[];
}

export interface TopFactor {
  value: string;
  count: number;
}

export interface TopFactorsResponse {
  category: string;
  factors: TopFactor[];
}

export interface ConfidenceBucket {
  bucket: string; // "0-20" | "20-40" | "40-60" | "60-80" | "80-100"
  count: number;
}

export interface ConfidenceDistributionResponse {
  buckets: ConfidenceBucket[];
}

export interface PatternGraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
  size: number;
  category: string;
}

export interface PatternGraphEdge {
  from: string;
  to: string;
}

export interface PatternGraphResponse {
  nodes: PatternGraphNode[];
  edges: PatternGraphEdge[];
}

export interface PatternTrendPoint {
  run_at: string;
  confidence_score: number;
}

/** Populates once >=2 discovery runs have touched this pattern_id; a
 * single point otherwise — render a flat/short trend, not an error. */
export interface PatternTrendResponse {
  pattern_id: string;
  points: PatternTrendPoint[];
}

// ── Advanced Research tools (Module 27, Phase 3c) ─────────────────────────────

export interface DatasetValidationReport {
  total_cases: number;
  cases_without_snapshots: string[];
  life_events_without_snapshots: number;
  stale_snapshot_case_ids: string[];
  duplicate_case_ids: string[];
}

export interface SnapshotRebuildResult {
  cases_processed: number;
  snapshots_created: number;
  snapshot_version: string;
  errors: string[];
}

export interface EvidenceRecalculationResult {
  patterns_refreshed: number;
}
