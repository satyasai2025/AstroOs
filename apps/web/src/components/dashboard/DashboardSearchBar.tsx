"use client";

/**
 * AstroOS — Dashboard Search Bar
 *
 * Honest scope note (see ASTROOS_VISION_V3_ROADMAP.md, Phase 9):
 * The vision mockup's header reads "Search Person | DOB | TOB | POB |
 * Compare Charts | AI Search". This component implements the real subset
 * of that today:
 *   - Keyword search over the signed-in user's already-loaded saved
 *     charts (`useMyCharts()` → GET /api/v1/horoscope/my-charts),
 *     filtered client-side by subject name. No new backend endpoint,
 *     no semantic/AI search — the input is labeled plainly as what it
 *     does, not "AI Search".
 *   - A "Compare Charts" link to the existing `/charts/compare` page.
 *
 * Explicitly out of scope here (see report to caller for detail):
 *   - DOB / TOB / POB as standalone search fields — those are birth-data
 *     inputs that belong to chart *creation* (BirthDetailsForm), not a
 *     distinct search feature over saved data in this app's current
 *     architecture.
 *   - "AI Search" — there is no NLP/semantic backend for this yet;
 *     faking it would violate the no-fabrication constraint.
 *   - Clicking a result does not "load" that chart's full analysis —
 *     there is no GET-by-chart_id endpoint that returns a full D1 +
 *     vargas + dasha payload yet (only the create endpoint and the
 *     list/summary endpoint exist). Clicking a result therefore
 *     navigates to /charts/history, where the full saved-charts list
 *     (including that match) is genuinely visible, rather than silently
 *     failing or pretending to load chart detail.
 */

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMyCharts } from "@/lib/charts";

export interface DashboardSearchBarProps {
  /** Optional extra className applied to the outer wrapper. */
  className?: string;
}

export function DashboardSearchBar({ className }: DashboardSearchBarProps) {
  const router = useRouter();
  const { data, isLoading } = useMyCharts();
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const matches = useMemo(() => {
    const charts = data?.charts ?? [];
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return [];
    return charts
      .filter((c) => c.subject_name.toLowerCase().includes(trimmed))
      .slice(0, 8);
  }, [data, query]);

  function goToHistory() {
    setIsOpen(false);
    router.push("/charts/history");
  }

  function handleBlur() {
    // Delay so a click on a dropdown item registers before we close it.
    window.setTimeout(() => setIsOpen(false), 150);
  }

  return (
    <div
      ref={containerRef}
      className={`relative flex flex-col gap-2 sm:flex-row sm:items-center ${className ?? ""}`}
    >
      <div className="relative flex-1">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={handleBlur}
          placeholder="Search your saved charts by name…"
          aria-label="Search your saved charts by name"
          className="field-input w-full"
          role="combobox"
          aria-expanded={isOpen}
          aria-controls="dashboard-search-results"
          autoComplete="off"
        />

        {isOpen && query.trim().length > 0 && (
          <div
            id="dashboard-search-results"
            role="listbox"
            className="glass-card absolute left-0 right-0 top-full z-20 mt-1 max-h-72 overflow-y-auto p-1"
          >
            {isLoading && (
              <p
                className="px-3 py-2 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                Loading your saved charts…
              </p>
            )}

            {!isLoading && matches.length === 0 && (
              <p
                className="px-3 py-2 text-xs"
                style={{ color: "var(--text-muted)" }}
              >
                No saved charts match &quot;{query.trim()}&quot;.
              </p>
            )}

            {!isLoading &&
              matches.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  role="option"
                  aria-selected="false"
                  onClick={goToHistory}
                  className="flex w-full flex-col items-start gap-0.5 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-white/5"
                  style={{ color: "var(--text-primary)" }}
                >
                  <span className="font-medium">{c.subject_name}</span>
                  <span
                    className="text-xs"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {c.place_name ?? "Unknown place"}
                    {c.lagna_rashi ? ` · ${c.lagna_rashi} lagna` : ""}
                  </span>
                </button>
              ))}

            {!isLoading && matches.length > 0 && (
              <button
                type="button"
                onClick={goToHistory}
                className="mt-1 w-full rounded-md px-3 py-2 text-left text-xs font-medium"
                style={{ color: "var(--accent)" }}
              >
                View all saved charts →
              </button>
            )}
          </div>
        )}
      </div>

      <Link
        href="/charts/compare"
        className="btn-ghost whitespace-nowrap px-3 py-2 text-sm"
      >
        Compare Charts
      </Link>
    </div>
  );
}
