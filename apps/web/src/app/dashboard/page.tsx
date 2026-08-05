"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardOverview } from "@/components/dashboard/DashboardOverview";
import { CreateChartModal, type ChartTypeId } from "@/components/dashboard/CreateChartModal";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { ApiError } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import type { WorkflowAnalysisRequest } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const analyze = useAnalyzeWorkflow();
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

  // A newly-generated chart is no longer shown inline on the dashboard —
  // it's saved (setResult, so /charts pages can still read it) and the
  // user is taken to My Charts, where the chart itself lives, rather than
  // the dashboard growing a second full analysis view under the overview.
  useEffect(() => {
    if (analyze.isSuccess && analyze.data && lastRequest) {
      setResult(analyze.data, lastRequest);
      closeCreateModal();
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
    <AppShell>
      <DashboardOverview
        activeResult={storeResult}
        activeSubjectName={storeRequest?.subject_name}
        onStartNewChart={() => {
          clearResult();
          analyze.reset();
          setLastRequest(null);
          openCreateModal();
        }}
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
    </AppShell>
  );
}
