"use client";

import { Badge, Button, Card, KpiCard } from "@/components/ui";
import { useMyCharts } from "@/lib/charts";
import { useWorkflowStore } from "@/lib/store";
import { useLiveTransit } from "@/lib/transitPatterns";
import type {
  AyanamsaCode,
  BirthChartSummary,
  HouseSystemCode,
  TransitRequest,
  TransitResponse,
} from "@/lib/types";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
}

function toIsoDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function todayIsoDate(): string {
  return toIsoDate(new Date());
}

function tomorrowIsoDate(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return toIsoDate(d);
}

export function CreateTransitModal({ open, onClose }: Props) {
  const router = useRouter();
  const request = useWorkflowStore((s) => s.request);
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);
  const setTransitChart = useWorkflowStore((s) => s.setTransitChart);

  const [step, setStep] = useState(1);
  const [transitDate, setTransitDate] = useState(todayIsoDate);
  const [transitTime, setTransitTime] = useState("10:30");
  const [datePreset, setDatePreset] = useState<"today" | "tomorrow" | "custom">("today");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [transitData, setTransitData] = useState<TransitResponse | null>(null);
  const [selectedChart, setSelectedChart] = useState<BirthChartSummary | null>(null);

  const myCharts = useMyCharts();
  const charts: BirthChartSummary[] = myCharts.data?.charts ?? [];
  const isLoadingCharts = myCharts.isLoading;
  const fetchError = myCharts.isError ? "Failed to load your charts. Please try again." : null;

  const transitDatetimeUtc = useMemo(() => {
    if (!transitDate || !transitTime) return undefined;
    return new Date(`${transitDate}T${transitTime}`).toISOString();
  }, [transitDate, transitTime]);

  // Prefer the user-selected chart; fall back to the workflow store's active chart.
  const transitRequest: TransitRequest | null = useMemo(() => {
    if (!transitDatetimeUtc) return null;

    if (selectedChart) {
      return {
        birth_datetime_utc: selectedChart.birth_datetime_utc,
        latitude: selectedChart.birth_latitude,
        longitude: selectedChart.birth_longitude,
        ayanamsa: selectedChart.ayanamsa as AyanamsaCode,
        house_system: selectedChart.house_system as HouseSystemCode,
        transit_datetime_utc: transitDatetimeUtc,
      };
    }

    if (!request) return null;
    return {
      birth_datetime_utc: request.birth_datetime_utc,
      latitude: request.latitude,
      longitude: request.longitude,
      ayanamsa: request.ayanamsa,
      house_system: request.house_system,
      transit_datetime_utc: transitDatetimeUtc,
    };
  }, [transitDatetimeUtc, selectedChart, request]);

  const liveTransit = useLiveTransit(transitRequest);
  const transits = liveTransit.data;

  useEffect(() => {
    if (transitRequest && transits) {
      setIsAnalyzing(false);
      setTransitData(transits);
      // Auto-advance to Review & Confirm once the analysis completes.
      setStep(3);
    }
  }, [transits, transitRequest]);

  function handleAnalyze() {
    if (!transitRequest || !transitDate) return;
    setIsAnalyzing(true);
    setTransitData(null);
    liveTransit.refetch();
    setStep(2);
  }

  function handleViewReport() {
    const encoded = encodeURIComponent(`${transitDate}T${transitTime}`);
    router.push(`/transit/${encoded}`);
    // Defer the close so the navigation isn't swallowed by the modal unmount.
    setTimeout(() => onClose(), 0);
  }

  function handleSelectChart(chart: BirthChartSummary) {
    setSelectedChart(chart);
    setTransitChart(chart);
    setTransitData(null);
    setStep(2);
  }

  function handleSelectActiveChart() {
    setSelectedChart(null);
    setTransitChart(null);
    setTransitData(null);
    setStep(2);
  }

  function handleCreateNewChart() {
    onClose();
    // Defer the reopen so the close actually renders first. Without this,
    // React 18 batches the two Zustand updates and CreateChartModal's
    // reset effect (keyed on `open`) never fires — its chartType would
    // stay "transit_chart" and the user would be trapped in this modal.
    setTimeout(() => openCreateModal(), 0);
  }

  function applyPreset(preset: "today" | "tomorrow") {
    setDatePreset(preset);
    setTransitDate(preset === "today" ? todayIsoDate() : tomorrowIsoDate());
    setTransitData(null);
  }

  if (!open) return null;

  // No store chart AND no saved charts to pick from → ask the user to create one.
  if (!request && !isLoadingCharts && charts.length === 0) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black/70" onClick={onClose} />
        <Card style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem", padding: "2rem", textAlign: "center", maxWidth: "400px" }}>
          <div className="flex w-full items-start justify-between">
            <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
              No Birth Chart Available
            </h2>
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
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Please create a birth chart first before analyzing transits.
          </p>
          <div className="flex gap-2">
            <Button onClick={handleCreateNewChart}>Create Birth Chart</Button>
            <Button variant="secondary" onClick={onClose}>Close</Button>
          </div>
        </Card>
      </div>
    );
  }

  const activeSubjectName = selectedChart?.subject_name ?? request?.subject_name ?? "Unknown";
  const activeBirthDatetimeUtc = selectedChart?.birth_datetime_utc ?? request?.birth_datetime_utc ?? "";
  const activePlaceName = selectedChart?.place_name ?? request?.place_name ?? null;
  const activeLatitude = selectedChart?.birth_latitude ?? request?.latitude ?? 0;
  const activeLongitude = selectedChart?.birth_longitude ?? request?.longitude ?? 0;
  const activeAyanamsa = (selectedChart?.ayanamsa as AyanamsaCode) ?? request?.ayanamsa ?? "lahiri";
  const activeHouseSystem = (selectedChart?.house_system as HouseSystemCode) ?? request?.house_system ?? "W";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <Card style={{ display: "flex", flexDirection: "column", maxHeight: "90vh", width: "100%", maxWidth: "768px", overflow: "hidden", padding: 0 }}>
        {/* Header */}
        <div className="flex items-start justify-between border-b p-5" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-tertiary-soft)", color: "var(--obsidian-accent-tertiary)" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <ellipse cx="12" cy="12" rx="9" ry="4" />
              </svg>
            </div>
            <div>
              <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>Create Transit Analysis</h2>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Analyze planetary transits for an existing birth chart.</p>
            </div>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded p-1 transition-colors" style={{ color: "var(--text-muted)" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Step rail */}
        <div className="flex items-center justify-center gap-6 border-b p-4" style={{ borderColor: "var(--border-primary)" }}>
          {[
            { n: 1, label: "Select Chart" },
            { n: 2, label: "Transit Date" },
            { n: 3, label: "Review & Confirm" },
          ].map((s) => (
            <div key={s.n} className="flex items-center gap-2">
              <span
                className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold"
                style={{
                  backgroundColor: step >= s.n ? "var(--accent)" : "var(--bg-surface-800)",
                  color: step >= s.n ? "var(--accent-text)" : "var(--text-muted)",
                  border: `1px solid ${step >= s.n ? "var(--accent)" : "var(--border-default)"}`,
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
              {s.n < 3 && <span style={{ color: "var(--text-muted)", margin: "0 8px" }}>/</span>}
            </div>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {step === 1 && (
            <div className="mx-auto max-w-2xl">
              <div className="mb-6">
                <h2 className="mb-2 text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                  Select Birth Chart
                </h2>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Choose a birth chart to analyze transits for.
                </p>
              </div>

              {/* Current active chart from the store (not yet saved) */}
              {request && (
                <div className="mb-4">
                  <p className="mb-2 text-xs font-medium" style={{ color: "var(--text-muted)" }}>ACTIVE CHART</p>
                  <button
                    type="button"
                    onClick={handleSelectActiveChart}
                    className="w-full rounded-lg border p-4 text-left transition-colors"
                    style={{
                      borderColor: !selectedChart ? "var(--obsidian-accent-tertiary)" : "var(--border-primary)",
                      backgroundColor: !selectedChart ? "var(--obsidian-accent-tertiary-soft)" : "var(--obsidian-surface)",
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                          {request.subject_name || "Active Birth Chart"}
                        </h3>
                        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                          {new Date(request.birth_datetime_utc).toLocaleDateString("en-US", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                        <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                          {request.place_name || `${request.latitude.toFixed(4)}°, ${request.longitude.toFixed(4)}°`}
                        </p>
                      </div>
                      {!selectedChart ? (
                        <Badge tone="cyan">Selected</Badge>
                      ) : (
                        <Badge tone="cyan">Select</Badge>
                      )}
                    </div>
                  </button>
                </div>
              )}

              <p className="mb-2 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                {request ? "SAVED CHARTS" : "YOUR CHARTS"}
              </p>

              {isLoadingCharts ? (
                <div className="mb-6 flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-2 border-t-transparent" style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }} />
                    <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Loading charts...</p>
                  </div>
                </div>
              ) : fetchError ? (
                <div className="mb-6 rounded-lg border p-6 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                  <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    Could Not Load Charts
                  </h3>
                  <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>{fetchError}</p>
                  <Button variant="secondary" size="sm" onClick={() => myCharts.refetch()}>Retry</Button>
                </div>
              ) : charts.length > 0 ? (
                <div className="mb-6 space-y-2">
                  {charts.map((chart) => {
                    const selected = selectedChart?.id === chart.id;
                    return (
                      <button
                        key={chart.id}
                        type="button"
                        onClick={() => handleSelectChart(chart)}
                        className="w-full rounded-lg border p-4 text-left transition-colors"
                        style={{
                          borderColor: selected ? "var(--obsidian-accent-tertiary)" : "var(--border-primary)",
                          backgroundColor: selected ? "var(--obsidian-accent-tertiary-soft)" : "var(--obsidian-surface)",
                        }}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="mb-1 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                              {chart.subject_name}
                            </h3>
                            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                              {new Date(chart.birth_datetime_utc).toLocaleDateString("en-US", {
                                year: "numeric",
                                month: "long",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                            <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                              {chart.place_name || `${chart.birth_latitude.toFixed(4)}°, ${chart.birth_longitude.toFixed(4)}°`}
                            </p>
                          </div>
                          {selected ? (
                            <Badge tone="cyan">Selected</Badge>
                          ) : (
                            <Badge tone="cyan">Select</Badge>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="mb-6 rounded-lg border p-6 text-center" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                  <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    No Saved Charts Found
                  </h3>
                  <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                    You can continue with the active chart above or create a new one.
                  </p>
                  <Button onClick={handleCreateNewChart}>Create New Chart</Button>
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="mx-auto max-w-4xl">
              <div className="mb-6">
                <h2 className="mb-2 text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                  Transit Date
                </h2>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Select the date and time for transit analysis.
                </p>
              </div>

              <div className="mb-4 flex gap-2">
                <Button
                  variant={datePreset === "today" ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => applyPreset("today")}
                >
                  <span className="mr-2">○</span>
                  Today
                </Button>
                <Button
                  variant={datePreset === "tomorrow" ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => applyPreset("tomorrow")}
                >
                  <span className="mr-2">○</span>
                  Tomorrow
                </Button>
                <Button
                  variant={datePreset === "custom" ? "primary" : "secondary"}
                  size="sm"
                  onClick={() => setDatePreset("custom")}
                >
                  <span className="mr-2">○</span>
                  Custom Date
                </Button>
              </div>

              <div className="mb-6 grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                    Date
                  </label>
                  <input
                    type="date"
                    value={transitDate}
                    onChange={(e) => {
                      setTransitDate(e.target.value);
                      setDatePreset("custom");
                      setTransitData(null);
                    }}
                    className="obsidian-input w-full [color-scheme:dark]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                    Time
                  </label>
                  <input
                    type="time"
                    value={transitTime}
                    onChange={(e) => {
                      setTransitTime(e.target.value);
                      setTransitData(null);
                    }}
                    className="obsidian-input w-full [color-scheme:dark]"
                  />
                </div>
              </div>

              {transitDate && (
                <div className="mb-6 rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Selected: {new Date(`${transitDate}T${transitTime}`).toLocaleString("en-US", {
                      weekday: "long",
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              )}

              <div className="mb-6">
                <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  Chart
                </h3>
                <div className="rounded-lg border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {activeSubjectName}
                  </p>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                    {activePlaceName || `${activeLatitude.toFixed(4)}°, ${activeLongitude.toFixed(4)}°`}
                  </p>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                    {selectedChart ? `Saved chart · ${selectedChart.ayanamsa} / ${selectedChart.house_system}` : "Using birth chart location"}
                  </p>
                </div>
              </div>

              <Button
                fullWidth
                size="lg"
                onClick={handleAnalyze}
                disabled={!transitDate || isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <span className="inline-block mr-2 h-4 w-4 animate-spin rounded-full border-2 border-t-transparent" />
                    Analyzing...
                  </>
                ) : (
                  "Analyze Transit"
                )}
              </Button>

              {isAnalyzing && (
                <div className="mt-6 flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-2 border-t-transparent" style={{ borderColor: "var(--accent)", borderTopColor: "transparent" }} />
                    <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                      Analyzing transits for {transitDate}...
                    </p>
                  </div>
                </div>
              )}

              {transitData && !isAnalyzing && (
                <Card style={{ marginTop: "1.5rem" }}>
                  <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    Transit Overview
                  </h3>
                  <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    <KpiCard label="Active Transits" value={String(transitData.planets?.length || 0)} accent="cyan" />
                    <KpiCard label="Benefic" value={String(transitData.planets?.filter((p) => p.is_favorable_house === true).length || 0)} accent="success" />
                    <KpiCard label="Challenging" value={String(transitData.planets?.filter((p) => p.is_favorable_house === false).length || 0)} accent="gold" />
                    <KpiCard label="Retrograde" value={String(transitData.planets?.filter((p) => p.is_retrograde).length || 0)} accent="violet" />
                  </div>
                </Card>
              )}
            </div>
          )}

          {step === 3 && transitData && (
            <div className="mx-auto max-w-4xl">
              <div className="mb-6">
                <h2 className="mb-2 text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
                  Review & Confirm
                </h2>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Confirm the transit analysis settings before proceeding.
                </p>
              </div>

              <div className="mb-6 rounded-lg border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Birth Chart Details</h3>
                <div className="grid grid-cols-1 gap-2 text-xs md:grid-cols-2">
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Subject:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>{activeSubjectName}</span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Birth Date:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>
                      {activeBirthDatetimeUtc ? new Date(activeBirthDatetimeUtc).toLocaleDateString() : "—"}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Location:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>
                      {activePlaceName || `${activeLatitude.toFixed(2)}°, ${activeLongitude.toFixed(2)}°`}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Ayanamsa:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>{activeAyanamsa}</span>
                  </div>
                </div>
              </div>

              <div className="mb-6 rounded-lg border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--obsidian-surface)" }}>
                <h3 className="mb-2 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Transit Details</h3>
                <div className="grid grid-cols-1 gap-2 text-xs md:grid-cols-2">
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Transit Date:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>{transitDate}</span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Transit Time:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>{transitTime}</span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Active Planets:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>{transitData.planets?.length || 0}</span>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>House System:</span>
                    <span className="ml-2" style={{ color: "var(--text-primary)" }}>{activeHouseSystem}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="secondary" onClick={() => setStep(2)}>
                  ← Back
                </Button>
                <Button onClick={handleViewReport}>
                  View Transit Analysis →
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t p-4" style={{ borderColor: "var(--border-primary)" }}>
          <div />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={step === 1 ? onClose : () => setStep((s) => s - 1)}
              className="obsidian-btn-secondary text-sm"
            >
              {step === 1 ? "Cancel" : "Back"}
            </button>
            {step < 3 && (
              <button
                type="button"
                onClick={() => step === 1 ? setStep(2) : setStep(3)}
                disabled={step === 1 && charts.length === 0 && !request}
                className="obsidian-btn-primary text-sm"
              >
                Continue →
              </button>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
