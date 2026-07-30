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
  return { mahadasha: md, antardasha: ad ?? null, percentElapsed, daysLeft };
}

function StatCard({ label, value, sublabel }: { label: string; value: string; sublabel?: string }) {
  return (
    <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
      <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{label}</p>
      <p className="mt-1 text-sm font-bold" style={{ color: "var(--text-primary)" }}>{value}</p>
      {sublabel && <p className="mt-0.5 text-[11px]" style={{ color: "var(--text-secondary)" }}>{sublabel}</p>}
    </div>
  );
}

interface Props {
  result: WorkflowAnalysisResponse;
  request: WorkflowAnalysisRequest;
  onEditDetails?: () => void;
}

export function ChartDetailView({ result, request, onEditDetails }: Props) {
  const { chart, dasha } = result;
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

  return (
    <div className="space-y-6">
      {/* Breadcrumb + header */}
      <div>
        <p className="mb-2 text-xs" style={{ color: "var(--text-muted)" }}>
          <Link href="/charts/history" className="hover:underline">Charts</Link> {" > "}
        </p>
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
            <Link href="/charts/compare" className="obsidian-btn-secondary text-sm">
              Compare
            </Link>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Lagna" value={chart.ascendant.rashi} sublabel={`${chart.ascendant.rashi_degree.toFixed(2)}°`} />
        <StatCard
          label="Sun Sign"
          value={chart.planets.find((p) => p.planet.toLowerCase() === "sun")?.rashi ?? "—"}
        />
        <StatCard
          label="Moon Sign"
          value={chart.planets.find((p) => p.planet.toLowerCase() === "moon")?.rashi ?? "—"}
        />
        <StatCard
          label="Nakshatra"
          value={chart.ascendant.nakshatra}
          sublabel={`Pada ${chart.ascendant.pada}`}
        />
        <StatCard label="Yoga" value={chart.panchanga.yoga.name} sublabel={`${chart.panchanga.yoga.completion_percent.toFixed(0)}% elapsed`} />
        <StatCard label="Karana" value={chart.panchanga.karana.name} />
        <StatCard
          label="Current Dasha"
          value={current ? `${current.mahadasha.lord}${current.antardasha ? ` / ${current.antardasha.lord}` : ""}` : "—"}
          sublabel={current ? `${current.daysLeft}d left` : undefined}
        />
        <StatCard
          label="MD Elapsed"
          value={current ? `${current.percentElapsed}%` : "—"}
          sublabel={current ? `of ${current.mahadasha.lord} MD` : undefined}
        />
      </div>

      {/* Main content (chart, table, dasha, quick actions) alongside a sticky
          detail panel that shows whichever planet/house is hovered or
          pinned in the chart — replaces the old static AI Insight / Key
          Yogas / Strength Overview cards with one live, interactive view. */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="obsidian-card p-5">
            <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Lagna Chart (North Indian)
            </h2>
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

          <div className="obsidian-card overflow-x-auto p-5">
            <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Planetary Positions
            </h2>
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
                <tr className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                  <td className="py-2 pr-3 font-medium">Ascendant</td>
                  <td className="py-2 pr-3 capitalize">{chart.ascendant.rashi}</td>
                  <td className="py-2 pr-3">{chart.ascendant.rashi_degree.toFixed(2)}°</td>
                  <td className="py-2 pr-3">1</td>
                  <td className="py-2 pr-3 capitalize">{chart.ascendant.nakshatra} (pada {chart.ascendant.pada})</td>
                </tr>
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
            <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Dasha Timeline ({dasha.system})
            </h2>
            <DashaTimeline dasha={dasha} height={140} />
          </div>

          <div className="obsidian-card p-5">
            <h2 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Quick Actions</h2>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <Link href="/charts/compare" className="block rounded-lg border p-2.5 text-xs transition-colors" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                Compare With Another Chart
              </Link>
              <Link href="/charts?view=timeline" className="block rounded-lg border p-2.5 text-xs transition-colors" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                View Current Transits
              </Link>
              <Link href="/charts?view=dasha" className="block rounded-lg border p-2.5 text-xs transition-colors" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                Full Dasha Timeline
              </Link>
            </div>
          </div>
        </div>

        <div className="lg:col-span-1">
          <ChartDetailPanel chart={chart} activePlanet={activePlanet} activeHouse={activeHouse} />
        </div>
      </div>
    </div>
  );
}
