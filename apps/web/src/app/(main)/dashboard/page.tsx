"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { DashboardOverview } from "@/components/dashboard/DashboardOverview";
import { DashboardErrorBoundary } from "@/components/consultation/ErrorBoundary";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useMyCharts } from "@/lib/charts";
import { useWorkflowStore } from "@/lib/store";
import type { BirthChartSummary, WorkflowAnalysisRequest } from "@/lib/types";
import { normalizeAyanamsa, normalizeHouseSystem } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const analyze = useAnalyzeWorkflow();
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const setResult = useWorkflowStore((s) => s.setResult);
  const clearResult = useWorkflowStore((s) => s.clear);
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);
  const storeResult = useWorkflowStore((s) => s.result);
  const storeRequest = useWorkflowStore((s) => s.request);
  const autoHydrated = useRef(false);

  const handleSelectAndLoadChart = (chart: BirthChartSummary) => {
    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: chart.birth_datetime_utc,
      latitude: chart.birth_latitude,
      longitude: chart.birth_longitude,
      ayanamsa: normalizeAyanamsa(chart.ayanamsa),
      house_system: normalizeHouseSystem(chart.house_system),
      dasha_system: "vimshottari",
      include_vargas: true,
      subject_name: chart.subject_name,
      place_name: chart.place_name,
      persist: false,
      chart_id: chart.id,
    };
    analyze.mutate(request, {
      onSuccess: (data) => {
        setResult(data, request);
        try {
          if (typeof window !== "undefined") {
            localStorage.setItem("astroos_last_viewed_chart_id", chart.id);
          }
        } catch {
          // ignore
        }
      },
      onError: (err) => {
        autoHydrated.current = false;
        console.error("Failed to load chart analysis:", err);
      },
    });
  };

  // Auto-Hydrate Dashboard on Page Load:
  useEffect(() => {
    if (autoHydrated.current || chartsLoading || !chartsData || chartsData.charts.length === 0) return;
    if (storeResult && storeRequest) return;

    autoHydrated.current = true;
    let targetChart: BirthChartSummary | null = null;
    try {
      const lastViewedId = localStorage.getItem("astroos_last_viewed_chart_id");
      if (lastViewedId) {
        targetChart = chartsData.charts.find((c) => c.id === lastViewedId) || null;
      }
    } catch {
      // ignore
    }

    if (!targetChart) {
      targetChart = chartsData.charts.find((c) => c.is_default) || chartsData.charts[0] || null;
    }

    if (targetChart) {
      handleSelectAndLoadChart(targetChart);
    }
  }, [chartsLoading, chartsData, storeResult, storeRequest]);


  return (
    <>
      {/* ♿ Skip Navigation Links for Keyboard & Screen Reader Users */}
      <nav aria-label="Skip navigation links" className="sr-only focus-within:not-sr-only focus-within:relative focus-within:z-50">
        <div className="flex flex-wrap gap-2 p-3 bg-cyan-900 text-white rounded-xl shadow-xl font-mono text-xs mb-3">
          <a href="#main-content" className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 rounded font-bold">Skip to Main Content</a>
          <a href="#kpi-scorecards" className="px-3 py-1.5 bg-cyan-700 hover:bg-cyan-600 rounded font-bold">Skip to KPI Scorecards</a>
          <a href="#panchanga-studio" className="px-3 py-1.5 bg-cyan-700 hover:bg-cyan-600 rounded font-bold">Skip to Panchanga Studio</a>
          <a href="#recent-charts-section" className="px-3 py-1.5 bg-cyan-700 hover:bg-cyan-600 rounded font-bold">Skip to Recent Charts</a>
        </div>
      </nav>

      {/* ♿ Live Status Region for Screen Readers */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {analyze.isPending ? "Calculating horoscope chart and astrological synthesis..." : storeResult ? `Active chart loaded for ${storeRequest?.subject_name || "subject"}.` : ""}
      </div>

      <DashboardErrorBoundary
        fallbackTitle="Dashboard Overview Error"
        fallbackMessage="An unexpected issue occurred while rendering the dashboard overview."
        onReset={() => {
          clearResult();
          analyze.reset();
        }}
      >
        <DashboardOverview
          activeResult={storeResult}
          activeSubjectName={storeRequest?.subject_name}
          isLoadingChart={analyze.isPending || (chartsLoading && !storeResult)}
          onStartNewChart={() => {
            clearResult();
            analyze.reset();
            openCreateModal();
          }}
          onSelectChart={handleSelectAndLoadChart}
        />
      </DashboardErrorBoundary>
    </>
  );
}
