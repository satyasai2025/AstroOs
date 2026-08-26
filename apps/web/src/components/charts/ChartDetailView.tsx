"use client";

import { useState } from "react";
import Link from "next/link";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";
import { DivisionalChartSelector } from "@/components/charts/DivisionalChartSelector";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { LifeEventsTree } from "@/components/charts/LifeEventsTree";
import { KpiScorecards } from "@/components/dashboard/KpiScorecards";
import { PlanetaryPositionsTable } from "@/components/charts/PlanetaryPositionsTable";
import { ShadbalaGaugesOverview } from "@/components/charts/ShadbalaGaugesOverview";
import { StrengthRadarWebChart } from "@/components/charts/StrengthRadarWebChart";
import { ActiveYogasCard } from "@/components/charts/ActiveYogasCard";
import { PanchangaDetailedCard } from "@/components/charts/PanchangaDetailedCard";
import { ResizablePanels, ShareButton } from "@/components/ui";
import { useChartEvents } from "@/lib/events";
import { useWorkflowStore } from "@/lib/store";
import { VARGA_DIVISORS } from "@/lib/astro";
import type {
  DashaPeriodResponse,
  WorkflowAnalysisRequest,
  WorkflowAnalysisResponse,
} from "@/lib/types";

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

  const sunPlanet = chart.planets.find((p) => p.planet === "Sun");
  const moonPlanet = chart.planets.find((p) => p.planet === "Moon");

  const sunSign = sunPlanet?.rashi ?? "—";
  const sunDegree = sunPlanet?.rashi_degree ?? 0;

  const moonSign = moonPlanet?.rashi ?? chart.ascendant.rashi;
  const moonDegree = moonPlanet?.rashi_degree ?? 0;
  const moonNakshatra = moonPlanet?.nakshatra ?? chart.ascendant.nakshatra;
  const moonPada = moonPlanet?.pada ?? chart.ascendant.pada;

  const currentYoga = yogas?.detected_yogas?.[0]?.name ?? "Siddhi Yoga";
  const currentKarana = "Vanija";

  return (
    <div className="space-y-4">
      {/* ── Top Header Title & Actions Bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-1 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <span>{request.subject_name || "Birth Chart Analysis"}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 font-mono font-bold">
              {chart.ascendant.rashi} Ascendant
            </span>
          </h1>
          <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">
            {formatDate(request.birth_datetime_utc)} · {request.place_name || `${request.latitude.toFixed(2)}°, ${request.longitude.toFixed(2)}°`} · {request.ayanamsa} Ayanamsa
          </p>
        </div>
        <div className="flex items-center gap-2">
          {onEditDetails && (
            <button
              type="button"
              onClick={onEditDetails}
              className="rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
            >
              Edit Details
            </button>
          )}
          <ShareButton />
        </div>
      </div>

      {/* ── Row 1: 7 Panchang & Astrological KPI Cards Grid ── */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-7">
        {/* Card 1: Lagna */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-sm flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-base font-bold flex-shrink-0">
            ♉
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Lagna</p>
            <p className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">{chart.ascendant.rashi}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">{formatDegree(chart.ascendant.rashi_degree)}</p>
          </div>
        </div>

        {/* Card 2: Moon Sign */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-sm flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-base font-bold flex-shrink-0">
            ♈
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Moon Sign</p>
            <p className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">{moonSign}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">{formatDegree(moonDegree)}</p>
          </div>
        </div>

        {/* Card 3: Sun Sign */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-sm flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-base font-bold flex-shrink-0">
            ♌
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Sun Sign</p>
            <p className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">{sunSign}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">{formatDegree(sunDegree)}</p>
          </div>
        </div>

        {/* Card 4: Nakshatra */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-sm flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-base font-bold flex-shrink-0">
            ✵
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Nakshatra</p>
            <p className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">{moonNakshatra}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">Pada {moonPada}</p>
          </div>
        </div>

        {/* Card 5: Yoga */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-sm flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-base font-bold flex-shrink-0">
            ☸
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Yoga</p>
            <p className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">{currentYoga}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">Active</p>
          </div>
        </div>

        {/* Card 6: Karana */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-sm flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-base font-bold flex-shrink-0">
            ⚙
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Karana</p>
            <p className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">{currentKarana}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">Active</p>
          </div>
        </div>

        {/* Card 7: Tithi */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-sm flex items-center gap-2.5">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-base font-bold flex-shrink-0">
            🌙
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Tithi</p>
            <p className="text-xs font-extrabold text-slate-900 dark:text-slate-100 truncate">Shukla Ekadashi</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">Active</p>
          </div>
        </div>
      </div>

      {/* ── Row 2: Main Resizable 3-Column Above-the-Fold Panels ── */}
      <ResizablePanels defaultSizes={[0.34, 0.33, 0.33]}>
        {/* Column 1: Lagna Chart (D1) Canvas */}
        <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm flex flex-col justify-between h-full">
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

            <div className="py-2 flex items-center justify-center w-full min-h-[320px]">
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

        {/* Column 2: Planetary Positions Table */}
        <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm flex flex-col justify-between h-full">
          <PlanetaryPositionsTable
            ascendant={chart.ascendant}
            planets={chart.planets}
            activePlanet={activePlanet}
            onPlanetClick={handlePlanetClick}
          />
        </div>

        {/* Column 3: Shadbala Overview Circular Gauges */}
        <div className="flex flex-col h-full">
          <ShadbalaGaugesOverview result={result} />
        </div>
      </ResizablePanels>

      {/* ── Row 3: Bottom Resizable 3-Column Panels ── */}
      <ResizablePanels defaultSizes={[0.34, 0.33, 0.33]}>
        {/* Column 1: Jagannatha Hora Classical Panchanga & Dasha Card */}
        <div className="flex flex-col h-full">
          <PanchangaDetailedCard result={result} request={request} />
        </div>

        {/* Column 2: Strength Analysis 6-Axis Radar Web Chart */}
        <div className="flex flex-col h-full">
          <StrengthRadarWebChart result={result} />
        </div>

        {/* Column 3: Active Yogas Card */}
        <div className="flex flex-col h-full">
          <ActiveYogasCard result={result} />
        </div>
      </ResizablePanels>

      {/* ── Below-the-Fold Expandable Sections ── */}
      <div className="space-y-4 pt-2">
        {/* Chart KPI Scorecards */}
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-400">
            Comprehensive KPI Scorecards
          </h3>
          <KpiScorecards result={result} />
        </div>

        {/* Dasha Timeline Section */}
        <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">Full Vimshottari Dasha Timeline</h2>
            <Link href="/charts/dasha" className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline">View Full Explorer →</Link>
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
          <div>
            <LifeEventsTree chartId={chartId} />
          </div>
        )}
      </div>
    </div>
  );
}