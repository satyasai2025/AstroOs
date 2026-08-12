"use client";

import { useMemo, useState } from "react";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { VargaGuideCard } from "@/components/charts/VargaGuideCard";
import { Table, type TableColumn } from "@/components/ui";
import { VARGA_DIVISORS, rashiLordFromApiName } from "@/lib/astro";
import type {
  AllVargaChartsResponse,
  D1ChartResponse,
  TransitResponse,
} from "@/lib/types";

type ExplorerMode = "single" | "mixed" | "grid";
type ChartSource = "natal" | "transit";

interface ChartContext {
  source: ChartSource;
  varga: string;
}

interface PlanetPlacement {
  planet: string;
  rashi: string;
  house_number?: number;
  is_retrograde?: boolean;
  rashi_degree?: number;
}

interface AscendantPlacement {
  rashi: string;
  rashi_degree?: number;
}

interface ResolvedChart {
  title: string;
  ascendant: AscendantPlacement;
  planets: PlanetPlacement[];
  isVarga: boolean;
  vargaDivisor?: number;
}

interface Props {
  chart: D1ChartResponse;
  vargas: AllVargaChartsResponse | null;
  transits: TransitResponse | null;
  selectedVarga: string;
  setSelectedVarga: (v: string) => void;
}

function getVargaPlanets(
  vargas: AllVargaChartsResponse | null,
  vargaKey: string,
): PlanetPlacement[] | null {
  if (vargaKey === "D1") return null;
  const vc = vargas?.charts[vargaKey];
  if (!vc) return null;
  return vc.planet_positions.map((p) => ({
    planet: p.planet,
    rashi: p.varga_rashi,
    house_number: p.varga_house_number,
    is_retrograde: p.is_retrograde,
    rashi_degree: p.varga_rashi_degree,
  }));
}

function getVargaAscendant(
  vargas: AllVargaChartsResponse | null,
  vargaKey: string,
  fallback: AscendantPlacement,
): AscendantPlacement {
  if (vargaKey === "D1") return fallback;
  const ac = vargas?.charts[vargaKey]?.ascendant;
  return ac
    ? { rashi: ac.varga_rashi, rashi_degree: ac.varga_rashi_degree }
    : fallback;
}

function getTransitPlanets(transits: TransitResponse | null): PlanetPlacement[] | null {
  if (!transits) return null;
  return transits.planets.map((p) => ({
    planet: p.planet,
    rashi: p.transit_rashi,
    is_retrograde: p.is_retrograde,
    rashi_degree: p.transit_rashi_degree,
  }));
}

function getTransitAscendant(transits: TransitResponse | null): AscendantPlacement | null {
  if (!transits) return null;
  return { rashi: transits.natal_moon_rashi };
}

function resolveChart(
  ctx: ChartContext,
  chart: D1ChartResponse,
  vargas: AllVargaChartsResponse | null,
  transits: TransitResponse | null,
): ResolvedChart | null {
  const vd = VARGA_DIVISORS[ctx.varga];
  const label = vd?.label ?? ctx.varga;

  if (ctx.source === "transit") {
    const tPlanets = getTransitPlanets(transits);
    const tAsc = getTransitAscendant(transits);
    if (!tPlanets || !tAsc) return null;
    return {
      title: `Transit — ${label}`,
      ascendant: tAsc,
      planets: tPlanets,
      isVarga: ctx.varga !== "D1",
      vargaDivisor: vd?.divisor,
    };
  }

  if (ctx.varga === "D1") {
    return {
      title: `D1 — ${label}`,
      ascendant: { rashi: chart.ascendant.rashi, rashi_degree: chart.ascendant.rashi_degree },
      planets: chart.planets.map((p) => ({
        planet: p.planet,
        rashi: p.rashi,
        house_number: p.house_number,
        is_retrograde: p.is_retrograde,
        rashi_degree: p.rashi_degree,
      })),
      isVarga: false,
    };
  }

  const vPlanets = getVargaPlanets(vargas, ctx.varga);
  if (!vPlanets) return null;
  return {
    title: `${ctx.varga} — ${label}`,
    ascendant: getVargaAscendant(vargas, ctx.varga, {
      rashi: chart.ascendant.rashi,
      rashi_degree: chart.ascendant.rashi_degree,
    }),
    planets: vPlanets,
    isVarga: true,
    vargaDivisor: vd?.divisor,
  };
}

