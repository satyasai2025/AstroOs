/**
 * AstroOS — Sarvatobhadra Chakra (SBC) API call (TanStack Query integration)
 *
 * POST /api/v1/sbc/report — full 9x9 grid snapshot (all 9 grahas' current
 * SBC nakshatra/cell) at a moment, plus (optionally) the Vedha result onto
 * a specified Janma element. See apps/api/services/sbc_vedha_engine.py for
 * the underlying mechanism (benefic-only casting, motion-based direction,
 * dignity-based scoring) — sourced from a real SBC tool's VBA and
 * cross-checked against live JHora screenshots for Dhanishtha/Shatabhisha.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";

export interface SBCGridPlanet {
  planet: string;
  nakshatra: string;
  cellnum: number;
  rashi: string;
  rashi_degree: number;
  is_retrograde: boolean;
  is_combust: boolean;
  speed_deg_per_day: number;
}

export interface SBCVedhaHit {
  planet: string;
  direction: string;
  from_nakshatra: string;
  score: number;
}

export interface SBCVedhaResult {
  hits: SBCVedhaHit[];
  total_score: number;
  zeroed_by_malefic_conjunction: boolean;
}

export interface SBCReport {
  moment_utc: string;
  tithi_number: number;
  positions: SBCGridPlanet[];
  janma_nakshatra: string | null;
  vedha_result: SBCVedhaResult | null;
}

export const sbcKeys = {
  report: (momentUtc: string | null, janmaNakshatra: string | null) =>
    ["sbc", "report", momentUtc, janmaNakshatra] as const,
};

export function useSBCReport(momentUtc: string | null, janmaNakshatra: string | null) {
  return useQuery<SBCReport>({
    queryKey: sbcKeys.report(momentUtc, janmaNakshatra),
    queryFn: () =>
      api.post<SBCReport>("/api/v1/sbc/report", {
        moment_utc: momentUtc,
        janma_nakshatra: janmaNakshatra,
      }),
    enabled: !!tokenStore.getAccess(),
    staleTime: 60_000,
  });
}
