"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { PredictionStepList } from "@/components/charts/predictions/PredictionStepList";
import { PredictionStepDetail } from "@/components/charts/predictions/PredictionStepDetail";
import { PredictionScorePanel } from "@/components/charts/predictions/PredictionScorePanel";
import { PredictionScoreBreakdown } from "@/components/charts/predictions/PredictionScoreBreakdown";
import { PredictionDashaTimeline } from "@/components/charts/predictions/PredictionDashaTimeline";
import { PredictionDataSources } from "@/components/charts/predictions/PredictionDataSources";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useAvastha } from "@/lib/avastha";
import { useShadbalaAll } from "@/lib/shadbala";
import { buildPredictionGraph } from "@/lib/predictions/chainEngine";
import { AREA_LABELS } from "@/lib/predictions/scoring";
import type { LifeArea } from "@/lib/predictions/types";
import type { WorkflowAnalysisRequest } from "@/lib/types";

const AREA_KEYS = Object.keys(AREA_LABELS) as LifeArea[];

function isLifeArea(v: string | null): v is LifeArea {
  return !!v && (AREA_KEYS as string[]).includes(v);
}

export default function PredictionsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const storeResult = useWorkflowStore((s) => s.result);
  const storeRequest = useWorkflowStore((s) => s.request);
  const setResult = useWorkflowStore((s) => s.setResult);

  const requestedChartId = searchParams.get("chartId");
  const requestedKpi = searchParams.get("kpi");

  const [area, setArea] = useState<LifeArea>(isLifeArea(requestedKpi) ? requestedKpi : "career");
  useEffect(() => {
    if (isLifeArea(requestedKpi)) setArea(requestedKpi);
  }, [requestedKpi]);

  const hasMatchingResult = requestedChartId ? storeResult?.chart_id === requestedChartId && !!storeRequest : !!storeResult && !!storeRequest;

  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const analyze = useAnalyzeWorkflow();
  const [autoRecomputeStarted, setAutoRecomputeStarted] = useState(false);

  const targetSummary = useMemo(() => {
    if (!chartsData) return null;
    if (requestedChartId) return chartsData.charts.find((c) => c.id === requestedChartId) ?? null;
    return chartsData.charts.find((c) => c.is_default) ?? chartsData.charts[0] ?? null;
  }, [chartsData, requestedChartId]);

  useEffect(() => {
    if (hasMatchingResult || autoRecomputeStarted || !targetSummary) return;
    setAutoRecomputeStarted(true);
    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: targetSummary.birth_datetime_utc,
      latitude: targetSummary.birth_latitude,
      longitude: targetSummary.birth_longitude,
      ayanamsa: targetSummary.ayanamsa as WorkflowAnalysisRequest["ayanamsa"],
      house_system: targetSummary.house_system as WorkflowAnalysisRequest["house_system"],
      dasha_system: "vimshottari",
      include_vargas: true,
      subject_name: targetSummary.subject_name,
      place_name: targetSummary.place_name,
      persist: false,
      chart_id: targetSummary.id,
    };
    analyze.mutate(request, { onSuccess: (data) => setResult(data, request) });
    // Fire once per targetSummary — analyze/setResult are stable references.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasMatchingResult, autoRecomputeStarted, targetSummary]);

  const result = hasMatchingResult ? storeResult! : null;
  const request = hasMatchingResult ? storeRequest! : null;

  const avasthaQuery = useAvastha(request);
  const shadbalaAllQuery = useShadbalaAll(request);

  const graph = useMemo(() => {
    if (!result) return null;
    return buildPredictionGraph(area, result, { avastha: avasthaQuery.data, shadbalaAll: shadbalaAllQuery.data });
  }, [area, result, avasthaQuery.data, shadbalaAllQuery.data]);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  useEffect(() => {
    setSelectedNodeId(graph?.nodes[0]?.id ?? null);
  }, [graph]);

  const selectedNode = graph?.nodes.find((n) => n.id === selectedNodeId) ?? null;

  if (!result) {
    return (
      <AppShell sectionColor="--section-analysis">
        <div className="flex flex-col items-center justify-center gap-4 py-20" role="status">
          <div className="glass-card flex flex-col items-center gap-4 p-8 text-center">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" style={{ color: "var(--text-muted)" }}>
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            {chartsLoading || analyze.isPending ? (
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Loading chart data…
              </p>
            ) : (
              <>
                <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                  No Chart Data Available
                </h2>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                  Run an analysis on the Dashboard first to populate chart data.
                </p>
                <Link href="/dashboard" className="btn-primary">
                  Go to Dashboard
                </Link>
              </>
            )}
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell sectionColor="--section-analysis">
      <div className="flex flex-col gap-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
              Prediction Chain Explorer
            </h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              The real computation chain behind each prediction — every number traces back to a real chart field.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span
              className="rounded-full px-3 py-1.5 text-xs font-medium"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
            >
              Chart: Rashi (D1)
            </span>
            <select
              value={area}
              onChange={(e) => {
                const next = e.target.value as LifeArea;
                setArea(next);
                const params = new URLSearchParams(searchParams.toString());
                params.set("kpi", next);
                router.replace(`/predictions?${params.toString()}`);
              }}
              className="field-input"
              style={{ width: "auto" }}
              aria-label="Select KPI"
            >
              {AREA_KEYS.map((key) => (
                <option key={key} value={key}>
                  {AREA_LABELS[key]} Strength
                </option>
              ))}
            </select>
          </div>
        </div>

        {graph && (
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[280px_1fr_300px]">
            <PredictionStepList nodes={graph.nodes} selectedId={selectedNodeId} onSelect={setSelectedNodeId} />

            <PredictionStepDetail node={selectedNode} />

            <div className="flex flex-col gap-5">
              <PredictionScorePanel finalLabel={graph.finalLabel} finalScore={graph.finalScore} confidence={graph.confidence} />
              <PredictionScoreBreakdown categories={graph.categories} baseline={graph.baseline} finalScore={graph.finalScore} />
              <PredictionDashaTimeline entries={graph.dashaTimeline} />
              <PredictionDataSources sources={graph.dataSources} />
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
