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
  /**
   * Set only when the person was populated from a saved chart, whose
   * birth_datetime_utc is already a true UTC instant. The birthDate /
   * birthTime fields are then the UTC components of that instant, NOT
   * local wall-clock time at the birth place, so they must not be run
   * through the local→UTC conversion below. Cleared the moment the user
   * edits date, time, or place, at which point the fields become
   * user-entered local time again.
   */
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

/**
 * Converts a local calendar date+time at a known UTC offset into the true
 * UTC instant, without ever touching the browser's own timezone. Same
 * approach as BirthDetailsForm's helper: Date.UTC() treats the y/m/d/h/m/s
 * as literal wall-clock numbers with no timezone applied, so subtracting
 * the birth place's actual offset (resolved server-side for this exact
 * date, DST/historical rules included) yields the correct UTC instant.
 */
function localToUtcIso(dateStr: string, timeStr: string, utcOffsetMinutes: number): string {
  const [year, month, day] = dateStr.split("-").map(Number);
  const timeParts = timeStr.split(":").map(Number);
  const hour = timeParts[0] ?? 0;
  const minute = timeParts[1] ?? 0;
  const second = timeParts[2] ?? 0;
  const localAsUtcMs = Date.UTC(year!, month! - 1, day!, hour, minute, second);
  return new Date(localAsUtcMs - utcOffsetMinutes * 60_000).toISOString();
}

interface ResolvedPerson {
  utc: string;
  latitude: number;
  longitude: number;
}

/**
 * Resolves one person's form state into the UTC instant + coordinates the
 * compatibility engine expects. A person taken from a saved chart already
 * carries a true UTC instant; anything typed into the form is local time at
 * the birth place and needs the timezone lookup first.
 */
async function resolvePerson(person: PersonFormState, label: string): Promise<ResolvedPerson> {
  const place = person.resolvedPlace;
  if (!place) {
    throw new Error(`${label}: pick a birth place from the search results so its coordinates resolve.`);
  }
  if (person.sourceUtc) {
    return { utc: person.sourceUtc, latitude: place.latitude, longitude: place.longitude };
  }
  if (!person.birthDate || !person.birthTime) {
    throw new Error(`${label}: enter both a date and time of birth.`);
  }

  const tz = await api.get<TimezoneResolutionResponse>(
    `/api/v1/geocode/timezone?latitude=${place.latitude}` +
      `&longitude=${place.longitude}&local_date=${person.birthDate}`,
  );

  return {
    utc: localToUtcIso(person.birthDate, person.birthTime, tz.utc_offset_minutes),
    latitude: place.latitude,
    longitude: place.longitude,
  };
}

const STATUS_TEXT_CLASS: Record<string, string> = {
  Excellent: "text-emerald-400",
  Good: "text-amber-400",
  Average: "text-amber-400",
  Poor: "text-red-400",
};

function statusClass(status: string): string {
  return STATUS_TEXT_CLASS[status] ?? "text-slate-400";
}

