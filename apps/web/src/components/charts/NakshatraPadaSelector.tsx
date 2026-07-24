"use client";

import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import {
  NAKSHATRAS,
  NAKSHATRA_LORDS,
  RASHIS,
  RASHI_LORDS,
  type NakshatraName,
} from "@/lib/astro";
import { useNakshatraDetail } from "@/lib/nakshatraKnowledge";
import type { PlanetPositionSchema } from "@/lib/types";

interface NakshatraPadaSelectorProps {
  /** Planet positions from the chart to highlight their nakshatras. */
  planets?: PlanetPositionSchema[];
  /** Called when user selects a specific nakshatra-pada combo. */
  onSelect?: (nakshatra: NakshatraName, pada: number) => void;
  /** Currently highlighted nakshatra (e.g. from search). */
  highlightNakshatra?: NakshatraName | null;
}

const PADA_DEGREES = 13.3333 / 4; // each pada is 3°20'

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span style={{ color: "var(--text-muted)" }}>{label}: </span>
      <span className="font-medium" style={{ color: "var(--text-primary)" }}>{value}</span>
    </div>
  );
}

export function NakshatraPadaSelector({
  planets = [],
  onSelect,
  highlightNakshatra,
}: NakshatraPadaSelectorProps) {
  const [search, setSearch] = useState("");
  const [selectedNakshatra, setSelectedNakshatra] = useState<NakshatraName | null>(null);
  const [selectedPada, setSelectedPada] = useState<number | null>(null);
  const [expandedLord, setExpandedLord] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Group nakshatras by their lord (planet)
  const byLord = useMemo(() => {
    const map: Record<string, NakshatraName[]> = {};
    for (const nak of NAKSHATRAS) {
      const lord = NAKSHATRA_LORDS[nak];
      if (!map[lord]) map[lord] = [];
      map[lord].push(nak);
    }
    return map;
  }, []);

  // Find which planets are in which nakshatras
  const planetByNakshatra = useMemo(() => {
    const map: Record<string, { planet: string; pada: number }[]> = {};
    for (const p of planets) {
      const nak = p.nakshatra;
      if (!map[nak]) map[nak] = [];
      map[nak].push({ planet: p.planet, pada: p.pada });
    }
    return map;
  }, [planets]);

  // Filter nakshatras by search query
  const filtered = useMemo(() => {
    if (!search.trim()) return NAKSHATRAS;
    const q = search.toLowerCase();
    return NAKSHATRAS.filter(
      (n) =>
        n.toLowerCase().includes(q) ||
        NAKSHATRA_LORDS[n].toLowerCase().includes(q),
    );
  }, [search]);

  const handleSelect = useCallback(
    (nakshatra: NakshatraName, pada: number) => {
      setSelectedNakshatra(nakshatra);
      setSelectedPada(pada);
      onSelect?.(nakshatra, pada);
    },
    [onSelect],
  );

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!listRef.current) return;
      const items = listRef.current.querySelectorAll<HTMLElement>("[data-nakshatra-item]");
      const currentIndex = Array.from(items).findIndex(
        (el) => el === document.activeElement,
      );

      if (e.key === "ArrowDown") {
        e.preventDefault();
        const next = items[currentIndex + 1] ?? items[0];
        next?.focus();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const prev = items[currentIndex - 1] ?? items[items.length - 1];
        prev?.focus();
      }
    };
    listRef.current?.addEventListener("keydown", handleKeyDown);
    return () => listRef.current?.removeEventListener("keydown", handleKeyDown);
  }, []);

  const activeNakshatra = highlightNakshatra ?? selectedNakshatra;

  // Level 2 — real classical knowledge base, fetched from the backend's
  // nakshatra catalogue (the 27 YAML files under knowledge/catalogues/
  // nakshatras) once a nakshatra is selected. See lib/nakshatraKnowledge.ts.
  const { data: nakDetail, isLoading: nakLoading } = useNakshatraDetail(selectedNakshatra);

  return (
    <div
      className="glass-card p-5 space-y-4"
      role="region"
      aria-label="Nakshatra and Pada lookup selector"
    >
      <h3
        className="text-sm font-semibold uppercase tracking-wide"
        style={{ color: "var(--accent)" }}
      >
        Nakshatra / Pada Selector
      </h3>

      {/* Context selector: jump straight to any chart planet's actual
          nakshatra + pada, instead of hunting for it in the grid below. */}
      {planets.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Jump to Graha
          </p>
          <div className="flex flex-wrap gap-1.5">
            {planets.map((p) => {
              const isActive = selectedNakshatra === p.nakshatra && selectedPada === p.pada;
              return (
                <button
                  key={p.planet}
                  type="button"
                  onClick={() => handleSelect(p.nakshatra as NakshatraName, p.pada)}
                  className="rounded-full border px-2.5 py-1 text-xs font-medium transition"
                  style={{
                    borderColor: isActive ? "var(--accent)" : "var(--border-primary)",
                    backgroundColor: isActive ? "var(--accent)" : "var(--bg-card)",
                    color: isActive ? "var(--accent-text)" : "var(--text-secondary)",
                  }}
                  title={`${p.planet}: ${p.nakshatra} Pada ${p.pada}`}
                >
                  {p.planet}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Search input */}
      <div className="relative">
        <label htmlFor="nakshatra-search" className="sr-only">
          Search nakshatras or lords
        </label>
        <input
          id="nakshatra-search"
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search nakshatra or lord (e.g. Ashwini, Jupiter)..."
          className="field-input pl-9"
          aria-label="Search nakshatras by name or planetary lord"
        />
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          aria-hidden="true"
          style={{ color: "var(--text-muted)" }}
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
      </div>

      {/* Nakshatra grid */}
      <div
        ref={listRef}
        className="grid grid-cols-1 gap-1 sm:grid-cols-2 lg:grid-cols-3"
        role="listbox"
        aria-label="List of 27 nakshatras"
      >
        {filtered.map((nakshatra) => {
          const lord = NAKSHATRA_LORDS[nakshatra];
          const isActive = activeNakshatra === nakshatra;
          const planetInNak = planetByNakshatra[nakshatra] ?? [];
          const isExpanded = expandedLord === lord;

          return (
            <div key={nakshatra} role="option" aria-selected={isActive}>
              <button
                type="button"
                data-nakshatra-item
                onClick={() => {
                  setSelectedNakshatra(nakshatra);
                  setSelectedPada(null);
                }}
                className="w-full rounded-lg border p-3 text-left transition focus-visible:outline-none focus-visible:ring-2"
                style={{
                  borderColor: isActive
                    ? "var(--accent)"
                    : "var(--border-primary)",
                  backgroundColor: isActive
                    ? "var(--bg-card-hover)"
                    : "var(--bg-card)",
                  color: "var(--text-primary)",
                }}
                aria-label={`${nakshatra} nakshatra, ruled by ${lord}${
                  planetInNak.length > 0
                    ? `. Contains ${planetInNak.map((p) => p.planet).join(", ")}`
                    : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{nakshatra}</span>
                  <span
                    className="text-xs"
                    style={{ color: "var(--text-muted)" }}
                  >
                    {lord}
                  </span>
                </div>

                {/* Planets indicator */}
                {planetInNak.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {planetInNak.map((p) => (
                      <span
                        key={p.planet}
                        className="rounded px-1.5 py-0.5 text-xs"
                        style={{
                          backgroundColor: "var(--accent)",
                          color: "var(--accent-text)",
                        }}
                      >
                        {p.planet} P{p.pada}
                      </span>
                    ))}
                  </div>
                )}
              </button>

              {/* Padas grid (shown when nakshatra is selected) */}
              {isActive && (
                <div
                  className="mt-2 grid grid-cols-4 gap-1 pl-2"
                  role="radiogroup"
                  aria-label={`${nakshatra} padas`}
                >
                  {[1, 2, 3, 4].map((pada) => {
                    const isSelected = selectedPada === pada;
                    const startDeg =
                      NAKSHATRAS.indexOf(nakshatra) * 13.3333 + (pada - 1) * PADA_DEGREES;
                    return (
                      <button
                        key={pada}
                        type="button"
                        role="radio"
                        aria-checked={isSelected}
                        aria-label={`${nakshatra} pada ${pada}, starting at ${startDeg.toFixed(1)} degrees`}
                        onClick={() => handleSelect(nakshatra, pada)}
                        className="rounded border p-2 text-center text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2"
                        style={{
                          borderColor: isSelected
                            ? "var(--accent)"
                            : "var(--border-primary)",
                          backgroundColor: isSelected
                            ? "var(--accent)"
                            : "transparent",
                          color: isSelected
                            ? "var(--accent-text)"
                            : "var(--text-secondary)",
                        }}
                      >
                        <div>P{pada}</div>
                        <div
                          className="mt-0.5 text-xs"
                          style={{
                            color: isSelected
                              ? "var(--accent-text)"
                              : "var(--text-muted)",
                          }}
                        >
                          {startDeg.toFixed(1)}°
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-sm" style={{ color: "var(--text-muted)" }}>
          No nakshatras match "{search}"
        </p>
      )}

      {/* Summary of selected */}
      {selectedNakshatra && selectedPada && (
        <div
          className="rounded-lg border p-3"
          style={{
            borderColor: "var(--border-primary)",
            backgroundColor: "var(--bg-card)",
          }}
          role="status"
          aria-live="polite"
        >
          <p className="text-sm" style={{ color: "var(--text-primary)" }}>
            <span className="font-semibold" style={{ color: "var(--accent)" }}>
              {selectedNakshatra}
            </span>{" "}
            — Pada {selectedPada} — Rashi:{" "}
            {RASHIS[Math.floor((NAKSHATRAS.indexOf(selectedNakshatra) * 4 + selectedPada - 1) / 4)] ??
              "—"}
          </p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
            Lord: {NAKSHATRA_LORDS[selectedNakshatra]} · Degree range:{" "}
            {(NAKSHATRAS.indexOf(selectedNakshatra) * 13.3333 + (selectedPada - 1) * PADA_DEGREES).toFixed(
              1,
            )}
            ° –{" "}
            {(NAKSHATRAS.indexOf(selectedNakshatra) * 13.3333 + selectedPada * PADA_DEGREES).toFixed(
              1,
            )}
            ° sidereal
          </p>
        </div>
      )}

      {/* Level 2 — Classical Knowledge Base panel, real data from the
          backend's nakshatra catalogue (deity, shakti, nature, per-pada
          Navamsha mapping, karakatvas, cited sources). Only the fields the
          catalogue actually has are shown — no invented attributes. */}
      {selectedNakshatra && (
        <div
          className="space-y-3 rounded-lg border p-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
          aria-live="polite"
        >
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
              Classical Knowledge — {selectedNakshatra}
            </h4>
            {!!nakDetail?.sources.length && (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {nakDetail.sources.length} cited source{nakDetail.sources.length > 1 ? "s" : ""}
              </span>
            )}
          </div>

          {nakLoading && (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Loading…</p>
          )}

          {nakDetail && (
            <>
              {nakDetail.meaning && (
                <p className="text-sm italic" style={{ color: "var(--text-secondary)" }}>
                  {nakDetail.meaning}
                </p>
              )}

              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-3">
                {nakDetail.deity?.name && <KV label="Deity" value={nakDetail.deity.name} />}
                {nakDetail.shakti?.name && <KV label="Shakti" value={nakDetail.shakti.name} />}
                {nakDetail.nature?.guna && <KV label="Guna" value={nakDetail.nature.guna} />}
                {nakDetail.nature?.gana && <KV label="Gana" value={nakDetail.nature.gana} />}
                {nakDetail.nature?.yoni && <KV label="Yoni" value={nakDetail.nature.yoni} />}
                {nakDetail.nature?.nadi && <KV label="Nadi" value={nakDetail.nature.nadi} />}
              </div>

              {/* This is the real classical link between Nakshatra Pada and
                  the Navamsha (D9) chart — each pada maps to a fixed D9
                  sign, straight from the catalogue's per-pada data. */}
              {selectedPada && (
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Pada {selectedPada} → Navamsha (D9) sign:{" "}
                  <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                    {nakDetail.padas.find((p) => p.pada === selectedPada)?.navamsha_rashi ?? "—"}
                  </span>
                </p>
              )}

              {nakDetail.deity?.description && (
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  {nakDetail.deity.description.trim()}
                </p>
              )}

              {nakDetail.karakatvas.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {nakDetail.karakatvas.map((k) => (
                    <span
                      key={k}
                      className="rounded-full px-2 py-0.5 text-xs"
                      style={{ backgroundColor: "var(--bg-card-hover)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
                    >
                      {k}
                    </span>
                  ))}
                </div>
              )}

              {nakDetail.compatible_nakshatras.length > 0 && (
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                  Compatible: {nakDetail.compatible_nakshatras.join(", ")}
                </p>
              )}

              {nakDetail.sources.length > 0 && (
                <details className="text-xs">
                  <summary className="cursor-pointer" style={{ color: "var(--text-muted)" }}>
                    Sources
                  </summary>
                  <ul className="mt-1 space-y-1 pl-3" style={{ color: "var(--text-secondary)" }}>
                    {nakDetail.sources.map((s, i) => (
                      <li key={i}>
                        <span className="font-medium">{s.ref}</span>
                        {s.claim && <>: "{s.claim.trim()}"</>}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </>
          )}
        </div>
      )}

      {/* Lord-grouped quick links */}
      <details
        className="rounded-lg border"
        style={{
          borderColor: "var(--border-primary)",
          backgroundColor: "var(--bg-card)",
        }}
      >
        <summary
          className="cursor-pointer p-3 text-xs font-semibold uppercase tracking-wide"
          style={{ color: "var(--text-secondary)" }}
        >
          Browse by Planetary Lord
        </summary>
        <div className="space-y-2 p-3 pt-0">
          {Object.entries(byLord).map(([lord, naks]) => (
            <div key={lord}>
              <button
                type="button"
                onClick={() =>
                  setExpandedLord(expandedLord === lord ? null : lord)
                }
                className="flex items-center gap-2 text-xs font-medium"
                style={{ color: "var(--accent)" }}
                aria-expanded={expandedLord === lord}
              >
                <span>{expandedLord === lord ? "▾" : "▸"}</span>
                {lord}
                <span
                  className="text-xs"
                  style={{ color: "var(--text-muted)" }}
                >
                  ({naks.length})
                </span>
              </button>
              {expandedLord === lord && (
                <div className="mt-1 flex flex-wrap gap-1 pl-4">
                  {naks.map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => {
                        setSelectedNakshatra(n);
                        setSelectedPada(null);
                      }}
                      className="rounded border px-2 py-1 text-xs transition"
                      style={{
                        borderColor:
                          selectedNakshatra === n
                            ? "var(--accent)"
                            : "var(--border-primary)",
                        color:
                          selectedNakshatra === n
                            ? "var(--accent)"
                            : "var(--text-secondary)",
                      }}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
