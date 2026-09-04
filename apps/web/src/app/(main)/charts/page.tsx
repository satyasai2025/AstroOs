"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";
import { PlanetDetailPanel } from "@/components/charts/PlanetDetailPanel";
import PlanetRelationshipGraph2 from "@/components/charts/PlanetRelationshipGraph2";
import { StrengthAnalysisCenter } from "@/components/charts/StrengthAnalysisCenter";
import { HouseDependencyNetwork, type EdgeKind } from "@/components/charts/HouseDependencyNetwork";
import { TransitTimeline, getCurrentPeriodChain } from "@/components/charts/TransitTimeline";
import { LifeEventTimeline } from "@/components/charts/LifeEventTimeline";
import { VedhaAnalysisPanel } from "@/components/charts/VedhaAnalysisPanel";
import { PredictionChainExplorer } from "@/components/charts/PredictionChainExplorer";
import { KPAnalysisCenter } from "@/components/kp/KPAnalysisCenter";
import { NakshatraPadaSelector } from "@/components/charts/NakshatraPadaSelector";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { DashaSystemSwitcher } from "@/components/charts/DashaSystemSwitcher";
import { DashaOverviewCard } from "@/components/charts/DashaOverviewCard";
import { DashaTreeExplorer } from "@/components/charts/DashaTreeExplorer";
import { DashaExportPanel } from "@/components/charts/DashaExportPanel";
import { ChartPanel } from "@/components/workflow/panels/ChartPanel";
import { DashaTransitSummaryCard } from "@/components/charts/DashaTransitSummaryCard";
import { DivisionalChartSelector } from "@/components/charts/DivisionalChartSelector";
import InteractiveKundliView from "@/components/charts/InteractiveKundliView";
import { YogaIntelligenceDashboard } from "@/components/charts/YogaIntelligenceDashboard";
import AshtakavargaPanel from "@/components/charts/AshtakavargaPanel";
import JaiminiPanel from "@/components/charts/JaiminiPanel";
import PlanetExplorerPanel from "@/components/charts/PlanetExplorerPanel";
import VargaExplorer from "@/components/charts/VargaExplorer";
import { SBCChakraGrid } from "@/components/charts/SBCChakraGrid";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import type { WorkflowAnalysisRequest } from "@/lib/types";
import { normalizeAyanamsa, normalizeHouseSystem } from "@/lib/types";
import { VARGA_DIVISORS, rashiLordFromApiName, RASHIS, RASHI_LORDS } from "@/lib/astro";
import { currentDasha, currentTransitSummary } from "@/lib/kpiScoring";

export const dynamic = "force-dynamic";

type HousesMode = "standard" | "advanced";

const ALL_EDGE_KINDS: EdgeKind[] = [
  "lordship", "aspect", "parivartana", "argala",
  "trinal", "angular", "dusthana", "functional", "maraka",
];

const HOUSE_EDGE_FILTERS: { key: EdgeKind | "all"; label: string }[] = [
  { key: "all",          label: "All" },
  { key: "lordship",     label: "Lordship" },
  { key: "aspect",       label: "Aspects" },
  { key: "parivartana",  label: "Parivartana" },
  { key: "argala",       label: "Argala" },
  { key: "trinal",       label: "Trinal 1·5·9" },
  { key: "angular",      label: "Angular 1·4·7·10" },
  { key: "dusthana",     label: "Dusthana 6·8·12" },
  { key: "maraka",       label: "Maraka" },
];

type ViewMode =
  | "kundli"
  | "chart"
  | "nakshatra"
  | "dasha"
  | "strength"
  | "relationships-v2"
  | "houses"
  | "timeline"
  | "predictions"
  | "kp"
  | "yogas"
  | "ashtakavarga"
  | "jaimini"
  | "planets"
  | "divisional"
  | "sbc";

const VALID_VIEWS: ViewMode[] = [
  "kundli",
  "chart",
  "nakshatra",
  "dasha",
  "strength",
  "relationships-v2",
  "houses",
  "timeline",
  "predictions",
  "kp",
  "yogas",
  "ashtakavarga",
  "jaimini",
  "planets",
  "divisional",
  "sbc"
];

type DashaSubView = "dashboard" | "timeline" | "tree" | "analysis" | "events" | "reports";

const DASHA_SUBVIEWS: { key: DashaSubView; label: string }[] = [
  { key: "dashboard", label: "Dashboard" },
  { key: "timeline", label: "Timeline" },
  { key: "tree", label: "Tree" },
  { key: "analysis", label: "Analysis" },
  { key: "events", label: "Event Timing" },
  { key: "reports", label: "Reports" },
];

