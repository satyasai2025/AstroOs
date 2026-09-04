/**
 * AstroOS — Structured Narrative & Comparative Reporting Client Library
 */

import { api } from "@/lib/api";

export interface TechnicalEvidenceItem {
  evidence_id: string;
  category: string;
  parameter_name: string;
  computed_value: string;
  classical_reference?: string | null;
  confidence_or_strength: string;
}

export interface MultiVargaGrahaRow {
  planet: string;
  d1_rashi: string;
  d1_house: number;
  d1_dignity: string;
  d9_rashi: string;
  d9_dignity: string;
  d10_rashi: string;
  d10_dignity: string;
  d7_rashi: string;
  d7_dignity: string;
  is_vargottama: boolean;
}

export interface NarrativeParagraph {
  paragraph_index: number;
  heading: string;
  content_text: string;
  referenced_evidence_ids: string[];
}

export interface StructuredNarrativeSection {
  section_type: string;
  title: string;
  subtitle: string;
  paragraphs: NarrativeParagraph[];
  evidence_table: TechnicalEvidenceItem[];
  raw_section_data: Record<string, unknown>;
}

export interface ComparativeChartMetrics {
  chart_a_name: string;
  chart_b_name: string;
  lagna_relationship: string;
  moon_relationship: string;
  ashtakoota_guna_score?: number | null;
  varga_dignity_overlap_score: number;
  synastry_aspects: string[];
  comparative_summary: string;
  evidence_items: TechnicalEvidenceItem[];
}

export interface FullStructuredAstrologicalReportResponse {
  report_id: string;
  report_title: string;
  subject_name: string;
  birth_datetime_iso: string;
  latitude: number;
  longitude: number;
  ayanamsa: string;
  house_system: string;
  generated_at_iso: string;
  sections: StructuredNarrativeSection[];
  multi_varga_matrix: MultiVargaGrahaRow[];
  all_evidence_index: Record<string, TechnicalEvidenceItem>;
  comparative_analysis?: ComparativeChartMetrics | null;
  overall_confluence_summary: string;
}

export interface DocumentExportResponse {
  export_format: string;
  filename: string;
  mime_type: string;
  content_base64_or_text: string;
  size_bytes: number;
}

export async function generateNarrativeReport(params: {
  chart: Record<string, unknown>;
  subject_name?: string;
  report_title?: string;
  transit_datetime_iso?: string;
}): Promise<FullStructuredAstrologicalReportResponse> {
  return api.post<FullStructuredAstrologicalReportResponse>("/api/v1/report/narrative", params);
}

export async function generateComparativeNarrativeReport(params: {
  chart_a: Record<string, unknown>;
  chart_b: Record<string, unknown>;
  chart_a_name?: string;
  chart_b_name?: string;
  report_title?: string;
}): Promise<FullStructuredAstrologicalReportResponse> {
  return api.post<FullStructuredAstrologicalReportResponse>("/api/v1/report/comparative-narrative", params);
}

export async function exportReportDocument(params: {
  report: Record<string, unknown>;
  export_format: "pdf" | "html" | "csv" | "json";
  include_tables?: boolean;
}): Promise<DocumentExportResponse> {
  return api.post<DocumentExportResponse>("/api/v1/report/export-document", params);
}
