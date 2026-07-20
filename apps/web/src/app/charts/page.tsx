"use client";

import { useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { NakshatraPadaSelector } from "@/components/charts/NakshatraPadaSelector";
import { DashaTimeline } from "@/components/charts/DashaTimeline";
import { useWorkflowStore } from "@/lib/store";
import { VARGA_DIVISORS, RASHI_LORDS } from "@/lib/astro";

const VARGA_KEYS = ["D1", "D9"] as const;

type ViewMode = "chart" | "nakshatra" | "dasha";

export default function ChartsPage() {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const [view, setView] = useState<ViewMode>("chart");
  const [selectedVarga, setSelectedVarga] = useState<string>("D1");

  if (!result) {
    return (
      <AppShell>
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
    <AppShell>
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
          { key: "chart" as ViewMode, label: "Chart View" },
          { key: "nakshatra" as ViewMode, label: "Nakshatra / Pada" },
          { key: "dasha" as ViewMode, label: "Dasha Timeline" },
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

      {/* Chart View Panel */}
      {view === "chart" && (
        <div
          id="panel-chart"
          role="tabpanel"
          aria-label="Chart visualization panel"
          className="space-y-6"
        >
          {/* Varga selector */}
          <div className="flex flex-wrap gap-2">
            {VARGA_KEYS.map((vk) => {
              const vd = VARGA_DIVISORS[vk];
              return (
                <button
                  key={vk}
                  type="button"
                  onClick={() => setSelectedVarga(vk)}
                  className="rounded-full px-3 py-1 text-xs font-semibold transition"
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

          {/* Chart rendering */}
          <div className="flex flex-col items-center gap-6 lg:flex-row lg:items-start lg:justify-center">
            <div className="glass-card p-6 flex-shrink-0">
              <NorthIndianChart
                title={`${selectedVarga} — ${
                  VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"
                }`}
                ascendant={currentAscendant}
                planets={currentVargaPlanets}
                size={420}
                isVarga={selectedVarga !== "D1"}
                vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
              />
            </div>

            {/* Planet table sidebar */}
            <div className="glass-card overflow-x-auto p-5 min-w-[320px] max-w-md flex-1">
              <h3
                className="mb-3 text-sm font-semibold uppercase tracking-wide"
                style={{ color: "var(--accent)" }}
              >
                {selectedVarga} Planetary Positions
              </h3>
              <table className="w-full text-left text-sm" role="table">
                <thead>
                  <tr
                    className="border-b text-xs uppercase tracking-wide"
                    style={{
                      borderColor: "var(--border-primary)",
                      color: "var(--text-muted)",
                    }}
                  >
                    <th className="py-2 pr-3" scope="col">Planet</th>
                    <th className="py-2 pr-3" scope="col">Rashi</th>
                    <th className="py-2 pr-3" scope="col">Degree</th>
                    <th className="py-2" scope="col">House</th>
                  </tr>
                </thead>
                <tbody>
                  {currentVargaPlanets.map((p) => (
                    <tr
                      key={p.planet}
                      className="border-b"
                      style={{
                        borderColor: "var(--border-primary)",
                        color: "var(--text-primary)",
                      }}
                    >
                      <td className="py-2 pr-3 font-medium capitalize">
                        {p.planet}
                        {p.is_retrograde && (
                          <span
                            className="ml-1 text-xs"
                            style={{ color: "var(--chart-ascendant)" }}
                          >
                            (R)
                          </span>
                        )}
                      </td>
                      <td className="py-2 pr-3 capitalize">{p.rashi}</td>
                      <td className="py-2 pr-3">
                        {p.rashi_degree.toFixed(2)}°
                      </td>
                      <td className="py-2">{p.house_number}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Ascendant summary */}
              <div
                className="mt-4 rounded-lg border p-3"
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
                  {RASHI_LORDS[
                    currentAscendant.rashi as keyof typeof RASHI_LORDS
                  ] ?? "—"}
                </p>
              </div>
            </div>
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
    </AppShell>
  );
}
