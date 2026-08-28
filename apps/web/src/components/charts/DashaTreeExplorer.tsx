"use client";

import { useMemo, useState } from "react";
import { TreeView, type TreeNode } from "@/components/ui";
import { LEVEL_CONFIG } from "./DashaHeroCard";
import type { DashaPeriodResponse, DashaTreeResponse } from "@/lib/types";

function periodToNode(period: DashaPeriodResponse, path: string): TreeNode {
  const cfg = LEVEL_CONFIG[period.level] || LEVEL_CONFIG[1];
  return {
    key: path,
    label: `${period.lord} — ${cfg.short} (${period.start_date} → ${period.end_date})`,
    children: period.sub_periods.map((sub, i) => periodToNode(sub, `${path}.${i}`)),
  };
}

function findPeriod(periods: DashaPeriodResponse[], path: string): DashaPeriodResponse | null {
  const indices = path.split(".").map(Number);
  let list = periods;
  let found: DashaPeriodResponse | null = null;
  for (const idx of indices) {
    found = list[idx] ?? null;
    if (!found) return null;
    list = found.sub_periods;
  }
  return found;
}

export function DashaTreeExplorer({ dasha }: { dasha: DashaTreeResponse }) {
  const [selectedKey, setSelectedKey] = useState<string | null>("0");

  const treeData = useMemo(
    () => dasha.mahadashas.map((period, i) => periodToNode(period, `${i}`)),
    [dasha.mahadashas],
  );

  const selected = selectedKey ? findPeriod(dasha.mahadashas, selectedKey) : null;
  const selectedCfg = selected ? LEVEL_CONFIG[selected.level] || LEVEL_CONFIG[1] : null;

  return (
    <div className="space-y-4">
      {/* ── Mahadasha Bar Strip ────────────────────────────────────── */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
        <div className="mb-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-indigo-500" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Mahadasha Full-Cycle Span ({dasha.total_cycle_years}y)
            </h4>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            {dasha.mahadashas.length} Mahadashas
          </span>
        </div>

        <div className="flex h-9 w-full overflow-hidden rounded-lg bg-slate-800/80 p-0.5 border border-slate-700/60 gap-1">
          {dasha.mahadashas.map((period, i) => {
            const widthPct = (period.duration_days / (dasha.total_cycle_years * 365.25)) * 100;
            const active = selectedKey === `${i}`;
            return (
              <button
                key={`${period.lord}-${period.start_date}-${i}`}
                type="button"
                onClick={() => setSelectedKey(`${i}`)}
                title={`${period.lord} MD (${period.start_date} → ${period.end_date}) · ${Math.round(period.duration_days / 365.25)} yrs`}
                className={`flex flex-col items-center justify-center rounded px-1 transition ${
                  active
                    ? "bg-indigo-600 text-white font-bold shadow-xs"
                    : "bg-slate-900/80 text-slate-300 hover:bg-slate-700/80"
                }`}
                style={{ width: `${Math.max(widthPct, 4)}%` }}
              >
                <span className="text-[11px] leading-none">{period.lord}</span>
                <span className="text-[8px] opacity-75 leading-tight">
                  {Math.round(period.duration_days / 365.25)}y
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Hierarchy Tree & Detail Panel ───────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.3fr_1fr]">
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Period Hierarchy (5-Levels)
            </h4>
            <span className="text-[11px] text-slate-400">Click to expand sub-periods</span>
          </div>
          <div className="max-h-[420px] overflow-y-auto pr-1">
            <TreeView data={treeData} activeKey={selectedKey ?? undefined} onSelect={setSelectedKey} />
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 flex flex-col justify-between shadow-sm">
          <div>
            <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-200">
              Period Details
            </h4>
            {selected && selectedCfg ? (
              <div className="space-y-3">
                <div className={`flex items-center justify-between rounded-lg p-3 border ${selectedCfg.bg} ${selectedCfg.border}`}>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Selected Lord</span>
                    <h3 className="text-base font-bold text-slate-100">{selected.lord}</h3>
                  </div>
                  <span className="rounded-full bg-slate-900 px-2.5 py-1 text-xs font-bold uppercase text-slate-200 border border-slate-700">
                    {selectedCfg.label} ({selectedCfg.short})
                  </span>
                </div>

                <dl className="space-y-2 rounded-lg bg-slate-950/60 p-3 text-xs border border-slate-800/80">
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Hierarchy Depth:</dt>
                    <dd className="font-semibold text-slate-200">Level {selected.level} of 5</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Start Date:</dt>
                    <dd className="font-mono text-cyan-400">{selected.start_date}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">End Date:</dt>
                    <dd className="font-mono text-cyan-400">{selected.end_date}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Duration:</dt>
                    <dd className="font-mono font-semibold text-amber-400">
                      {selected.duration_days} days ({Math.round((selected.duration_days / 365.25) * 10) / 10}y)
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-slate-400">Sub-Periods:</dt>
                    <dd className="font-semibold text-slate-200">{selected.sub_periods.length}</dd>
                  </div>
                </dl>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-400">
                Click any period in the tree or timeline to inspect its full period specifications.
              </div>
            )}
          </div>

          <div className="mt-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 p-2.5 text-xs text-indigo-300">
            💡 <strong>Hierarchy Rule:</strong> Each Mahadasha is recursively subdivided in proportion to the cycle years of each planet.
          </div>
        </div>
      </div>
    </div>
  );
}
