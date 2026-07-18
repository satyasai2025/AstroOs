"use client";

import { useState } from "react";
import type {
  AyanamsaCode,
  DashaSystemCode,
  HouseSystemCode,
  PlaceResultResponse,
  WorkflowAnalysisRequest,
} from "@/lib/types";
import { useTimezoneResolution } from "@/lib/geocoding";
import { BirthPlaceSearch } from "./BirthPlaceSearch";

const AYANAMSA_OPTIONS: { value: AyanamsaCode; label: string }[] = [
  { value: "lahiri", label: "Lahiri" },
  { value: "kp", label: "KP" },
  { value: "raman", label: "Raman" },
  { value: "yukteshwar", label: "Yukteshwar" },
  { value: "fagan_bradley", label: "Fagan-Bradley" },
  { value: "true_chitra", label: "True Chitra" },
];

const HOUSE_SYSTEM_OPTIONS: { value: HouseSystemCode; label: string }[] = [
  { value: "W", label: "Whole Sign" },
  { value: "P", label: "Placidus" },
  { value: "K", label: "Koch" },
  { value: "E", label: "Equal" },
];

const DASHA_SYSTEM_OPTIONS: { value: DashaSystemCode; label: string }[] = [
  { value: "vimshottari", label: "Vimshottari" },
  { value: "yogini", label: "Yogini" },
  { value: "ashtottari", label: "Ashtottari" },
  { value: "kalachakra", label: "Kalachakra" },
  { value: "chara", label: "Chara (Jaimini)" },
  { value: "narayana", label: "Narayana (Jaimini)" },
];

interface Props {
  onSubmit: (request: WorkflowAnalysisRequest) => void;
  isPending: boolean;
  errorMessage: string | null;
}

/**
 * Converts a local calendar date+time at a known UTC offset into the
 * true UTC instant, without ever touching the browser's own timezone.
 * Date.UTC() treats the y/m/d/h/m/s as literal wall-clock numbers with
 * no timezone applied — from there, subtracting the birth place's
 * actual UTC offset (resolved server-side for this exact date, so it
 * already accounts for DST/historical zone rules) gives the correct
 * UTC instant.
 */
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

