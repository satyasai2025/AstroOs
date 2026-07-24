"use client";

import { useMemo } from "react";
import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import { VedhaAnalysisPanel } from "@/components/charts/VedhaAnalysisPanel";
import type {
  DashaTreeResponse,
  DashaPeriodResponse,
  TransitResponse,
  TransitPlanetResponse,
} from "@/lib/types";

interface TransitTimelineProps {
  dasha: DashaTreeResponse;
  transits: TransitResponse;
}

const LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantar Dasha", "Sookshma Dasha", "Prana Dasha"];

const LEVEL_COLORS: Record<number, string> = {
  1: "#fbbf24",
  2: "#a78bfa",
  3: "#34d399",
  4: "#f87171",
  5: "#38bdf8",
};

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

function formatDateTime(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleString("en-US", {
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

/**
 * Walk down the dasha tree from the mahadasha list, collecting every level
 * (mahadasha -> antardasha -> ...) that is currently active — i.e. whose
 * own start_date/end_date bracket "now". Stops descending once a level has
 * no sub_periods left, or none of them contain "now" (e.g. the tree wasn't
 * expanded that deep by the backend).
 */
function getCurrentPeriodChain(mahadashas: DashaPeriodResponse[]): DashaPeriodResponse[] {
  const now = Date.now();
  const chain: DashaPeriodResponse[] = [];
  let candidates = mahadashas;

  while (candidates && candidates.length > 0) {
    const active = candidates.find((p) => {
      const start = new Date(p.start_date).getTime();
      const end = new Date(p.end_date).getTime();
      return now >= start && now <= end;
    });
    if (!active) break;
    chain.push(active);
    candidates = active.sub_periods;
  }

  return chain;
}

function periodProgressPercent(period: DashaPeriodResponse): number {
  const start = new Date(period.start_date).getTime();
  const end = new Date(period.end_date).getTime();
  const now = Date.now();
  if (end <= start) return 0;
  const pct = ((now - start) / (end - start)) * 100;
  return Math.min(100, Math.max(0, pct));
}

/** Small horizontal "start ── today ── end" bar for one active dasha period. */
function PeriodBar({ period }: { period: DashaPeriodResponse }) {
  const pct = periodProgressPercent(period);
  const color = LEVEL_COLORS[period.level] ?? "var(--accent)";
  const levelName = LEVEL_NAMES[period.level - 1] ?? `Level ${period.level}`;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 font-medium" style={{ color: "var(--text-secondary)" }}>
          <span
            className="inline-block h-2 w-2 rounded-sm"
            style={{ backgroundColor: color }}
            aria-hidden="true"
          />
          {levelName}
        </span>
        <span style={{ color: "var(--text-primary)" }}>
          {PLANET_SYMBOLS[period.lord] ?? ""} {period.lord}
        </span>
      </div>
      <div
        className="relative h-3 w-full overflow-hidden rounded-full"
        style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
        role="img"
        aria-label={`${levelName} ${period.lord}: ${formatDate(period.start_date)} to ${formatDate(period.end_date)}, ${pct.toFixed(0)}% elapsed`}
      >
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color, opacity: 0.85 }}
        />
        <div
          className="absolute top-0 h-full w-0.5"
          style={{ left: `${pct}%`, backgroundColor: "#ef4444" }}
          aria-hidden="true"
        />
      </div>
      <div className="flex items-center justify-between text-[10px]" style={{ color: "var(--text-muted)" }}>
        <span>{formatDate(period.start_date)}</span>
        <span>{pct.toFixed(0)}% elapsed</span>
        <span>{formatDate(period.end_date)}</span>
      </div>
    </div>
  );
}

const FLAG_DEFS: {
  key: keyof TransitPlanetResponse;
  label: string;
  tone: "warn" | "danger" | "ok";
}[] = [
  { key: "is_sade_sati", label: "Sade Sati", tone: "danger" },
  { key: "is_ashtama_shani", label: "Ashtama Shani", tone: "danger" },
  { key: "has_vedha", label: "Vedha", tone: "warn" },
  { key: "has_vipreet_vedha", label: "Vipreet Vedha", tone: "warn" },
];

