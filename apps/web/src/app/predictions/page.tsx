"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { PredictionStepList } from "@/components/charts/predictions/PredictionStepList";
import { PredictionStepDetail } from "@/components/charts/predictions/PredictionStepDetail";
import { PredictionDashaTimeline } from "@/components/charts/predictions/PredictionDashaTimeline";
import { PredictionDataSources } from "@/components/charts/predictions/PredictionDataSources";
import { PredictionRelatedRules } from "@/components/charts/predictions/PredictionRelatedRules";
import { PredictionFactorsPanel } from "@/components/charts/predictions/PredictionFactorsPanel";
import { PredictionChainGraph } from "@/components/charts/predictions/PredictionChainGraph";
import { FormulaInspectorPanel } from "@/components/charts/predictions/FormulaInspectorPanel";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useAvastha } from "@/lib/avastha";
import { useShadbalaAll } from "@/lib/shadbala";
import { buildPredictionGraph } from "@/lib/predictions/chainEngine";
import { AREA_LABELS, type LifeArea } from "@/lib/predictions/types";
import type { WorkflowAnalysisRequest } from "@/lib/types";
import {
  ConfidenceHeatmap,
  CategoryStrengthRadar,
  YogaImpactHeatmap,
  SourceDensityHeatmap,
  OverallConfidenceRadar,
  QuickInsights,
  type AreaGraphEntry,
} from "@/components/charts/predictions/PredictionInsights";

const AREA_KEYS = Object.keys(AREA_LABELS) as LifeArea[];

function isLifeArea(v: string | null): v is LifeArea {
  return !!v && (AREA_KEYS as string[]).includes(v);
}

