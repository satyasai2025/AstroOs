/**
 * AstroOS — Saravali Shadbala API & Calculations
 *
 * Full 6-Fold Shadbala Suite matching Kalyana Varma's Saravali & BPHS Ch. 27:
 * 1. Sthana Bala (Uchcha, Saptavargaja, Ojayugmarasyamsa, Kendradi, Drekkana)
 * 2. Dig Bala (Directional Quadrants)
 * 3. Kala Bala (Nathonatha, Paksha, Tribhaga, Dina-Hora, Yudhdha, Ayana)
 * 4. Cheshta Bala (8 motional states & velocity)
 * 5. Naisargika Bala (Fixed luminosity scale)
 * 6. Drig Bala (Aspectual Sputa Drishti rectified)
 * Total Pinda (Virupas & Rupas), Minimum Requirements comparison, and Ishta/Kashta Bala.
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

export interface SubBalaCheck {
  bala_key: string;
  bala_name: string;
  obtained_virupas: number;
  required_virupas: number;
  passed: boolean;
}

export interface SaravaliPlanetSummary {
  planet: string;
  planet_display_name: string;

  // 6 Main Balas (Virupas)
  sthana_bala_virupas: number;
  dig_bala_virupas: number;
  kala_bala_virupas: number;
  chesta_bala_virupas: number;
  naisargika_bala_virupas: number;
  drig_bala_virupas: number;

  // Sthana Sub-components
  uchcha_bala_virupas: number;
  saptavargaja_bala_virupas: number;
  ojayugmarasyamsa_bala_virupas: number;
  kendradi_bala_virupas: number;
  drekkana_bala_virupas: number;

  // Kala Sub-components
  nathonnata_bala_virupas: number;
  paksha_bala_virupas: number;
  tribhaga_bala_virupas: number;
  dina_hora_bala_virupas: number;
  ayana_bala_virupas: number;
  yuddha_bala_virupas: number;

  // Total Shadbala Pinda
  total_virupas: number;
  total_rupas: number;
  required_virupas: number;
  required_rupas: number;
  strength_ratio: number;
  percentage: number;
  is_strong: boolean;
  status_label: "Strong" | "Moderate" | "Deficient" | string;
  rank: number;

  // Ishta / Kashta
  ishta_bala_virupas: number;
  kashta_bala_virupas: number;

  // Individual Sub-Bala Checks
  sub_bala_checks: SubBalaCheck[];
  all_sub_balas_passed: boolean;
}

export interface SaravaliShadbalaReport {
  planets: SaravaliPlanetSummary[];
  strongest_planet: string;
  weakest_planet: string;
  average_strength_ratio: number;
  chart_strength_score: number;
}

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
  summary?: SaravaliShadbalaReport | null;
}

// Classical Minimum Shadbala Constants (Saravali & BPHS Ch. 27)
export const SARAVALI_REQUIRED_VIRUPAS: Record<string, number> = {
  sun: 390.0,
  moon: 360.0,
  mars: 300.0,
  mercury: 420.0,
  jupiter: 390.0,
  venus: 330.0,
  saturn: 300.0,
};

export const SARAVALI_REQUIRED_RUPAS: Record<string, number> = {
  sun: 6.5,
  moon: 6.0,
  mars: 5.0,
  mercury: 7.0,
  jupiter: 6.5,
  venus: 5.5,
  saturn: 5.0,
};

export const SARAVALI_INDIVIDUAL_SUB_BALA_REQUIREMENTS: Record<
  string,
  { sthana: number; dig: number; kala: number; cheshta: number; ayana: number }
> = {
  sun: { sthana: 165, dig: 35, kala: 50, cheshta: 112, ayana: 30 },
  jupiter: { sthana: 165, dig: 35, kala: 50, cheshta: 112, ayana: 30 },
  mercury: { sthana: 165, dig: 35, kala: 50, cheshta: 112, ayana: 30 },
  moon: { sthana: 133, dig: 50, kala: 30, cheshta: 100, ayana: 40 },
  venus: { sthana: 133, dig: 50, kala: 30, cheshta: 100, ayana: 40 },
  mars: { sthana: 96, dig: 30, kala: 40, cheshta: 67, ayana: 20 },
  saturn: { sthana: 96, dig: 30, kala: 40, cheshta: 67, ayana: 20 },
};

export const NAISARGIKA_BALA_TABLE: Record<string, { virupas: number; rupas: string; rank: number }> = {
  sun: { virupas: 60.0, rupas: "7/7 (1.000)", rank: 1 },
  moon: { virupas: 51.43, rupas: "6/7 (0.857)", rank: 2 },
  venus: { virupas: 42.86, rupas: "5/7 (0.714)", rank: 3 },
  jupiter: { virupas: 34.29, rupas: "4/7 (0.571)", rank: 4 },
  mercury: { virupas: 25.71, rupas: "3/7 (0.429)", rank: 5 },
  mars: { virupas: 17.14, rupas: "2/7 (0.286)", rank: 6 },
  saturn: { virupas: 8.57, rupas: "1/7 (0.143)", rank: 7 },
};

export const shadbalaKeys = {
  ishtaKashta: (
    req: Pick<
      WorkflowAnalysisRequest,
      "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"
    > | null,
  ) =>
    [
      "shadbala",
      "ishta-kashta",
      req?.birth_datetime_utc,
      req?.latitude,
      req?.longitude,
      req?.ayanamsa,
      req?.house_system,
    ] as const,
  all: (
    req: Pick<
      WorkflowAnalysisRequest,
      "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"
    > | null,
  ) =>
    [
      "shadbala",
      "all",
      req?.birth_datetime_utc,
      req?.latitude,
      req?.longitude,
      req?.ayanamsa,
      req?.house_system,
    ] as const,
  summary: (
    req: Pick<
      WorkflowAnalysisRequest,
      "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"
    > | null,
  ) =>
    [
      "shadbala",
      "summary",
      req?.birth_datetime_utc,
      req?.latitude,
      req?.longitude,
      req?.ayanamsa,
      req?.house_system,
    ] as const,
};

export function useIshtaKashtaBala(
  request: Pick<
    WorkflowAnalysisRequest,
    "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"
  > | null,
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
    staleTime: Infinity,
  });
}

export function useShadbalaAll(
  request: Pick<
    WorkflowAnalysisRequest,
    "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"
  > | null,
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
    staleTime: Infinity,
  });
}

export function useShadbalaSummary(
  request: Pick<
    WorkflowAnalysisRequest,
    "birth_datetime_utc" | "latitude" | "longitude" | "ayanamsa" | "house_system"
  > | null,
) {
  return useQuery<SaravaliShadbalaReport>({
    queryKey: shadbalaKeys.summary(request),
    queryFn: () =>
      api.post<SaravaliShadbalaReport>("/api/v1/shadbala/summary", {
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
