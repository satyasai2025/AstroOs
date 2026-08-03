"use client";

import Link from "next/link";
import { useState } from "react";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { ChartDetailPanel } from "@/components/charts/ChartDetailPanel";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
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

  const [hoveredPlanet, setHoveredPlanet] = useState<string | null>(null);
  const [pinnedPlanet, setPinnedPlanet] = useState<string | null>(null);
  const [hoveredHouse, setHoveredHouse] = useState<number | null>(null);
  const [pinnedHouse, setPinnedHouse] = useState<number | null>(null);

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

  const sunSign = chart.planets.find((p) => p.planet.toLowerCase() === "sun")?.rashi ?? "—";
  const moonSign = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.rashi ?? "—";
  const sunDegree = chart.planets.find((p) => p.planet.toLowerCase() === "sun")?.rashi_degree ?? 0;
  const moonDegree = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.rashi_degree ?? 0;
  const moonNakshatra = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.nakshatra ?? "—";
  const moonPada = chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.pada ?? 0;
  const currentYoga = chart.panchanga.yoga.name;
  const currentKarana = chart.panchanga.karana.name;

  const activeYogas = yogas?.results?.filter((y) => y.is_present) ?? [];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className="flex h-11 w-11 items-center justify-center rounded-lg"
            style={{ backgroundColor: "var(--obsidian-accent-tertiary-soft)", color: "var(--obsidian-accent-tertiary)" }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="m12 3 2.6 6.2L21 10l-5 4.3L17.4 21 12 17.5 6.6 21 8 14.3 3 10l6.4-.8L12 3Z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
                {request.subject_name} Birth Chart
              </h1>
              <span
                className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
                style={{ border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
              >
                D1 Chart
              </span>
            </div>
            <p className="mt-0.5 text-sm" style={{ color: "var(--text-secondary)" }}>
              Born {formatDate(request.birth_datetime_utc)}
              {request.place_name ? `, ${request.place_name}` : ""}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {onEditDetails && (
            <button type="button" onClick={onEditDetails} className="obsidian-btn-secondary text-sm">
              Edit Details
            </button>
          )}
          <button type="button" className="obsidian-btn-secondary text-sm">Share</button>
        </div>
      </div>

      {/* Quick Stat Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-8">
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Lagna</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{chart.ascendant.rashi}</p>
          <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{formatDegree(chart.ascendant.rashi_degree)}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Sun Sign</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{sunSign}</p>
          <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{formatDegree(sunDegree)}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Moon Sign</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{moonSign}</p>
          <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{formatDegree(moonDegree)}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Nakshatra</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{moonNakshatra}</p>
          <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>Pada {moonPada}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Yoga</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{currentYoga}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Karana</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{currentKarana}</p>
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Current Dasha</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {current ? `${current.mahadasha.lord}${current.antardasha ? ` / ${current.antardasha.lord}` : ""}` : "—"}
          </p>
          {current && (
            <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>
              {current.yearsLeft}y {current.monthsLeft}m left
            </p>
          )}
        </div>
        <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
          <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Dasha Rate</p>
          <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{current ? `${current.percentElapsed}%` : "—"}</p>
          <p className="text-[11px]" style={{ color: "var(--text-secondary)" }}>
            {current ? `of ${current.mahadasha.lord} MD` : ""}
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(300px,1.2fr)_1fr_320px]">
        {/* Chart */}
        <div className="obsidian-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Lagna Chart (North Indian)</h2>
            <Link href="/charts" className="text-[11px] underline" style={{ color: "var(--text-muted)" }}>View Full Chart</Link>
          </div>
          <div className="mx-auto max-w-xl">
            <NorthIndianChart
              ascendant={chart.ascendant}
              planets={chart.planets}
              aspects={chart.aspects}
              size={480}
              onPlanetHover={setHoveredPlanet}
              onPlanetClick={handlePlanetClick}
              activePlanet={activePlanet}
              onHouseHover={setHoveredHouse}
              onHouseClick={handleHouseClick}
              activeHouse={activeHouse}
            />
          </div>
        </div>

        {/* Planetary Positions + Dasha */}
        <div className="space-y-5">
          <div className="obsidian-card overflow-x-auto p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Planetary Positions</h2>
              <Link href="/charts" className="text-[11px] underline" style={{ color: "var(--text-muted)" }}>View All</Link>
            </div>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-xs uppercase" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                  <th className="py-2 pr-3">Planet</th>
                  <th className="py-2 pr-3">Sign</th>
                  <th className="py-2 pr-3">Degree</th>
                  <th className="py-2 pr-3">House</th>
                  <th className="py-2 pr-3">Nakshatra</th>
                </tr>
              </thead>
              <tbody>
                {chart.planets.map((p) => (
                  <tr key={p.planet} className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                    <td className="py-2 pr-3 font-medium capitalize">{p.planet}</td>
                    <td className="py-2 pr-3 capitalize">{p.rashi}</td>
                    <td className="py-2 pr-3">{p.rashi_degree.toFixed(2)}°</td>
                    <td className="py-2 pr-3">{p.house_number}</td>
                    <td className="py-2 pr-3 capitalize">{p.nakshatra}{p.is_retrograde ? " (R)" : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="obsidian-card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Dasha Timeline</h2>
              <Link href="/charts?view=dasha" className="text-[11px] underline" style={{ color: "var(--text-muted)" }}>View Details</Link>
            </div>
            <DashaTimeline dasha={dasha} height={120} />
          </div>
        </div>

        {/* Right sidebar: Insights + Recent Analyses + Quick Actions */}
        <div className="space-y-5">
          {/* AI Insights */}
          <div className="obsidian-card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-widest" style={{ color: "var(--text-tertiary)" }}>AI Insights</h3>
              <Link href="/ai/explain" className="text-[11px] underline" style={{ color: "var(--text-muted)" }}>View Analysis</Link>
            </div>
            {current && (
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                {current.mahadasha.lord} Mahadasha is a favorable period for growth, learning, and expansion.
                The ongoing Jupiter/Saturn Antardasha indicates disciplined progress, potential gains through hard work, and long-term stability.
              </p>
            )}
          </div>

          {/* Recent Analyses */}
          <div className="obsidian-card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-widest" style={{ color: "var(--text-tertiary)" }}>Recent Analyses</h3>
              <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>View All</span>
            </div>
            <div className="space-y-2.5">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "var(--text-muted)" }}>
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>Career Prospects Analysis</span>
                </div>
                <span className="text-[10px]" style={{ color: "var(--success-400)" }}>Completed</span>
              </div>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "var(--text-muted)" }}>
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>Marriage Timing Analysis</span>
                </div>
                <span className="text-[10px]" style={{ color: "var(--success-400)" }}>Completed</span>
              </div>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "var(--text-muted)" }}>
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>Financial Growth Analysis</span>
                </div>
                <span className="text-[10px]" style={{ color: "var(--success-400)" }}>Completed</span>
              </div>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "var(--text-muted)" }}>
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>Health & Longevity Analysis</span>
                </div>
                <span className="text-[10px]" style={{ color: "var(--success-400)" }}>Completed</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="obsidian-card p-5">
            <h3 className="mb-3 text-xs font-bold uppercase tracking-widest" style={{ color: "var(--text-tertiary)" }}>Quick Actions</h3>
            <div className="space-y-2">
              <Link href="/reports/pdf" className="flex items-center gap-2.5 rounded-lg border p-2.5 text-xs transition-colors" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
                </svg>
                <div>
                  <div className="font-medium">Generate Full Report</div>
                  <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>PDF report with all analysis</div>
                </div>
              </Link>
              <Link href="/charts/compare" className="flex items-center gap-2.5 rounded-lg border p-2.5 text-xs transition-colors" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 13 9 5 9-5" />
                </svg>
                <div>
                  <div className="font-medium">Compare With Chart</div>
                  <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>Compare with another chart</div>
                </div>
              </Link>
              <Link href="/charts?view=timeline" className="flex items-center gap-2.5 rounded-lg border p-2.5 text-xs transition-colors" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="2.5" /><ellipse cx="12" cy="12" rx="9" ry="4" />
                </svg>
                <div>
                  <div className="font-medium">Transit Now</div>
                  <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>See current transits</div>
                </div>
              </Link>
              <Link href="/charts?view=dasha" className="flex items-center gap-2.5 rounded-lg border p-2.5 text-xs transition-colors" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" />
                </svg>
                <div>
                  <div className="font-medium">Dasha Calendar</div>
                  <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>View full dasha timeline</div>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}