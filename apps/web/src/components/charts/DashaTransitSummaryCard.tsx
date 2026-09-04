"use client";

import Link from "next/link";
import type { WorkflowAnalysisResponse, WorkflowAnalysisRequest } from "@/lib/types";
import { currentDasha, currentTransitSummary } from "@/lib/kpiScoring";

interface DashaTransitSummaryCardProps {
  result: WorkflowAnalysisResponse;
  request?: WorkflowAnalysisRequest | null;
}

export function DashaTransitSummaryCard({
  result,
  request,
}: DashaTransitSummaryCardProps) {
  const { chart, dasha, yogas, shadbala } = result;

  // Compute active dasha details
  const now = new Date().getTime();
  const currentMD = dasha?.mahadashas?.find(
    (m) =>
      now >= new Date(m.start_date).getTime() &&
      now <= new Date(m.end_date).getTime(),
  );
  const currentAD = currentMD?.sub_periods?.find(
    (p) =>
      now >= new Date(p.start_date).getTime() &&
      now <= new Date(p.end_date).getTime(),
  );

  let mdPercent = 0;
  let daysRemaining = 0;
  if (currentMD) {
    const start = new Date(currentMD.start_date).getTime();
    const end = new Date(currentMD.end_date).getTime();
    const total = end - start;
    const elapsed = now - start;
    mdPercent = total > 0 ? Math.min(100, Math.max(0, Math.round((elapsed / total) * 100))) : 0;
    daysRemaining = Math.max(0, Math.round((end - now) / 86400000));
  }

  // Calculate average shadbala in Rupas if available
  const avgShadbala =
    shadbala && shadbala.length > 0
      ? (
          shadbala.reduce((acc, s) => acc + s.total_rupas, 0) / shadbala.length
        ).toFixed(1)
      : null;

  const activeYogasCount =
    yogas?.total_present ?? yogas?.results?.filter((y) => y.is_present).length ?? 0;

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm flex flex-col gap-3 h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
          Active Influence
        </h3>
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-50 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800">
          Live Timing
        </span>
      </div>

      {/* Mini KPI Pills */}
      <div className="grid grid-cols-3 gap-1.5">
        <div className="p-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 text-center">
          <p className="text-[9px] uppercase font-semibold text-slate-500 dark:text-slate-400">Yogas</p>
          <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{activeYogasCount} Active</p>
        </div>
        <div className="p-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 text-center">
          <p className="text-[9px] uppercase font-semibold text-slate-500 dark:text-slate-400">Moon Sign</p>
          <p className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">
            {chart.planets.find((p) => p.planet === "Moon")?.rashi || "—"}
          </p>
        </div>
        <div className="p-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 text-center">
          <p className="text-[9px] uppercase font-semibold text-slate-500 dark:text-slate-400">Shadbala</p>
          <p className="text-xs font-bold text-cyan-600 dark:text-cyan-400">
            {avgShadbala ? `${avgShadbala}R` : "Normal"}
          </p>
        </div>
      </div>

      {/* Dasha Period Section */}
      <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Vimshottari Dasha
          </span>
          <Link
            href="/charts/dasha"
            className="text-[10px] font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
          >
            Timeline →
          </Link>
        </div>

        <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
          {currentDasha(result)}
        </p>

        {currentMD && (
          <div className="mt-2 space-y-1">
            <div className="flex justify-between text-[10px] text-slate-600 dark:text-slate-400">
              <span>{currentMD.lord} Mahadasha</span>
              <span>{mdPercent}% ({Math.floor(daysRemaining / 30)} mo left)</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
                style={{ width: `${mdPercent}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Transit Gochara Section */}
      <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Current Transits
          </span>
          <Link
            href="/charts/transit"
            className="text-[10px] font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
          >
            Gochara Map →
          </Link>
        </div>

        <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
          {currentTransitSummary(result)}
        </p>
        <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
          Calculated relative to natal Moon in {chart.planets.find((p) => p.planet === "Moon")?.rashi || "chart"}.
        </p>
      </div>

      {/* Quick Actions Shortcuts */}
      <div className="mt-auto pt-1 flex items-center gap-2">
        <Link
          href="/charts/transit"
          className="flex-1 py-1.5 px-2 text-center text-xs font-semibold rounded-lg bg-cyan-50 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800 hover:bg-cyan-100 dark:hover:bg-cyan-900/60 transition"
        >
          Transits Console
        </Link>
        <Link
          href="/charts/compare"
          className="flex-1 py-1.5 px-2 text-center text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
        >
          Compare Charts
        </Link>
      </div>
    </div>
  );
}
