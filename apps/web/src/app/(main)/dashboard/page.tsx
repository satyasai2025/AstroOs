"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { DashboardOverview } from "@/components/dashboard/DashboardOverview";
import { CreateChartModal, type ChartTypeId } from "@/components/dashboard/CreateChartModal";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useMyCharts } from "@/lib/charts";
import { ApiError } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import type { BirthChartSummary, WorkflowAnalysisRequest } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const analyze = useAnalyzeWorkflow();
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const setResult = useWorkflowStore((s) => s.setResult);
  const clearResult = useWorkflowStore((s) => s.clear);
  const createModalOpen = useWorkflowStore((s) => s.createModalOpen);
  const createModalInitialType = useWorkflowStore((s) => s.createModalInitialType);
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);
  const closeCreateModal = useWorkflowStore((s) => s.closeCreateModal);
  const storeResult = useWorkflowStore((s) => s.result);
  const storeRequest = useWorkflowStore((s) => s.request);
  const [lastRequest, setLastRequest] =
    useState<WorkflowAnalysisRequest | null>(null);
  const autoHydrated = useRef(false);

  const handleSelectAndLoadChart = (chart: BirthChartSummary) => {
    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: chart.birth_datetime_utc,
      latitude: chart.birth_latitude,
      longitude: chart.birth_longitude,
      ayanamsa: chart.ayanamsa as WorkflowAnalysisRequest["ayanamsa"],
      house_system: chart.house_system as WorkflowAnalysisRequest["house_system"],
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
          localStorage.setItem("astroos_last_viewed_chart_id", chart.id);
        } catch {
          // ignore
        }
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

  // A newly-generated chart is saved and navigated to its detail page
  useEffect(() => {
    if (analyze.isSuccess && analyze.data && lastRequest) {
      setResult(analyze.data, lastRequest);
      closeCreateModal();
      try {
        localStorage.setItem("astroos_last_viewed_chart_id", analyze.data.chart_id);
      } catch {
        // ignore
      }
      router.push(`/charts/${analyze.data.chart_id}`);
    }
  }, [analyze.isSuccess, analyze.data, lastRequest, setResult, closeCreateModal, router]);

  const errorMessage =
    analyze.error instanceof ApiError
      ? analyze.error.detail
      : analyze.error
        ? "An unexpected error occurred. Please try again."
        : null;

  return (
    <>
      <DashboardOverview
        activeResult={storeResult}
        activeSubjectName={storeRequest?.subject_name}
        onStartNewChart={() => {
          clearResult();
          analyze.reset();
          setLastRequest(null);
          openCreateModal();
        }}
        onSelectChart={handleSelectAndLoadChart}
      />

      <CreateChartModal
        open={createModalOpen}
        onClose={closeCreateModal}
        onSubmit={(request) => {
          setLastRequest(request);
          analyze.mutate(request);
        }}
        isPending={analyze.isPending}
        errorMessage={errorMessage}
        initialChartType={createModalInitialType as ChartTypeId | null}
      />
    </>
  );
}
