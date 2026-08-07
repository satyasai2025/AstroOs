"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { PlanetDetailPanel } from "@/components/charts/PlanetDetailPanel";
import { PlanetRelationshipGraph } from "@/components/charts/PlanetRelationshipGraph";
import PlanetRelationshipGraph2 from "@/components/charts/PlanetRelationshipGraph2";
import { PlanetStrengthHeatmap } from "@/components/charts/PlanetStrengthHeatmap";
import { PlanetStrengthRadar } from "@/components/charts/PlanetStrengthRadar";
import { HouseDependencyNetwork } from "@/components/charts/HouseDependencyNetwork";
import { TransitTimeline } from "@/components/charts/TransitTimeline";
import { LifeEventTimeline } from "@/components/charts/LifeEventTimeline";
import { PredictionChainExplorer } from "@/components/charts/PredictionChainExplorer";
import { KPSignificatorExplorer } from "@/components/charts/KPSignificatorExplorer";
import { IshtaKashtaBalaPanel } from "@/components/charts/IshtaKashtaBalaPanel";
import { AvasthaPanel } from "@/components/charts/AvasthaPanel";
import { NakshatraPadaSelector } from "@/components/charts/NakshatraPadaSelector";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { ChartPanel } from "@/components/workflow/panels/ChartPanel";
import InteractiveKundliView from "@/components/charts/InteractiveKundliView";
import YogasPanel from "@/components/charts/YogasPanel";
import AshtakavargaPanel from "@/components/charts/AshtakavargaPanel";
import JaiminiPanel from "@/components/charts/JaiminiPanel";
import PlanetExplorerPanel from "@/components/charts/PlanetExplorerPanel";
import DivisionalChartsPanel from "@/components/charts/DivisionalChartsPanel";
import { useWorkflowStore } from "@/lib/store";
import { useMyCharts } from "@/lib/charts";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { VARGA_DIVISORS, rashiLordFromApiName } from "@/lib/astro";
import { currentDasha, currentTransitSummary } from "@/lib/kpiScoring";
import type { WorkflowAnalysisRequest } from "@/lib/types";

type ViewMode =
  | "kundli"
  | "chart"
  | "nakshatra"
  | "dasha"
  | "strength"
  | "relationships"
  | "relationships-v2"
  | "houses"
  | "timeline"
  | "predictions"
  | "kp"
  | "yogas"
  | "ashtakavarga"
  | "jaimini"
  | "planets"
  | "divisional";

const VALID_VIEWS: ViewMode[] = [
  "kundli",
  "chart",
  "nakshatra",
  "dasha",
  "strength",
  "relationships",
  "relationships-v2",
  "houses",
  "timeline",
  "predictions",
  "kp",
  "yogas",
  "ashtakavarga",
  "jaimini",
  "planets",
  "divisional"
];

