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

/**
 * Soft-deletes a saved chart (DELETE /api/v1/horoscope/charts/{id}) and
 * refetches the saved-charts list on success so the row disappears
 * without a manual page reload.
 */
export function useDeleteChart() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (chartId: string) => api.delete<void>(`/api/v1/horoscope/charts/${chartId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chartKeys.mine });
    },
  });
}
