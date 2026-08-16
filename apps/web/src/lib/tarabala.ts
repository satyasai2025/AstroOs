/**
 * AstroOS — Navatara / Tarabala API call (TanStack Query integration)
 *
 * POST /api/v1/tarabala/report — see apps/api/services/tarabala_report_service.py
 * and packages/shared/tarabala.py for the underlying mechanism (9-name
 * cycle for natal/transit/lordship Tarabala, full 27-name extended
 * table for the yearly cycle — deliberately not the same table).
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";

export interface PlanetTara {
  planet: string;
  nakshatra: string;
  position: number;
  name: string;
  is_favorable: boolean;
}

export interface LordshipTaraEntry {
  dasha_level: number;
  lord: string;
  position_name: string;
  is_favorable: boolean;
}

export interface SpecialPointEntry {
  name: string;
  from_moon: string;
  from_lagna: string | null;
}

export interface TarabalaReport {
  janma_nakshatra: string;
  lagna_nakshatra: string | null;
  moment_utc: string;
  natal_tarabala: PlanetTara[];
  transit_tarabala: PlanetTara[];
  lordship_tarabala: LordshipTaraEntry[];
  favorable_level_count: number;
  total_active_levels: number;
  all_levels_favorable: boolean;
  yearly_age: number | null;
  yearly_position: number | null;
  yearly_name: string | null;
  best_stars: string[] | null;
  special_points: SpecialPointEntry[];
}

export interface TarabalaReportRequest {
  janma_nakshatra: string;
  birth_datetime_utc: string;
  moment_utc?: string | null;
  lagna_nakshatra?: string | null;
  dasha_chain?: string[] | null;
}

export const tarabalaKeys = {
  report: (req: TarabalaReportRequest | null) =>
    ["tarabala", "report", req?.janma_nakshatra, req?.birth_datetime_utc, req?.moment_utc, req?.lagna_nakshatra, req?.dasha_chain?.join(",")] as const,
};

export function useTarabalaReport(request: TarabalaReportRequest | null) {
  return useQuery<TarabalaReport>({
    queryKey: tarabalaKeys.report(request),
    queryFn: () => api.post<TarabalaReport>("/api/v1/tarabala/report", request),
    enabled: !!tokenStore.getAccess() && !!request,
    staleTime: 60_000,
  });
}