/** Kootas are scored on fractional half-points; trim trailing ".0" for display. */
function fmtScore(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

// Radar geometry — one axis per koota, in the order the engine returns them.
const RADAR_CENTER = 100;
const RADAR_RADIUS = 72;

function radarPoint(index: number, count: number, pct: number): [number, number] {
  const angle = (-90 + (360 / count) * index) * (Math.PI / 180);
  const r = RADAR_RADIUS * Math.max(0, Math.min(100, pct)) / 100;
  return [RADAR_CENTER + r * Math.cos(angle), RADAR_CENTER + r * Math.sin(angle)];
}

function radarPolygon(values: number[]): string {
  return values.map((v, i) => radarPoint(i, values.length, v).join(",")).join(" ");
}

// Tailwind needs whole class names at build time, so the per-person accent
// colours are looked up rather than interpolated.
const ACCENT = {
  purple: { border: "border-purple-500/40", hover: "hover:bg-purple-600/30" },
  blue: { border: "border-blue-500/40", hover: "hover:bg-blue-600/30" },
} as const;

interface ChartSearchResultsProps {
  visible: boolean;
  query: string;
  matches: BirthChartSummary[];
  /** Fetch state of the whole saved-charts list, shared by both persons. */
  isLoading: boolean;
  error: unknown;
  totalSaved: number;
  onSelect: (chart: BirthChartSummary) => void;
  accent: keyof typeof ACCENT;
}

/**
 * Dropdown under the "Search Existing Chart" input. Renders the real
 * saved-charts list, and says so plainly when it is loading, failed, or
 * has nothing to match — an empty dropdown would otherwise be
 * indistinguishable from "no results".
 */
function ChartSearchResults({
  visible, query, matches, isLoading, error, totalSaved, onSelect, accent,
}: ChartSearchResultsProps) {
  if (!visible || query.trim() === "") return null;

  const { border, hover } = ACCENT[accent];
  const shell = `absolute left-0 right-0 top-full z-20 mt-1 max-h-48 overflow-y-auto rounded-lg border ${border} bg-white dark:bg-slate-900 p-1 shadow-2xl`;
  const note = (text: string, tone = "text-slate-500 dark:text-slate-400") => (
    <div className={shell}>
      <p className={`px-2 py-1.5 text-[11px] ${tone}`}>{text}</p>
    </div>
  );

  if (isLoading) return note("Loading your saved charts…", "text-slate-500 dark:text-slate-400");
  if (error) {
    return note(
      error instanceof ApiError ? error.detail : "Could not load your saved charts.",
      "text-rose-500",
    );
  }
  if (totalSaved === 0) return note("You have no saved charts yet — enter birth details below instead.");
  if (matches.length === 0) return note(`No saved chart matches “${query.trim()}”.`);

  return (
    <div className={shell}>
      {matches.map((c) => (
        <div
          key={c.id}
          onClick={() => onSelect(c)}
          className={`cursor-pointer rounded-md p-2 ${hover} transition text-xs`}
        >
          <p className="font-bold text-slate-900 dark:text-slate-100">{c.subject_name}</p>
          <p className="text-[10px] text-slate-600 dark:text-slate-400">
            {c.birth_datetime_utc.split("T")[0]}
            {c.place_name ? ` · ${c.place_name}` : ""}
          </p>
        </div>
      ))}
    </div>
  );
}

export function CreateCompatibilityModal({ open, onClose }: Props) {
  const router = useRouter();
  const [relationshipType, setRelationshipType] = useState<"marriage" | "business" | "friendship" | "parent_child">("marriage");
  const [activeTab, setActiveTab] = useState<"ashtakoota" | "timing">("ashtakoota");

  // Person A State
  const [personA, setPersonA] = useState<PersonFormState>(() => emptyPerson("Male"));
  const [searchQueryA, setSearchQueryA] = useState("");
  const [showSearchResultsA, setShowSearchResultsA] = useState(false);
  const [foundChartA, setFoundChartA] = useState<BirthChartSummary | null>(null);

  // Person B State
  const [personB, setPersonB] = useState<PersonFormState>(() => emptyPerson("Female"));
  const [searchQueryB, setSearchQueryB] = useState("");
  const [showSearchResultsB, setShowSearchResultsB] = useState(false);
  const [foundChartB, setFoundChartB] = useState<BirthChartSummary | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<CompatibilityResponse | null>(null);

  // The user's real saved charts (GET /api/v1/horoscope/my-charts). Declared
  // before the `open` early-return so hook order stays stable across renders.
  const savedCharts = useMyCharts();

  if (!open) return null;

  const allCharts = savedCharts.data?.charts ?? [];
  const matchCharts = (query: string) => {
    const q = query.trim().toLowerCase();
    if (q === "") return [];
    return allCharts.filter(
      (c) =>
        c.subject_name.toLowerCase().includes(q) ||
        (c.place_name ?? "").toLowerCase().includes(q),
    );
  };
  const filteredChartsA = matchCharts(searchQueryA);
  const filteredChartsB = matchCharts(searchQueryB);

  const handleSelectChartA = (chart: BirthChartSummary) => {
    setFoundChartA(chart);
    const dateObj = new Date(chart.birth_datetime_utc);
    const dateStr = dateObj.toISOString().split("T")[0] || "";
    const timeStr = dateObj.toISOString().split("T")[1]?.substring(0, 8) || "12:00:00";

    setPersonA((prev) => ({
      ...prev,
      name: chart.subject_name,
      birthDate: dateStr,
      birthTime: timeStr,
      placeSearchText: chart.place_name || "",
      resolvedPlace: { display_name: chart.place_name || "", latitude: chart.birth_latitude, longitude: chart.birth_longitude, country: null, state: null },
      saveToMyCharts: false,
      chartId: chart.id,
      sourceUtc: chart.birth_datetime_utc,
    }));
    setSearchQueryA("");
    setShowSearchResultsA(false);
  };

  const handleSelectChartB = (chart: BirthChartSummary) => {
    setFoundChartB(chart);
    const dateObj = new Date(chart.birth_datetime_utc);
    const dateStr = dateObj.toISOString().split("T")[0] || "";
    const timeStr = dateObj.toISOString().split("T")[1]?.substring(0, 8) || "12:00:00";

    setPersonB((prev) => ({
      ...prev,
      name: chart.subject_name,
      birthDate: dateStr,
      birthTime: timeStr,
      placeSearchText: chart.place_name || "",
      resolvedPlace: { display_name: chart.place_name || "", latitude: chart.birth_latitude, longitude: chart.birth_longitude, country: null, state: null },
      saveToMyCharts: false,
      chartId: chart.id,
      sourceUtc: chart.birth_datetime_utc,
    }));
    setSearchQueryB("");
    setShowSearchResultsB(false);
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setApiError(null);

    try {
      const [a, b] = await Promise.all([
        resolvePerson(personA, "Person A"),
        resolvePerson(personB, "Person B"),
      ]);

      const response = await compatibilityApi.analyze({
        birth_datetime_utc_a: a.utc,
        latitude_a: a.latitude,
        longitude_a: a.longitude,
        subject_name_a: personA.name || "Person A",
        birth_datetime_utc_b: b.utc,
        latitude_b: b.latitude,
        longitude_b: b.longitude,
        subject_name_b: personB.name || "Person B",
        relationship_type: relationshipType,
      });

      setResult(response);

      // After a successful analysis, navigate directly to the dedicated
      // report page instead of keeping the user inside the creation modal.
      // The report includes the relationship profile so the displayed
      // results always match the selected relationship type.
      const reportParams = new URLSearchParams({
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
      router.push(`/compatibility/report?${reportParams.toString()}`);
    } catch (err) {
      // Never fall through to a rendered result on failure — an empty
      // panel with an error is honest, a stale one is not.
      setResult(null);
      setApiError(err instanceof Error ? err.message : "Calculation engine unavailable");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

      <div className="relative flex h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl border border-white/10 shadow-2xl" style={{ backgroundColor: "#0b0f19" }}>
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/20 text-purple-400">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8Z" /></svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Create Compatibility Analysis</h2>
              <p className="text-xs text-slate-400">Search existing chart records or enter new birth details to run compatibility.</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/5 hover:text-white" aria-label="Close dialog">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Content Layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Main Form & Results Deck */}
          <div className="flex flex-1 flex-col overflow-y-auto p-6 space-y-6">
            <div className="grid grid-cols-2 gap-6">
              {/* Person A Section */}
              <div className="rounded-xl border border-purple-500/30 bg-purple-950/10 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-purple-400">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>
                    Person A
                  </div>
                  {foundChartA && <span className="rounded-md bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30">✓ Saved Chart Found</span>}
                </div>

                <div className="relative">
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">🔍 Search Existing Chart</label>
                  <input
                    type="text"
                    placeholder="Search saved charts by name or place..."
                    value={searchQueryA}
                    onFocus={() => setShowSearchResultsA(true)}
                    onChange={(e) => { setSearchQueryA(e.target.value); setShowSearchResultsA(true); }}
                    className="w-full rounded-lg border border-purple-500/40 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 focus:outline-none"
                  />

                  <ChartSearchResults
                    visible={showSearchResultsA}
                    query={searchQueryA}
                    matches={filteredChartsA}
                    isLoading={savedCharts.isLoading}
                    error={savedCharts.error}
                    totalSaved={allCharts.length}
                    onSelect={handleSelectChartA}
                    accent="purple"
                  />
                </div>

                <div className="relative flex items-center justify-center py-1">
                  <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200 dark:border-slate-800" /></div>
                  <span className="relative bg-slate-50 dark:bg-slate-900 px-2 text-[10px] font-semibold tracking-wider text-slate-500 dark:text-slate-400">OR ENTER DETAILS</span>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Full Name</label>
                    <input type="text" value={personA.name} onChange={(e) => { setFoundChartA(null); setPersonA({ ...personA, name: e.target.value }); }} className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-indigo-500 outline-none" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Date of Birth</label>
                      <input type="date" value={personA.birthDate} onChange={(e) => setPersonA({ ...personA, birthDate: e.target.value, sourceUtc: null })} className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Time of Birth</label>
                      <input type="time" step="1" value={personA.birthTime} onChange={(e) => setPersonA({ ...personA, birthTime: e.target.value, sourceUtc: null })} className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 outline-none" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Place of Birth</label>
                    <BirthPlaceSearch value={personA.placeSearchText} onChange={(text) => setPersonA({ ...personA, placeSearchText: text, resolvedPlace: null, sourceUtc: null })} onSelect={(place) => setPersonA({ ...personA, resolvedPlace: place, placeSearchText: place.display_name, sourceUtc: null })} />
                  </div>
                  {!foundChartA && (
                    <>
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Gender</label>
                        <div className="flex gap-4 text-xs text-slate-700 dark:text-slate-300">
                          {(["Male", "Female", "Other"] as const).map((g) => (
                            <label key={g} className="flex items-center gap-1.5 cursor-pointer">
                              <input type="radio" name="genderA" checked={personA.gender === g} onChange={() => setPersonA({ ...personA, gender: g })} className="text-purple-500 focus:ring-purple-400" />
                              {g}
                            </label>
                          ))}
                        </div>
                      </div>
                      <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 pt-1 cursor-pointer">
                        <input type="checkbox" checked={personA.saveToMyCharts} onChange={(e) => setPersonA({ ...personA, saveToMyCharts: e.target.checked })} className="rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-purple-500" />
                        Save Person A to My Charts
                      </label>
                    </>
                  )}
                </div>
              </div>

              {/* Person B Section */}
              <div className="rounded-xl border border-blue-500/30 bg-blue-950/10 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-blue-500 dark:text-blue-400">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>
                    Person B
                  </div>
                  {foundChartB && <span className="rounded-md bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30">✓ Saved Chart Found</span>}
                </div>

                <div className="relative">
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">🔍 Search Existing Chart</label>
                  <input
                    type="text"
                    placeholder="Search saved charts by name or place..."
                    value={searchQueryB}
                    onFocus={() => setShowSearchResultsB(true)}
                    onChange={(e) => { setSearchQueryB(e.target.value); setShowSearchResultsB(true); }}
                    className="w-full rounded-lg border border-blue-500/40 bg-white dark:bg-slate-900 px-3 py-2 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
                  />

                  <ChartSearchResults
                    visible={showSearchResultsB}
                    query={searchQueryB}
                    matches={filteredChartsB}
                    isLoading={savedCharts.isLoading}
                    error={savedCharts.error}
                    totalSaved={allCharts.length}
                    onSelect={handleSelectChartB}
                    accent="blue"
                  />
                </div>

                <div className="relative flex items-center justify-center py-1">
                  <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-200 dark:border-slate-800" /></div>
                  <span className="relative bg-slate-50 dark:bg-slate-900 px-2 text-[10px] font-semibold tracking-wider text-slate-500 dark:text-slate-400">OR ENTER DETAILS</span>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Full Name</label>
                    <input type="text" value={personB.name} onChange={(e) => { setFoundChartB(null); setPersonB({ ...personB, name: e.target.value }); }} className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-indigo-500 outline-none" />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Date of Birth</label>
                      <input type="date" value={personB.birthDate} onChange={(e) => setPersonB({ ...personB, birthDate: e.target.value, sourceUtc: null })} className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Time of Birth</label>
                      <input type="time" step="1" value={personB.birthTime} onChange={(e) => setPersonB({ ...personB, birthTime: e.target.value, sourceUtc: null })} className="w-full rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 outline-none" />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Place of Birth</label>
                    <BirthPlaceSearch value={personB.placeSearchText} onChange={(text) => setPersonB({ ...personB, placeSearchText: text, resolvedPlace: null, sourceUtc: null })} onSelect={(place) => setPersonB({ ...personB, resolvedPlace: place, placeSearchText: place.display_name, sourceUtc: null })} />
                  </div>

                  {!foundChartB && (
                    <>
                      <div>
                        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Gender</label>
                        <div className="flex gap-4 text-xs text-slate-700 dark:text-slate-300">
                          {(["Male", "Female", "Other"] as const).map((g) => (
                            <label key={g} className="flex items-center gap-1.5 cursor-pointer">
                              <input type="radio" name="genderB" checked={personB.gender === g} onChange={() => setPersonB({ ...personB, gender: g })} className="text-blue-500 focus:ring-blue-400" />
                              {g}
                            </label>
                          ))}
                        </div>
                      </div>

                      <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 pt-1 cursor-pointer">
                        <input type="checkbox" checked={personB.saveToMyCharts} onChange={(e) => setPersonB({ ...personB, saveToMyCharts: e.target.checked })} className="rounded border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-blue-500" />
                        Save Person B to My Charts
                      </label>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Context Selector & Action Bar */}
            <div className="flex items-center justify-between rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-4">
              <div className="flex items-center gap-3">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300">Relationship Type:</label>
                <select value={relationshipType} onChange={(e) => { setRelationshipType(e.target.value as any); setResult(null); }} className="rounded-lg border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="marriage">Marriage / Matrimonial</option>
                  <option value="business">Business / Partnership</option>
                  <option value="friendship">Friendship / Social</option>
                  <option value="parent_child">Parent – Child Synastry</option>
                </select>
              </div>

              <button
                type="button"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="rounded-xl bg-purple-600 px-6 py-2.5 text-xs font-bold text-white shadow-lg transition hover:bg-purple-500 disabled:opacity-60"
              >
                {isAnalyzing ? "⏳ Running Synastry Engines..." : "✨ Analyze Compatibility →"}
              </button>
            </div>

            {apiError && (
              <div className="rounded-xl border border-red-500/40 bg-red-950/30 px-4 py-3 text-xs text-red-300">
                <span className="font-bold">Analysis failed:</span> {apiError}
              </div>
            )}

            {/* Analytics Tab Deck */}
            {result && (
              <div className="rounded-xl border border-white/10 bg-black/30 p-4 space-y-4">
                <div className="flex border-b border-white/10">
                  <button onClick={() => setActiveTab("ashtakoota")} className={`px-4 py-2 text-xs font-semibold border-b-2 transition ${activeTab === "ashtakoota" ? "border-purple-500 text-purple-400" : "border-transparent text-slate-400 hover:text-slate-200"}`}>
                    Ashtakoota Matching (36 Pts)
                  </button>
                  <button onClick={() => setActiveTab("timing")} className={`px-4 py-2 text-xs font-semibold border-b-2 transition ${activeTab === "timing" ? "border-purple-500 text-purple-400" : "border-transparent text-slate-400 hover:text-slate-200"}`}>
                    Marriage Timing Transit Scanner (Ju/Sa)
                  </button>
                </div>

                {activeTab === "ashtakoota" && (
                  <div className="grid grid-cols-2 gap-6 items-center">
                    <div className="space-y-2">
                      <div className="grid grid-cols-4 text-[11px] font-bold text-slate-400 border-b border-white/10 pb-1.5">
                        <span>Koota</span>
                        <span className="text-center">Max</span>
                        <span className="text-center">Score</span>
                        <span className="text-right">Status</span>
                      </div>
                      {result.kootas.map((k, i) => (
                        <div key={k.name} className="grid grid-cols-4 items-center text-xs py-1" title={k.description}>
                          <span className="text-slate-200 font-medium">{i + 1}. {k.name}</span>
                          <span className="text-center text-slate-400">{fmtScore(k.max_score)}</span>
                          <span className="text-center text-white font-bold">{fmtScore(k.obtained_score)}</span>
                          <span className={`text-right text-[11px] font-semibold ${statusClass(k.status)}`}>
                            {k.status === "Poor" ? "✕" : "✓"} {k.status}
                          </span>
                        </div>
                      ))}
                      <div className="flex items-center justify-between border-t border-white/10 pt-3 mt-2">
                        <span className="text-xs font-bold text-white">Total Score</span>
                        <span className="text-xs font-bold text-purple-400">
                          {fmtScore(result.total_score)} / {fmtScore(result.max_total_score)}
                        </span>
                        <span className="rounded-lg bg-purple-500/20 px-2.5 py-1 text-xs font-bold text-purple-300">
                          {Math.round(result.compatibility_percentage)}% {result.verdict}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-col items-center justify-center p-2">
                      {(() => {
                        // One axis per koota, driven by the engine's normalised
                        // 0–100 radar_values (falls back to the koota list's own
                        // order so the labels and the polygon can never drift).
                        const axes = result.kootas.map((k) => ({
                          label: k.name,
                          value: result.radar_values[k.name] ?? (k.obtained_score / k.max_score) * 100,
                        }));
                        const n = axes.length;
                        return (
                          <svg width="220" height="220" viewBox="0 0 200 200" className="overflow-visible">
                            {[100, 66, 33].map((ring) => (
                              <polygon
                                key={ring}
                                points={radarPolygon(axes.map(() => ring))}
                                fill="none"
                                stroke="rgba(255,255,255,0.1)"
                                strokeWidth="1"
                              />
                            ))}
                            {axes.map((a, i) => {
                              const [x, y] = radarPoint(i, n, 100);
                              return <line key={a.label} x1={RADAR_CENTER} y1={RADAR_CENTER} x2={x} y2={y} stroke="rgba(255,255,255,0.1)" />;
                            })}

                            <polygon
                              points={radarPolygon(axes.map((a) => a.value))}
                              fill="rgba(168,85,247,0.3)"
                              stroke="#a855f7"
                              strokeWidth="2"
                            />

                            {axes.map((a, i) => {
                              const [x, y] = radarPoint(i, n, 122);
                              const anchor = x > RADAR_CENTER + 2 ? "start" : x < RADAR_CENTER - 2 ? "end" : "middle";
                              return (
                                <text key={a.label} x={x} y={y} textAnchor={anchor} dominantBaseline="middle" fill="#cbd5e1" fontSize="9">
                                  {a.label}
                                </text>
                              );
                            })}
                          </svg>
                        );
                      })()}
                    </div>
                  </div>
                )}

                {activeTab === "timing" && (
                  <div className="space-y-3 p-2">
                    <p className="text-xs font-bold text-white">Jupiter / Saturn Transit Marriage Window Scanner (Swiss Ephemeris)</p>
                    {/*
                      Still illustrative. apps/api/services/marriage_timing_engine.py
                      exists but is not exposed over HTTP yet, so there is nothing to
                      call — labelled as sample data until that endpoint lands.
                    */}
                    <div className="rounded-lg border border-amber-500/30 bg-amber-950/20 px-3 py-2 text-[11px] text-amber-300">
                      Sample data — the transit scanner is not wired to the backend yet and does not
                      reflect the charts entered above.
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-center text-xs opacity-60">
                      <div className="rounded-lg bg-emerald-950/30 border border-emerald-500/30 p-3">
                        <p className="font-bold text-emerald-400">2027 (Age 37)</p>
                        <p className="text-[10px] text-slate-300 mt-1">🟢 Probable Window</p>
                        <p className="text-[9px] text-slate-400 mt-0.5">Jupiter 5th aspect on Natal Venus</p>
                      </div>
                      <div className="rounded-lg bg-amber-950/30 border border-amber-500/30 p-3">
                        <p className="font-bold text-amber-400">2029 (Age 39)</p>
                        <p className="text-[10px] text-slate-300 mt-1">🟡 Delayed Window</p>
                        <p className="text-[9px] text-slate-400 mt-0.5">Jupiter triggers, Saturn aspects 7th Cusp</p>
                      </div>
                      <div className="rounded-lg bg-slate-900 border border-white/10 p-3">
                        <p className="font-bold text-slate-400">2031 (Age 41)</p>
                        <p className="text-[10px] text-slate-300 mt-1">⚪ Not Indicated</p>
                        <p className="text-[9px] text-slate-500 mt-0.5">No direct Guru aspect on Venus</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Sidebar */}
          <div className="w-80 border-l border-white/10 p-5 space-y-5 overflow-y-auto">
            {!result ? (
              <div className="rounded-xl border border-dashed border-white/10 bg-white/5 p-5 text-center space-y-2">
                <p className="text-xs font-bold text-slate-300">No analysis yet</p>
                <p className="text-[11px] text-slate-500">
                  Enter both birth details and run <span className="text-slate-300">Analyze Compatibility</span> to
                  see the Ashtakoota score, dosha checks, and insights.
                </p>
              </div>
            ) : (
              <>
                <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-center space-y-3">
                  <p className="text-xs font-bold text-slate-400">Overall Compatibility</p>
                  <div className="relative mx-auto flex h-24 w-24 items-center justify-center rounded-full border-4 border-pink-500/80 bg-pink-500/10">
                    <span className="text-2xl font-black text-white">{Math.round(result.compatibility_percentage)}%</span>
                  </div>
                  <div>
                    <p className="text-sm font-bold text-pink-400">{result.verdict}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {result.subject_name_a} & {result.subject_name_b} · {relationshipType.replace("_", " ")}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 border-t border-white/10 pt-3 text-[11px]">
                    <div className="rounded-lg bg-black/40 p-2">
                      <p className="text-slate-400">Ashtakoota Score</p>
                      <p className="text-sm font-bold text-white">{fmtScore(result.total_score)} / {fmtScore(result.max_total_score)}</p>
                    </div>
                    <div className="rounded-lg bg-black/40 p-2">
                      <p className="text-slate-400">Compatibility Index</p>
                      <p className="text-sm font-bold text-white">{Math.round(result.compatibility_percentage)} / 100</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
                  <p className="text-xs font-bold text-white flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    Important Checks
                  </p>
                  <div className="space-y-2 text-xs">
                    {result.doshas.map((d) => (
                      <div key={d.name} className="flex items-center justify-between" title={d.description}>
                        <span className="text-slate-300">{d.name}</span>
                        <span className={`text-[11px] font-semibold ${d.has_dosha ? "text-amber-400" : "text-emerald-400"}`}>
                          {d.severity} {d.has_dosha ? "⚠" : "✓"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-xl border border-purple-500/20 bg-purple-950/20 p-4 space-y-3">
                  <p className="text-xs font-bold text-purple-300 flex items-center gap-1.5"><span>✨</span> Insights</p>
                  <div className="space-y-2 text-[11px]">
                    {result.strengths.length > 0 && (
                      <div>
                        <p className="font-bold text-emerald-400 mb-1">Strengths</p>
                        <ul className="list-disc pl-3 text-slate-300 space-y-0.5">
                          {result.strengths.map((s) => <li key={s}>{s}</li>)}
                        </ul>
                      </div>
                    )}
                    {result.challenges.length > 0 && (
                      <div>
                        <p className="font-bold text-amber-400 mb-1">Challenges</p>
                        <ul className="list-disc pl-3 text-slate-300 space-y-0.5">
                          {result.challenges.map((c) => <li key={c}>{c}</li>)}
                        </ul>
                      </div>
                    )}
                    {result.recommendations.length > 0 && (
                      <div>
                        <p className="font-bold text-purple-400 mb-1">Recommendations</p>
                        <ul className="list-disc pl-3 text-slate-300 space-y-0.5">
                          {result.recommendations.map((r) => <li key={r}>{r}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-white/10 px-6 py-4 bg-black/40">
          <p className="text-[11px] text-slate-500">🔒 Your data is secure and private</p>
          <div className="flex gap-3">
            <button onClick={onClose} className="rounded-xl border border-white/10 px-5 py-2 text-xs font-bold text-slate-300 hover:bg-white/5">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  );
}
