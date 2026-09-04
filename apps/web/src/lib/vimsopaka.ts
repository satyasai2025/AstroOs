/**
 * AstroOS — Vimsopaka Bala API & Calculations (TanStack Query integration)
 *
 * POST /api/v1/vimsopaka/all — Vimsopaka Bala (20-point divisional strength scale)
 * across Shadvarga, Saptavarga, Dasavarga, and Shodasavarga schemes.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";
import type { WorkflowAnalysisRequest } from "./types";

export interface VargaDignityScore {
  varga: string;
  varga_rashi: string;
  dignity: string;
  weight: number;
  base_points: number;
  weighted_points: number;
}

export interface VimsopakaScheme {
  scheme_name: "shadvarga" | "saptavarga" | "dasavarga" | "shodasavarga";
  total_weight: number;
  vimsopaka_score: number;
  category: "Ati Purna" | "Purna" | "Madhya" | "Alpa";
  varga_breakdown: VargaDignityScore[];
}

export interface VimsopakaPlanetResult {
  planet: string;
  shadvarga: VimsopakaScheme;
  saptavarga: VimsopakaScheme;
  dasavarga: VimsopakaScheme;
  shodasavarga: VimsopakaScheme;
}

export interface VimsopakaListResponse {
  planets: VimsopakaPlanetResult[];
}

type BirthFields = Pick<
  WorkflowAnalysisRequest,
  "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"
>;

export const vimsopakaKeys = {
  all: (req: BirthFields | null) =>
    [
      "vimsopaka",
      "all",
      req?.birth_datetime_utc,
      req?.latitude,
      req?.longitude,
      req?.ayanamsa,
      req?.house_system,
    ] as const,
};

export function useVimsopaka(request: BirthFields | null) {
  return useQuery<VimsopakaListResponse>({
    queryKey: vimsopakaKeys.all(request),
    queryFn: () =>
      api.post<VimsopakaListResponse>("/api/v1/vimsopaka/all", {
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
