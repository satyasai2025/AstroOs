"use client";

import { useMemo, useState } from "react";
import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import {
  useShadbalaAll,
  type SaravaliPlanetSummary,
  type BalaComponent,
  NAISARGIKA_BALA_TABLE,
  SARAVALI_REQUIRED_VIRUPAS,
  SARAVALI_REQUIRED_RUPAS,
} from "@/lib/shadbala";
import type { WorkflowAnalysisRequest } from "@/lib/types";
import { getShadbalaInterpretation } from "@/lib/shadbalaInterpretation";

interface SaravaliShadbalaSuiteProps {
  request: WorkflowAnalysisRequest | null;
  activePlanet?: string | null;
  onPlanetSelect?: (planet: string) => void;
}

type SubTab =
  | "summary"
  | "sthana"
  | "dig"
  | "kala"
  | "cheshta"
  | "naisargika"
  | "drig"
  | "ishta_kashta"
  | "reference";

const TABS: { key: SubTab; label: string; number?: string }[] = [
  { key: "summary", label: "Bala Summary" },
  { key: "sthana", label: "Sthana Bala", number: "1" },
  { key: "dig", label: "Dig Bala", number: "2" },
  { key: "kala", label: "Kala Bala", number: "3" },
  { key: "cheshta", label: "Cheshta Bala", number: "4" },
  { key: "naisargika", label: "Naisargika Bala", number: "5" },
  { key: "drig", label: "Drig Bala", number: "6" },
  { key: "ishta_kashta", label: "Ishta / Kashta" },
  { key: "reference", label: "Classical Texts (Saravali Ch. 27)" },
];

const PLANET_COLORS: Record<string, string> = {
  sun: "#F59E0B",
  moon: "#38BDF8",
  mars: "#EF4444",
  mercury: "#10B981",
  jupiter: "#EAB308",
  venus: "#EC4899",
  saturn: "#6366F1",
};

