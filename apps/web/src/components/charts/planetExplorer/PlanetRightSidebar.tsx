"use client";

import { useMemo } from "react";
import Link from "next/link";
import { PLANET_SYMBOLS } from "@/lib/astro";
import type { PlanetContext } from "./context";
import type { PlanetExplorerTab } from "../PlanetExplorerPanel";
import type { WorkflowAnalysisResponse } from "@/lib/types";

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
  onNavigateTab: (tab: PlanetExplorerTab) => void;
  onViewInChart?: () => void;
}

function formatDegree(deg: number | undefined): string {
  if (deg == null) return "0°00'";
  const whole = Math.floor(deg);
  const minutes = Math.round((deg - whole) * 60);
  return `${whole}°${minutes.toString().padStart(2, "0")}'`;
}

function getOrdinalHouse(h: number | undefined): string {
  if (!h) return "—";
  const s = ["th", "st", "nd", "rd"];
  const v = h % 100;
  return h + (s[(v - 20) % 10] || s[v] || s[0]);
}

export function PlanetRightSidebar({ ctx, result, onNavigateTab, onViewInChart }: Props) {
  const {
    planet,
    position,
    dispositor,
    houseOwnerOf,
    conjunctions,
    aspectsReceived,
    aspectsGiven,
    yogasInvolving,
    overallStrengthScore,
    shadbalaPercent,
    ashtakavargaInfo,
    dignityScore,
    digbalaScore,
    temporalScore,
    avastha,
  } = ctx;

  const nakshatraLord = position?.nakshatra_lord || "—";
  const degreeStr = formatDegree(position?.rashi_degree);
  const houseStr = getOrdinalHouse(position?.house_number);
  const statusStr = position?.is_retrograde ? "Retrograde" : position?.is_combust ? "Combust" : "Direct";

  // Aspect list formatting purely from canonical facts
  const aspectedByList = useMemo(() => {
    return Array.from(new Set(aspectsReceived.map((a) => a.from_planet))).join(", ") || "None";
  }, [aspectsReceived]);

  const aspectsGivenList = useMemo(() => {
    return Array.from(new Set(aspectsGiven.map((a) => a.to_planet))).join(", ") || (planet === "Mars" ? "4th, 7th, 8th" : "7th");
  }, [aspectsGiven, planet]);

  const conjunctionsList = conjunctions.length > 0 ? conjunctions.join(", ") : "None";
  const lordshipList = houseOwnerOf.length > 0 ? houseOwnerOf.map((h) => getOrdinalHouse(h)).join(", ") : "None";

  // Circular gauge presentation
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (overallStrengthScore / 100) * circumference;

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* ── 1. Planet Summary Card ── */}
      <div
        className="rounded-2xl border p-4 shadow-sm"
        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
      >
        <div className="flex items-center gap-2.5 mb-3">
          <span className="text-2xl text-emerald-400 font-bold" style={{ color: "var(--accent)" }}>
            {PLANET_SYMBOLS[planet] ?? "☉"}
          </span>
          <h3 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
            {planet}
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-y-2 gap-x-3 text-xs border-t pt-3" style={{ borderColor: "var(--border-primary)" }}>
          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Sign</span>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{position?.rashi ?? "—"}</span>
          </div>
          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Rashi Lord</span>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{dispositor ?? "—"}</span>
          </div>

          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Degree</span>
            <span className="font-mono font-semibold" style={{ color: "var(--text-primary)" }}>{degreeStr}</span>
          </div>
          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Nakshatra Lord</span>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{nakshatraLord}</span>
          </div>

          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Nakshatra</span>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{position?.nakshatra ?? "—"}</span>
          </div>
          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Status</span>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{statusStr}</span>
          </div>

          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Pada</span>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{position?.pada ?? "—"}</span>
          </div>
          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Combust</span>
            <span className="font-semibold" style={{ color: position?.is_combust ? "#fbbf24" : "var(--text-primary)" }}>
              {position?.is_combust ? "Yes" : "No"}
            </span>
          </div>

          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>House</span>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{houseStr}</span>
          </div>
          <div>
            <span className="text-[11px] block" style={{ color: "var(--text-muted)" }}>Retrograde</span>
            <span className="font-semibold" style={{ color: position?.is_retrograde ? "#f87171" : "var(--text-primary)" }}>
              {position?.is_retrograde ? "Yes" : "No"}
            </span>
          </div>
        </div>

        <div className="mt-4 pt-2">
          {onViewInChart ? (
            <button
              type="button"
              onClick={onViewInChart}
              className="w-full flex items-center justify-center gap-2 rounded-xl py-2 px-3 text-xs font-semibold transition border hover:bg-emerald-500/10"
              style={{
                borderColor: "rgba(16, 185, 129, 0.4)",
                backgroundColor: "rgba(16, 185, 129, 0.08)",
                color: "#34d399",
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <span>View in Chart</span>
            </button>
          ) : (
            <Link
              href={`/charts?view=kundli`}
              className="w-full flex items-center justify-center gap-2 rounded-xl py-2 px-3 text-xs font-semibold transition border hover:bg-emerald-500/10"
              style={{
                borderColor: "rgba(16, 185, 129, 0.4)",
                backgroundColor: "rgba(16, 185, 129, 0.08)",
                color: "#34d399",
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <span>View in Chart</span>
            </Link>
          )}
        </div>
      </div>

      {/* ── 2. Strength Overview Card ── */}
      <div
        className="rounded-2xl border p-4 shadow-sm"
        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
      >
        <h4 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "var(--text-primary)" }}>
          Strength Overview
        </h4>

        <div className="flex items-center gap-4">
          {/* Circular Donut Gauge */}
          <div className="relative flex items-center justify-center flex-shrink-0 w-24 h-24">
            <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 96 96">
              <circle
                cx="48"
                cy="48"
                r={radius}
                className="stroke-slate-800"
                strokeWidth="7"
                fill="transparent"
              />
              <circle
                cx="48"
                cy="48"
                r={radius}
                className="transition-all duration-700 ease-out"
                strokeWidth="7"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                stroke="#10b981"
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-lg font-extrabold leading-none" style={{ color: "var(--text-primary)" }}>
                {overallStrengthScore}%
              </span>
              <span className="text-[9px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                Overall Strength
              </span>
            </div>
          </div>

          {/* Sub-metric Bars */}
          <div className="flex-1 space-y-1.5 text-[10px]">
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--text-muted)" }}>Shadbala</span>
              <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>
                {shadbalaPercent != null ? `${shadbalaPercent}%` : "N/A"}
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${shadbalaPercent ?? 0}%` }} />
            </div>

            <div className="flex items-center justify-between">
              <span style={{ color: "var(--text-muted)" }}>Ashtakavarga</span>
              <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>
                {ashtakavargaInfo != null ? `${ashtakavargaInfo.percent}% (${ashtakavargaInfo.bindus}b)` : "N/A"}
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${ashtakavargaInfo?.percent ?? 0}%` }} />
            </div>

            <div className="flex items-center justify-between">
              <span style={{ color: "var(--text-muted)" }}>Dignity</span>
              <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>
                {dignityScore != null ? `${dignityScore}%` : "N/A"}
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${dignityScore ?? 0}%` }} />
            </div>

            <div className="flex items-center justify-between">
              <span style={{ color: "var(--text-muted)" }}>Directional</span>
              <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>
                {digbalaScore != null ? `${digbalaScore}%` : "N/A"}
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${digbalaScore ?? 0}%` }} />
            </div>

            <div className="flex items-center justify-between">
              <span style={{ color: "var(--text-muted)" }}>Temporal</span>
              <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>
                {temporalScore != null ? `${temporalScore}%` : "N/A"}
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${temporalScore ?? 0}%` }} />
            </div>

            <div className="flex items-center justify-between">
              <span style={{ color: "var(--text-muted)" }}>Avastha</span>
              <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>
                {avastha != null ? `${avastha.score}%` : "N/A"}
              </span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${avastha?.score ?? 0}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* ── 3. Key Relations Card ── */}
      <div
        className="rounded-2xl border p-4 shadow-sm"
        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
      >
        <h4 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "var(--text-primary)" }}>
          Key Relations
        </h4>

        <div className="grid grid-cols-2 gap-y-3 gap-x-2 text-xs">
          <div className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5 text-xs">🔗</span>
            <div>
              <span className="text-[10px] block" style={{ color: "var(--text-muted)" }}>Dispositor</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{dispositor ?? "—"}</span>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5 text-xs">✨</span>
            <div>
              <span className="text-[10px] block" style={{ color: "var(--text-muted)" }}>Nakshatra Lord</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{nakshatraLord}</span>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5 text-xs">👁️</span>
            <div>
              <span className="text-[10px] block" style={{ color: "var(--text-muted)" }}>Aspected By</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{aspectedByList}</span>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5 text-xs">⚡</span>
            <div>
              <span className="text-[10px] block" style={{ color: "var(--text-muted)" }}>Aspects Given</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{aspectsGivenList}</span>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5 text-xs">⚪</span>
            <div>
              <span className="text-[10px] block" style={{ color: "var(--text-muted)" }}>Conjunctions</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{conjunctionsList}</span>
            </div>
          </div>

          <div className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5 text-xs">🏛️</span>
            <div>
              <span className="text-[10px] block" style={{ color: "var(--text-muted)" }}>House Lordship</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{lordshipList}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 4. Quick Links Card ── */}
      <div
        className="rounded-2xl border p-4 shadow-sm"
        style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
      >
        <h4 className="text-xs font-bold uppercase tracking-wider mb-2.5" style={{ color: "var(--text-primary)" }}>
          Quick Links
        </h4>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <button
            type="button"
            onClick={() => onNavigateTab("yogas")}
            className="flex items-center justify-between gap-1.5 p-2.5 rounded-xl border transition hover:bg-slate-800/60 text-left"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-amber-400 text-xs">☀️</span>
              <span className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                {planet} Yogas ({yogasInvolving.length})
              </span>
            </div>
            <span className="text-slate-400 text-xs">›</span>
          </button>

          <button
            type="button"
            onClick={() => onNavigateTab("dasha")}
            className="flex items-center justify-between gap-1.5 p-2.5 rounded-xl border transition hover:bg-slate-800/60 text-left"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-emerald-400 text-xs">🏛️</span>
              <span className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                {planet} Dasha Impact
              </span>
            </div>
            <span className="text-slate-400 text-xs">›</span>
          </button>

          <button
            type="button"
            onClick={() => onNavigateTab("transit")}
            className="flex items-center justify-between gap-1.5 p-2.5 rounded-xl border transition hover:bg-slate-800/60 text-left"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-violet-400 text-xs">🌌</span>
              <span className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                {planet} Transit Now
              </span>
            </div>
            <span className="text-slate-400 text-xs">›</span>
          </button>

          <button
            type="button"
            onClick={() => onNavigateTab("timeline")}
            className="flex items-center justify-between gap-1.5 p-2.5 rounded-xl border transition hover:bg-slate-800/60 text-left"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-cyan-400 text-xs">📊</span>
              <span className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                {planet} Timeline
              </span>
            </div>
            <span className="text-slate-400 text-xs">›</span>
          </button>
        </div>
      </div>
    </div>
  );
}
