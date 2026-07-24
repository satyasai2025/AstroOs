/**
 * AstroOS — Ishta/Kashta Bala API call (TanStack Query integration)
 *
 * POST /api/v1/shadbala/ishta-kashta — benefic (Ishta) vs malefic
 * (Kashta) strength per planet, derived from Uchcha Bala x Chesta Bala
 * (real classical formula, see apps/api/services/shadbala/
 * ishta_kashta_bala.py). Scoped to the 5 planets Chesta Bala covers
 * (Mars/Mercury/Jupiter/Venus/Saturn) — Sun/Moon are omitted rather than
 * given a fabricated figure.
 *
 * Unlike most of this app's data (fetched by chart_id once persisted),
 * ShadbalaEngine is compute-only and needs the original birth details
 * again — this reuses the WorkflowAnalysisRequest already sitting in
 * useWorkflowStore rather than asking the user to re-enter anything.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";
import type { WorkflowAnalysisRequest } from "./types";

export interface BalaComponent {
  component_id: string;
  component_name: string;
  rule_version: string;
  planet: string;
  value_shashtiamsas: number;
  trace: string[];
}

export interface IshtaKashtaResponse {
  ishta_bala: BalaComponent[];
  kashta_bala: BalaComponent[];
}

export const shadbalaKeys = {
  ishtaKashta: (req: Pick<WorkflowAnalysisRequest, "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"> | null) =>
    ["shadbala", "ishta-kashta", req?.birth_datetime_utc, req?.latitude, req?.longitude, req?.ayanamsa, req?.house_system] as const,
};

export function useIshtaKashtaBala(
  request: Pick<WorkflowAnalysisRequest, "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"> | null,
) {
  return useQuery<IshtaKashtaResponse>({
    queryKey: shadbalaKeys.ishtaKashta(request),
    queryFn: () =>
      api.post<IshtaKashtaResponse>("/api/v1/shadbala/ishta-kashta", {
        birth_datetime_utc: request!.birth_datetime_utc,
        latitude: request!.latitude,
        longitude: request!.longitude,
        ayanamsa: request!.ayanamsa,
        house_system: request!.house_system,
      }),
    enabled: !!tokenStore.getAccess() && !!request,
    staleTime: Infinity, // deterministic given the same birth data
  });
}
