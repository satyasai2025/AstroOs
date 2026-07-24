/**
 * AstroOS — Avastha (planetary state) API call (TanStack Query integration)
 *
 * POST /api/v1/avastha/all — Baladi (degree-based 5-fold) and Deeptadi
 * (dignity-based) planetary states, real classical calculations (see
 * apps/api/services/avastha_engine.py). Jagradadi Avastha is
 * deliberately not implemented — see that file's module docstring for
 * why (genuine classical-source ambiguity, not an oversight).
 *
 * Same compute-only, re-send-birth-data pattern as lib/shadbala.ts.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";
import type { WorkflowAnalysisRequest } from "./types";

export interface Avastha {
  planet: string;
  baladi_avastha: string;
  baladi_trace: string[];
  deeptadi_avastha: string;
  deeptadi_trace: string[];
}

export interface AvasthaListResponse {
  avasthas: Avastha[];
  not_implemented: string[];
}

type BirthFields = Pick<WorkflowAnalysisRequest, "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system">;

export const avasthaKeys = {
  all: (req: BirthFields | null) =>
    ["avastha", "all", req?.birth_datetime_utc, req?.latitude, req?.longitude, req?.ayanamsa, req?.house_system] as const,
};

export function useAvastha(request: BirthFields | null) {
  return useQuery<AvasthaListResponse>({
    queryKey: avasthaKeys.all(request),
    queryFn: () =>
      api.post<AvasthaListResponse>("/api/v1/avastha/all", {
        birth_datetime_utc: request!.birth_datetime_utc,
        latitude: request!.latitude,
        longitude: request!.longitude,
        ayanamsa: request!.ayanamsa,
        house_system: request!.house_system,
      }),
    enabled: !!tokenStore.getAccess() && !!request,
    staleTime: Infinity,
  });
}
