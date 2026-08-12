"use client";

import { useMemo } from "react";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { VargaGuideCard } from "@/components/charts/VargaGuideCard";
import { Table, type TableColumn } from "@/components/ui";
import { VARGA_DIVISORS, rashiLordFromApiName } from "@/lib/astro";
import type {
  AllVargaChartsResponse,
  D1ChartResponse,
  VargaPlanetResponse,
} from "@/lib/types";

interface Props {
  chart: D1ChartResponse;
  vargas: AllVargaChartsResponse | null;
  selectedVarga: string;
  setSelectedVarga: (v: string) => void;
}

/**
 * Dedicated "Divisional Charts" presentation for the main Charts page.
 *
 * Data contract: reuses the same varga calculation already loaded by the
 * Charts page (`vargas.charts[key]` for D2…D60, and the base natal `chart`
 * for D1). No varga math happens here — this is presentation only.
 *
 * Reuses existing rendering infrastructure: `NorthIndianChart` for the wheel
 * and the shared `Table` for planetary positions, so this view stays a single
 * chart-rendering system rather than introducing a second one.
 */
export default function DivisionalChartsPanel({
  chart,
  vargas,
  selectedVarga,
  setSelectedVarga,
}: Props) {
  const vargaKeys = useMemo(
    () =>
      ["D1", ...Object.keys(vargas?.charts ?? {})].filter(
        (k, i, arr) => arr.indexOf(k) === i && !!VARGA_DIVISORS[k],
      ),
    [vargas],
  );

  const currentPlanets = useMemo(() => {
    if (selectedVarga === "D1") {
      return chart.planets.map((p) => ({
        planet: p.planet,
        rashi: p.rashi,
        house_number: p.house_number,
        is_retrograde: p.is_retrograde,
        rashi_degree: p.rashi_degree,
      }));
    }
    const vc = vargas?.charts[selectedVarga];
    if (!vc) return null;
    return vc.planet_positions.map((p) => ({
      planet: p.planet,
      rashi: p.varga_rashi,
      house_number: p.varga_house_number,
      is_retrograde: p.is_retrograde,
      rashi_degree: p.varga_rashi_degree,
    }));
  }, [chart, vargas, selectedVarga]);

  const currentAscendant = useMemo(() => {
    if (selectedVarga === "D1") {
      return {
        rashi: chart.ascendant.rashi,
        rashi_degree: chart.ascendant.rashi_degree,
      };
    }
    const ac = vargas?.charts[selectedVarga]?.ascendant;
    return ac
      ? { rashi: ac.varga_rashi, rashi_degree: ac.varga_rashi_degree }
      : { rashi: chart.ascendant.rashi, rashi_degree: chart.ascendant.rashi_degree };
  }, [chart, vargas, selectedVarga]);

  const retroByPlanet = useMemo<Record<string, boolean>>(() => {
    const vc = vargas?.charts[selectedVarga];
    if (!vc) return {};
    return Object.fromEntries(
      vc.planet_positions.map((p) => [p.planet, p.is_retrograde]),
    );
  }, [vargas, selectedVarga]);

  if (!currentPlanets) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-secondary)" }}>
        Divisional charts were not computed for this chart (vargas unchecked at input
        time).
      </div>
    );
  }

  const columns: TableColumn<(typeof currentPlanets)[number]>[] = [
    { key: "planet", label: "Planet" },
    { key: "rashi", label: "Sign" },
    {
      key: "rashi_degree",
      label: "Degree",
      mono: true,
      align: "right",
      render: (r) => r.rashi_degree?.toFixed(2) ?? "—",
    },
    {
      key: "house_number",
      label: "House",
      align: "center",
      render: (r) => r.house_number ?? "—",
    },
    {
      key: "retro",
      label: "State",
      align: "center",
      render: (r) =>
        (retroByPlanet[r.planet] ?? r.is_retrograde) ? (
          <span style={{ color: "var(--text-warning)" }}>R</span>
        ) : (
          <span style={{ color: "var(--text-muted)" }}>—</span>
        ),
    },
  ];

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="glass-card flex flex-col items-center p-6">
        <h2
          className="mb-4 text-sm font-semibold uppercase tracking-wide"
          style={{ color: "var(--accent)" }}
        >
          {selectedVarga} — {VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}
        </h2>

        <NorthIndianChart
          title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
          ascendant={currentAscendant}
          planets={currentPlanets}
          size={380}
          isVarga={selectedVarga !== "D1"}
          vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
        />

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
          <p className="font-semibold" style={{ color: "var(--accent)" }}>
            {currentAscendant.rashi}{" "}
            <span className="font-normal" style={{ color: "var(--text-secondary)" }}>
              {currentAscendant.rashi_degree?.toFixed(2)}°
            </span>
          </p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Lord: {rashiLordFromApiName(currentAscendant.rashi) ?? "—"}
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="glass-card p-4">
          <h3
            className="mb-3 text-xs font-semibold uppercase tracking-wide"
            style={{ color: "var(--accent)" }}
          >
            Varga
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {vargaKeys.map((vk) => {
              const vd = VARGA_DIVISORS[vk];
              const isActive = selectedVarga === vk;
              return (
                <button
                  key={vk}
                  type="button"
                  onClick={() => setSelectedVarga(vk)}
                  className="rounded-full px-2.5 py-1 text-xs font-semibold transition"
                  style={{
                    backgroundColor: isActive ? "var(--accent)" : "var(--bg-card)",
                    color: isActive ? "var(--accent-text)" : "var(--text-secondary)",
                    border: `1px solid ${
                      isActive ? "var(--accent)" : "var(--border-primary)"
                    }`,
                  }}
                  aria-pressed={isActive}
                  aria-label={`Show ${vd?.label ?? vk} chart`}
                >
                  {vd?.label ?? vk}
                </button>
              );
            })}
          </div>
        </div>

        <VargaGuideCard code={selectedVarga} />

        <div className="glass-card p-4">
          <h3
            className="mb-3 text-xs font-semibold uppercase tracking-wide"
            style={{ color: "var(--accent)" }}
          >
            Planet Positions
          </h3>
          <Table columns={columns} rows={currentPlanets} />
        </div>
      </div>
    </div>
  );
}