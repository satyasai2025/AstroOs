"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";
import { ChartPanel } from "@/components/workflow/panels/ChartPanel";
import { DashaTransitSummaryCard } from "@/components/charts/DashaTransitSummaryCard";
import { DivisionalChartSelector } from "@/components/charts/DivisionalChartSelector";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { LifeEventsTree } from "@/components/charts/LifeEventsTree";
import { KpiScorecards } from "@/components/dashboard/KpiScorecards";
import { ShareButton } from "@/components/ui";
import { useChartEvents } from "@/lib/events";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { VARGA_DIVISORS } from "@/lib/astro";
import type { WorkflowAnalysisRequest } from "@/lib/types";

export const dynamic = "force-dynamic";

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function findCurrentDasha(mahadashas: any[], at: Date) {
  const t = at.getTime();
  const md = mahadashas.find(
    (m: any) => t >= new Date(m.start_date).getTime() && t <= new Date(m.end_date).getTime(),
  );
  if (!md) return null;
  const ad = md.sub_periods?.find(
    (p: any) => t >= new Date(p.start_date).getTime() && t <= new Date(p.end_date).getTime(),
  );
  const totalMs = new Date(md.end_date).getTime() - new Date(md.start_date).getTime();
  const elapsedMs = t - new Date(md.start_date).getTime();
  const percentElapsed = totalMs > 0 ? Math.round((elapsedMs / totalMs) * 100) : 0;
  const daysLeft = Math.max(0, Math.round((new Date(md.end_date).getTime() - t) / 86_400_000));
  const yearsLeft = Math.floor(daysLeft / 365);
  const monthsLeft = Math.floor((daysLeft % 365) / 30);
  return { mahadasha: md, antardasha: ad ?? null, percentElapsed, daysLeft, yearsLeft, monthsLeft };
}

