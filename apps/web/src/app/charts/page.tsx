"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { PlanetDetailPanel } from "@/components/charts/PlanetDetailPanel";
import { PlanetStrengthHeatmap } from "@/components/charts/PlanetStrengthHeatmap";
import { PlanetStrengthRadar } from "@/components/charts/PlanetStrengthRadar";
import { PlanetRelationshipGraph } from "@/components/charts/PlanetRelationshipGraph";
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
import { useWorkflowStore } from "@/lib/store";
import { VARGA_DIVISORS, rashiLordFromApiName } from "@/lib/astro";
import { currentDasha, currentTransitSummary } from "@/lib/kpiScoring";

type ViewMode =
  | "kundli"
  | "chart"
  | "nakshatra"
  | "dasha"
  | "strength"
  | "relationships"
  | "houses"
  | "timeline"
  | "predictions"
  | "kp";

const VALID_VIEWS: ViewMode[] = [
  "kundli", "chart", "nakshatra", "dasha", "strength", "relationships",
  "houses", "timeline", "predictions", "kp",
];

export default function ChartsPage() {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const searchParams = useSearchParams();
  const [view, setView] = useState<ViewMode>("chart");

  // Deep-link support — e.g. the sidebar's "Planet Relationship Graph"
  // link goes to /charts?view=relationships. Only runs on the initial
  // query value (not a two-way URL sync) so in-page tab clicks stay fast
  // client-only state, same as before.
  useEffect(() => {
    const requested = searchParams.get("view");
    if (requested && (VALID_VIEWS as string[]).includes(requested)) {
      setView(requested as ViewMode);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);
  const [selectedVarga, setSelectedVarga] = useState<string>("D1");
  const [activePlanet, setActivePlanet] = useState<string | null>(null);
  // Click "pins" a planet so its detail panel stays put while the mouse
  // moves away to scroll it — without this, mouseleave-driven hover alone
  // would clear the panel the instant the cursor left the chart, making it
  // impossible to ever scroll down and read the rest of the panel.
  const [pinnedPlanet, setPinnedPlanet] = useState<string | null>(null);

  const handlePlanetHover = (planet: string | null) => {
    if (pinnedPlanet) return; // a pinned selection wins over hover previews
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

  if (!result) {
    return (
      <AppShell sectionColor="--section-analysis">
        <div
          className="flex flex-col items-center justify-center gap-4 py-20"
          role="status"
        >
          <div
            className="glass-card flex flex-col items-center gap-4 p-8 text-center"
          >
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              aria-hidden="true"
              style={{ color: "var(--text-muted)" }}
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <h2
              className="text-lg font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              No Chart Data Available
            </h2>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Run an analysis on the Dashboard first to populate chart data.
            </p>
            <Link href="/dashboard" className="btn-primary">
              Go to Dashboard
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  const { chart, vargas, dasha } = result;

  // Every varga the backend actually computed for this chart (D1 plus
  // whichever of the 15 divisional charts came back in the response),
  // in the canonical D1→D60 order from VARGA_DIVISORS — previously this
  // was hardcoded to just D1/D9 even though the backend computes all 15.
  const vargaKeys = Object.keys(VARGA_DIVISORS).filter(
    (k) => k === "D1" || !!vargas?.charts[k],
  );

  // Build D1 planet placements from chart data
  const d1Planets = chart.planets.map((p) => ({
    planet: p.planet,
    rashi: p.rashi,
    house_number: p.house_number,
    is_retrograde: p.is_retrograde,
    rashi_degree: p.rashi_degree,
  }));

  // Build Varga chart placements (D9 and others)
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
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Chart Visualization
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            D1 Rashi and divisional charts rendered as North Indian diamond charts.
            {request && (
              <>
                {" "}
                Subject: <span className="font-medium">{request.subject_name}</span>
                {" "}· Ayanamsa: {request.ayanamsa}
              </>
            )}
          </p>
        </div>
        <Link
          href="/charts/compare"
          className="btn-ghost text-xs px-3 py-1.5"
          aria-label="Compare charts side by side"
        >
          Compare D1 + D9
        </Link>
      </div>

      {/* View tabs */}
      <div
        className="mb-6 flex gap-1 border-b pb-2"
        style={{ borderColor: "var(--border-primary)" }}
        role="tablist"
        aria-label="Chart view options"
      >
        {([
          { key: "kundli" as ViewMode, label: "Interactive Kundli" },
          { key: "chart" as ViewMode, label: "Chart View" },
          { key: "nakshatra" as ViewMode, label: "Nakshatra / Pada" },
          { key: "dasha" as ViewMode, label: "Dasha Timeline" },
          { key: "strength" as ViewMode, label: "Strength" },
          { key: "relationships" as ViewMode, label: "Relationships" },
          { key: "houses" as ViewMode, label: "House Network" },
          { key: "timeline" as ViewMode, label: "Timeline" },
          { key: "predictions" as ViewMode, label: "Prediction Chains" },
          { key: "kp" as ViewMode, label: "KP Significators" },
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
              backgroundColor:
                view === tab.key ? "var(--accent)" : "transparent",
              color:
                view === tab.key
                  ? "var(--accent-text)"
                  : "var(--text-secondary)",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Interactive Kundli Panel — the standalone hover/click explorer
          (chart + planet/house/aspect tabs in one widget), plus a toolbar
          and a bottom row summarizing dasha/transit/status/notifications
          at a glance. */}
      {view === "kundli" && (
        <div id="panel-kundli" role="tabpanel" aria-label="Interactive Kundli panel" className="space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/dashboard" className="btn-ghost text-xs px-3 py-1.5">
              Edit Chart
            </Link>
            <Link href="/dashboard" className="btn-ghost text-xs px-3 py-1.5">
              New Chart
            </Link>
            <Link href="/charts/history" className="btn-ghost text-xs px-3 py-1.5 ml-auto">
              View All
            </Link>
          </div>

          <div className="glass-card h-[600px] overflow-hidden p-0">
            <InteractiveKundliView chart={chart} />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <button
              type="button"
              onClick={() => setView("dasha")}
              className="glass-card p-4 text-left transition hover:opacity-90"
            >
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                Dasha Timeline
              </h4>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                {currentDasha(result)}
              </p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                Currently active period · view full timeline
              </p>
            </button>

            <button
              type="button"
              onClick={() => setView("timeline")}
              className="glass-card p-4 text-left transition hover:opacity-90"
            >
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                Transit Timeline
              </h4>
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                {currentTransitSummary(result)}
              </p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                Today's transits from natal Moon
              </p>
            </button>

            <div className="glass-card p-4">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                Status
              </h4>
              <dl className="space-y-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Ayanamsa</dt>
                  <dd>{chart.ayanamsa_system}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>House System</dt>
                  <dd>{chart.house_system}</dd>
                </div>
                {result.verification && (
                  <div className="flex justify-between">
                    <dt style={{ color: "var(--text-muted)" }}>Verification Confidence</dt>
                    <dd>{(result.verification.confidence_score * 100).toFixed(0)}%</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* AI Notifications — no backend notification/alert feed exists yet
                (there's no push/poll endpoint for chart-triggered alerts), so
                this is an explicit placeholder rather than fabricated content. */}
            <div className="glass-card p-4">
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                AI Notifications
              </h4>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                No notifications yet — proactive AI alerts are a planned feature.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Chart View Panel — 4-column workspace (mockup layout): a narrow
          left sidebar (chart details + quick view + varga selector), the
          chart itself, the full planetary-positions/house-cusps tables, and
          a right-hand planet insights panel, all visible together on wide
          screens instead of stacked cards. Collapses to a single column on
          small screens. */}
      {view === "chart" && (
        <div
          id="panel-chart"
          role="tabpanel"
          aria-label="Chart visualization panel"
          className="grid grid-cols-1 gap-5 xl:grid-cols-[260px_1fr_1.1fr_320px] xl:items-start"
        >
          {/* Column 1: Chart Details + Quick View + Varga selector */}
          <div className="space-y-4">
            <div className="glass-card p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                Chart Details
              </h3>
              <dl className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                {request && (
                  <div className="flex justify-between">
                    <dt style={{ color: "var(--text-muted)" }}>Name</dt>
                    <dd style={{ color: "var(--text-primary)" }}>{request.subject_name}</dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Ayanamsa</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{chart.ayanamsa_system}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>House System</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{chart.house_system}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Lagna</dt>
                  <dd style={{ color: "var(--text-primary)" }}>
                    {chart.ascendant.rashi} {chart.ascendant.rashi_degree.toFixed(2)}°
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Lagna Lord</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{rashiLordFromApiName(chart.ascendant.rashi) ?? "—"}</dd>
                </div>
              </dl>
            </div>

            <div className="glass-card p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                Quick View
              </h3>
              <dl className="space-y-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Sun Sign</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{chart.planets.find((p) => p.planet === "Sun")?.rashi ?? "—"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Moon Sign</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{chart.planets.find((p) => p.planet === "Moon")?.rashi ?? "—"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Nakshatra (Moon)</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{chart.panchanga.nakshatra.nakshatra}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Tithi</dt>
                  <dd style={{ color: "var(--text-primary)" }}>
                    {chart.panchanga.tithi.name} ({chart.panchanga.tithi.paksha})
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Yoga</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{chart.panchanga.yoga.name}</dd>
                </div>
                <div className="flex justify-between">
                  <dt style={{ color: "var(--text-muted)" }}>Karana</dt>
                  <dd style={{ color: "var(--text-primary)" }}>{chart.panchanga.karana.name}</dd>
                </div>
              </dl>
            </div>

            <div className="glass-card p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
                Divisional Chart
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {vargaKeys.map((vk) => {
                  const vd = VARGA_DIVISORS[vk];
                  return (
                    <button
                      key={vk}
                      type="button"
                      onClick={() => setSelectedVarga(vk)}
                      className="rounded-full px-2.5 py-1 text-xs font-semibold transition"
                      style={{
                        backgroundColor:
                          selectedVarga === vk
                            ? "var(--accent)"
                            : "var(--bg-card)",
                        color:
                          selectedVarga === vk
                            ? "var(--accent-text)"
                            : "var(--text-secondary)",
                        border: `1px solid ${
                          selectedVarga === vk ? "var(--accent)" : "var(--border-primary)"
                        }`,
                      }}
                      aria-pressed={selectedVarga === vk}
                      aria-label={`Show ${vd?.label ?? vk} chart`}
                    >
                      {vd?.label ?? vk}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Column 2: the chart itself */}
          <div className="glass-card flex flex-col items-center p-6">
            <NorthIndianChart
              title={`${selectedVarga} — ${
                VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"
              }`}
              ascendant={currentAscendant}
              planets={currentVargaPlanets}
              size={380}
              isVarga={selectedVarga !== "D1"}
              vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
              activePlanet={activePlanet}
              onPlanetHover={handlePlanetHover}
              onPlanetClick={handlePlanetClick}
            />
            {/* Ascendant summary */}
            <div
              className="mt-4 w-full rounded-lg border p-3"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-card)",
              }}
            >
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Ascendant
              </p>
              <p
                className="font-semibold"
                style={{ color: "var(--accent)" }}
              >
                {currentAscendant.rashi}{" "}
                <span
                  className="font-normal"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {currentAscendant.rashi_degree?.toFixed(2)}°
                </span>
              </p>
              <p
                className="mt-1 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                Lord:{" "}
                {rashiLordFromApiName(currentAscendant.rashi) ?? "—"}
              </p>
            </div>
          </div>

          {/* Column 3: full planetary positions + house cusps tables (same
              real data the Dashboard's post-analysis results view uses via
              ChartPanel — reused rather than duplicated). */}
          <div className="min-w-0">
            <ChartPanel chart={chart} />
          </div>

          {/* Column 4: interactive planet insights panel — replaces the old
              static table. Hover or click any planet in the chart (or its
              legend) to populate this. */}
          <div className="xl:sticky xl:top-20">
            <PlanetDetailPanel
              planet={activePlanet}
              result={result}
              pinned={pinnedPlanet === activePlanet && activePlanet !== null}
              onUnpin={() => {
                setPinnedPlanet(null);
                setActivePlanet(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Nakshatra Panel */}
      {view === "nakshatra" && (
        <div
          id="panel-nakshatra"
          role="tabpanel"
          aria-label="Nakshatra and Pada lookup panel"
        >
          <NakshatraPadaSelector planets={chart.planets} />
        </div>
      )}

      {/* Dasha Panel */}
      {view === "dasha" && (
        <div
          id="panel-dasha"
          role="tabpanel"
          aria-label="Dasha timeline visualization panel"
        >
          <DashaTimeline dasha={dasha} />
        </div>
      )}

      {/* Strength Panel */}
      {view === "strength" && (
        <div
          id="panel-strength"
          role="tabpanel"
          aria-label="Planet strength visualization panel"
          className="grid grid-cols-1 gap-6 lg:grid-cols-2"
        >
          <PlanetStrengthHeatmap shadbala={result.shadbala} />
          <PlanetStrengthRadar strengths={chart.planet_strengths} shadbala={result.shadbala} />
          <IshtaKashtaBalaPanel request={request} />
          <AvasthaPanel request={request} />
        </div>
      )}

      {/* Relationships Panel — the component itself now lays out its own
          left (info+filters) / center (graph) / right (top pairs+detail)
          columns, so this wrapper just needs full width, no centering. */}
      {view === "relationships" && (
        <div
          id="panel-relationships"
          role="tabpanel"
          aria-label="Planet relationship graph panel"
        >
          <PlanetRelationshipGraph
            planets={chart.planets}
            aspects={chart.aspects}
            yogas={result.yogas.results}
            mahadashas={dasha.mahadashas}
            result={result}
          />
        </div>
      )}

      {/* House Dependency Network Panel */}
      {view === "houses" && (
        <div
          id="panel-houses"
          role="tabpanel"
          aria-label="House dependency network panel"
          className="flex justify-center"
        >
          <HouseDependencyNetwork
            houses={chart.houses}
            planetStrengths={chart.planet_strengths}
            planets={chart.planets}
          />
        </div>
      )}

      {/* Timeline Panel */}
      {view === "timeline" && (
        <div
          id="panel-timeline"
          role="tabpanel"
          aria-label="Dasha and transit timeline panel"
          className="space-y-6"
        >
          <TransitTimeline dasha={dasha} transits={result.transits} />
          <LifeEventTimeline chartId={result.chart_id} />
        </div>
      )}

      {/* Prediction Chains Panel */}
      {view === "predictions" && (
        <div
          id="panel-predictions"
          role="tabpanel"
          aria-label="Prediction chain explorer panel"
          className="flex justify-center"
        >
          <PredictionChainExplorer result={result} />
        </div>
      )}

      {/* KP Significators Panel */}
      {view === "kp" && (
        <div
          id="panel-kp"
          role="tabpanel"
          aria-label="KP significator explorer panel"
          className="flex justify-center"
        >
          <KPSignificatorExplorer result={result} />
        </div>
      )}
    </AppShell>
  );
}