type TabId = "overview" | "formula" | "timeline" | "yogas" | "sources" | "ai" | "insights";

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "formula", label: "Formula Inspector" },
  { id: "timeline", label: "Timeline" },
  { id: "insights", label: "Heatmap / Radar" },
  { id: "yogas", label: "Yogas" },
  { id: "sources", label: "Sources" },
  { id: "ai", label: "AI Explain" },
];

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

  const [activeTab, setActiveTab] = useState<TabId>("overview");

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

  const allAreaGraphs: AreaGraphEntry[] = useMemo(() => {
    if (!result) return [];
    return AREA_KEYS.map((a) => ({
      area: a,
      label: AREA_LABELS[a],
      graph: buildPredictionGraph(a, result, { avastha: avasthaQuery.data, shadbalaAll: shadbalaAllQuery.data }),
    }));
  }, [result, avasthaQuery.data, shadbalaAllQuery.data]);

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
        {/* Breadcrumb */}
        <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>Predictions</span>
          <span>›</span>
          <span style={{ color: "var(--text-secondary)" }}>{graph?.finalLabel ?? "Prediction Explorer"}</span>
        </div>

        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-baseline gap-3">
            <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
              {graph?.finalLabel ?? "Prediction Explorer"}
            </h1>
            {graph && (
              <span className="text-2xl font-bold" style={{ color: "var(--accent)" }}>
                {graph.finalScore} <span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}>/ 100</span>
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
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
              aria-label="Select Life Area"
            >
              {AREA_KEYS.map((key) => (
                <option key={key} value={key}>
                  {AREA_LABELS[key]}
                </option>
              ))}
            </select>
          </div>
        </div>

        {graph && (
          <div className="flex flex-wrap items-center gap-6">
            <span className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
              Confidence
              <span
                className="rounded-full px-2.5 py-1 text-xs font-semibold"
                style={{
                  color: graph.confidence.level === "High" ? "#34d399" : graph.confidence.level === "Medium" ? "#fbbf24" : "#f87171",
                  border: `1px solid ${graph.confidence.level === "High" ? "#34d399" : graph.confidence.level === "Medium" ? "#fbbf24" : "#f87171"}`,
                }}
              >
                {graph.confidence.level}
              </span>
            </span>
            <span className="flex min-w-[180px] items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
              Data Completeness
              <span className="h-1.5 w-24 overflow-hidden rounded-full" style={{ backgroundColor: "var(--border-primary)" }}>
                <span className="block h-full rounded-full" style={{ width: `${graph.confidence.dataCompletePercent}%`, backgroundColor: "var(--accent)" }} />
              </span>
              <span style={{ color: "var(--text-primary)" }}>{graph.confidence.dataCompletePercent}%</span>
            </span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 border-b" style={{ borderColor: "var(--border-primary)" }}>
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="px-4 py-2 text-sm font-medium transition"
              style={{
                color: activeTab === tab.id ? "var(--accent)" : "var(--text-secondary)",
                borderBottom: activeTab === tab.id ? "2px solid var(--accent)" : "2px solid transparent",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {graph && (
          <div>
            {activeTab === "overview" && (
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-[280px_1fr_340px]">
                <PredictionFactorsPanel
                  nodes={graph.nodes}
                  selectedId={selectedNodeId}
                  onSelect={setSelectedNodeId}
                  baseline={graph.baseline}
                  finalScore={graph.finalScore}
                />

                <div className="flex flex-col gap-5">
                  <PredictionChainGraph graph={graph} selectedId={selectedNodeId} onSelect={setSelectedNodeId} />
                  <div className="glass-card p-5">
                    <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                      Summary
                    </h3>
                    <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                      {[...graph.nodes]
                        .filter((n) => !n.unavailable && n.detail.length > 0)
                        .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
                        .slice(0, 3)
                        .map((n) => n.detail[0])
                        .join(" ") || "No computation detail available for this chart yet."}
                    </p>
                  </div>
                </div>

                <FormulaInspectorPanel
                  nodes={graph.nodes}
                  selectedId={selectedNodeId}
                  onSelect={setSelectedNodeId}
                  onViewSources={() => setActiveTab("sources")}
                />
              </div>
            )}

            {activeTab === "formula" && (
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-[280px_1fr]">
                <PredictionStepList nodes={graph.nodes} selectedId={selectedNodeId} onSelect={setSelectedNodeId} />
                <PredictionStepDetail node={selectedNode} />
              </div>
            )}

            {activeTab === "timeline" && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Dasha Timeline
                </h3>
                <PredictionDashaTimeline entries={graph.dashaTimeline} />
              </div>
            )}

            {activeTab === "insights" && (
              <div className="flex flex-col gap-5">
                <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
                  <ConfidenceHeatmap areaGraphs={allAreaGraphs} />
                  <CategoryStrengthRadar graph={graph} />
                  <YogaImpactHeatmap areaGraphs={allAreaGraphs} />
                </div>
                <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
                  <SourceDensityHeatmap areaGraphs={allAreaGraphs} />
                  <OverallConfidenceRadar areaGraphs={allAreaGraphs} />
                  <QuickInsights areaGraphs={allAreaGraphs} />
                </div>
              </div>
            )}

            {activeTab === "yogas" && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Related Yogas
                </h3>
                <div className="space-y-3">
                  {graph.nodes
                    .filter((n) => n.category === "Yogas")
                    .map((node) => (
                      <div key={node.id} className="p-3 rounded" style={{ border: "1px solid var(--border-primary)" }}>
                        <h4 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{node.label}</h4>
                        <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                          Delta: {node.delta >= 0 ? "+" : ""}{node.delta}
                        </p>
                        <ul className="mt-2 space-y-1">
                          {node.detail.map((d, i) => (
                            <li key={i} className="text-xs" style={{ color: "var(--text-muted)" }}>{d}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  {graph.nodes.filter((n) => n.category === "Yogas").length === 0 && (
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>No yogas directly related to this life area.</p>
                  )}
                </div>
                <div className="mt-4">
                  <PredictionRelatedRules rules={graph.relatedRules} />
                </div>
              </div>
            )}

            {activeTab === "sources" && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  Data Sources
                </h3>
                <PredictionDataSources sources={graph.dataSources} />
              </div>
            )}

            {activeTab === "ai" && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
                  AI Explanation
                </h3>
                <div className="space-y-4">
                  <div className="p-4 rounded" style={{ backgroundColor: "var(--bg-card)" }}>
                    <h4 className="text-sm font-semibold mb-2" style={{ color: "var(--accent)" }}>
                      Why is {AREA_LABELS[graph.area]} {graph.finalScore}/100?
                    </h4>
                    <p className="text-sm mb-3" style={{ color: "var(--text-secondary)" }}>
                      {graph.finalLabel}
                    </p>
                    <div className="space-y-2">
                      {graph.nodes
                        .filter((n) => !n.unavailable)
                        .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
                        .slice(0, 5)
                        .map((node, i) => (
                          <div key={i} className="text-xs" style={{ color: "var(--text-primary)" }}>
                            • {node.detail[0] || node.label}
                          </div>
                        ))}
                    </div>
                  </div>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    This is a rule-based explanation. Full AI-powered conversational explanation coming in Phase 7.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}