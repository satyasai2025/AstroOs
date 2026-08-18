/**
 * AstroOS — Research API Client (Phase I.4)
 *
 * Client-side wrappers for all research tools endpoints:
 * - Research projects CRUD
 * - Snapshot management & comparison
 * - Research mode toggle & query logs
 * - Hypothesis validation workflow
 * - CSV/JSON export with citations
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";

// ── Types (mirror of backend schemas) ────────────────────────────────────────

export interface ResearchProject {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface ResearchProjectListResponse {
  projects: ResearchProject[];
  total: number;
}

export interface ResearchSnapshot {
  id: string;
  project_id: string;
  chart_id: string;
  label: string | null;
  captured_at: string;
  snapshot_version: string;
}

export interface SnapshotListResponse {
  snapshots: ResearchSnapshot[];
  total: number;
}

export interface FieldDiff {
  field: string;
  value_a: unknown;
  value_b: unknown;
}

export interface SnapshotComparisonResponse {
  snapshot_a_id: string;
  snapshot_b_id: string;
  chart_id_a: string;
  chart_id_b: string;
  matching_fields: string[];
  differing_fields: FieldDiff[];
}

export interface ResearchMode {
  enabled: boolean;
  user_id: string;
  total_logged_queries: number;
}

export interface QueryLogEntry {
  id: string;
  user_id: string;
  action: string;
  request_payload: Record<string, unknown>;
  response_summary: string;
  duration_ms: number;
  created_at: string | null;
}

export interface QueryLogListResponse {
  logs: QueryLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface HypothesisValidation {
  id: string;
  hypothesis_id: string;
  chart_id: string;
  project_id: string;
  title: string;
  description: string;
  domain: string;
  ai_generated: boolean;
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  reviewer_notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface HypothesisValidationListResponse {
  validations: HypothesisValidation[];
  total: number;
  limit: number;
  offset: number;
}

// ── Research Projects API ────────────────────────────────────────────────────

export const researchProjectsApi = {
  /** List projects owned by the authenticated user (server derives the
   * user from the auth token — it's no longer a client-supplied param,
   * since trusting a client-passed user_id let any researcher read
   * anyone else's projects). */
  list: (statusFilter?: string) => {
    const params = new URLSearchParams();
    if (statusFilter) params.set("status_filter", statusFilter);
    const qs = params.toString();
    return api.get<ResearchProjectListResponse>(
      `/api/v1/research/projects${qs ? `?${qs}` : ""}`
    );
  },

  /** Get a single project */
  get: (projectId: string) =>
    api.get<ResearchProject>(`/api/v1/research/projects/${projectId}`),

  /** Create a new project (ownership is derived server-side from the
   * authenticated user, not sent by the client). */
  create: (data: { title: string; description?: string | null }) =>
    api.post<ResearchProject>("/api/v1/research/projects", data),

  /** Update a project */
  update: (projectId: string, data: {
    title?: string;
    description?: string | null;
    status?: string;
  }) => api.patch<ResearchProject>(`/api/v1/research/projects/${projectId}`, data),

  /** Delete a project */
  delete: (projectId: string) =>
    api.delete<void>(`/api/v1/research/projects/${projectId}`),
};

// ── Snapshots API ────────────────────────────────────────────────────────────

export const snapshotsApi = {
  /** List snapshots for a project */
  list: (projectId: string) =>
    api.get<SnapshotListResponse>(
      `/api/v1/research/projects/${projectId}/snapshots`
    ),

  /** Get a single snapshot */
  get: (snapshotId: string) =>
    api.get<ResearchSnapshot>(`/api/v1/research/snapshots/${snapshotId}`),

  /** Capture a new snapshot */
  capture: (
    projectId: string,
    data: { chart_id: string; label?: string | null }
  ) =>
    api.post<ResearchSnapshot>(
      `/api/v1/research/projects/${projectId}/snapshots`,
      data
    ),

  /** Delete a snapshot */
  delete: (snapshotId: string) =>
    api.delete<void>(`/api/v1/research/snapshots/${snapshotId}`),

  /** Compare two snapshots */
  compare: (snapshotAId: string, snapshotBId: string) =>
    api.post<SnapshotComparisonResponse>("/api/v1/research/snapshots/compare", {
      snapshot_a_id: snapshotAId,
      snapshot_b_id: snapshotBId,
    }),
};

// ── Research Mode API ────────────────────────────────────────────────────────

export const researchModeApi = {
  /** Check if research mode is enabled */
  get: () => api.get<ResearchMode>("/api/v1/research-tools/mode"),

  /** Set research mode */
  set: (enabled: boolean) =>
    api.put<ResearchMode>("/api/v1/research-tools/mode", { enabled }),

  /** List query logs */
  listLogs: (params?: { action?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.action) searchParams.set("action", params.action);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    return api.get<QueryLogListResponse>(
      `/api/v1/research-tools/logs?${searchParams.toString()}`
    );
  },

  /** Clear query logs */
  clearLogs: () => api.delete<void>("/api/v1/research-tools/logs"),
};

