"use client";

import { useRouter } from "next/navigation";

import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import { ApiError, api } from "@/lib/api";
import { useMyCharts } from "@/lib/charts";
import { compatibilityApi, type CompatibilityResponse } from "@/lib/research";
import type { BirthChartSummary, PlaceResultResponse, TimezoneResolutionResponse } from "@/lib/types";
import { useState } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface PersonFormState {
  name: string;
  birthDate: string;
  birthTime: string;
  placeSearchText: string;
  resolvedPlace: PlaceResultResponse | null;
  gender: "Male" | "Female" | "Other";
  saveToMyCharts: boolean;
  chartId?: string | null;
  sourceUtc?: string | null;
}

function emptyPerson(gender: PersonFormState["gender"]): PersonFormState {
  return {
    name: "",
    birthDate: "",
    birthTime: "",
    placeSearchText: "",
    resolvedPlace: null,
    gender,
    saveToMyCharts: false,
    chartId: null,
    sourceUtc: null,
  };
}

async function resolvePerson(
  person: PersonFormState,
  label: string,
): Promise<{ utc: string; latitude: number; longitude: number }> {
  const place = person.resolvedPlace;
  if (!place) throw new Error(`${label}: pick a birth place from the search results.`);
  if (person.sourceUtc) return { utc: person.sourceUtc, latitude: place.latitude, longitude: place.longitude };
  if (!person.birthDate || !person.birthTime) throw new Error(`${label}: enter both a date and time of birth.`);
  const tz = await api.get<TimezoneResolutionResponse>(
    `/api/v1/geocode/timezone?latitude=${place.latitude}&longitude=${place.longitude}&local_date=${person.birthDate}`,
  );
  const [year, month, day] = person.birthDate.split("-").map(Number);
  const parts = person.birthTime.split(":").map(Number);
  const hour = parts[0] ?? 0;
  const minute = parts[1] ?? 0;
  const second = parts[2] ?? 0;
  const localAsUtcMs = Date.UTC(year!, month! - 1, day!, hour, minute, second);
  return {
    utc: new Date(localAsUtcMs - tz.utc_offset_minutes * 60_000).toISOString(),
    latitude: place.latitude,
    longitude: place.longitude,
  };
}

function fmtScore(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

const RELATIONSHIP_OPTIONS = [
  { value: "marriage",     label: "Marriage / Matrimonial" },
  { value: "business",     label: "Business Partnership" },
  { value: "friendship",   label: "Friendship" },
  { value: "parent_child", label: "Parent – Child" },
] as const;

type RelType = "marriage" | "business" | "friendship" | "parent_child";

// Radar geometry
const RC = 100;
const RR = 72;
function radarPoint(i: number, n: number, pct: number): [number, number] {
  const a = (-90 + (360 / n) * i) * (Math.PI / 180);
  const r = RR * Math.max(0, Math.min(100, pct)) / 100;
  return [RC + r * Math.cos(a), RC + r * Math.sin(a)];
}
function radarPolygon(vals: number[]): string {
  return vals.map((v, i) => radarPoint(i, vals.length, v).join(",")).join(" ");
}

const STATUS_COLOR: Record<string, string> = {
  Excellent: "#10b981",
  Good:      "#f59e0b",
  Average:   "#f59e0b",
  Poor:      "#ef4444",
};
function statusColor(s: string) { return STATUS_COLOR[s] ?? "var(--text-muted)"; }

/* ── Chart search dropdown ── */
const ACCENT_BORDER: Record<string, string> = {
  purple: "rgba(168,85,247,0.35)",
  blue:   "rgba(6,182,212,0.35)",
};
const ACCENT_HOVER: Record<string, string> = {
  purple: "rgba(168,85,247,0.08)",
  blue:   "rgba(6,182,212,0.08)",
};

function ChartSearchResults({
  visible, query, matches, isLoading, error, totalSaved, onSelect, accent,
}: {
  visible: boolean; query: string; matches: BirthChartSummary[]; isLoading: boolean;
  error: unknown; totalSaved: number; onSelect: (c: BirthChartSummary) => void; accent: "purple" | "blue";
}) {
  if (!visible || query.trim() === "") return null;
  const shell = (
    <div
      className="absolute left-0 right-0 top-full z-20 mt-1 max-h-44 overflow-y-auto rounded-lg border p-1 shadow-xl"
      style={{ borderColor: ACCENT_BORDER[accent], backgroundColor: "var(--obsidian-surface-elevated)" }}
    >
      {isLoading ? (
        <p className="px-2 py-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>Loading saved charts…</p>
      ) : error ? (
        <p className="px-2 py-1.5 text-[11px] text-red-400">
          {error instanceof ApiError ? error.detail : "Could not load saved charts."}
        </p>
      ) : totalSaved === 0 ? (
        <p className="px-2 py-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
          No saved charts yet — enter birth details below.
        </p>
      ) : matches.length === 0 ? (
        <p className="px-2 py-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
          No match for "{query.trim()}".
        </p>
      ) : (
        matches.map((c) => (
          <div
            key={c.id}
            onClick={() => onSelect(c)}
            className="cursor-pointer rounded-md p-2 text-xs transition"
            style={{ color: "var(--text-secondary)" }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = ACCENT_HOVER[accent])}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
          >
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>{c.subject_name}</p>
            <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
              {c.birth_datetime_utc.split("T")[0]}
              {c.place_name ? ` · ${c.place_name}` : ""}
            </p>
          </div>
        ))
      )}
    </div>
  );
  return shell;
}

