"use client";

import { useState } from "react";
import Link from "next/link";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";
import { ChartDetailPanel } from "@/components/charts/ChartDetailPanel";
import { ChartPanel } from "@/components/workflow/panels/ChartPanel";
import { DashaTransitSummaryCard } from "@/components/charts/DashaTransitSummaryCard";
import { DivisionalChartSelector } from "@/components/charts/DivisionalChartSelector";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { LifeEventsTree } from "@/components/charts/LifeEventsTree";
import { KpiScorecards } from "@/components/dashboard/KpiScorecards";
import { PlanetaryPositionsTable } from "@/components/charts/PlanetaryPositionsTable";
import { ShareButton } from "@/components/ui";
import { useChartEvents } from "@/lib/events";
import { useWorkflowStore } from "@/lib/store";
import { VARGA_DIVISORS } from "@/lib/astro";
import type {
  DashaPeriodResponse,
  WorkflowAnalysisRequest,
  WorkflowAnalysisResponse,
} from "@/lib/types";

const PLANET_SIGNIFICATIONS: Record<string, string> = {
  Sun: "leadership, authority, vitality, and self-realization",
  Moon: "mind, emotional growth, intuition, and public connection",
  Mars: "courage, action, drive, and technical or strategic pursuits",
  Mercury: "intellect, analytical skill, communication, and commercial enterprise",
  Jupiter: "expansion, learning, wisdom, prosperity, and spiritual growth",
  Venus: "harmony, creativity, relationships, and refinement",
  Saturn: "discipline, structure, perseverance, and long-term stability",
  Rahu: "transformation, material ambition, innovation, and intense evolution",
  Ketu: "spiritual insight, detachment, research, and deep introspection",
};

