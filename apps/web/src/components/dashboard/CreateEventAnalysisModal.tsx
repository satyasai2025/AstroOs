"use client";

import { useRouter } from "next/navigation";
import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import { useCreateEventAnalysis } from "@/lib/eventAnalysis";
import { useTimezoneResolution } from "@/lib/geocoding";
import { useMyCharts } from "@/lib/charts";
import type {
  EventAnalysisScopeFlag,
  PlaceResultResponse,
} from "@/lib/types";
import { useMemo, useState } from "react";

/** Local date/time → UTC instant, using Date.UTC() semantics (treats the
 * date/time as literal wall-clock digits) minus the place's real offset, so
 * the result is the true UTC instant. */
function localToUtcIso(dateStr: string, timeStr: string, utcOffsetMinutes: number): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const [h, mi, s] = timeStr.split(":").map(Number);
  const asUtc = Date.UTC(y, m - 1, d, h ?? 0, mi ?? 0, s ?? 0);
  return new Date(asUtc - utcOffsetMinutes * 60_000).toISOString();
}

function formatOffset(minutes: number): string {
  const sign = minutes >= 0 ? "+" : "-";
  const abs = Math.abs(minutes);
  const hh = String(Math.floor(abs / 60)).padStart(2, "0");
  const mm = String(abs % 60).padStart(2, "0");
  return `UTC${sign}${hh}:${mm}`;
}

