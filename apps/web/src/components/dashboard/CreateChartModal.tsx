"use client";

import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import { CreateCompatibilityModal } from "./CreateCompatibilityModal";
import { CreateTransitModal } from "./CreateTransitModal";

import {
  AYANAMSA_OPTIONS,
  DASHA_SYSTEM_OPTIONS,
  HOUSE_SYSTEM_OPTIONS,
  resolveAstrologicalAlignment
} from "@/lib/chart-alignment";
import { useTimezoneResolution } from "@/lib/geocoding";
import type {
  AyanamsaCode,
  DashaSystemCode,
  HouseSystemCode,
  PlaceResultResponse,
  WorkflowAnalysisRequest,
} from "@/lib/types";
import { useEffect, useMemo, useState } from "react";

type ChartTypeId =
  | "birth_chart"
  | "compatibility"
  | "transit_chart"
  | "horary_chart"
  | "event_chart"
  | "import_chart";

const CHART_TYPES: {
  id: ChartTypeId;
  label: string;
  sublabel: string;
  icon: React.ReactNode;
  enabled: boolean;
}[] = [
  {
    id: "birth_chart",
    label: "Birth Chart",
    sublabel: "Natal Analysis",
    enabled: true,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
      </svg>
    ),
  },
  {
    id: "compatibility",
    label: "Compatibility",
    sublabel: "Match Analysis",
    enabled: true,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z" />
      </svg>
    ),
  },
  {
    id: "transit_chart",
    label: "Transit Chart",
    sublabel: "Transit Analysis",
    enabled: true,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <ellipse cx="12" cy="12" rx="9" ry="4" />
      </svg>
    ),
  },
  {
    id: "horary_chart",
    label: "Horary Chart",
    sublabel: "Prashna Analysis",
    enabled: true,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.5-2.5 1.8-2.5 3.5" />
        <path d="M12 17h.01" />
      </svg>
    ),
  },
  {
    id: "event_chart",
    label: "Event Chart",
    sublabel: "Event Analysis",
    enabled: true,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M3 10h18M8 3v4M16 3v4" />
      </svg>
    ),
  },
  {
    id: "import_chart",
    label: "Import Chart",
    sublabel: "From File",
    enabled: true,
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 16V4M12 4l-4 4M12 4l4 4" />
        <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
      </svg>
    ),
  },
];

const STEPS = [
  { n: 1, label: "Chart Type" },
  { n: 2, label: "Birth Details" },
  { n: 3, label: "Review & Confirm" },
];

/** Same UTC conversion as BirthDetailsForm — Date.UTC() treats y/m/d/h/m/s
 * as literal wall-clock numbers with no timezone applied, so subtracting
 * the birth place's actual UTC offset gives the true UTC instant. */
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

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (request: WorkflowAnalysisRequest) => void;
  isPending: boolean;
  errorMessage: string | null;
}

