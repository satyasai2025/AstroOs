/**
 * AstroOS — Life Events API calls (TanStack Query integration)
 *
 * Mirrors apps/api/routers/events.py's `GET /api/v1/events?chart_id=...`
 * (Module 14, Phase 3). Same conventions as lib/charts.ts.
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, tokenStore } from "./api";

// Mirrors apps/api/schemas/events.py — kept local to this file per the
// Phase 8 file-boundary rules (types.ts is off-limits for this workstream).
export interface EventResponse {
  id: string;
  chart_id: string;
  user_id: string | null;
  event_date: string;
  title: string;
  description: string | null;
  category: string | null;
  is_verified: boolean;
}

export interface EventCreateInput {
  chart_id: string;
  event_date: string;
  title: string;
  description?: string | null;
  category?: string | null;
  is_verified?: boolean;
}

export interface EventListResponse {
  events: EventResponse[];
  total: number;
}

export const eventKeys = {
  forChart: (chartId: string) => ["events", "chart", chartId] as const,
};

export function useChartEvents(chartId: string | undefined | null) {
  return useQuery<EventListResponse>({
    queryKey: eventKeys.forChart(chartId ?? ""),
    queryFn: () => api.get<EventListResponse>(`/api/v1/events?chart_id=${encodeURIComponent(chartId as string)}`),
    enabled: Boolean(chartId) && !!tokenStore.getAccess(),
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EventCreateInput) => api.post<EventResponse>("/api/v1/events", data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: eventKeys.forChart(variables.chart_id) });
    },
  });
}

export function useDeleteEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ eventId, chartId }: { eventId: string; chartId: string }) =>
      api.delete<void>(`/api/v1/events/${eventId}`),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: eventKeys.forChart(variables.chartId) });
    },
  });
}
