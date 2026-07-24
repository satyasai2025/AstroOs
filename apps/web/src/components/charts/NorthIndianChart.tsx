"use client";

import { useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";
import {
  RASHIS,
  rashiIndexFromApiName,
  PLANET_ABBREV,
  PLANET_SYMBOLS,
} from "@/lib/astro";

/**
 * Planet placement data — the minimum information needed to draw a chart.
 */
interface PlanetPlacement {
  planet: string;
  rashi: string;
  house_number?: number;
  is_retrograde?: boolean;
  rashi_degree?: number;
}

interface AscendantPlacement {
  rashi: string;
  rashi_degree?: number;
}

interface NorthIndianChartProps {
  /** Title shown above the chart (e.g. "D1 — Rashi Chart"). */
  title?: string;
  /** Ascendant position. */
  ascendant: AscendantPlacement;
  /** Planets to render in the chart. */
  planets: PlanetPlacement[];
  /** Optional: size override in pixels (default 400). */
  size?: number;
  /** Optional: show planet full names in tooltip. */
  showFullNames?: boolean;
  /** Whether this is a varga chart (changes subtitle). */
  isVarga?: boolean;
  /** Varga divisor (e.g. 9 for D9). */
  vargaDivisor?: number;
  /** Called with a planet name on hover-in, and null on hover-out. */
  onPlanetHover?: (planet: string | null) => void;
  /** Called with a planet name when clicked (pins the selection). */
  onPlanetClick?: (planet: string) => void;
  /** Currently hovered or selected planet — drawn with a highlight ring. */
  activePlanet?: string | null;
}

/**
 * NorthIndianChart renders a traditional North Indian diamond-style
 * Vedic astrology chart using D3.js for SVG construction.
 *
 * The chart layout:
 *   - The outer diamond has 12 houses
 *   - Lines cross through the center forming 4 triangles
 *   - The ascendant (Lagna) house is always at the top
 *   - Houses proceed COUNTER-CLOCKWISE, per the standard North Indian
 *     convention: 1(top) → 2(upper-left) → 3(left) → 4(lower-left) →
 *     5(bottom) → 6(lower-right) → 7(right) → 8(upper-right) → back to 1.
 *     (South Indian and East Indian style charts use different fixed
 *     layouts — this component is North Indian style specifically.)
 *   - Inner ring: 9(top) → 10(left) → 11(bottom) → 12(right), same
 *     counter-clockwise direction.
 *
 * The diamond is split into 8 outer sections + 4 inner triangles = 12
 * houses. Note this is a simplified schematic (evenly-spaced compass
 * positions), not a pixel-accurate reproduction of the traditional
 * kite/triangle house shapes — house-number direction is classically
 * correct, but houses 1/4/7/10 (Kendras) aren't drawn as the larger
 * quadrilaterals a hand-drawn chart would use.
 */
export function NorthIndianChart({
  title,
  ascendant,
  planets,
  size = 400,
  showFullNames = true,
  isVarga = false,
  vargaDivisor,
  onPlanetHover,
  onPlanetClick,
  activePlanet,
}: NorthIndianChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  // Map planets into their houses based on rashi placement
  const housePlanets = useMemo(() => {
    const ascIdx = rashiIndexFromApiName(ascendant.rashi);
    const map: Record<number, PlanetPlacement[]> = {};
    for (const p of planets) {
      const pIdx = rashiIndexFromApiName(p.rashi);
      const house = ((pIdx - ascIdx + 12) % 12) + 1;
      if (!map[house]) map[house] = [];
      map[house].push(p);
    }
    return map;
  }, [ascendant.rashi, planets]);

  // Map rashi label for each house
  const houseRashis = useMemo(() => {
    const ascIdx = rashiIndexFromApiName(ascendant.rashi);
    const map: Record<number, string> = {};
    for (let h = 1; h <= 12; h++) {
      map[h] = RASHIS[(ascIdx + h - 1) % 12];
    }
    return map;
  }, [ascendant.rashi]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const cx = size / 2;
    const cy = size / 2;
    const r = size * 0.42; // outer radius
    const halfR = r * Math.SQRT2 / 2; // half diagonal for inner triangles

    // ── Background ─────────────────────────────────────────────────────────
    const bgVar = "var(--chart-bg)";
    svg
      .append("rect")
      .attr("width", size)
      .attr("height", size)
      .attr("rx", 12)
      .style("fill", bgVar);

    // ── Outer diamond ──────────────────────────────────────────────────────
    const diamondPoints = [
      [cx, cy - r],       // top
      [cx + r, cy],       // right
      [cx, cy + r],       // bottom
      [cx - r, cy],       // left
    ];

    svg
      .append("polygon")
      .attr("points", diamondPoints.map((p) => p.join(",")).join(" "))
      .style("fill", "none")
      .style("stroke", "var(--chart-border)")
      .style("stroke-width", 2);

    // ── House dividing lines ───────────────────────────────────────────────
    // Outer triangle lines (from each corner to midpoints of opposite sides)
    const lineColor = "var(--chart-border)";

    // Vertical line top→bottom
    svg.append("line")
      .attr("x1", cx).attr("y1", cy - r)
      .attr("x2", cx).attr("y2", cy + r)
      .style("stroke", lineColor).style("stroke-width", 1.5);

    // Horizontal line left→right
    svg.append("line")
      .attr("x1", cx - r).attr("y1", cy)
      .attr("x2", cx + r).attr("y2", cy)
      .style("stroke", lineColor).style("stroke-width", 1.5);

    // Diagonal lines forming inner diamond
    // Top-left to bottom-right of inner diamond
    svg.append("line")
      .attr("x1", cx - halfR).attr("y1", cy - halfR)
      .attr("x2", cx + halfR).attr("y2", cy + halfR)
      .style("stroke", lineColor).style("stroke-width", 1);

    // Top-right to bottom-left of inner diamond
    svg.append("line")
      .attr("x1", cx + halfR).attr("y1", cy - halfR)
      .attr("x2", cx - halfR).attr("y2", cy + halfR)
      .style("stroke", lineColor).style("stroke-width", 1);

    // ── House positions (centroids for placing text) ───────────────────────
    // North Indian chart house positions (12 houses in the diamond).
    // Numbering runs COUNTER-CLOCKWISE from the top (house 1), per the
    // standard convention — e.g. house 4 sits on the LEFT and house 10 on
    // the RIGHT, not the other way around.
    const housePositions: { house: number; x: number; y: number }[] = [
      // Outer triangle positions (houses 1-8)
      { house: 1, x: cx, y: cy - r * 0.65 },          // top center
      { house: 2, x: cx - r * 0.55, y: cy - r * 0.4 }, // upper left
      { house: 3, x: cx - r * 0.65, y: cy },            // left
      { house: 4, x: cx - r * 0.55, y: cy + r * 0.4 },  // lower left
      { house: 5, x: cx, y: cy + r * 0.65 },           // bottom center
      { house: 6, x: cx + r * 0.55, y: cy + r * 0.4 },  // lower right
      { house: 7, x: cx + r * 0.65, y: cy },            // right
      { house: 8, x: cx + r * 0.55, y: cy - r * 0.4 },  // upper right
      // Inner triangle positions (houses 9-12)
      { house: 9, x: cx, y: cy - halfR * 0.45 },        // inner top
      { house: 10, x: cx - halfR * 0.45, y: cy },        // inner left
      { house: 11, x: cx, y: cy + halfR * 0.45 },        // inner bottom
      { house: 12, x: cx + halfR * 0.45, y: cy },        // inner right
    ];

    // ── Rashi labels (small, in each house corner) ─────────────────────────
    const rashiPositions: { house: number; x: number; y: number }[] = [
      { house: 1, x: cx, y: cy - r * 0.95 },
      { house: 2, x: cx - r * 0.85, y: cy - r * 0.6 },
      { house: 3, x: cx - r * 0.95, y: cy },
      { house: 4, x: cx - r * 0.85, y: cy + r * 0.6 },
      { house: 5, x: cx, y: cy + r * 0.95 },
      { house: 6, x: cx + r * 0.85, y: cy + r * 0.6 },
      { house: 7, x: cx + r * 0.95, y: cy },
      { house: 8, x: cx + r * 0.85, y: cy - r * 0.6 },
      { house: 9, x: cx - halfR * 0.3, y: cy - halfR * 0.7 },
      { house: 10, x: cx - halfR * 0.7, y: cy + halfR * 0.3 },
      { house: 11, x: cx + halfR * 0.3, y: cy + halfR * 0.7 },
      { house: 12, x: cx + halfR * 0.7, y: cy - halfR * 0.3 },
    ];

    const chartText = "var(--chart-text)";
    const accentColor = "var(--accent)";
    const ascColor = "var(--chart-ascendant)";

    // Draw rashi labels
    rashiPositions.forEach(({ house, x: rx, y: ry }) => {
      const rashiName = houseRashis[house] ?? "";
      svg.append("text")
        .attr("x", rx)
        .attr("y", ry)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .style("font-size", "9px")
        .style("fill", chartText)
        .style("opacity", 0.6)
        .text(rashiName.slice(0, 3));
    });

    // ── House number labels (tiny, at the very edge) ───────────────────────
    housePositions.forEach(({ house, x: hx, y: hy }) => {
      // Small house number indicator
      if (house <= 8) {
        // Negative increment — same counter-clockwise direction as the
        // house/rashi position tables above.
        const angle = (-(house - 1) * 45 - 90) * (Math.PI / 180);
        const labelR = r * 1.06;
        const lx = cx + labelR * Math.cos(angle);
        const ly = cy + labelR * Math.sin(angle);
        svg.append("text")
          .attr("x", lx)
          .attr("y", ly)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "central")
          .style("font-size", "7px")
          .style("fill", chartText)
          .style("opacity", 0.4)
          .text(house);
      }
    });

    // ── Place planets in houses ────────────────────────────────────────────
    const allPlacements = Object.entries(housePlanets).map(([h, ps]) => ({
      house: parseInt(h),
      planets: ps,
    }));

    allPlacements.forEach(({ house, planets: ps }) => {
      const pos = housePositions.find((p) => p.house === house);
      if (!pos) return;

      ps.forEach((planet, i) => {
        const abbrev = PLANET_ABBREV[planet.planet] ?? planet.planet.slice(0, 2);
        const symbol = PLANET_SYMBOLS[planet.planet] ?? "";
        const isAsc = i === 0 && house === 1;
        const isActive = activePlanet === planet.planet;

        // Stack planets vertically if multiple in same house
        const offsetX = ps.length > 1 ? (i - (ps.length - 1) / 2) * 30 : 0;
        const py = pos.y + 6; // slight offset below center

        const g = svg.append("g")
          .attr("transform", `translate(${pos.x + offsetX}, ${py})`)
          .style("cursor", onPlanetHover || onPlanetClick ? "pointer" : "default")
          .on("mouseenter", () => onPlanetHover?.(planet.planet))
          .on("mouseleave", () => onPlanetHover?.(null))
          .on("click", () => onPlanetClick?.(planet.planet));

        // Highlight ring behind the active (hovered/selected) planet
        if (isActive) {
          g.append("circle")
            .attr("cx", 0)
            .attr("cy", -2)
            .attr("r", 16)
            .style("fill", "var(--accent)")
            .style("opacity", 0.18);
        }

        // Planet symbol
        g.append("text")
          .attr("x", 0)
          .attr("y", -8)
          .attr("text-anchor", "middle")
          .style("font-size", "10px")
          .style("fill", isAsc ? ascColor : accentColor)
          .text(symbol);

        // Planet abbreviation
        g.append("text")
          .attr("x", 0)
          .attr("y", 6)
          .attr("text-anchor", "middle")
          .style("font-size", "11px")
          .style("font-weight", isActive ? "900" : "bold")
          .style("fill", isAsc ? ascColor : accentColor)
          .text(abbrev);

        // Retrograde marker
        if (planet.is_retrograde) {
          g.append("text")
            .attr("x", 10)
            .attr("y", 6)
            .attr("text-anchor", "start")
            .style("font-size", "8px")
            .style("fill", "var(--chart-ascendant)")
            .text("R");
        }

        // Degree (if available)
        if (planet.rashi_degree !== undefined) {
          g.append("text")
            .attr("x", 0)
            .attr("y", 18)
            .attr("text-anchor", "middle")
            .style("font-size", "7px")
            .style("fill", chartText)
            .style("opacity", 0.7)
            .text(`${planet.rashi_degree.toFixed(1)}°`);
        }
      });
    });

    // ── Ascendant marker (Lagna) ───────────────────────────────────────────
    const ascHousePos = housePositions.find((p) => p.house === 1);
    if (ascHousePos) {
      svg.append("text")
        .attr("x", ascHousePos.x)
        .attr("y", ascHousePos.y - 18)
        .attr("text-anchor", "middle")
        .style("font-size", "8px")
        .style("font-weight", "bold")
        .style("fill", ascColor)
        .text("LAGNA");
    }

  }, [size, housePlanets, houseRashis, ascendant.rashi, activePlanet, onPlanetHover, onPlanetClick]);

  const chartTitle =
    title ??
    (isVarga && vargaDivisor
      ? `D${vargaDivisor} — ${vargaDivisor === 9 ? "Navamsha" : `Varga (÷${vargaDivisor})`}`
      : "D1 — Rashi Chart");

  return (
    <div
      className="flex flex-col items-center gap-2"
      role="img"
      aria-label={`${chartTitle} chart showing ${ascendant.rashi} ascendant with ${planets.length} planets`}
    >
      {title && (
        <h4
          className="text-sm font-semibold uppercase tracking-wide"
          style={{ color: "var(--accent)" }}
        >
          {chartTitle}
        </h4>
      )}
      <svg
        ref={svgRef}
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="max-w-full h-auto"
        style={{ maxWidth: "100%" }}
        role="img"
        aria-label={`North Indian diamond chart: ${chartTitle}`}
      />
      {/* Legend */}
      {showFullNames && (
        <div
          className="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs"
          style={{ color: "var(--text-secondary)" }}
          aria-label="Planet legend"
        >
          {planets.map((p) => {
            const abbrev = PLANET_ABBREV[p.planet] ?? p.planet.slice(0, 2);
            const full = p.planet;
            const isActive = activePlanet === p.planet;
            return (
              <button
                key={p.planet}
                type="button"
                className="flex items-center gap-1 rounded px-1 transition"
                style={{
                  backgroundColor: isActive ? "var(--accent)" : "transparent",
                  color: isActive ? "var(--accent-text)" : undefined,
                  cursor: onPlanetHover || onPlanetClick ? "pointer" : "default",
                }}
                onMouseEnter={() => onPlanetHover?.(p.planet)}
                onMouseLeave={() => onPlanetHover?.(null)}
                onClick={() => onPlanetClick?.(p.planet)}
              >
                <span style={{ color: isActive ? "inherit" : "var(--accent)" }}>{abbrev}</span>
                <span>{full}</span>
                {p.is_retrograde && (
                  <span style={{ color: isActive ? "inherit" : "var(--chart-ascendant)" }}>(R)</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