const DASHA_SUBVIEW_HELP: Record<DashaSubView, string> = {
  dashboard:
    "Quick summary: which system is active, the trigger planet/sign, total cycle length, and the current period chain (Mahadasha → Antardasha → ...) as of today.",
  timeline:
    "Interactive D3 timeline of every period from Mahadasha down to the deepest computed level. Scroll/pinch to zoom, drag to pan, click a period for details. Orange hatching marks Dasha Sandhi (junction) windows.",
  tree:
    "Full period hierarchy as an expandable tree, plus a proportional Mahadasha bar strip. Click any period (in either view) to see its exact lord, level, start/end dates and duration.",
  analysis:
    "Dasha ↔ transit correlation: shows Vedha and Vipreet Vedha (obstruction/relief) between the currently-active dasha lords and today's transiting planets, plus Nakshatra Vedha via the Sarvatobhadra Chakra.",
  events:
    "A chronological log of real, recorded life events for this chart (career, relationship, travel, etc.) — the research ledger you compare against the Dashboard/Analysis tabs to check whether the dasha framework's classical significations lined up with what actually happened. Events are not auto-correlated to periods yet; add and review them via the Events API.",
  reports:
    "Exports the currently-displayed dasha tree as a CSV (one row per period, opens directly in Excel/Sheets) — a raw data snapshot, not a formatted narrative report.",
};