function getPlanetSignification(planet: string): string {
  const p = planet.charAt(0).toUpperCase() + planet.slice(1).toLowerCase();
  return PLANET_SIGNIFICATIONS[p] || "development and transformative life learning";
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function formatDegree(deg: number): string {
  const whole = Math.floor(deg);
  const minutes = Math.round((deg - whole) * 60);
  return `${whole}° ${minutes}'`;
}

/** The mahadasha (and its active antardasha, if any) whose window contains `at`. */
function findCurrentDasha(mahadashas: DashaPeriodResponse[], at: Date) {
  const t = at.getTime();
  const md = mahadashas.find(
    (m) => t >= new Date(m.start_date).getTime() && t <= new Date(m.end_date).getTime(),
  );
  if (!md) return null;
  const ad = md.sub_periods?.find(
    (p) => t >= new Date(p.start_date).getTime() && t <= new Date(p.end_date).getTime(),
  );
  const totalMs = new Date(md.end_date).getTime() - new Date(md.start_date).getTime();
  const elapsedMs = t - new Date(md.start_date).getTime();
  const percentElapsed = totalMs > 0 ? Math.round((elapsedMs / totalMs) * 100) : 0;
  const daysLeft = Math.max(0, Math.round((new Date(md.end_date).getTime() - t) / 86_400_000));
  const yearsLeft = Math.floor(daysLeft / 365);
  const monthsLeft = Math.floor((daysLeft % 365) / 30);
  return { mahadasha: md, antardasha: ad ?? null, percentElapsed, daysLeft, yearsLeft, monthsLeft };
}

interface Props {
  result: WorkflowAnalysisResponse;
  request: WorkflowAnalysisRequest;
  onEditDetails?: () => void;
}

export function ChartDetailView({ result, request, onEditDetails }: Props) {
  const { chart, dasha, yogas } = result;
  const current = findCurrentDasha(dasha.mahadashas, new Date());
  const chartId = result.chart_id || "";
  const { data: chartEventsData } = useChartEvents(chartId);
  const [datasetAdded, setDatasetAdded] = useState(false);

  const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);
  const [pinnedPlanet, setPinnedPlanet] = useState<string | null>(null);
  const [hoveredHouse, setHoveredHouse] = useState<number | null>(null);
  const [pinnedHouse, setPinnedHouse] = useState<number | null>(null);
  const [selectedVarga, setSelectedVarga] = useState<string>("D1");
  const chartStyle = useWorkflowStore((s) => s.chartStyle);
  const setChartStyle = useWorkflowStore((s) => s.setChartStyle);

  const activePlanet = hoveredPlanet ?? pinnedPlanet;
  const activeHouse = hoveredHouse ?? pinnedHouse;

  const handlePlanetClick = (planet: string) => {
    setPinnedPlanet((cur) => (cur === planet ? null : planet));
    setPinnedHouse(null);
  };
  const handleHouseClick = (house: number) => {
    setPinnedHouse((cur) => (cur === house ? null : house));
    setPinnedPlanet(null);
  };

  const handleAddToDataset = () => {
    try {
      const stored = localStorage.getItem("astroos_research_dataset_charts");
      const list = stored ? JSON.parse(stored) : [];
      if (!list.includes(chartId)) {
        list.push(chartId);
        localStorage.setItem("astroos_research_dataset_charts", JSON.stringify(list));
      }
      setDatasetAdded(true);
      setTimeout(() => setDatasetAdded(false), 3000);
    } catch {
      setDatasetAdded(true);
      setTimeout(() => setDatasetAdded(false), 3000);
    }
  };

  const sunSign = chart.planets.find((p) => p.planet.toLowerCase() === "sun")?.rashi ?? "—";
  const moonSign = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.rashi ?? "—";
  const sunDegree = chart.planets.find((p) => p.planet.toLowerCase() === "sun")?.rashi_degree ?? 0;
  const moonDegree = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.rashi_degree ?? 0;
  const moonNakshatra = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.nakshatra ?? "—";
  const moonPada = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.pada ?? 0;
  const currentYoga = chart.panchanga.yoga.name;
  const currentKarana = chart.panchanga.karana.name;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-lg"
            style={{ backgroundColor: "var(--obsidian-accent-tertiary-soft)", color: "var(--obsidian-accent-tertiary)" }}
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
              <span
                className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300"
              >
                D1 Chart
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Born {formatDate(request.birth_datetime_utc)}
              {request.place_name ? `, ${request.place_name}` : ""}
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
          {onEditDetails && (
            <button type="button" onClick={onEditDetails} className="obsidian-btn-secondary text-xs py-1 px-2.5">
              Edit
            </button>
          )}
          <ShareButton />
        </div>
      </div>

      {/* Quick Stat Cards */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-8">
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Lagna</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">{chart.ascendant.rashi}</p>
          <p className="text-[10px] text-slate-600 dark:text-slate-400">{formatDegree(chart.ascendant.rashi_degree)}</p>
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Sun Sign</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">{sunSign}</p>
          <p className="text-[10px] text-slate-600 dark:text-slate-400">{formatDegree(sunDegree)}</p>
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Moon Sign</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">{moonSign}</p>
          <p className="text-[10px] text-slate-600 dark:text-slate-400">{formatDegree(moonDegree)}</p>
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Nakshatra</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">{moonNakshatra}</p>
          <p className="text-[10px] text-slate-600 dark:text-slate-400">Pada {moonPada}</p>
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Yoga</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">{currentYoga}</p>
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Karana</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">{currentKarana}</p>
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Dasha</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">
            {current ? `${current.mahadasha.lord}/${current.antardasha?.lord ?? ""}` : "—"}
          </p>
          {current && (
            <p className="text-[10px] text-slate-600 dark:text-slate-400">
              {current.yearsLeft}y {current.monthsLeft}m
            </p>
          )}
        </div>
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-2 shadow-sm">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Dasha Rate</p>
          <p className="mt-0.5 text-xs font-bold text-slate-900 dark:text-slate-100">{current ? `${current.percentElapsed}%` : "—"}</p>
          <p className="text-[10px] text-slate-600 dark:text-slate-400">
            {current ? `${current.mahadasha.lord} MD` : ""}
          </p>
        </div>
      </div>

      {/* Main 3-Column Dense Above-the-Fold Grid */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12 items-stretch">
        {/* Left Column (lg:col-span-4): Chart Canvas */}
        <div className="lg:col-span-4 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3 shadow-sm flex flex-col justify-between">
          <div>
            <div className="mb-2 flex flex-col gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center justify-between gap-1.5">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  {selectedVarga} {VARGA_DIVISORS[selectedVarga]?.label ? `· ${VARGA_DIVISORS[selectedVarga].label}` : ""}
                </span>
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
                availableVargas={["D1", ...Object.keys(result.vargas?.charts ?? {})]}
              />
            </div>

            <div className="py-1 flex items-center justify-center min-h-[300px] max-h-[340px] overflow-hidden">
              {chartStyle === "south" ? (
                <SouthIndianChart
                  title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
                  ascendant={
                    selectedVarga === "D1"
                      ? chart.ascendant
                      : result.vargas?.charts[selectedVarga]
                        ? {
                            rashi: result.vargas.charts[selectedVarga].ascendant.varga_rashi,
                            rashi_degree: result.vargas.charts[selectedVarga].ascendant.varga_rashi_degree,
                          }
                        : chart.ascendant
                  }
                  planets={
                    selectedVarga === "D1"
                      ? chart.planets
                      : result.vargas?.charts[selectedVarga]?.planet_positions.map((p) => ({
                          planet: p.planet,
                          rashi: p.varga_rashi,
                          house_number: p.varga_house_number,
                          is_retrograde: p.is_retrograde,
                          rashi_degree: p.varga_rashi_degree,
                        })) ?? chart.planets
                  }
                  size={330}
                  isVarga={selectedVarga !== "D1"}
                  vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                  onPlanetHover={setHoveredPlanet}
                  onPlanetClick={handlePlanetClick}
                  activePlanet={activePlanet}
                  onHouseHover={setHoveredHouse}
                  onHouseClick={handleHouseClick}
                  activeHouse={activeHouse}
                />
              ) : (
                <NorthIndianChart
                  title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
                  ascendant={
                    selectedVarga === "D1"
                      ? chart.ascendant
                      : result.vargas?.charts[selectedVarga]
                        ? {
                            rashi: result.vargas.charts[selectedVarga].ascendant.varga_rashi,
                            rashi_degree: result.vargas.charts[selectedVarga].ascendant.varga_rashi_degree,
                          }
                        : chart.ascendant
                  }
                  planets={
                    selectedVarga === "D1"
                      ? chart.planets
                      : result.vargas?.charts[selectedVarga]?.planet_positions.map((p) => ({
                          planet: p.planet,
                          rashi: p.varga_rashi,
                          house_number: p.varga_house_number,
                          is_retrograde: p.is_retrograde,
                          rashi_degree: p.varga_rashi_degree,
                        })) ?? chart.planets
                  }
                  aspects={chart.aspects}
                  size={330}
                  isVarga={selectedVarga !== "D1"}
                  vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
                  onPlanetHover={setHoveredPlanet}
                  onPlanetClick={handlePlanetClick}
                  activePlanet={activePlanet}
                  onHouseHover={setHoveredHouse}
                  onHouseClick={handleHouseClick}
                  activeHouse={activeHouse}
                />
              )}
            </div>
          </div>

          <div className="mt-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 px-2.5 py-1.5 flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-900 dark:text-slate-100">
              Lagna: <span className="text-cyan-600 dark:text-cyan-400">{chart.ascendant.rashi}</span> {chart.ascendant.rashi_degree.toFixed(2)}°
            </span>
            <span className="text-slate-600 dark:text-slate-400 text-[11px]">
              {chart.ascendant.nakshatra} ({chart.ascendant.pada})
            </span>
          </div>
        </div>

        {/* Middle Column (lg:col-span-5): Tabbed High-Density Sub-Panels */}
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
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">Vimshottari Dasha Timeline</h2>
          <Link href="/charts?view=dasha" className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline">View Full Explorer →</Link>
        </div>
        <DashaTimeline
          dasha={dasha}
          height={110}
          birthDate={request.birth_datetime_utc}
          activeDasha={current}
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