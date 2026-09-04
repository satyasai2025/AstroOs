"use client";

import { useRouter } from "next/navigation";
import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import { useCreateEventAnalysis } from "@/lib/eventAnalysis";
import { useTimezoneResolution } from "@/lib/geocoding";
import { useMyCharts } from "@/lib/charts";
import { useEventCategoryTree } from "@/lib/research";
import type { EventCategoryNode } from "@/lib/research";
import type {
  EventAnalysisScopeFlag,
  PlaceResultResponse,
} from "@/lib/types";
import { useEffect, useMemo, useState } from "react";

/** Local date/time → UTC instant */
function localToUtcIso(dateStr: string, timeStr: string, utcOffsetMinutes: number): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const [h, mi, s] = timeStr.split(":").map(Number);
  const asUtc = Date.UTC(y!, m! - 1, d!, h ?? 0, mi ?? 0, s ?? 0);
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
  { key: "muhurta", label: "Muhurta Fitness", hint: "Moment panchang, tithi, vara, nakshatra & hora auspiciousness" },
  { key: "natal_promise", label: "Natal Promise", hint: "Relevant houses (Bhavas) and Karaka lords promise in D1/D9" },
  { key: "dasha_support", label: "Dasha Support", hint: "Active Vimshottari Mahadasha, Antardasha & Pratyantardasha" },
  { key: "transit_influence", label: "Transit Influence (Gochara)", hint: "Planetary transits over natal sensitive points at event moment" },
  { key: "planetary_strength", label: "Planetary Strength", hint: "Shadbala, Ashtakavarga points, and Digbala ratings" },
  { key: "yogas_activated", label: "Yogas Activated", hint: "Auspicious and inauspicious planetary yogas triggered by event" },
  { key: "overall_score", label: "Composite Success Score", hint: "Weighted probabilistic event manifestation score" },
];

/** Standardized AstroOS Life Event Taxonomy */
export interface EventCategoryConfig {
  id: string;
  name: string;
  icon: string;
  houses: string;
  events: string[];
}

/** Icon mapping for database-driven taxonomy root domains */
const ROOT_ICONS: Record<string, string> = {
  "Career & Professions": "💼",
  Career: "💼",
  Finance: "💰",
  Health: "🏥",
  "Health Conditions": "🩺",
  "Family & Relations": "👪",
  Family: "👪",
  Marriage: "💍",
  Legal: "⚖️",
  Spiritual: "🕉️",
  Property: "🏠",
  Travel: "✈️",
  Education: "🎓",
  Relationships: "💞",
  Loss: "🥀",
  "Personality & Mind": "🧠",
  "Character & Temperament": "🎭",
  "Communication & News": "📰",
  Social: "👥",
  "Fame & Renown": "🌟",
  "Private Life": "🔒",
  "Interests & Inclinations": "✨",
  "Living Patterns": "🌿",
  "World Affairs": "🌍",
  General: "📌",
};

function rootIcon(name: string): string {
  return ROOT_ICONS[name] ?? "📌";
}

/** Collect all leaf nodes (no children) under a taxonomy node */
function collectLeaves(node: EventCategoryNode, out: EventCategoryNode[] = []): EventCategoryNode[] {
  if (!node.children || node.children.length === 0) {
    out.push(node);
  } else {
    for (const child of node.children) collectLeaves(child, out);
  }
  return out;
}

/** First tagged leaf's Vedic anchor, e.g. "2H · Jupiter" */
function rootHousesTag(leaves: EventCategoryNode[]): string {
  const tagged = leaves.find((l) => l.house_number != null);
  if (!tagged || tagged.house_number == null) return "—";
  const h = `${tagged.house_number}H`;
  return tagged.karaka_planet ? `${h} · ${tagged.karaka_planet}` : h;
}

