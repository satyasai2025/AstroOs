"use client";

/**
 * AstroOS — KP Event Explorer (Full KP Master 408 Events Master Replication)
 *
 * Config-driven event promise: each event reads its exact classical house
 * configurations (Main House, Supporting Houses, Hindering Houses, Supporting Planets & Signs)
 * straight from KP Master's master database.
 */

import { useState, useMemo } from "react";
import type { EventPromiseResponse } from "@/lib/types";
import rawEventsData from "@/lib/kpMasterEventsData.json";

interface Props {
  eventPromises: EventPromiseResponse[];
}

interface KPEventItem {
  label: string;
  category: string;
  houses: number[];
  primaryCusp: number;
  supportingHouses: number[];
  adverseHouses: number[];
  polarity: "BENEFICIAL" | "ADVERSE";
  supportingPlanets: string[];
  supportingSigns: string[];
}

const KP_EVENTS = rawEventsData as Record<string, KPEventItem>;
const ALL_EVENT_KEYS = Object.keys(KP_EVENTS);
const CATEGORIES = ["All", "Career", "Finance", "Marriage", "Health", "Property", "Travel", "Legal", "Progeny", "Education", "Spiritual"];

const VERDICT_COLORS: Record<string, { fg: string; bg: string }> = {
  POSITIVE: { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  PARTIAL: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
  WEAK: { fg: "#f87171", bg: "rgba(248,113,113,0.15)" },
  ADVERSE_RISK: { fg: "#ef4444", bg: "rgba(239,68,68,0.2)" },
};

export function KPEventExplorer({ eventPromises }: Props) {
  const [selectedKey, setSelectedKey] = useState<string>("adopt_a_child");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  // Filtered list of event keys
  const filteredKeys = useMemo(() => {
    return ALL_EVENT_KEYS.filter((k) => {
      const ev = KP_EVENTS[k];
      if (!ev) return false;
      const matchCat = selectedCategory === "All" || ev.category.toLowerCase() === selectedCategory.toLowerCase();
      const matchSearch = searchTerm.trim() === "" || ev.label.toLowerCase().includes(searchTerm.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [searchTerm, selectedCategory]);

  const activeEvent: KPEventItem = KP_EVENTS[selectedKey] || KP_EVENTS["adopt_a_child"] || {
    label: "Selected Event",
    category: "General",
    houses: [10],
    primaryCusp: 10,
    supportingHouses: [],
    adverseHouses: [],
    polarity: "BENEFICIAL",
    supportingPlanets: [],
    supportingSigns: [],
  };

  const backendPromise = eventPromises.find((e) => e.eventKey === selectedKey);
  const isAdverse = activeEvent.polarity === "ADVERSE";
  const vc = isAdverse ? VERDICT_COLORS.ADVERSE_RISK : (VERDICT_COLORS[backendPromise?.promise ?? "POSITIVE"] || VERDICT_COLORS.POSITIVE);

  return (
    <div className="space-y-5">
      {/* ── Category Tabs & Search Bar ───────────────────────────────────────── */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-1.5">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className="rounded-full px-3 py-1 text-xs font-semibold transition"
                style={{
                  backgroundColor: selectedCategory === cat ? "var(--accent)" : "var(--bg-card)",
                  color: selectedCategory === cat ? "var(--accent-text)" : "var(--text-secondary)",
                  border: `1px solid ${selectedCategory === cat ? "var(--accent)" : "var(--border-primary)"}`,
                }}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
              {filteredKeys.length} / {ALL_EVENT_KEYS.length} KP Classical Events
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-1">
          <div className="flex-1 min-w-[240px]">
            <input
              type="text"
              placeholder="🔍 Search all 408 Classical KP events (e.g. Adopt a child, Break in Service, Accident, Property)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-md px-3.5 py-2 text-xs font-medium"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-primary)",
              }}
            />
          </div>

          <div className="w-full md:w-auto min-w-[260px]">
            <select
              value={selectedKey}
              onChange={(e) => setSelectedKey(e.target.value)}
              className="w-full rounded-md px-3.5 py-2 text-xs font-semibold"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-primary)",
              }}
            >
              {filteredKeys.map((k) => {
                const ev = KP_EVENTS[k];
                return (
                  <option key={k} value={k}>
                    {ev.label} ({ev.polarity === "ADVERSE" ? "⚠️ Adverse" : "✅ Beneficial"} • House {ev.primaryCusp})
                  </option>
                );
              })}
            </select>
          </div>
        </div>
      </div>

      {/* ── Active Selected Event Details (Classical KP Configuration) ──────────── */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Card 1: Event Verdict & Promise */}
        <div className="glass-card p-5" style={{ borderLeft: `4px solid ${vc.fg}` }}>
          <p className="text-[10px] uppercase tracking-wide font-bold" style={{ color: "var(--text-muted)" }}>
            {isAdverse ? "⚠️ KP Adverse Disruption Analysis" : "🔮 KP Event Fructification"}
          </p>
          <p className="mt-1 text-2xl font-bold" style={{ color: vc.fg }}>
            {activeEvent.label}
          </p>
          <div className="mt-2 flex items-center gap-2">
            <span
              className="inline-block rounded-full px-3 py-0.5 text-xs font-bold"
              style={{ backgroundColor: vc.bg, color: vc.fg }}
            >
              {isAdverse ? "ADVERSE RISK / CAUTION" : (backendPromise?.promise ?? "POSITIVE PROMISE")}
            </span>
            <span className="text-[11px] font-semibold" style={{ color: "var(--text-muted)" }}>
              Category: {activeEvent.category}
            </span>
          </div>

          <p className="mt-3 text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {isAdverse
              ? `Adverse event configuration active. Activating houses (${activeEvent.supportingHouses.join(", ") || activeEvent.houses.join(", ")}) trigger disruption against House ${activeEvent.primaryCusp}.`
              : `Classical KP Fructification for "${activeEvent.label}". Primary Cusp: ${activeEvent.primaryCusp}, Supporting Houses: ${activeEvent.supportingHouses.join(", ") || "—"}.`}
          </p>

          <div className="mt-4 pt-3 border-t text-xs space-y-1" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
            <p><strong>Primary Main House:</strong> House {activeEvent.primaryCusp}</p>
            <p><strong>Supporting Houses:</strong> {activeEvent.supportingHouses.length ? activeEvent.supportingHouses.join(", ") : "—"}</p>
            {activeEvent.adverseHouses.length > 0 && (
              <p className="text-red-400"><strong>Hindering Houses:</strong> {activeEvent.adverseHouses.join(", ")}</p>
            )}
          </div>
        </div>

        {/* Card 2: CSL Decision Chain & KP Master Factors */}
        <div className="glass-card p-5">
          <p className="mb-2 text-[10px] uppercase tracking-wide font-bold" style={{ color: "var(--text-muted)" }}>
            KP Master KP Matrix & Planetary Rules
          </p>
          <ol className="space-y-2 text-xs" style={{ color: "var(--text-secondary)" }}>
            <li className="rounded-lg border p-2 flex justify-between" style={{ borderColor: "var(--border-primary)" }}>
              <span>Main House (Cusp):</span>
              <span className="font-bold" style={{ color: "var(--accent)" }}>House {activeEvent.primaryCusp}</span>
            </li>
            <li className="rounded-lg border p-2 flex justify-between" style={{ borderColor: "var(--border-primary)" }}>
              <span>Fruitful Significations:</span>
              <span className="font-bold" style={{ color: "var(--text-primary)" }}>{activeEvent.houses.join(", ")}</span>
            </li>
            <li className="rounded-lg border p-2 flex justify-between" style={{ borderColor: "var(--border-primary)" }}>
              <span>Supporting Planets:</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                {activeEvent.supportingPlanets.length ? activeEvent.supportingPlanets.join(", ") : "All favorable grahas"}
              </span>
            </li>
            <li className="rounded-lg border p-2 flex justify-between" style={{ borderColor: "var(--border-primary)" }}>
              <span>Supporting Signs:</span>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>
                {activeEvent.supportingSigns.length ? activeEvent.supportingSigns.join(", ") : "All fruitful signs"}
              </span>
            </li>
          </ol>
        </div>

        {/* Card 3: Dasha & Transit Timing Rules */}
        <div className="glass-card p-5">
          <p className="mb-2 text-[10px] uppercase tracking-wide font-bold" style={{ color: "var(--text-muted)" }}>
            Dasha & Transit Fructification Windows
          </p>
          <div className="space-y-2 text-xs" style={{ color: "var(--text-secondary)" }}>
            <div className="rounded-lg border p-2.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-surface)" }}>
              <p className="font-bold text-[11px]" style={{ color: "var(--accent)" }}>⏳ Vimshottari DBAS Alignment</p>
              <p className="mt-0.5 text-[11px]">
                Event delivers during running Mahadasha / Antardasha of planets holding Level A/B significations for Houses {activeEvent.houses.join(", ")}.
              </p>
            </div>

            <div className="rounded-lg border p-2.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-surface)" }}>
              <p className="font-bold text-[11px]" style={{ color: "#34d399" }}>⚡ Transit (Gochar) Trigger</p>
              <p className="mt-0.5 text-[11px]">
                Jupiter & Saturn transits over the {activeEvent.primaryCusp}th cusp axis activate timing window; Moon transit delivers daily trigger.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
