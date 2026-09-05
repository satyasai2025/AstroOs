/**
 * AstroOS — Saved Charts API calls (TanStack Query integration)
 *
 * Lists the charts persisted under the logged-in user's account
 * (GET /api/v1/horoscope/my-charts).
 */

"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, tokenStore } from "./api";
import type { BirthChartListResponse } from "./types";

export const chartKeys = {
  mine: ["charts", "mine"] as const,
};

export function useMyCharts() {
  return useQuery<BirthChartListResponse>({
    queryKey: chartKeys.mine,
    queryFn: () => api.get<BirthChartListResponse>("/api/v1/horoscope/my-charts?limit=50&offset=0"),
    enabled: !!tokenStore.getAccess(),
  });
}

export function useChart(chartId: string | null | undefined) {
  return useQuery<BirthChartSummary>({
    queryKey: ["charts", chartId],
    queryFn: () => api.get<BirthChartSummary>(`/api/v1/horoscope/charts/${chartId}`),
    enabled: !!chartId && !!tokenStore.getAccess(),
  });
}

/**
 * Soft-deletes a saved chart (DELETE /api/v1/horoscope/charts/{id}) and
 * refetches the saved-charts list on success so the row disappears
 * without a manual page reload.
 */
export function useDeleteChart() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (chartId: string) => api.delete<void>(`/api/v1/horoscope/charts/${chartId}`),
    onSuccess: (_, chartId) => {
      queryClient.setQueryData<BirthChartListResponse>(chartKeys.mine, (old) => {
        if (!old) return old;
        return {
          ...old,
          total: Math.max(0, old.total - 1),
          charts: old.charts.filter((c) => c.id !== chartId),
        };
      });
      queryClient.invalidateQueries({ queryKey: chartKeys.mine });
    },
  });
}

/**
 * Marks a saved chart as the user's default (POST
 * /api/v1/horoscope/charts/{id}/set-default), unsetting whichever chart
 * previously held that flag, then refetches the saved-charts list so the
 * "Default" badge moves without a manual page reload.
 */
export function useSetDefaultChart() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (chartId: string) => api.post<void>(`/api/v1/horoscope/charts/${chartId}/set-default`, {}),
    onSuccess: (_, chartId) => {
      queryClient.setQueryData<BirthChartListResponse>(chartKeys.mine, (old) => {
        if (!old) return old;
        return {
          ...old,
          charts: old.charts.map((c) => ({
            ...c,
            is_default: c.id === chartId,
          })),
        };
      });
      queryClient.invalidateQueries({ queryKey: chartKeys.mine });
    },
  });
}

import { useCallback, useMemo } from "react";
import { useWorkflowStore } from "./store";
import { useAnalyzeWorkflow } from "./workflow";
import {
  normalizeAyanamsa,
  normalizeHouseSystem,
  type BirthChartSummary,
  type WorkflowAnalysisRequest,
} from "./types";

/**
 * Global Active Chart Hook.
 * Synchronizes with useWorkflowStore and useMyCharts to provide the active
 * chart result, request, summary, and a selectChart() function.
 */
export function useActiveChart() {
  const { result, request, setResult } = useWorkflowStore();
  const { data: myCharts, isLoading: isLoadingCharts } = useMyCharts();
  const analyze = useAnalyzeWorkflow();

  const selectChart = useCallback(
    async (chart: BirthChartSummary) => {
      const req: WorkflowAnalysisRequest = {
        birth_datetime_utc: chart.birth_datetime_utc,
        latitude: chart.birth_latitude,
        longitude: chart.birth_longitude,
        ayanamsa: normalizeAyanamsa(chart.ayanamsa),
        house_system: normalizeHouseSystem(chart.house_system),
        dasha_system: "vimshottari",
        include_vargas: true,
        subject_name: chart.subject_name,
        place_name: chart.place_name,
        persist: false,
        chart_id: chart.id,
      };
      const data = await analyze.mutateAsync(req);
      setResult(data, req);
      try {
        if (typeof window !== "undefined") {
          localStorage.setItem("astroos_last_viewed_chart_id", chart.id);
        }
      } catch {
        // ignore
      }
      return data;
    },
    [analyze, setResult]
  );

  const activeSummary = useMemo(() => {
    if (!myCharts?.charts?.length) return null;
    if (request?.chart_id) {
      return myCharts.charts.find((c) => c.id === request.chart_id) || null;
    }
    if (request?.subject_name) {
      return myCharts.charts.find((c) => c.subject_name === request.subject_name) || null;
    }
    return myCharts.charts.find((c) => c.is_default) || myCharts.charts[0] || null;
  }, [myCharts, request]);

  return {
    result,
    request,
    activeSummary,
    myCharts: myCharts?.charts || [],
    isLoading: isLoadingCharts || analyze.isPending,
    selectChart,
  };
}

