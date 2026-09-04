/**
 * AstroOS — Geocoding API calls (TanStack Query integration)
 *
 * Birth-place search and timezone/DST resolution, so a user never has
 * to know their own latitude/longitude/UTC-offset.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { PlaceSearchResponse, TimezoneResolutionResponse } from "./types";

export function usePlaceSearch(query: string) {
  return useQuery<PlaceSearchResponse>({
    queryKey: ["geocode", "search", query],
    queryFn: () => api.get<PlaceSearchResponse>(`/api/v1/geocode/search?query=${encodeURIComponent(query)}`),
    enabled: query.trim().length >= 2,
    staleTime: 1000 * 60 * 5, // place names don't change; cache generously
    retry: false,
  });
}

export function useTimezoneResolution(
  latitude: number | null,
  longitude: number | null,
  localDate: string | null, // YYYY-MM-DD
) {
  return useQuery<TimezoneResolutionResponse>({
    queryKey: ["geocode", "timezone", latitude, longitude, localDate],
    queryFn: () =>
      api.get<TimezoneResolutionResponse>(
        `/api/v1/geocode/timezone?latitude=${latitude}&longitude=${longitude}&local_date=${localDate}`,
      ),
    enabled: latitude !== null && longitude !== null && !!localDate,
    staleTime: 1000 * 60 * 5,
    retry: false,
  });
}