export default function BirthChartPage() {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const chartStyle = useWorkflowStore((s) => s.chartStyle);
  const setChartStyle = useWorkflowStore((s) => s.setChartStyle);
  const setResult = useWorkflowStore((s) => s.setResult);

  const { data: myChartsData, isLoading: loadingCharts } = useMyCharts();
  const analyze = useAnalyzeWorkflow();

  const [selectedVarga, setSelectedVarga] = useState<string>("D1");
  const [activePlanet, setActivePlanet] = useState<string | null>(null);
  const [activeHouse, setActiveHouse] = useState<number | null>(null);
  const [datasetAdded, setDatasetAdded] = useState(false);

  const chartId = result?.chart_id;
  const { data: chartEventsData } = useChartEvents(chartId);

  // Auto-hydrate if no active chart in store
  useEffect(() => {
    if (result || analyze.isPending || loadingCharts) return;
    const activeId = typeof window !== "undefined" ? localStorage.getItem("astroos_active_chart_id") : null;
    const target =
      (activeId ? myChartsData?.charts?.find((c) => c.id === activeId) : null) ??
      myChartsData?.charts?.find((c) => c.is_default) ??
      myChartsData?.charts?.[0];

    const req: WorkflowAnalysisRequest = target
      ? {
          birth_datetime_utc: target.birth_datetime_utc,
          latitude: target.birth_latitude,
          longitude: target.birth_longitude,
          ayanamsa: target.ayanamsa as WorkflowAnalysisRequest["ayanamsa"],
          house_system: target.house_system as WorkflowAnalysisRequest["house_system"],
          dasha_system: "vimshottari",
          include_vargas: true,
          subject_name: target.subject_name,
          place_name: target.place_name,
          persist: false,
          chart_id: target.id,
        }
      : {
          birth_datetime_utc: "1995-01-01T12:00:00Z",
          latitude: 28.6139,
          longitude: 77.2090,
          ayanamsa: "lahiri",
          house_system: "P",
          dasha_system: "vimshottari",
          include_vargas: true,
          subject_name: "Default Sample Chart",
          place_name: "New Delhi, India",
          persist: false,
        };

    analyze.mutate(req, {
      onSuccess: (data) => setResult(data, req),
    });
  }, [result, myChartsData, loadingCharts, analyze, setResult]);

  if (!result || !request) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-8 text-center shadow-sm">
        {loadingCharts || analyze.isPending ? (
          <div className="space-y-2">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent mx-auto" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              Loading Birth Chart…
            </p>
          </div>
        ) : (
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              No Active Birth Chart
            </h2>
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
              Select an existing chart from your dashboard or calculate a new birth chart.
            </p>
            <div className="mt-4 flex items-center justify-center gap-2">
              <Link href="/dashboard" className="obsidian-btn-primary text-xs px-4 py-2">
                Go to Dashboard
              </Link>
              <Link href="/charts/history" className="obsidian-btn-secondary text-xs px-4 py-2">
                View Saved Charts
              </Link>
            </div>
          </div>
        )}
      </div>
    );
  }

  const { chart, dasha, vargas } = result;

  const currentVargaPlanets =
    selectedVarga === "D1"
      ? chart.planets
      : vargas?.charts[selectedVarga]?.planet_positions.map((p) => ({
          planet: p.planet,
          rashi: p.varga_rashi,
          house_number: p.varga_house_number,
          is_retrograde: p.is_retrograde,
          rashi_degree: p.varga_rashi_degree,
        })) ?? chart.planets;

  const currentAscendant =
    selectedVarga === "D1"
      ? { rashi: chart.ascendant.rashi, rashi_degree: chart.ascendant.rashi_degree }
      : vargas?.charts[selectedVarga]
        ? {
            rashi: vargas.charts[selectedVarga].ascendant.varga_rashi,
            rashi_degree: vargas.charts[selectedVarga].ascendant.varga_rashi_degree,
          }
        : { rashi: chart.ascendant.rashi, rashi_degree: chart.ascendant.rashi_degree };

  const currentDashaPeriod = findCurrentDasha(dasha?.mahadashas ?? [], new Date());

  const handleAddToDataset = () => {
    try {
      const stored = localStorage.getItem("astroos_research_dataset_charts");
      const list: string[] = stored ? JSON.parse(stored) : [];
      if (chartId && !list.includes(chartId)) {
        list.push(chartId);
        localStorage.setItem("astroos_research_dataset_charts", JSON.stringify(list));
      }
      setDatasetAdded(true);
    } catch {
      setDatasetAdded(true);
    }
  };

  return (
    <div className="space-y-3">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800 text-cyan-600 dark:text-cyan-400"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="m12 3 2.6 6.2L21 10l-5 4.3L17.4 21 12 17.5 6.6 21 8 14.3 3 10l6.4-.8L12 3Z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                {request.subject_name} Birth Chart
              </h1>
              <span className="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                {selectedVarga}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Born {formatDate(request.birth_datetime_utc)}
              {request.place_name ? `, ${request.place_name}` : ""} · Ayanamsa: {request.ayanamsa}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center shrink-0 gap-1.5">
          <button
            type="button"
            onClick={handleAddToDataset}
            className="obsidian-btn-secondary text-xs flex items-center gap-1.5 py-1 px-2.5"
            title="Add to AstroOS Global Research Dataset"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            <span>{datasetAdded ? "Added!" : "+ Dataset"}</span>
          </button>
          <Link href="/charts" className="obsidian-btn-secondary text-xs py-1 px-2.5">
            Full Workspace
          </Link>
          <ShareButton />
        </div>
      </div>

      {/* Main 3-Column Dense Above-the-Fold Grid */}
      <div className="grid grid-cols-12 gap-3 items-stretch">
        {/* Column 1: Chart Canvas Pane (col-span-12 lg:col-span-4) */}
        <div className="col-span-12 lg:col-span-4 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3 shadow-sm flex flex-col justify-between">
          <div>
            {/* Top Toolbar: Style Switcher + Varga Selector */}
            <div className="mb-2 flex flex-col gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center justify-between gap-1.5">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  {selectedVarga} {VARGA_DIVISORS[selectedVarga]?.label ? `· ${VARGA_DIVISORS[selectedVarga].label}` : ""}
                </span>
                {/* [North | South] Style Toggle */}
                <div className="flex items-center rounded-lg p-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={() => setChartStyle("north")}
                    className={`px-2 py-0.5 text-[11px] font-semibold rounded transition ${
                      chartStyle === "north"
                        ? "bg-cyan-500 text-white shadow-sm"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                    }`}
                    aria-pressed={chartStyle === "north"}
                  >
                    North
                  </button>
                  <button
                    type="button"
                    onClick={() => setChartStyle("south")}
                    className={`px-2 py-0.5 text-[11px] font-semibold rounded transition ${
                      chartStyle === "south"
                        ? "bg-cyan-500 text-white shadow-sm"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                    }`}
                    aria-pressed={chartStyle === "south"}
                  >
                    South
                  </button>
                </div>
              </div>

              {/* Full Set Varga Selector (D1 through D60) */}
              <DivisionalChartSelector
                selectedVarga={selectedVarga}
                onSelectVarga={setSelectedVarga}
                availableVargas={["D1", ...Object.keys(vargas?.charts ?? {})]}
              />
            </div>

            {/* SVG Chart Canvas (max-h-[340px]) */}
            <div className="py-1 flex items-center justify-center min-h-[300px] max-h-[340px] overflow-hidden">
              {chartStyle === "south" ? (
                <SouthIndianChart
                  title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
                  ascendant={currentAscendant}
                  planets={currentVargaPlanets}
                  size={330}
                  isVarga={selectedVarga !== "D1"}
                  vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                  activePlanet={activePlanet}
                  activeHouse={activeHouse}
                  onPlanetClick={setActivePlanet}
                  onHouseClick={setActiveHouse}
                />
              ) : (
                <NorthIndianChart
                  title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
                  ascendant={currentAscendant}
                  planets={currentVargaPlanets}
                  aspects={chart.aspects}
                  size={330}
                  isVarga={selectedVarga !== "D1"}
                  vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                  activePlanet={activePlanet}
                  activeHouse={activeHouse}
                  onPlanetClick={setActivePlanet}
                  onHouseClick={setActiveHouse}
                />
              )}
            </div>
          </div>

          <div className="mt-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 px-2.5 py-1.5 flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-900 dark:text-slate-100">
              Lagna: <span className="text-cyan-600 dark:text-cyan-400">{currentAscendant.rashi}</span> {currentAscendant.rashi_degree?.toFixed(2)}°
            </span>
            <span className="text-slate-600 dark:text-slate-400 text-[11px]">
              {chart.ascendant.nakshatra} ({chart.ascendant.pada})
            </span>
          </div>
        </div>

        {/* Column 2: Planetary & Cusps Table (col-span-12 lg:col-span-5) */}
        <div className="col-span-12 lg:col-span-5 flex flex-col">
          <ChartPanel
            chart={chart}
            result={result}
            activePlanet={activePlanet}
            onPlanetClick={setActivePlanet}
          />
        </div>

        {/* Column 3: Active Influence & Transit Snapshot (col-span-12 lg:col-span-3) */}
        <div className="col-span-12 lg:col-span-3 flex flex-col">
          <DashaTransitSummaryCard result={result} request={request} />
        </div>
      </div>

      {/* Chart KPI Scorecards */}
      <div className="pt-2">
        <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-400">
          Chart KPI Scorecards
        </h3>
        <KpiScorecards result={result} />
      </div>

      {/* Dasha Timeline Section */}
      <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
            Vimshottari Dasha Timeline
          </h2>
          <Link href="/charts?view=dasha" className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline">
            View Full Explorer →
          </Link>
        </div>
        <DashaTimeline
          dasha={dasha}
          height={110}
          birthDate={request.birth_datetime_utc}
          activeDasha={currentDashaPeriod}
          events={chartEventsData?.events}
        />
      </div>

      {/* Life Events Tree Section */}
      {chartId && (
        <div className="pt-1">
          <LifeEventsTree chartId={chartId} />
        </div>
      )}
    </div>
  );
}
