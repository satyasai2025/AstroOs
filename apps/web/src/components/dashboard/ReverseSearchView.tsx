"use client";

import { useState } from "react";
import type { YogaResultResponse } from "@/lib/types";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface PatternCriteria {
  selectedYogas: string[]; // yoga_id values
  requiredPlanets: string[]; // e.g. ["Jupiter", "Saturn"]
  requiredHouse: number | null; // e.g. 10 for 10th house
  requiredAspect: { from: string; to: string; type: string } | null;
}

interface ChartMatch {
  chartId: string;
  subjectName: string;
  score: number; // 0-100
  matchedYogas: YogaResultResponse[];
  summary: string;
}

interface ReverseSearchViewProps {
  /** Pre-populated chart data to search within (optional) — reserved for future use */
  chartData?: {
    id: string;
    name: string;
    yogaResults: YogaResultResponse[];
  };
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const YOGA_CATEGORIES = [
  { id: "raja", label: "Raja Yogas" },
  { id: "dhana", label: "Dhana Yogas" },
  { id: "panch_mahapurusha", label: "Panch Mahapurusha" },
  { id: "sanyasa", label: "Sanyasa Yogas" },
  { id: "solar", label: "Solar Yogas" },
  { id: "gajakesari", label: "Gajakesari Group" },
  { id: "kendradi", label: "Kendradi Yogas" },
  { id: "special", label: "Special Combinations" },
];

const ASPECT_TYPES = ["conjunction", "trine", "square", "opposition", "sextile"];

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function ReverseSearchView({ chartData }: ReverseSearchViewProps) {
  const [criteria, setCriteria] = useState<PatternCriteria>({
    selectedYogas: [],
    requiredPlanets: [],
    requiredHouse: null,
    requiredAspect: null,
  });
  const [searchResults, setSearchResults] = useState<ChartMatch[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [yogaCatalog] = useState<YogaCatalogResponse | null>(
    null,
  );

  const handleSearch = () => {
    setIsSearching(true);
    // Simulate search — later connect to API
    setTimeout(() => {
      const mockResults: ChartMatch[] = [
        {
          chartId: "chart-123",
          subjectName: "Sample Natal Chart A",
          score: 87,
          matchedYogas: [],
          summary: "3 targeted yogas present",
        },
        {
          chartId: "chart-456",
          subjectName: "Historical Figure B",
          score: 72,
          matchedYogas: [],
          summary: "2 targeted yogas present",
        },
      ];
      setSearchResults(mockResults);
      setIsSearching(false);
    }, 600);
  };

  const toggleYoga = (yogaId: string) => {
    setCriteria((prev) => ({
      ...prev,
      selectedYogas: prev.selectedYogas.includes(yogaId)
        ? prev.selectedYogas.filter((id) => id !== yogaId)
        : [...prev.selectedYogas, yogaId],
    }));
  };

  return (
    <div className="flex h-full flex-col">
      {/* ── Header ── */}
      <div className="border-b px-4 py-3" style={{ borderColor: "var(--obsidian-border)" }}>
        <h1
          className="text-base font-bold"
          style={{ color: "var(--obsidian-text-primary)" }}
        >
          Reverse Pattern Search
        </h1>
        <p
          className="mt-0.5 text-xs"
          style={{ color: "var(--obsidian-text-muted)" }}
        >
          Find charts matching specific planetary combinations, yogas, or aspects
        </p>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left: Filter Panel ── */}
        <div
          className="w-80 overflow-y-auto border-r px-4 py-4"
          style={{ borderColor: "var(--obsidian-border)" }}
        >
          <FilterSection title="Select Yogas">
            <div className="space-y-1">
              {YOGA_CATEGORIES.map((cat) => (
                <div key={cat.id} className="mb-3">
                  <h4
                    className="mb-1.5 text-xs font-semibold uppercase tracking-wide"
                    style={{ color: "var(--obsidian-text-secondary)" }}
                  >
                    {cat.label}
                  </h4>
                  {yogaCatalog && (
                    <div className="space-y-1">
                      {yogaCatalog.modules[cat.id]?.slice(0, 4).map((yoga) => (
                        <label
                          key={yoga.id}
                          className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-xs transition-colors hover:bg-[var(--obsidian-surface-hover)]"
                          style={{ color: "var(--obsidian-text-primary)" }}
                        >
                          <input
                            type="checkbox"
                            checked={criteria.selectedYogas.includes(yoga.id)}
                            onChange={() => toggleYoga(yoga.id)}
                            className="h-3.5 w-3.5 rounded border-gray-600 text-cyan-400 focus:ring-0"
                          />
                          <span className="line-clamp-1">
                            {yoga.name || yoga.id}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </FilterSection>

          <FilterSection title="Required Planets">
            <div className="flex flex-wrap gap-1.5">
              {["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"].map((planet) => (
                <button
                  key={planet}
                  onClick={() => {
                    setCriteria((prev) => ({
                      ...prev,
                      requiredPlanets: prev.requiredPlanets.includes(planet)
                        ? prev.requiredPlanets.filter((p) => p !== planet)
                        : [...prev.requiredPlanets, planet],
                    }));
                  }}
                  className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                    criteria.requiredPlanets.includes(planet)
                      ? "bg-cyan-400 text-[#0B0E14]"
                      : "bg-[var(--obsidian-surface)] text-[var(--obsidian-text-secondary)] hover:bg-[var(--obsidian-surface-hover)]"
                  }`}
                >
                  {planet}
                </button>
              ))}
            </div>
          </FilterSection>

          <FilterSection title="House Emphasis">
            <div className="grid grid-cols-3 gap-1.5">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((house) => (
                <button
                  key={house}
                  onClick={() =>
                    setCriteria((prev) => ({
                      ...prev,
                      requiredHouse: prev.requiredHouse === house ? null : house,
                    }))
                  }
                  className={`rounded-md px-2 py-1.5 text-xs font-medium transition-colors ${
                    criteria.requiredHouse === house
                      ? "bg-cyan-400 text-[#0B0E14]"
                      : "bg-[var(--obsidian-surface)] text-[var(--obsidian-text-secondary)] hover:bg-[var(--obsidian-surface-hover)]"
                  }`}
                >
                  {house}
                </button>
              ))}
            </div>
          </FilterSection>

          <FilterSection title="Aspect Condition">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <select
                  value={criteria.requiredAspect?.from || ""}
                  onChange={(e) =>
                    setCriteria((prev) => ({
                      ...prev,
                      requiredAspect: prev.requiredAspect
                        ? { ...prev.requiredAspect, from: e.target.value }
                        : { from: e.target.value, to: "", type: "conjunction" },
                    }))
                  }
                  className="flex-1 rounded border bg-[var(--bg-card)] px-2 py-1 text-xs"
                  style={{ borderColor: "var(--obsidian-border)", color: "var(--obsidian-text-primary)" }}
                >
                  <option value="">From</option>
                  {["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"].map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
                <span style={{ color: "var(--obsidian-text-muted)" }}>→</span>
                <select
                  value={criteria.requiredAspect?.to || ""}
                  onChange={(e) =>
                    setCriteria((prev) => ({
                      ...prev,
                      requiredAspect: prev.requiredAspect
                        ? { ...prev.requiredAspect, to: e.target.value }
                        : { from: "", to: e.target.value, type: "conjunction" },
                    }))
                  }
                  className="flex-1 rounded border bg-[var(--bg-card)] px-2 py-1 text-xs"
                  style={{ borderColor: "var(--obsidian-border)", color: "var(--obsidian-text-primary)" }}
                >
                  <option value="">To</option>
                  {["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"].map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
              <select
                value={criteria.requiredAspect?.type || "conjunction"}
                onChange={(e) =>
                  setCriteria((prev) => ({
                    ...prev,
                    requiredAspect: prev.requiredAspect
                      ? { ...prev.requiredAspect, type: e.target.value }
                      : { from: "", to: "", type: e.target.value },
                  }))
                }
                className="w-full rounded border bg-[var(--bg-card)] px-2 py-1 text-xs"
                style={{ borderColor: "var(--obsidian-border)", color: "var(--obsidian-text-primary)" }}
              >
                {ASPECT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </FilterSection>

          <div className="mt-4">
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="w-full rounded-lg py-2 text-sm font-medium transition-all"
              style={{
                backgroundColor:
                  "var(--obsidian-accent-primary)",
                color: "#0B0E14",
                opacity: isSearching ? 0.6 : 1,
              }}
            >
              {isSearching ? "Searching…" : "Search Patterns"}
            </button>
          </div>
        </div>

        {/* ── Right: Results ── */}
        <div className="flex-1 overflow-y-auto p-4">
          {searchResults.length === 0 && !isSearching ? (
            <div
              className="flex h-full flex-col items-center justify-center text-center text-sm"
              style={{ color: "var(--obsidian-text-muted)" }}
            >
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.2"
                className="mb-3 opacity-30"
              >
                <circle cx="11" cy="11" r="7" />
                <path d="M21 21l-4.35-4.35" />
                <path d="M11 8v6M8 11h6" />
              </svg>
              <p className="max-w-xs">
                Select criteria on the left and click Search to find matching charts
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div
                className="text-xs font-medium"
                style={{ color: "var(--obsidian-text-secondary)" }}
              >
                {searchResults.length} chart{searchResults.length !== 1 ? "s" : ""} found
              </div>
              {searchResults.map((match) => (
                <div
                  key={match.chartId}
                  className="rounded-lg border p-3 transition-colors hover:bg-[var(--obsidian-surface-hover)]"
                  style={{ borderColor: "var(--obsidian-border)" }}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4
                        className="text-sm font-semibold"
                        style={{ color: "var(--obsidian-text-primary)" }}
                      >
                        {match.subjectName}
                      </h4>
                      <p
                        className="mt-0.5 text-xs"
                        style={{ color: "var(--obsidian-text-muted)" }}
                      >
                        ID: {match.chartId} · {match.summary}
                      </p>
                    </div>
                    <div
                      className="rounded-md px-2 py-1 text-xs font-bold"
                      style={{
                        backgroundColor: "rgba(6, 207, 255, 0.12)",
                        color: "var(--obsidian-accent-primary)",
                      }}
                    >
                      {match.score}%
                    </div>
                  </div>
                  {match.matchedYogas.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {match.matchedYogas.slice(0, 3).map((yoga) => (
                        <span
                          key={yoga.yoga_id}
                          className="rounded px-1.5 py-0.5 text-[10px] font-medium"
                          style={{
                            backgroundColor: "var(--obsidian-surface)",
                            color: "var(--obsidian-text-secondary)",
                            border: "1px solid var(--obsidian-border)",
                          }}
                        >
                          {yoga.yoga_id}
                        </span>
                      ))}
                      {match.matchedYogas.length > 3 && (
                        <span
                          className="px-1.5 py-0.5 text-[10px]"
                          style={{ color: "var(--obsidian-text-muted)" }}
                        >
                          +{match.matchedYogas.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Sub-component: Filter Section                                      */
/* ------------------------------------------------------------------ */

function FilterSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-5">
      <h3
        className="mb-2 text-xs font-semibold uppercase tracking-wide"
        style={{ color: "var(--obsidian-accent-primary)" }}
      >
        {title}
      </h3>
      {children}
    </div>
  );
}
