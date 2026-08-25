"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ChartDetailView } from "@/components/charts/ChartDetailView";
import { RecomputeChartModal } from "@/components/charts/RecomputeChartModal";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useWorkflowStore } from "@/lib/store";
import { ApiError } from "@/lib/api";
import type { BirthChartSummary, WorkflowAnalysisRequest } from "@/lib/types";

/**
 * Per-chart detail page. There's no GET-by-chart-id endpoint that returns
 * the full analysis payload (D1 + vargas + dasha + yogas + shadbala...) —
 * only /workflow/analyze (compute) and /horoscope/my-charts (list
 * summaries) exist. So:
 *   - If the shared store already holds this exact chart's result (the
 *     common case: you just created or recomputed it), render it directly.
 *   - Otherwise (direct link, fresh reload, browser back/forward), look
 *     up this chart's saved birth parameters from the summary list and
 *     silently recompute the full analysis once, using the same defaults
 *     RecomputeChartModal starts from (vimshottari dasha, vargas included)
 *     — Swiss Ephemeris is deterministic, so this reproduces the same
 *     chart, not a different one. Sent with persist: false and this
 *     chart's own id, so the recompute never writes a duplicate
 *     birth_charts row — see WorkflowAnalysisRequest.persist.
 */
const KNOWN_VIEW_REDIRECTS: Record<string, string> = {
  houses: "houses",
  relationships: "relationships-v2",
  "relationships-v2": "relationships-v2",
  dasha: "dasha",
  yogas: "yogas",
  ashtakavarga: "ashtakavarga",
  strength: "strength",
  kp: "kp",
  jaimini: "jaimini",
  planets: "planets",
  divisional: "divisional",
  kundli: "kundli",
  birth: "chart",
  chart: "chart",
  timeline: "timeline",
  predictions: "predictions",
};

export default function ChartDetailPage() {
  const params = useParams<{ chartId: string }>();
  const router = useRouter();
  const chartId = params.chartId;

  useEffect(() => {
    if (chartId === "planets") {
      router.replace("/charts/planets");
      return;
    }
    if (chartId && KNOWN_VIEW_REDIRECTS[chartId]) {
      router.replace(`/charts?view=${KNOWN_VIEW_REDIRECTS[chartId]}`);
    }
  }, [chartId, router]);

  const storeResult = useWorkflowStore((s) => s.result);
  const storeRequest = useWorkflowStore((s) => s.request);
  const setResult = useWorkflowStore((s) => s.setResult);

  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const analyze = useAnalyzeWorkflow();
  const [recomputeTarget, setRecomputeTarget] = useState<BirthChartSummary | null>(null);

  const hasMatchingResult = storeResult?.chart_id === chartId && !!storeRequest;
  const summary = chartsData?.charts.find((c) => c.id === chartId) ?? null;

  const [autoRecomputeStarted, setAutoRecomputeStarted] = useState(false);

  useEffect(() => {
    if (chartId && KNOWN_VIEW_REDIRECTS[chartId]) return;
    if (hasMatchingResult || autoRecomputeStarted || !summary) return;
    setAutoRecomputeStarted(true);
    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: summary.birth_datetime_utc,
      latitude: summary.birth_latitude,
      longitude: summary.birth_longitude,
      ayanamsa: summary.ayanamsa as WorkflowAnalysisRequest["ayanamsa"],
      house_system: summary.house_system as WorkflowAnalysisRequest["house_system"],
      dasha_system: "vimshottari",
      include_vargas: true,
      subject_name: summary.subject_name,
      place_name: summary.place_name,
      persist: false,
      chart_id: summary.id,
    };
    analyze.mutate(request, {
      onSuccess: (data) => setResult(data, request),
    });
    // Only fire once per chartId — `analyze`/`setResult` are stable
    // references from useMutation/zustand, safe to omit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasMatchingResult, autoRecomputeStarted, summary]);

  let body: React.ReactNode;

  if (hasMatchingResult) {
    body = (
      <ChartDetailView
        result={storeResult!}
        request={storeRequest!}
        onEditDetails={summary ? () => setRecomputeTarget(summary) : undefined}
      />
    );
  } else if (chartsLoading || analyze.isPending) {
    body = (
      <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
        {chartsLoading ? "Loading chart…" : "Recomputing chart…"}
      </div>
    );
  } else if (!summary) {
    body = (
      <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
        <p>No saved chart with that ID, or it isn&apos;t yours.</p>
        <Link href="/charts/history" className="obsidian-btn-primary mt-4 inline-flex text-sm">
          Back to My Charts
        </Link>
      </div>
    );
  } else if (analyze.isError) {
    const msg =
      analyze.error instanceof ApiError ? analyze.error.detail : "Could not recompute this chart.";
    body = (
      <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
        {msg}
      </div>
    );
  } else {
    body = (
      <div className="obsidian-card p-10 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
        Recomputing chart…
      </div>
    );
  }

  return (
    <>
      {body}
      {recomputeTarget && (
        <RecomputeChartModal chart={recomputeTarget} onClose={() => setRecomputeTarget(null)} />
      )}
    </>
  );
}