/* ── Person form card ── */
function PersonCard({
  label, accent, accentBorder, accentSoft,
  person, setPerson,
  foundChart, setFoundChart,
  searchQuery, setSearchQuery,
  showResults, setShowResults,
  filteredCharts, savedCharts,
  handleSelectChart,
}: {
  label: string; accent: string; accentBorder: string; accentSoft: string;
  person: PersonFormState; setPerson: (p: PersonFormState) => void;
  foundChart: BirthChartSummary | null; setFoundChart: (c: BirthChartSummary | null) => void;
  searchQuery: string; setSearchQuery: (s: string) => void;
  showResults: boolean; setShowResults: (v: boolean) => void;
  filteredCharts: BirthChartSummary[];
  savedCharts: ReturnType<typeof useMyCharts>;
  handleSelectChart: (c: BirthChartSummary) => void;
}) {
  return (
    <div
      className="rounded-xl border p-5 space-y-4"
      style={{ borderColor: accentBorder, backgroundColor: accentSoft }}
    >
      {/* Card header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="flex h-7 w-7 items-center justify-center rounded-full"
            style={{ backgroundColor: accentBorder, color: accent }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="8" r="4" /><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8" />
            </svg>
          </div>
          <span className="text-xs font-bold" style={{ color: accent }}>{label}</span>
        </div>
        {foundChart && (
          <span
            className="rounded-md border px-2 py-0.5 text-[10px] font-semibold"
            style={{ borderColor: "rgba(16,185,129,0.35)", backgroundColor: "rgba(16,185,129,0.1)", color: "#10b981" }}
          >
            ✓ From saved chart
          </span>
        )}
      </div>

      {/* Search existing */}
      <div className="relative">
        <label className="mb-1 block text-[11px] font-medium" style={{ color: "var(--text-muted)" }}>
          Search Saved Chart
        </label>
        <input
          type="text"
          placeholder="Search by name or place…"
          value={searchQuery}
          onFocus={() => setShowResults(true)}
          onChange={(e) => { setSearchQuery(e.target.value); setShowResults(true); }}
          className="obsidian-input w-full text-xs"
        />
        <ChartSearchResults
          visible={showResults}
          query={searchQuery}
          matches={filteredCharts}
          isLoading={savedCharts.isLoading}
          error={savedCharts.error}
          totalSaved={savedCharts.data?.charts.length ?? 0}
          onSelect={handleSelectChart}
          accent={accent === "rgba(168,85,247,0.35)" ? "purple" : "blue"}
        />
      </div>

      {/* Divider */}
      <div className="relative flex items-center justify-center py-0.5">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t" style={{ borderColor: "var(--border-primary)" }} />
        </div>
        <span
          className="relative px-2 text-[10px] font-bold uppercase tracking-widest"
          style={{ backgroundColor: "var(--obsidian-surface-elevated)", color: "var(--text-muted)" }}
        >
          or enter details
        </span>
      </div>

      {/* Form fields */}
      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-[11px] font-medium" style={{ color: "var(--text-secondary)" }}>Full Name</label>
          <input
            type="text"
            value={person.name}
            onChange={(e) => { setFoundChart(null); setPerson({ ...person, name: e.target.value }); }}
            className="obsidian-input w-full"
            placeholder="Unnamed"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-[11px] font-medium" style={{ color: "var(--text-secondary)" }}>Date of Birth</label>
            <input
              type="date"
              value={person.birthDate}
              onChange={(e) => setPerson({ ...person, birthDate: e.target.value, sourceUtc: null })}
              className="obsidian-input w-full"
            />
          </div>
          <div>
            <label className="mb-1 block text-[11px] font-medium" style={{ color: "var(--text-secondary)" }}>Time of Birth</label>
            <input
              type="time"
              step="1"
              value={person.birthTime}
              onChange={(e) => setPerson({ ...person, birthTime: e.target.value, sourceUtc: null })}
              className="obsidian-input w-full"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-[11px] font-medium" style={{ color: "var(--text-secondary)" }}>Place of Birth</label>
          <BirthPlaceSearch
            value={person.placeSearchText}
            onChange={(text) => setPerson({ ...person, placeSearchText: text, resolvedPlace: null, sourceUtc: null })}
            onSelect={(place) => setPerson({ ...person, resolvedPlace: place, placeSearchText: place.display_name, sourceUtc: null })}
          />
        </div>

        {!foundChart && (
          <>
            <div>
              <label className="mb-1 block text-[11px] font-medium" style={{ color: "var(--text-secondary)" }}>Gender</label>
              <div className="flex gap-4">
                {(["Male", "Female", "Other"] as const).map((g) => (
                  <label key={g} className="flex cursor-pointer items-center gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                    <input
                      type="radio"
                      name={`gender-${label}`}
                      checked={person.gender === g}
                      onChange={() => setPerson({ ...person, gender: g })}
                      className="accent-purple-500"
                    />
                    {g}
                  </label>
                ))}
              </div>
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-xs" style={{ color: "var(--text-muted)" }}>
              <input
                type="checkbox"
                checked={person.saveToMyCharts}
                onChange={(e) => setPerson({ ...person, saveToMyCharts: e.target.checked })}
                className="accent-purple-500"
              />
              Save to My Charts
            </label>
          </>
        )}

        {/* Location resolved indicator */}
        {person.resolvedPlace && (
          <p className="text-[10px]" style={{ color: "#10b981" }}>
            ✓ {person.resolvedPlace.display_name} ({person.resolvedPlace.latitude.toFixed(3)}°, {person.resolvedPlace.longitude.toFixed(3)}°)
          </p>
        )}
      </div>
    </div>
  );
}