export default function ChartsPage() {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const searchParams = useSearchParams();
  const [view, setView] = useState<ViewMode>("chart");

  useEffect(() => {
    const requested = searchParams.get("view");
    if (requested && (VALID_VIEWS as string[]).includes(requested)) {
      setView(requested as ViewMode);
    }
  }, [searchParams]);

  const [selectedVarga, setSelectedVarga] = useState<string>("D1");
  const [activePlanet, setActivePlanet] = useState<string | null>(null);
  const [pinnedPlanet, setPinnedPlanet] = useState<string | null>(null);
  const setResult = useWorkflowStore((s) => s.setResult);

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
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const analyze = useAnalyzeWorkflow();
  const [autoRecomputeStarted, setAutoRecomputeStarted] = useState(false);

  const targetSummary = chartsData
    ? (chartsData.charts.find((c) => c.is_default) ?? chartsData.charts[0] ?? null)
    : null;

  useEffect(() => {
    if (result || autoRecomputeStarted || !targetSummary) return;
    setAutoRecomputeStarted(true);
    const req: WorkflowAnalysisRequest = {
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
    analyze.mutate(req, { onSuccess: (data) => setResult(data, req) });
    // Fire once per targetSummary — analyze/setResult are stable references.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result, autoRecomputeStarted, targetSummary]);

  if (!result) {
    return (
      <AppShell sectionColor="--section-analysis">
        <div className="flex flex-col items-center justify-center gap-4 py-20" role="status">
          <div className="glass-card flex flex-col items-center gap-4 p-8 text-center">
            {chartsLoading || analyze.isPending ? (
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Loading chart data…</p>
            ) : (
              <>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" style={{ color: "var(--text-muted)" }}>
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>No Chart Data Available</h2>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Run an analysis on the Dashboard first to populate chart data.</p>
            <Link href="/dashboard" className="btn-primary">Go to Dashboard</Link>
              </>
            )}
          </div>
        </div>
      </AppShell>
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
    <AppShell sectionColor="--section-analysis">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>Chart Visualization</h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            D1 Rashi and divisional charts rendered as North Indian diamond charts.
            {request && (<><span> Subject: <span className="font-medium">{request.subject_name}</span> {" "}· Ayanamsa: {request.ayanamsa}</span></>)}
          </p>
        </div>
        <Link href="/charts/compare" className="btn-ghost text-xs px-3 py-1.5" aria-label="Compare charts side by side">Compare D1 + D9</Link>
      </div>

      <div className="mb-6 flex gap-1 border-b pb-2" style={{ borderColor: "var(--border-primary)" }} role="tablist" aria-label="Chart view options">
        {([
          { key: "kundli" as ViewMode, label: "Interactive Kundli" },
          { key: "chart" as ViewMode, label: "Chart View" },
          { key: "nakshatra" as ViewMode, label: "Nakshatra / Pada" },
          { key: "dasha" as ViewMode, label: "Dasha Timeline" },
          { key: "strength" as ViewMode, label: "Strength" },
          { key: "relationships" as ViewMode, label: "Relationships" },
          { key: "relationships-v2" as ViewMode, label: "Relationships v2" },
          { key: "houses" as ViewMode, label: "House Network" },
          { key: "timeline" as ViewMode, label: "Timeline" },
          { key: "predictions" as ViewMode, label: "Prediction Chains" },
          { key: "kp" as ViewMode, label: "KP Significators" },
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
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
            style={{
              backgroundColor: view === tab.key ? "var(--accent)" : "transparent",
              color: view === tab.key ? "var(--accent-text)" : "var(--text-secondary)",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {view === "kundli" && (
        <div id="panel-kundli" role="tabpanel" aria-label="Interactive Kundli panel" className="space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/dashboard" className="btn-ghost text-xs px-3 py-1.5">Edit Chart</Link>
            <Link href="/dashboard" className="btn-ghost text-xs px-3 py-1.5">New Chart</Link>
            <Link href="/charts/history" className="btn-ghost text-xs px-3 py-1.5 ml-auto">View All</Link>
          </div>
          <div className="glass-card h-[600px] overflow-hidden p-0"><InteractiveKundliView chart={chart} vargas={vargas} shadbala={result.shadbala} request={request} /></div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <button type="button" onClick={() => setView("dasha")} className="glass-card p-4 text-left transition hover:opacity-90">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Dasha Timeline</h4>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>{currentDasha(result)}</p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Currently active period · view full timeline</p>
            </button>
            <button type="button" onClick={() => setView("timeline")} className="glass-card p-4 text-left transition hover:opacity-90">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Transit Timeline</h4>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>{currentTransitSummary(result)}</p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Today's transits from natal Moon</p>
            </button>
            <div className="glass-card p-4">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Status</h4>
              <dl className="space-y-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Ayanamsa</dt><dd>{chart.ayanamsa_system}</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>House System</dt><dd>{chart.house_system}</dd></div>
                {result.verification && (<div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Verification Confidence</dt><dd>{(result.verification.confidence_score * 100).toFixed(0)}%</dd></div>)}
              </dl>
            </div>
            <div className="glass-card p-4">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>AI Notifications</h4>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No notifications yet — proactive AI alerts are a planned feature.</p>
            </div>
          </div>
        </div>
      )}

      {view === "chart" && (
        <div id="panel-chart" role="tabpanel" aria-label="Chart visualization panel" className="grid grid-cols-1 gap-5 xl:grid-cols-[260px_1fr_1.1fr_320px] xl:items-start">
          <div className="space-y-4">
            <div className="glass-card p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Chart Details</h3>
              <dl className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                {request && (<div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Name</dt><dd style={{ color: "var(--text-primary)" }}>{request.subject_name}</dd></div>)}
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Ayanamsa</dt><dd style={{ color: "var(--text-primary)" }}>{chart.ayanamsa_system}</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>House System</dt><dd style={{ color: "var(--text-primary)" }}>{chart.house_system}</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Lagna</dt><dd style={{ color: "var(--text-primary)" }}>{chart.ascendant.rashi} {chart.ascendant.rashi_degree.toFixed(2)}°</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Lagna Lord</dt><dd style={{ color: "var(--text-primary)" }}>{rashiLordFromApiName(chart.ascendant.rashi) ?? "—"}</dd></div>
              </dl>
            </div>
            <div className="glass-card p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Quick View</h3>
              <dl className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Sun Sign</dt><dd style={{ color: "var(--text-primary)" }}>{chart.planets.find((p) => p.planet === "Sun")?.rashi ?? "—"}</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Moon Sign</dt><dd style={{ color: "var(--text-primary)" }}>{chart.planets.find((p) => p.planet === "Moon")?.rashi ?? "—"}</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Nakshatra (Moon)</dt><dd style={{ color: "var(--text-primary)" }}>{chart.panchanga.nakshatra.nakshatra}</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Tithi</dt><dd style={{ color: "var(--text-primary)" }}>{chart.panchanga.tithi.name} ({chart.panchanga.tithi.paksha})</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Yoga</dt><dd style={{ color: "var(--text-primary)" }}>{chart.panchanga.yoga.name}</dd></div>
                <div className="flex justify-between"><dt style={{ color: "var(--text-muted)" }}>Karana</dt><dd style={{ color: "var(--text-primary)" }}>{chart.panchanga.karana.name}</dd></div>
              </dl>
            </div>
            <div className="glass-card p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Divisional Chart</h3>
              <div className="flex flex-wrap gap-1.5">
                {vargaKeys.map((vk) => {
                  const vd = VARGA_DIVISORS[vk];
                  return (
                    <button key={vk} type="button" onClick={() => setSelectedVarga(vk)} className="rounded-full px-2.5 py-1 text-xs font-semibold transition" style={{ backgroundColor: selectedVarga === vk ? "var(--accent)" : "var(--bg-card)", color: selectedVarga === vk ? "var(--accent-text)" : "var(--text-secondary)", border: `1px solid ${selectedVarga === vk ? "var(--accent)" : "var(--border-primary)"}` }} aria-pressed={selectedVarga === vk} aria-label={`Show ${vd?.label ?? vk} chart`}>
                      {vd?.label ?? vk}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          <div className="glass-card flex flex-col items-center p-6">
            <NorthIndianChart
              title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
              ascendant={currentAscendant}
              planets={currentVargaPlanets}
              size={380}
              isVarga={selectedVarga !== "D1"}
              vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
              activePlanet={activePlanet}
              onPlanetHover={handlePlanetHover}
              onPlanetClick={handlePlanetClick}
            />
            <div className="mt-4 w-full rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Ascendant</p>
              <p className="font-semibold" style={{ color: "var(--accent)" }}>{currentAscendant.rashi} <span className="font-normal" style={{ color: "var(--text-secondary)" }}>{currentAscendant.rashi_degree?.toFixed(2)}°</span></p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Lord: {rashiLordFromApiName(currentAscendant.rashi) ?? "—"}</p>
            </div>
          </div>
          <div className="min-w-0"><ChartPanel chart={chart} /></div>
          <div className="xl:sticky xl:top-20">
            <PlanetDetailPanel planet={activePlanet} result={result} pinned={pinnedPlanet === activePlanet && activePlanet !== null} onUnpin={() => { setPinnedPlanet(null); setActivePlanet(null); }} />
          </div>
        </div>
      )}

      {view === "nakshatra" && (
        <div id="panel-nakshatra" role="tabpanel" aria-label="Nakshatra and Pada lookup panel"><NakshatraPadaSelector planets={chart.planets} /></div>
      )}

      {view === "dasha" && (
        <div id="panel-dasha" role="tabpanel" aria-label="Dasha timeline visualization panel"><DashaTimeline dasha={dasha} /></div>
      )}

      {view === "strength" && (
        <div id="panel-strength" role="tabpanel" aria-label="Planet strength visualization panel" className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <PlanetStrengthHeatmap shadbala={result.shadbala} />
          <PlanetStrengthRadar strengths={chart.planet_strengths} shadbala={result.shadbala} />
          <IshtaKashtaBalaPanel request={request} />
          <AvasthaPanel request={request} />
        </div>
      )}

      {view === "relationships" && (
        <div id="panel-relationships" role="tabpanel" aria-label="Planet relationship graph panel">
          <PlanetRelationshipGraph planets={chart.planets} aspects={chart.aspects} yogas={result.yogas.results} mahadashas={dasha.mahadashas} result={result} />
        </div>
      )}

      {view === "relationships-v2" && (
        <div id="panel-relationships-v2" role="tabpanel" aria-label="Planet relationship graph v2 panel">
          <PlanetRelationshipGraph2 planets={chart.planets} aspects={chart.aspects} mahadashas={dasha.mahadashas} result={result} />
        </div>
      )}

      {view === "houses" && (
        <div id="panel-houses" role="tabpanel" aria-label="House dependency network panel" className="flex justify-center">
          <HouseDependencyNetwork houses={chart.houses} planetStrengths={chart.planet_strengths} planets={chart.planets} />
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
        <div id="panel-kp" role="tabpanel" aria-label="KP significator explorer panel" className="flex justify-center">
          <KPSignificatorExplorer result={result} />
        </div>
      )}

      {view === "yogas" && (
        <div id="panel-yogas" role="tabpanel" aria-label="Yogas and combinations panel"><YogasPanel result={result} /></div>
      )}

      {view === "ashtakavarga" && (
        <div id="panel-ashtakavarga" role="tabpanel" aria-label="Ashtakavarga panel"><AshtakavargaPanel result={result} /></div>
      )}

      {view === "jaimini" && (
        <div id="panel-jaimini" role="tabpanel" aria-label="Jaimini analysis panel"><JaiminiPanel result={result} /></div>
      )}

      {view === "planets" && (
        <div id="panel-planets" role="tabpanel" aria-label="Planet explorer panel"><PlanetExplorerPanel chart={chart} activePlanet={activePlanet} /></div>
      )}

      {view === "divisional" && (
        <div id="panel-divisional" role="tabpanel" aria-label="Divisional charts panel"><DivisionalChartsPanel chart={chart} vargas={vargas} selectedVarga={selectedVarga} setSelectedVarga={setSelectedVarga} /></div>
      )}
    </AppShell>
  );
}