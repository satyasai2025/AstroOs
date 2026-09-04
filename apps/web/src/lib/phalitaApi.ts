/**
 * AstroOS — Canonical Phalita MoE & 3-Chart Synthesis API Client
 *
 * Types and methods for connecting frontend components to:
 * 1. POST /api/v1/phalita/canonical-synthesis
 * 2. POST /api/v1/phalita/vpc-timeline
 * 3. POST /api/v1/phalita/noise-diagnostics
 */

import { api } from "@/lib/api";

export interface CanonicalHouseSpan {
  house_number: number;
  start_sandhi: number;
  madhya: number;
  end_sandhi: number;
  primary_lord: string;
  primary_rashi: string;
  secondary_lord?: string | null;
  secondary_rashi?: string | null;
  total_span_deg: number;
}

export interface SudarshanaChakraProfile {
  net_functional_score: number;
  is_functional_benefic: boolean;
  is_functional_malefic: boolean;
}

export interface SudarshanaChakraSynthesis {
  lagna_rashi: string;
  sun_rashi: string;
  moon_rashi: string;
  is_tri_lagna_active: boolean;
  sun_in_lagna: boolean;
  moon_in_lagna: boolean;
  profiles: Record<string, SudarshanaChakraProfile>;
}

export interface DivisionalSynthesisItem {
  d1_dignity: string;
  d1_s_eff: number;
  d10_dignity: string;
  d10_s_eff: number;
  verdict: "REINFORCING" | "D1_PREVAILS" | "OPPOSITION";
}

export interface VPCSCDMonthlyEntry {
  scd_house: number;
  entry_datetime_utc: string;
}

export interface MunthaData {
  rashi: string;
  rashi_index: number;
  house_number: number;
  lord: string;
}

export interface YearLordData {
  selected: string;
  selection_method: string;
  candidates: string[];
}

export interface VarshaAscendantData {
  rashi: string;
  rashi_degree: number;
  longitude: number;
  sidereal_longitude: number;
  nakshatra?: string;
  pada?: number;
}

export interface ChartPlanetPosition {
  planet: string;
  rashi: string;
  rashi_degree: number;
  house_number: number;
  sidereal_longitude: number;
  is_retrograde: boolean;
  dignity?: string;
}

export interface PanchavargiyaBalaItem {
  planet: string;
  total_score: number;
  visheshika_bala: number;
  strength_category: string;
}

export interface SahamItem {
  name: string;
  rashi: string;
  sidereal_longitude: number;
}

export interface VPCSolarReturnReport {
  target_year: number;
  completed_years: number;
  vpc_datetime_utc: string;
  scd_annual_house: number;
  sun_longitude_deg?: number;
  muntha?: MunthaData;
  year_lord?: YearLordData;
  varsha_ascendant?: VarshaAscendantData;
  varsha_planets?: ChartPlanetPosition[];
  panchavargiya_bala?: PanchavargiyaBalaItem[];
  sahams?: SahamItem[];
  monthly_entries: VPCSCDMonthlyEntry[];
}

export interface TPhalitSignedState {
  deterministic_score: number;
  block_totals: Record<string, number>;
  atomic_features: Record<string, number>;
}

export interface CanonicalSynthesisResponse {
  birth_datetime_utc: string;
  lagna_madhya_deg: number;
  madhya_lagna_deg: number;
  natal_ascendant?: {
    rashi: string;
    rashi_degree: number;
    sidereal_longitude: number;
  };
  natal_planets?: ChartPlanetPosition[];
  houses: CanonicalHouseSpan[];
  sudarshana_chakra: SudarshanaChakraSynthesis;
  divisional_synthesis_d10: Record<string, DivisionalSynthesisItem>;
  vpc_solar_return: VPCSolarReturnReport;
  tphalit_signed_state: TPhalitSignedState;
}

export interface VPCTimelineEntry {
  year: number;
  completed_age: number;
  vpc_datetime_utc: string;
  scd_annual_house: number;
  monthly_entries_count: number;
}

export interface VPCTimelineResponse {
  birth_datetime_utc: string;
  solar_returns: VPCTimelineEntry[];
}

export interface NoiseDiagnosticsResponse {
  data_noise_score: number;
  rules_noise_score: number;
  model_noise_score: number;
  useful_noise_bandwidth: number;
  dominant_noise_category: "DATA" | "RULES" | "MODEL" | "CLEAN";
  is_prediction_trustworthy: boolean;
}

export interface CognitiveEventPredictionRequest {
  birth_datetime: string; // ISO-8601 string (e.g. "1990-05-15T12:00:00Z")
  latitude: number;
  longitude: number;
  ayanamsa?: string;
  target_dasha?: {
    md?: string;
    ad?: string;
    pd?: string;
    sk?: string;
    pr?: string;
  };
}

