"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { useWorkflowStore } from "@/lib/store";
import { useTimezoneResolution } from "@/lib/geocoding";
import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import { ApiError } from "@/lib/api";
import type {
  AyanamsaCode,
  BirthChartSummary,
  DashaSystemCode,
  HouseSystemCode,
  PlaceResultResponse,
  WorkflowAnalysisRequest,
} from "@/lib/types";
import {
  AYANAMSA_OPTIONS,
  HOUSE_SYSTEM_OPTIONS,
  DASHA_SYSTEM_OPTIONS,
  resolveAstrologicalAlignment,
} from "@/lib/chart-alignment";

const AYANAMSA_HOUSE_SYSTEM_ADVISORY: Partial<Record<AyanamsaCode, string>> = {
  yukteshwar:
    "Sri Yukteshwar ayanamsa is conventionally paired with Whole Sign (Rashi) houses.",
};

interface RecomputeChartModalProps {
  chart: BirthChartSummary;
  onClose: () => void;
}

function parseIsoToDateAndTime(iso: string): { dateStr: string; timeStr: string } {
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return { dateStr: "", timeStr: "" };
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const min = String(d.getMinutes()).padStart(2, "0");
    return { dateStr: `${yyyy}-${mm}-${dd}`, timeStr: `${hh}:${min}` };
  } catch {
    return { dateStr: "", timeStr: "" };
  }
}

function localToUtcIso(dateStr: string, timeStr: string, utcOffsetMinutes: number): string {
  const [year, month, day] = dateStr.split("-").map(Number);
  const timeParts = timeStr.split(":").map(Number);
  const hour = timeParts[0] ?? 0;
  const minute = timeParts[1] ?? 0;
  const second = timeParts[2] ?? 0;
  const localAsUtcMs = Date.UTC(year, month - 1, day, hour, minute, second);
  const trueUtcMs = localAsUtcMs - utcOffsetMinutes * 60_000;
  return new Date(trueUtcMs).toISOString();
}

function formatOffset(minutes: number): string {
  const sign = minutes >= 0 ? "+" : "-";
  const abs = Math.abs(minutes);
  const hh = String(Math.floor(abs / 60)).padStart(2, "0");
  const mm = String(abs % 60).padStart(2, "0");
  return `UTC${sign}${hh}:${mm}`;
}

