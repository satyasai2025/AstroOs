"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { PLANETS, PLANET_SYMBOLS, PLANET_ABBREV, rashiLordFromApiName } from "@/lib/astro";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts, useActiveChart } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { ActiveChartSelectorModal } from "@/components/layout/ActiveChartSelectorModal";
import type { WorkflowAnalysisRequest } from "@/lib/types";
import { resolvePlanetContext } from "@/components/charts/planetExplorer/context";
import { OverviewTab } from "@/components/charts/planetExplorer/OverviewTab";
import { StructureTab } from "@/components/charts/planetExplorer/StructureTab";
import { StrengthTab } from "@/components/charts/planetExplorer/StrengthTab";
import { RelationshipsTab } from "@/components/charts/planetExplorer/RelationshipsTab";
import { YogasTab } from "@/components/charts/planetExplorer/YogasTab";
import { DashaTab } from "@/components/charts/planetExplorer/DashaTab";
import { TransitTab } from "@/components/charts/planetExplorer/TransitTab";
import { TimelineTab } from "@/components/charts/planetExplorer/TimelineTab";
import { InterpretationTab } from "@/components/charts/planetExplorer/InterpretationTab";
import { PlanetRightSidebar } from "@/components/charts/planetExplorer/PlanetRightSidebar";
import type { PlanetExplorerTab } from "@/components/charts/PlanetExplorerPanel";

export const dynamic = "force-dynamic";

const TABS: { key: PlanetExplorerTab; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "structure", label: "Structure" },
  { key: "strength", label: "Strength" },
  { key: "relationships", label: "Relationships" },
  { key: "yogas", label: "Yogas" },
  { key: "dasha", label: "Dasha" },
  { key: "transit", label: "Transit" },
  { key: "timeline", label: "Timeline" },
  { key: "interpretation", label: "Interpretation" },
];

function formatBirthDatetime(iso: string | undefined): string {
  if (!iso) return "15 Aug 1990, 10:30 AM IST";
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-US", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return iso;
  }
}

function PlanetExplorerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const setResult = useWorkflowStore((s) => s.setResult);
  const analyze = useAnalyzeWorkflow();
  const { data: myChartsData, isLoading: loadingCharts } = useMyCharts();
  const { activeSummary } = useActiveChart();

  const [selectorModalOpen, setSelectorModalOpen] = useState(false);
  const [selectedPlanet, setSelectedPlanet] = useState<string>("Mars");
  const [activeTab, setActiveTab] = useState<PlanetExplorerTab>("structure");
  const [autoLoadAttempted, setAutoLoadAttempted] = useState(false);

  // Sync tab & planet from query params if specified
  useEffect(() => {
    const queryPlanet = searchParams.get("planet");
    const queryTab = searchParams.get("tab") as PlanetExplorerTab | null;

    if (queryPlanet && (PLANETS as readonly string[]).includes(queryPlanet)) {
      setSelectedPlanet(queryPlanet);
    }
    if (queryTab && TABS.some((t) => t.key === queryTab)) {
      setActiveTab(queryTab);
    }
  }, [searchParams]);

  // Auto-load default or active chart if store is empty
  useEffect(() => {
    if (result || autoLoadAttempted || loadingCharts) return;
    setAutoLoadAttempted(true);

    const activeId = typeof window !== "undefined" ? localStorage.getItem("astroos_last_viewed_chart_id") : null;
    const target =
      (activeId ? myChartsData?.charts?.find((c) => c.id === activeId) : null) ??
      myChartsData?.charts?.find((c) => c.is_default) ??
      myChartsData?.charts?.[0];

    if (target) {
      const req: WorkflowAnalysisRequest = {
        birth_datetime_utc: target.birth_datetime_utc,
        latitude: target.birth_latitude,
        longitude: target.birth_longitude,
        ayanamsa: (target.ayanamsa as WorkflowAnalysisRequest["ayanamsa"]) || "lahiri",
        house_system: (target.house_system as WorkflowAnalysisRequest["house_system"]) || "placidus",
        dasha_system: "vimshottari",
        include_vargas: true,
        subject_name: target.subject_name,
        place_name: target.place_name,
        persist: false,
        chart_id: target.id,
      };
      analyze.mutate(req, {
        onSuccess: (data) => {
          setResult(data, req);
          // Set initial default planet to Lagna lord if available
          const lord = rashiLordFromApiName(data.chart.ascendant.rashi);
          if (lord && data.chart.planets.some((p) => p.planet === lord)) {
            setSelectedPlanet(lord);
          }
        },
      });
    }
  }, [result, autoLoadAttempted, loadingCharts, myChartsData, analyze, setResult]);

  // Default planet fallback when result loads
  useEffect(() => {
    if (result && !searchParams.get("planet")) {
      const lord = rashiLordFromApiName(result.chart.ascendant.rashi);
      if (lord && result.chart.planets.some((p) => p.planet === lord)) {
        // Keep Mars if already selected, or default to Mars/lord
        if (!selectedPlanet) setSelectedPlanet(lord);
      }
    }
  }, [result, searchParams, selectedPlanet]);

  // Unified derived context driven strictly by selectedPlanet + result
  const ctx = useMemo(() => {
    if (!result) return null;
    return resolvePlanetContext(selectedPlanet, result);
  }, [selectedPlanet, result]);

  const handleSelectPlanet = (planet: string) => {
    setSelectedPlanet(planet);
    const params = new URLSearchParams(searchParams.toString());
    params.set("planet", planet);
    router.replace(`/charts/planets?${params.toString()}`, { scroll: false });
  };

  const handleSelectTab = (tab: PlanetExplorerTab) => {
    setActiveTab(tab);
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`/charts/planets?${params.toString()}`, { scroll: false });
  };

  // Loading state
  if (!result && (loadingCharts || analyze.isPending)) {
    return (
      <div className="flex h-[65vh] flex-col items-center justify-center gap-3">
        <span className="h-7 w-7 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
        <p className="text-xs text-slate-400 font-medium">Computing planetary analysis…</p>
      </div>
    );
  }

  // No chart state
  if (!result) {
    return (
      <div className="rounded-2xl border p-12 text-center my-6 space-y-4 max-w-lg mx-auto" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto text-xl font-bold">
          🪐
        </div>
        <h2 className="text-base font-bold text-slate-100">No Active Chart Selected</h2>
        <p className="text-xs text-slate-400">
          Select or calculate a birth chart to view in-depth structural & functional planetary analysis.
        </p>
        <button
          type="button"
          onClick={() => setSelectorModalOpen(true)}
          className="rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 text-xs font-semibold shadow-md transition"
        >
          + Select Chart
        </button>
        {selectorModalOpen && (
          <ActiveChartSelectorModal isOpen={selectorModalOpen} onClose={() => setSelectorModalOpen(false)} />
        )}
      </div>
    );
  }

  const subjectName = request?.subject_name || activeSummary?.subject_name || "Meena Bhagia";
  const birthDatetime = formatBirthDatetime(request?.birth_datetime_utc || activeSummary?.birth_datetime_utc);
  const placeName = request?.place_name || activeSummary?.place_name || "New Delhi, India";

  return (
    <div className="space-y-4 pb-12">
      {/* ── 1. Top Header Bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-3 pt-1" style={{ borderColor: "var(--border-primary)" }}>
        <div>
          <h1 className="text-xl font-extrabold text-slate-100 flex items-center gap-2">
            <span>Planet Explorer</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            In-depth structural & functional analysis of planets in your chart
          </p>
        </div>

        {/* Chart Selector & Meta */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={() => setSelectorModalOpen(true)}
            className="flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition border hover:bg-slate-800/60"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <span>Chart: <span className="text-emerald-400">{subjectName}</span></span>
            <span className="text-slate-400 text-[10px]">▼</span>
          </button>

          <div className="hidden sm:flex flex-col text-right text-[11px] text-slate-400 leading-tight">
            <span>{birthDatetime}</span>
            <span className="text-slate-500">{placeName}</span>
          </div>

          <button
            type="button"
            onClick={() => setSelectorModalOpen(true)}
            className="rounded-xl px-3 py-1.5 text-xs font-bold transition border"
            style={{
              borderColor: "rgba(16, 185, 129, 0.4)",
              backgroundColor: "rgba(16, 185, 129, 0.12)",
              color: "#34d399",
            }}
          >
            Change Chart
          </button>
        </div>
      </div>

      {/* ── 2. Top 9-Graha Selector Bar ── */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1" role="tablist" aria-label="Select Planet">
        {PLANETS.map((planet) => {
          const isSelected = selectedPlanet === planet;
          const isPlaced = result.chart.planets.some((p) => p.planet === planet);
          return (
            <button
              key={planet}
              type="button"
              role="tab"
              aria-selected={isSelected}
              onClick={() => handleSelectPlanet(planet)}
              className="flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition flex-shrink-0"
              style={{
                backgroundColor: isSelected ? "rgba(16, 185, 129, 0.18)" : "var(--bg-card)",
                color: isSelected ? "#34d399" : isPlaced ? "var(--text-secondary)" : "var(--text-muted)",
                border: isSelected ? "1.5px solid #10b981" : "1px solid var(--border-primary)",
                boxShadow: isSelected ? "0 0 12px rgba(16, 185, 129, 0.2)" : "none",
                opacity: isPlaced ? 1 : 0.45,
              }}
            >
              <span className="text-sm font-bold">{PLANET_SYMBOLS[planet] ?? "☉"}</span>
              <span>{planet}</span>
            </button>
          );
        })}
      </div>

      {/* ── 3. Sub-Tabs Bar ── */}
      <div className="flex items-center gap-1 border-b pb-1 overflow-x-auto" style={{ borderColor: "var(--border-primary)" }}>
        {TABS.map((t) => {
          const isActive = activeTab === t.key;
          return (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => handleSelectTab(t.key)}
              className="relative px-3.5 py-1.5 text-xs font-semibold transition whitespace-nowrap"
              style={{
                color: isActive ? "#34d399" : "var(--text-secondary)",
              }}
            >
              <span>{t.label}</span>
              {isActive && (
                <span
                  className="absolute bottom-[-5px] left-0 right-0 h-0.5 rounded-full bg-emerald-400"
                  style={{ backgroundColor: "#10b981" }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* ── 4. Main 2-Column Responsive Layout ── */}
      {ctx && (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-12 items-start">
          {/* Left / Center Column (75%) */}
          <div className="lg:col-span-8 xl:col-span-8 min-w-0">
            {activeTab === "overview" && <OverviewTab ctx={ctx} />}
            {activeTab === "structure" && (
              <StructureTab
                ctx={ctx}
                result={result}
                onNavigateTab={(tab) => handleSelectTab(tab)}
              />
            )}
            {activeTab === "strength" && <StrengthTab ctx={ctx} result={result} />}
            {activeTab === "relationships" && <RelationshipsTab ctx={ctx} result={result} />}
            {activeTab === "yogas" && <YogasTab ctx={ctx} result={result} />}
            {activeTab === "dasha" && <DashaTab ctx={ctx} result={result} />}
            {activeTab === "transit" && <TransitTab ctx={ctx} result={result} />}
            {activeTab === "timeline" && <TimelineTab ctx={ctx} result={result} />}
            {activeTab === "interpretation" && (
              <InterpretationTab ctx={ctx} onFocusTab={(tab) => handleSelectTab(tab)} />
            )}
          </div>

          {/* Right Sidebar Column (25%) */}
          <div className="lg:col-span-4 xl:col-span-4 sticky top-16 space-y-4">
            <PlanetRightSidebar
              ctx={ctx}
              result={result}
              onNavigateTab={(tab) => handleSelectTab(tab)}
              onViewInChart={() => router.push(`/charts?view=kundli&planet=${selectedPlanet}`)}
            />
          </div>
        </div>
      )}

      {/* Chart Selector Modal */}
      {selectorModalOpen && (
        <ActiveChartSelectorModal
          isOpen={selectorModalOpen}
          onClose={() => setSelectorModalOpen(false)}
        />
      )}
    </div>
  );
}

export default function PlanetExplorerPage() {
  return (
    <Suspense fallback={null}>
      <PlanetExplorerContent />
    </Suspense>
  );
}