const SCOPE_OPTIONS: { key: EventAnalysisScopeFlag; label: string; hint: string }[] = [
  { key: "muhurta", label: "Muhurta", hint: "Event-moment fitness" },
  { key: "natal_promise", label: "Natal Promise", hint: "Relevant houses/lords for the event" },
  { key: "dasha_support", label: "Dasha Support", hint: "Active dasha chain support" },
  { key: "transit_influence", label: "Transit Influence", hint: "Transits at the event moment" },
  { key: "planetary_strength", label: "Planetary Strength", hint: "Shadbala / planet strength" },
  { key: "yogas_activated", label: "Yogas Activated", hint: "Natal + event-chart yogas" },
  { key: "overall_score", label: "Overall Score", hint: "Composite success score" },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

export function CreateEventAnalysisModal({ open, onClose }: Props) {
  const router = useRouter();
  const createAnalysis = useCreateEventAnalysis();
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const charts = chartsData?.charts ?? [];

  const [step, setStep] = useState(1);

  // Step 1 — subject natal chart
  const [selectedChartId, setSelectedChartId] = useState<string | null>(null);

  // Step 2 — event details
  const [eventName, setEventName] = useState("");
  const [category, setCategory] = useState("");
  const [eventDate, setEventDate] = useState("");
  const [eventTime, setEventTime] = useState("");
  const [useBirthLocation, setUseBirthLocation] = useState(true);
  const [placeSearchText, setPlaceSearchText] = useState("");
  const [eventPlace, setEventPlace] = useState<PlaceResultResponse | null>(null);

  // Step 3 — scope
  const [scope, setScope] = useState<EventAnalysisScopeFlag[]>(
    SCOPE_OPTIONS.map((o) => o.key),
  );

  const selectedChart = charts.find((c) => c.id === selectedChartId) ?? null;

  // Effective event location: custom place if chosen, else the birth coords.
  const effectiveLat = eventPlace ? eventPlace.latitude : (useBirthLocation ? selectedChart?.birth_latitude ?? null : null);
  const effectiveLon = eventPlace ? eventPlace.longitude : (useBirthLocation ? selectedChart?.birth_longitude ?? null : null);

  const tzQuery = useTimezoneResolution(
    useBirthLocation || !!eventPlace ? effectiveLat : null,
    useBirthLocation || !!eventPlace ? effectiveLon : null,
    eventDate || null,
  );

  const canContinueToEvent = !!selectedChartId;
  const canContinueToScope = !!eventName && canContinueToEvent;
  const canAnalyze =
    canContinueToScope &&
    !!eventDate &&
    !!eventTime &&
    // Only require tzQuery.data when we have coordinates to resolve
    (!effectiveLat || !effectiveLon || !!tzQuery.data) &&
    !createAnalysis.isPending;

  function reset() {
    setStep(1);
    setSelectedChartId(null);
    setEventName("");
    setCategory("");
    setEventDate("");
    setEventTime("");
    setUseBirthLocation(true);
    setPlaceSearchText("");
    setEventPlace(null);
    setScope(SCOPE_OPTIONS.map((o) => o.key));
  }

  function toggleScope(key: EventAnalysisScopeFlag) {
    setScope((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
    );
  }

  function handleAnalyze() {
    if (!selectedChart || !tzQuery.data || !eventDate || !eventTime) return;
    const eventDatetimeUtc = localToUtcIso(eventDate, eventTime, tzQuery.data.utc_offset_minutes);
    createAnalysis.mutate(
      {
        birth_chart_id: selectedChart.id,
        event_name: eventName
          .trim()
          .split(/\s+/)
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
          .join(" ") || "Untitled Event",
        category: category.trim() || null,
        event_datetime_utc: eventDatetimeUtc,
        latitude: eventPlace ? eventPlace.latitude : null,
        longitude: eventPlace ? eventPlace.longitude : null,
        place_name: eventPlace?.display_name
          ?.split(/\s+/)
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
          .join(" ") ?? null,
        timezone_iana: tzQuery.data.iana_name,
        scope,
      },
      {
        onSuccess: (result) => {
          onClose();
          reset();
          router.push(`/charts/event/${result.id}`);
        },
      },
    );
  }

  if (!open) return null;

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
                <rect x="3" y="5" width="18" height="16" rx="2" />
                <path d="M3 10h18M8 3v4M16 3v4" />
              </svg>
            </div>
            <div>
              <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>Event Analysis</h2>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                Analyze a chosen event moment against a saved natal chart.
              </p>
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

        {/* Step rail */}
        <div className="flex gap-4 border-b px-5 py-3" style={{ borderColor: "var(--border-primary)" }}>
          {["Select Chart", "Add Event", "Scope & Analyze"].map((label, i) => {
            const n = i + 1;
            return (
              <div key={n} className="flex items-center gap-1.5">
                <span
                  className="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold"
                  style={{
                    backgroundColor: step >= n ? "var(--obsidian-accent-tertiary)" : "var(--obsidian-surface)",
                    color: step >= n ? "#fff" : "var(--text-muted)",
                    border: step >= n ? "none" : "1px solid var(--border-primary)",
                  }}
                >
                  {n}
                </span>
                <span className="text-xs font-medium" style={{ color: step === n ? "var(--text-primary)" : "var(--text-muted)" }}>
                  {label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {step === 1 && (
            <div>
              <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Select Saved Birth Chart</h3>
              <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                Pick the person whose natal chart anchors this event analysis.
              </p>
              {chartsLoading && <p className="text-xs" style={{ color: "var(--text-muted)" }}>Loading saved charts…</p>}
              {!chartsLoading && charts.length === 0 && (
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  No saved charts yet. Create a birth chart first, then return here.
                </p>
              )}
              <div className="space-y-2">
                {charts.map((c) => {
                  const selected = selectedChartId === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setSelectedChartId(c.id)}
                      className="flex w-full items-center justify-between gap-3 rounded-lg border p-3 text-left transition-colors"
                      style={{
                        borderColor: selected ? "var(--obsidian-accent-tertiary)" : "var(--border-primary)",
                        backgroundColor: selected ? "var(--obsidian-accent-tertiary-soft)" : "transparent",
                      }}
                    >
                      <div>
                        <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                          {c.subject_name}{c.is_default ? " (default)" : ""}
                        </p>
                        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                          {new Date(c.birth_datetime_utc).toLocaleDateString()}
                          {c.place_name ? ` · ${c.place_name}` : ""}
                        </p>
                      </div>
                      <span className="text-xs" style={{ color: "var(--obsidian-accent-tertiary)" }}>
                        {selected ? "Selected ✓" : "Select"}
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
                <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Add Event</h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Describe the event and when/where it happens. Times are local to the event's location.
                </p>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Event Name</label>
                <input
                  type="text"
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                  className="obsidian-input"
                  placeholder="e.g. Business Launch, Marriage, House Purchase"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Category (optional)</label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="obsidian-input"
                  placeholder="e.g. Career, Marriage, Travel"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Event Date</label>
                  <input
                    type="date"
                    required
                    value={eventDate}
                    onChange={(e) => setEventDate(e.target.value)}
                    className="obsidian-input w-full [color-scheme:dark]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Event Time</label>
                  <input
                    type="time"
                    step="1"
                    required
                    value={eventTime}
                    onChange={(e) => setEventTime(e.target.value)}
                    className="obsidian-input w-full [color-scheme:dark]"
                  />
                </div>
              </div>
              <p className="-mt-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
                Local date and time at the event's location — not UTC. The location below determines the conversion.
              </p>

              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <label className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Event Location</label>
                  <button
                    type="button"
                    onClick={() => {
                      setUseBirthLocation((v) => !v);
                      if (!useBirthLocation) setEventPlace(null);
                    }}
                    className="text-[11px] transition"
                    style={{ color: "var(--obsidian-accent-secondary)" }}
                  >
                    {useBirthLocation ? "Use a different location" : "Use the birth location"}
                  </button>
                </div>

                {useBirthLocation && selectedChart ? (
                  <div className="rounded-lg border p-3 text-xs" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                    <p className="font-medium" style={{ color: "var(--text-secondary)" }}>
                      {selectedChart.place_name ?? "Birth location"}
                    </p>
                    <p className="mt-1" style={{ color: "var(--text-muted)" }}>
                      {selectedChart.birth_latitude.toFixed(4)}°{selectedChart.birth_latitude >= 0 ? "N" : "S"},{" "}
                      {selectedChart.birth_longitude.toFixed(4)}°{selectedChart.birth_longitude >= 0 ? "E" : "W"}
                    </p>
                  </div>
                ) : (
                  <BirthPlaceSearch
                    value={placeSearchText}
                    onChange={(text) => {
                      setPlaceSearchText(text);
                      setEventPlace(null);
                    }}
                    onSelect={(place) => {
                      setEventPlace(place);
                      setPlaceSearchText(place.display_name);
                    }}
                  />
                )}

                {eventDate && !useBirthLocation && eventPlace && renderTzHint()}
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Select Analysis Scope</h3>
              <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                Choose which dimensions to score. All are selected by default.
              </p>
              <div className="space-y-2">
                {SCOPE_OPTIONS.map((o) => {
                  const checked = scope.includes(o.key);
                  return (
                    <label
                      key={o.key}
                      className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border p-3"
                      style={{
                        borderColor: checked ? "var(--obsidian-accent-tertiary)" : "var(--border-primary)",
                        backgroundColor: checked ? "var(--obsidian-accent-tertiary-soft)" : "transparent",
                      }}
                    >
                      <div>
                        <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{o.label}</p>
                        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{o.hint}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleScope(o.key)}
                        className="h-4 w-4 rounded"
                      />
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {createAnalysis.isError && (
            <p className="mt-4 text-xs" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>
              {(createAnalysis.error as Error)?.message ?? "Event analysis failed."}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t p-4" style={{ borderColor: "var(--border-primary)" }}>
          <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
            Event chart is a computed artifact — no new saved birth chart.
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={step === 1 ? onClose : () => setStep((s) => s - 1)}
              className="obsidian-btn-secondary text-sm"
              disabled={createAnalysis.isPending}
            >
              {step === 1 ? "Cancel" : "Back"}
            </button>
            {step < 3 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                disabled={step === 1 ? !canContinueToEvent : !canContinueToScope}
                className="obsidian-btn-primary text-sm"
              >
                Continue →
              </button>
            ) : (
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={!canAnalyze}
                className="obsidian-btn-primary text-sm"
              >
                {createAnalysis.isPending ? (
                  <>
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-t-transparent" />
                    Analyzing…
                  </>
                ) : (
                  "Analyze Event"
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // Helper for the tz resolution hint on step 2 (custom location).
  function renderTzHint() {
    if (tzQuery.isLoading) {
      return <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Resolving timezone…</p>;
    }
    if (tzQuery.isError) {
      return <p className="mt-1 text-xs" style={{ color: "var(--obsidian-status-danger, #ef4444)" }}>Could not resolve a timezone for this location.</p>;
    }
    if (tzQuery.data) {
      return (
        <p className="mt-1 text-xs" style={{ color: "var(--obsidian-accent-success, #10B981)" }}>
          {tzQuery.data.iana_name} · {formatOffset(tzQuery.data.utc_offset_minutes)}
          {tzQuery.data.is_dst ? " · DST in effect" : ""}
        </p>
      );
    }
    return null;
  }
}