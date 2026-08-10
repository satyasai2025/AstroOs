"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { ApiError } from "@/lib/api";
import type { WorkflowAnalysisRequest, WorkflowAnalysisResponse } from "@/lib/types";
import { CompareChartsModal } from "./components/CompareChartsModal";
import { ComparisonWorkspace, type ComparedChart } from "./components/ComparisonWorkspace";
import { useSavedComparisons } from "./hooks/useSavedComparisons";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
  } catch {
    return iso;
  }
}

/**
 * /charts/compare — side-by-side comparison of 2-4 saved charts (planets,
 * houses, dasha, yogas, summary), with CSV/PDF export and locally saved
 * comparison sets for quick re-opening.
 */
export default function ChartComparePage() {
  const { data: chartsData, isLoading: chartsLoading, isError: chartsErrored } = useMyCharts();
  const analyze = useAnalyzeWorkflow();
  const {
    savedComparisons,
    saveComparison,
    deleteComparison,
    togglePin,
  } = useSavedComparisons();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [compared, setCompared] = useState<ComparedChart[] | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);
  const [activeChartIds, setActiveChartIds] = useState<string[]>([]);

  // Swiss Ephemeris recompute is deterministic — a chart's analysis never
  // changes for the same stored birth parameters — so once fetched within
  // this page visit, reuse it instead of re-calling the rate-limited
  // /workflow/analyze endpoint (6/minute) every time a comparison re-runs
  // or a saved comparison is reopened.
  const resultCache = useRef<Map<string, WorkflowAnalysisResponse>>(new Map());

  const availableCharts = (chartsData?.charts ?? []).map((c) => ({
    id: c.id,
    name: c.subject_name,
    subtitle: `${formatDate(c.birth_datetime_utc)}${c.place_name ? ` · ${c.place_name}` : ""}`,
  }));

  const runComparison = async (chartIds: string[]) => {
    setCompareError(null);
    setIsComparing(true);
    setActiveChartIds(chartIds);
    try {
      // Sequential, not Promise.all: keeps us well under the 6/minute cap
      // on /workflow/analyze and lets already-cached charts resolve
      // instantly without consuming any of that budget at all.
      const results: ComparedChart[] = [];
      for (const id of chartIds) {
        const summary = chartsData?.charts.find((c) => c.id === id);
        if (!summary) throw new Error("One of the selected charts is no longer available.");

        const cached = resultCache.current.get(id);
        if (cached) {
          results.push({ id, name: summary.subject_name, result: cached });
          continue;
        }

        const request: WorkflowAnalysisRequest = {
          birth_datetime_utc: summary.birth_datetime_utc,
          latitude: summary.birth_latitude,
          longitude: summary.birth_longitude,
          ayanamsa: summary.ayanamsa as WorkflowAnalysisRequest["ayanamsa"],
          house_system: summary.house_system as WorkflowAnalysisRequest["house_system"],
          dasha_system: "vimshottari",
          include_vargas: false,
          subject_name: summary.subject_name,
          place_name: summary.place_name,
          persist: false,
          chart_id: summary.id,
        };
        const result = await analyze.mutateAsync(request);
        resultCache.current.set(id, result);
        results.push({ id, name: summary.subject_name, result });
      }
      setCompared(results);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setCompareError("Too many chart recomputes in a short time — please wait about a minute and try again.");
      } else {
        setCompareError(err instanceof ApiError ? err.detail : "Could not load one or more charts for comparison.");
      }
      setCompared(null);
    } finally {
      setIsComparing(false);
    }
  };

  const handleCompare = (chartIds: string[]) => {
    setIsModalOpen(false);
    void runComparison(chartIds);
  };

  const handleSave = (name: string) => {
    saveComparison({
      name,
      charts: activeChartIds,
      comparisonType: "multi",
      userNotes: "",
      aiSummary: "",
      pinned: false,
    });
  };

  const handleOpenSaved = (chartIds: string[]) => {
    const allStillExist = chartIds.every((id) => chartsData?.charts.some((c) => c.id === id));
    if (!allStillExist) {
      setCompareError("One or more charts in this saved comparison have been deleted.");
      return;
    }
    void runComparison(chartIds);
  };

  // Consumes a shared comparison link (?ids=a,b,c,d) — only works for
  // charts the signed-in account itself owns, since saved charts are
  // per-user; sharing across accounts isn't meaningful here.
  const searchParams = useSearchParams();
  const sharedIdsLoaded = useRef(false);
  useEffect(() => {
    if (sharedIdsLoaded.current || chartsLoading || !chartsData) return;
    const idsParam = searchParams.get("ids");
    if (!idsParam) return;
    sharedIdsLoaded.current = true;
    const ids = idsParam.split(",").map((s) => s.trim()).filter(Boolean);
    if (ids.length < 2) {
      setCompareError("This link doesn't include enough charts to compare.");
      return;
    }
    const allExist = ids.every((id) => chartsData.charts.some((c) => c.id === id));
    if (!allExist) {
      setCompareError("One or more charts in this shared link aren't available on this account.");
      return;
    }
    void runComparison(ids);
    // runComparison intentionally omitted: it's redefined every render but
    // reads current chartsData/resultCache via closure, and this effect
    // should only ever fire once per page load (guarded by sharedIdsLoaded).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartsLoading, chartsData, searchParams]);

  return (
    <>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Compare Charts
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Pick 2-4 saved charts to compare planets, houses, dasha, and yogas side by side.
          </p>
        </div>
        <button type="button" onClick={() => setIsModalOpen(true)} className="obsidian-btn-primary text-sm">
          + Choose Charts
        </button>
      </div>

      {compareError && (
        <div
          className="obsidian-card mb-4 p-3 text-sm"
          style={{ color: "var(--obsidian-status-danger, #ef4444)" }}
          role="alert"
        >
          {compareError}
        </div>
      )}

      {isComparing && (
        <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
          Loading charts for comparison…
        </div>
      )}

      {!isComparing && compared && (
        <div className="mb-6">
          <ComparisonWorkspace charts={compared} onClose={() => setCompared(null)} onSave={handleSave} />
        </div>
      )}

      {!isComparing && !compared && (
        <>
          {chartsLoading && (
            <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
              Loading your saved charts…
            </div>
          )}

          {chartsErrored && (
            <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
              Could not load your saved charts.
            </div>
          )}

          {!chartsLoading && !chartsErrored && availableCharts.length < 2 && (
            <div className="obsidian-card flex flex-col items-center gap-4 p-10 text-center">
              <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                Not Enough Saved Charts
              </h2>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                You need at least 2 saved charts to compare. Generate more from the Dashboard.
              </p>
              <Link href="/dashboard" className="obsidian-btn-primary text-sm">
                Go to Dashboard
              </Link>
            </div>
          )}

          {!chartsLoading && !chartsErrored && availableCharts.length >= 2 && (
            <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
              Choose 2-4 charts above to see them compared side by side.
            </div>
          )}

          {savedComparisons.length > 0 && (
            <div className="obsidian-card mt-6 p-5">
              <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Saved Comparisons
              </h2>
              <ul className="space-y-2">
                {savedComparisons.map((sc) => (
                  <li
                    key={sc.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                    style={{ borderColor: "var(--border-primary)" }}
                  >
                    <div>
                      <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                        {sc.pinned ? "📌 " : ""}
                        {sc.name}
                      </p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {sc.charts.length} charts · saved {formatDate(sc.createdAt)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleOpenSaved(sc.charts)}
                        className="obsidian-btn-secondary text-xs"
                      >
                        Open
                      </button>
                      <button
                        type="button"
                        onClick={() => togglePin(sc.id)}
                        className="obsidian-btn-secondary text-xs"
                      >
                        {sc.pinned ? "Unpin" : "Pin"}
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteComparison(sc.id)}
                        className="px-2 py-1 text-xs font-medium"
                        style={{ color: "var(--obsidian-status-danger, #ef4444)" }}
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      <CompareChartsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCompare={handleCompare}
        availableCharts={availableCharts}
      />
    </>
  );
}
