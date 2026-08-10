"use client";

/**
 * KP Ruling Planets — the RP panel: Lagna/Moon sign + star + sub lords
 * plus the Day (Vara) lord, deduplicated, and the "fruitful
 * significators" intersection with any selected house group.
 */

import { useMemo, useState } from "react";
import {
  computeRulingPlanets,
  computeFruitfulSignificators,
} from "@/lib/kpAnalysis";
import type { D1ChartResponse } from "@/lib/types";

interface Props {
  chart: D1ChartResponse;
}

const HOUSE_OPTIONS = [
  { label: "Marriage (2, 7, 11)", houses: [2, 7, 11] },
  { label: "Career (2, 6, 10, 11)", houses: [2, 6, 10, 11] },
  { label: "Childbirth (2, 5, 11)", houses: [2, 5, 11] },
  { label: "Disease (6, 8, 12)", houses: [6, 8, 12] },
];

export function KPRulingPlanets({ chart }: Props) {
  const rps = useMemo(() => computeRulingPlanets(chart), [chart]);
  const [houses, setHouses] = useState<number[]>(HOUSE_OPTIONS[0].houses);
  const fruitful = useMemo(() => computeFruitfulSignificators(chart, houses), [chart, houses]);

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
          {rps.map((rp) => (
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
