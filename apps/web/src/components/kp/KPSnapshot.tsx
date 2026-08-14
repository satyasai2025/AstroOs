"use client";

/**
 * KP Snapshot — the live computed summary shown by default when the KP
 * Analysis Center opens. Every figure here comes pre-computed from the
 * backend KP engine (cusp sub-lords, planet star/sub/sub-sub lords,
 * ruling planets, event promises, fructification), so the page visibly
 * demonstrates the engine is working.
 */

import type {
  KPCuspResponse,
  KPPlanetProfileResponse,
  RulingPlanetResponse,
  EventPromiseResponse,
  EventTimingAnalysisResponse,
} from "@/lib/types";
import { PLANET_SYMBOLS } from "@/lib/astro";

interface Props {
  cusps: KPCuspResponse[];
  profiles: KPPlanetProfileResponse[];
  rulingPlanets: RulingPlanetResponse[];
  eventPromises: EventPromiseResponse[];
  timing: EventTimingAnalysisResponse[];
}

const PROMISE_COLORS: Record<string, { fg: string; bg: string }> = {
  POSITIVE: { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  PARTIAL: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
  WEAK: { fg: "#f87171", bg: "rgba(248,113,113,0.15)" },
};

export function KPSnapshot({ cusps, profiles, rulingPlanets, eventPromises, timing }: Props) {
  return (
    <div className="space-y-4">
      <div className="glass-card p-5">
        <div className="mb-3 flex items-baseline gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            KP Snapshot — Live
          </h3>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            computed from this chart&apos;s real cusp and planet data
          </span>
        </div>

        <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
          Cusp Sub Lords (CSL)
        </p>
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 xl:grid-cols-6">
          {cusps.map((c) => (
            <div key={c.house_number} className="rounded-lg border px-2 py-1.5" style={{ borderColor: "var(--border-primary)" }}>
              <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>H{c.house_number} · {c.rashi}</p>
              <p className="text-xs font-semibold" style={{ color: "var(--accent)" }}>{c.sub_lord || "—"}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="glass-card p-5">
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Planet Star / Sub / Sub-Sub Lords
          </p>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                <th className="py-1.5 pr-3">Planet</th>
                <th className="py-1.5 pr-3">Rashi</th>
                <th className="py-1.5 pr-3">Star</th>
                <th className="py-1.5 pr-3">Sub</th>
                <th className="py-1.5">Sub-Sub</th>
              </tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.planet} className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                  <td className="py-1.5 pr-3 font-medium">
                    <span aria-hidden="true" style={{ color: "var(--accent)" }}>{PLANET_SYMBOLS[p.planet] ?? ""}</span> {p.planet}
                  </td>
                  <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{p.rashi}</td>
                  <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{p.star_lord || "—"}</td>
                  <td className="py-1.5 pr-3 font-medium" style={{ color: "var(--accent)" }}>{p.sub_lord || "—"}</td>
                  <td className="py-1.5" style={{ color: "var(--text-secondary)" }}>{p.sub_sub_lord || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="space-y-4">
          <div className="glass-card p-5">
            <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Ruling Planets
            </p>
            <div className="flex flex-wrap gap-2">
              {rulingPlanets.map((rp) => (
                <span
                  key={rp.planet}
                  className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs"
                  style={{ backgroundColor: "rgba(96,165,250,0.15)", color: "#60a5fa", border: "1px solid rgba(96,165,250,0.4)" }}
                >
                  <span className="font-semibold">{rp.planet}</span>
                  <span style={{ color: "var(--text-secondary)" }}>{rp.source}</span>
                </span>
              ))}
            </div>
          </div>

          <div className="glass-card p-5">
            <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
              Event Promise
            </p>
            <div className="space-y-2">
              {eventPromises.map((ev) => {
                const vc = PROMISE_COLORS[ev.promise];
                return (
                  <div key={ev.eventKey} className="flex items-center justify-between rounded-lg border px-3 py-2" style={{ borderColor: "var(--border-primary)" }}>
                    <span className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>{ev.label}</span>
                    <span className="rounded-full px-2 py-0.5 text-[10px] font-bold" style={{ backgroundColor: vc.bg, color: vc.fg }}>
                      {ev.promise} · CSL {ev.csl_verdict.csl || "—"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card p-5">
        <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
          Fructification (Dasha Link + Transit + RP)
        </p>
        <div className="flex flex-wrap gap-2">
          {timing.map((w) => (
            <span
              key={w.eventKey}
              className="rounded-full px-3 py-1 text-xs"
              style={{
                backgroundColor:
                  w.fructification === "OPEN"
                    ? "rgba(52,211,153,0.15)"
                    : w.fructification === "PARTIAL"
                      ? "rgba(251,191,36,0.15)"
                      : "rgba(148,163,184,0.15)",
                color:
                  w.fructification === "OPEN"
                    ? "#34d399"
                    : w.fructification === "PARTIAL"
                      ? "#fbbf24"
                      : "#94a3b8",
              }}
            >
              {w.label}: <span className="font-semibold">{w.fructification}</span>
              {w.fructification === "OPEN" && w.dasha_link.significator_level
                ? ` · ${w.dasha_link.significator_level.lord} ${w.dasha_link.significator_level.level}`
                : w.fructification === "PARTIAL" && w.transit_triggers.length > 0
                  ? ` · ${w.transit_triggers.length} trigger${w.transit_triggers.length === 1 ? "" : "s"}`
                  : ""}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