const TONE_COLORS: Record<string, string> = {
  warn: "#fbbf24",
  danger: "#f87171",
  ok: "#34d399",
};

/** One planet's current transit row. */
function TransitRow({ p }: { p: TransitPlanetResponse }) {
  const activeFlags = FLAG_DEFS.filter((f) => Boolean(p[f.key]));

  return (
    <div
      className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-lg border px-3 py-2"
      style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
    >
      <span className="w-16 flex-shrink-0 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
        {PLANET_SYMBOLS[p.planet] ?? ""} {PLANET_ABBREV[p.planet] ?? p.planet.slice(0, 2)}
      </span>
      <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
        In <strong style={{ color: "var(--text-primary)" }}>{p.transit_rashi}</strong> · House{" "}
        {p.house_from_natal_moon} from natal Moon
        {p.ashtakavarga_bindus !== null && (
          <>
            {" "}
            · <span style={{ color: "var(--text-muted)" }}>{p.ashtakavarga_bindus} bindus</span>
          </>
        )}
      </span>
      <div className="flex flex-wrap items-center justify-end gap-1">
        {p.is_favorable_house !== null && (
          <span
            className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
            style={{
              color: p.is_favorable_house ? TONE_COLORS.ok : "var(--text-muted)",
              border: `1px solid ${p.is_favorable_house ? TONE_COLORS.ok : "var(--border-primary)"}`,
            }}
          >
            {p.is_favorable_house ? "Good House" : "Neutral House"}
          </span>
        )}
        {activeFlags.map((f) => (
          <span
            key={f.key}
            className="rounded px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide"
            style={{ color: TONE_COLORS[f.tone], border: `1px solid ${TONE_COLORS[f.tone]}` }}
            title={f.key === "has_vedha" && p.vedha_planet ? `Vedha by ${p.vedha_planet}` : undefined}
          >
            {f.label}
          </span>
        ))}
      </div>
    </div>
  );
}

/**
 * TransitTimeline — an honest "right now" snapshot, not a fabricated
 * multi-month prediction timeline. The backend only computes transits for
 * a single instant (transit_datetime_utc), so this shows:
 *
 *  (a) where "today" falls inside the currently-running dasha period at
 *      every level the backend resolved (Mahadasha down through whatever
 *      sub_periods are active right now), as start/end progress bars, and
 *  (b) the current transit position + flags for each planet, as a plain
 *      list/grid — no invented month-by-month history.
 */
export function TransitTimeline({ dasha, transits }: TransitTimelineProps) {
  const currentChain = useMemo(() => getCurrentPeriodChain(dasha.mahadashas), [dasha.mahadashas]);

  return (
    <div
      className="glass-card space-y-5 p-5"
      role="region"
      aria-label="Current dasha and transit snapshot"
    >
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Current Period &amp; Transit Snapshot
        </h3>
        <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
          {dasha.system} dasha, as of {formatDateTime(transits.transit_datetime_utc)}. This shows
          today&apos;s position only — the backend computes transits for a single instant, not a
          historical month-by-month forecast.
        </p>
      </div>

      {/* ── Active dasha chain ── */}
      <div className="space-y-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
          Active Dasha Levels
        </h4>
        {currentChain.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No dasha period currently overlaps today&apos;s date in this tree.
          </p>
        ) : (
          <div className="space-y-4">
            {currentChain.map((period, idx) => (
              <PeriodBar key={`${period.level}-${period.lord}-${idx}`} period={period} />
            ))}
          </div>
        )}
      </div>

      {/* ── Transit snapshot ── */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
          Transit Positions (Natal Moon in {transits.natal_moon_rashi})
        </h4>
        {transits.planets.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No transit data available.
          </p>
        ) : (
          <div className="space-y-1.5">
            {transits.planets.map((p) => (
              <TransitRow key={p.planet} p={p} />
            ))}
          </div>
        )}
      </div>

      {/* ── Vedha analysis ── */}
      <div className="border-t pt-4" style={{ borderColor: "var(--border-primary)" }}>
        <VedhaAnalysisPanel transits={transits} dashaChain={currentChain} />
      </div>
    </div>
  );
}
