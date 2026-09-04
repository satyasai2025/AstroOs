/**
 * AstroOS — Classical Rule Evidence Engine Client Library
 *
 * Provides API clients and types for:
 * 1. Canonical Classical Literature (BPHS, Saravali, Jaimini, Brihat Jataka, Phaladeepika)
 * 2. 5-Stage Deterministic Rule Evidence Chains
 * 3. Chart Condition Evaluation and Cancellation Factor Detection
 */

import { api } from "@/lib/api";

export interface ClassicalSourceCitation {
  book_title: string;
  author: string;
  chapter: number;
  chapter_name: string;
  sloka_range: string;
  sanskrit_iast: string;
  sanskrit_devanagari: string;
  translation_english: string;
  tradition: string;
  commentary_notes?: string | null;
  is_verified: boolean;
}

export interface ConditionRequirement {
  condition_id: string;
  description: string;
  condition_type: string;
  required_parameters: Record<string, unknown>;
  is_mandatory: boolean;
}

export interface ChartEvidenceItem {
  condition_id: string;
  is_satisfied: boolean;
  actual_chart_value: string;
  notes?: string;
  contributing_planets: string[];
  contributing_houses: number[];
}

export interface CancellationFactor {
  factor_id: string;
  description: string;
  classical_reference: string;
  is_active: boolean;
  impact_deduction: number;
}

export interface RuleEvidenceChain {
  rule_id: string;
  rule_name: string;
  category: string;
  brief_description: string;
  citation: ClassicalSourceCitation;
  required_conditions: ConditionRequirement[];
  actual_evidence: ChartEvidenceItem[];
  status: "SATISFIED" | "PARTIALLY_SATISFIED" | "CANCELLED_AFFLICTED" | "NOT_PRESENT" | "UNVERIFIED";
  strength_score: number;
  cancellation_factors: CancellationFactor[];
  fructification_summary: string;
  audit_trace: string[];
}

export interface ClassicalRuleExploreItem {
  rule_id: string;
  rule_name: string;
  category: string;
  book_title: string;
  author: string;
  chapter_info: string;
  tradition: string;
  brief_description: string;
  sanskrit_preview: string;
  translation_preview: string;
  is_verified: boolean;
}

export interface ClassicalRuleExploreResponse {
  total_rules: number;
  rules: ClassicalRuleExploreItem[];
}

export interface EvaluateChartRuleEvidenceResponse {
  evaluated_chart_id?: string | null;
  total_rules_evaluated: number;
  satisfied_rules_count: number;
  partially_satisfied_count: number;
  cancelled_count: number;
  evidence_chains: RuleEvidenceChain[];
}

export async function fetchClassicalRules(params?: {
  tradition?: string;
  category?: string;
  query?: string;
}): Promise<ClassicalRuleExploreResponse> {
  const queryParams = new URLSearchParams();
  if (params?.tradition && params.tradition !== "all") queryParams.set("tradition", params.tradition);
  if (params?.category && params.category !== "all") queryParams.set("category", params.category);
  if (params?.query) queryParams.set("query", params.query);

  const qs = queryParams.toString();
  const url = `/api/v1/rules/explore${qs ? `?${qs}` : ""}`;
  return api.get<ClassicalRuleExploreResponse>(url);
}

export async function fetchRuleDetails(ruleId: string): Promise<Record<string, unknown>> {
  return api.get<Record<string, unknown>>(`/api/v1/rules/${encodeURIComponent(ruleId)}/details`);
}

export async function evaluateChartRuleEvidence(chart: Record<string, unknown>): Promise<EvaluateChartRuleEvidenceResponse> {
  return api.post<EvaluateChartRuleEvidenceResponse>("/api/v1/rules/evaluate-chart", { chart });
}
