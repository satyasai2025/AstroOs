"use client";

import { useMemo, useState } from "react";
import { PLANET_SYMBOLS } from "@/lib/astro";
import type { DashaPeriodResponse, TransitResponse } from "@/lib/types";

interface VedhaAnalysisPanelProps {
  transits: TransitResponse;
  /** The currently-active dasha chain (Mahadasha -> Antardasha -> ...), same
   * shape TransitTimeline's getCurrentPeriodChain() already produces —
   * passed in rather than recomputed so there's one source of truth for
   * "which planet's period is running right now". */
  dashaChain: DashaPeriodResponse[];
}

const LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantar Dasha", "Sookshma Dasha", "Prana Dasha"];

type VedhaKind = "vedha" | "vipreet_vedha";

interface VedhaRow {
  id: string;
  kind: VedhaKind;
  /** The planet whose transit is being obstructed/relieved. */
  affected: string;
  /** The planet causing the obstruction/relief. */
  cause: string | null;
  house: number;
  reason: string;
  /** Only set for the Dasha-Transit tab. */
  dashaLevel?: string;
}

/** Nakshatra Vedha rows have a different shape from the Rashi Vedha rows
 * above — a target nakshatra + ray direction instead of a house number,
 * and no favorable/unfavorable judgment (Saravali presents this as a
 * plain obstruction relationship, not good/bad). Kept as a separate
 * interface rather than overloading VedhaRow with optional fields. */
interface NakshatraVedhaRow {
  id: string;
  planet: string;
  nakshatra: string;
  vedhaType: string | null; // "forward" | "backward"
  target: string | null;
  cause: string | null;
  active: boolean;
}

