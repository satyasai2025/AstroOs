/**
 * AstroOS — Transit Patterns API call (TanStack Query integration)
 *
 * POST /api/v1/transit/patterns — Sade Sati, Ashtama Shani, planetary
 * returns, and transit-to-natal aspects for the active chart. Not part of
 * the /workflow/analyze response, so the Transit Analysis console fetches
 * it separately, keyed off the active chart's birth data plus an optional
 * transit_datetime_utc override (undefined = "now" on the backend).
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { TransitPatternsRequest, TransitPatternsResponse, TransitRequest, TransitResponse } from "./types";

export function transitPatternsQueryKey(request: TransitPatternsRequest) {
  return ["transit-patterns", request] as const;
}

export function useTransitPatterns(request: TransitPatternsRequest | null) {
  return useQuery<TransitPatternsResponse>({
    queryKey: transitPatternsQueryKey(
      request ?? { birth_datetime_utc: "", latitude: 0, longitude: 0, ayanamsa: "lahiri", house_system: "W" },
    ),
    queryFn: () => api.post<TransitPatternsResponse>("/api/v1/transit/patterns", request),
    enabled: request !== null,
  });
}

/**
 * POST /api/v1/transit/current — same positions/flags shape as the
 * workflow response's `result.transits`, but re-computable for an
 * arbitrary transit_datetime_utc. Powers the Transit Analysis console's
 * "Recalculate Transits" button, which re-reads live positions for "now"
 * rather than the (potentially stale) moment the original chart analysis
 * ran.
 */
export function liveTransitQueryKey(request: TransitRequest) {
  return ["transit-current", request] as const;
}

export function useLiveTransit(request: TransitRequest | null) {
  return useQuery<TransitResponse>({
    queryKey: liveTransitQueryKey(
      request ?? { birth_datetime_utc: "", latitude: 0, longitude: 0, ayanamsa: "lahiri", house_system: "W" },
    ),
    queryFn: () => api.post<TransitResponse>("/api/v1/transit/current", request),
    enabled: Boolean(request && request.birth_datetime_utc),
  });
}
