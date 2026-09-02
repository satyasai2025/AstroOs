"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { GraphExplorer } from "@/components/charts/knowledge-graph/GraphExplorer";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import type { WorkflowAnalysisRequest } from "@/lib/types";
import { normalizeAyanamsa, normalizeHouseSystem } from "@/lib/types";

export default function GraphExplorerPage() {
  const result = useWorkflowStore((s) => s.result);
  const setResult = useWorkflowStore((s) => s.setResult);

  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const analyze = useAnalyzeWorkflow();
  const [autoRecomputeStarted, setAutoRecomputeStarted] = useState(false);

  const targetSummary = useMemo(() => {
    if (!chartsData) return null;
    return chartsData.charts.find((c) => c.is_default) ?? chartsData.charts[0] ?? null;
  }, [chartsData]);

  useEffect(() => {
    if (result || autoRecomputeStarted || !targetSummary) return;
    setAutoRecomputeStarted(true);
    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: targetSummary.birth_datetime_utc,
      latitude: targetSummary.birth_latitude,
      longitude: targetSummary.birth_longitude,
      ayanamsa: normalizeAyanamsa(targetSummary.ayanamsa),
      house_system: normalizeHouseSystem(targetSummary.house_system),
      dasha_system: "vimshottari",
      include_vargas: true,
      subject_name: targetSummary.subject_name,
      place_name: targetSummary.place_name,
      persist: false,
      chart_id: targetSummary.id,
    };
    analyze.mutate(request, { onSuccess: (data) => setResult(data, request) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result, autoRecomputeStarted, targetSummary]);

  return (
    <>
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
          <span>Knowledge Graph</span>
          <span>›</span>
          <span style={{ color: "var(--text-secondary)" }}>Graph Explorer</span>
        </div>

        <div>
          <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
            Knowledge Graph Explorer
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Interactive graph of this chart&apos;s planets, houses, present yogas and current dasha — click any node to see its real, chart-derived relationships.
          </p>
        </div>

        {!result ? (
          <div className="flex flex-col items-center justify-center gap-4 py-20" role="status">
            <div className="glass-card flex flex-col items-center gap-4 p-8 text-center">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" style={{ color: "var(--text-muted)" }}>
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              {chartsLoading || analyze.isPending ? (
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Loading chart data…</p>
              ) : (
                <>
                  <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>No Chart Data Available</h2>
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Run an analysis on the Dashboard first to populate chart data.</p>
                  <Link href="/dashboard" className="btn-primary">Go to Dashboard</Link>
                </>
              )}
            </div>
          </div>
        ) : (
          <GraphExplorer result={result} />
        )}
      </div>
    </>
  );
}
