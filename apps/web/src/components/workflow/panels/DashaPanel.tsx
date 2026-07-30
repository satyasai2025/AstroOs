"use client";

import { useMemo, useState } from "react";
import { Card, TreeView, type TreeNode } from "@/components/ui";
import type { DashaPeriodResponse, DashaTreeResponse } from "@/lib/types";

const LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"];

function periodToNode(period: DashaPeriodResponse, path: string): TreeNode {
  return {
    key: path,
    label: `${period.lord} — ${LEVEL_NAMES[period.level - 1] ?? `Level ${period.level}`} (${period.start_date} → ${period.end_date})`,
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

export function DashaPanel({ dasha }: { dasha: DashaTreeResponse }) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const treeData = useMemo(
    () => dasha.mahadashas.map((period, i) => periodToNode(period, `${i}`)),
    [dasha.mahadashas],
  );

  const selected = selectedKey ? findPeriod(dasha.mahadashas, selectedKey) : null;

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          {dasha.system} Dasha
        </h3>
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          Trigger: {dasha.trigger_planet} · {dasha.trigger_nakshatra} nakshatra · Total cycle:{" "}
          {dasha.total_cycle_years} years
        </p>
      </Card>

      {/* Mahadasha bar strip — proportional width per period against the total cycle */}
      <Card>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
          Mahadasha Timeline
        </h4>
        <div className="flex h-8 w-full overflow-hidden rounded-md">
          {dasha.mahadashas.map((period, i) => {
            const widthPct = (period.duration_days / (dasha.total_cycle_years * 365.25)) * 100;
            const active = selectedKey === `${i}`;
            return (
              <button
                key={`${period.lord}-${period.start_date}-${i}`}
                type="button"
                onClick={() => setSelectedKey(`${i}`)}
                title={`${period.lord} (${period.start_date} → ${period.end_date})`}
                className="flex items-center justify-center overflow-hidden text-[10px] font-semibold transition"
                style={{
                  width: `${Math.max(widthPct, 3)}%`,
                  backgroundColor: active ? "var(--accent)" : "var(--bg-card)",
                  color: active ? "var(--accent-text)" : "var(--text-secondary)",
                  border: "1px solid var(--border-primary)",
                  borderLeft: i === 0 ? "1px solid var(--border-primary)" : "none",
                }}
              >
                {period.lord}
              </button>
            );
          })}
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
            Period Hierarchy
          </h4>
          <TreeView data={treeData} activeKey={selectedKey ?? undefined} onSelect={setSelectedKey} />
        </Card>

        <Card>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
            Period Detail
          </h4>
          {selected ? (
            <dl className="space-y-1.5 text-sm">
              <div className="flex justify-between">
                <dt style={{ color: "var(--text-muted)" }}>Lord</dt>
                <dd style={{ color: "var(--text-primary)" }}>{selected.lord}</dd>
              </div>
              <div className="flex justify-between">
                <dt style={{ color: "var(--text-muted)" }}>Level</dt>
                <dd style={{ color: "var(--text-primary)" }}>{LEVEL_NAMES[selected.level - 1] ?? selected.level}</dd>
              </div>
              <div className="flex justify-between">
                <dt style={{ color: "var(--text-muted)" }}>Start</dt>
                <dd style={{ color: "var(--text-primary)" }}>{selected.start_date}</dd>
              </div>
              <div className="flex justify-between">
                <dt style={{ color: "var(--text-muted)" }}>End</dt>
                <dd style={{ color: "var(--text-primary)" }}>{selected.end_date}</dd>
              </div>
              <div className="flex justify-between">
                <dt style={{ color: "var(--text-muted)" }}>Duration</dt>
                <dd style={{ color: "var(--text-primary)" }}>{selected.duration_days} days</dd>
              </div>
              <div className="flex justify-between">
                <dt style={{ color: "var(--text-muted)" }}>Sub-periods</dt>
                <dd style={{ color: "var(--text-primary)" }}>{selected.sub_periods.length}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Click a period in the timeline or hierarchy to see its details.
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
