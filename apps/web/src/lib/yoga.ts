/**
 * AstroOS — Yoga API calls (TanStack Query integration)
 *
 * Hooks wrapping the Yoga Engine REST endpoints in
 * apps/api/routers/yoga.py:
 *   GET  /api/v1/yoga/catalog                 — all registered yoga definitions
 *   POST /api/v1/yoga/evaluate                — evaluate all yogas against a birth chart
 *   POST /api/v1/yoga/evaluate/with-strength  — + 0-100 numerical strength scores
 *   POST /api/v1/yoga/evaluate/timeline       — + Dasha activation timelines
 *
 * These are separate from the workflow /analyze endpoint because the workflow
 * pipeline calls YogaEngine.evaluate_all() (without strength scoring) to keep
 * the main analysis fast. The Yoga Intelligence Dashboard enriches the basic
 * results with strength scores and timelines on demand.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type {
  YogaCatalogResponse,
  YogaDefinitionResponse,
  YogaEvaluationRequest,
  YogaEvaluationResponse,
  YogaTimelineEvaluationResponse,
  YogaTimelineResponse,
} from "./types";

export const yogaQueryKeys = {
  catalog: () => ["yoga", "catalog"] as const,
  catalogByCategory: (category: string) => ["yoga", "catalog", "by-category", category] as const,
  evaluation: (body: YogaEvaluationRequest, opts?: { presentOnly?: boolean; category?: string }) => [
    "yoga", "evaluate", JSON.stringify(body), opts?.presentOnly, opts?.category,
  ] as const,
  strength: (body: YogaEvaluationRequest, opts?: { presentOnly?: boolean; category?: string }) => [
    "yoga", "evaluate", "with-strength", JSON.stringify(body), opts?.presentOnly, opts?.category,
  ] as const,
  timeline: (body: YogaEvaluationRequest) => [
    "yoga", "evaluate", "timeline", JSON.stringify(body),
  ] as const,
};

/** Full yoga catalog — every registered yoga definition. Static reference data,
 *  cached indefinitely. */
export function useYogaCatalog() {
  return useQuery<YogaCatalogResponse>({
    queryKey: yogaQueryKeys.catalog(),
    queryFn: () => api.get<YogaCatalogResponse>("/api/v1/yoga/catalog"),
    staleTime: Infinity, // registered definitions change rarely
  });
}

/** Yoga definitions filtered to one category. */
export function useYogaCatalogByCategory(category: string | null) {
  return useQuery<YogaCatalogResponse>({
    queryKey: yogaQueryKeys.catalogByCategory(category ?? ""),
    queryFn: () => api.get<YogaCatalogResponse>(`/api/v1/yoga/catalog/by-category/${encodeURIComponent(category!)}`),
    enabled: !!category,
    staleTime: Infinity,
  });
}

/**
 * Evaluate all yogas with 0-100 strength scores and optionally timeline data.
 * Reuses the birth-data from the workflow request so the same chart is evaluated.
 */
export function useYogaStrengthEvaluation(
  body: YogaEvaluationRequest | null,
  opts?: { presentOnly?: boolean; category?: string },
) {
  return useQuery<YogaEvaluationResponse>({
    queryKey: yogaQueryKeys.strength(body ?? ({} as YogaEvaluationRequest), opts),
    queryFn: () =>
      api.post<YogaEvaluationResponse>("/api/v1/yoga/evaluate/with-strength", {
        ...body,
        only_present: opts?.presentOnly ?? false,
        category: opts?.category ?? undefined,
      }),
    enabled: !!body,
    staleTime: 5 * 60 * 1000, // 5 minutes — birth data doesn't change
  });
}

/** Evaluate all present yogas and return their Dasha activation timelines. */
export function useYogaTimelineEvaluation(
  body: YogaEvaluationRequest | null,
) {
  return useQuery<YogaTimelineEvaluationResponse>({
    queryKey: yogaQueryKeys.timeline(body ?? ({} as YogaEvaluationRequest)),
    queryFn: () =>
      api.post<YogaTimelineEvaluationResponse>("/api/v1/yoga/evaluate/timeline", body),
    enabled: !!body,
    staleTime: 5 * 60 * 1000,
  });
}

/** Convenience: look up a single yoga definition by yoga_id from the catalog. */
export function useYogaDefinition(yogaId: string | null): YogaDefinitionResponse | undefined {
  // Uses the cached catalog query — no extra network call if already loaded.
  // Caller should ensure useYogaCatalog() has been called at a parent level.
  const { data } = useQuery({
    queryKey: yogaQueryKeys.catalog(),
    queryFn: () => api.get<YogaCatalogResponse>("/api/v1/yoga/catalog"),
    staleTime: Infinity,
    placeholderData: (previousData) => previousData,
  });
  if (!data) return undefined;
  return data.yogas.find((d) => d.yoga_id === yogaId);
}