// ── Hypothesis Validation API ────────────────────────────────────────────────

export const hypothesisValidationApi = {
  /** Flag a hypothesis for human review */
  flag: (data: {
    hypothesis_id: string;
    chart_id: string;
    project_id: string;
    title: string;
    description: string;
    domain: string;
    hypothesis_data?: Record<string, unknown>;
    ai_generated?: boolean;
  }) => api.post<HypothesisValidation>("/api/v1/research-tools/validations", data),

  /** List validation records */
  list: (params?: {
    project_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.project_id) searchParams.set("project_id", params.project_id);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    return api.get<HypothesisValidationListResponse>(
      `/api/v1/research-tools/validations?${searchParams.toString()}`
    );
  },

  /** Get a single validation record */
  get: (validationId: string) =>
    api.get<HypothesisValidation>(
      `/api/v1/research-tools/validations/${validationId}`
    ),

  /** Confirm or reject a hypothesis */
  update: (
    validationId: string,
    data: { status: "confirmed" | "rejected"; reviewer_notes?: string | null }
  ) =>
    api.patch<HypothesisValidation>(
      `/api/v1/research-tools/validations/${validationId}`,
      data
    ),

  /** Delete a validation record */
  delete: (validationId: string) =>
    api.delete<void>(`/api/v1/research-tools/validations/${validationId}`),
};

// ── Research Export API ──────────────────────────────────────────────────────

export const researchExportApi = {
  /** Export research project data as CSV or JSON with citations */
  export: async (
    projectId: string,
    format: "csv" | "json" = "csv",
    includeDetail: boolean = true
  ): Promise<Blob> => {
    let access: string | null = null;
    try {
      access = localStorage.getItem("astro_access_token");
    } catch {
      // storage access blocked by browser/privacy settings
    }
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (access) {
      headers["Authorization"] = `Bearer ${access}`;
    }

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";
    const res = await fetch(
      `${apiBase}/api/v1/research-tools/export/${projectId}`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ format, include_detail: includeDetail }),
      }
    );

    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        detail = body.detail ?? detail;
      } catch {
        // ignore
      }
      throw new Error(detail);
    }

    return res.blob();
  },
};

// ── Compatibility API ────────────────────────────────────────────────────────

export interface KootaScore {
  name: string;
  max_score: number;
  obtained_score: number;
  status: string;
  description: string;
}

export interface DoshaResult {
  name: string;
  has_dosha: boolean;
  severity: string;
  description: string;
}

export interface CompatibilityRequest {
  birth_datetime_utc_a: string;
  latitude_a: number;
  longitude_a: number;
  subject_name_a?: string;
  birth_datetime_utc_b: string;
  latitude_b: number;
  longitude_b: number;
  subject_name_b?: string;
  relationship_type?: string;
  ayanamsa?: string;
  house_system?: string;
}

export interface CompatibilityResponse {
  total_score: number;
  max_total_score: number;
  compatibility_percentage: number;
  verdict: string;
  kootas: KootaScore[];
  doshas: DoshaResult[];
  radar_values: Record<string, number>;
  strengths: string[];
  challenges: string[];
  recommendations: string[];
  subject_name_a: string;
  subject_name_b: string;
}

export const compatibilityApi = {
  analyze: (data: CompatibilityRequest) =>
    api.post<CompatibilityResponse>("/api/v1/ai/compatibility", data),
};

// ── Marriage Timing API (Jupiter/Saturn Transit Scanner) ─────────────────────

export type MarriageTimingStatus = "probable" | "delayed" | "not_indicated";

export interface MarriageTimingRequest {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  subject_name?: string;
  scan_start_age?: number;
  scan_end_age?: number;
  ayanamsa?: string;
  house_system?: string;
}

export interface TransitScanYear {
  year: number;
  age_at_year: number;
  julian_day: number;
  jupiter_sidereal: number;
  jupiter_rashi: string;
  saturn_sidereal: number;
  saturn_rashi: string;
  status: MarriageTimingStatus;
  aspect_details: string[];
  saturn_obstruction_details: string[];
}

export interface MarriageTimingResponse {
  subject_name: string;
  birth_datetime_utc: string;
  scan_start_age: number;
  scan_end_age: number;
  natal_venus_rashi: string;
  natal_venus_longitude: number;
  natal_seventh_cusp_rashi: string;
  total_years_scanned: number;
  probable_windows: number;
  delayed_windows: number;
  scan_results: TransitScanYear[];
}

export const marriageTimingApi = {
  scan: (data: MarriageTimingRequest) =>
    api.post<MarriageTimingResponse>("/api/v1/ai/marriage-timing", data),
};

// ── Sadhu Padhdhati Marriage Timing (alternate method) ──────────────────────

export interface SadhuPadhdhatiRequest {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  subject_name?: string;
  gender: "male" | "female";
  ayanamsa?: string;
  house_system?: string;
}

