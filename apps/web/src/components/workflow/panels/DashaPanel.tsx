"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, TreeView, type TreeNode } from "@/components/ui";
import { computeDasha, getDashaSystems } from "@/lib/dasha-api";
import { DASHA_SYSTEM_OPTIONS } from "@/lib/chart-alignment";
import type {
  AyanamsaCode,
  DashaPeriodResponse,
  DashaSystemCode,
  DashaSystemInfo,
  DashaTreeResponse,
  HouseSystemCode,
} from "@/lib/types";

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

export interface DashaBirthParams {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: AyanamsaCode;
  house_system: HouseSystemCode;
}

export function DashaPanel({
  dasha,
  birthParams,
}: {
  dasha: DashaTreeResponse;
  /** When provided, enables the dasha-system switcher; otherwise the panel
   *  renders read-only exactly as before. */
  birthParams?: DashaBirthParams;
}) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [activeDasha, setActiveDasha] = useState<DashaTreeResponse>(dasha);
  const [systemOptions, setSystemOptions] = useState<DashaSystemInfo[]>(
    DASHA_SYSTEM_OPTIONS.map((o) => ({ system: o.value, label: o.label, category: "nakshatra" })),
  );
  const [switching, setSwitching] = useState(false);
  const [switchError, setSwitchError] = useState<string | null>(null);

  // Reset to the freshly-supplied tree whenever the parent hands us a new one
  // (e.g. a brand new analysis), rather than sticking with a stale switch.
  useEffect(() => {
    setActiveDasha(dasha);
    setSelectedKey(null);
    setSwitchError(null);
  }, [dasha]);

  useEffect(() => {
    if (!birthParams) return;
    let cancelled = false;
    getDashaSystems()
      .then((systems) => {
        if (!cancelled && systems.length > 0) setSystemOptions(systems);
      })
      .catch(() => {
        // Keep the static fallback list — switcher still works via /dasha/{system}.
      });
    return () => {
      cancelled = true;
    };
  }, [birthParams]);

  async function handleSystemChange(system: DashaSystemCode) {
    if (!birthParams || system === activeDasha.system) return;
    setSwitching(true);
    setSwitchError(null);
    try {
      const next = await computeDasha(system, { ...birthParams, persist: false });
      setActiveDasha(next);
      setSelectedKey(null);
    } catch (err) {
      setSwitchError(err instanceof Error ? err.message : "Failed to switch dasha system.");
    } finally {
      setSwitching(false);
    }
  }

  const treeData = useMemo(
    () => activeDasha.mahadashas.map((period, i) => periodToNode(period, `${i}`)),
    [activeDasha.mahadashas],
  );

  const selected = selectedKey ? findPeriod(activeDasha.mahadashas, selectedKey) : null;

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-1 flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            {activeDasha.system} Dasha
          </h3>
          {birthParams && (
            <select
              value={activeDasha.system}
              disabled={switching}
              onChange={(e) => handleSystemChange(e.target.value as DashaSystemCode)}
              className="rounded-md border px-2 py-1 text-xs"
              style={{
                borderColor: "var(--border-primary)",
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
              }}
              aria-label="Dasha system"
            >
              {systemOptions.map((opt) => (
                <option key={opt.system} value={opt.system}>
                  {opt.label}
                </option>
              ))}
            </select>
          )}
        </div>
        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
          Trigger: {activeDasha.trigger_planet} · {activeDasha.trigger_nakshatra} nakshatra · Total cycle:{" "}
          {activeDasha.total_cycle_years} years
        </p>
        {switchError && (
          <p className="mt-1 text-xs" style={{ color: "var(--color-danger, #f87171)" }}>
            {switchError}
          </p>
        )}
      </Card>

      {/* Mahadasha bar strip — proportional width per period against the total cycle */}
      <Card>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
          Mahadasha Timeline
        </h4>
        <div className="flex h-8 w-full overflow-hidden rounded-md">
          {activeDasha.mahadashas.map((period, i) => {
            const widthPct = (period.duration_days / (activeDasha.total_cycle_years * 365.25)) * 100;
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
