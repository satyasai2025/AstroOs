"use client";

import { useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";
import {
  RASHIS,
  rashiIndexFromApiName,
  PLANET_ABBREV,
  PLANET_SYMBOLS,
  CHART_COLORS,
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

interface AspectPlacement {
  from_planet: string;
  to_planet: string;
  aspect_type: string;
}

const ASPECT_COLORS: Record<string, string> = CHART_COLORS.aspectColors;
const ASPECT_DEFAULT_COLOR = "#6B7280";

interface NorthIndianChartProps {
  /** Title shown above the chart (e.g. "D1 — Rashi Chart"). */
  title?: string;
  /** Ascendant position. */
  ascendant: AscendantPlacement;
  /** Planets to render in the chart. */
  planets: PlanetPlacement[];
  /** Optional: aspects to draw as dashed lines between planets. */
  aspects?: AspectPlacement[];
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
  /** Called with a house number on hover-in, and null on hover-out. */
  onHouseHover?: (house: number | null) => void;
  /** Called with a house number when clicked (pins the selection). */
  onHouseClick?: (house: number) => void;
  /** Currently hovered or selected house — drawn with a highlight fill. */
  activeHouse?: number | null;
}

/**
 * The classical North Indian chart construction: an outer square, both
 * diagonals (corner to corner), and an inner diamond connecting the
 * midpoints of the four sides. That produces exactly 12 regions — a
 * rhombus at the midpoint of each side (houses 1/4/7/10, the Kendras)
 * and two triangles filling each corner (the remaining 8 houses) — not
 * 12 equal angular wedges. Coordinates below are worked out in a 0–100
 * unit square and verified by hand (every rhombus has 4 equal sides);
 * `unitToPoint` maps them into the actual SVG size at render time.
 *
 * House 1 is fixed at the top, proceeding counter-clockwise per the
 * standard North Indian convention (1 top → 4 left → 7 bottom → 10
 * right for the Kendras, with 2/3, 5/6, 8/9, 11/12 filling the
 * corners between them in that order).
 */
const A: [number, number] = [0, 0]; // top-left
const B: [number, number] = [100, 0]; // top-right
const C: [number, number] = [100, 100]; // bottom-right
const D: [number, number] = [0, 100]; // bottom-left
const O: [number, number] = [50, 50]; // center
const M_AB: [number, number] = [50, 0];
const M_BC: [number, number] = [100, 50];
const M_CD: [number, number] = [50, 100];
const M_DA: [number, number] = [0, 50];
const MID_AO: [number, number] = [25, 25];
const MID_BO: [number, number] = [75, 25];
const MID_CO: [number, number] = [75, 75];
const MID_DO: [number, number] = [25, 75];

const HOUSE_UNIT_POLYGONS: Record<number, [number, number][]> = {
  1: [M_AB, MID_BO, O, MID_AO],
  2: [A, MID_AO, M_AB],
  3: [A, M_DA, MID_AO],
  4: [M_DA, MID_AO, O, MID_DO],
  5: [D, MID_DO, M_DA],
  6: [D, M_CD, MID_DO],
  7: [M_CD, MID_DO, O, MID_CO],
  8: [C, MID_CO, M_CD],
  9: [C, M_BC, MID_CO],
  10: [M_BC, MID_CO, O, MID_BO],
  11: [B, M_BC, MID_BO],
  12: [B, MID_BO, M_AB],
};

function centroid(points: [number, number][]): [number, number] {
  const n = points.length;
  const sum = points.reduce((acc, [x, y]) => [acc[0] + x, acc[1] + y], [0, 0]);
  return [sum[0] / n, sum[1] / n];
}

const HOUSE_CENTROIDS: Record<number, [number, number]> = Object.fromEntries(
  Object.entries(HOUSE_UNIT_POLYGONS).map(([h, pts]) => [Number(h), centroid(pts)]),
);

/**
 * Where the small house-number digit sits: interpolated from the
 * centroid toward whichever of the house's own vertices sits farthest
 * from the chart's center — i.e. the outer corner/edge-midpoint that
 * house actually touches. Since both endpoints belong to the same
 * convex polygon, every point strictly between them is guaranteed to
 * be inside it, not sitting on one of the construction lines that
 * happen to pass through the vertices themselves — unlike an earlier
 * version of this table that hand-picked coordinates without checking
 * them against the real geometry, which put a couple of labels
 * directly on top of the diagonal (e.g. house 2's old position (12,12)
 * sits exactly on the y=x diagonal).
 */
function farthestVertexFromCenter(points: [number, number][]): [number, number] {
  return points.reduce((farthest, p) => {
    const d = (p[0] - O[0]) ** 2 + (p[1] - O[1]) ** 2;
    const df = (farthest[0] - O[0]) ** 2 + (farthest[1] - O[1]) ** 2;
    return d > df ? p : farthest;
  }, points[0]);
}

function interpolate(
  from: [number, number],
  to: [number, number],
  t: number,
): [number, number] {
  return [from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t];
}

const HOUSE_NUMBER_UNIT_POS: Record<number, [number, number]> = Object.fromEntries(
  Object.entries(HOUSE_UNIT_POLYGONS).map(([h, pts]) => {
    const house = Number(h);
    const outer = farthestVertexFromCenter(pts);
    return [house, interpolate(HOUSE_CENTROIDS[house], outer, 0.55)];
  }),
);

export function NorthIndianChart({
  title,
  ascendant,
  planets,
  aspects = [],
  size = 400,
  showFullNames = true,
  isVarga = false,
  vargaDivisor,
  onPlanetHover,
  onPlanetClick,
  activePlanet,
  onHouseHover,
  onHouseClick,
  activeHouse,
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

    // Padding around the square leaves room for house-number labels
    // just outside the border, matching how a hand-drawn Kundli reads.
    const pad = size * 0.08;
    const squareSize = size - pad * 2;
    const toPoint = ([ux, uy]: [number, number]): [number, number] => [
      pad + (ux / 100) * squareSize,
      pad + (uy / 100) * squareSize,
    ];

    // ── Background ─────────────────────────────────────────────────────────
    svg
      .append("rect")
      .attr("width", size)
      .attr("height", size)
      .attr("rx", 12)
      .style("fill", "var(--chart-bg)");

    const lineColor = "var(--chart-border)";

    // ── Clickable house regions (drawn under the construction lines, so a
    // thin stroke-only line on top doesn't block clicks to the house area
    // beneath it) ────────────────────────────────────────────────────────
    if (onHouseHover || onHouseClick) {
      for (const [houseStr, unitPts] of Object.entries(HOUSE_UNIT_POLYGONS)) {
        const house = Number(houseStr);
        const pts = unitPts.map(toPoint);
        svg
          .append("polygon")
          .attr("points", pts.map((p) => p.join(",")).join(" "))
          .style("fill", activeHouse === house ? "var(--accent)" : "transparent")
          .style("fill-opacity", activeHouse === house ? 0.12 : 0)
          .style("cursor", "pointer")
          .on("mouseenter", () => onHouseHover?.(house))
          .on("mouseleave", () => onHouseHover?.(null))
          .on("click", () => onHouseClick?.(house));
      }
    }

    // ── Construction lines: outer square + both diagonals + inner diamond ──
    const [pA, pB, pC, pD] = [A, B, C, D].map(toPoint);
    const [pMAB, pMBC, pMCD, pMDA] = [M_AB, M_BC, M_CD, M_DA].map(toPoint);

    svg
      .append("polygon")
      .attr("points", [pA, pB, pC, pD].map((p) => p.join(",")).join(" "))
      .style("fill", "none")
      .style("stroke", lineColor)
      .style("stroke-width", 2);

    svg.append("line").attr("x1", pA[0]).attr("y1", pA[1]).attr("x2", pC[0]).attr("y2", pC[1])
      .style("stroke", lineColor).style("stroke-width", 1);
    svg.append("line").attr("x1", pB[0]).attr("y1", pB[1]).attr("x2", pD[0]).attr("y2", pD[1])
      .style("stroke", lineColor).style("stroke-width", 1);

    svg
      .append("polygon")
      .attr("points", [pMAB, pMBC, pMCD, pMDA].map((p) => p.join(",")).join(" "))
      .style("fill", "none")
      .style("stroke", lineColor)
      .style("stroke-width", 1);

    // ── House number labels ──────────────────────────────────────────────────
    const chartText = "var(--chart-text)";
    const accentColor = "var(--accent)";
    const ascColor = "var(--chart-ascendant)";

    for (let house = 1; house <= 12; house++) {
      const [lx, ly] = toPoint(HOUSE_NUMBER_UNIT_POS[house]);
      svg.append("text")
        .attr("x", lx)
        .attr("y", ly)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .attr("paint-order", "stroke")
        .style("font-size", "8px")
        .style("stroke", "var(--chart-bg)")
        .style("stroke-width", "3px")
        .style("fill", chartText)
        .style("opacity", 0.7)
        .text(house);
    }

    // ── Rashi labels (small, near each house's number) ──────────────────────
    for (let house = 1; house <= 12; house++) {
      const [nx, ny] = toPoint(HOUSE_NUMBER_UNIT_POS[house]);
      const [cx, cy] = toPoint(HOUSE_CENTROIDS[house]);
      // Nudge partway from the number position toward the centroid so the
      // rashi abbreviation doesn't collide with the house-number digit.
      const rx = nx + (cx - nx) * 0.35;
      const ry = ny + (cy - ny) * 0.35;
      const rashiName = houseRashis[house] ?? "";
      svg.append("text")
        .attr("x", rx)
        .attr("y", ry)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .attr("paint-order", "stroke")
        .style("font-size", "9px")
        .style("font-weight", "600")
        .style("stroke", "var(--chart-bg)")
        .style("stroke-width", "3px")
        .style("fill", chartText)
        .style("opacity", 0.9)
        .text(rashiName.slice(0, 3));
    }

    // ── Compute each planet's rendered position up front — reused for both
    // the aspect lines (drawn first, underneath) and the planet glyphs
    // themselves (drawn after, on top). ─────────────────────────────────
    const planetPositions: Record<string, [number, number]> = {};
    for (const [houseStr, ps] of Object.entries(housePlanets)) {
      const house = Number(houseStr);
      const [px, py] = toPoint(HOUSE_CENTROIDS[house]);
      const lineHeight = 15;
      ps.forEach((planet, i) => {
        const offsetY = (i - (ps.length - 1) / 2) * lineHeight;
        planetPositions[planet.planet] = [px, py + offsetY];
      });
    }

    // ── Aspect lines between planets — dim by default; hovering/pinning a
    // planet highlights only the lines touching it, per the interactive
    // Kundli spec ("hover a planet → shows aspect lines to connected
    // planets"), while still leaving a faint always-on hint of the full
    // aspect network so the chart isn't blank at rest. ───────────────────
    for (const asp of aspects) {
      const from = planetPositions[asp.from_planet];
      const to = planetPositions[asp.to_planet];
      if (!from || !to) continue;
      const color = ASPECT_COLORS[asp.aspect_type] ?? ASPECT_DEFAULT_COLOR;
      const touchesActive =
        !!activePlanet && (asp.from_planet === activePlanet || asp.to_planet === activePlanet);
      const dimmed = !!activePlanet && !touchesActive;
      svg
        .append("line")
        .attr("x1", from[0]).attr("y1", from[1])
        .attr("x2", to[0]).attr("y2", to[1])
        .style("stroke", color)
        .style("stroke-width", touchesActive ? 1.75 : 1)
        .style("stroke-dasharray", "3,3")
        .style("opacity", dimmed ? 0.12 : touchesActive ? 0.9 : 0.35);
    }

    // ── Place planets in houses (at each house's centroid) ──────────────────
    for (const [houseStr, ps] of Object.entries(housePlanets)) {
      const house = Number(houseStr);
      const [px, py] = toPoint(HOUSE_CENTROIDS[house]);

      ps.forEach((planet, i) => {
        const abbrev = PLANET_ABBREV[planet.planet] ?? planet.planet.slice(0, 2);
        const symbol = PLANET_SYMBOLS[planet.planet] ?? "";
        const isAsc = house === 1 && i === 0;
        const isActive = activePlanet === planet.planet;

        // Stack planets vertically within the house if there's more than one.
        const lineHeight = 15;
        const offsetY = (i - (ps.length - 1) / 2) * lineHeight;

        const g = svg.append("g")
          .attr("transform", `translate(${px}, ${py + offsetY})`)
          .style("cursor", onPlanetHover || onPlanetClick ? "pointer" : "default")
          .on("mouseenter", () => onPlanetHover?.(planet.planet))
          .on("mouseleave", () => onPlanetHover?.(null))
          .on("click", () => onPlanetClick?.(planet.planet));

        if (isActive) {
          g.append("circle")
            .attr("cx", 0)
            .attr("cy", -2)
            .attr("r", 14)
            .style("fill", "var(--accent)")
            .style("opacity", 0.18);
        }

        g.append("text")
          .attr("x", -14)
          .attr("y", 0)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "central")
          .style("font-size", "9px")
          .style("fill", isAsc ? ascColor : accentColor)
          .text(symbol);

        g.append("text")
          .attr("x", 2)
          .attr("y", 0)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "central")
          .style("font-size", "10px")
          .style("font-weight", isActive ? "900" : "bold")
          .style("fill", isAsc ? ascColor : accentColor)
          .text(abbrev);

        if (planet.is_retrograde) {
          g.append("text")
            .attr("x", 20)
            .attr("y", 0)
            .attr("text-anchor", "start")
            .attr("dominant-baseline", "central")
            .style("font-size", "7px")
            .style("fill", "var(--chart-ascendant)")
            .text("R");
        }

        if (planet.rashi_degree !== undefined) {
          g.append("text")
            .attr("x", 2)
            .attr("y", 11)
            .attr("text-anchor", "middle")
            .style("font-size", "6px")
            .style("fill", chartText)
            .style("opacity", 0.7)
            .text(`${planet.rashi_degree.toFixed(1)}°`);
        }
      });
    }

    // ── Ascendant marker (Lagna) ─────────────────────────────────────────────
    const [ascX, ascY] = toPoint(HOUSE_CENTROIDS[1]);
    svg.append("text")
      .attr("x", ascX)
      .attr("y", ascY - 20)
      .attr("text-anchor", "middle")
      .style("font-size", "8px")
      .style("font-weight", "bold")
      .style("fill", ascColor)
      .text("LAGNA");
  }, [
    size,
    housePlanets,
    houseRashis,
    ascendant.rashi,
    aspects,
    activePlanet,
    onPlanetHover,
    onPlanetClick,
    activeHouse,
    onHouseHover,
    onHouseClick,
  ]);

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
        className="h-auto w-full"
        role="img"
        aria-label={`North Indian square chart: ${chartTitle}`}
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
