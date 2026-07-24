"use client";

import { useMemo, useState } from "react";
import { PLANET_SYMBOLS } from "@/lib/astro";
import type { PlanetStrengthSchema, ShadbalaTotalResponse } from "@/lib/types";

interface PlanetStrengthRadarProps {
  /** Composite strength (0-10, dignity + house placement) — used for the
   * tooltip breakdown, not the axis position (see below). */
  strengths: PlanetStrengthSchema[];
  /** Real Shadbala totals in Rupas — this is what the radar actually
   * plots. Kept as a separate prop (rather than folding into `strengths`)
   * because it's a different backend response (ShadbalaTotalResponse),
   * same real data the "Planet Strength (Shadbala)" bar chart next to
   * this component uses. */
  shadbala: ShadbalaTotalResponse[];
  size?: number;
}

/** The 7 classical grahas the radar plots — Rahu/Ketu (shadow planets)
 * don't get a Shadbala or dignity-based strength_score from the backend's
 * model, so they're excluded here rather than shown with a fabricated
 * value. */
const RADAR_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"] as const;

/**
 * Classical minimum-required Shadbala per planet, in Rupas (BPHS, per
 * B.V. Raman's "Graha and Bhava Balas" — the same convention most modern
 * Shadbala calculators cite). A planet below its own minimum is
 * classically "Balaheena" (weak) regardless of how it compares to other
 * planets' minimums, which is why this is a per-planet table rather than
 * one flat cutoff.
 *
 * Note: at least one other classical source (Raman's own teaching
 * lineage via Dirah Academy) instead gives Sun a minimum of 5.0 rather
 * than 6.5 — texts vary slightly here. This uses the more commonly cited
 * figure (6.5); either way it's real classical source material, not an
 * invented number.
 */
const MIN_REQUIRED_RUPAS: Record<string, number> = {
  Sun: 6.5,
  Moon: 6.0,
  Mars: 5.0,
  Mercury: 7.0,
  Jupiter: 6.5,
  Venus: 5.5,
  Saturn: 5.0,
};

type Classification = "weak" | "average" | "strong";

/**
 * Weak/Average/Strong banding — the classical system only really defines
 * a pass/fail line (ratio >= 1.0 means the planet clears its minimum
 * requirement). Splitting the "pass" side into Average vs Strong at 1.5x
 * the minimum is AstroOS's own UI convenience, not a classical tier —
 * flagged here and in the legend so it isn't mistaken for scripture.
 */
function classify(ratio: number | null): Classification {
  if (ratio === null) return "average";
  if (ratio < 1.0) return "weak";
  if (ratio < 1.5) return "average";
  return "strong";
}

const CLASS_COLOR: Record<Classification, string> = {
  weak: "#f87171",
  average: "#fbbf24",
  strong: "#34d399",
};

const CLASS_LABEL: Record<Classification, string> = {
  weak: "Weak (below classical minimum)",
  average: "Average (meets minimum)",
  strong: "Strong (well above minimum)",
};

/**
 * Spider/radar chart of each planet's actual Shadbala (Rupas) — plotted
 * against a dashed reference polygon marking each planet's own classical
 * minimum requirement, so it's visually obvious at a glance whether a
 * planet clears its bar. This intentionally plots the SAME metric
 * (total_rupas) as the "Planet Strength (Shadbala)" bar chart next to it
 * — two views of one real number, not two competing numbers that could
 * look like a contradiction.
 *
 * The dignity/house-placement composite (strength_score, 0-10) is real
 * too, but only surfaces in the hover tooltip breakdown rather than a
 * second axis position — putting two different-scaled metrics on one set
 * of axes would be misleading.
 */
