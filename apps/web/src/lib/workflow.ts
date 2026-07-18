/**
 * AstroOS — Workflow Orchestrator API calls (TanStack Query integration)
 *
 * One mutation: submit birth details, get back the full Unified
 * Analysis Pipeline result (Chart, Vargas, Dasha, Yoga, Shadbala,
 * Ashtakavarga, Transit, Rule Engine, Knowledge, Verification, Report).
 */

"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "./api";
import type { WorkflowAnalysisRequest, WorkflowAnalysisResponse } from "./types";

export function useAnalyzeWorkflow() {
  return useMutation<WorkflowAnalysisResponse, Error, WorkflowAnalysisRequest>({
    mutationFn: (payload) =>
      api.post<WorkflowAnalysisResponse>("/api/v1/workflow/analyze", payload),
  });
}