export function BirthDetailsForm({ onSubmit, isPending, errorMessage }: Props) {
  const [subjectName, setSubjectName] = useState("");
  const [birthDate, setBirthDate] = useState(""); // YYYY-MM-DD, local
  const [birthTime, setBirthTime] = useState(""); // HH:MM:SS, local

  const [placeSearchText, setPlaceSearchText] = useState("");
  const [resolvedPlace, setResolvedPlace] = useState<PlaceResultResponse | null>(null);

  const [manualOverride, setManualOverride] = useState(false);
  const [manualLatitude, setManualLatitude] = useState("");
  const [manualLongitude, setManualLongitude] = useState("");

  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>("lahiri");
  const [houseSystem, setHouseSystem] = useState<HouseSystemCode>("W");
  const [dashaSystem, setDashaSystem] = useState<DashaSystemCode>("vimshottari");
  const [includeVargas, setIncludeVargas] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Effective coordinates: manual entry wins when the override is on,
  // otherwise whatever the place search resolved.
  const manualLatNum = manualLatitude === "" ? null : Number(manualLatitude);
  const manualLonNum = manualLongitude === "" ? null : Number(manualLongitude);
  const manualCoordsValid =
    manualLatNum !== null && !Number.isNaN(manualLatNum) && manualLatNum >= -90 && manualLatNum <= 90 &&
    manualLonNum !== null && !Number.isNaN(manualLonNum) && manualLonNum >= -180 && manualLonNum <= 180;

  const effectiveLatitude = manualOverride ? (manualCoordsValid ? manualLatNum : null) : resolvedPlace?.latitude ?? null;
  const effectiveLongitude = manualOverride ? (manualCoordsValid ? manualLonNum : null) : resolvedPlace?.longitude ?? null;

  const tzQuery = useTimezoneResolution(effectiveLatitude, effectiveLongitude, birthDate || null);

  const locationResolved = effectiveLatitude !== null && effectiveLongitude !== null;
  const timezoneResolved = tzQuery.isSuccess && !!tzQuery.data;
  const canSubmit =
    !isPending && !!birthDate && !!birthTime && locationResolved && timezoneResolved;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!birthDate || !birthTime) {
      setValidationError("Birth date and time are both required.");
      return;
    }
    if (effectiveLatitude === null || effectiveLongitude === null) {
      setValidationError(
        manualOverride
          ? "Enter valid latitude (-90 to 90) and longitude (-180 to 180)."
          : "Search for and select a birth place.",
      );
      return;
    }
    if (!tzQuery.data) {
      setValidationError("Timezone could not be resolved for this location yet.");
      return;
    }

    const birthDatetimeUtc = localToUtcIso(birthDate, birthTime, tzQuery.data.utc_offset_minutes);

    onSubmit({
      birth_datetime_utc: birthDatetimeUtc,
      latitude: effectiveLatitude,
      longitude: effectiveLongitude,
      ayanamsa,
      house_system: houseSystem,
      dasha_system: dashaSystem,
      include_vargas: includeVargas,
      subject_name: subjectName.trim() || "Unnamed",
    });
  };

  const disabled = isPending;
  const shownError = validationError ?? errorMessage;

  return (
    <form onSubmit={handleSubmit} className="glass-card space-y-4 p-6">
      <div>
        <label htmlFor="subjectName" className="field-label">
          Subject Name
        </label>
        <input
          id="subjectName"
          type="text"
          value={subjectName}
          onChange={(e) => setSubjectName(e.target.value)}
          className="field-input"
          placeholder="Unnamed"
          disabled={disabled}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="birthDate" className="field-label">
            Birth Date
          </label>
          <input
            id="birthDate"
            type="date"
            required
            value={birthDate}
            onChange={(e) => setBirthDate(e.target.value)}
            className="field-input"
            disabled={disabled}
          />
        </div>
        <div>
          <label htmlFor="birthTime" className="field-label">
            Birth Time
          </label>
          <input
            id="birthTime"
            type="time"
            step="1"
            required
            value={birthTime}
            onChange={(e) => setBirthTime(e.target.value)}
            className="field-input"
            disabled={disabled}
          />
        </div>
      </div>
      <p className="-mt-2 text-xs text-slate-500">
        Local date and time at the birth place — not UTC. The birth place below determines
        the conversion.
      </p>

      <div>
        <div className="mb-1.5 flex items-center justify-between">
          <label className="field-label mb-0">Birth Place</label>
          <button
            type="button"
            onClick={() => setManualOverride((v) => !v)}
            disabled={disabled}
            className="text-xs text-amber-400 hover:text-amber-300 transition"
          >
            {manualOverride ? "Search by place name instead" : "Enter coordinates manually"}
          </button>
        </div>

        {manualOverride ? (
          <div className="grid grid-cols-2 gap-4">
            <input
              type="number"
              step="any"
              value={manualLatitude}
              onChange={(e) => setManualLatitude(e.target.value)}
              className="field-input"
              placeholder="Latitude, e.g. 28.6139"
              disabled={disabled}
            />
            <input
              type="number"
              step="any"
              value={manualLongitude}
              onChange={(e) => setManualLongitude(e.target.value)}
              className="field-input"
              placeholder="Longitude, e.g. 77.2090"
              disabled={disabled}
            />
          </div>
        ) : (
          <BirthPlaceSearch
            value={placeSearchText}
            onChange={(text) => {
              setPlaceSearchText(text);
              setResolvedPlace(null);
            }}
            onSelect={(place) => {
              setResolvedPlace(place);
              setPlaceSearchText(place.display_name);
            }}
            disabled={disabled}
          />
        )}
      </div>

      {/* Resolved-location validation summary — required reading before submit is enabled */}
      {locationResolved && (
        <div className="rounded-lg border border-white/10 bg-white/5 p-3 text-xs">
          <p className="font-medium text-slate-300">
            {manualOverride
              ? "Manual coordinates"
              : resolvedPlace?.display_name ?? ""}
          </p>
          <p className="mt-1 text-slate-400">
            {effectiveLatitude?.toFixed(4)}°{effectiveLatitude! >= 0 ? "N" : "S"},{" "}
            {effectiveLongitude?.toFixed(4)}°{effectiveLongitude! >= 0 ? "E" : "W"}
            {!birthDate && " · pick a birth date to resolve the timezone"}
          </p>
          {birthDate && tzQuery.isLoading && (
            <p className="mt-1 text-slate-500">Resolving timezone…</p>
          )}
          {birthDate && tzQuery.isError && (
            <p className="mt-1 text-red-400">Could not resolve a timezone for this location.</p>
          )}
          {birthDate && tzQuery.data && (
            <p className="mt-1 text-emerald-400">
              {tzQuery.data.iana_name} · {formatOffset(tzQuery.data.utc_offset_minutes)}
              {tzQuery.data.is_dst ? " · DST in effect" : ""}
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label htmlFor="ayanamsa" className="field-label">
            Ayanamsa
          </label>
          <select
            id="ayanamsa"
            value={ayanamsa}
            onChange={(e) => setAyanamsa(e.target.value as AyanamsaCode)}
            className="field-input"
            disabled={disabled}
          >
            {AYANAMSA_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="houseSystem" className="field-label">
            House System
          </label>
          <select
            id="houseSystem"
            value={houseSystem}
            onChange={(e) => setHouseSystem(e.target.value as HouseSystemCode)}
            className="field-input"
            disabled={disabled}
          >
            {HOUSE_SYSTEM_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="dashaSystem" className="field-label">
            Dasha System
          </label>
          <select
            id="dashaSystem"
            value={dashaSystem}
            onChange={(e) => setDashaSystem(e.target.value as DashaSystemCode)}
            className="field-input"
            disabled={disabled}
          >
            {DASHA_SYSTEM_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-300">
        <input
          type="checkbox"
          checked={includeVargas}
          onChange={(e) => setIncludeVargas(e.target.checked)}
          disabled={disabled}
          className="h-4 w-4 rounded border-white/20 bg-cosmos-900 text-amber-500 focus:ring-amber-400/40"
        />
        Compute all 15 divisional charts (Vargas)
      </label>

      {shownError && <p className="text-error animate-fade-in">{shownError}</p>}

      <button type="submit" disabled={!canSubmit} className="btn-primary w-full">
        {isPending ? (
          <>
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-cosmos-800 border-t-transparent" />
            Running analysis pipeline…
          </>
        ) : (
          "Run Analysis"
        )}
      </button>
    </form>
  );
}