export function SaravaliShadbalaSuite({
  request,
  activePlanet: externalActivePlanet,
  onPlanetSelect,
}: SaravaliShadbalaSuiteProps) {
  const [activeTab, setActiveTab] = useState<SubTab>("summary");
  const [internalSelectedPlanet, setInternalSelectedPlanet] = useState<string>("sun");
  const [ayanaMethod, setAyanaMethod] = useState<"kranti" | "khandas" | "length">("kranti");

  const { data: shadbalaAll, isLoading, isError, error } = useShadbalaAll(request);

  const selectedPlanet = (externalActivePlanet?.toLowerCase() || internalSelectedPlanet).toLowerCase();

  const handleSelectPlanet = (p: string) => {
    setInternalSelectedPlanet(p.toLowerCase());
    onPlanetSelect?.(p.charAt(0).toUpperCase() + p.slice(1));
  };

  const report = shadbalaAll?.summary ?? null;
  const planetsList = useMemo(() => report?.planets ?? [], [report]);

  const selectedPlanetSummary = useMemo(() => {
    return planetsList.find((p) => p.planet.toLowerCase() === selectedPlanet) ?? planetsList[0] ?? null;
  }, [planetsList, selectedPlanet]);

  if (isLoading) {
    return (
      <div className="glass-card flex flex-col items-center justify-center p-12 text-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-current border-t-transparent text-accent" />
        <p className="mt-3 text-sm" style={{ color: "var(--text-secondary)" }}>
          Calculating Six-Fold Shadbala strengths according to Saravali &amp; BPHS...
        </p>
      </div>
    );
  }

  if (isError || !shadbalaAll) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        <p className="font-semibold text-rose-400">Unable to calculate complete Shadbala</p>
        <p className="mt-1 text-xs">{error instanceof Error ? error.message : "Ensure birth details are provided."}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="glass-card p-4">
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
            Chart Strength Index
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>
              {report?.chart_strength_score ?? "—"}
            </span>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              / 100
            </span>
          </div>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            Mean ratio: {report ? `${(report.average_strength_ratio * 100).toFixed(0)}% of required` : "—"}
          </p>
        </div>

        <div className="glass-card p-4">
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#10B981" }}>
            Strongest Graha
          </span>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
              {report?.strongest_planet ? `${PLANET_SYMBOLS[report.strongest_planet] ?? ""} ${report.strongest_planet}` : "—"}
            </span>
          </div>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            {planetsList[0] ? `${planetsList[0].total_rupas.toFixed(2)} Rupas (${planetsList[0].percentage}%)` : "—"}
          </p>
        </div>

        <div className="glass-card p-4">
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#EF4444" }}>
            Weakest Graha
          </span>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
              {report?.weakest_planet ? `${PLANET_SYMBOLS[report.weakest_planet] ?? ""} ${report.weakest_planet}` : "—"}
            </span>
          </div>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            {planetsList[planetsList.length - 1]
              ? `${planetsList[planetsList.length - 1].total_rupas.toFixed(2)} Rupas (${planetsList[planetsList.length - 1].percentage}%)`
              : "—"}
          </p>
        </div>

        <div className="glass-card p-4">
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
            Requirement Fulfillment
          </span>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-3xl font-bold" style={{ color: "var(--text-primary)" }}>
              {planetsList.filter((p) => p.is_strong).length}
            </span>
            <span className="text-sm font-normal" style={{ color: "var(--text-muted)" }}>
              / 7 grahas passed
            </span>
          </div>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
            BPHS Ch. 27 &amp; Saravali Standard
          </p>
        </div>
      </div>

      {/* Planet Selector Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl p-2" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="px-2 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
            Select Planet:
          </span>
          {["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"].map((p) => {
            const pSummary = planetsList.find((item) => item.planet === p);
            const isSelected = selectedPlanet === p;
            const pName = p.charAt(0).toUpperCase() + p.slice(1);
            return (
              <button
                key={p}
                type="button"
                onClick={() => handleSelectPlanet(p)}
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition"
                style={{
                  backgroundColor: isSelected ? "var(--accent)" : "transparent",
                  color: isSelected ? "var(--accent-text)" : "var(--text-secondary)",
                  border: isSelected ? "1px solid var(--accent)" : "1px solid transparent",
                }}
              >
                <span>{PLANET_SYMBOLS[pName] ?? ""}</span>
                <span>{pName}</span>
                {pSummary && (
                  <span
                    className="ml-1 rounded px-1.5 py-0.2 text-[10px] font-bold"
                    style={{
                      backgroundColor: pSummary.is_strong ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                      color: pSummary.is_strong ? "#10B981" : "#EF4444",
                    }}
                  >
                    {pSummary.total_rupas.toFixed(1)} R
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Tab Navigation */}
      <div className="flex flex-wrap gap-1 border-b pb-2" style={{ borderColor: "var(--border-primary)" }} role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition"
            style={{
              backgroundColor: activeTab === tab.key ? "var(--accent)" : "transparent",
              color: activeTab === tab.key ? "var(--accent-text)" : "var(--text-secondary)",
            }}
          >
            {tab.number && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold" style={{ backgroundColor: activeTab === tab.key ? "rgba(0,0,0,0.2)" : "var(--bg-card)" }}>
                {tab.number}
              </span>
            )}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* TAB CONTENT: 1. SUMMARY */}
      {activeTab === "summary" && (
        <div className="space-y-6">
          {/* Complete Total Shadbala Table */}
          <div className="glass-card overflow-x-auto p-5">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
                  Total Shadbala Pinda &amp; Minimum Requirements (BPHS Ch. 27 / Saravali)
                </h3>
                <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
                  1 Rupa = 60 Virupas. Total Shadbala is the sum of Sthana, Dig, Kala, Cheshta, Naisargika, and Drig Balas.
                </p>
              </div>
            </div>

            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                  <th className="pb-2.5 pr-2">Rank</th>
                  <th className="pb-2.5 pr-3">Graha</th>
                  <th className="pb-2.5 pr-3 text-right">Total Virupas</th>
                  <th className="pb-2.5 pr-3 text-right">Total Rupas</th>
                  <th className="pb-2.5 pr-3 text-right">Req. (Rupas)</th>
                  <th className="pb-2.5 pr-3 text-right">Req. (Virupas)</th>
                  <th className="pb-2.5 pr-3 text-right">Ratio</th>
                  <th className="pb-2.5 pr-3 text-center">Fulfillment</th>
                  <th className="pb-2.5 pr-3">Status</th>
                  <th className="pb-2.5">Sub-Bala Check</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                {planetsList.map((p) => {
                  const isSelected = p.planet.toLowerCase() === selectedPlanet;
                  return (
                    <tr
                      key={p.planet}
                      onClick={() => handleSelectPlanet(p.planet)}
                      className="cursor-pointer transition hover:bg-white/5"
                      style={{
                        backgroundColor: isSelected ? "rgba(var(--accent-rgb, 99, 102, 241), 0.08)" : undefined,
                      }}
                    >
                      <td className="py-2.5 pr-2 font-bold" style={{ color: "var(--text-muted)" }}>
                        #{p.rank}
                      </td>
                      <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                        <span className="mr-1.5">{PLANET_SYMBOLS[p.planet_display_name] ?? ""}</span>
                        {p.planet_display_name}
                      </td>
                      <td className="py-2.5 pr-3 text-right font-mono font-medium" style={{ color: "var(--text-primary)" }}>
                        {p.total_virupas.toFixed(2)}
                      </td>
                      <td className="py-2.5 pr-3 text-right font-mono font-bold" style={{ color: "var(--accent)" }}>
                        {p.total_rupas.toFixed(2)}
                      </td>
                      <td className="py-2.5 pr-3 text-right font-mono" style={{ color: "var(--text-muted)" }}>
                        {p.required_rupas.toFixed(1)}
                      </td>
                      <td className="py-2.5 pr-3 text-right font-mono" style={{ color: "var(--text-muted)" }}>
                        {p.required_virupas.toFixed(0)}
                      </td>
                      <td className="py-2.5 pr-3 text-right font-mono font-bold" style={{ color: p.is_strong ? "#10B981" : "#EF4444" }}>
                        {p.strength_ratio.toFixed(2)}×
                      </td>
                      <td className="py-2.5 pr-3">
                        <div className="flex items-center gap-2">
                          <div className="h-2 w-20 overflow-hidden rounded-full" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${Math.min(100, p.percentage / 1.5)}%`,
                                backgroundColor: p.is_strong ? "#10B981" : "#EF4444",
                              }}
                            />
                          </div>
                          <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>
                            {p.percentage}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-3">
                        <span
                          className="inline-block rounded-full px-2 py-0.5 text-xs font-semibold"
                          style={{
                            backgroundColor: p.is_strong ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                            color: p.is_strong ? "#10B981" : "#EF4444",
                          }}
                        >
                          {p.status_label}
                        </span>
                      </td>
                      <td className="py-2.5 text-xs">
                        {p.all_sub_balas_passed ? (
                          <span className="font-medium text-emerald-400">✓ All 5 Sub-Balas Passed</span>
                        ) : (
                          <span className="text-amber-400">
                            {p.sub_bala_checks.filter((c) => c.passed).length} / 5 Passed
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Individual Sub-Bala Requirements Matrix (Saravali Chapter 27) */}
          <div className="glass-card overflow-x-auto p-5">
            <div className="mb-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
                Individual Sub-Bala Requirements Matrix (Virupas)
              </h3>
              <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
                Classical criteria from Saravali Ch. 27. Each planet must meet its group requirement across individual sources.
              </p>
            </div>

            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                  <th className="pb-2 pr-3">Planet</th>
                  <th className="pb-2 pr-3 text-center">Sthana Bala</th>
                  <th className="pb-2 pr-3 text-center">Dig Bala</th>
                  <th className="pb-2 pr-3 text-center">Kala Bala</th>
                  <th className="pb-2 pr-3 text-center">Cheshta Bala</th>
                  <th className="pb-2 pr-3 text-center">Ayana Bala</th>
                  <th className="pb-2 text-center">Overall Compliance</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                {planetsList.map((p) => {
                  const checkMap = Object.fromEntries(p.sub_bala_checks.map((c) => [c.bala_key, c]));
                  return (
                    <tr key={p.planet} className="hover:bg-white/5">
                      <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                        {PLANET_SYMBOLS[p.planet_display_name] ?? ""} {p.planet_display_name}
                      </td>
                      {["sthana_bala", "dig_bala", "kala_bala", "chesta_bala", "ayana_bala"].map((key) => {
                        const check = checkMap[key];
                        if (!check) return <td key={key} className="py-2 text-center">—</td>;
                        return (
                          <td key={key} className="py-2.5 pr-3 text-center">
                            <div className="inline-flex flex-col items-center">
                              <span className="font-mono text-xs font-semibold" style={{ color: check.passed ? "#10B981" : "#EF4444" }}>
                                {check.obtained_virupas.toFixed(1)} / {check.required_virupas}
                              </span>
                              <span className="text-[10px]" style={{ color: check.passed ? "var(--text-muted)" : "#EF4444" }}>
                                {check.passed ? "✓ Passed" : "✗ Deficient"}
                              </span>
                            </div>
                          </td>
                        );
                      })}
                      <td className="py-2.5 text-center">
                        <span
                          className="rounded-full px-2 py-0.5 text-xs font-semibold"
                          style={{
                            backgroundColor: p.all_sub_balas_passed ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                            color: p.all_sub_balas_passed ? "#10B981" : "#EF4444",
                          }}
                        >
                          {p.all_sub_balas_passed ? "Fully Satisfied" : "Partial"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Dasha & Transit Interpretations (downstream from canonical facts) */}
          {selectedPlanetSummary && (() => {
            const interp = getShadbalaInterpretation(selectedPlanetSummary);
            return (
            <div className="glass-card p-5">
              <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
                <div className="flex items-center gap-2">
                  <span className="text-xl">{PLANET_SYMBOLS[selectedPlanetSummary.planet_display_name] ?? ""}</span>
                  <h3 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                    {selectedPlanetSummary.planet_display_name} — Classical Dasha &amp; Transit Impact
                  </h3>
                </div>
                <span
                  className="rounded-full px-3 py-1 text-xs font-bold"
                  style={{
                    backgroundColor: selectedPlanetSummary.is_strong ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                    color: selectedPlanetSummary.is_strong ? "#10B981" : "#F59E0B",
                  }}
                >
                  {interp.auspiciousness}
                </span>
              </div>
              <p className="mt-3 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {interp.dashaInterpretation}
              </p>
              <p className="mt-2 text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
                {interp.transitImpact}
              </p>
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-card)" }}>
                  <span style={{ color: "var(--text-muted)" }}>Total Strength:</span>
                  <p className="mt-0.5 font-bold" style={{ color: "var(--accent)" }}>
                    {selectedPlanetSummary.total_rupas.toFixed(2)} Rupas ({selectedPlanetSummary.total_virupas.toFixed(1)} V)
                  </p>
                </div>
                <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-card)" }}>
                  <span style={{ color: "var(--text-muted)" }}>Ishta Bala (Benefic):</span>
                  <p className="mt-0.5 font-bold text-emerald-400">
                    {selectedPlanetSummary.ishta_bala_virupas.toFixed(2)} Virupas
                  </p>
                </div>
                <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-card)" }}>
                  <span style={{ color: "var(--text-muted)" }}>Kashta Bala (Difficult):</span>
                  <p className="mt-0.5 font-bold text-rose-400">
                    {selectedPlanetSummary.kashta_bala_virupas.toFixed(2)} Virupas
                  </p>
                </div>
                <div className="rounded-lg p-2.5" style={{ backgroundColor: "var(--bg-card)" }}>
                  <span style={{ color: "var(--text-muted)" }}>Strength Ratio:</span>
                  <p className="mt-0.5 font-bold" style={{ color: selectedPlanetSummary.is_strong ? "#10B981" : "#EF4444" }}>
                    {selectedPlanetSummary.strength_ratio.toFixed(2)}× Required
                  </p>
                </div>
              </div>
            </div>
          );
          })()}
        </div>
      )}

      {/* TAB CONTENT: 1. STHANA BALA */}
      {activeTab === "sthana" && (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
              1. Sthana Bala (Positional Strength)
            </h3>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Sthana Bala is the strength derived from planetary zodiacal positions across signs, houses, and divisional charts. It consists of 5 sub-balas: Uchcha, Saptavargaja, Ojhajugmariamsa, Kendradi, and Drekkana.
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Planet</th>
                    <th className="pb-2 pr-3 text-right">Uchcha (Exaltation)</th>
                    <th className="pb-2 pr-3 text-right">Saptavargaja (7 Vargas)</th>
                    <th className="pb-2 pr-3 text-right">Ojhajugmariamsa (Odd/Even)</th>
                    <th className="pb-2 pr-3 text-right">Kendradi (Angles)</th>
                    <th className="pb-2 pr-3 text-right">Drekkana (Decanates)</th>
                    <th className="pb-2 text-right font-bold">Total Sthana Bala</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  {planetsList.map((p) => (
                    <tr key={p.planet} className="hover:bg-white/5">
                      <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                        {PLANET_SYMBOLS[p.planet_display_name] ?? ""} {p.planet_display_name}
                      </td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.uchcha_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.saptavargaja_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.ojayugmarasyamsa_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.kendradi_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.drekkana_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 text-right font-mono font-bold" style={{ color: "var(--accent)" }}>
                        {p.sthana_bala_virupas.toFixed(2)} V
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sthana Sub-components Classical Rules Cards */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="glass-card p-4 text-xs space-y-2">
              <h4 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                1.1 Uchcha Bala (Exaltation Strength)
              </h4>
              <p style={{ color: "var(--text-secondary)" }}>
                Measures the distance from deep debilitation point (Neecha). Maximum 60 Virupas at deep exaltation (Uchcha), 0 at deep debilitation.
              </p>
              <p className="font-mono" style={{ color: "var(--accent)" }}>
                Formula: (Distance from Deep Debilitation in degrees) / 3
              </p>
            </div>

            <div className="glass-card p-4 text-xs space-y-2">
              <h4 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                1.2 Saptavargaja Bala (7 Divisional Charts)
              </h4>
              <p style={{ color: "var(--text-secondary)" }}>
                Evaluates dignity in 7 Vargas (D1, D9, D2, D3, D7, D12, D30).
              </p>
              <div className="grid grid-cols-2 gap-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
                <span>Moolatrikona: 45 V</span>
                <span>Own Rasi: 30 V</span>
                <span>Great Friend: 20 V</span>
                <span>Friend: 15 V</span>
                <span>Neutral: 10 V</span>
                <span>Enemy: 4 V / Great Enemy: 2 V</span>
              </div>
            </div>

            <div className="glass-card p-4 text-xs space-y-2">
              <h4 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                1.3 Ojhajugmariamsa Bala (Odd / Even Signs &amp; Navamsas)
              </h4>
              <p style={{ color: "var(--text-secondary)" }}>
                Female planets (Moon, Venus) get 15 Virupas in even signs and 15 in even Navamsas (max 30). Male (Sun, Mars, Jupiter) and Neutral (Mercury, Saturn) get 15 in odd signs and 15 in odd Navamsas.
              </p>
            </div>

            <div className="glass-card p-4 text-xs space-y-2">
              <h4 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                1.4 Kendradi &amp; 1.5 Drekkana Bala
              </h4>
              <p style={{ color: "var(--text-secondary)" }}>
                <strong>Kendradi:</strong> Kendra houses (1, 4, 7, 10) = 60 V, Panaphara (2, 5, 8, 11) = 30 V, Apoklima (3, 6, 9, 12) = 15 V.
              </p>
              <p style={{ color: "var(--text-secondary)" }}>
                <strong>Drekkana:</strong> Male planets in 1st decanate (0°-10°) = 15 V; Female in 2nd (10°-20°) = 15 V; Neutral in 3rd (20°-30°) = 15 V.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: 2. DIG BALA */}
      {activeTab === "dig" && (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
              2. Dig Bala (Directional Strength)
            </h3>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Dig Bala measures a planet&apos;s strength based on its orientation relative to the 4 cardinal angular points (Kendras).
            </p>

            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <span className="font-bold text-xs uppercase text-amber-400">East / Ascendant (1st House)</span>
                <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Mercury &amp; Jupiter</p>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Gain 60 Virupas at Lagna cusp; 0 at 7th house.</p>
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <span className="font-bold text-xs uppercase text-sky-400">North / Nadir (4th House)</span>
                <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Moon &amp; Venus</p>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Gain 60 Virupas at 4th cusp; 0 at 10th house.</p>
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <span className="font-bold text-xs uppercase text-indigo-400">West / Descendant (7th House)</span>
                <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Saturn</p>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Gains 60 Virupas at 7th cusp; 0 at 1st house.</p>
              </div>

              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}>
                <span className="font-bold text-xs uppercase text-rose-400">South / Meridian (10th House)</span>
                <p className="mt-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Sun &amp; Mars</p>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Gain 60 Virupas at 10th cusp; 0 at 4th house.</p>
              </div>
            </div>

            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Graha</th>
                    <th className="pb-2 pr-3">Strongest Point</th>
                    <th className="pb-2 pr-3">Weakest Point (0 V)</th>
                    <th className="pb-2 pr-3 text-right">Dig Bala (Virupas)</th>
                    <th className="pb-2 pr-3 text-right">Dig Bala (Rupas)</th>
                    <th className="pb-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  {planetsList.map((p) => {
                    const digRupas = p.dig_bala_virupas / 60.0;
                    return (
                      <tr key={p.planet} className="hover:bg-white/5">
                        <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                          {PLANET_SYMBOLS[p.planet_display_name] ?? ""} {p.planet_display_name}
                        </td>
                        <td className="py-2.5 pr-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                          {p.planet === "sun" || p.planet === "mars"
                            ? "10th House (Meridian)"
                            : p.planet === "mercury" || p.planet === "jupiter"
                            ? "1st House (Ascendant)"
                            : p.planet === "moon" || p.planet === "venus"
                            ? "4th House (Nadir)"
                            : "7th House (Descendant)"}
                        </td>
                        <td className="py-2.5 pr-3 text-xs" style={{ color: "var(--text-muted)" }}>
                          {p.planet === "sun" || p.planet === "mars"
                            ? "4th House (Nadir)"
                            : p.planet === "mercury" || p.planet === "jupiter"
                            ? "7th House (Descendant)"
                            : p.planet === "moon" || p.planet === "venus"
                            ? "10th House (Meridian)"
                            : "1st House (Ascendant)"}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold" style={{ color: "var(--accent)" }}>
                          {p.dig_bala_virupas.toFixed(2)} V
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono" style={{ color: "var(--text-secondary)" }}>
                          {digRupas.toFixed(2)} R
                        </td>
                        <td className="py-2.5 text-right text-xs">
                          {p.dig_bala_virupas >= 30 ? (
                            <span className="font-semibold text-emerald-400">Directionally Strong</span>
                          ) : (
                            <span className="text-amber-400">Moderate</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: 3. KALA BALA */}
      {activeTab === "kala" && (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
              3. Kala Bala (Temporal Strength)
            </h3>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Temporal strength encompasses time-of-birth factors: Diurnal/Nocturnal (Nathonatha), Lunar phase (Paksha), Portions of day/night (Tribhaga), Time lords (Dina/Hora), Planetary war (Yudhdha), and Declination (Ayana).
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Graha</th>
                    <th className="pb-2 pr-3 text-right">Nathonatha</th>
                    <th className="pb-2 pr-3 text-right">Paksha</th>
                    <th className="pb-2 pr-3 text-right">Tribhaga</th>
                    <th className="pb-2 pr-3 text-right">Dina/Hora</th>
                    <th className="pb-2 pr-3 text-right">Ayana</th>
                    <th className="pb-2 pr-3 text-right">Yuddha</th>
                    <th className="pb-2 text-right font-bold">Total Kala Bala</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  {planetsList.map((p) => (
                    <tr key={p.planet} className="hover:bg-white/5">
                      <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                        {PLANET_SYMBOLS[p.planet_display_name] ?? ""} {p.planet_display_name}
                      </td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.nathonnata_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.paksha_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.tribhaga_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.dina_hora_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.ayana_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 pr-3 text-right font-mono">{p.yuddha_bala_virupas.toFixed(2)}</td>
                      <td className="py-2.5 text-right font-mono font-bold" style={{ color: "var(--accent)" }}>
                        {p.kala_bala_virupas.toFixed(2)} V
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Ayana Bala Classical Calculation Method Details */}
          <div className="glass-card p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h4 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                  3.6 Ayana Bala (Equinoctial / Declination Strength)
                </h4>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  Ayana Bala depends on planetary declination (Kranti) relative to the equator.
                </p>
              </div>

              <div className="flex rounded-lg p-1" style={{ backgroundColor: "var(--bg-card)" }}>
                <button
                  type="button"
                  onClick={() => setAyanaMethod("kranti")}
                  className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                    ayanaMethod === "kranti" ? "bg-accent text-accent-text" : "text-text-secondary"
                  }`}
                >
                  Method 1: Kranti (Declination)
                </button>
                <button
                  type="button"
                  onClick={() => setAyanaMethod("khandas")}
                  className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                    ayanaMethod === "khandas" ? "bg-accent text-accent-text" : "text-text-secondary"
                  }`}
                >
                  Method 2: Parasara Khandas
                </button>
                <button
                  type="button"
                  onClick={() => setAyanaMethod("length")}
                  className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                    ayanaMethod === "length" ? "bg-accent text-accent-text" : "text-text-secondary"
                  }`}
                >
                  Method 3: Tropical Length
                </button>
              </div>
            </div>

            <div className="mt-3 rounded-lg p-3 text-xs leading-relaxed" style={{ backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}>
              {ayanaMethod === "kranti" && (
                <div>
                  <p className="font-semibold text-emerald-400">Formula: Ayana Bala = 30 × (ε ± Kranti) / ε = 1.2793 × (ε ± Kranti)</p>
                  <p className="mt-1">
                    Where ε is obliquity (23.44°). Moon &amp; Saturn gain with Southern Kranti; Sun, Mars, Jupiter, Venus gain with Northern Kranti; Mercury gains with both.
                  </p>
                </div>
              )}
              {ayanaMethod === "khandas" && (
                <div>
                  <p className="font-semibold text-emerald-400">Parasara Hora Shastra Ch. 27 (15-17): 3 Khandas (45, 33, 12)</p>
                  <p className="mt-1">
                    Portions calculated from nearest equinox: 1st sign (0-30°) gets proportion of 45; 2nd sign (30-60°) gets 45 + proportion of 33; 3rd sign (60-90°) gets 78 + proportion of 12.
                  </p>
                </div>
              )}
              {ayanaMethod === "length" && (
                <div>
                  <p className="font-semibold text-emerald-400">Formula: Ayana Bala = 30 × (1 ± |sin(tropical longitude)|)</p>
                  <p className="mt-1">
                    Length-based calculation produces values virtually identical to Kranti declination (within 1-2 Virupas).
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: 4. CHESHTA BALA */}
      {activeTab === "cheshta" && (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
              4. Cheshta Bala (Motional Strength)
            </h3>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Measures the planetary effort and motional vigor. For the Sun, Cheshta Bala equals Ayana Bala. For the Moon, it equals Paksha Bala. For Mars, Mercury, Jupiter, Venus, and Saturn, it is evaluated across 8 classical motion types.
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Graha</th>
                    <th className="pb-2 pr-3">Motional Basis</th>
                    <th className="pb-2 pr-3 text-right">Cheshta Bala (Virupas)</th>
                    <th className="pb-2 pr-3 text-right">Cheshta Bala (Rupas)</th>
                    <th className="pb-2 text-right">State</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  {planetsList.map((p) => {
                    const cRupas = p.chesta_bala_virupas / 60.0;
                    return (
                      <tr key={p.planet} className="hover:bg-white/5">
                        <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                          {PLANET_SYMBOLS[p.planet_display_name] ?? ""} {p.planet_display_name}
                        </td>
                        <td className="py-2.5 pr-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                          {p.planet === "sun"
                            ? "Equal to Ayana Bala (Saravali Rule)"
                            : p.planet === "moon"
                            ? "Equal to Paksha Bala (Saravali Rule)"
                            : "Geocentric Motion & Velocity (8-Type Scale)"}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold" style={{ color: "var(--accent)" }}>
                          {p.chesta_bala_virupas.toFixed(2)} V
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono" style={{ color: "var(--text-secondary)" }}>
                          {cRupas.toFixed(2)} R
                        </td>
                        <td className="py-2.5 text-right text-xs">
                          {p.chesta_bala_virupas >= 45 ? (
                            <span className="font-semibold text-emerald-400">High Motional Force</span>
                          ) : p.chesta_bala_virupas >= 25 ? (
                            <span className="text-amber-400">Moderate</span>
                          ) : (
                            <span className="text-rose-400">Low Motion</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 8 Types of Motion Table according to Saravali */}
          <div className="glass-card p-5">
            <h4 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
              The 8 Types of Motion in Hora Shastra &amp; Saravali
            </h4>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b font-semibold uppercase" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Motion</th>
                    <th className="pb-2 pr-3">Sanskrit Name</th>
                    <th className="pb-2 pr-3 text-right">Virupas</th>
                    <th className="pb-2 pr-3">Speed Criterion</th>
                    <th className="pb-2">Classical Significance</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  <tr>
                    <td className="py-2 font-bold text-emerald-400">Retrograde</td>
                    <td className="py-2 font-serif">Vakra</td>
                    <td className="py-2 text-right font-mono font-bold text-emerald-400">60.0</td>
                    <td className="py-2">&lt; 0 (Retrograde)</td>
                    <td className="py-2 text-text-secondary">Maximum strength; planet fights against natural order.</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold text-emerald-400">Retrograde &amp; Previous Sign</td>
                    <td className="py-2 font-serif">Anuvakra</td>
                    <td className="py-2 text-right font-mono font-bold">30.0</td>
                    <td className="py-2">&lt; 0 (Enters previous sign)</td>
                    <td className="py-2 text-text-secondary">50% strength; re-enters previous zodiac sign.</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold">Stationary</td>
                    <td className="py-2 font-serif">Vikala</td>
                    <td className="py-2 text-right font-mono font-bold">15.0</td>
                    <td className="py-2">&lt; 10% average speed</td>
                    <td className="py-2 text-text-secondary">Devoid of motion during turnaround station.</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold">Very Slow Direct</td>
                    <td className="py-2 font-serif">Mandatara</td>
                    <td className="py-2 text-right font-mono font-bold">15.0</td>
                    <td className="py-2">10% - 50% average speed</td>
                    <td className="py-2 text-text-secondary">Slow direct progression.</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold">Slow Direct</td>
                    <td className="py-2 font-serif">Manda</td>
                    <td className="py-2 text-right font-mono font-bold">30.0</td>
                    <td className="py-2">50% - 100% average speed</td>
                    <td className="py-2 text-text-secondary">Medium direct speed.</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold text-rose-400">Normal / Average</td>
                    <td className="py-2 font-serif">Sama</td>
                    <td className="py-2 text-right font-mono font-bold text-rose-400">7.5</td>
                    <td className="py-2">100% - 150% average speed</td>
                    <td className="py-2 text-text-secondary">Weakest of all motions.</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold text-emerald-400">Fast Direct</td>
                    <td className="py-2 font-serif">Chara</td>
                    <td className="py-2 text-right font-mono font-bold text-emerald-400">45.0</td>
                    <td className="py-2">&gt; 150% average speed</td>
                    <td className="py-2 text-text-secondary">Accelerated swift progression.</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold">Accelerated &amp; Next Sign</td>
                    <td className="py-2 font-serif">Atichara</td>
                    <td className="py-2 text-right font-mono font-bold">30.0</td>
                    <td className="py-2">&gt; 150% (Enters next sign)</td>
                    <td className="py-2 text-text-secondary">Rapid leap into next zodiac sign.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: 5. NAISARGIKA BALA */}
      {activeTab === "naisargika" && (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
              5. Naisargika Bala (Natural Strength)
            </h3>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Naisargika Bala is the inherent, constant natural strength of planets ordered strictly by luminosity. It is permanent and identical across all horoscopes.
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Luminosity Rank</th>
                    <th className="pb-2 pr-3">Graha</th>
                    <th className="pb-2 pr-3 text-right">Fractional Rupas</th>
                    <th className="pb-2 pr-3 text-right">Virupas</th>
                    <th className="pb-2 text-right">Rupas Decimal</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  {Object.entries(NAISARGIKA_BALA_TABLE).map(([p, info]) => {
                    const pName = p.charAt(0).toUpperCase() + p.slice(1);
                    return (
                      <tr key={p} className="hover:bg-white/5">
                        <td className="py-2.5 pr-3 font-bold" style={{ color: "var(--text-muted)" }}>
                          #{info.rank}
                        </td>
                        <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                          {PLANET_SYMBOLS[pName] ?? ""} {pName}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold" style={{ color: "var(--accent)" }}>
                          {info.rupas}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono" style={{ color: "var(--text-primary)" }}>
                          {info.virupas.toFixed(2)} V
                        </td>
                        <td className="py-2.5 text-right font-mono" style={{ color: "var(--text-muted)" }}>
                          {(info.virupas / 60.0).toFixed(4)} R
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: 6. DRIG BALA */}
      {activeTab === "drig" && (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
              6. Drig Bala (Aspectual Strength)
            </h3>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Drig Bala measures strength conferred by aspects (Graha Drishti) received from other planets. Aspects are rectified with classical weights: Benefic aspects contribute +125% of Sputa Drishti, while Malefic aspects subtract 75%.
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Graha</th>
                    <th className="pb-2 pr-3 text-right">Drig Bala (Virupas)</th>
                    <th className="pb-2 pr-3 text-right">Drig Bala (Rupas)</th>
                    <th className="pb-2">Aspectual Influence</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  {planetsList.map((p) => {
                    const dRupas = p.drig_bala_virupas / 60.0;
                    return (
                      <tr key={p.planet} className="hover:bg-white/5">
                        <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                          {PLANET_SYMBOLS[p.planet_display_name] ?? ""} {p.planet_display_name}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold" style={{ color: p.drig_bala_virupas >= 0 ? "#10B981" : "#EF4444" }}>
                          {p.drig_bala_virupas > 0 ? `+${p.drig_bala_virupas.toFixed(2)}` : p.drig_bala_virupas.toFixed(2)} V
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono" style={{ color: "var(--text-muted)" }}>
                          {dRupas.toFixed(2)} R
                        </td>
                        <td className="py-2.5 text-xs">
                          {p.drig_bala_virupas > 5 ? (
                            <span className="font-semibold text-emerald-400">Benefic Aspects Dominate (+125%)</span>
                          ) : p.drig_bala_virupas < -5 ? (
                            <span className="font-semibold text-rose-400">Malefic Aspects Dominate (-75%)</span>
                          ) : (
                            <span className="text-slate-400">Balanced Aspects</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: ISHTA & KASHTA BALA */}
      {activeTab === "ishta_kashta" && (
        <div className="space-y-6">
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
              Ishta Bala &amp; Kashta Bala (Benefic vs. Malefic Force)
            </h3>
            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
              Derived from Uchcha Bala (Exaltation) and Cheshta Bala (Motional force). Ishta indicates auspicious, benevolent potency, while Kashta indicates difficult, turbulent potential.
            </p>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-xs font-semibold uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                    <th className="pb-2 pr-3">Graha</th>
                    <th className="pb-2 pr-3 text-right text-emerald-400">Ishta Bala (Benefic)</th>
                    <th className="pb-2 pr-3 text-right text-rose-400">Kashta Bala (Difficult)</th>
                    <th className="pb-2 pr-3 text-right">Ishta / Kashta Ratio</th>
                    <th className="pb-2">Classical Tendency</th>
                  </tr>
                </thead>
                <tbody className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                  {planetsList.map((p) => {
                    const ratio = p.kashta_bala_virupas > 0 ? p.ishta_bala_virupas / p.kashta_bala_virupas : 1.0;
                    return (
                      <tr key={p.planet} className="hover:bg-white/5">
                        <td className="py-2.5 pr-3 font-semibold" style={{ color: "var(--text-primary)" }}>
                          {PLANET_SYMBOLS[p.planet_display_name] ?? ""} {p.planet_display_name}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold text-emerald-400">
                          {p.ishta_bala_virupas.toFixed(2)} V
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold text-rose-400">
                          {p.kashta_bala_virupas.toFixed(2)} V
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-bold" style={{ color: ratio >= 1.0 ? "#10B981" : "#F59E0B" }}>
                          {ratio.toFixed(2)}×
                        </td>
                        <td className="py-2.5 text-xs">
                          {p.ishta_bala_virupas > p.kashta_bala_virupas ? (
                            <span className="font-semibold text-emerald-400">Predominantly Auspicious</span>
                          ) : (
                            <span className="text-amber-400">Challenging / Mixed</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT: SARAVALI REFERENCE */}
      {activeTab === "reference" && (
        <div className="glass-card space-y-4 p-5 text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--accent)" }}>
            Classical Treatises: Saravali &amp; Brihat Parashara Hora Shastra (Ch. 27)
          </h3>

          <div className="space-y-3 border-l-2 pl-3" style={{ borderColor: "var(--accent)" }}>
            <p>
              <strong>Kalyana Varma&apos;s Saravali</strong> and <strong>Maharishi Parashara&apos;s BPHS</strong> establish the 6-fold Shadbala as the supreme mathematical criterion for judging planetary potency during Dasas and Gochara (transits).
            </p>
            <p>
              <strong>1 Rupa = 60 Virupas (Shashtiamsas).</strong> When a planet exceeds its required threshold, its significations manifest abundantly. Benefic planets (Jupiter, Venus, unafflicted Mercury, waxing Moon) produce unhindered fortune and wisdom; malefic planets (Sun, Mars, Saturn) produce decisive power, authority, and grit, but require awareness to avoid friction.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 pt-2">
            <div className="rounded-lg p-3" style={{ backgroundColor: "var(--bg-card)" }}>
              <span className="font-bold text-accent">Minimum Shadbala Standards:</span>
              <ul className="mt-1 space-y-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
                <li>• Sun: 390 Virupas (6.5 Rupas)</li>
                <li>• Moon: 360 Virupas (6.0 Rupas)</li>
                <li>• Mars: 300 Virupas (5.0 Rupas)</li>
                <li>• Mercury: 420 Virupas (7.0 Rupas)</li>
                <li>• Jupiter: 390 Virupas (6.5 Rupas)</li>
                <li>• Venus: 330 Virupas (5.5 Rupas)</li>
                <li>• Saturn: 300 Virupas (5.0 Rupas)</li>
              </ul>
            </div>

            <div className="rounded-lg p-3" style={{ backgroundColor: "var(--bg-card)" }}>
              <span className="font-bold text-accent">Sub-Bala Group Criteria:</span>
              <ul className="mt-1 space-y-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
                <li>• <strong>Sun, Jupiter, Mercury:</strong> Sthana ≥ 165, Dig ≥ 35, Kala ≥ 50, Cheshta ≥ 112, Ayana ≥ 30</li>
                <li>• <strong>Moon, Venus:</strong> Sthana ≥ 133, Dig ≥ 50, Kala ≥ 30, Cheshta ≥ 100, Ayana ≥ 40</li>
                <li>• <strong>Mars, Saturn:</strong> Sthana ≥ 96, Dig ≥ 30, Kala ≥ 40, Cheshta ≥ 67, Ayana ≥ 20</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SaravaliShadbalaSuite;
