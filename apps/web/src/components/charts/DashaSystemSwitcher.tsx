"use client";

import { useEffect, useState } from "react";
import { computeDasha, getDashaSystems } from "@/lib/dasha-api";
import { DASHA_SYSTEM_OPTIONS } from "@/lib/chart-alignment";
import type {
  AyanamsaCode,
  DashaSystemCode,
  DashaSystemInfo,
  DashaTreeResponse,
  HouseSystemCode,
} from "@/lib/types";

export interface DashaBirthParams {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: AyanamsaCode;
  house_system: HouseSystemCode;
}

/**
 * Minimal, non-animated dasha-system switcher. Calls the per-system
 * /dasha/{system} endpoint directly (apps/api/routers/dasha.py) so
 * switching doesn't require re-running the full workflow analysis.
 */
export function DashaSystemSwitcher({
  current,
  birthParams,
  onChange,
}: {
  current: string;
  birthParams?: DashaBirthParams;
  onChange: (tree: DashaTreeResponse) => void;
}) {
  const [systemOptions, setSystemOptions] = useState<DashaSystemInfo[]>(
    DASHA_SYSTEM_OPTIONS.map((o) => ({ system: o.value, label: o.label, category: "nakshatra" })),
  );
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  if (!birthParams) return null;

  async function handleChange(system: DashaSystemCode) {
    if (system === current) return;
    setSwitching(true);
    setError(null);
    try {
      const tree = await computeDasha(system, { ...birthParams!, persist: false });
      onChange(tree);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to switch dasha system.");
    } finally {
      setSwitching(false);
    }
  }

  return (
    <div className="mb-3 flex items-center gap-3">
      <label className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
        Dasha System
      </label>
      <select
        value={current}
        disabled={switching}
        onChange={(e) => handleChange(e.target.value as DashaSystemCode)}
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
      {error && (
        <span className="text-xs" style={{ color: "var(--color-danger, #f87171)" }}>
          {error}
        </span>
      )}
    </div>
  );
}