export const ASTROOS_EVENT_CATEGORIES: EventCategoryConfig[] = [
  {
    id: "career",
    name: "Career & Job",
    icon: "💼",
    houses: "10H · 6H · 2H · 11H",
    events: [
      "Job Interview & Selection",
      "New Job Joining",
      "Promotion & Rank Elevation",
      "Business Launch & Incorporation",
      "Contract & Deal Signing",
      "Resignation & Career Shift",
      "Retirement Commencement",
    ],
  },
  {
    id: "marriage",
    name: "Marriage & Relationships",
    icon: "💍",
    houses: "7H · 2H · 11H",
    events: [
      "Engagement & Ring Ceremony",
      "Vivaha / Wedding Muhurta",
      "First Meeting / Proposal",
      "Legal Marriage Registration",
      "Partnership Agreement",
      "Marital Reconciliation",
    ],
  },
  {
    id: "property",
    name: "Property & Real Estate",
    icon: "🏠",
    houses: "4H · 11H · 12H",
    events: [
      "Griha Pravesh (Housewarming)",
      "Property / Flat Purchase Registration",
      "Bhumi Pujan / Construction Start",
      "Vehicle / Car Purchase",
      "Home Renovation Commencement",
      "Property Sale & Handover",
    ],
  },
  {
    id: "finance",
    name: "Finance & Wealth",
    icon: "💰",
    houses: "2H · 11H · 5H · 9H",
    events: [
      "Major Capital Investment",
      "Loan Approval & Disbursal",
      "Gold & Precious Asset Purchase",
      "Debt Settlement & Payoff",
      "Stock Market Portfolio Entry",
      "Inheritance / Legacy Receipt",
    ],
  },
  {
    id: "education",
    name: "Education & Academics",
    icon: "🎓",
    houses: "5H · 9H · 4H",
    events: [
      "University Admission & Enrollment",
      "Competitive Examination Appearance",
      "Vidyarambha Ceremony",
      "Graduation & Degree Award",
      "Research Thesis Submission",
      "Scholarship Grant Receipt",
    ],
  },
  {
    id: "travel",
    name: "Travel & Relocation",
    icon: "✈️",
    houses: "9H · 12H · 3H",
    events: [
      "Visa Application Submission",
      "Foreign Relocation / Immigration Flight",
      "Passport / Green Card Issuance",
      "Sacred Pilgrimage / Tirth Yatra Departure",
      "Domestic City Relocation",
      "International Business Tour",
    ],
  },
  {
    id: "health",
    name: "Health & Medical",
    icon: "🏥",
    houses: "1H · 6H · 8H",
    events: [
      "Surgical Operation / Medical Procedure",
      "Treatment & Therapy Commencement",
      "Ayurvedic Rejuvenation / Detox Start",
      "Medical Diagnostic Evaluation",
      "Hospital Discharge & Full Recovery",
    ],
  },
  {
    id: "family",
    name: "Family & Progeny",
    icon: "👶",
    houses: "5H · 2H · 9H",
    events: [
      "Childbirth / Progeny Arrival",
      "Namakarana (Naming Ceremony)",
      "Annaprashana (First Feeding)",
      "Mundan (Chudakarana Ceremony)",
      "Upanayana (Sacred Thread Ceremony)",
      "Child Adoption Finalization",
    ],
  },
  {
    id: "legal",
    name: "Legal & Governance",
    icon: "⚖️",
    houses: "6H · 9H · 10H",
    events: [
      "Court Case / Petition Filing",
      "Judicial Final Verdict Day",
      "Government Tender Submission",
      "Legal Arbitration & Settlement",
      "Patent / Trademark Filing",
    ],
  },
  {
    id: "spiritual",
    name: "Spiritual & Initiation",
    icon: "🕉️",
    houses: "9H · 5H · 12H · 1H",
    events: [
      "Mantra Diksha & Guru Initiation",
      "Temple Consecration / Yajna Purna Ahuti",
      "Meditation Retreat Commencement",
      "Spiritual Vow / Sannyasa Deeksha",
      "Satyanarayan Katha / Vedic Puja",
    ],
  },
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
  const [chartSearch, setChartSearch] = useState("");

  // Step 1 — subject natal chart
  const [selectedChartId, setSelectedChartId] = useState<string | null>(null);

  // Step 2 — event details
  const [selectedCategory, setSelectedCategory] = useState<string>("career");
  const [eventName, setEventName] = useState<string>("Job Interview & Selection");
  const [isCustomTitle, setIsCustomTitle] = useState(false);

  // Dynamic event-category library (Postgres-backed) with static fallback
  const catTree = useEventCategoryTree();
  const [eventFilter, setEventFilter] = useState("");

  const now = new Date();
  const [eventDate, setEventDate] = useState(now.toISOString().split("T")[0]!);
  const [eventTime, setEventTime] = useState(now.toTimeString().split(" ")[0]!);

  const [useBirthLocation, setUseBirthLocation] = useState(true);
  const [placeSearchText, setPlaceSearchText] = useState("");
  const [eventPlace, setEventPlace] = useState<PlaceResultResponse | null>(null);

  // Step 3 — scope
  const [scope, setScope] = useState<EventAnalysisScopeFlag[]>(
    SCOPE_OPTIONS.map((o) => o.key),
  );

  const selectedChart = charts.find((c) => c.id === selectedChartId) ?? null;

  // Active category object — DB taxonomy preferred, built-in presets fallback
  type CatVM = EventCategoryConfig & { leafCount?: number };
  const dbRoots = useMemo(() => catTree.data?.categories ?? [], [catTree.data]);
  const usingDb = dbRoots.length > 0;

  const dbVMs = useMemo<CatVM[]>(
    () =>
      dbRoots
        .map((root) => {
          const leaves = collectLeaves(root).sort((a, b) => a.name.localeCompare(b.name));
          return {
            id: root.id,
            name: root.name,
            icon: rootIcon(root.name),
            houses: rootHousesTag(leaves),
            events: leaves.map((l) => l.name),
            leafCount: leaves.length,
          };
        })
        .filter((v) => v.events.length > 0),
    [dbRoots],
  );

  const categoryVMs: readonly CatVM[] = usingDb ? dbVMs : ASTROOS_EVENT_CATEGORIES;

  const currentCategoryConfig = useMemo(() => {
    return (
      categoryVMs.find((c) => c.id === selectedCategory) ??
      (usingDb ? categoryVMs[0] : ASTROOS_EVENT_CATEGORIES[0])!
    );
  }, [categoryVMs, selectedCategory, usingDb]);

  // Ensure selection lands on a real DB domain once loaded
  useEffect(() => {
    if (!usingDb || !dbVMs.length) return;
    if (!dbVMs.some((v) => v.id === selectedCategory)) {
      const first = dbVMs[0]!;
      setSelectedCategory(first.id);
      setEventName(first.events[0] ?? "");
      setIsCustomTitle(false);
    }
  }, [usingDb, dbVMs, selectedCategory]);

  const activeLeaf = useMemo<EventCategoryNode | null>(() => {
    if (!usingDb) return null;
    for (const root of dbRoots) {
      const hit = collectLeaves(root).find((l) => l.name === eventName);
      if (hit) return hit;
    }
    return null;
  }, [usingDb, dbRoots, eventName]);

  const visibleEvents = useMemo(() => {
    const evs = currentCategoryConfig?.events ?? [];
    const q = eventFilter.trim().toLowerCase();
    const filtered = q ? evs.filter((e) => e.toLowerCase().includes(q)) : evs;
    return { list: filtered.slice(0, 80), total: filtered.length };
  }, [currentCategoryConfig, eventFilter]);

  // Filtered charts list for search
  const filteredCharts = useMemo(() => {
    if (!chartSearch.trim()) return charts;
    const q = chartSearch.toLowerCase();
    return charts.filter(
      (c) =>
        c.subject_name.toLowerCase().includes(q) ||
        (c.place_name && c.place_name.toLowerCase().includes(q)),
    );
  }, [charts, chartSearch]);

  // Effective event location
  const effectiveLat = eventPlace ? eventPlace.latitude : (useBirthLocation ? selectedChart?.birth_latitude ?? null : null);
  const effectiveLon = eventPlace ? eventPlace.longitude : (useBirthLocation ? selectedChart?.birth_longitude ?? null : null);

  const tzQuery = useTimezoneResolution(
    useBirthLocation || !!eventPlace ? effectiveLat : null,
    useBirthLocation || !!eventPlace ? effectiveLon : null,
    eventDate || null,
  );

  const canContinueToEvent = !!selectedChartId;
  const canContinueToScope = !!eventName.trim() && canContinueToEvent;
  const canAnalyze =
    canContinueToScope &&
    !!eventDate &&
    !!eventTime &&
    (!effectiveLat || !effectiveLon || !!tzQuery.data) &&
    !createAnalysis.isPending;

  function reset() {
    setStep(1);
    setSelectedChartId(null);
    setChartSearch("");
    setEventFilter("");
    setSelectedCategory("career");
    setEventName("Job Interview & Selection");
    setIsCustomTitle(false);
    setEventDate(new Date().toISOString().split("T")[0]!);
    setEventTime(new Date().toTimeString().split(" ")[0]!);
    setUseBirthLocation(true);
    setPlaceSearchText("");
    setEventPlace(null);
    setScope(SCOPE_OPTIONS.map((o) => o.key));
  }

  function handleCategoryChange(catId: string) {
    setSelectedCategory(catId);
    setEventFilter("");
    const vm = categoryVMs.find((c) => c.id === catId);
    if (vm && vm.events.length > 0) {
      setEventName(vm.events[0]!);
      setIsCustomTitle(false);
    }
  }

  function handleHereAndNow() {
    const d = new Date();
    setEventDate(d.toISOString().split("T")[0]!);
    setEventTime(d.toTimeString().split(" ")[0]!);
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
        event_name: eventName.trim() || "Untitled Event",
        category: currentCategoryConfig.name,
        event_datetime_utc: eventDatetimeUtc,
        latitude: eventPlace ? eventPlace.latitude : null,
        longitude: eventPlace ? eventPlace.longitude : null,
        place_name: eventPlace?.display_name
          ? eventPlace.display_name.split(/\s+/).map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(" ")
          : selectedChart.place_name ?? null,
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
      <div className="absolute inset-0 bg-black/80 backdrop-blur-md" onClick={onClose} />

      <div
        className="obsidian-card relative flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border shadow-2xl animate-in fade-in zoom-in-95 duration-200"
        style={{ backgroundColor: "var(--obsidian-surface-elevated, #0f172a)", borderColor: "var(--border-primary)" }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between border-b px-6 py-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl border text-xl"
              style={{
                backgroundColor: "rgba(6,182,212,0.15)",
                borderColor: "rgba(6,182,212,0.3)",
                color: "#06b6d4",
              }}
            >
              📅
            </div>
            <div>
              <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
                Event Analysis (घटना फलादेश)
              </h2>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Analyze a chosen life event moment against a saved natal birth chart
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1.5 transition hover:opacity-70 cursor-pointer"
            style={{ color: "var(--text-muted)" }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Step Rail */}
        <div
          className="flex items-center gap-3 border-b px-6 py-3"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
        >
          {[
            { n: 1, title: "1. Select Natal Chart" },
            { n: 2, title: "2. AstroOS Event Taxonomy" },
            { n: 3, title: "3. Scope & Calculate" },
          ].map((item) => (
            <div key={item.n} className="flex items-center gap-2">
              <span
                className="flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold transition"
                style={{
                  backgroundColor: step >= item.n ? "var(--obsidian-accent-secondary, #06b6d4)" : "transparent",
                  color: step >= item.n ? "#000" : "var(--text-muted)",
                  border: step >= item.n ? "none" : "1px solid var(--border-primary)",
                }}
              >
                {step > item.n ? "✓" : item.n}
              </span>
              <span
                className="text-xs font-semibold hidden sm:inline"
                style={{ color: step === item.n ? "var(--text-primary)" : "var(--text-muted)" }}
              >
                {item.title}
              </span>
              {item.n < 3 && <span className="text-xs text-slate-700">›</span>}
            </div>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6" style={{ backgroundColor: "var(--bg-card)" }}>

          {/* STEP 1: Select Saved Birth Chart */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                  Select Subject Natal Chart
                </h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Pick the person whose natal chart (D1/D9) anchors this event transit and Dasha analysis.
                </p>
              </div>

              {chartsLoading && (
                <p className="text-xs font-mono text-cyan-400">Loading saved birth charts…</p>
              )}

              {!chartsLoading && charts.length === 0 && (
                <div
                  className="rounded-xl border p-4 text-center text-xs"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                >
                  <p style={{ color: "var(--text-secondary)" }}>No saved charts yet.</p>
                  <p className="mt-1" style={{ color: "var(--text-muted)" }}>
                    Please create or import a birth chart first, then return here for event analysis.
                  </p>
                </div>
              )}

              {charts.length > 0 && (
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Search saved charts by name or place..."
                    value={chartSearch}
                    onChange={(e) => setChartSearch(e.target.value)}
                    className="obsidian-input w-full text-xs"
                  />

                  <div className="max-h-[300px] overflow-y-auto space-y-2 pr-1">
                    {filteredCharts.map((c) => {
                      const selected = selectedChartId === c.id;
                      return (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => setSelectedChartId(c.id)}
                          className="flex w-full items-center justify-between gap-3 rounded-xl border p-3.5 text-left transition cursor-pointer"
                          style={{
                            borderColor: selected ? "var(--obsidian-accent-secondary, #06b6d4)" : "var(--border-primary)",
                            backgroundColor: selected ? "rgba(6,182,212,0.12)" : "var(--bg-primary)",
                          }}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className="flex h-9 w-9 items-center justify-center rounded-xl font-bold text-xs border"
                              style={{
                                borderColor: selected ? "var(--obsidian-accent-secondary)" : "var(--border-primary)",
                                backgroundColor: selected ? "rgba(6,182,212,0.2)" : "var(--bg-card)",
                                color: selected ? "#06b6d4" : "var(--text-secondary)",
                              }}
                            >
                              {c.subject_name.slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <p className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                                {c.subject_name} {c.is_default && <span className="text-[10px] text-cyan-400 font-normal">(Default)</span>}
                              </p>
                              <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                                {new Date(c.birth_datetime_utc).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
                                {c.place_name ? ` · ${c.place_name}` : ""}
                              </p>
                            </div>
                          </div>

                          <span
                            className="text-xs font-bold px-3 py-1 rounded-lg border transition"
                            style={{
                              borderColor: selected ? "rgba(6,182,212,0.4)" : "transparent",
                              backgroundColor: selected ? "rgba(6,182,212,0.2)" : "transparent",
                              color: selected ? "#06b6d4" : "var(--text-muted)",
                            }}
                          >
                            {selected ? "Selected ✓" : "Select"}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* STEP 2: AstroOS Event Taxonomy & Time */}
          {step === 2 && (
            <div className="space-y-5">
              <div>
                <h3 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                  Standardized Event Selection (AstroOS Taxonomy)
                </h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Select the certified life event category and specific event type anchored to Vedic Bhavas.
                </p>
              </div>

              {/* 1. Category Selection Pills */}
              <div className="space-y-2">
                <label className="block text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                  1. Choose Life Event Category:
                </label>
                {catTree.isLoading && (
                  <p className="text-xs font-mono text-cyan-400">Loading full event-category library…</p>
                )}
                {catTree.isError && (
                  <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                    ⚠ Category library unavailable right now — showing built-in presets.
                  </p>
                )}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {categoryVMs.map((cat) => {
                    const active = selectedCategory === cat.id;
                    return (
                      <button
                        key={cat.id}
                        type="button"
                        onClick={() => handleCategoryChange(cat.id)}
                        className="flex flex-col items-start p-2.5 rounded-xl border text-left transition cursor-pointer"
                        style={{
                          borderColor: active ? "var(--obsidian-accent-secondary, #06b6d4)" : "var(--border-primary)",
                          backgroundColor: active ? "rgba(6,182,212,0.15)" : "var(--bg-primary)",
                        }}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>{cat.icon}</span>
                          <span className="text-xs font-bold truncate" style={{ color: active ? "#06b6d4" : "var(--text-primary)" }}>
                            {cat.name.split(" ")[0]}
                          </span>
                  {cat.leafCount != null && (
                   <span className="text-[9px] font-mono" style={{ color: "var(--text-muted)" }}>( {cat.leafCount} )</span>
                  )}
                        </div>
                        <span className="text-[10px] mt-1 font-mono" style={{ color: "var(--text-muted)" }}>
                          {cat.houses}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 2. Standardized Event Names Presets */}
              <div className="space-y-2 pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                    2. Select Event Type ({currentCategoryConfig.name}):
                  </label>
                  <button
                    type="button"
                    onClick={() => setIsCustomTitle((v) => !v)}
                    className="text-[11px] font-semibold text-cyan-400 hover:underline cursor-pointer"
                  >
                    {isCustomTitle ? "← Pick from standard presets" : "✏️ Custom title override"}
                  </button>
                </div>

                {!isCustomTitle ? (
                  <div className="space-y-2">
                    {(currentCategoryConfig.events.length > 24 || eventFilter) && (
                      <input
                        type="text"
                        value={eventFilter}
                        onChange={(e) => setEventFilter(e.target.value)}
                        placeholder={`Filter ${currentCategoryConfig.events.length} events…`}
                        className="obsidian-input w-full text-xs"
                      />
                    )}
                    <div className="flex flex-wrap gap-2">
                      {visibleEvents.list.map((ev) => {
                      const active = eventName === ev;
                      return (
                        <button
                          key={ev}
                          type="button"
                          onClick={() => setEventName(ev)}
                          className="px-3 py-1.5 rounded-lg border text-xs font-medium transition cursor-pointer"
                          style={{
                            borderColor: active ? "var(--obsidian-accent-secondary, #06b6d4)" : "var(--border-primary)",
                            backgroundColor: active ? "rgba(6,182,212,0.18)" : "var(--bg-primary)",
                            color: active ? "#06b6d4" : "var(--text-secondary)",
                          }}
                        >
                          {ev} {active && "✓"}
                        </button>
                      );
                    })}
                    </div>
                    {visibleEvents.total > visibleEvents.list.length && (
                      <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                        Showing 80 of {visibleEvents.total} — refine the filter to narrow down.
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-1">
                    <input
                      type="text"
                      value={eventName}
                      onChange={(e) => setEventName(e.target.value)}
                      placeholder="Enter specific custom title (e.g. Google Senior Architect Appointment)"
                      className="obsidian-input w-full text-xs"
                    />
                    <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                      Category remains strictly aligned with {currentCategoryConfig.name} ({currentCategoryConfig.houses}).
                    </p>
                  </div>
                )}
              </div>

              {/* Selected leaf Vedic anchor */}
              {activeLeaf && (activeLeaf.house_number != null || !!activeLeaf.karaka_planet) && (
                <div
                  className="flex flex-wrap items-center gap-2 rounded-lg border px-3 py-1.5"
                  style={{ borderColor: "rgba(6,182,212,0.35)", backgroundColor: "rgba(6,182,212,0.06)" }}
                >
                  <span className="text-[10px] font-mono font-bold text-cyan-300">
                    {activeLeaf.house_number != null ? `${activeLeaf.house_number}H` : ""}
                    {activeLeaf.karaka_planet ? ` · ${activeLeaf.karaka_planet}` : ""}
                  </span>
                  <span className="text-[10px] truncate" style={{ color: "var(--text-muted)" }}>
                    {activeLeaf.path}
                  </span>
                </div>
              )}

              {/* 3. Event Date & Time */}
              <div className="space-y-2 pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                    3. Event Date &amp; Time (Local Moment):
                  </label>
                  <button
                    type="button"
                    onClick={handleHereAndNow}
                    className="text-[11px] font-bold text-cyan-400 hover:underline cursor-pointer flex items-center gap-1"
                  >
                    <span>⚡ Here &amp; Now</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="block text-[11px]" style={{ color: "var(--text-secondary)" }}>Event Date:</span>
                    <input
                      type="date"
                      required
                      value={eventDate}
                      onChange={(e) => setEventDate(e.target.value)}
                      className="obsidian-input w-full text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <span className="block text-[11px]" style={{ color: "var(--text-secondary)" }}>Event Time:</span>
                    <input
                      type="time"
                      step="1"
                      required
                      value={eventTime}
                      onChange={(e) => setEventTime(e.target.value)}
                      className="obsidian-input w-full text-xs"
                    />
                  </div>
                </div>
              </div>

              {/* 4. Event Location */}
              <div className="space-y-2 pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                    4. Event Geographic Location:
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setUseBirthLocation((v) => !v);
                      if (!useBirthLocation) setEventPlace(null);
                    }}
                    className="text-[11px] font-semibold text-cyan-400 hover:underline cursor-pointer"
                  >
                    {useBirthLocation ? "📍 Use different event location" : "👶 Use subject's birth location"}
                  </button>
                </div>

                {useBirthLocation && selectedChart ? (
                  <div
                    className="rounded-xl border p-3 text-xs flex items-center justify-between"
                    style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
                  >
                    <div>
                      <p className="font-bold" style={{ color: "var(--text-primary)" }}>
                        {selectedChart.place_name ?? "Birth location"}
                      </p>
                      <p className="text-[11px] font-mono mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {selectedChart.birth_latitude.toFixed(4)}°N, {selectedChart.birth_longitude.toFixed(4)}°E
                      </p>
                    </div>
                    <span className="text-[11px] text-cyan-400 font-semibold">Matched with Natal Chart</span>
                  </div>
                ) : (
                  <div className="space-y-1">
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
                  </div>
                )}

                {eventDate && !useBirthLocation && eventPlace && renderTzHint()}
              </div>
            </div>
          )}

          {/* STEP 3: Select Scope & Calculate */}
          {step === 3 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                  Select Analysis Dimensions (Scope)
                </h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Choose which astrological dimensions to calculate. All 7 dimensions are recommended for complete fidelity.
                </p>
              </div>

              {/* Event Summary Banner */}
              <div
                className="rounded-xl border p-3.5 text-xs flex flex-wrap items-center justify-between gap-3"
                style={{ borderColor: "rgba(6,182,212,0.3)", backgroundColor: "rgba(6,182,212,0.08)" }}
              >
                <div>
                  <span className="text-cyan-400 font-bold block">{currentCategoryConfig.icon} {eventName}</span>
                  <span style={{ color: "var(--text-muted)" }}>
                    Subject: <strong>{selectedChart?.subject_name}</strong> · Date: {eventDate} {eventTime}
                  </span>
                </div>
                <span className="font-mono text-xs font-bold text-cyan-300">
                  Houses: {currentCategoryConfig.houses}
                </span>
              </div>

              <div className="space-y-2">
                {SCOPE_OPTIONS.map((o) => {
                  const checked = scope.includes(o.key);
                  return (
                    <label
                      key={o.key}
                      className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border p-3.5 transition"
                      style={{
                        borderColor: checked ? "var(--obsidian-accent-secondary, #06b6d4)" : "var(--border-primary)",
                        backgroundColor: checked ? "rgba(6,182,212,0.08)" : "var(--bg-primary)",
                      }}
                    >
                      <div>
                        <p className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>{o.label}</p>
                        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{o.hint}</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleScope(o.key)}
                        className="h-4 w-4 rounded accent-cyan-400"
                      />
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {createAnalysis.isError && (
            <p className="mt-4 text-xs font-semibold text-rose-400">
              {(createAnalysis.error as Error)?.message ?? "Event analysis computation failed."}
            </p>
          )}
        </div>

        {/* Footer Navigation */}
        <div
          className="flex items-center justify-between border-t px-6 py-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
            ⚡ Instant event-transit matrix synthesized against natal D1/D9.
          </span>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={step === 1 ? onClose : () => setStep((s) => s - 1)}
              className="obsidian-btn-secondary text-xs px-4 py-2"
              disabled={createAnalysis.isPending}
            >
              {step === 1 ? "Cancel" : "← Back"}
            </button>

            {step < 3 ? (
              <button
                type="button"
                onClick={() => setStep((s) => s + 1)}
                disabled={step === 1 ? !canContinueToEvent : !canContinueToScope}
                className="obsidian-btn-primary text-xs px-5 py-2 font-bold cursor-pointer disabled:opacity-50"
                style={{ backgroundColor: "var(--obsidian-accent-secondary, #06b6d4)", color: "#000" }}
              >
                Continue →
              </button>
            ) : (
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={!canAnalyze}
                className="obsidian-btn-primary text-xs px-6 py-2.5 font-bold cursor-pointer disabled:opacity-50"
                style={{ backgroundColor: "var(--obsidian-accent-secondary, #06b6d4)", color: "#000" }}
              >
                {createAnalysis.isPending ? (
                  <>
                    <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-t-transparent border-black" />
                    <span>Analyzing Event Moment…</span>
                  </>
                ) : (
                  "Calculate Event Analysis →"
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // Timezone resolution hint helper
  function renderTzHint() {
    if (tzQuery.isLoading) {
      return <p className="mt-1 text-xs text-cyan-400">Resolving event timezone…</p>;
    }
    if (tzQuery.isError) {
      return <p className="mt-1 text-xs text-rose-400">Could not resolve timezone for this location.</p>;
    }
    if (tzQuery.data) {
      return (
        <p className="mt-1 text-xs text-emerald-400 font-mono">
          {tzQuery.data.iana_name} · {formatOffset(tzQuery.data.utc_offset_minutes)}
          {tzQuery.data.is_dst ? " · DST Active" : ""}
        </p>
      );
    }
    return null;
  }
}