export default function VargaExplorer({
  chart,
  vargas,
  transits,
  selectedVarga,
  setSelectedVarga,
}: Props) {
  const [mode, setMode] = useState<ExplorerMode>("single");
  const [chartA, setChartA] = useState<ChartContext>({ source: "natal", varga: "D1" });
  const [chartB, setChartB] = useState<ChartContext>({ source: "natal", varga: "D9" });
  const [gridSlots, setGridSlots] = useState<ChartContext[]>([
    { source: "natal", varga: "D1" },
    { source: "natal", varga: "D9" },
    { source: "natal", varga: "D10" },
    { source: "transit", varga: "D1" },
  ]);

  const vargaKeys = useMemo(
    () =>
      ["D1", ...Object.keys(vargas?.charts ?? {})].filter(
        (k, i, arr) => arr.indexOf(k) === i && !!VARGA_DIVISORS[k],
      ),
    [vargas],
  );

  const hasTransit = !!transits;
  const sourceOptions = [
    { value: "natal", label: "Natal" },
    ...(hasTransit ? [{ value: "transit", label: "Transit" }] : []),
  ];
  const vargaOptions = vargaKeys.map((vk) => ({
    value: vk,
    label: VARGA_DIVISORS[vk]?.label ?? vk,
  }));

  // Single mode
  const singlePlanets = useMemo(() => {
    if (selectedVarga === "D1") {
      return chart.planets.map((p) => ({
        planet: p.planet,
        rashi: p.rashi,
        house_number: p.house_number,
        is_retrograde: p.is_retrograde,
        rashi_degree: p.rashi_degree,
      }));
    }
    return getVargaPlanets(vargas, selectedVarga);
  }, [chart, vargas, selectedVarga]);

  const singleAscendant = useMemo(
    () =>
      getVargaAscendant(vargas, selectedVarga, {
        rashi: chart.ascendant.rashi,
        rashi_degree: chart.ascendant.rashi_degree,
      }),
    [chart, vargas, selectedVarga],
  );

  const retroByPlanet = useMemo<Record<string, boolean>>(() => {
    const vc = vargas?.charts[selectedVarga];
    if (!vc) return {};
    return Object.fromEntries(
      vc.planet_positions.map((p) => [p.planet, p.is_retrograde]),
    );
  }, [vargas, selectedVarga]);

  // Mixed 2
  const resolvedA = useMemo(
    () => resolveChart(chartA, chart, vargas, transits),
    [chartA, chart, vargas, transits],
  );
  const resolvedB = useMemo(
    () => resolveChart(chartB, chart, vargas, transits),
    [chartB, chart, vargas, transits],
  );

  const handleSwap = () => {
    setChartA(chartB);
    setChartB(chartA);
  };

  // Grid
  const resolvedGrid = useMemo(
    () => gridSlots.map((ctx) => ({ ctx, resolved: resolveChart(ctx, chart, vargas, transits) })),
    [gridSlots, chart, vargas, transits],
  );

  const handleGridSlotChange = (index: number, patch: Partial<ChartContext>) => {
    setGridSlots((prev) =>
      prev.map((ctx, i) => (i === index ? { ...ctx, ...patch } : ctx)),
    );
  };

  const renderContextSelector = (
    label: string,
    ctx: ChartContext,
    onChange: (next: ChartContext) => void,
    accentColor: string,
  ) => (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: accentColor }}>
        {label}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <select
          className="field-input"
          style={{ width: "auto", minWidth: 110 }}
          value={ctx.source}
          onChange={(e) => onChange({ ...ctx, source: e.target.value as ChartSource })}
          aria-label={`${label} source`}
        >
          {sourceOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select
          className="field-input"
          style={{ width: "auto", minWidth: 160 }}
          value={ctx.varga}
          onChange={(e) => onChange({ ...ctx, varga: e.target.value })}
          aria-label={`${label} varga`}
        >
          {vargaOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>
    </div>
  );

  const renderChartCard = (
    resolved: ResolvedChart | null,
    ctx: ChartContext,
    accentColor: string,
  ) => {
    if (!resolved) {
      return (
        <div
          className="glass-card flex flex-col items-center justify-center p-6 text-sm"
          style={{ color: "var(--text-secondary)", minHeight: 300 }}
        >
          {ctx.source === "transit"
            ? "Transit data not available for this chart."
            : "Divisional chart not computed (vargas unchecked at input time)."}
        </div>
      );
    }

    return (
      <div className="glass-card flex flex-col items-center p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide" style={{ color: accentColor }}>
          {resolved.title}
        </h2>
        <NorthIndianChart
          title={resolved.title}
          ascendant={resolved.ascendant}
          planets={resolved.planets}
          size={340}
          isVarga={resolved.isVarga}
          vargaDivisor={resolved.vargaDivisor}
        />
        <div
          className="mt-4 w-full rounded-lg border p-3"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Ascendant</p>
          <p className="font-semibold" style={{ color: accentColor }}>
            {resolved.ascendant.rashi}{" "}
            <span className="font-normal" style={{ color: "var(--text-secondary)" }}>
              {resolved.ascendant.rashi_degree?.toFixed(2)}°
            </span>
          </p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Lord: {rashiLordFromApiName(resolved.ascendant.rashi) ?? "—"}
          </p>
        </div>
      </div>
    );
  };

  const singleColumns: TableColumn<PlanetPlacement>[] = [
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

  const modeTabs: { key: ExplorerMode; label: string; help: string }[] = [
    { key: "single", label: "Single Varga", help: "Explore one divisional chart at a time with its guide and planetary positions." },
    { key: "mixed", label: "Mixed 2", help: "Compare two chart contexts side by side — any varga, natal or transit, independently." },
    { key: "grid", label: "Grid", help: "View up to four chart contexts in a research grid." },
  ];
  const activeModeHelp = modeTabs.find((t) => t.key === mode)?.help ?? "";

  const presets = [
    { label: "D1 + D9", a: { source: "natal" as const, varga: "D1" }, b: { source: "natal" as const, varga: "D9" } },
    { label: "D1 + D10", a: { source: "natal" as const, varga: "D1" }, b: { source: "natal" as const, varga: "D10" } },
    { label: "D1 + D7", a: { source: "natal" as const, varga: "D1" }, b: { source: "natal" as const, varga: "D7" } },
    { label: "D1 + D12", a: { source: "natal" as const, varga: "D1" }, b: { source: "natal" as const, varga: "D12" } },
    { label: "D9 + D10", a: { source: "natal" as const, varga: "D9" }, b: { source: "natal" as const, varga: "D10" } },
    { label: "D60 + D1", a: { source: "natal" as const, varga: "D60" }, b: { source: "natal" as const, varga: "D1" } },
    ...(hasTransit
      ? [
          { label: "D1 + Transit", a: { source: "natal" as const, varga: "D1" }, b: { source: "transit" as const, varga: "D1" } },
          { label: "D9 + Transit", a: { source: "natal" as const, varga: "D9" }, b: { source: "transit" as const, varga: "D1" } },
          { label: "D10 + Transit", a: { source: "natal" as const, varga: "D10" }, b: { source: "transit" as const, varga: "D1" } },
        ]
      : []),
  ];

  return (
    <div className="space-y-4">
      {/* Mode selector */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            Varga Explorer
          </h3>
          <div className="flex gap-1" role="tablist" aria-label="Varga Explorer view modes">
            {modeTabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                role="tab"
                aria-selected={mode === tab.key}
                aria-controls={`varga-panel-${tab.key}`}
                onClick={() => setMode(tab.key)}
                className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
                style={{
                  backgroundColor: mode === tab.key ? "var(--accent)" : "transparent",
                  color: mode === tab.key ? "var(--accent-text)" : "var(--text-secondary)",
                  border: `1px solid ${mode === tab.key ? "var(--accent)" : "var(--border-primary)"}`,
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>{activeModeHelp}</p>
      </div>

      {/* Single Varga */}
      {mode === "single" && (
        <div id="varga-panel-single" role="tabpanel" aria-label="Single Varga panel" className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="glass-card flex flex-col items-center p-6">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
              {selectedVarga} — {VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}
            </h2>
            {singlePlanets ? (
              <NorthIndianChart
                title={`${selectedVarga} — ${VARGA_DIVISORS[selectedVarga]?.label ?? "Chart"}`}
                ascendant={singleAscendant}
                planets={singlePlanets}
                size={380}
                isVarga={selectedVarga !== "D1"}
                vargaDivisor={VARGA_DIVISORS[selectedVarga]?.divisor}
              />
            ) : (
              <div className="flex flex-col items-center justify-center p-6 text-sm" style={{ color: "var(--text-secondary)", minHeight: 300 }}>
                Divisional charts were not computed for this chart (vargas unchecked at input time).
              </div>
            )}
            <div className="mt-4 w-full rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Ascendant</p>
              <p className="font-semibold" style={{ color: "var(--accent)" }}>
                {singleAscendant.rashi}{" "}
                <span className="font-normal" style={{ color: "var(--text-secondary)" }}>
                  {singleAscendant.rashi_degree?.toFixed(2)}°
                </span>
              </p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                Lord: {rashiLordFromApiName(singleAscendant.rashi) ?? "—"}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="glass-card p-4">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Varga</h3>
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
                        border: `1px solid ${isActive ? "var(--accent)" : "var(--border-primary)"}`,
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
            {singlePlanets && (
              <div className="glass-card p-4">
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Planet Positions</h3>
                <Table columns={singleColumns} rows={singlePlanets} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mixed 2 */}
      {mode === "mixed" && (
        <div id="varga-panel-mixed" role="tabpanel" aria-label="Mixed 2 Varga panel" className="space-y-4">
          <div className="glass-card p-4">
            <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-end">
              <div>{renderContextSelector("Chart A", chartA, setChartA, "var(--cyan-400)")}</div>
              <div className="flex items-center justify-center pb-1">
                <button
                  type="button"
                  onClick={handleSwap}
                  className="rounded-lg px-3 py-2 text-xs font-semibold transition"
                  style={{ backgroundColor: "var(--bg-surface-700)", color: "var(--text-secondary)", border: "1px solid var(--border-primary)" }}
                  aria-label="Swap Chart A and Chart B"
                  title="Swap charts"
                >
                  ⇄ Swap
                </button>
              </div>
              <div>{renderContextSelector("Chart B", chartB, setChartB, "var(--gold-400)")}</div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {renderChartCard(resolvedA, chartA, "var(--cyan-400)")}
            {renderChartCard(resolvedB, chartB, "var(--gold-400)")}
          </div>

          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Quick Presets</h3>
            <div className="flex flex-wrap gap-1.5">
              {presets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => { setChartA(preset.a); setChartB(preset.b); }}
                  className="rounded-full px-2.5 py-1 text-xs font-semibold transition"
                  style={{ backgroundColor: "var(--bg-card)", color: "var(--text-secondary)", border: "1px solid var(--border-primary)" }}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Grid */}
      {mode === "grid" && (
        <div id="varga-panel-grid" role="tabpanel" aria-label="Varga Grid panel" className="space-y-4">
          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>Grid Slots</h3>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {gridSlots.map((slot, i) => (
                <div key={i} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                  <p className="mb-2 text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Slot {i + 1}</p>
                  <div className="flex flex-col gap-2">
                    <select
                      className="field-input"
                      value={slot.source}
                      onChange={(e) => handleGridSlotChange(i, { source: e.target.value as ChartSource })}
                      aria-label={`Slot ${i + 1} source`}
                    >
                      {sourceOptions.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                    <select
                      className="field-input"
                      value={slot.varga}
                      onChange={(e) => handleGridSlotChange(i, { varga: e.target.value })}
                      aria-label={`Slot ${i + 1} varga`}
                    >
                      {vargaOptions.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {resolvedGrid.map(({ ctx, resolved }, i) => (
              <div key={i}>
                {renderChartCard(resolved, ctx, i % 2 === 0 ? "var(--cyan-400)" : "var(--gold-400)")}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}