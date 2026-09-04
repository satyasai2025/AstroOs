"use client";

/**
 * AstroOS — Research Patterns cross-tab shared filter state.
 *
 * All 9 routes under /research/patterns/* (Overview, Patterns, Combinations,
 * Yogas, Dashas, Transits, Houses, Nakshatras, Compare) are separate Next.js
 * pages, so plain useState in each page.tsx would reset on navigation. This
 * Context lives in apps/web/src/app/research/patterns/layout.tsx, which
 * Next.js keeps mounted across client-side navigation between those sibling
 * routes — so the Provider's state (and therefore every tab's active
 * filters) survives switching tabs, making the Research Center behave as
 * one workspace instead of 9 independent pages.
 */

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

export interface NodeFilter {
  dimension: string;
  value: string;
}

interface ResearchPatternsFiltersValue {
  dataset: string;
  setDataset: (v: string) => void;
  dateFrom: string;
  setDateFrom: (v: string) => void;
  dateTo: string;
  setDateTo: (v: string) => void;
  eventType: string;
  setEventType: (v: string) => void;
  chartType: string;
  setChartType: (v: string) => void;
  confidenceBand: string;
  setConfidenceBand: (v: string) => void;
  supportBand: string;
  setSupportBand: (v: string) => void;
  gender: string;
  setGender: (v: string) => void;
  nodeFilter: NodeFilter | null;
  setNodeFilter: (v: NodeFilter | null) => void;
  clearNodeFilter: () => void;
  clearAll: () => void;
}

const ResearchPatternsFiltersContext = createContext<ResearchPatternsFiltersValue | null>(null);

export function ResearchPatternsFiltersProvider({ children }: { children: ReactNode }) {
  const [dataset, setDataset] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [eventType, setEventType] = useState("");
  const [chartType, setChartType] = useState("");
  const [confidenceBand, setConfidenceBand] = useState("");
  const [supportBand, setSupportBand] = useState("");
  const [gender, setGender] = useState("");
  const [nodeFilter, setNodeFilter] = useState<NodeFilter | null>(null);

  const clearNodeFilter = useCallback(() => setNodeFilter(null), []);
  const clearAll = useCallback(() => {
    setDataset("");
    setDateFrom("");
    setDateTo("");
    setEventType("");
    setChartType("");
    setConfidenceBand("");
    setSupportBand("");
    setGender("");
    setNodeFilter(null);
  }, []);

  const value = useMemo<ResearchPatternsFiltersValue>(
    () => ({
      dataset,
      setDataset,
      dateFrom,
      setDateFrom,
      dateTo,
      setDateTo,
      eventType,
      setEventType,
      chartType,
      setChartType,
      confidenceBand,
      setConfidenceBand,
      supportBand,
      setSupportBand,
      gender,
      setGender,
      nodeFilter,
      setNodeFilter,
      clearNodeFilter,
      clearAll,
    }),
    [dataset, dateFrom, dateTo, eventType, chartType, confidenceBand, supportBand, gender, nodeFilter, clearNodeFilter, clearAll],
  );

  return (
    <ResearchPatternsFiltersContext.Provider value={value}>
      {children}
    </ResearchPatternsFiltersContext.Provider>
  );
}

export function useResearchPatternsFilters(): ResearchPatternsFiltersValue {
  const ctx = useContext(ResearchPatternsFiltersContext);
  if (!ctx) {
    throw new Error(
      "useResearchPatternsFilters must be used within a ResearchPatternsFiltersProvider (apps/web/src/app/research/patterns/layout.tsx)",
    );
  }
  return ctx;
}