export interface ExpertFinding {
  expert_name: string;
  domain: string;
  expert_score: number;
  confidence: number;
  key_findings: string[];
  supporting_factors: string[];
  afflicting_factors: string[];
}

export interface ConflictResolutionSummary {
  has_conflict: boolean;
  conflict_type: string;
  precedence_rule_applied: string;
  adjusted_score: number;
  resolution_narrative: string;
}

export interface PhalitaMoEConsultationResponse {
  domain: string;
  final_cognitive_score: number; // 0 to 9 Cognitive Score
  is_probable: boolean;
  gating_weights: Record<string, number>;
  expert_breakdown: Record<string, ExpertFinding>;
  conflict_resolution: ConflictResolutionSummary;
  consensus_summary: string;
  actionable_recommendation: string;
  rule_traces: string[];
}

export interface CognitiveEventPredictionResponse {
  event_type: string;
  cognitive_score: number; // 0 to 9 Cognitive Score
  is_probable: boolean;
  upagraha_modifier: number;
  reasoning_summary: string;
  rule_traces: string[];
  level_assessments: Array<{
    level_name: string;
    lord: string;
    is_house_lord: boolean;
    is_occupant: boolean;
    aspect_strength: number;
    dignity_score: number;
    level_score: number;
    reasons: string[];
  }>;
}

export type PhalitaLifeDomain =
  | "health"
  | "wealth"
  | "siblings"
  | "property"
  | "children"
  | "legal"
  | "marriage"
  | "accident"
  | "father"
  | "career"
  | "gains"
  | "foreign"
  | "general";

export interface LifeDomainMeta {
  id: PhalitaLifeDomain;
  label: string;
  sanskritName: string;
  bhava: number;
  varga: string;
  icon: string;
  description: string;
}

export const CANONICAL_12_DOMAINS: LifeDomainMeta[] = [
  { id: "health", label: "Health & Vitality", sanskritName: "Tanu Bhava", bhava: 1, varga: "D1", icon: "Activity", description: "Constitution, longevity, physical resilience and vitality." },
  { id: "wealth", label: "Wealth & Assets", sanskritName: "Dhana Bhava", bhava: 2, varga: "D2", icon: "Coins", description: "Liquid wealth, family lineage, speech, and financial reserves." },
  { id: "siblings", label: "Siblings & Courage", sanskritName: "Sahaja Bhava", bhava: 3, varga: "D3", icon: "Users", description: "Younger co-borns, enterprise, initiative, and manual skill." },
  { id: "property", label: "Property & Vehicles", sanskritName: "Bandhu Bhava", bhava: 4, varga: "D4", icon: "Home", description: "Fixed assets, real estate, vehicles, mother, and inner happiness." },
  { id: "children", label: "Progeny & Intellect", sanskritName: "Putra Bhava", bhava: 5, varga: "D7", icon: "Sparkles", description: "Children, creative intelligence, speculative gains, and Purvapunya." },
  { id: "legal", label: "Litigation & Debts", sanskritName: "Shatru Bhava", bhava: 6, varga: "D6", icon: "ShieldAlert", description: "Enemies, debts, legal battles, competitive exams, and acute illness." },
  { id: "marriage", label: "Spouse & Partnership", sanskritName: "Kalatra Bhava", bhava: 7, varga: "D9", icon: "Heart", description: "Marriage, business partnerships, marital bliss, and social relations." },
  { id: "accident", label: "Crises & Longevity", sanskritName: "Randhra Bhava", bhava: 8, varga: "D8", icon: "AlertTriangle", description: "Sudden transformations, accidents, inheritance, and chronic vulnerabilities." },
  { id: "father", label: "Father & Higher Dharma", sanskritName: "Dharma Bhava", bhava: 9, varga: "D12", icon: "Compass", description: "Guru, father, spiritual righteousness, pilgrimage, and supreme fortune." },
  { id: "career", label: "Career & Status", sanskritName: "Karma Bhava", bhava: 10, varga: "D10", icon: "Briefcase", description: "Professional status, executive authority, public reputation, and Rajayogas." },
  { id: "gains", label: "Gains & Fulfillment", sanskritName: "Labha Bhava", bhava: 11, varga: "D11", icon: "TrendingUp", description: "Elder siblings, vast financial inflows, ambition fulfillment, and peer network." },
  { id: "foreign", label: "Foreign & Liberation", sanskritName: "Vyaya Bhava", bhava: 12, varga: "D12", icon: "Plane", description: "Overseas relocation, expenditure, spiritual liberation, and hospitalization." },
];

export interface DivisionalPlanetItem {
  planet: string;
  rashi: string;
  rashi_index: number;
  rashi_degree: number;
  house_number: number;
  is_bhavottama: boolean;
  bhavottama_type: string;
  dignity_label: string;
  dignity_score: number;
  final_varga_strength: number;
  is_debilitation_cancelled: boolean;
}

