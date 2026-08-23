"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";

export const dynamic = "force-dynamic";

/**
 * Canonical URL Redirect:
 * AstroOS uses single canonical URLs per birth chart (`/charts/[chartId]`).
 * Visiting `/charts/birth` automatically redirects to the active or default chart's
 * unique URL (`/charts/[chartId]`), eliminating URL duplication across the app.
 */
export default function BirthChartPageRedirect() {
  const router = useRouter();
  const storeResult = useWorkflowStore((s) => s.result);
  const { data: myChartsData, isLoading: loadingCharts } = useMyCharts();

  useEffect(() => {
    if (loadingCharts) return;

    // 1. If active chart in store has a chart_id, redirect to its canonical URL
    if (storeResult?.chart_id) {
      router.replace(`/charts/${storeResult.chart_id}`);
      return;
    }

    // 2. Otherwise find last viewed or default saved chart from list
    const activeId = typeof window !== "undefined" ? localStorage.getItem("astroos_last_viewed_chart_id") : null;
    const target =
      (activeId ? myChartsData?.charts?.find((c) => c.id === activeId) : null) ??
      myChartsData?.charts?.find((c) => c.is_default) ??
      myChartsData?.charts?.[0];

    if (target?.id) {
      router.replace(`/charts/${target.id}`);
    } else {
      // Fallback to dashboard if no chart exists yet
      router.replace("/dashboard");
    }
  }, [storeResult, myChartsData, loadingCharts, router]);

  return (
    <div className="flex h-[60vh] items-center justify-center font-mono text-xs text-slate-400">
      <div className="flex items-center gap-2">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent" />
        <span>Navigating to Birth Chart…</span>
      </div>
    </div>
  );
}
