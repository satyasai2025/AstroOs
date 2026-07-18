"use client";

import { useState } from "react";
import type { DashaPeriodResponse, DashaTreeResponse } from "@/lib/types";

const LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"];

function PeriodRow({ period, depth }: { period: DashaPeriodResponse; depth: number }) {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = period.children.length > 0;

  return (
    <div style={{ marginLeft: depth * 16 }}>
      <button
        type="button"
        onClick={() => hasChildren && setExpanded((v) => !v)}
        className="flex w-full items-center justify-between border-b border-white/5 py-2 text-left text-sm hover:bg-white/5"
        disabled={!hasChildren}
      >
        <span className="flex items-center gap-2">
          {hasChildren && <span className="text-xs text-slate-500">{expanded ? "▾" : "▸"}</span>}
          <span className="font-medium capitalize text-slate-200">{period.lord}</span>
          <span className="text-xs text-slate-500">
            {LEVEL_NAMES[period.level - 1] ?? `Level ${period.level}`}
          </span>
        </span>
        <span className="text-xs text-slate-400">
          {period.start_date} → {period.end_date} ({period.duration_days}d)
        </span>
      </button>
      {expanded &&
        period.children.map((sub, i) => (
          <PeriodRow key={`${sub.lord}-${sub.start_date}-${i}`} period={sub} depth={depth + 1} />
        ))}
    </div>
  );
}

export function DashaPanel({ dasha }: { dasha: DashaTreeResponse }) {
  return (
    <div className="glass-card p-5">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
        {dasha.system} Dasha
      </h3>
      <p className="mb-3 text-xs text-slate-500">
        Trigger: {dasha.trigger_planet} · {dasha.trigger_nakshatra} nakshatra · Total cycle:{" "}
        {dasha.total_cycle_years} years
      </p>
      <div>
        {dasha.mahadashas.map((period, i) => (
          <PeriodRow key={`${period.lord}-${period.start_date}-${i}`} period={period} depth={0} />
        ))}
      </div>
    </div>
  );
}