function formatDateTime(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

const KIND_LABEL: Record<VedhaKind, string> = {
  vedha: "Vedha (obstruction)",
  vipreet_vedha: "Vipreet Vedha (relief)",
};

const KIND_COLOR: Record<VedhaKind, string> = {
  vedha: "#f87171",
  vipreet_vedha: "#34d399",
};

type Tab = "active" | "dasha" | "all" | "nakshatra";

/**
 * Vedha Analysis — built entirely from the real, already-sourced Rashi/
 * Gochara Vedha table (packages/shared/transit_vedha_table.py, wired
 * through VedhaCalculator -> TransitEngine -> /api/v1/transit/current and
 * the main workflow response). Nothing here is fabricated, but two things
 * from the original mockup are deliberately NOT shown, because this app
 * doesn't have real data to back them yet:
 *
 *  - Nakshatra Vedha (Sarvatobhadra Chakra): a real classical system, but
 *    a different one from Gochara Vedha — a 9x9 geometric grid with
 *    direction-dependent obstruction lines (varies with retrograde
 *    motion) — see the "Nakshatra Vedha" tab below, now built and wired
 *    to a real backend calculator (packages/shared/sarvatobhadra_grid.py
 *    + services/nakshatra_vedha_calculator.py), sourced from and cross-
 *    verified against Saravali's (https://saravali.github.io) published
 *    SBC grid and worked examples — a genuinely different system from
 *    Rashi/Gochara Vedha above (nakshatra-based, not house-based, and
 *    not classified favorable/unfavorable).
 *  - Intensity (Low/Medium/High) and an explicit Start-End time window:
 *    the underlying VedhaCalculator is a pass/fail check at a single
 *    instant (house-pair based, not degree/orb based), so there's no real
 *    "how close" signal to grade, and no forward/backward transit scan to
 *    find exact entry/exit — so this shows a plain Active/Clear status as
 *    of the computed timestamp instead of inventing either one.
 *
 * "Dasha-Transit Vedha" here means: is the planet whose own Dasha level is
 * currently running (MD/AD/PD/...) ALSO showing has_vedha/has_vipreet_vedha
 * on its own transit right now? That's a straight cross-reference of two
 * already-real facts (the active dasha chain + each planet's existing
 * transit Vedha flags) — not a separate classical sub-system with its own
 * rule table.
 */
export function VedhaAnalysisPanel({ transits, dashaChain }: VedhaAnalysisPanelProps) {
  const [tab, setTab] = useState<Tab>("active");

  const allRows = useMemo<VedhaRow[]>(() => {
    return transits.planets
      .filter((p) => p.has_vedha || p.has_vipreet_vedha)
      .map((p) => {
        const kind: VedhaKind = p.has_vedha ? "vedha" : "vipreet_vedha";
        const reason = p.has_vedha
          ? `${p.vedha_planet ?? "Another planet"} is currently transiting ${p.planet}'s paired Vedha house, blocking ${p.planet}'s favorable effect from house ${p.house_from_natal_moon} (from natal Moon).`
          : `${p.vedha_planet ?? "Another planet"} is currently transiting the paired relief house, easing ${p.planet}'s unfavorable effect from house ${p.house_from_natal_moon} (from natal Moon).`;
        return {
          id: `active-${p.planet}`,
          kind,
          affected: p.planet,
          cause: p.vedha_planet,
          house: p.house_from_natal_moon,
          reason,
        };
      });
  }, [transits.planets]);

  const dashaRows = useMemo<VedhaRow[]>(() => {
    const rows: VedhaRow[] = [];
    dashaChain.forEach((period, i) => {
      const t = transits.planets.find((p) => p.planet === period.lord);
      if (!t || (!t.has_vedha && !t.has_vipreet_vedha)) return;
      const levelName = LEVEL_NAMES[i] ?? `Level ${i + 1}`;
      const kind: VedhaKind = t.has_vedha ? "vedha" : "vipreet_vedha";
      const reason = t.has_vedha
        ? `${t.planet} is running its own ${levelName} right now, but ${t.vedha_planet ?? "another planet"}'s transit is obstructing ${t.planet}'s favorable transit effect — the dasha lord's own expression may feel blocked while this holds.`
        : `${t.planet} is running its own ${levelName} right now, and ${t.vedha_planet ?? "another planet"}'s transit is relieving ${t.planet}'s unfavorable transit placement — some easing of this dasha lord's difficult house while this holds.`;
      rows.push({
        id: `dasha-${period.lord}-${i}`,
        kind,
        affected: t.planet,
        cause: t.vedha_planet,
        house: t.house_from_natal_moon,
        reason,
        dashaLevel: levelName,
      });
    });
    return rows;
  }, [dashaChain, transits.planets]);

  const allRuleRows = useMemo<VedhaRow[]>(() => {
    return transits.planets
      .filter((p) => p.is_favorable_house !== null)
      .map((p) => {
        const active = p.has_vedha || p.has_vipreet_vedha;
        const kind: VedhaKind = p.has_vedha ? "vedha" : "vipreet_vedha";
        return {
          id: `all-${p.planet}`,
          kind,
          affected: p.planet,
          cause: active ? p.vedha_planet : null,
          house: p.house_from_natal_moon,
          reason: active
            ? p.has_vedha
              ? `Obstructed by ${p.vedha_planet}.`
              : `Relieved by ${p.vedha_planet}.`
            : `${p.is_favorable_house ? "Favorable" : "Unfavorable"} house rule applies, no obstructing/relieving planet transiting right now.`,
        };
      });
  }, [transits.planets]);

  const nakshatraRows = useMemo<NakshatraVedhaRow[]>(() => {
    return transits.planets
      .filter((p) => p.transit_nakshatra_sbc)
      .map((p) => ({
        id: `nak-${p.planet}`,
        planet: p.planet,
        nakshatra: p.transit_nakshatra_sbc,
        vedhaType: p.nakshatra_vedha_type,
        target: p.nakshatra_vedha_target,
        cause: p.has_nakshatra_vedha ? p.nakshatra_vedha_planet : null,
        active: p.has_nakshatra_vedha,
      }));
  }, [transits.planets]);

  const rowsForTab = tab === "active" ? allRows : tab === "dasha" ? dashaRows : tab === "all" ? allRuleRows : [];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
          Vedha Analysis
        </h4>
        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
          As of {formatDateTime(transits.transit_datetime_utc)}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["active", `Active Vedhas (${allRows.length})`],
            ["dasha", `Dasha–Transit Vedha (${dashaRows.length})`],
            ["nakshatra", `Nakshatra Vedha (${nakshatraRows.filter((r) => r.active).length})`],
            ["all", `All Rashi Vedha Rules (${allRuleRows.length})`],
          ] as [Tab, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className="rounded-full px-2.5 py-1 text-xs transition"
            style={{
              border: `1px solid ${tab === key ? "var(--accent)" : "var(--border-primary)"}`,
              color: tab === key ? "var(--text-primary)" : "var(--text-muted)",
            }}
            aria-pressed={tab === key}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "nakshatra" ? (
        nakshatraRows.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No Nakshatra Vedha data available for this transit.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b text-[10px] uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                  <th className="py-1.5 pr-3">Planet</th>
                  <th className="py-1.5 pr-3">SBC Nakshatra</th>
                  <th className="py-1.5 pr-3">Ray</th>
                  <th className="py-1.5 pr-3">Targets</th>
                  <th className="py-1.5 pr-3">Obstructed By</th>
                  <th className="py-1.5">Status</th>
                </tr>
              </thead>
              <tbody>
                {nakshatraRows.map((row) => (
                  <tr key={row.id} className="border-b" style={{ borderColor: "var(--border-primary)" }}>
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-primary)" }}>
                      {PLANET_SYMBOLS[row.planet] ?? ""} {row.planet}
                    </td>
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>
                      {row.nakshatra}
                    </td>
                    <td className="py-1.5 pr-3 capitalize" style={{ color: "var(--text-muted)" }}>
                      {row.vedhaType ?? "—"}
                    </td>
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>
                      {row.target ?? "—"}
                    </td>
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>
                      {row.cause ? `${PLANET_SYMBOLS[row.cause] ?? ""} ${row.cause}` : "—"}
                    </td>
                    <td className="py-1.5">
                      <span
                        className="rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase"
                        style={{
                          color: row.active ? "#f87171" : "var(--text-muted)",
                          border: `1px solid ${row.active ? "#f87171" : "var(--border-primary)"}`,
                        }}
                      >
                        {row.active ? "Active" : "Clear"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : rowsForTab.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          {tab === "active" && "No active Vedha or Vipreet Vedha right now."}
          {tab === "dasha" && "The current dasha chain's lords aren't showing any Vedha on their own transit right now."}
          {tab === "all" && "No Rashi Vedha rule data available for this transit."}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b text-[10px] uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                <th className="py-1.5 pr-3">Type</th>
                <th className="py-1.5 pr-3">From → To</th>
                {tab === "dasha" && <th className="py-1.5 pr-3">Dasha Level</th>}
                <th className="py-1.5 pr-3">House Affected</th>
                <th className="py-1.5 pr-3">Reason</th>
                <th className="py-1.5">Status</th>
              </tr>
            </thead>
            <tbody>
              {rowsForTab.map((row) => {
                const isActiveRow = row.cause !== null;
                return (
                  <tr key={row.id} className="border-b" style={{ borderColor: "var(--border-primary)" }}>
                    <td className="py-1.5 pr-3">
                      <span style={{ color: KIND_COLOR[row.kind] }}>{KIND_LABEL[row.kind]}</span>
                    </td>
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>
                      {row.cause ? (
                        <>
                          {PLANET_SYMBOLS[row.cause] ?? ""} {row.cause} → {PLANET_SYMBOLS[row.affected] ?? ""} {row.affected}
                        </>
                      ) : (
                        <>
                          {PLANET_SYMBOLS[row.affected] ?? ""} {row.affected}
                        </>
                      )}
                    </td>
                    {tab === "dasha" && (
                      <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>
                        {row.dashaLevel}
                      </td>
                    )}
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>
                      House {row.house}
                    </td>
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-muted)" }}>
                      {row.reason}
                    </td>
                    <td className="py-1.5">
                      <span
                        className="rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase"
                        style={{
                          color: isActiveRow ? KIND_COLOR[row.kind] : "var(--text-muted)",
                          border: `1px solid ${isActiveRow ? KIND_COLOR[row.kind] : "var(--border-primary)"}`,
                        }}
                      >
                        {isActiveRow ? "Active" : "Clear"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
        Status is a snapshot at the timestamp above, not a predicted date range — exact entry/exit
        times would need scanning the transit forward/backward in time, which isn&apos;t computed yet.
        Intensity isn&apos;t shown because the underlying checks are pass/fail, not degree-based.
        {tab === "nakshatra" &&
          " Nakshatra Vedha (Sarvatobhadra Chakra) is a separate system from Rashi Vedha above — a direct-motion planet casts its ray Forward, a retrograde planet Backward; true stationary (near-zero speed) isn't distinguished here, so it's treated as Forward."}
      </p>
    </div>
  );
}
