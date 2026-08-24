"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, ResizablePanels, Select, type SelectOption } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import { formatEventTitle } from "@/lib/astro";
import { useEventTypeTree, type EventTypeNode } from "@/lib/research";
import type { ConfidenceBucket, PatternListItem, PatternSummary, ResearchEventType } from "@/lib/types";

// The backend's pattern list filter (`GET /cases/patterns?event_type=`)
// validates against the closed 22-value EventType enum — it 422s on
// anything else. The dropdown below also lists open Event Tree leaf names
// (e.g. "Royal family", "Love marriage") for visibility into real event
// data, but those are NOT valid filter values; VALID_FILTER_EVENT_TYPES
// gates which selections actually get sent to that endpoint.
const VALID_FILTER_EVENT_TYPES = new Set<string>([
  "Marriage", "Divorce", "Promotion", "Job Change", "Accident",
  "Surgery", "Hospitalization", "Child Birth", "Death of Parent",
  "Death of Spouse", "Foreign Travel", "Education", "Property",
  "Vehicle", "Finance", "Business", "Political", "Spiritual",
  "Awards", "Litigation", "Health", "Other",
]);

function extractLeafEventNames(nodes: EventTypeNode[]): string[] {
  const result: string[] = [];
  const traverse = (n: EventTypeNode) => {
    if (!n.children || n.children.length === 0) {
      if (n.name && n.name.toLowerCase() !== "other") {
        result.push(formatEventTitle(n.name));
      }
    } else {
      for (const child of n.children) {
        traverse(child);
      }
    }
  };
  for (const n of nodes) traverse(n);
  return Array.from(new Set(result));
}

const BASE_EVENT_TYPES: string[] = [
  "Marriage",
  "Begin significant relationship",
  "Death by Homicide",
  "Death of Mother",
  "Death of Father",
  "Death of Spouse",
  "Change in family responsibilities",
  "Gain social status",
  "Great Publicity",
  "Change of Lifestyle",
  "Royal family",
  "Career Promotion",
  "Job Change",
  "Business Success",
  "Property Purchase",
  "Education Success",
  "Relocation",
  "Surgery",
  "Hospitalization",
  "Childbirth",
  "Litigation",
  "Accident",
];

// Indicator Badges
function LiveDataBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-extrabold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
      🟢 LIVE ENGINE DATA
    </span>
  );
}

function DemoDataBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-extrabold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30">
      ⚠️ DEMO REFERENCE DATA
    </span>
  );
}