export function PlanetStrengthRadar({ strengths, shadbala, size = 340 }: PlanetStrengthRadarProps) {
  const [hovered, setHovered] = useState<string | null>(null);
  const [pinned, setPinned] = useState<string | null>(null);
  const activePlanet = pinned ?? hovered;

  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.32;

  const radarMax = useMemo(() => {
    const values = RADAR_PLANETS.map((p) => shadbala.find((s) => s.planet === p)?.total_rupas ?? 0);
    return Math.max(8, Math.ceil(Math.max(...values, 0) + 1));
  }, [shadbala]);

  const points = useMemo(() => {
    const n = RADAR_PLANETS.length;
    return RADAR_PLANETS.map((planet, i) => {
      const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
      const strengthEntry = strengths.find((s) => s.planet === planet);
      const rupas = shadbala.find((s) => s.planet === planet)?.total_rupas ?? 0;
      const required = MIN_REQUIRED_RUPAS[planet] ?? null;
      const ratio = required ? rupas / required : null;
      const cls = classify(ratio);
      const dist = (Math.max(0, Math.min(rupas, radarMax)) / radarMax) * r;
      const reqDist = required ? (Math.min(required, radarMax) / radarMax) * r : 0;
      return {
        planet,
        rupas,
        required,
        ratio,
        cls,
        strengthEntry,
        x: cx + dist * Math.cos(angle),
        y: cy + dist * Math.sin(angle),
        reqX: cx + reqDist * Math.cos(angle),
        reqY: cy + reqDist * Math.sin(angle),
        labelX: cx + (r + 26) * Math.cos(angle),
        labelY: cy + (r + 26) * Math.sin(angle),
        axisX: cx + r * Math.cos(angle),
        axisY: cy + r * Math.sin(angle),
      };
    });
  }, [strengths, shadbala, cx, cy, r, radarMax]);

  const polygonPoints = points.map((p) => `${p.x},${p.y}`).join(" ");
  const requiredPolygonPoints = points.map((p) => `${p.reqX},${p.reqY}`).join(" ");
  const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];

  const active = points.find((p) => p.planet === activePlanet) ?? null;
  // Clamp the tooltip box inside the SVG viewport so it doesn't spill off
  // the edge for planets plotted near the top/side.
  const tooltipWidth = 200;
  const tooltipLeft = active ? Math.min(Math.max(active.labelX - tooltipWidth / 2, 4), size - tooltipWidth - 4) : 0;
  const tooltipAbove = active ? active.labelY < cy : false;

  return (
    <div className="glass-card flex flex-col items-center gap-2 p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Planet Strength Radar (Shadbala)
      </h3>

      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Planet Shadbala radar chart">
          {/* Grid rings */}
          {gridLevels.map((level) => {
            const ringPoints = RADAR_PLANETS.map((_, i) => {
              const angle = (i / RADAR_PLANETS.length) * 2 * Math.PI - Math.PI / 2;
              const dist = level * r;
              return `${cx + dist * Math.cos(angle)},${cy + dist * Math.sin(angle)}`;
            }).join(" ");
            return (
              <polygon
                key={level}
                points={ringPoints}
                fill="none"
                stroke="var(--border-primary)"
                strokeWidth={1}
                opacity={0.5}
              />
            );
          })}

          {/* Axis lines */}
          {points.map((p) => (
            <line
              key={p.planet}
              x1={cx}
              y1={cy}
              x2={p.axisX}
              y2={p.axisY}
              stroke="var(--border-primary)"
              strokeWidth={1}
              opacity={0.5}
            />
          ))}

          {/* Minimum-required reference polygon (classical per-planet
              threshold) — dashed and neutral so it reads as "the bar",
              not as another data series. */}
          <polygon
            points={requiredPolygonPoints}
            fill="none"
            stroke="var(--text-muted)"
            strokeWidth={1.5}
            strokeDasharray="3 3"
            opacity={0.7}
          />

          {/* Data polygon — actual Shadbala */}
          <polygon
            points={polygonPoints}
            fill="var(--accent)"
            fillOpacity={0.18}
            stroke="var(--accent)"
            strokeWidth={2}
          />

          {/* Data points — color-coded Weak/Average/Strong */}
          {points.map((p) => (
            <g key={p.planet}>
              <circle
                cx={p.x}
                cy={p.y}
                r={activePlanet === p.planet ? 7 : 5}
                fill={CLASS_COLOR[p.cls]}
                stroke="var(--bg-card)"
                strokeWidth={1.5}
                className="transition-all"
              />
              {/* Larger invisible hit-area so hovering/tapping is easy */}
              <circle
                cx={p.x}
                cy={p.y}
                r={14}
                fill="transparent"
                style={{ cursor: "pointer" }}
                onMouseEnter={() => setHovered(p.planet)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => setPinned((prev) => (prev === p.planet ? null : p.planet))}
              />
            </g>
          ))}

          {/* Axis labels — planet symbol + name only, no numeric values
              (values live in the hover tooltip / legend instead). Label
              color reflects the same Weak/Average/Strong classification
              as the data point. */}
          {points.map((p) => (
            <g key={p.planet}>
              <text
                x={p.labelX}
                y={p.labelY - 6}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={15}
                fontWeight={700}
                fill={CLASS_COLOR[p.cls]}
              >
                {PLANET_SYMBOLS[p.planet] ?? ""}
              </text>
              <text
                x={p.labelX}
                y={p.labelY + 9}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={9.5}
                fill="var(--text-secondary)"
              >
                {p.planet}
              </text>
            </g>
          ))}
        </svg>

        {/* Hover/click tooltip — real breakdown: Shadbala, ratio vs
            classical minimum, dignity, house placement, composite score. */}
        {active && (
          <div
            className="pointer-events-none absolute z-10 rounded-lg p-3 text-xs shadow-lg"
            style={{
              left: tooltipLeft,
              top: tooltipAbove ? active.labelY + 14 : undefined,
              bottom: tooltipAbove ? undefined : size - active.labelY + 14,
              width: tooltipWidth,
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-primary)",
              color: "var(--text-primary)",
            }}
          >
            <p className="mb-1.5 flex items-center justify-between font-semibold">
              <span>
                {PLANET_SYMBOLS[active.planet] ?? ""} {active.planet}
              </span>
              <span
                className="rounded-full px-1.5 py-0.5 text-[10px] font-medium"
                style={{ backgroundColor: `${CLASS_COLOR[active.cls]}26`, color: CLASS_COLOR[active.cls] }}
              >
                {active.cls[0].toUpperCase() + active.cls.slice(1)}
              </span>
            </p>
            <div className="space-y-0.5" style={{ color: "var(--text-secondary)" }}>
              <p>
                Shadbala: <span style={{ color: "var(--text-primary)" }}>{active.rupas.toFixed(2)} rupas</span>
              </p>
              {active.required && (
                <p>
                  Required (classical min): {active.required.toFixed(1)} rupas
                  {active.ratio !== null && ` (${active.ratio.toFixed(2)}×)`}
                </p>
              )}
              {active.strengthEntry && (
                <>
                  <p>Composite Strength Score: {active.strengthEntry.strength_score.toFixed(1)} / 10</p>
                  <p>Dignity: {active.strengthEntry.dignity ?? "—"}</p>
                  <p>
                    Placement:{" "}
                    {[
                      active.strengthEntry.is_exalted && "Exalted",
                      active.strengthEntry.is_debilitated && "Debilitated",
                      active.strengthEntry.is_in_own_sign && "Own Sign",
                      active.strengthEntry.is_in_kendra && "Kendra",
                      active.strengthEntry.is_in_trikona && "Trikona",
                      active.strengthEntry.is_in_dusthana && "Dusthana",
                    ]
                      .filter(Boolean)
                      .join(", ") || "Neutral"}
                  </p>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-3 text-[11px]" style={{ color: "var(--text-muted)" }}>
        {(["strong", "average", "weak"] as Classification[]).map((cls) => (
          <span key={cls} className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CLASS_COLOR[cls] }} />
            {CLASS_LABEL[cls]}
          </span>
        ))}
      </div>
      <p className="text-center text-xs" style={{ color: "var(--text-muted)" }}>
        Solid line: actual Shadbala. Dashed line: each planet&apos;s own classical minimum requirement.
        Hover or tap a planet for the full breakdown. Average/Strong split at 1.5× minimum is AstroOS&apos;s
        own banding, not a classical tier.
      </p>
    </div>
  );
}
