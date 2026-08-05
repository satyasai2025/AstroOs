import { useQuery } from "@tanstack/react-query";
import { api, tokenStore } from "./api";

export interface SearchResultChart {
  type: "chart";
  id: string;
  title: string;
  subtitle?: string;
  snippet: string;
  created_at: string;
  href: string;
}

export interface SearchResultKnowledge {
  type: string;
  id: string;
  title: string;
  snippet: string;
  relevance: number;
  book_title?: string;
  tradition?: string;
  href: string;
}

export interface SearchResultProject {
  type: "project";
  id: string;
  title: string;
  snippet: string;
  created_at: string;
  href: string;
}

export type SearchResult = SearchResultChart | SearchResultKnowledge | SearchResultProject;

export interface UnifiedSearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

export const searchKeys = {
  unified: (query: string) => ["search", "unified", query] as const,
};

export const searchApi = {
  query: (query: string, limit: number = 15) =>
    api.post<UnifiedSearchResponse>("/api/v1/search", { query, limit }),
};

export function useUnifiedSearch(query: string, limit: number = 15) {
  return useQuery<UnifiedSearchResponse>({
    queryKey: searchKeys.unified(query),
    queryFn: () => searchApi.query(query, limit),
    enabled: !!tokenStore.getAccess() && query.length >= 2,
    staleTime: 1000 * 60 * 5,
  });
}