/* ──────────────────────────────────────── */
/*  Main modal                              */
/* ──────────────────────────────────────── */
export function CreateCompatibilityModal({ open, onClose }: Props) {
  const router = useRouter();
  const [relationshipType, setRelationshipType] = useState<RelType>("marriage");

  const [personA, setPersonA] = useState<PersonFormState>(() => emptyPerson("Male"));
  const [searchQueryA, setSearchQueryA] = useState("");
  const [showSearchResultsA, setShowSearchResultsA] = useState(false);
  const [foundChartA, setFoundChartA] = useState<BirthChartSummary | null>(null);

  const [personB, setPersonB] = useState<PersonFormState>(() => emptyPerson("Female"));
  const [searchQueryB, setSearchQueryB] = useState("");
  const [showSearchResultsB, setShowSearchResultsB] = useState(false);
  const [foundChartB, setFoundChartB] = useState<BirthChartSummary | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<CompatibilityResponse | null>(null);

  const savedCharts = useMyCharts();

  if (!open) return null;

  const allCharts = savedCharts.data?.charts ?? [];
  const matchCharts = (q: string) => {
    const lq = q.trim().toLowerCase();
    if (!lq) return [];
    return allCharts.filter(
      (c) => c.subject_name.toLowerCase().includes(lq) || (c.place_name ?? "").toLowerCase().includes(lq),
    );
  };

  const handleSelectChartA = (chart: BirthChartSummary) => {
    setFoundChartA(chart);
    const dateObj = new Date(chart.birth_datetime_utc);
    setPersonA({
      ...personA,
      name: chart.subject_name,
      birthDate: dateObj.toISOString().split("T")[0] || "",
      birthTime: dateObj.toISOString().split("T")[1]?.substring(0, 8) || "12:00:00",
      placeSearchText: chart.place_name || "",
      resolvedPlace: { display_name: chart.place_name || "", latitude: chart.birth_latitude, longitude: chart.birth_longitude, country: null, state: null },
      saveToMyCharts: false, chartId: chart.id, sourceUtc: chart.birth_datetime_utc,
    });
    setSearchQueryA(""); setShowSearchResultsA(false);
  };

  const handleSelectChartB = (chart: BirthChartSummary) => {
    setFoundChartB(chart);
    const dateObj = new Date(chart.birth_datetime_utc);
    setPersonB({
      ...personB,
      name: chart.subject_name,
      birthDate: dateObj.toISOString().split("T")[0] || "",
      birthTime: dateObj.toISOString().split("T")[1]?.substring(0, 8) || "12:00:00",
      placeSearchText: chart.place_name || "",
      resolvedPlace: { display_name: chart.place_name || "", latitude: chart.birth_latitude, longitude: chart.birth_longitude, country: null, state: null },
      saveToMyCharts: false, chartId: chart.id, sourceUtc: chart.birth_datetime_utc,
    });
    setSearchQueryB(""); setShowSearchResultsB(false);
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setApiError(null);
    setPreviewResult(null);
    try {
      const [a, b] = await Promise.all([
        resolvePerson(personA, "Person A"),
        resolvePerson(personB, "Person B"),
      ]);
      const response = await compatibilityApi.analyze({
        birth_datetime_utc_a: a.utc, latitude_a: a.latitude, longitude_a: a.longitude,
        subject_name_a: personA.name || "Person A",
        birth_datetime_utc_b: b.utc, latitude_b: b.latitude, longitude_b: b.longitude,
        subject_name_b: personB.name || "Person B",
        relationship_type: relationshipType,
      });
      setPreviewResult(response);

      // Navigate to full report page
      const params = new URLSearchParams({
        birth_datetime_utc_a: a.utc,
        latitude_a: String(a.latitude),
        longitude_a: String(a.longitude),
        subject_name_a: personA.name || "Person A",
        birth_datetime_utc_b: b.utc,
        latitude_b: String(b.latitude),
        longitude_b: String(b.longitude),
        subject_name_b: personB.name || "Person B",
        relationship_type: relationshipType,
      });
      onClose();
      router.push(`/compatibility/report?${params.toString()}`);
    } catch (err) {
      setPreviewResult(null);
      setApiError(err instanceof Error ? err.message : "Calculation engine unavailable");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const relLabel = RELATIONSHIP_OPTIONS.find((o) => o.value === relationshipType)?.label ?? "Marriage";

  const canAnalyze =
    !!personA.resolvedPlace &&
    (!!personA.sourceUtc || (!!personA.birthDate && !!personA.birthTime)) &&
    !!personB.resolvedPlace &&
    (!!personB.sourceUtc || (!!personB.birthDate && !!personB.birthTime));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div
        className="obsidian-card relative flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden"
        style={{ backgroundColor: "var(--obsidian-surface-elevated)" }}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between border-b px-6 py-4" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-3">
            <div
              className="flex h-9 w-9 items-center justify-center rounded-lg"
              style={{ backgroundColor: "rgba(168,85,247,0.12)", color: "var(--obsidian-accent-tertiary, #a855f7)" }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                Compatibility Analysis
              </h2>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Search saved charts or enter birth details to generate a full report
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1.5 transition hover:opacity-70"
            style={{ color: "var(--text-muted)" }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* ── Relationship type selector (top, full-width) ── */}
        <div className="border-b px-6 py-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <div className="flex items-center gap-3">
            <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Relationship Type
            </span>
            <div className="flex flex-wrap gap-2">
              {RELATIONSHIP_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { setRelationshipType(opt.value); setPreviewResult(null); }}
                  className="rounded-lg border px-3 py-1.5 text-xs font-semibold transition hover:opacity-80"
                  style={{
                    borderColor: relationshipType === opt.value ? "rgba(168,85,247,0.5)" : "var(--border-primary)",
                    backgroundColor: relationshipType === opt.value ? "rgba(168,85,247,0.1)" : "transparent",
                    color: relationshipType === opt.value ? "var(--obsidian-accent-tertiary, #a855f7)" : "var(--text-muted)",
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ── Body ── */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {/* Two person cards */}
          <div className="grid grid-cols-2 gap-5">
            <PersonCard
              label={relationshipType === "parent_child" ? "Parent" : "Person A"}
              accent="rgba(168,85,247,1)"
              accentBorder="rgba(168,85,247,0.2)"
              accentSoft="rgba(168,85,247,0.05)"
              person={personA} setPerson={setPersonA}
              foundChart={foundChartA} setFoundChart={setFoundChartA}
              searchQuery={searchQueryA} setSearchQuery={setSearchQueryA}
              showResults={showSearchResultsA} setShowResults={setShowSearchResultsA}
              filteredCharts={matchCharts(searchQueryA)}
              savedCharts={savedCharts}
              handleSelectChart={handleSelectChartA}
            />
            <PersonCard
              label={relationshipType === "parent_child" ? "Child" : "Person B"}
              accent="rgba(6,182,212,1)"
              accentBorder="rgba(6,182,212,0.2)"
              accentSoft="rgba(6,182,212,0.05)"
              person={personB} setPerson={setPersonB}
              foundChart={foundChartB} setFoundChart={setFoundChartB}
              searchQuery={searchQueryB} setSearchQuery={setSearchQueryB}
              showResults={showSearchResultsB} setShowResults={setShowSearchResultsB}
              filteredCharts={matchCharts(searchQueryB)}
              savedCharts={savedCharts}
              handleSelectChart={handleSelectChartB}
            />
          </div>

          {/* Preview result (quick inline while navigating) */}
          {previewResult && (
            <div
              className="mt-5 rounded-xl border p-4"
              style={{ borderColor: "rgba(168,85,247,0.25)", backgroundColor: "rgba(168,85,247,0.06)" }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold" style={{ color: "var(--obsidian-accent-tertiary, #a855f7)" }}>
                    {relLabel}
                  </p>
                  <p className="text-sm font-black" style={{ color: "var(--text-primary)" }}>
                    {previewResult.subject_name_a} · {previewResult.subject_name_b}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>
                    {Math.round(previewResult.compatibility_percentage)}%
                  </p>
                  <p className="text-xs" style={{ color: "var(--obsidian-accent-tertiary, #a855f7)" }}>
                    {previewResult.verdict}
                  </p>
                </div>
              </div>
              {/* Mini koota grid */}
              <div className="mt-3 grid grid-cols-4 gap-2">
                {previewResult.kootas.slice(0, 8).map((k) => {
                  const pct = (k.obtained_score / k.max_score) * 100;
                  const sc = statusColor(k.status);
                  return (
                    <div key={k.name} className="rounded-lg border p-2 text-center"
                      style={{ borderColor: "var(--border-primary)" }}>
                      <p className="text-[9px]" style={{ color: "var(--text-muted)" }}>{k.name}</p>
                      <p className="text-xs font-bold" style={{ color: sc }}>
                        {fmtScore(k.obtained_score)}/{fmtScore(k.max_score)}
                      </p>
                    </div>
                  );
                })}
              </div>
              <p className="mt-3 text-center text-[11px]" style={{ color: "var(--text-muted)" }}>
                Redirecting to full report…
              </p>
            </div>
          )}

          {/* Error */}
          {apiError && (
            <div
              className="mt-5 rounded-xl border px-4 py-3 text-xs"
              style={{ borderColor: "rgba(239,68,68,0.35)", backgroundColor: "rgba(239,68,68,0.06)", color: "#ef4444" }}
            >
              <span className="font-bold">Analysis failed: </span>{apiError}
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div
          className="flex items-center justify-between border-t px-6 py-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <p className="flex items-center gap-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
            </svg>
            Your data is secure and private
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="obsidian-btn-secondary text-sm"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isAnalyzing || !canAnalyze}
              className="obsidian-btn-primary text-sm disabled:opacity-50"
              title={!canAnalyze ? "Enter birth details for both people first" : undefined}
            >
              {isAnalyzing ? (
                <>
                  <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-t-transparent" />
                  Analyzing…
                </>
              ) : (
                `Analyze ${relLabel} →`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