export interface DivisionalExplorationResponse {
  varga_code: string;
  varga_number: number;
  varga_name: string;
  significations: string;
  vimshopaka_weight: number;
  ascendant_rashi: string;
  ascendant_rashi_idx: number;
  ascendant_degree: number;
  planets: DivisionalPlanetItem[];
  bhavottama_planets: string[];
  active_divisional_dasha: {
    varga_number: number;
    varga_code: string;
    target_date: string;
    mahadasha_lord: string;
    antardasha_lord: string;
    pratyantardasha_lord: string;
    md_start_date: string;
    md_end_date: string;
    ad_start_date: string;
    ad_end_date: string;
  };
  dual_dasha_comparison: {
    domain: string;
    target_varga: number;
    d1_md_lord: string;
    d1_ad_lord: string;
    div_md_lord: string;
    div_ad_lord: string;
    d1_combined_strength: number;
    div_combined_strength: number;
    is_divisional_supportive: boolean;
    siddhantic_verdict: string;
  };
  shastric_confluence_summary: string;
}

export interface ShastricPipelineResponse {
  domain: string;
  target_date_iso: string;
  calibrated_signal_score: number;
  signal_tier: string;
  confidence_percentage: number;
  confidence_margin_delta: number;
  primary_promisers: string[];
  primary_inhibitors: string[];
  evidence_provenance_id: string;
  executive_verdict: string;
  shastric_citations: string[];
  dasha_timing_synthesis: string;
  friction_analysis: string;
  siddhantic_counsel: string;
  full_markdown_report: string;
}

export interface Validation3TierAuditResponse {
  timestamp_iso: string;
  overall_system_status: string;
  tier1_regression: {
    tier_name: string;
    total_cases: number;
    passed_cases: number;
    is_clean: boolean;
  };
  tier2_generalization: {
    tier_name: string;
    total_cohort_charts: number;
    total_evaluated_windows: number;
    precision: number;
    recall_sensitivity: number;
    false_positive_rate: number;
    specificity: number;
    roc_auc_score: number;
    pr_auc_score: number;
    brier_calibration_score: number;
    is_statistically_robust: boolean;
    domain_breakdown: Record<string, Record<string, number>>;
  };
  tier3_holdout: {
    tier_name: string;
    total_holdout_charts: number;
    pre_freeze_hash: string;
    precision: number;
    recall: number;
    fpr: number;
    roc_auc: number;
    zero_leakage_verified: boolean;
    is_validation_passed: boolean;
  };
}

export const phalitaApi = {
  getCanonicalSynthesis: (params: {
    birth_date_iso: string;
    latitude: number;
    longitude: number;
    target_year?: number;
  }) => api.post<CanonicalSynthesisResponse>("/api/v1/phalita/canonical-synthesis", params),

  getVPCTimeline: (params: {
    birth_date_iso: string;
    latitude: number;
    longitude: number;
    start_year: number;
    end_year: number;
  }) => api.post<VPCTimelineResponse>("/api/v1/phalita/vpc-timeline", params),

  getNoiseDiagnostics: (params: {
    latitude: number;
    longitude: number;
    deterministic_score: number;
    planet_block_total: number;
    residual_error: number;
    varga_opposition_index?: number;
  }) => api.post<NoiseDiagnosticsResponse>("/api/v1/phalita/noise-diagnostics", params),

  synthesizeMoE: (params: CognitiveEventPredictionRequest, domain: PhalitaLifeDomain = "general") =>
    api.post<PhalitaMoEConsultationResponse>(`/api/v1/phalita/moe/synthesize?domain=${encodeURIComponent(domain)}`, params),

  predictEvent: (eventType: PhalitaLifeDomain, params: CognitiveEventPredictionRequest) =>
    api.post<CognitiveEventPredictionResponse>(`/api/v1/phalita/cognitive/predict/${eventType}`, params),

  getDivisionalExploration: (params: {
    birth_date_iso: string;
    latitude: number;
    longitude: number;
    varga_number: number;
    target_date_iso?: string;
    ayanamsa?: string;
  }) => api.post<DivisionalExplorationResponse>("/api/v1/phalita/divisional/explore", params),

  executeShastricPipeline: (params: {
    birth_datetime: string;
    latitude: number;
    longitude: number;
    domain?: string;
    target_date?: string;
    ayanamsa?: string;
  }) => api.post<ShastricPipelineResponse>("/api/v1/phalita/reasoning/pipeline", params),

  get3TierValidationAudit: () =>
    api.get<Validation3TierAuditResponse>("/api/v1/phalita/validation/3tier-audit"),
};




