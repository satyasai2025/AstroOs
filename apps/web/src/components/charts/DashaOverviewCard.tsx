"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui";
import { getCurrentPeriodChain } from "@/components/charts/TransitTimeline";
import type { DashaTreeResponse } from "@/lib/types";

const LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"];

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

/**
 * "Dasha Dashboard" panel from the architecture diagram — a quick-glance
 * summary (system, trigger, cycle length, current period chain) assembled
 * entirely from data already on the DashaTreeResponse, no new fetching.
 */
export function DashaOverviewCard({ dasha }: { dasha: DashaTreeResponse }) {
  const chain = useMemo(() => getCurrentPeriodChain(dasha.mahadashas), [dasha.mahadashas]);

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          {dasha.system} Dasha
        </h3>
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          Trigger: {dasha.trigger_planet}
          {dasha.trigger_nakshatra ? ` · ${dasha.trigger_nakshatra} nakshatra` : ""} · Total cycle:{" "}
          {dasha.total_cycle_years} years
        </p>
      </Card>

      <Card>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
          Current Period
        </h4>
        {chain.length === 0 ? (
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            No active period found for today within this tree's computed depth.
          </p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              {chain.map((period, i) => (
                <span key={`${period.lord}-${period.level}`} className="flex items-center gap-2">
                  {i > 0 && <span style={{ color: "var(--text-muted)" }}>→</span>}
                  <span
                    className="rounded-md px-2 py-1"
                    style={{ backgroundColor: "var(--bg-card)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
                    title={`${LEVEL_NAMES[period.level - 1] ?? `Level ${period.level}`} (${formatDate(period.start_date)} → ${formatDate(period.end_date)})`}
                  >
                    {period.lord}
                  </span>
                </span>
              ))}
            </div>
            <p className="mt-2 text-xs" style={{ color: "var(--text-secondary)" }}>
              {formatDate(chain[chain.length - 1].start_date)} — {formatDate(chain[chain.length - 1].end_date)}
            </p>
          </>
        )}
      </Card>
    </div>
  );
}
