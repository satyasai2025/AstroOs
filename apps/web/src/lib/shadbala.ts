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
  all: (req: Pick<WorkflowAnalysisRequest, "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"> | null) =>
    ["shadbala", "all", req?.birth_datetime_utc, req?.latitude, req?.longitude, req?.ayanamsa, req?.house_system] as const,
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

/**
 * AllShadbalaResponse — every implemented Shadbala component/sub-component,
 * grouped exactly as apps/api/schemas/shadbala.py's AllShadbalaResponse
 * groups them. Only used by the Prediction Chain Explorer for Digbala
 * (phase1.dig_bala) today; the other groups are typed for completeness
 * since the backend returns them regardless.
 */
export interface Phase1ComponentsResponse {
  naisargika_bala: BalaComponent[];
  dig_bala: BalaComponent[];
  drik_bala: BalaComponent[];
}

export interface Phase2ComponentsResponse {
  chesta_bala: BalaComponent[];
  paksha_bala: BalaComponent[];
  ayana_bala: BalaComponent[];
  yuddha_bala: BalaComponent[];
}

export interface SthanaBalaComponentsResponse {
  uchcha_bala: BalaComponent[];
  kendradi_bala: BalaComponent[];
  drekkana_bala: BalaComponent[];
}

export interface AllShadbalaResponse {
  phase1: Phase1ComponentsResponse;
  phase2: Phase2ComponentsResponse;
  sthana_bala: SthanaBalaComponentsResponse;
  saptavargaja_bala: BalaComponent[];
  ojayugmarasyamsa_bala: BalaComponent[];
  tribhaga_bala: BalaComponent[];
  nathonnata_bala: BalaComponent[];
  dina_hora_bala: BalaComponent[];
  ishta_bala: BalaComponent[];
  kashta_bala: BalaComponent[];
  implemented_components: string[];
  not_yet_implemented_components: string[];
}

/**
 * useShadbalaAll — full Shadbala component breakdown (Naisargika, Dig,
 * Drik, Chesta, Paksha, Ayana, Yuddha, Sthana sub-components, etc), real
 * classical calculations from apps/api/services/shadbala_engine.py.
 * Prediction Chain Explorer uses this only for Digbala (directional
 * strength) — see lib/predictions/scoring.ts — since chart.shadbala[]
 * (already in WorkflowAnalysisResponse) only carries the simplified
 * per-planet total_rupas, not the per-component breakdown.
 *
 * Same compute-only, re-send-birth-data pattern as useIshtaKashtaBala
 * above and useAvastha in lib/avastha.ts.
 */
export function useShadbalaAll(
  request: Pick<WorkflowAnalysisRequest, "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"> | null,
) {
  return useQuery<AllShadbalaResponse>({
    queryKey: shadbalaKeys.all(request),
    queryFn: () =>
      api.post<AllShadbalaResponse>("/api/v1/shadbala/all", {
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