export function RecomputeChartModal({ chart, onClose }: RecomputeChartModalProps) {
  const router = useRouter();
  const analyze = useAnalyzeWorkflow();
  const setResult = useWorkflowStore((s) => s.setResult);

  // Initial local date/time extracted from chart ISO
  const initial = useMemo(() => parseIsoToDateAndTime(chart.birth_datetime_utc), [chart.birth_datetime_utc]);

  // Form states: Identity & Birth Parameters
  const [subjectName, setSubjectName] = useState(chart.subject_name || "");
  const [birthDate, setBirthDate] = useState(initial.dateStr);
  const [birthTime, setBirthTime] = useState(initial.timeStr);

  // Place states
  const [placeSearchText, setPlaceSearchText] = useState(chart.place_name || "");
  const [resolvedPlace, setResolvedPlace] = useState<PlaceResultResponse | null>(() => {
    if (chart.birth_latitude && chart.birth_longitude) {
      return {
        display_name: chart.place_name || `${chart.birth_latitude}, ${chart.birth_longitude}`,
        latitude: chart.birth_latitude,
        longitude: chart.birth_longitude,
        country: null,
        state: null,
      };
    }
    return null;
  });

  const [manualCoords, setManualCoords] = useState(false);
  const [manualLat, setManualLat] = useState(String(chart.birth_latitude ?? ""));
  const [manualLon, setManualLon] = useState(String(chart.birth_longitude ?? ""));

  // Astrological Settings
  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>((chart.ayanamsa as AyanamsaCode) || "lahiri");
  const [houseSystem, setHouseSystem] = useState<HouseSystemCode>((chart.house_system as HouseSystemCode) || "W");
  const [dashaSystem, setDashaSystem] = useState<DashaSystemCode>("vimshottari");
  const [includeVargas, setIncludeVargas] = useState(true);
  const [showAstroSettings, setShowAstroSettings] = useState(false);

  const [validationError, setValidationError] = useState<string | null>(null);

  // Alignment matrix resolution
  const alignment = useMemo(
    () => resolveAstrologicalAlignment({ ayanamsa, houseSystem, dashaSystem }, "init"),
    [ayanamsa, houseSystem, dashaSystem]
  );

  useEffect(() => {
    if (alignment.values.ayanamsa !== ayanamsa) setAyanamsa(alignment.values.ayanamsa);
    if (alignment.values.houseSystem !== houseSystem) setHouseSystem(alignment.values.houseSystem);
    if (alignment.values.dashaSystem !== dashaSystem) setDashaSystem(alignment.values.dashaSystem);
  }, [alignment.values]);

  const houseSystemLockedByKp = ayanamsa === "kp";
  useEffect(() => {
    if (houseSystemLockedByKp) {
      setHouseSystem("P");
    }
  }, [houseSystemLockedByKp]);

  // Effective coordinates calculation
  const manualLatNum = manualLat === "" ? null : Number(manualLat);
  const manualLonNum = manualLon === "" ? null : Number(manualLon);
  const manualCoordsValid =
    manualLatNum !== null &&
    !Number.isNaN(manualLatNum) &&
    manualLatNum >= -90 &&
    manualLatNum <= 90 &&
    manualLonNum !== null &&
    !Number.isNaN(manualLonNum) &&
    manualLonNum >= -180 &&
    manualLonNum <= 180;

  const effectiveLatitude = manualCoords
    ? manualCoordsValid
      ? manualLatNum
      : null
    : resolvedPlace?.latitude ?? chart.birth_latitude;
  const effectiveLongitude = manualCoords
    ? manualCoordsValid
      ? manualLonNum
      : null
    : resolvedPlace?.longitude ?? chart.birth_longitude;

  const tzQuery = useTimezoneResolution(effectiveLatitude, effectiveLongitude, birthDate || null);

  const errorMessage =
    validationError ||
    (analyze.error instanceof ApiError
      ? analyze.error.detail
      : analyze.error
      ? "An unexpected error occurred. Please try again."
      : null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setValidationError(null);

    if (!subjectName.trim()) {
      setValidationError("Subject name is required.");
      return;
    }
    if (!birthDate || !birthTime) {
      setValidationError("Birth date and time are both required.");
      return;
    }
    if (effectiveLatitude === null || effectiveLongitude === null) {
      setValidationError(
        manualCoords
          ? "Enter valid coordinates: Latitude (-90 to 90) and Longitude (-180 to 180)."
          : "Please search and select a birth place."
      );
      return;
    }

    let birthDatetimeUtc: string;
    if (tzQuery.data) {
      birthDatetimeUtc = localToUtcIso(birthDate, birthTime, tzQuery.data.utc_offset_minutes);
    } else {
      // Fallback: treat user date & time as UTC or compute ISO
      const [y, m, d] = birthDate.split("-").map(Number);
      const [h, min] = birthTime.split(":").map(Number);
      birthDatetimeUtc = new Date(Date.UTC(y, m - 1, d, h || 0, min || 0)).toISOString();
    }

    const request: WorkflowAnalysisRequest = {
      birth_datetime_utc: birthDatetimeUtc,
      latitude: effectiveLatitude,
      longitude: effectiveLongitude,
      ayanamsa,
      house_system: houseSystem,
      dasha_system: dashaSystem,
      include_vargas: includeVargas,
      subject_name: subjectName.trim(),
      place_name: placeSearchText.trim() || resolvedPlace?.display_name || chart.place_name || undefined,
      persist: true,
      chart_id: chart.id,
    };

    analyze.mutate(request, {
      onSuccess: (data) => {
        setResult(data, request);
        onClose();
        router.push(`/charts/${data.chart_id}`);
      },
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label={`Edit details for ${chart.subject_name}`}
    >
      <div className="glass-card w-full max-w-lg overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="mb-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Edit Chart Details
            </h2>
            <p className="text-xs text-slate-700 dark:text-slate-300 font-medium">
              Update name, birth date, time, location, or astrological calculation settings.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="space-y-4 overflow-y-auto pr-1 flex-1">
          {/* 1. Name Input */}
          <div>
            <label htmlFor="recompute-name" className="mb-1 block text-xs font-bold text-slate-700 dark:text-slate-300">
              Name / Subject
            </label>
            <input
              id="recompute-name"
              aria-label="Name or Subject"
              type="text"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
              placeholder="e.g. John Doe"
              className="field-input w-full"
              required
            />
          </div>

          {/* 2. Date & Time Inputs Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="recompute-date" className="mb-1 block text-xs font-bold text-slate-700 dark:text-slate-300">
                Birth Date (Local)
              </label>
              <input
                id="recompute-date"
                aria-label="Birth Date"
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                className="field-input w-full"
                required
              />
            </div>

            <div>
              <label htmlFor="recompute-time" className="mb-1 block text-xs font-bold text-slate-700 dark:text-slate-300">
                Birth Time (Local)
              </label>
              <input
                id="recompute-time"
                aria-label="Birth Time"
                type="time"
                step="60"
                value={birthTime}
                onChange={(e) => setBirthTime(e.target.value)}
                className="field-input w-full"
                required
              />
            </div>
          </div>

          {/* 3. Place Search & Location Details */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="recompute-place" className="text-xs font-bold text-slate-700 dark:text-slate-300">
                Birth Place
              </label>
              <button
                type="button"
                onClick={() => setManualCoords(!manualCoords)}
                className="text-[11px] text-cyan-600 dark:text-cyan-400 hover:underline font-semibold"
              >
                {manualCoords ? "Search by City Name" : "Enter Coordinates Manually"}
              </button>
            </div>

            {manualCoords ? (
              <div className="grid grid-cols-2 gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
                <div>
                  <label htmlFor="recompute-lat" className="text-[10px] uppercase font-bold text-slate-500">Latitude (-90 to 90)</label>
                  <input
                    id="recompute-lat"
                    aria-label="Latitude"
                    type="number"
                    step="any"
                    value={manualLat}
                    onChange={(e) => setManualLat(e.target.value)}
                    placeholder="e.g. 28.6139"
                    className="field-input w-full mt-1"
                  />
                </div>
                <div>
                  <label htmlFor="recompute-lon" className="text-[10px] uppercase font-bold text-slate-500">Longitude (-180 to 180)</label>
                  <input
                    id="recompute-lon"
                    aria-label="Longitude"
                    type="number"
                    step="any"
                    value={manualLon}
                    onChange={(e) => setManualLon(e.target.value)}
                    placeholder="e.g. 77.2090"
                    className="field-input w-full mt-1"
                  />
                </div>
              </div>
            ) : (
              <BirthPlaceSearch
                value={placeSearchText}
                onChange={setPlaceSearchText}
                onSelect={(place) => {
                  setResolvedPlace(place);
                  setPlaceSearchText(place.display_name);
                  setManualLat(String(place.latitude));
                  setManualLon(String(place.longitude));
                }}
                disabled={analyze.isPending}
              />
            )}

            {/* Resolved Location & Timezone Info Pill */}
            {effectiveLatitude !== null && effectiveLongitude !== null && (
              <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/60 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700/60">
                <span>
                  📍 {effectiveLatitude.toFixed(4)}°, {effectiveLongitude.toFixed(4)}°
                </span>
                {tzQuery.data && (
                  <span className="font-mono text-cyan-600 dark:text-cyan-400 font-semibold">
                    ⏱ {tzQuery.data.iana_name} ({formatOffset(tzQuery.data.utc_offset_minutes)})
                  </span>
                )}
                {tzQuery.isFetching && <span className="text-amber-500">Resolving timezone…</span>}
              </div>
            )}
          </div>

          {/* 4. Astrological Calculation Settings Toggle */}
          <div className="border-t border-slate-200 dark:border-slate-800 pt-3">
            <button
              type="button"
              onClick={() => setShowAstroSettings(!showAstroSettings)}
              className="flex w-full items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300 hover:text-cyan-500 transition"
            >
              <span>⚙️ Astrological Calculation Settings</span>
              <span className="text-slate-400 text-[10px]">
                {showAstroSettings ? "▲ Hide" : "▼ Show"}
              </span>
            </button>

            {showAstroSettings && (
              <div className="mt-3 space-y-3 p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
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
                    <p className="mt-1 text-[11px] text-amber-500">
                      {AYANAMSA_HOUSE_SYSTEM_ADVISORY[ayanamsa]}
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
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
                    <p className="mt-1 text-[11px] text-amber-500">
                      Locked to Placidus — KP practice requires KP Ayanamsa + Placidus.
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
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

                <label className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 cursor-pointer pt-1">
                  <input
                    type="checkbox"
                    checked={includeVargas}
                    onChange={(e) => setIncludeVargas(e.target.checked)}
                    className="rounded text-cyan-500"
                  />
                  Compute all 15 divisional charts (Vargas)
                </label>
              </div>
            )}
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="rounded-lg bg-rose-500/10 border border-rose-500/30 p-2.5 text-xs text-rose-600 dark:text-rose-400" role="alert">
              ⚠️ {errorMessage}
            </div>
          )}

          {/* Action Buttons Footer */}
          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={analyze.isPending || tzQuery.isFetching}
              className="rounded-lg bg-cyan-600 dark:bg-cyan-500 hover:bg-cyan-500 dark:hover:bg-cyan-400 px-4 py-2 text-xs font-bold text-white shadow-sm transition disabled:opacity-50"
            >
              {analyze.isPending ? "Recomputing Chart…" : "Save & Recompute"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
