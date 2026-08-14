"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useWorkflowStore } from "@/lib/store";
import { ApiError } from "@/lib/api";
import type {
  AyanamsaCode,
  BirthChartSummary,
  DashaSystemCode,
  HouseSystemCode,
  WorkflowAnalysisRequest,
} from "@/lib/types";

const AYANAMSA_OPTIONS: { value: AyanamsaCode; label: string }[] = [
  { value: "lahiri", label: "Lahiri" },
  { value: "kp", label: "KP" },
  { value: "raman", label: "Raman" },
  { value: "yukteshwar", label: "Yukteshwar" },
  { value: "fagan_bradley", label: "Fagan-Bradley" },
  { value: "true_chitra", label: "True Chitra" },
  { value: "true_pushya", label: "True Pushya" },
];

const HOUSE_SYSTEM_OPTIONS: { value: HouseSystemCode; label: string }[] = [
  { value: "W", label: "Whole Sign" },
  { value: "P", label: "Placidus" },
  { value: "K", label: "Koch" },
  { value: "E", label: "Equal" },
];

// Same non-blocking advisory as BirthDetailsForm — see that component's
// comment for why this isn't a hard rule for anything except KP.
const AYANAMSA_HOUSE_SYSTEM_ADVISORY: Partial<Record<AyanamsaCode, string>> = {
  yukteshwar:
    "Sri Yukteshwar ayanamsa is conventionally paired with Whole Sign (Rashi) houses. (Sripathi/Bhava Chalit, the other traditional pairing, isn't supported as a house system yet.)",
};

const DASHA_SYSTEM_OPTIONS: { value: DashaSystemCode; label: string }[] = [
  { value: "vimshottari", label: "Vimshottari" },
  { value: "yogini", label: "Yogini" },
  { value: "ashtottari", label: "Ashtottari" },
  { value: "kalachakra", label: "Kalachakra" },
  { value: "chara", label: "Chara (Jaimini)" },
  { value: "narayana", label: "Narayana (Jaimini)" },
];

interface RecomputeChartModalProps {
  chart: BirthChartSummary;
  onClose: () => void;
}

/**
 * Lets you re-run the Unified Analysis Pipeline for an already-saved
 * chart's birth data (datetime + lat/lon, which the saved-charts summary
 * now includes — see apps/api/schemas/horoscope.py's
 * BirthChartSummarySchema), but with a DIFFERENT ayanamsa / house system
 * / dasha system, without re-typing the birth place or date.
 *
 * Reuses the exact same useAnalyzeWorkflow() mutation and
 * useWorkflowStore the Dashboard's BirthDetailsForm uses — this is not a
 * new backend endpoint, just a different, birth-data-prefilled entry
 * point into the same POST /api/v1/workflow/analyze call. get_or_create's
 * natural-key dedup on the backend (birth moment + location + ayanamsa +
 * house system) means recomputing with the SAME settings reuses the
 * existing birth_charts row rather than creating a duplicate; a
 * different ayanamsa/house_system creates a new row, same as if you'd
 * typed the birth data in twice with different settings on the Dashboard.
 */
export function RecomputeChartModal({ chart, onClose }: RecomputeChartModalProps) {
  const router = useRouter();
  const analyze = useAnalyzeWorkflow();
  const setResult = useWorkflowStore((s) => s.setResult);

  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>(chart.ayanamsa as AyanamsaCode);
  const [houseSystem, setHouseSystem] = useState<HouseSystemCode>(chart.house_system as HouseSystemCode);
  const [dashaSystem, setDashaSystem] = useState<DashaSystemCode>("vimshottari");
  const [includeVargas, setIncludeVargas] = useState(true);

  // Same KP Ayanamsa + Placidus lock as BirthDetailsForm — see that
  // component's comment for why.
  const houseSystemLockedByKp = ayanamsa === "kp";
  useEffect(() => {
    if (houseSystemLockedByKp) {
      setHouseSystem("P");
    }
  }, [houseSystemLockedByKp]);

  const errorMessage =
    analyze.error instanceof ApiError
      ? analyze.error.detail
      : analyze.error
        ? "An unexpected error occurred. Please try again."
        : null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: chart.birth_datetime_utc,
      latitude: chart.birth_latitude,
      longitude: chart.birth_longitude,
      ayanamsa,
      house_system: houseSystem,
      dasha_system: dashaSystem,
      include_vargas: includeVargas,
      subject_name: chart.subject_name,
      place_name: chart.place_name,
    };
    analyze.mutate(request, {
      onSuccess: (data) => {
        setResult(data, request);
        onClose();
        // Charts live under My Charts now, not the dashboard — see
        // apps/web/src/app/charts/[chartId]/page.tsx.
        router.push(`/charts/${data.chart_id}`);
      },
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`Recompute ${chart.subject_name}'s chart with different settings`}
    >
      <div className="glass-card w-full max-w-md p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
            Recompute — {chart.subject_name}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-sm"
            style={{ color: "var(--text-muted)" }}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div
          className="mb-4 rounded-lg border p-3 text-xs"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}
        >
          <p>Birth (UTC): {new Date(chart.birth_datetime_utc).toLocaleString()}</p>
          <p>
            Location: {chart.birth_latitude.toFixed(4)}, {chart.birth_longitude.toFixed(4)}
            {chart.place_name ? ` (${chart.place_name})` : ""}
          </p>
          <p className="mt-1" style={{ color: "var(--text-muted)" }}>
            Same birth data as saved — only the settings below change.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              Ayanamsa
            </label>
            <select
              value={ayanamsa}
              onChange={(e) => setAyanamsa(e.target.value as AyanamsaCode)}
              className="field-input w-full"
            >
              {AYANAMSA_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            {AYANAMSA_HOUSE_SYSTEM_ADVISORY[ayanamsa] && (
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                {AYANAMSA_HOUSE_SYSTEM_ADVISORY[ayanamsa]}
              </p>
            )}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              House System
            </label>
            <select
              value={houseSystem}
              onChange={(e) => setHouseSystem(e.target.value as HouseSystemCode)}
              className="field-input w-full"
              disabled={houseSystemLockedByKp}
            >
              {HOUSE_SYSTEM_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            {houseSystemLockedByKp && (
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                Locked to Placidus — KP practice requires KP Ayanamsa + Placidus.
              </p>
            )}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              Dasha System
            </label>
            <select
              value={dashaSystem}
              onChange={(e) => setDashaSystem(e.target.value as DashaSystemCode)}
              className="field-input w-full"
            >
              {DASHA_SYSTEM_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
            <input
              type="checkbox"
              checked={includeVargas}
              onChange={(e) => setIncludeVargas(e.target.checked)}
            />
            Compute all 15 divisional charts (Vargas)
          </label>

          {errorMessage && (
            <p className="text-xs" style={{ color: "var(--chart-ascendant)" }} role="alert">
              {errorMessage}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-ghost px-3 py-1.5 text-xs">
              Cancel
            </button>
            <button type="submit" disabled={analyze.isPending} className="btn-primary px-3 py-1.5 text-xs">
              {analyze.isPending ? "Computing…" : "Recompute"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
