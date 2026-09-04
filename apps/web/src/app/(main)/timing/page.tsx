"use client";

import { Suspense } from "react";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { UnifiedEventTimingWorkspace } from "@/components/timing/UnifiedEventTimingWorkspace";

function TimingPageContent() {
  const storeResult = useWorkflowStore((s) => s.result);
  const storeRequest = useWorkflowStore((s) => s.request);
  const { data: myCharts } = useMyCharts();

  const activeChart = myCharts?.charts?.find((c) => c.is_default) || myCharts?.charts?.[0];

  const request = storeRequest || (activeChart ? {
    birth_datetime_utc: activeChart.birth_datetime_utc,
    latitude: activeChart.birth_latitude,
    longitude: activeChart.birth_longitude,
    ayanamsa: activeChart.ayanamsa || "lahiri",
    house_system: activeChart.house_system || "P",
  } : null);

  return (
    <div className="w-full">
      <UnifiedEventTimingWorkspace
        request={request}
        result={storeResult}
      />
    </div>
  );
}

export default function TimingPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-[var(--text-muted)]">Loading Unified Event Timing Engine...</div>}>
      <TimingPageContent />
    </Suspense>
  );
}