export interface SadhuPadhdhatiLevel {
  label: string;
  yes_count: number;
  max_count: number;
  badhaka: boolean;
}

export interface SadhuPadhdhatiChart {
  chart_label: string;
  base: number;
  step: number;
  escalation_factor: number;
  male_female_factor: number;
  reducing_factor: number;
  delay: number;
  levels: SadhuPadhdhatiLevel[];
}

export interface SadhuPadhdhatiResponse {
  subject_name: string;
  birth_year: number;
  gender: string;
  d1: SadhuPadhdhatiChart;
  d9: SadhuPadhdhatiChart;
  net_delay: number;
  predicted_year: number;
  window_start: number;
  window_end: number;
  alphabet_class: string | null;
  destiny_factor: number | null;
}

export const sadhuPadhdhatiApi = {
  analyze: (data: SadhuPadhdhatiRequest) =>
    api.post<SadhuPadhdhatiResponse>("/api/v1/ai/sadhu-padhdhati-timing", data),
};

// ── Best Bet 58-Point Compatibility API ─────────────────────────────────────

export interface BestBetSubFactor {
  name: string;
  score: number;
  max: number;
  description: string;
}

export interface BestBetCompatibilityResponse {
  subject_name_a: string;
  subject_name_b: string;
  total_score: number;
  max_score: number;
  percentage: number;
  verdict: string;
  status: string;
  practical_score: number;
  practical_max: number;
  karmic_score: number;
  karmic_max: number;
  future_score: number;
  future_max: number;
  spiritual_score: number;
  spiritual_max: number;
  psychological_score: number;
  psychological_max: number;
  physical_score: number;
  physical_max: number;
  mars_dosha_score: number;
  mars_dosha_max: number;
  karmic_pattern_score: number;
  karmic_pattern_max: number;
  dasha_score: number;
  dasha_max: number;
  mutual_planets_score: number;
  mutual_planets_max: number;
  sub_factors: BestBetSubFactor[];
  strengths: string[];
  challenges: string[];
  recommendations: string[];
}

export interface BestBetCompatibilityRequest {
  birth_datetime_utc_a: string;
  latitude_a: number;
  longitude_a: number;
  subject_name_a?: string;
  birth_datetime_utc_b: string;
  latitude_b: number;
  longitude_b: number;
  subject_name_b?: string;
  ayanamsa?: string;
  house_system?: string;
}

export const bestBetApi = {
  analyze: (data: BestBetCompatibilityRequest) =>
    api.post<BestBetCompatibilityResponse>("/api/v1/ai/best-bet-compatibility", data),
};

// ── Export API ───────────────────────────────────────────────────────────────

export interface CompatibilityExportRequest {
  birth_datetime_utc_a: string;
  latitude_a: number;
  longitude_a: number;
  subject_name_a?: string;
  birth_datetime_utc_b: string;
  latitude_b: number;
  longitude_b: number;
  subject_name_b?: string;
  relationship_type?: string;
  ayanamsa?: string;
  house_system?: string;
  format?: "json" | "markdown" | "html";
}

export const exportApi = {
  /** Export compatibility report as JSON, Markdown, or HTML */
  compatibility: (data: CompatibilityExportRequest) => {
    const access = localStorage.getItem("astro_access_token");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (access) {
      headers["Authorization"] = `Bearer ${access}`;
    }

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";
    return fetch(`${apiBase}/api/v1/export/comparison`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        ...data,
        format: data.format ?? "json",
        charts: [
          {
            birth_datetime_utc: data.birth_datetime_utc_a,
            latitude: data.latitude_a,
            longitude: data.longitude_a,
            subject_name: data.subject_name_a,
            ayanamsa: data.ayanamsa,
            house_system: data.house_system,
            label: data.subject_name_a || "Person A",
          },
          {
            birth_datetime_utc: data.birth_datetime_utc_b,
            latitude: data.latitude_b,
            longitude: data.longitude_b,
            subject_name: data.subject_name_b,
            ayanamsa: data.ayanamsa,
            house_system: data.house_system,
            label: data.subject_name_b || "Person B",
          },
        ],
      }),
    });
  },
};

// ── React Query Hooks ────────────────────────────────────────────────────────

export function useResearchProjects(userId?: string) {
  return useQuery({
    queryKey: ["research", "projects", userId],
    queryFn: () => (userId ? researchProjectsApi.list(userId) : Promise.resolve({ projects: [], total: 0 })),
    enabled: !!userId,
  });
}

export function useQueryLogs(limit = 10) {
  return useQuery({
    queryKey: ["research", "logs", limit],
    queryFn: () => researchModeApi.listLogs({ limit }),
  });
}

export function useHypotheses(projectId?: string) {
  return useQuery({
    queryKey: ["research", "hypotheses", projectId],
    queryFn: () => hypothesisValidationApi.list({ project_id: projectId }),
  });
}

