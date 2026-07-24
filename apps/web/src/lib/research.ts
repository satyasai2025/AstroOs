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
  /** List all projects for a user */
  list: (userId: string, statusFilter?: string) => {
    const params = new URLSearchParams({ user_id: userId });
    if (statusFilter) params.set("status_filter", statusFilter);
    return api.get<ResearchProjectListResponse>(
      `/api/v1/research/projects?${params.toString()}`
    );
  },

  /** Get a single project */
  get: (projectId: string) =>
    api.get<ResearchProject>(`/api/v1/research/projects/${projectId}`),

  /** Create a new project */
  create: (data: {
    user_id: string;
    title: string;
    description?: string | null;
  }) => api.post<ResearchProject>("/api/v1/research/projects", data),

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