export function CreateChartModal({ open, onClose, onSubmit, isPending, errorMessage }: Props) {
  const [step, setStep] = useState(1);
  const [chartType, setChartType] = useState<ChartTypeId>("birth_chart");

  const [subjectName, setSubjectName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");

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

  // ── Alignment Matrix Resolution ──────────────────────────────────────────────
  // Evaluate cascading astrological configuration rules on every state change.
  const alignment = useMemo(
    () => resolveAstrologicalAlignment({ ayanamsa, houseSystem, dashaSystem }, "init"),
    [ayanamsa, houseSystem, dashaSystem],
  );

  // Sync the corrected values back after auto-switches
  useEffect(() => {
    if (alignment.values.ayanamsa !== ayanamsa) setAyanamsa(alignment.values.ayanamsa);
    if (alignment.values.houseSystem !== houseSystem) setHouseSystem(alignment.values.houseSystem);
    if (alignment.values.dashaSystem !== dashaSystem) setDashaSystem(alignment.values.dashaSystem);
  }, [alignment.values]);

  // Reset to a clean first step every time the modal is (re)opened, so a
  // previous session's data doesn't linger the next time it's opened.
  useEffect(() => {
    if (open) {
      setStep(1);
      setChartType("birth_chart");
      setSubjectName("");
      setBirthDate("");
      setBirthTime("");
      setPlaceSearchText("");
      setResolvedPlace(null);
      setManualOverride(false);
      setManualLatitude("");
      setManualLongitude("");
      setValidationError(null);
    }
  }, [open]);

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

  const canContinueFromDetails = !!birthDate && !!birthTime && locationResolved;
  const canSubmit = !isPending && canContinueFromDetails && timezoneResolved;

  if (!open) return null;

  // ── Redirect to CRM Compatibility Studio ─────────────────────────────────
  // When user selects "Compatibility" and clicks Continue, show the full CRM suite!
  if (chartType === "compatibility" && step > 1) {
    return <CreateCompatibilityModal open={open} onClose={onClose} />;
  }

  // ── Redirect to dedicated Transit Chart creation modal ────────────────────
  // When user selects "Transit Chart", render the dedicated transit modal
  if (chartType === "transit_chart") {
    return <CreateTransitModal open={open} onClose={onClose} />;
  }

  function handleContinue() {
    setValidationError(null);
    if (step === 2) {
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
    }
    setStep((s) => Math.min(3, s + 1));
  }

  function handleCreate() {
    setValidationError(null);
    if (!tzQuery.data || effectiveLatitude === null || effectiveLongitude === null) {
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
      place_name: manualOverride ? null : resolvedPlace?.display_name ?? null,
    });
  }

  const shownError = validationError ?? errorMessage;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />

      <div
        className="obsidian-card relative flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden"
        style={{ backgroundColor: "var(--obsidian-surface-elevated)" }}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b p-5" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg"
              style={{ backgroundColor: "var(--obsidian-accent-tertiary-soft)", color: "var(--obsidian-accent-tertiary)" }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </div>
            <div>
              <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>Create New Chart</h2>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Create a new chart to begin your astrological analysis.</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1 transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Step rail */}
          <div className="w-40 flex-shrink-0 border-r p-5" style={{ borderColor: "var(--border-primary)" }}>
            <div className="flex flex-col gap-4">
              {STEPS.map((s) => (
                <div key={s.n} className="flex items-center gap-2">
                  <span
                    className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-semibold"
                    style={{
                      backgroundColor: step >= s.n ? "var(--obsidian-accent-tertiary)" : "var(--obsidian-surface)",
                      color: step >= s.n ? "#fff" : "var(--text-muted)",
                      border: step >= s.n ? "none" : "1px solid var(--border-primary)",
                    }}
                  >
                    {s.n}
                  </span>
                  <span
                    className="text-xs font-medium"
                    style={{ color: step === s.n ? "var(--text-primary)" : "var(--text-muted)" }}
                  >
                    {s.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Step content */}
          <div className="flex-1 overflow-y-auto p-5">
            {step === 1 && (
              <div>
                <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Select Chart Type</h3>
                <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>Choose the type of chart you want to create</p>
                <div className="grid grid-cols-3 gap-3">
                  {CHART_TYPES.map((ct) => {
                    const selected = chartType === ct.id;
                    return (
                      <button
                        key={ct.id}
                        type="button"
                        disabled={!ct.enabled}
                        onClick={() => ct.enabled && setChartType(ct.id)}
                        className="flex flex-col items-center gap-2 rounded-lg border p-4 text-center transition-colors"
                        style={{
                          borderColor: selected ? "var(--obsidian-accent-tertiary)" : "var(--border-primary)",
                          backgroundColor: selected ? "var(--obsidian-accent-tertiary-soft)" : "transparent",
                          opacity: ct.enabled ? 1 : 0.4,
                          cursor: ct.enabled ? "pointer" : "not-allowed",
                        }}
                        title={ct.enabled ? undefined : "Not built yet"}
                      >
                        <span style={{ color: selected ? "var(--obsidian-accent-tertiary)" : "var(--text-secondary)" }}>
                          {ct.icon}
                        </span>
                        <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                          {ct.label}
                        </span>
                        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                          {ct.enabled ? ct.sublabel : "Soon"}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div>
                  <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Birth Details</h3>
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Enter the birth details for accurate chart calculation</p>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Subject Name</label>
                  <input
                    type="text"
                    value={subjectName}
                    onChange={(e) => setSubjectName(e.target.value)}
                    className="obsidian-input"
                    placeholder="Unnamed"
                    disabled={isPending}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Birth Date</label>
                    <input
                      type="date"
                      required
                      value={birthDate}
                      onChange={(e) => setBirthDate(e.target.value)}
                      className="obsidian-input w-full [color-scheme:dark]"
                      disabled={isPending}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Birth Time</label>
                    <input
                      type="time"
                      step="1"
                      required
                      value={birthTime}
                      onChange={(e) => setBirthTime(e.target.value)}
                      className="obsidian-input w-full [color-scheme:dark]"
                      disabled={isPending}
                    />
                  </div>
                </div>
                <p className="-mt-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
                  Local date and time at the birth place — not UTC. The birth place below determines the conversion.
                </p>

                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <label className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Birth Place</label>
                    <button
                      type="button"
                      onClick={() => setManualOverride((v) => !v)}
                      disabled={isPending}
                      className="text-[11px] transition"
                      style={{ color: "var(--obsidian-accent-secondary)" }}
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
                        className="obsidian-input"
                        placeholder="Latitude, e.g. 28.6139"
                        disabled={isPending}
                      />
                      <input
                        type="number"
                        step="any"
                        value={manualLongitude}
                        onChange={(e) => setManualLongitude(e.target.value)}
                        className="obsidian-input"
                        placeholder="Longitude, e.g. 77.2090"
                        disabled={isPending}
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
                      disabled={isPending}
                    />
                  )}
                </div>

                {locationResolved && (
                  <div className="rounded-lg border p-3 text-xs" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                    <p className="font-medium" style={{ color: "var(--text-secondary)" }}>
                      {manualOverride ? "Manual coordinates" : resolvedPlace?.display_name ?? ""}
                    </p>
                    <p className="mt-1" style={{ color: "var(--text-muted)" }}>
                      {effectiveLatitude?.toFixed(4)}°{effectiveLatitude! >= 0 ? "N" : "S"},{" "}
                      {effectiveLongitude?.toFixed(4)}°{effectiveLongitude! >= 0 ? "E" : "W"}
                      {!birthDate && " · pick a birth date to resolve the timezone"}
                    </p>
                    {birthDate && tzQuery.isLoading && <p className="mt-1" style={{ color: "var(--text-muted)" }}>Resolving timezone…</p>}
                    {birthDate && tzQuery.isError && <p className="mt-1" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>Could not resolve a timezone for this location.</p>}
                    {birthDate && tzQuery.data && (
                      <p className="mt-1" style={{ color: "var(--obsidian-accent-success, #10B981)" }}>
                        {tzQuery.data.iana_name} · {formatOffset(tzQuery.data.utc_offset_minutes)}
                        {tzQuery.data.is_dst ? " · DST in effect" : ""}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <div>
                  <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Review & Confirm</h3>
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Confirm the calculation settings, then create the chart</p>
                </div>

                <div className="rounded-lg border p-3 text-xs" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                  <p style={{ color: "var(--text-primary)" }}>{subjectName.trim() || "Unnamed"}</p>
                  <p className="mt-1" style={{ color: "var(--text-secondary)" }}>
                    {birthDate} · {birthTime}
                  </p>
                  <p className="mt-1" style={{ color: "var(--text-muted)" }}>
                    {manualOverride ? "Manual coordinates" : resolvedPlace?.display_name ?? ""}
                    {" — "}
                    {effectiveLatitude?.toFixed(4)}°{effectiveLatitude! >= 0 ? "N" : "S"},{" "}
                    {effectiveLongitude?.toFixed(4)}°{effectiveLongitude! >= 0 ? "E" : "W"}
                  </p>
                  {tzQuery.data && (
                    <p className="mt-1" style={{ color: "var(--obsidian-accent-success, #10B981)" }}>
                      {tzQuery.data.iana_name} · {formatOffset(tzQuery.data.utc_offset_minutes)}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Ayanamsa</label>
                    <select
                      value={ayanamsa}
                      onChange={(e) => setAyanamsa(e.target.value as AyanamsaCode)}
                      className="obsidian-input"
                      disabled={isPending}
                    >
                      {AYANAMSA_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value} disabled={!!alignment.disabled.ayanamsa[o.value]}>
                          {o.label}{alignment.disabled.ayanamsa[o.value] ? ` — ${alignment.disabled.ayanamsa[o.value]}` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>House System</label>
                    <select
                      value={houseSystem}
                      onChange={(e) => setHouseSystem(e.target.value as HouseSystemCode)}
                      className="obsidian-input"
                      disabled={isPending}
                    >
                      {HOUSE_SYSTEM_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value} disabled={!!alignment.disabled.houseSystem[o.value]}>
                          {o.label}{alignment.disabled.houseSystem[o.value] ? ` — ${alignment.disabled.houseSystem[o.value]}` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Dasha System</label>
                    <select
                      value={dashaSystem}
                      onChange={(e) => setDashaSystem(e.target.value as DashaSystemCode)}
                      className="obsidian-input"
                      disabled={isPending}
                    >
                      {DASHA_SYSTEM_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value} disabled={!!alignment.disabled.dashaSystem[o.value]}>
                          {o.label}{alignment.disabled.dashaSystem[o.value] ? ` — ${alignment.disabled.dashaSystem[o.value]}` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Contextual Alignment Alert Banners */}
                {alignment.banners.map((banner, idx) => (
                  <div
                    key={idx}
                    className="mt-2 flex items-start gap-2 rounded-md border px-3 py-2 text-[11px] leading-relaxed"
                    style={{
                      borderColor:
                        banner.severity === "lock" ? "var(--obsidian-accent-tertiary, #818cf8)" :
                        banner.severity === "advisory" ? "#f59e0b" :
                        "var(--border-primary)",
                      backgroundColor:
                        banner.severity === "lock" ? "rgba(129,140,248,0.08)" :
                        banner.severity === "advisory" ? "rgba(245,158,11,0.08)" :
                        "rgba(255,255,255,0.03)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <span className="mt-0.5 text-xs">
                      {banner.severity === "lock" ? "🔒" : banner.severity === "advisory" ? "⚠️" : "ℹ️"}
                    </span>
                    <span>{banner.message}</span>
                  </div>
                ))}

                <label className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                  <input
                    type="checkbox"
                    checked={includeVargas}
                    onChange={(e) => setIncludeVargas(e.target.checked)}
                    disabled={isPending}
                    className="h-4 w-4 rounded"
                  />
                  Compute all 15 divisional charts (Vargas)
                </label>
              </div>
            )}

            {shownError && (
              <p className="mt-4 text-xs" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>{shownError}</p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t p-4" style={{ borderColor: "var(--border-primary)" }}>
          <p className="flex items-center gap-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="5" y="11" width="14" height="9" rx="2" />
              <path d="M8 11V7a4 4 0 0 1 8 0v4" />
            </svg>
            Your data is secure and private
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={step === 1 ? onClose : () => setStep((s) => s - 1)}
              className="obsidian-btn-secondary text-sm"
              disabled={isPending}
            >
              {step === 1 ? "Cancel" : "Back"}
            </button>
            {step < 3 ? (
              <button
                type="button"
                onClick={handleContinue}
                disabled={step === 2 && !canContinueFromDetails}
                className="obsidian-btn-primary text-sm"
              >
                Continue →
              </button>
            ) : (
              <button
                type="button"
                onClick={handleCreate}
                disabled={!canSubmit}
                className="obsidian-btn-primary text-sm"
              >
                {isPending ? (
                  <>
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-t-transparent" />
                    Creating…
                  </>
                ) : (
                  "Create Chart"
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
