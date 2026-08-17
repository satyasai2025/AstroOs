"use client";

import React from "react";
import { useWorkflowStore } from "@/lib/store";

export function SplitWorkspaceLayout({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
}) {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const setRequest = useWorkflowStore((s) => s.setRequest);

  React.useEffect(() => {
    if (!request && typeof window !== "undefined") {
      const stored = localStorage.getItem("astroos_active_chart_request");
      if (stored) {
        try {
          setRequest(JSON.parse(stored));
        } catch {
          // ignore
        }
      }
    }
  }, [request, setRequest]);
  
  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Left Pane: Fixed 280px-320px Sidebar */}
      <div className="w-[280px] lg:w-[300px] flex-shrink-0 border-r border-slate-200 dark:border-slate-800 p-3 overflow-y-auto bg-white/70 dark:bg-slate-900/60 backdrop-blur-sm">
        <h2 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
          Active Subject
        </h2>
        {request ? (
          <div className="space-y-3">
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3.5 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{request.subject_name || "Active Chart"}</h3>
              <p className="mt-0.5 text-xs font-mono text-slate-600 dark:text-slate-400">
                {new Date(request.birth_datetime_utc).toLocaleString()}
              </p>
              <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                {request.latitude.toFixed(2)}°, {request.longitude.toFixed(2)}° · {request.place_name || request.ayanamsa}
              </p>
            </div>

            {result && (
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3.5 shadow-sm">
                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                  Ascendant &amp; Moon
                </h4>
                <p className="mt-1.5 text-xs text-slate-700 dark:text-slate-300">
                  Lagna: <span className="font-semibold capitalize text-cyan-600 dark:text-cyan-400">{result.chart.ascendant.rashi}</span> ({result.chart.ascendant.nakshatra})
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-800 p-4 text-center">
            <p className="text-xs font-medium text-slate-700 dark:text-slate-300">No active chart loaded.</p>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Select or create a chart to view the subject profile.
            </p>
          </div>
        )}
      </div>

      {/* Right Pane: Main Content */}
      <div className="min-w-0 flex-1 overflow-x-hidden overflow-y-auto p-3 md:p-4 bg-slate-50/50 dark:bg-slate-950">
        {title && (
          <div className="mb-3 pb-2 border-b border-slate-200 dark:border-slate-800">
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">{title}</h1>
            {subtitle && <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">{subtitle}</p>}
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
