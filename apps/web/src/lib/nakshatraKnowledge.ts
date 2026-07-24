/**
 * AstroOS — Nakshatra Knowledge Base API calls (TanStack Query integration)
 *
 * GET /api/v1/knowledge/nakshatras and GET /api/v1/knowledge/nakshatras/{id}
 * — real classical reference data (deity, shakti, nature, per-pada Navamsha
 * mapping, karakatvas, cited sources) loaded from the 27 YAML files in
 * knowledge/catalogues/nakshatras/. This is "Level 2" of the context-
 * selector vision the user described — see components/charts/
 * NakshatraPadaSelector.tsx for where it's wired into the UI.
 *
 * These two GET routes are public (no auth) on the backend, matching the
 * rest of the knowledge module's read endpoints — see routers/knowledge.py.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

export interface NakshatraDeity {
  name: string;
  description: string;
  attributes: string[];
}

export interface NakshatraShakti {
  name: string;
  meaning: string;
  power: string;
}

export interface NakshatraPadaKnowledge {
  pada: number;
  degrees: string;
  rashi: string;
  /** The Navamsha (D9) sign this pada classically falls in — each of a
   * nakshatra's 4 padas maps to a fixed D9 sign in rotation. */
  navamsha_rashi: string;
}

export interface NakshatraNature {
  temperament: string;
  guna: string;
  gana: string;
  yoni: string;
  nadi: string;
}

export interface NakshatraSource {
  ref: string;
  claim: string;
  confidence: string;
}

export interface NakshatraSummary {
  id: string;
  name: string;
  sequential: number;
  ruler: string;
  classical_name: string;
}

export interface NakshatraListResponse {
  nakshatras: NakshatraSummary[];
  total: number;
}

export interface NakshatraDetail {
  id: string;
  name: string;
  sequential: number;
  aliases: string[];
  classical_name: string;
  devanagari: string;
  meaning: string;
  ruler: string;
  starting_degree: number;
  ending_degree: number;
  rashi_span: string[];
  padas: NakshatraPadaKnowledge[];
  deity: NakshatraDeity | null;
  shakti: NakshatraShakti | null;
  nature: NakshatraNature | null;
  karakatvas: string[];
  compatible_nakshatras: string[];
  incompatible_nakshatras: string[];
  sources: NakshatraSource[];
  notes: string;
}

export const nakshatraKnowledgeKeys = {
  list: () => ["nakshatra-knowledge", "list"] as const,
  detail: (name: string) => ["nakshatra-knowledge", "detail", name] as const,
};

/** All 27 nakshatras, summary only — used to build the drill-down grid. */
export function useNakshatraList() {
  return useQuery<NakshatraListResponse>({
    queryKey: nakshatraKnowledgeKeys.list(),
    queryFn: () => api.get<NakshatraListResponse>("/api/v1/knowledge/nakshatras"),
    staleTime: Infinity, // static classical reference data
  });
}

/** Full classical detail for one nakshatra — only fetched once selected. */
export function useNakshatraDetail(name: string | null) {
  return useQuery<NakshatraDetail>({
    queryKey: nakshatraKnowledgeKeys.detail(name ?? ""),
    queryFn: () => api.get<NakshatraDetail>(`/api/v1/knowledge/nakshatras/${encodeURIComponent(name!)}`),
    enabled: !!name,
    staleTime: Infinity,
  });
}
