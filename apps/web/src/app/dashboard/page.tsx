"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { BirthDetailsForm } from "@/components/workflow/BirthDetailsForm";
import { AnalysisResults } from "@/components/workflow/AnalysisResults";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { ApiError } from "@/lib/api";
import type { WorkflowAnalysisRequest } from "@/lib/types";

export default function DashboardPage() {
  const analyze = useAnalyzeWorkflow();
  const [lastRequest, setLastRequest] =
    useState<WorkflowAnalysisRequest | null>(null);

  const errorMessage =
    analyze.error instanceof ApiError
      ? analyze.error.detail
      : analyze.error
        ? "An unexpected error occurred. Please try again."
        : null;

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Unified Analysis Pipeline</h1>
        <p className="mt-1 text-sm text-slate-400">
          One birth-data submission runs Chart → Vargas → Dasha → Yoga → Shadbala →
          Ashtakavarga → Transit → Rule Engine → Knowledge → Verification → Report.
        </p>
      </div>

      {analyze.isSuccess && lastRequest ? (
        <AnalysisResults
          result={analyze.data}
          request={lastRequest}
          onReset={() => analyze.reset()}
        />
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
