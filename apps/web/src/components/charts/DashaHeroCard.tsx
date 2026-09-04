"use client";

import { useMemo } from "react";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type { DashaTreeResponse, DashaPeriodResponse } from "@/lib/types";

export const LEVEL_CONFIG: Record<
  number,
  { label: string; short: string; color: string; bg: string; border: string }
> = {
  1: {
    label: "Mahadasha",
    short: "MD",
    color: "#6366f1",
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/30 text-indigo-400",
  },
  2: {
    label: "Antardasha",
    short: "AD",
    color: "#0ea5e9",
    bg: "bg-sky-500/10",
    border: "border-sky-500/30 text-sky-400",
  },
  3: {
    label: "Pratyantar",
    short: "PD",
    color: "#10b981",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30 text-emerald-400",
  },
  4: {
    label: "Sookshma",
    short: "SD",
    color: "#f59e0b",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30 text-amber-400",
  },
  5: {
    label: "Prana",
    short: "PR",
    color: "#f43f5e",
    bg: "bg-rose-500/10",
    border: "border-rose-500/30 text-rose-400",
  },
};

function formatDate(d: string): string {
  try {
    return new Date(d).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return d;
  }
}

function durationLabel(days: number): string {
  if (days <= 0) return "Ended";
  const years = Math.floor(days / 365);
  const months = Math.floor((days % 365) / 30);
  const d = days % 30;
  const parts: string[] = [];
  if (years > 0) parts.push(`${years}y`);
  if (months > 0) parts.push(`${months}m`);
  if (d > 0 && years === 0) parts.push(`${d}d`);
  return parts.join(" ") || "< 1d";
}

function progressPercent(period: DashaPeriodResponse): number {
  const now = Date.now();
  const start = new Date(period.start_date).getTime();
  const end = new Date(period.end_date).getTime();
  const total = end - start;
  if (total <= 0) return 100;
  return Math.min(100, Math.max(0, Math.round(((now - start) / total) * 100)));
}

function daysRemaining(period: DashaPeriodResponse): number {
  return Math.max(
    0,
    Math.round((new Date(period.end_date).getTime() - Date.now()) / 86_400_000),
  );
}

export function DashaHeroCard({ dasha }: { dasha: DashaTreeResponse }) {
  const chain = useMemo(
    () => getCurrentDashaChain(dasha.mahadashas),
    [dasha.mahadashas],
  );

  const md = chain[0] ?? null;
  const ad = chain[1] ?? null;
  const pd = chain[2] ?? null;

  const mdPct = md ? progressPercent(md) : 0;
  const adPct = ad ? progressPercent(ad) : 0;
  const mdDaysLeft = md ? daysRemaining(md) : 0;
  const adDaysLeft = ad ? daysRemaining(ad) : 0;

  return (
    <div className="space-y-4">
      {/* ── System Overview Card ────────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold capitalize text-slate-100">
                {dasha.system} Dasha Timeline
              </h2>
              <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                Active Cycle
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Trigger: <span className="font-medium text-slate-200">{dasha.trigger_planet}</span>
              {dasha.trigger_nakshatra ? (
                <> · Nakshatra: <span className="font-medium text-slate-200">{dasha.trigger_nakshatra}</span></>
              ) : null}
              {" · "}Total Cycle: <span className="font-medium text-slate-200">{dasha.total_cycle_years} Years</span>
            </p>
          </div>

          {/* Active Lords Badges */}
          <div className="flex flex-wrap items-center gap-2">
            {chain.slice(0, 3).map((p) => {
              const cfg = LEVEL_CONFIG[p.level] || LEVEL_CONFIG[1];
              return (
                <div
                  key={`${p.lord}-${p.level}`}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold border ${cfg.bg} ${cfg.border}`}
                >
                  <span className="text-[10px] opacity-75">{cfg.short}:</span>
                  <span>{p.lord}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Active Period Chain Breadcrumb ─────────────────────────── */}
        <div className="mt-4 pt-3 border-t border-slate-800">
          <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-2">
            Current Period Chain
          </div>
          {chain.length === 0 ? (
            <p className="text-xs text-slate-400">No active period found within computed depth.</p>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              {chain.map((period, i) => {
                const cfg = LEVEL_CONFIG[period.level] || LEVEL_CONFIG[1];
                return (
                  <div key={`${period.lord}-${period.level}`} className="flex items-center gap-2">
                    {i > 0 && <span className="text-xs text-slate-600 font-bold">→</span>}
                    <div
                      className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold border ${cfg.bg} ${cfg.border}`}
                    >
                      <span className="rounded bg-slate-800/80 px-1 py-0.5 text-[9px] font-mono">
                        {cfg.short}
                      </span>
                      <span className="text-slate-100 font-bold">{period.lord}</span>
                      <span className="text-[10px] text-slate-400 font-normal">
                        ({formatDate(period.start_date)} - {formatDate(period.end_date)})
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── MD + AD Progress Gauges ───────────────────────────────────── */}
      {md && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Mahadasha Progress Gauge */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-indigo-400">
                Mahadasha (MD)
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {formatDate(md.start_date)} → {formatDate(md.end_date)}
              </span>
            </div>
            <div className="flex items-baseline justify-between mb-2">
              <span className="text-lg font-bold text-slate-100">{md.lord}</span>
              <span className="text-xs font-mono font-medium text-slate-300">
                {durationLabel(mdDaysLeft)} remaining
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                style={{ width: `${mdPct}%` }}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-[11px] text-slate-400">
              <span>{mdPct}% elapsed</span>
              <span>Total: {durationLabel(md.duration_days)}</span>
            </div>
          </div>

          {/* Antardasha Progress Gauge */}
          {ad ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-sky-400">
                  Antardasha (AD in {md.lord})
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  {formatDate(ad.start_date)} → {formatDate(ad.end_date)}
                </span>
              </div>
              <div className="flex items-baseline justify-between mb-2">
                <span className="text-lg font-bold text-slate-100">{ad.lord}</span>
                <span className="text-xs font-mono font-medium text-slate-300">
                  {durationLabel(adDaysLeft)} remaining
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-sky-500 transition-all duration-500"
                  style={{ width: `${adPct}%` }}
                />
              </div>
              <div className="mt-1.5 flex justify-between text-[11px] text-slate-400">
                <span>{adPct}% elapsed</span>
                <span>Total: {durationLabel(ad.duration_days)}</span>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 text-xs text-slate-400 flex items-center justify-center">
              No Antardasha active within computed depth.
            </div>
          )}
        </div>
      )}

      {/* ── MD–AD–PD Lord Synthesis ──────────────────────────────────── */}
      {md && ad && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3.5 text-xs text-slate-300 flex flex-wrap items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded bg-amber-500/10 text-amber-400 font-bold text-xs">
              ⚡
            </span>
            <span>
              <strong className="text-indigo-400">{md.lord}</strong> (MD) ×{" "}
              <strong className="text-sky-400">{ad.lord}</strong> (AD)
              {pd ? <> × <strong className="text-emerald-400">{pd.lord}</strong> (PD)</> : null}
              {" "}Sambandha: Active lords jointly modulate house activations and planetary yoga outcomes.
            </span>
          </div>
          <div className="text-[11px] font-mono text-slate-400">
            System: {dasha.system.toUpperCase()}
          </div>
        </div>
      )}
    </div>
  );
}
