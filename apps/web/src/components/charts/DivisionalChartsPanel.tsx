"use client";

import { useMemo } from "react";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";
import { VargaGuideCard } from "@/components/charts/VargaGuideCard";
import { Table, type TableColumn } from "@/components/ui";
import { DivisionalChartSelector } from "@/components/charts/DivisionalChartSelector";
import { VARGA_DIVISORS, rashiLordFromApiName } from "@/lib/astro";
import { useWorkflowStore } from "@/lib/store";
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
  const chartStyle = useWorkflowStore((s) => s.chartStyle);
  const setChartStyle = useWorkflowStore((s) => s.setChartStyle);

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

        {chartStyle === "south" ? (
          <SouthIndianChart
            title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
            ascendant={currentAscendant}
            planets={currentPlanets}
            size={380}
            isVarga={selectedVarga !== "D1"}
            vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
          />
        ) : (
          <NorthIndianChart
            title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
            ascendant={currentAscendant}
            planets={currentPlanets}
            size={380}
            isVarga={selectedVarga !== "D1"}
            vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
          />
        )}

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
        <div className="glass-card p-4 flex flex-col gap-4">
          <div>
            <h3
              className="mb-2 text-xs font-semibold uppercase tracking-wide"
              style={{ color: "var(--accent)" }}
            >
              Chart Style
            </h3>
            <div className="flex items-center rounded-lg p-0.5 bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700">
              <button
                type="button"
                onClick={() => setChartStyle("north")}
                className={`w-1/2 rounded-md py-1.5 text-xs font-semibold transition ${
                  chartStyle === "north"
                    ? "bg-cyan-500 text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
                aria-pressed={chartStyle === "north"}
              >
                North Indian
              </button>
              <button
                type="button"
                onClick={() => setChartStyle("south")}
                className={`w-1/2 rounded-md py-1.5 text-xs font-semibold transition ${
                  chartStyle === "south"
                    ? "bg-cyan-500 text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
                aria-pressed={chartStyle === "south"}
              >
                South Indian
              </button>
            </div>
          </div>

          <div>
            <h3
              className="mb-2 text-xs font-semibold uppercase tracking-wide"
              style={{ color: "var(--accent)" }}
            >
              Varga
            </h3>
            <DivisionalChartSelector
              selectedVarga={selectedVarga}
              onSelectVarga={setSelectedVarga}
              availableVargas={vargaKeys}
            />
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