function ChartsPageContent() {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);
  const searchParams = useSearchParams();
  const [view, setView] = useState<ViewMode>("chart");
  const [dashaSubView, setDashaSubView] = useState<DashaSubView>("timeline");
  const [housesMode, setHousesMode] = useState<HousesMode>("standard");
  const [activeKinds, setActiveKinds] = useState<Set<EdgeKind>>(new Set(ALL_EDGE_KINDS));

  const router = useRouter();

  useEffect(() => {
    const requested = searchParams.get("view");
    if (requested === "planets") {
      router.replace("/charts/planets");
      return;
    }
    if (requested === "dasha") {
      router.replace("/charts/dasha");
      return;
    }
    if (requested && (VALID_VIEWS as string[]).includes(requested)) {
      setView(requested as ViewMode);
    }
    const requestedMode = searchParams.get("mode");
    if (requestedMode === "advanced" || requestedMode === "standard") {
      setHousesMode(requestedMode);
    }
  }, [searchParams, router]);

  const [selectedVarga, setSelectedVarga] = useState<string>("D1");
  const [activePlanet, setActivePlanet] = useState<string | null>(null);
  const [pinnedPlanet, setPinnedPlanet] = useState<string | null>(null);
  const [zoomModalOpen, setZoomModalOpen] = useState(false);
  const setResult = useWorkflowStore((s) => s.setResult);
  const chartStyle = useWorkflowStore((s) => s.chartStyle);
  const setChartStyle = useWorkflowStore((s) => s.setChartStyle);

  const handlePlanetHover = (planet: string | null) => {
    if (pinnedPlanet) return;
    setActivePlanet(planet);
  };

  const handlePlanetClick = (planet: string) => {
    if (pinnedPlanet === planet) {
      setPinnedPlanet(null);
      setActivePlanet(null);
    } else {
      setPinnedPlanet(planet);
      setActivePlanet(planet);
    }
  };

  // When no chart is loaded in the workflow store (fresh reload, or a
  // direct link like /charts?view=houses), load the user's default saved
  // chart in place — same pattern as /predictions — so the requested
  // `?view=` is preserved instead of being dropped by a redirect to the
  // separate /charts/[chartId] detail page.
  const { data: chartsData, isLoading: chartsLoading, isError: chartsError, refetch: refetchCharts } = useMyCharts();
  const analyze = useAnalyzeWorkflow();
  const [autoRecomputeStarted, setAutoRecomputeStarted] = useState(false);
  const [loadTimedOut, setLoadTimedOut] = useState(false);

  const DEFAULT_DEMO_CHART_REQUEST: WorkflowAnalysisRequest = {
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

  const targetSummary = chartsData
    ? (chartsData.charts.find((c) => c.is_default) ?? chartsData.charts[0] ?? null)
    : null;

  useEffect(() => {
    if (result || autoRecomputeStarted || chartsLoading) return;
    setAutoRecomputeStarted(true);
    setLoadTimedOut(false);

    const timeoutTimer = setTimeout(() => {
      setLoadTimedOut(true);
    }, 15000);

    const req: WorkflowAnalysisRequest = targetSummary
      ? {
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
        }
      : DEFAULT_DEMO_CHART_REQUEST;

    analyze.mutate(req, {
      onSuccess: (data) => {
        clearTimeout(timeoutTimer);
        setResult(data, req);
      },
      onError: () => {
        clearTimeout(timeoutTimer);
      },
    });

    return () => clearTimeout(timeoutTimer);
  }, [result, autoRecomputeStarted, targetSummary, chartsLoading]);

  if (!result) {
    const isFetching = (chartsLoading || analyze.isPending) && !loadTimedOut;
    const hasError = analyze.isError || chartsError || loadTimedOut;
    const noChartSelected = !chartsLoading && !targetSummary;

    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20" role="status">
        <div className="glass-card flex flex-col items-center gap-4 p-8 text-center max-w-md">
          {isFetching ? (
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Loading chart data…</p>
            </div>
          ) : hasError ? (
            <>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-rose-500">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Chart Loading Error</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                An error occurred while calculating chart and yoga data.
              </p>
              <button
                type="button"
                onClick={() => {
                  setAutoRecomputeStarted(false);
                  setLoadTimedOut(false);
                  analyze.reset();
                  if (targetSummary) {
                    const req: WorkflowAnalysisRequest = {
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
                    analyze.mutate(req, { onSuccess: (data) => setResult(data, req) });
                  } else {
                    refetchCharts();
                  }
                }}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition"
              >
                Retry
              </button>
            </>
          ) : noChartSelected ? (
            <>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-amber-500">
                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">No Chart Selected</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                No Chart Selected. Please click &apos;+ Create / Select Chart&apos; to view Yogas and predictions.
              </p>
              <button
                type="button"
                onClick={() => openCreateModal("birth_chart")}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition cursor-pointer shadow-sm"
              >
                + Create / Select Chart
              </button>
            </>
          ) : (
            <>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-400">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">No Chart Data Available</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">Create a birth chart or select an existing one to populate calculations.</p>
              <button
                type="button"
                onClick={() => openCreateModal("birth_chart")}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition cursor-pointer shadow-sm"
              >
                + Create / Select Chart
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  const { chart, vargas, dasha } = result;
  const vargaKeys = Object.keys(VARGA_DIVISORS).filter(
    (k) => k === "D1" || !!vargas?.charts[k],
  );

  const d1Planets = chart.planets.map((p) => ({
    planet: p.planet,
    rashi: p.rashi,
    house_number: p.house_number,
    is_retrograde: p.is_retrograde,
    rashi_degree: p.rashi_degree,
  }));

  const getVargaPlanets = (vargaKey: string) => {
    if (!vargas?.charts[vargaKey]) return null;
    const vc = vargas.charts[vargaKey];
    return vc.planet_positions.map((p) => ({
      planet: p.planet,
      rashi: p.varga_rashi,
      house_number: p.varga_house_number,
      is_retrograde: p.is_retrograde,
      rashi_degree: p.varga_rashi_degree,
    }));
  };

  const currentVargaPlanets =
    selectedVarga === "D1"
      ? d1Planets
      : getVargaPlanets(selectedVarga) ?? d1Planets;

  const currentAscendant =
    selectedVarga === "D1"
      ? { rashi: chart.ascendant.rashi, rashi_degree: chart.ascendant.rashi_degree }
      : vargas?.charts[selectedVarga]
        ? {
            rashi: vargas.charts[selectedVarga].ascendant.varga_rashi,
            rashi_degree: vargas.charts[selectedVarga].ascendant.varga_rashi_degree,
          }
        : { rashi: chart.ascendant.rashi, rashi_degree: chart.ascendant.rashi_degree };

  return (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Chart Visualization</h1>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            D1 Rashi &amp; divisional varga charts.
            {request && (<><span> Native: <span className="font-semibold text-slate-800 dark:text-slate-200">{request.subject_name}</span> · Ayanamsa: {request.ayanamsa}</span></>)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => openCreateModal("birth_chart")}
            className="btn-ghost text-xs px-2.5 py-1 cursor-pointer"
            aria-label="Select or create another chart"
          >
            + New / Select Chart
          </button>
          <Link href="/charts/compare" className="btn-ghost text-xs px-2.5 py-1" aria-label="Compare charts side by side">
            Compare D1 + D9
          </Link>
        </div>
      </div>

      <div className="mb-3 flex gap-1 border-b border-slate-200 dark:border-slate-800 pb-1.5 overflow-x-auto" role="tablist" aria-label="Chart view options">
        {([
          { key: "kundli" as ViewMode, label: "Interactive Kundli" },
          { key: "chart" as ViewMode, label: "Chart View" },
          { key: "nakshatra" as ViewMode, label: "Nakshatra / Pada" },
          { key: "dasha" as ViewMode, label: "Dasha Timeline" },
          { key: "strength" as ViewMode, label: "Strength" },
          { key: "relationships-v2" as ViewMode, label: "Relationships" },
          { key: "houses" as ViewMode, label: "House Network" },
          { key: "timeline" as ViewMode, label: "Timeline" },
          { key: "predictions" as ViewMode, label: "Prediction Chains" },
          { key: "kp" as ViewMode, label: "KP Analysis" },
          { key: "yogas" as ViewMode, label: "Yogas" },
          { key: "ashtakavarga" as ViewMode, label: "Ashtakavarga" },
          { key: "jaimini" as ViewMode, label: "Jaimini" },
          { key: "planets" as ViewMode, label: "Planet Explorer" },
          { key: "divisional" as ViewMode, label: "Divisional" },
        ] as const).map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={view === tab.key}
            aria-controls={`panel-${tab.key}`}
            onClick={() => setView(tab.key)}
            className={`rounded-lg px-2.5 py-1 text-xs font-semibold whitespace-nowrap transition ${
              view === tab.key
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {view === "kundli" && (
        <div id="panel-kundli" role="tabpanel" aria-label="Interactive Kundli panel" className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => openCreateModal("birth_chart")}
              className="btn-ghost text-xs px-2.5 py-1 cursor-pointer"
            >
              Edit Chart
            </button>
            <button
              type="button"
              onClick={() => openCreateModal("birth_chart")}
              className="btn-ghost text-xs px-2.5 py-1 cursor-pointer font-bold text-cyan-600 dark:text-cyan-400"
            >
              + New Chart
            </button>
            <Link href="/charts/history" className="btn-ghost text-xs px-2.5 py-1 ml-auto">View All</Link>
          </div>
          <div className="glass-card h-[540px] overflow-hidden p-0"><InteractiveKundliView chart={chart} vargas={vargas} shadbala={result.shadbala} request={request} /></div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <button type="button" onClick={() => setView("dasha")} className="glass-card p-3 text-left transition hover:opacity-90">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-cyan-600 dark:text-cyan-400">Dasha Timeline</h4>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{currentDasha(result)}</p>
              <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">Currently active period</p>
            </button>
            <button type="button" onClick={() => setView("timeline")} className="glass-card p-3 text-left transition hover:opacity-90">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-cyan-600 dark:text-cyan-400">Transit Timeline</h4>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{currentTransitSummary(result)}</p>
              <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">Transits from natal Moon</p>
            </button>
            <div className="glass-card p-3">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-cyan-600 dark:text-cyan-400">Status</h4>
              <dl className="space-y-0.5 text-[11px] text-slate-600 dark:text-slate-400">
                <div className="flex justify-between"><dt>Ayanamsa</dt><dd className="font-semibold text-slate-800 dark:text-slate-200">{chart.ayanamsa_system}</dd></div>
                <div className="flex justify-between"><dt>House System</dt><dd className="font-semibold text-slate-800 dark:text-slate-200">{chart.house_system}</dd></div>
              </dl>
            </div>
            <div className="glass-card p-3">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-cyan-600 dark:text-cyan-400">AI Alerts</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">No critical planetary alerts detected.</p>
            </div>
          </div>
        </div>
      )}

      {view === "chart" && (
        <div id="panel-chart" role="tabpanel" aria-label="Chart visualization panel" className="space-y-3">
          {/* Main 3-Column Dense Above-the-Fold Grid */}
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-12 items-stretch">
            {/* Left Column (lg:col-span-4): Chart Canvas & Style/Varga Switcher */}
            <div className="lg:col-span-4 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3 shadow-sm flex flex-col justify-between">
              {/* Single Clean Toolbar Above Chart */}
              <div className="flex items-center justify-between gap-2 pb-2 border-b border-slate-100 dark:border-slate-800 font-mono">
                <DivisionalChartSelector
                  selectedVarga={selectedVarga}
                  onSelectVarga={setSelectedVarga}
                  availableVargas={vargaKeys}
                />

                <div className="flex items-center gap-1.5 shrink-0">
                  <div className="flex items-center rounded-md p-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
                    <button
                      type="button"
                      onClick={() => setChartStyle("north")}
                      className={`px-2 py-0.5 font-bold rounded transition cursor-pointer ${
                        chartStyle === "north"
                          ? "bg-cyan-500 text-white shadow-sm"
                          : "text-slate-600 dark:text-slate-400"
                      }`}
                    >
                      North
                    </button>
                    <button
                      type="button"
                      onClick={() => setChartStyle("south")}
                      className={`px-2 py-0.5 font-bold rounded transition cursor-pointer ${
                        chartStyle === "south"
                          ? "bg-cyan-500 text-white shadow-sm"
                          : "text-slate-600 dark:text-slate-400"
                      }`}
                    >
                      South
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => setZoomModalOpen(true)}
                    className="p-1 rounded-md bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-cyan-600 dark:text-cyan-400 hover:border-cyan-500 transition cursor-pointer"
                    title="Zoom Chart"
                    aria-label="Zoom Chart"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8"></circle>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                      <line x1="11" y1="8" x2="11" y2="14"></line>
                      <line x1="8" y1="11" x2="14" y2="11"></line>
                    </svg>
                  </button>
                </div>
              </div>

              {/* Compact SVG Chart Canvas (Click to Zoom) */}
              <div
                onClick={() => setZoomModalOpen(true)}
                className="py-2 flex items-center justify-center cursor-pointer"
                title="Click chart to zoom"
              >
                {chartStyle === "south" ? (
                  <SouthIndianChart
                    ascendant={currentAscendant}
                    planets={currentVargaPlanets}
                    size={330}
                    isVarga={selectedVarga !== "D1"}
                    vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                    activePlanet={activePlanet}
                    onPlanetHover={handlePlanetHover}
                    onPlanetClick={handlePlanetClick}
                  />
                ) : (
                  <NorthIndianChart
                    ascendant={currentAscendant}
                    planets={currentVargaPlanets}
                    size={330}
                    showFullNames={false}
                    isVarga={selectedVarga !== "D1"}
                    vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                    activePlanet={activePlanet}
                    onPlanetHover={handlePlanetHover}
                    onPlanetClick={handlePlanetClick}
                  />
                )}
              </div>

              {/* Bottom Lagna Summary */}
              <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 px-2.5 py-1.5 flex items-center justify-between text-xs font-mono">
                <span className="font-semibold text-slate-900 dark:text-slate-100">
                  Lagna: <span className="text-cyan-600 dark:text-cyan-400">{currentAscendant.rashi}</span> {currentAscendant.rashi_degree?.toFixed(2)}°
                </span>
                <span className="text-slate-600 dark:text-slate-400 text-[11px]">
                  Lord: {rashiLordFromApiName(currentAscendant.rashi) ?? "—"}
                </span>
              </div>

              {/* 🪐 Grahas / Planet Names Below Chart */}
              <div className="mt-2.5 pt-2 border-t border-slate-200 dark:border-slate-800 font-mono">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-[11px]">
                  {currentVargaPlanets.map((p) => {
                    const isAct = activePlanet === p.planet;
                    return (
                      <button
                        key={p.planet}
                        type="button"
                        onClick={() => handlePlanetClick(p.planet)}
                        className={`px-2 py-1 rounded-md border text-left flex items-center justify-between transition cursor-pointer ${
                          isAct
                            ? "bg-cyan-500/20 border-cyan-500 text-cyan-400 font-bold"
                            : "bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-300 hover:border-cyan-400"
                        }`}
                        title={`${p.planet} in ${p.rashi} ${p.rashi_degree?.toFixed(2)}° ${p.is_retrograde ? '(Retrograde)' : ''}`}
                      >
                        <span className="truncate flex items-center gap-1 font-semibold">
                          <span>{p.planet.slice(0, 3)}</span>
                          {p.is_retrograde && <span className="text-amber-500 text-[9px] font-bold">(R)</span>}
                        </span>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400">
                          {p.rashi.slice(0, 3)} {p.rashi_degree?.toFixed(0)}°
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Middle Column (lg:col-span-5): High-Density Tabbed Sub-Panels */}
            <div className="lg:col-span-5 flex flex-col">
              <ChartPanel
                chart={chart}
                result={result}
                activePlanet={activePlanet}
                onPlanetClick={handlePlanetClick}
              />
            </div>

            {/* Right Column (lg:col-span-3): Dasha & Transit Summary */}
            <div className="lg:col-span-3 flex flex-col">
              <DashaTransitSummaryCard result={result} request={request} />
            </div>
          </div>

          {/* 🔍 Zoom & Comprehensive Shastric Details Modal */}
          {zoomModalOpen && (
            <div
              className="fixed inset-0 z-[200] bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6"
              onClick={() => setZoomModalOpen(false)}
            >
              <div
                className="relative w-full max-w-6xl max-h-[94vh] overflow-y-auto bg-white dark:bg-[#070e1c] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-5 sm:p-7 text-slate-900 dark:text-white"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Modal Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
                  <div>
                    <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-mono text-xs font-bold uppercase">
                      <span>{selectedVarga} — {VARGA_DIVISORS[selectedVarga]?.label || "Rashi Chart"}</span>
                      <span className="text-slate-400">·</span>
                      <span className="text-slate-500">High-Resolution Precision View</span>
                    </div>
                    <h3 className="text-xl font-extrabold text-slate-900 dark:text-white mt-0.5">
                      {request?.subject_name ? `${request.subject_name}'s Kundli` : "Kundli Precision Studio"}
                    </h3>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex items-center rounded-lg p-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-xs">
                      <button
                        type="button"
                        onClick={() => setChartStyle("north")}
                        className={`px-3 py-1 font-bold rounded-md transition cursor-pointer ${
                          chartStyle === "north" ? "bg-cyan-500 text-white shadow-sm" : "text-slate-600 dark:text-slate-400"
                        }`}
                      >
                        North Indian
                      </button>
                      <button
                        type="button"
                        onClick={() => setChartStyle("south")}
                        className={`px-3 py-1 font-bold rounded-md transition cursor-pointer ${
                          chartStyle === "south" ? "bg-cyan-500 text-white shadow-sm" : "text-slate-600 dark:text-slate-400"
                        }`}
                      >
                        South Indian
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={() => setZoomModalOpen(false)}
                      className="h-8 w-8 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-rose-100 dark:hover:bg-rose-950/50 text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 flex items-center justify-center font-bold text-sm transition cursor-pointer border border-slate-300 dark:border-slate-700"
                      aria-label="Close modal"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Modal Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-5">
                  {/* Left Column: Big Enlarge Chart */}
                  <div className="lg:col-span-6 flex flex-col items-center justify-center bg-slate-50/50 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800/80 rounded-2xl p-4 shadow-inner min-h-[500px]">
                    {chartStyle === "south" ? (
                      <SouthIndianChart
                        ascendant={currentAscendant}
                        planets={currentVargaPlanets}
                        size={480}
                        isVarga={selectedVarga !== "D1"}
                        vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                        activePlanet={activePlanet}
                        onPlanetHover={handlePlanetHover}
                        onPlanetClick={handlePlanetClick}
                      />
                    ) : (
                      <NorthIndianChart
                        ascendant={currentAscendant}
                        planets={currentVargaPlanets}
                        size={480}
                        showFullNames={false}
                        isVarga={selectedVarga !== "D1"}
                        vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                        activePlanet={activePlanet}
                        onPlanetHover={handlePlanetHover}
                        onPlanetClick={handlePlanetClick}
                      />
                    )}
                  </div>

                  {/* Right Column: Special Points (AL, UL, Gulika, Mandi) & Comprehensive Longitude Table */}
                  <div className="lg:col-span-6 space-y-4 font-mono text-xs">
                    {/* Special Shastric Lagnas & Upagrahas Card */}
                    <div className="p-4 rounded-xl border border-cyan-900/40 bg-cyan-950/20 space-y-2.5">
                      <div className="text-cyan-400 font-bold uppercase tracking-wider text-[11px] flex items-center justify-between">
                        <span>Special Shastric Lagnas &amp; Upagraha Coordinates</span>
                        <span className="text-[10px] text-cyan-300 font-normal">Siddhantic Reference</span>
                      </div>

                      {(() => {
                        const lagnaIdx = RASHIS.indexOf(chart.ascendant.rashi as any);
                        const lagnaLord = rashiLordFromApiName(chart.ascendant.rashi) || "Mars";
                        const lagnaLordPl = chart.planets.find((p) => p.planet === lagnaLord);
                        const lordIdx = lagnaLordPl ? RASHIS.indexOf(lagnaLordPl.rashi as any) : lagnaIdx;
                        const distAL = (lordIdx - lagnaIdx + 12) % 12;
                        const alRashi = RASHIS[(lordIdx + distAL) % 12] || chart.ascendant.rashi;

                        const h7Idx = (lagnaIdx + 6) % 12;
                        const h7Rashi = RASHIS[h7Idx];
                        const h7Lord = rashiLordFromApiName(h7Rashi) || "Venus";
                        const h7LordPl = chart.planets.find((p) => p.planet === h7Lord);
                        const h7LordIdx = h7LordPl ? RASHIS.indexOf(h7LordPl.rashi as any) : h7Idx;
                        const distUL = (h7LordIdx - h7Idx + 12) % 12;
                        const ulRashi = RASHIS[(h7LordIdx + distUL) % 12] || "Sagittarius";

                        const saturn = chart.planets.find((p) => p.planet === "Saturn");
                        const saturnIdx = saturn ? RASHIS.indexOf(saturn.rashi as any) : 9;
                        const gulikaRashi = RASHIS[(saturnIdx + 2) % 12] || "Aquarius";
                        const mandiRashi = RASHIS[(saturnIdx + 1) % 12] || "Capricorn";

                        return (
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                            <div className="p-2 rounded-lg bg-slate-900/80 border border-cyan-800/40">
                              <span className="text-[10px] text-cyan-400 font-bold block">AL (Arudha)</span>
                              <span className="font-bold text-white text-xs">{alRashi}</span>
                            </div>
                            <div className="p-2 rounded-lg bg-slate-900/80 border border-cyan-800/40">
                              <span className="text-[10px] text-cyan-400 font-bold block">UL (Upapada)</span>
                              <span className="font-bold text-white text-xs">{ulRashi}</span>
                            </div>
                            <div className="p-2 rounded-lg bg-slate-900/80 border border-amber-800/40">
                              <span className="text-[10px] text-amber-400 font-bold block">Gulika (Gk)</span>
                              <span className="font-bold text-white text-xs">{gulikaRashi}</span>
                            </div>
                            <div className="p-2 rounded-lg bg-slate-900/80 border border-amber-800/40">
                              <span className="text-[10px] text-amber-400 font-bold block">Mandi (Md)</span>
                              <span className="font-bold text-white text-xs">{mandiRashi}</span>
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    {/* Detailed Planetary Positions Table */}
                    <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                      <div className="p-2.5 bg-slate-100 dark:bg-slate-800/60 font-bold text-slate-700 dark:text-slate-300 text-[11px] flex justify-between">
                        <span>GRAHA POSITIONS &amp; DIGNITIES</span>
                        <span className="text-cyan-500">{chart.planets.length} Bodies</span>
                      </div>
                      <div className="max-h-[260px] overflow-y-auto">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 dark:text-slate-400 text-[10px] uppercase border-b border-slate-200 dark:border-slate-800">
                            <tr>
                              <th className="py-1.5 px-3">Planet</th>
                              <th className="py-1.5 px-2">Rashi</th>
                              <th className="py-1.5 px-2">Longitude</th>
                              <th className="py-1.5 px-2">Nakshatra</th>
                              <th className="py-1.5 px-2">Dignity</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                            {/* Ascendant Row */}
                            <tr className="bg-cyan-50/30 dark:bg-cyan-950/20 font-semibold">
                              <td className="py-1.5 px-3 text-cyan-600 dark:text-cyan-400">Ascendant (Lagna)</td>
                              <td className="py-1.5 px-2">{currentAscendant.rashi}</td>
                              <td className="py-1.5 px-2 font-bold">{currentAscendant.rashi_degree?.toFixed(2)}°</td>
                              <td className="py-1.5 px-2 text-slate-500">—</td>
                              <td className="py-1.5 px-2 text-slate-500">—</td>
                            </tr>
                            {chart.planets.map((p) => (
                              <tr key={p.planet} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                                <td className="py-1.5 px-3 font-semibold flex items-center gap-1.5">
                                  <span>{p.planet}</span>
                                  {p.is_retrograde && <span className="text-amber-500 text-[10px] font-bold">(R)</span>}
                                </td>
                                <td className="py-1.5 px-2">{p.rashi}</td>
                                <td className="py-1.5 px-2 font-bold">{p.rashi_degree?.toFixed(2)}°</td>
                                <td className="py-1.5 px-2 text-slate-600 dark:text-slate-400">
                                  {p.nakshatra} (P{p.pada})
                                </td>
                                <td className="py-1.5 px-2">
                                  <span className="capitalize text-[10px] font-semibold text-cyan-600 dark:text-cyan-400">
                                    {p.dignity || "Neutral"}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {view === "nakshatra" && (
        <div id="panel-nakshatra" role="tabpanel" aria-label="Nakshatra and Pada lookup panel"><NakshatraPadaSelector planets={chart.planets} /></div>
      )}

      {view === "dasha" && (
        <div id="panel-dasha" role="tabpanel" aria-label="Dasha analysis panel">
          <DashaSystemSwitcher
            current={dasha.system}
            birthParams={
              request
                ? {
                    birth_datetime_utc: request.birth_datetime_utc,
                    latitude: request.latitude,
                    longitude: request.longitude,
                    ayanamsa: request.ayanamsa,
                    house_system: request.house_system,
                  }
                : undefined
            }
            onChange={(nextDasha) => setResult({ ...result, dasha: nextDasha }, request!)}
          />

          <div
            className="mb-3 flex flex-wrap gap-1 border-b pb-2"
            style={{ borderColor: "var(--border-primary)" }}
            role="tablist"
            aria-label="Dasha sub-panel tabs"
          >
            {DASHA_SUBVIEWS.map((sv) => (
              <button
                key={sv.key}
                type="button"
                role="tab"
                aria-selected={dashaSubView === sv.key}
                onClick={() => setDashaSubView(sv.key)}
                className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
                style={{
                  backgroundColor: dashaSubView === sv.key ? "var(--accent)" : "transparent",
                  color: dashaSubView === sv.key ? "var(--accent-text)" : "var(--text-secondary)",
                }}
              >
                {sv.label}
              </button>
            ))}
          </div>

          <p
            className="mb-3 text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            {DASHA_SUBVIEW_HELP[dashaSubView]}
          </p>

          {dashaSubView === "dashboard" && <DashaOverviewCard dasha={dasha} />}
          {dashaSubView === "timeline" && <DashaTimeline dasha={dasha} />}
          {dashaSubView === "tree" && <DashaTreeExplorer dasha={dasha} />}
          {dashaSubView === "analysis" && (
            <VedhaAnalysisPanel transits={result.transits} dashaChain={getCurrentPeriodChain(dasha.mahadashas)} />
          )}
          {dashaSubView === "events" && <LifeEventTimeline chartId={result.chart_id} />}
          {dashaSubView === "reports" && <DashaExportPanel dasha={dasha} />}
        </div>
      )}

      {view === "strength" && (
        <div id="panel-strength" role="tabpanel" aria-label="Strength Analysis Center">
          <StrengthAnalysisCenter
            strengths={chart.planet_strengths}
            shadbala={result.shadbala}
            request={request}
            activePlanet={activePlanet}
            pinnedPlanet={pinnedPlanet}
            onPlanetHover={handlePlanetHover}
            onPlanetClick={handlePlanetClick}
          />
        </div>
      )}

      {view === "relationships-v2" && (
        <div id="panel-relationships-v2" role="tabpanel" aria-label="Planet relationship graph panel">
          <PlanetRelationshipGraph2 planets={chart.planets} aspects={chart.aspects} yogas={result.yogas.results} mahadashas={dasha.mahadashas} result={result} />
        </div>
      )}

      {view === "houses" && (
        <div id="panel-houses" role="tabpanel" aria-label="House dependency network panel" className="space-y-4">

          {/* ── Mode sub-tabs ───────────────────────────────────────── */}
          <div
            className="flex gap-1 border-b pb-2"
            style={{ borderColor: "var(--border-primary)" }}
            role="tablist"
            aria-label="House view mode"
          >
            {(["standard", "advanced"] as HousesMode[]).map((m) => (
              <button
                key={m}
                type="button"
                role="tab"
                aria-selected={housesMode === m}
                onClick={() => setHousesMode(m)}
                className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
                style={{
                  backgroundColor: housesMode === m ? "var(--accent)" : "transparent",
                  color: housesMode === m ? "var(--accent-text)" : "var(--text-secondary)",
                }}
              >
                {m === "standard" ? "Standard" : "Advanced · Edge Filters"}
              </button>
            ))}
          </div>

          {/* ── Edge-kind filter chips (advanced mode only) ─────────── */}
          {housesMode === "advanced" && (
            <div className="flex flex-wrap items-center gap-2">
              {HOUSE_EDGE_FILTERS.map((filter) => {
                const isAll = filter.key === "all";
                const isActive = isAll
                  ? activeKinds.size === ALL_EDGE_KINDS.length
                  : activeKinds.has(filter.key as EdgeKind);
                return (
                  <button
                    key={filter.key}
                    type="button"
                    onClick={() => {
                      if (isAll) {
                        setActiveKinds(
                          isActive ? new Set() : new Set(ALL_EDGE_KINDS),
                        );
                      } else {
                        setActiveKinds((prev) => {
                          const next = new Set(prev);
                          if (next.has(filter.key as EdgeKind)) next.delete(filter.key as EdgeKind);
                          else next.add(filter.key as EdgeKind);
                          return next;
                        });
                      }
                    }}
                    className="rounded-lg border px-3 py-1.5 text-xs font-medium transition-all"
                    style={{
                      backgroundColor: isActive ? "var(--cyan-glow-soft)" : "transparent",
                      borderColor: isActive ? "var(--cyan-400)" : "var(--border-primary)",
                      color: isActive ? "var(--cyan-400)" : "var(--text-secondary)",
                    }}
                  >
                    {filter.label}
                  </button>
                );
              })}
            </div>
          )}

          {/* ── Network — live workflow store data in both modes ─────── */}
          <div className="flex justify-center">
            <HouseDependencyNetwork
              houses={chart.houses}
              planetStrengths={chart.planet_strengths}
              planets={chart.planets}
              activeKinds={housesMode === "advanced" ? activeKinds : undefined}
              onFilterChange={housesMode === "advanced" ? setActiveKinds : undefined}
            />
          </div>
        </div>
      )}

      {view === "timeline" && (
        <div id="panel-timeline" role="tabpanel" aria-label="Dasha and transit timeline panel" className="space-y-6">
          <TransitTimeline dasha={dasha} transits={result.transits} />
          <LifeEventTimeline chartId={result.chart_id} />
        </div>
      )}

      {view === "predictions" && (
        <div id="panel-predictions" role="tabpanel" aria-label="Prediction chain explorer panel" className="flex justify-center">
          <PredictionChainExplorer result={result} />
        </div>
      )}

      {view === "kp" && (
        <div id="panel-kp" role="tabpanel" aria-label="KP analysis panel" className="flex justify-center">
          <KPAnalysisCenter request={request} result={result} />
        </div>
      )}

      {view === "yogas" && (
        <div id="panel-yogas" role="tabpanel" aria-label="Yogas and combinations panel" className="h-[calc(100vh-200px)]">
          <YogaIntelligenceDashboard result={result} request={request} />
        </div>
      )}

      {view === "ashtakavarga" && (
        <div id="panel-ashtakavarga" role="tabpanel" aria-label="Ashtakavarga panel"><AshtakavargaPanel result={result} /></div>
      )}

      {view === "jaimini" && (
        <div id="panel-jaimini" role="tabpanel" aria-label="Jaimini analysis panel">
          <JaiminiPanel
            result={result}
            request={
              request
                ? {
                    birth_datetime_utc: request.birth_datetime_utc,
                    latitude: request.latitude,
                    longitude: request.longitude,
                    ayanamsa: request.ayanamsa,
                    house_system: request.house_system,
                  }
                : null
            }
          />
        </div>
      )}

      {view === "planets" && (
        <div id="panel-planets" role="tabpanel" aria-label="Planet explorer panel"><PlanetExplorerPanel result={result} request={request} selectedPlanet={pinnedPlanet ?? activePlanet} onSelectPlanet={(p) => { setPinnedPlanet(p); setActivePlanet(p); }} /></div>
      )}

      {view === "divisional" && (
        <div id="panel-divisional" role="tabpanel" aria-label="Divisional charts panel"><VargaExplorer chart={chart} vargas={vargas} transits={result.transits} selectedVarga={selectedVarga} setSelectedVarga={setSelectedVarga} /></div>
      )}

      {view === "sbc" && (
        <div id="panel-sbc" role="tabpanel" aria-label="Sarvatobhadra Chakra panel" className="space-y-6">
          <div className="rounded-2xl border p-4 sm:p-6 shadow-xl backdrop-blur-sm" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
            <SBCChakraGrid />
          </div>
        </div>
      )}
    </>
  );
}

export default function ChartsPage() {
  return (
    <Suspense fallback={null}>
      <ChartsPageContent />
    </Suspense>
  );
}