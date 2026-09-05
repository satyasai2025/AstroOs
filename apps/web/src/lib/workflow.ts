/**
 * AstroOS — Workflow Orchestrator API calls (TanStack Query integration)
 *
 * One mutation: submit birth details, get back the full Unified
 * Analysis Pipeline result (Chart, Vargas, Dasha, Yoga, Shadbala,
 * Ashtakavarga, Transit, Rule Engine, Knowledge, Verification, Report).
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import { chartKeys } from "./charts";
import type {
  BulkImportRow,
  BulkImportResponse,
  FullReportRequest,
  FullReportResponse,
  KPAnalysisRequest,
  KPAnalysisResponse,
  WorkflowAnalysisRequest,
  WorkflowAnalysisResponse,
  WorkflowDuplicateCheckRequest,
  WorkflowDuplicateCheckResponse,
} from "./types";

export function useAnalyzeWorkflow() {
  const queryClient = useQueryClient();
  return useMutation<WorkflowAnalysisResponse, Error, WorkflowAnalysisRequest>({
    mutationFn: (payload) =>
      api.post<WorkflowAnalysisResponse>("/api/v1/workflow/analyze", payload),
    onSuccess: (_data, variables) => {
      if (variables.persist !== false) {
        queryClient.invalidateQueries({ queryKey: chartKeys.mine });
      }
    },
  });
}

/** Full Report — the complete analysis pipeline + KP in one call
 * (POST /api/v1/report/full). Used by the printable /reports/full page. */
export function useFullReport() {
  return useMutation<FullReportResponse, Error, FullReportRequest>({
    mutationFn: (payload) =>
      api.post<FullReportResponse>("/api/v1/report/full", payload),
  });
}

/**
 * KP Analysis Center data source — the backend KP Analysis + Evidence
 * engine (POST /api/v1/kp/analyze). Stateless: the request carries the
 * chart's own birth data, so the query is keyed on the serialized request
 * and re-fetched only when the chart changes.
 */
export function useKPAnalysis(request: KPAnalysisRequest | null) {
  return useQuery<KPAnalysisResponse>({
    queryKey: ["kp", "analyze", request],
    queryFn: () => api.post<KPAnalysisResponse>("/api/v1/kp/analyze", request),
    enabled: !!request,
  });
}

/** Check whether this user already has a saved chart with the exact same
 * birth data before persisting — two different people can share an exact
 * birth moment and location, so a match should prompt the user rather than
 * silently merge into an existing chart. */
export function useCheckExistingChart() {
  return useMutation<WorkflowDuplicateCheckResponse, Error, WorkflowDuplicateCheckRequest>({
    mutationFn: (payload) =>
      api.post<WorkflowDuplicateCheckResponse>("/api/v1/workflow/check-existing", payload),
  });
}

export function useBulkImportCharts() {
  return useMutation<BulkImportResponse, Error, BulkImportRow[]>({
    mutationFn: (rows) =>
      api.post<BulkImportResponse>("/api/v1/workflow/bulk-import", { rows }),
  });
}
