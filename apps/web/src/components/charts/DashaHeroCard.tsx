"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui";
import { getCurrentDashaChain } from "@/lib/kpiScoring";
import type { DashaTreeResponse, DashaPeriodResponse } from "@/lib/types";

const LEVEL_NAMES = ["MD", "AD", "PD", "SD", "Prana"] as const;

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

/**
 * Dasha Hero Card — shows the full MD→AD→PD→SD→Prana active chain,
 * with progress bar and countdown for the current MD and AD periods.
 *
 * All data sourced exclusively from DashaTreeResponse (no extra fetching).
 */
export function DashaHeroCard({ dasha }: { dasha: DashaTreeResponse }) {
  const chain = useMemo(
    () => getCurrentDashaChain(dasha.mahadashas),
    [dasha.mahadashas],
  );

  const md = chain[0] ?? null;
  const ad = chain[1] ?? null;

  const mdPct = md ? progressPercent(md) : 0;
  const adPct = ad ? progressPercent(ad) : 0;
  const mdDaysLeft = md ? daysRemaining(md) : 0;
  const adDaysLeft = ad ? daysRemaining(ad) : 0;

  return (
    <div className="space-y-4">
      {/* ── System info ─────────────────────────────────────────────────── */}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3
              className="text-sm font-bold uppercase tracking-wide"
              style={{ color: "var(--accent)" }}
            >
              {dasha.system} Dasha
            </h3>
            <p className="mt-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>
              Trigger: {dasha.trigger_planet}
              {dasha.trigger_nakshatra ? ` · ${dasha.trigger_nakshatra}` : ""}
              {" · "}Total cycle: {dasha.total_cycle_years} years
            </p>
          </div>
          <span
            className="rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wider"
            style={{
              background: "var(--accent)",
              color: "var(--accent-text)",
              opacity: 0.9,
            }}
          >
            Live
          </span>
        </div>
      </Card>

      {/* ── Active chain breadcrumb ──────────────────────────────────────── */}
      <Card>
        <h4
          className="mb-3 text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-tertiary)" }}
        >
          Current Period Chain
        </h4>
        {chain.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            No active period found within computed depth.
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            {chain.map((period, i) => (
              <span
                key={`${period.lord}-${period.level}`}
                className="flex items-center gap-2"
              >
                {i > 0 && (
                  <span
                    className="text-sm font-bold"
                    style={{ color: "var(--text-muted)" }}
                  >
                    →
                  </span>
                )}
                <span
                  className="rounded-md px-2.5 py-1 text-xs font-semibold"
                  style={{
                    background: i === 0 ? "var(--accent)" : "var(--bg-card)",
                    color: i === 0 ? "var(--accent-text)" : "var(--text-primary)",
                    border: "1px solid var(--border-primary)",
                  }}
                  title={`${LEVEL_NAMES[period.level - 1] ?? `L${period.level}`} · ${formatDate(period.start_date)} → ${formatDate(period.end_date)}`}
                >
                  {period.lord}
                  <span
                    className="ml-1 text-[9px] font-normal opacity-70"
                  >
                    {LEVEL_NAMES[period.level - 1] ?? `L${period.level}`}
                  </span>
                </span>
              </span>
            ))}
          </div>
        )}
      </Card>

      {/* ── MD + AD progress ────────────────────────────────────────────── */}
      {md && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {/* Mahadasha progress */}
          <Card>
            <p
              className="mb-1.5 text-[10px] font-bold uppercase tracking-wider"
              style={{ color: "var(--text-muted)" }}
            >
              Mahadasha
            </p>
            <p className="mb-2 text-base font-bold" style={{ color: "var(--text-primary)" }}>
              {md.lord}
            </p>
            <div
              className="mb-1.5 h-1.5 w-full overflow-hidden rounded-full"
              style={{ background: "var(--border-primary)" }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${mdPct}%`,
                  background: "var(--accent)",
                }}
              />
            </div>
            <div
              className="flex justify-between text-[10px]"
              style={{ color: "var(--text-secondary)" }}
            >
              <span>{mdPct}% elapsed</span>
              <span>{durationLabel(mdDaysLeft)} left</span>
            </div>
            <p className="mt-1 text-[10px]" style={{ color: "var(--text-muted)" }}>
              {formatDate(md.start_date)} → {formatDate(md.end_date)}
            </p>
          </Card>

          {/* Antardasha progress */}
          {ad ? (
            <Card>
              <p
                className="mb-1.5 text-[10px] font-bold uppercase tracking-wider"
                style={{ color: "var(--text-muted)" }}
              >
                Antardasha (in {md.lord})
              </p>
              <p className="mb-2 text-base font-bold" style={{ color: "var(--text-primary)" }}>
                {ad.lord}
              </p>
              <div
                className="mb-1.5 h-1.5 w-full overflow-hidden rounded-full"
                style={{ background: "var(--border-primary)" }}
              >
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${adPct}%`,
                    background: "var(--accent)",
                    opacity: 0.7,
                  }}
                />
              </div>
              <div
                className="flex justify-between text-[10px]"
                style={{ color: "var(--text-secondary)" }}
              >
                <span>{adPct}% elapsed</span>
                <span>{durationLabel(adDaysLeft)} left</span>
              </div>
              <p className="mt-1 text-[10px]" style={{ color: "var(--text-muted)" }}>
                {formatDate(ad.start_date)} → {formatDate(ad.end_date)}
              </p>
            </Card>
          ) : (
            <Card>
              <p
                className="text-xs"
                style={{ color: "var(--text-secondary)" }}
              >
                No Antardasha active within computed depth.
              </p>
            </Card>
          )}
        </div>
      )}

      {/* ── MD–AD Lord Relationship ─────────────────────────────────────── */}
      {md && ad && (
        <Card>
          <h4
            className="mb-1 text-[10px] font-bold uppercase tracking-wider"
            style={{ color: "var(--text-muted)" }}
          >
            MD–AD Sambandha
          </h4>
          <p className="text-sm" style={{ color: "var(--text-primary)" }}>
            {md.lord} Mahadasha · {ad.lord} Antardasha
          </p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
            The Antardasha lord activates significations of both{" "}
            <strong style={{ color: "var(--text-primary)" }}>{md.lord}</strong> and{" "}
            <strong style={{ color: "var(--text-primary)" }}>{ad.lord}</strong> simultaneously
            during this sub-period.
          </p>
        </Card>
      )}
    </div>
  );
}
