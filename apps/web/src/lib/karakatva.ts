/**
 * AstroOS — Karakatva Explorer API calls (TanStack Query integration)
 *
 * Searches the classical signification (karakatva) catalogue —
 * GET /api/v1/knowledge/karakatvas?subject=&graha= — which already exists
 * in apps/api/routers/knowledge.py and is backed by KnowledgeRepository.
 * list_karakatvas() (subject: case-insensitive substring match, graha:
 * exact match against the 9-value planet enum).
 *
 * This is a small, curated catalogue (source-cited to BPHS), not a huge
 * database — see the empty-state copy in app/karakatva/page.tsx.
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";

export interface KnowledgeReference {
  book_id: string;
  chapter: number | null;
  verse_number: number | null;
  edition: string | null;
  translator: string | null;
}

export interface Karakatva {
  id: string;
  subject: string;
  graha: string | null;
  sign_id: number | null;
  house_number: number | null;
  tradition: string | null;
  source: KnowledgeReference | null;
  description: string | null;
  version: number;
  version_comment: string | null;
  superseded_by: string | null;
}

export interface KarakatvaListResponse {
  karakatvas: Karakatva[];
  total: number;
}

/** The 9 grahas the `graha` filter (and the DB enum) accepts. */
export const KARAKATVA_GRAHAS = [
  "sun",
  "moon",
  "mars",
  "mercury",
  "jupiter",
  "venus",
  "saturn",
  "rahu",
  "ketu",
] as const;

export type KarakatvaGraha = (typeof KARAKATVA_GRAHAS)[number];

export const karakatvaKeys = {
  search: (subject: string, graha: string) => ["karakatva", "search", subject, graha] as const,
};

export interface UseKarakatvaSearchArgs {
  /** Free-text keyword, matched against the karakatva's subject (e.g. "career", "blood", "surgery"). */
  subject?: string;
  /** Restrict to one graha, e.g. "mars". Empty string / omitted = no filter. */
  graha?: string;
}

/**
 * Search the karakatva catalogue by subject keyword and/or graha.
 *
 * Only runs once the user is signed in (matches the rest of the app's
 * TanStack Query hooks) and once at least one filter has been provided —
 * an unfiltered request would return the entire (still fairly small)
 * catalogue, which is wasteful for a live-typing search box.
 */
export function useKarakatvaSearch({ subject = "", graha = "" }: UseKarakatvaSearchArgs) {
  const trimmedSubject = subject.trim();

  return useQuery<KarakatvaListResponse>({
    queryKey: karakatvaKeys.search(trimmedSubject, graha),
    queryFn: () => {
      const params = new URLSearchParams();
      if (trimmedSubject) params.set("subject", trimmedSubject);
      if (graha) params.set("graha", graha);
      return api.get<KarakatvaListResponse>(`/api/v1/knowledge/karakatvas?${params.toString()}`);
    },
    enabled: !!tokenStore.getAccess() && (trimmedSubject.length >= 2 || !!graha),
    staleTime: 1000 * 60 * 5, // classical significations don't change at runtime
  });
}
