"use client";

import { useState, useEffect } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { BirthDetailsForm } from "@/components/workflow/BirthDetailsForm";
import { AnalysisResults } from "@/components/workflow/AnalysisResults";
import { KpiScorecards } from "@/components/dashboard/KpiScorecards";
import { DashboardSearchBar } from "@/components/dashboard/DashboardSearchBar";
import { DashboardOverview } from "@/components/dashboard/DashboardOverview";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { ApiError } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import type { WorkflowAnalysisRequest } from "@/lib/types";

export default function DashboardPage() {
  const analyze = useAnalyzeWorkflow();
  const setResult = useWorkflowStore((s) => s.setResult);
  const clearResult = useWorkflowStore((s) => s.clear);
  // The shared store — not this component's own mutation state — is the
  // source of truth for "is there a result to show". The form submission
  // below writes into it via the effect, but so does RecomputeChartModal
  // (from Saved Charts), which uses its own separate useAnalyzeWorkflow()
  // mutation instance. Two different useMutation() calls never share
  // isSuccess/data state with each other — only the store is shared —
  // so gating the render on this component's local `analyze.isSuccess`
  // meant a successful recompute updated the store but Dashboard kept
  // showing the blank form, since ITS OWN mutation was never triggered.
  const storeResult = useWorkflowStore((s) => s.result);
  const storeRequest = useWorkflowStore((s) => s.request);
  const [lastRequest, setLastRequest] =
    useState<WorkflowAnalysisRequest | null>(null);

  // Persist latest result to global store so /charts pages can read it
  useEffect(() => {
    if (analyze.isSuccess && analyze.data && lastRequest) {
      setResult(analyze.data, lastRequest);
    }
  }, [analyze.isSuccess, analyze.data, lastRequest, setResult]);

  const errorMessage =
    analyze.error instanceof ApiError
      ? analyze.error.detail
      : analyze.error
        ? "An unexpected error occurred. Please try again."
        : null;

  return (
    <AppShell>
      {/* Overview stays visible regardless of whether a chart is currently
          loaded — it's the home/landing content (mockup: "Dashboard
          Overview"), not tied to the single-chart workflow below it. */}
      <div className="mb-8">
        <DashboardOverview
          activeResult={storeResult}
          activeSubjectName={storeRequest?.subject_name}
          onStartNewChart={() => {
            clearResult();
            analyze.reset();
            setLastRequest(null);
          }}
        />
      </div>

      <div className="mb-6 border-t pt-6" style={{ borderColor: "var(--border-primary)" }}>
        <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
          {storeResult ? "Analysis Result" : "New Chart"}
        </h2>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          {storeResult
            ? "Chart → Vargas → Dasha → Yoga → Shadbala → Ashtakavarga → Transit → Rule Engine → Knowledge → Verification → Report."
            : "Submit birth data to run the full analysis pipeline."}
        </p>
      </div>

      <div className="mb-6">
        <DashboardSearchBar />
      </div>

      {storeResult && storeRequest ? (
        <div className="space-y-6">
          <KpiScorecards result={storeResult} />
          <AnalysisResults
            result={storeResult}
            request={storeRequest}
            onReset={() => {
              clearResult();
              analyze.reset();
              setLastRequest(null);
            }}
          />
        </div>
      ) : (
        <div className="mx-auto max-w-xl">
          <BirthDetailsForm
            onSubmit={(request) => {
              setLastRequest(request);
              analyze.mutate(request);
            }}
            isPending={analyze.isPending}
            errorMessage={errorMessage}
          />
        </div>
      )}
    </AppShell>
  );
}
