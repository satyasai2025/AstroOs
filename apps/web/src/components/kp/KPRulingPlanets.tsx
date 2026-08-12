"use client";

/**
 * KP Ruling Planets — the RP panel: Lagna/Moon sign + star + sub lords
 * plus the Day (Vara) lord, deduplicated, and the "fruitful
 * significators" intersection with any selected house group. The RPs come
 * pre-computed from the backend engine; the fruitful intersection is a
 * pure data lookup over the backend's house-significator table.
 */

import { useState } from "react";
import type { HouseSignificatorsResponse, RulingPlanetResponse } from "@/lib/types";

interface Props {
  rulingPlanets: RulingPlanetResponse[];
  houseSignificators: HouseSignificatorsResponse[];
}

const HOUSE_OPTIONS = [
  { label: "Marriage (2, 7, 11)", houses: [2, 7, 11] },
  { label: "Career (2, 6, 10, 11)", houses: [2, 6, 10, 11] },
  { label: "Childbirth (2, 5, 11)", houses: [2, 5, 11] },
  { label: "Disease (6, 8, 12)", houses: [6, 8, 12] },
];

export function KPRulingPlanets({ rulingPlanets, houseSignificators }: Props) {
  const [houses, setHouses] = useState<number[]>(HOUSE_OPTIONS[0].houses);

  // Ruling Planets that also signify any of the selected houses — the
  // classical RP-intersection rule, computed directly over the backend
  // significator table (no chart recompute on the client).
  const fruitful = rulingPlanets
    .map((rp) => {
      const housesSignified = houses
        .filter((h) => {
          const hs = houseSignificators.find((s) => s.houseNumber === h);
          return hs?.significators.some((sig) => sig.planet === rp.planet) ?? false;
        })
        .sort((a, b) => a - b);
      return housesSignified.length > 0
        ? { planet: rp.planet, rpSource: rp.source, housesSignified }
        : null;
    })
    .filter((f): f is { planet: string; rpSource: string; housesSignified: number[] } => f !== null);

  return (
    <div className="space-y-4">
      <div className="glass-card p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Ruling Planets
        </h3>
        <p className="mb-3 text-xs" style={{ color: "var(--text-muted)" }}>
          The Lagna and Moon sign/star/sub lords plus the weekday (Vara) lord — the planets that
          &ldquo;rule&rdquo; the moment. Deduplicated in the founder&apos;s ordering.
        </p>
        <div className="flex flex-wrap gap-2">
          {rulingPlanets.map((rp) => (
            <span
              key={rp.planet}
              className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs"
              style={{ backgroundColor: "rgba(96,165,250,0.15)", color: "#60a5fa", border: "1px solid rgba(96,165,250,0.4)" }}
            >
              <span className="font-semibold">{rp.planet}</span>
              <span style={{ color: "var(--text-secondary)" }}>{rp.source}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="glass-card p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Fruitful Significators
        </h3>
        <p className="mb-3 text-xs" style={{ color: "var(--text-muted)" }}>
          Ruling Planets that ALSO signify the selected house group — the strongest candidates for
          that matter per the classical RP-intersection rule.
        </p>
        <div className="mb-4 flex flex-wrap gap-2">
          {HOUSE_OPTIONS.map((opt) => (
            <button
              key={opt.label}
              type="button"
              onClick={() => setHouses(opt.houses)}
              className="rounded-full px-3 py-1 text-xs font-semibold transition"
              style={{
                backgroundColor: houses.join(",") === opt.houses.join(",") ? "var(--accent)" : "var(--bg-card)",
                color: houses.join(",") === opt.houses.join(",") ? "var(--accent-text)" : "var(--text-secondary)",
                border: `1px solid ${houses.join(",") === opt.houses.join(",") ? "var(--accent)" : "var(--border-primary)"}`,
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {fruitful.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>No ruling planet also signifies these houses.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                <th className="py-2 pr-4">Planet</th>
                <th className="py-2 pr-4">RP Source</th>
                <th className="py-2">Houses Signified</th>
              </tr>
            </thead>
            <tbody>
              {fruitful.map((f) => (
                <tr key={f.planet} className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                  <td className="py-2 pr-4 font-medium">{f.planet}</td>
                  <td className="py-2 pr-4" style={{ color: "var(--text-secondary)" }}>{f.rpSource}</td>
                  <td className="py-2" style={{ color: "var(--text-secondary)" }}>{f.housesSignified.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
