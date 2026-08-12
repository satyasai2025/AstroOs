/**
 * AstroOS — Event Analysis API calls (TanStack Query)
 *
 * The Event Analysis / event chart (muhurta) feature. One mutation to
 * create+run+persist+return an Event Analysis (POST /event-analysis), and
 * a query to fetch a completed analysis (with its generated artifact
 * snapshots) by id (GET /event-analysis/{id}).
 */

"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type {
  EventAnalysisRequest,
  EventAnalysisResponse,
} from "./types";

export function useCreateEventAnalysis() {
  return useMutation<EventAnalysisResponse, Error, EventAnalysisRequest>({
    mutationFn: (payload) =>
      api.post<EventAnalysisResponse>("/api/v1/event-analysis", payload),
  });
}

export function useEventAnalysis(eventId: string | null) {
  return useQuery<EventAnalysisResponse>({
    queryKey: ["event-analysis", eventId],
    enabled: !!eventId,
    queryFn: () =>
      api.get<EventAnalysisResponse>(`/api/v1/event-analysis/${eventId}`),
  });
}