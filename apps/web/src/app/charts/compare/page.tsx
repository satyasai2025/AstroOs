"use client";

import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { useWorkflowStore } from "@/lib/store";
import { VARGA_DIVISORS } from "@/lib/astro";

/**
 * /charts/compare — Side-by-side D1 + D9 chart comparison view.
 *
 * Displays the Rashi (D1) and Navamsha (D9) charts rendered as
 * North Indian diamond charts, allowing the user to visually compare
 * planetary placements across the two divisional charts.
 */
export default function ChartComparePage() {
  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);

  if (!result) {
    return (
      <AppShell>
        <div
          className="flex flex-col items-center justify-center gap-4 py-20"
          role="status"
        >
          <div className="glass-card flex flex-col items-center gap-4 p-8 text-center">
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
              <rect x="2" y="3" width="8" height="18" rx="1" />
              <rect x="14" y="3" width="8" height="18" rx="1" />
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

  const { chart, vargas } = result;

  // D1 planet placements
  const d1Planets = chart.planets.map((p) => ({
    planet: p.planet,
    rashi: p.rashi,
    house_number: p.house_number,
    is_retrograde: p.is_retrograde,
    rashi_degree: p.rashi_degree,
  }));

  // D9 planet placements
  const d9Data = vargas?.charts["D9"];
  const d9Planets = d9Data
    ? d9Data.planet_positions.map((p) => ({
        planet: p.planet,
        rashi: p.varga_rashi,
        house_number: p.varga_house_number,
        is_retrograde: p.is_retrograde,
        rashi_degree: p.varga_rashi_degree,
      }))
    : null;

  const d9Ascendant = d9Data
    ? {
        rashi: d9Data.ascendant.varga_rashi,
        rashi_degree: d9Data.ascendant.varga_rashi_degree,
      }
    : null;

  const d1Ascendant = {
    rashi: chart.ascendant.rashi,
    rashi_degree: chart.ascendant.rashi_degree,
  };

  // Build comparison summary
  const d1Placements = new Map(
    chart.planets.map((p) => [p.planet, p.rashi]),
  );
  const d9Placements = d9Data
    ? new Map(d9Data.planet_positions.map((p) => [p.planet, p.varga_rashi]))
    : new Map();

  const planets = [
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
    "Rahu",
    "Ketu",
  ];

  const samePlacement = planets.filter(
    (p) => d1Placements.get(p) && d9Placements.get(p) && d1Placements.get(p) === d9Placements.get(p),
  );

  return (
    <AppShell>
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Chart Comparison
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Side-by-side D1 (Rashi) and D9 (Navamsha) chart comparison.
            {request && (
              <>
                {" "}
                Subject: <span className="font-medium">{request.subject_name}</span>
              </>
            )}
          </p>
        </div>
        <Link
          href="/charts"
          className="btn-ghost text-xs px-3 py-1.5"
          aria-label="Back to chart view"
        >
          Back to Charts
        </Link>
      </div>

      {/* Side-by-side charts */}
      <div
        className="grid grid-cols-1 gap-6 lg:grid-cols-2"
        role="region"
        aria-label="D1 and D9 charts side by side"
      >
        {/* D1 Chart */}
        <div className="glass-card p-6">
          <NorthIndianChart
            title="D1 — Rashi Chart"
            ascendant={d1Ascendant}
            planets={d1Planets}
            size={380}
          />
        </div>

        {/* D9 Chart */}
        {d9Planets && d9Ascendant ? (
          <div className="glass-card p-6">
            <NorthIndianChart
              title="D9 — Navamsha Chart"
              ascendant={d9Ascendant}
              planets={d9Planets}
              size={380}
              isVarga
              vargaDivisor={9}
            />
          </div>
        ) : (
          <div className="glass-card flex items-center justify-center p-6">
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              D9 (Navamsha) chart data not available.
              Ensure "Include Vargas" was checked during analysis.
            </p>
          </div>
        )}
      </div>

      {/* Comparison summary table */}
      <div className="mt-6 glass-card overflow-x-auto p-5">
        <h3
          className="mb-3 text-sm font-semibold uppercase tracking-wide"
          style={{ color: "var(--accent)" }}
        >
          Placement Comparison — D1 vs D9
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
              <th className="py-2 pr-3" scope="col">D1 Rashi</th>
              <th className="py-2 pr-3" scope="col">D9 Rashi</th>
              <th className="py-2 pr-3" scope="col">Same?</th>
              <th className="py-2 pr-3" scope="col">D1 House</th>
              <th className="py-2" scope="col">D9 House</th>
            </tr>
          </thead>
          <tbody>
            {planets.map((planet) => {
              const d1Rashi = d1Placements.get(planet) ?? "—";
              const d9Rashi = d9Placements.get(planet) ?? "—";
              const isSame = d1Rashi === d9Rashi && d1Rashi !== "—";
              const d1Planet = chart.planets.find((p) => p.planet === planet);
              const d9Planet = d9Data?.planet_positions.find(
                (p) => p.planet === planet,
              );

              return (
                <tr
                  key={planet}
                  className="border-b"
                  style={{
                    borderColor: "var(--border-primary)",
                    color: "var(--text-primary)",
                  }}
                >
                  <td className="py-2 pr-3 font-medium capitalize">{planet}</td>
                  <td className="py-2 pr-3 capitalize">{d1Rashi}</td>
                  <td className="py-2 pr-3 capitalize">{d9Rashi}</td>
                  <td className="py-2 pr-3">
                    <span
                      className="inline-block h-2 w-2 rounded-full"
                      style={{
                        backgroundColor: isSame
                          ? "#34d399"
                          : "var(--text-muted)",
                      }}
                      aria-label={isSame ? "Same placement in D1 and D9" : "Different placement"}
                    />
                  </td>
                  <td className="py-2 pr-3">{d1Planet?.house_number ?? "—"}</td>
                  <td className="py-2">{d9Planet?.varga_house_number ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Summary */}
        <div
          className="mt-4 rounded-lg border p-3"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
        >
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            {samePlacement.length > 0 ? (
              <>
                <span style={{ color: "var(--accent)" }}>
                  {samePlacement.length} planet{samePlacement.length !== 1 ? "s" : ""}
                </span>{" "}
                {samePlacement.length === 1 ? "has" : "have"} the same rashi placement
                in both D1 and D9:{" "}
                <span className="font-medium">
                  {samePlacement.join(", ")}
                </span>
                .
              </>
            ) : (
              <span>
                No planets share the same rashi placement between D1 and D9.
              </span>
            )}
          </p>
        </div>
      </div>
    </AppShell>
  );
}
