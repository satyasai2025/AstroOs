"use client";

import { useEffect, useMemo, useState } from "react";
import { PLANETS, PLANET_SYMBOLS, PLANET_ABBREV, rashiLordFromApiName } from "@/lib/astro";
import { StrengthProgressBar } from "@/components/charts/StrengthProgressBar";
import { Tabs, type TabItem } from "@/components/ui/Tabs";
import type { WorkflowAnalysisRequest, WorkflowAnalysisResponse } from "@/lib/types";
import { resolvePlanetContext } from "./planetExplorer/context";
import { OverviewTab } from "./planetExplorer/OverviewTab";
import { StructureTab } from "./planetExplorer/StructureTab";
import { StrengthTab } from "./planetExplorer/StrengthTab";
import { RelationshipsTab } from "./planetExplorer/RelationshipsTab";
import { YogasTab } from "./planetExplorer/YogasTab";
import { DashaTab } from "./planetExplorer/DashaTab";
import { TransitTab } from "./planetExplorer/TransitTab";
import { TimelineTab } from "./planetExplorer/TimelineTab";
import { InterpretationTab } from "./planetExplorer/InterpretationTab";

export type PlanetExplorerTab =
  | "overview"
  | "structure"
  | "strength"
  | "relationships"
  | "yogas"
  | "dasha"
  | "transit"
  | "timeline"
  | "interpretation";

const TABS: TabItem[] = [
  { key: "overview", label: "Overview" },
  { key: "structure", label: "Structure" },
  { key: "strength", label: "Strength" },
  { key: "relationships", label: "Relationships" },
  { key: "yogas", label: "Yogas" },
  { key: "dasha", label: "Dasha" },
  { key: "transit", label: "Transit" },
  { key: "timeline", label: "Timeline" },
  { key: "interpretation", label: "Interpretation" },
];

function StatusChip({ label, active }: { label: string; active: boolean }) {
  if (!active) return null;
  return (
    <span
      className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
      style={{ backgroundColor: "rgba(244,63,94,0.14)", color: "#f87171", border: "1px solid rgba(244,63,94,0.3)" }}
    >
      {label}
    </span>
  );
}

interface Props {
  result: WorkflowAnalysisResponse;
  request: WorkflowAnalysisRequest | null;
  /** Planet pinned/selected in the shared chart; null → defaults to Lagna lord. */
  selectedPlanet?: string | null;
  /** Mirrors the chart-workspace click-to-pin. */
  onSelectPlanet?: (planet: string) => void;
}

export default function PlanetExplorerPanel({ result, request, selectedPlanet, onSelectPlanet }: Props) {
  const [internal, setInternal] = useState<string | null>(null);
  const [tab, setTab] = useState<PlanetExplorerTab>("overview");

  // Keep internal selection in sync when the outer chart pins a planet.
  useEffect(() => {
    if (selectedPlanet) setInternal(selectedPlanet);
  }, [selectedPlanet]);

  const defaultPlanet = useMemo(() => {
    const lord = rashiLordFromApiName(result.chart.ascendant.rashi);
    if (lord && result.chart.planets.some((p) => p.planet === lord)) return lord;
    return "Moon";
  }, [result]);

  const selected = selectedPlanet ?? internal ?? defaultPlanet;
  const ctx = useMemo(() => resolvePlanetContext(selected, result), [selected, result]);
  const position = ctx.position;

  const choose = (planet: string) => {
    setInternal(planet);
    onSelectPlanet?.(planet);
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
        <div className="flex items-center gap-3">
          <span className="text-3xl" style={{ color: "var(--accent)" }}>{PLANET_SYMBOLS[selected] ?? ""}</span>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{selected}</h2>
              {position?.is_retrograde && (
                <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" style={{ backgroundColor: "rgba(244,63,94,0.14)", color: "#f87171" }}>
                  Retrograde
                </span>
              )}
              {position?.is_combust && (
                <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" style={{ backgroundColor: "rgba(240,192,90,0.16)", color: "#fbbf24" }}>
                  Combust
                </span>
              )}
            </div>
            <p className="mt-0.5 text-sm capitalize" style={{ color: "var(--text-secondary)" }}>
              {position
                ? `${position.rashi} ${position.rashi_degree.toFixed(2)}° · ${position.nakshatra} · Pada ${position.pada} · Bhava ${position.house_number}`
                : request?.subject_name ?? "Chart"}
            </p>
          </div>
        </div>
        {ctx.strength ? (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Structural Strength</p>
              <p className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                {ctx.strength.score}% <span className="font-normal capitalize" style={{ color: "var(--text-secondary)" }}>({ctx.strength.band})</span>
              </p>
            </div>
            <div className="w-40"><StrengthProgressBar score={ctx.strength.score} size="md" showLabel={false} /></div>
          </div>
        ) : (
          <StatusChip label="Strength unavailable" active />
        )}
      </div>

      {/* Selector */}
      <div className="flex flex-wrap gap-1" role="tablist" aria-label="Select a planet">
        {PLANETS.map((planet) => {
          const present = result.chart.planets.some((p) => p.planet === planet);
          const isActive = selected === planet;
          return (
            <button
              key={planet}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => choose(planet)}
              className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
              style={{
                backgroundColor: isActive ? "var(--accent)" : "transparent",
                color: isActive ? "var(--accent-text)" : present ? "var(--text-secondary)" : "var(--text-muted)",
                border: "1px solid " + (isActive ? "var(--accent)" : "var(--border-primary)"),
                opacity: present ? 1 : 0.45,
              }}
              title={present ? `${planet} in ${result.chart.planets.find((p) => p.planet === planet)?.rashi ?? ""}` : `${planet} not placed`}
            >
              {PLANET_SYMBOLS[planet]} <span className="ml-0.5">{PLANET_ABBREV[planet] ?? planet}</span>
            </button>
          );
        })}
      </div>

      {/* Tab bar */}
      <div className="border-b" style={{ borderColor: "var(--border-primary)" }}>
        <Tabs tabs={TABS} active={tab} onChange={(k) => setTab(k as PlanetExplorerTab)} />
      </div>

      {/* Active tab */}
      <div>
        {tab === "overview" && <OverviewTab ctx={ctx} />}
        {tab === "structure" && <StructureTab ctx={ctx} result={result} />}
        {tab === "strength" && <StrengthTab ctx={ctx} result={result} />}
        {tab === "relationships" && <RelationshipsTab ctx={ctx} result={result} />}
        {tab === "yogas" && <YogasTab ctx={ctx} result={result} />}
        {tab === "dasha" && <DashaTab ctx={ctx} result={result} />}
        {tab === "transit" && <TransitTab ctx={ctx} result={result} />}
        {tab === "timeline" && <TimelineTab ctx={ctx} result={result} />}
        {tab === "interpretation" && <InterpretationTab ctx={ctx} onFocusTab={setTab} />}
      </div>
    </div>
  );
}