// Compact Event Category Select with Max 5 Visible Items (No Screen Blocking)
function Compact5ItemEventSelect({
  options,
  value,
  onChange,
}: {
  options: string[];
  value: string;
  onChange: (val: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredOptions = options.filter((o) =>
    o.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div ref={ref} className="relative min-w-[230px]">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="w-full flex items-center justify-between gap-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 font-bold outline-none cursor-pointer hover:border-cyan-500 transition shadow-sm"
      >
        <span className="truncate">{value || "Select Event Category..."}</span>
        <span className="text-[10px] text-slate-400">▼</span>
      </button>

      {open && (
        <div className="absolute top-[calc(100%+4px)] left-0 z-50 w-full min-w-[260px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl p-2 space-y-1.5 font-mono">
          {/* Search bar inside dropdown */}
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="🔍 Search events..."
            className="w-full rounded-lg px-2.5 py-1 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500"
            autoFocus
          />

          {/* EXACTLY MAX 5 ITEMS VISIBLE AT ONCE (~150px HEIGHT) WITH SMOOTH SCROLL */}
          <div className="max-h-[150px] overflow-y-auto custom-scrollbar space-y-0.5 pr-0.5">
            {filteredOptions.length === 0 ? (
              <p className="p-2 text-[11px] text-slate-400 text-center">No matching events found</p>
            ) : (
              filteredOptions.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => {
                    onChange(opt);
                    setOpen(false);
                    setSearch("");
                  }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center justify-between cursor-pointer ${
                    opt === value
                      ? "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <span className="truncate">{opt}</span>
                  {opt === value && <span className="text-cyan-500 font-bold shrink-0 ml-1">✓</span>}
                </button>
              ))
            )}
          </div>
          <div className="pt-1 border-t border-slate-100 dark:border-slate-800 text-[10px] text-slate-400 text-center font-bold">
            showing max 5 visible · scroll for more
          </div>
        </div>
      )}
    </div>
  );
}

export default function PatternDiscoveryPage() {
  // Event Taxonomy Tree
  const { data: treeData } = useEventTypeTree();

  // Database imported cases real events
  const [databaseEvents, setDatabaseEvents] = useState<string[]>([]);

  useEffect(() => {
    researchCasesApi
      .list()
      .then((res) => {
        if (res.cases) {
          const caseEvents: string[] = [];
          for (const c of res.cases) {
            if (c.total_events && c.research_case_id) {
              // Fetch detail or extract summary events
            }
          }
        }
      })
      .catch(() => {});
  }, []);

  const allAvailableEvents = useMemo(() => {
    const combined = new Set<string>();

    // 1. Add taxonomy tree events
    if (treeData?.event_types) {
      for (const ev of extractLeafEventNames(treeData.event_types)) {
        const clean = formatEventTitle(ev);
        if (clean && clean.toLowerCase() !== "other") combined.add(clean);
      }
    }

    // 2. Add baseline standard events
    for (const ev of BASE_EVENT_TYPES) {
      const clean = formatEventTitle(ev);
      if (clean && clean.toLowerCase() !== "other") combined.add(clean);
    }

    return Array.from(combined).sort();
  }, [treeData]);

  // Filters state
  const [eventType, setEventType] = useState("Marriage");
  const [minConfidence, setMinConfidence] = useState("Any");
  const [minSupport, setMinSupport] = useState("Any");
  const [chartType, setChartType] = useState("All Charts");
  const [factorTab, setFactorTab] = useState<"planets" | "houses" | "yogas" | "dashas">("planets");

  // Real API state
  const [summary, setSummary] = useState<PatternSummary | null>(null);
  const [patternsList, setPatternsList] = useState<PatternListItem[]>([]);
  const [confidenceBuckets, setConfidenceBuckets] = useState<ConfidenceBucket[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRealData, setIsRealData] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);

  const loadPatternsData = async () => {
    setLoading(true);
    try {
      const [sumData, listData, confData] = await Promise.all([
        researchCasesApi.getPatternSummary().catch(() => null),
        // event_type (not category!) is the correct filter param — the
        // backend's `category` param means dimension-category (planet /
        // house / yoga / dasha), a completely different filter. Sending
        // eventType as `category` silently matched zero rows every time.
        // Only send it when it's one of the closed EventType enum values —
        // the dropdown also lists open Event Tree leaf names for
        // visibility, and sending those 422s (silently caught below,
        // which is why this filter used to just show "Sample Dataset"
        // with no error for most selections).
        researchCasesApi
          .listPatterns(VALID_FILTER_EVENT_TYPES.has(eventType) ? { event_type: eventType } : {})
          .catch(() => null),
        researchCasesApi.getConfidenceDistribution().catch(() => null),
      ]);
      let realDataFound = false;
      if (sumData && sumData.patterns_found > 0) {
        setSummary(sumData);
        realDataFound = true;
      } else {
        setSummary(null);
      }
      if (listData && listData.patterns && listData.patterns.length > 0) {
        setPatternsList(listData.patterns);
        realDataFound = true;
      } else {
        setPatternsList([]);
      }
      if (confData && confData.buckets) {
        setConfidenceBuckets(confData.buckets);
      } else {
        setConfidenceBuckets([]);
      }
      setIsRealData(realDataFound);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatternsData();
  }, [eventType]);

  const handleDiscoverRealPatterns = async () => {
    setIsDiscovering(true);
    try {
      await researchCasesApi.discoverPatterns({});
      await loadPatternsData();
    } catch (err) {
      console.error("Pattern discovery error", err);
    } finally {
      setIsDiscovering(false);
    }
  };

  // Derived from the real patternsList (backend has no standalone
  // "strongest pattern" / "avg confidence" summary field) — top pattern is
  // the highest confidence_score entry; avg confidence is the mean over
  // whatever patterns are currently loaded for the selected event category.
  const topPattern = useMemo(() => {
    if (patternsList.length === 0) return null;
    return patternsList.reduce((best, p) => (p.confidence_score > best.confidence_score ? p : best), patternsList[0]);
  }, [patternsList]);
  const avgConfidence = useMemo(() => {
    if (patternsList.length === 0) return null;
    return patternsList.reduce((sum, p) => sum + p.confidence_score, 0) / patternsList.length;
  }, [patternsList]);

  // Fallback Reference Factors
  const factorsData = {
    planets: [
      { name: "Jupiter (Guru)", symbol: "♃", pct: 78, count: "10,032", color: "bg-amber-400" },
      { name: "Venus (Shukra)", symbol: "♀", pct: 74, count: "9,501", color: "bg-amber-400" },
      { name: "Moon (Chandra)", symbol: "☽", pct: 48, count: "6,167", color: "bg-emerald-400" },
      { name: "Saturn (Shani)", symbol: "♄", pct: 41, count: "5,257", color: "bg-emerald-400" },
      { name: "Sun (Surya)", symbol: "☉", pct: 34, count: "4,415", color: "bg-cyan-400" },
      { name: "Mars (Mangala)", symbol: "♂", pct: 27, count: "3,462", color: "bg-cyan-400" },
    ],
    houses: [
      { name: "7th House (Kalatra)", symbol: "H7", pct: 84, count: "10,787", color: "bg-amber-400" },
      { name: "1st House (Lagna)", symbol: "H1", pct: 62, count: "7,962", color: "bg-emerald-400" },
      { name: "5th House (Putra)", symbol: "H5", pct: 55, count: "7,063", color: "bg-emerald-400" },
      { name: "9th House (Dharma)", symbol: "H9", pct: 49, count: "6,292", color: "bg-cyan-400" },
      { name: "10th House (Karma)", symbol: "H10", pct: 38, count: "4,880", color: "bg-cyan-400" },
    ],
    yogas: [
      { name: "Gaja Kesari Yoga", symbol: "Y1", pct: 68, count: "8,732", color: "bg-amber-400" },
      { name: "Dhana Yoga", symbol: "Y2", pct: 59, count: "7,576", color: "bg-emerald-400" },
      { name: "Raja Yoga Sambandha", symbol: "Y3", pct: 45, count: "5,778", color: "bg-cyan-400" },
    ],
    dashas: [
      { name: "Venus Mahadasha", symbol: "D1", pct: 81, count: "10,402", color: "bg-amber-400" },
      { name: "Jupiter Antardasha", symbol: "D2", pct: 72, count: "9,246", color: "bg-amber-400" },
      { name: "Moon Antardasha", symbol: "D3", pct: 51, count: "6,549", color: "bg-emerald-400" },
    ],
  };

  // Fallback Top Patterns Table Data
  const fallbackPatterns = [
    { rank: 1, pattern: "Jupiter + Venus + D9 7th House Activation", badge: "D9 7th House", support: "4,550 / 5,248", conf: "87%", confLabel: "Very High", lift: "3.42", liftLabel: "Very High" },
    { rank: 2, pattern: "Venus in Kendra + Jupiter Aspect", badge: "D1 Aspect", support: "3,842 / 5,248", conf: "73%", confLabel: "High", lift: "2.81", liftLabel: "High" },
    { rank: 3, pattern: "7th Lord Strong + Jupiter Dasha", badge: "D1 Dasha", support: "3,105 / 5,248", conf: "59%", confLabel: "High", lift: "2.32", liftLabel: "High" },
    { rank: 4, pattern: "Venus + Moon Conjunction", badge: "D1 Conjunction", support: "2,798 / 5,248", conf: "53%", confLabel: "Medium", lift: "1.95", liftLabel: "Medium" },
    { rank: 5, pattern: "Jupiter Transit in 7th from Lagna", badge: "Transit 7th", support: "2,642 / 5,248", conf: "50%", confLabel: "Medium", lift: "1.88", liftLabel: "Medium" },
    { rank: 6, pattern: "D9 Lagna Lord Exalted + Venus", badge: "D9 Strength", support: "2,213 / 5,248", conf: "42%", confLabel: "Medium", lift: "1.63", liftLabel: "Medium" },
    { rank: 7, pattern: "Shukra Dasha + 7th House Activated", badge: "Dasha 7th", support: "1,987 / 5,248", conf: "38%", confLabel: "Low", lift: "1.41", liftLabel: "Low" },
  ];

  return (
    <AppShell sectionColor="--section-research">
      <div className="space-y-4 pb-8">
        {/* ── Top Header ── */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">✨</span>
              <h1 className="text-xl font-extrabold text-slate-900 dark:text-slate-100">
                Pattern Discovery Studio
              </h1>
              {isRealData ? <LiveDataBadge /> : <DemoDataBadge />}
            </div>
            <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400 font-mono">
              Discover statistically verified astrological patterns and correlate planetary positions across life events.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleDiscoverRealPatterns}
              disabled={isDiscovering}
              className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 text-xs font-bold font-mono transition cursor-pointer flex items-center gap-1.5"
            >
              <span>{isDiscovering ? "⏳ Mining Engine..." : "⚡ Run Real Discovery"}</span>
            </button>
            <Button href="/research/cases" variant="secondary" size="sm">
              🧪 Case Databank
            </Button>
            <Button href="/research/projects" variant="primary" size="sm">
              📁 Research Projects
            </Button>
          </div>
        </div>

        {/* ── Top KPI Stat Cards ── */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 flex items-center gap-3 shadow-sm">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-violet-500/10 text-violet-600 dark:text-violet-400 font-bold text-lg">
              🗄️
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono">Total Events</p>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-slate-100">
                {summary ? summary.total_events.toLocaleString() : "—"}
              </h3>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">Across verified cases</p>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 flex items-center gap-3 shadow-sm">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-bold text-lg">
              🌐
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono">Discovered Patterns</p>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-slate-100">
                {summary ? summary.patterns_found.toLocaleString() : "—"}
              </h3>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">Significant rules</p>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 flex items-center gap-3 shadow-sm">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold text-lg">
              🛡️
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono">High Confidence</p>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-slate-100">
                {summary ? summary.high_confidence_patterns.toLocaleString() : "—"}
              </h3>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">Confidence ≥ 75%</p>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 flex items-center gap-3 shadow-sm">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 font-bold text-lg">
              ⭐
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono">Top Pattern Score</p>
              <h3 className="text-lg font-extrabold text-amber-600 dark:text-amber-400">
                {topPattern ? `${(topPattern.confidence_score * 100).toFixed(0)}%` : "—"}
              </h3>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono truncate max-w-[130px]">
                {topPattern?.description ?? "No patterns loaded"}
              </p>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 flex items-center gap-3 shadow-sm">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-bold text-lg">
              📊
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono">Avg Confidence</p>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-slate-100">
                {avgConfidence !== null ? `${(avgConfidence * 100).toFixed(1)}%` : "—"}
              </h3>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">Mean over loaded patterns</p>
            </div>
          </div>
        </div>

        {/* ── Filter Bar ── */}
        <div className="p-3 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center gap-3 text-xs font-mono shadow-sm">
          <div className="flex flex-col gap-0.5 min-w-[220px]">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-600 dark:text-slate-400 font-bold shrink-0">Event Category:</span>
              <Compact5ItemEventSelect
                options={allAvailableEvents}
                value={eventType}
                onChange={setEventType}
              />
            </div>
            {!VALID_FILTER_EVENT_TYPES.has(eventType) && (
              <span className="text-[10px] text-amber-600 dark:text-amber-400">
                Not one of the filterable event types — showing all patterns instead.
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-600 dark:text-slate-400 font-bold">Min Confidence:</span>
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded px-2.5 py-1 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="Any">Any</option>
              <option value="50%">50%+</option>
              <option value="75%">75%+</option>
              <option value="90%">90%+</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-600 dark:text-slate-400 font-bold">Chart Scope:</span>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              className="bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded px-2.5 py-1 text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="All Charts">All Charts</option>
              <option value="D1 Natal">D1 Natal</option>
              <option value="D9 Navamsha">D9 Navamsha</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => {
              setEventType("Marriage");
              setMinConfidence("Any");
              setChartType("All Charts");
            }}
            className="ml-auto text-xs text-cyan-600 dark:text-cyan-400 font-bold hover:underline cursor-pointer flex items-center gap-1"
          >
            ↻ Reset Filters
          </button>
        </div>

        {/* ── IDE Multi-Pane Resizable Workspace ── */}
        <ResizablePanels defaultSizes={[0.26, 0.44, 0.30]} className="min-h-[640px]">
          {/* BLOCK 1: Top Contributing Factors (Left) */}
          <div className="flex flex-col gap-3 pr-2 h-full">
            <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm h-full">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 font-mono">
                  Contributing Factors
                </h3>
                <DemoDataBadge />
              </div>
              <p className="text-[10px] text-slate-400 dark:text-slate-500 -mt-2">
                Illustrative reference values for {eventType} — not computed from imported cases yet.
              </p>

              {/* Sub-tabs */}
              <div className="flex items-center gap-2 pb-1.5 border-b border-slate-200 dark:border-slate-800 text-[11px] font-mono">
                {(["planets", "houses", "yogas", "dashas"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setFactorTab(tab)}
                    className={`capitalize transition cursor-pointer ${
                      factorTab === tab
                        ? "text-cyan-600 dark:text-cyan-400 font-bold underline underline-offset-4"
                        : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-300"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Factors Progress Bars */}
              <div className="space-y-2 text-xs">
                {factorsData[factorTab].map((f) => (
                  <div key={f.name} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                        <span className="text-slate-500">{f.symbol}</span> {f.name}
                      </span>
                      <span className="font-mono text-slate-500 dark:text-slate-400">{f.pct}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-slate-950 overflow-hidden">
                      <div className={`h-full ${f.color}`} style={{ width: `${f.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Event Type Category Distribution */}
              <div className="pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-[11px] font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider font-mono">
                    Event Share
                  </h4>
                  <span className="text-[9px] text-slate-400">demo reference</span>
                </div>
                <div className="space-y-1.5 text-[11px] font-mono">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                      <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" /> Marriage
                    </span>
                    <span className="text-slate-500 dark:text-slate-400">40.9%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Career Promotion
                    </span>
                    <span className="text-slate-500 dark:text-slate-400">24.1%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Business Success
                    </span>
                    <span className="text-slate-500 dark:text-slate-400">15.5%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* BLOCK 2: Discovered Patterns Table (Middle) */}
          <div className="px-2 h-full flex flex-col space-y-3">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm flex-1 overflow-y-auto custom-scrollbar">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 font-mono">
                  Discovered Astrological Patterns ({VALID_FILTER_EVENT_TYPES.has(eventType) ? eventType : "All"})
                </h3>
                <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono font-bold">
                  {patternsList.length > 0 ? `${patternsList.length} Real Patterns` : "Sample Dataset"}
                </span>
              </div>

              {loading ? (
                <div className="p-8 text-center text-xs text-slate-400 font-mono">
                  Evaluating statistical pattern matrix…
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 uppercase tracking-wider bg-slate-50 dark:bg-slate-800/40">
                        <th className="py-2 px-2">Rank</th>
                        <th className="py-2 px-2">Astrological Pattern</th>
                        <th className="py-2 px-2">Support</th>
                        <th className="py-2 px-2">Confidence</th>
                        <th className="py-2 px-2">Lift</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {patternsList.length > 0
                        ? patternsList.map((p, idx) => (
                            <tr key={p.pattern_id || idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                              <td className="py-2.5 px-2 font-bold text-slate-600 dark:text-slate-400">
                                #{idx + 1}
                              </td>
                              <td className="py-2.5 px-2">
                                <p className="font-bold text-slate-900 dark:text-slate-100">{p.description}</p>
                                <span className="inline-block mt-0.5 px-1.5 py-0.2 rounded text-[9px] bg-slate-100 dark:bg-slate-950 text-cyan-600 dark:text-cyan-400 border border-slate-200 dark:border-slate-800 font-bold">
                                  {formatEventTitle(p.event_type)}
                                </span>
                              </td>
                              <td className="py-2.5 px-2 text-slate-600 dark:text-slate-400">
                                {p.sample_size} cases
                              </td>
                              <td className="py-2.5 px-2 font-bold text-emerald-600 dark:text-emerald-400">
                                {(p.confidence_score * 100).toFixed(0)}%
                              </td>
                              <td className="py-2.5 px-2 font-bold text-slate-900 dark:text-slate-100">
                                {p.lift_score.toFixed(2)}x
                              </td>
                            </tr>
                          ))
                        : fallbackPatterns.map((p) => (
                            <tr key={p.rank} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                              <td className="py-2.5 px-2 font-bold text-slate-600 dark:text-slate-400">
                                #{p.rank}
                              </td>
                              <td className="py-2.5 px-2">
                                <p className="font-bold text-slate-900 dark:text-slate-100">{p.pattern}</p>
                                <span className="inline-block mt-0.5 px-1.5 py-0.2 rounded text-[9px] bg-slate-100 dark:bg-slate-950 text-cyan-600 dark:text-cyan-400 border border-slate-200 dark:border-slate-800 font-bold">
                                  {p.badge}
                                </span>
                              </td>
                              <td className="py-2.5 px-2 text-slate-600 dark:text-slate-400">{p.support}</td>
                              <td className="py-2.5 px-2 font-bold text-emerald-600 dark:text-emerald-400">
                                {p.conf}
                              </td>
                              <td className="py-2.5 px-2 font-bold text-slate-900 dark:text-slate-100">
                                {p.lift}x
                              </td>
                            </tr>
                          ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* BLOCK 3: Statistical Metrics & Distribution (Right) */}
          <div className="pl-2 h-full flex flex-col space-y-3">
            {/* Confidence Histogram */}
            <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 font-mono">
                Confidence Distribution
              </h3>

              {confidenceBuckets.length > 0 ? (
                <div className="h-28 flex items-end justify-between gap-2 pt-4 px-2 border-b border-slate-200 dark:border-slate-800 text-[10px] font-mono">
                  {(() => {
                    const maxCount = Math.max(...confidenceBuckets.map((b) => b.count), 1);
                    const barColors: Record<string, string> = {
                      "0-20": "bg-slate-300 dark:bg-slate-700",
                      "20-40": "bg-amber-400",
                      "40-60": "bg-amber-500",
                      "60-80": "bg-emerald-500",
                      "80-100": "bg-cyan-500",
                    };
                    return confidenceBuckets.map((b) => (
                      <div key={b.bucket} className="flex flex-col items-center flex-1">
                        <span className="text-[9px] text-slate-500">{b.count}</span>
                        <div
                          className={`w-full rounded-t ${barColors[b.bucket] ?? "bg-cyan-500"}`}
                          style={{ height: `${Math.max(4, (b.count / maxCount) * 88)}px` }}
                        />
                        <span className="text-[9px] text-slate-400 mt-1">{b.bucket}%</span>
                      </div>
                    ));
                  })()}
                </div>
              ) : (
                <p className="text-[11px] text-slate-400 py-4 text-center">No persisted patterns yet — nothing to distribute.</p>
              )}
            </div>

            {/* Pattern Strength (Lift) Breakdown */}
            <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm flex-1">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 font-mono">
                  Pattern Strength (Lift Score)
                </h3>
                <span className="text-[9px] text-slate-400">demo reference</span>
              </div>

              <div className="space-y-2 text-[11px] font-mono">
                <div className="flex items-center justify-between p-2 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                  <span className="flex items-center gap-1.5 text-slate-800 dark:text-slate-200 font-bold">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" /> Very High (≥ 2.0x)
                  </span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-extrabold">28%</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                  <span className="flex items-center gap-1.5 text-slate-800 dark:text-slate-200 font-bold">
                    <span className="w-2 h-2 rounded-full bg-amber-400" /> High (1.5x - 2.0x)
                  </span>
                  <span className="text-amber-600 dark:text-amber-400 font-extrabold">32%</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
                  <span className="flex items-center gap-1.5 text-slate-800 dark:text-slate-200 font-bold">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" /> Medium (1.0x - 1.5x)
                  </span>
                  <span className="text-cyan-600 dark:text-cyan-400 font-extrabold">25%</span>
                </div>
              </div>
            </div>
          </div>
        </ResizablePanels>
      </div>
    </AppShell>
  );
}
