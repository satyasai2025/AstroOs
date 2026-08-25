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
import {
  A,
  B,
  C,
  D,
  M_AB,
  M_BC,
  M_CD,
  M_DA,
  HOUSE_UNIT_POLYGONS,
  HOUSE_CENTROIDS,
  HOUSE_NUMBER_UNIT_POS,
} from "@/lib/chartGeometry";

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

// House geometry (HOUSE_UNIT_POLYGONS etc.) lives in lib/chartGeometry.ts —
// shared with MixedVargaTransitChart's concentric dual-ring rendering.
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
    const pad = size * 0.10;
    const squareSize = size - pad * 2;
    const toPoint = ([ux, uy]: [number, number]): [number, number] => [
      pad + (ux / 100) * squareSize,
      pad + (uy / 100) * squareSize,
    ];

    // ── Background ─────────────────────────────────────────────────────────
    svg
      .append("rect")
      .attr("x", -20)
      .attr("y", -20)
      .attr("width", size + 40)
      .attr("height", size + 40)
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

    // ── Rashi number labels ───────────────────────────────────────────────
    for (let house = 1; house <= 12; house++) {
      const [lx, ly] = toPoint(HOUSE_NUMBER_UNIT_POS[house]);
      const rashiName = houseRashis[house] ?? "";
      const rashiNumber = rashiName ? rashiIndexFromApiName(rashiName) + 1 : house;
      svg.append("text")
        .attr("x", lx)
        .attr("y", ly)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .attr("paint-order", "stroke")
        .style("font-size", "10px")
        .style("font-weight", "700")
        .style("stroke", "var(--chart-bg)")
        .style("stroke-width", "2px")
        .style("fill", "var(--text-secondary, #475569)")
        .style("opacity", 0.85)
        .text(rashiNumber);
    }

    // ── Helper to calculate clean planet positions within house centroids ─────
    const getPlanetOffset = (i: number, count: number, house: number) => {
      const isHouse1 = house === 1;
      const yShift = isHouse1 ? 6 : 0;
      const isCorner = [2, 3, 5, 6, 8, 9, 11, 12].includes(house);

      if (count <= 1) {
        return { offsetX: 0, offsetY: yShift };
      }
      if (count === 2) {
        const offset = isCorner ? 11 : 13;
        return { offsetX: 0, offsetY: (i === 0 ? -offset : offset) + yShift };
      }

      // 3+ planets: 2-column balanced grid
      const col = i % 2 === 0 ? 0 : 1;
      const rowIndex = Math.floor(i / 2);
      const itemsInCol = Math.ceil(count / 2) - (col === 1 && count % 2 !== 0 ? 1 : 0);
      const colSpacing = isCorner ? (count >= 4 ? 14 : 16) : (count >= 5 ? 24 : 20);
      const offsetX = col === 0 ? -colSpacing : colSpacing;

      let offsetY = 0;
      if (itemsInCol === 1) {
        offsetY = 0;
      } else if (itemsInCol === 2) {
        offsetY = rowIndex === 0 ? (isCorner ? -13 : -15) : (isCorner ? 13 : 15);
      } else {
        offsetY = (rowIndex - 1) * (isCorner ? 22 : 26);
      }
      return { offsetX, offsetY: offsetY + yShift };
    };

    // ── Compute each planet's rendered position ──────────────────────────
    const planetPositions: Record<string, [number, number]> = {};
    for (const [houseStr, ps] of Object.entries(housePlanets)) {
      const house = Number(houseStr);
      const [px, py] = toPoint(HOUSE_CENTROIDS[house]);
      const count = ps.length;
      ps.forEach((planet, i) => {
        const { offsetX, offsetY } = getPlanetOffset(i, count, house);
        // Clamp to ensure planets stay inside SVG bounds
        const clampedX = Math.max(16, Math.min(size - 16, px + offsetX));
        const clampedY = Math.max(16, Math.min(size - 16, py + offsetY));
        planetPositions[planet.planet] = [clampedX, clampedY];
      });
    }

    // ── Aspect lines ─────────────────────────────────────────────────────
    for (const asp of aspects) {
      const from = planetPositions[asp.from_planet];
      const to = planetPositions[asp.to_planet];
      if (!from || !to) continue;
      const color = ASPECT_COLORS[asp.aspect_type] ?? ASPECT_DEFAULT_COLOR;
      const touchesActive = activePlanet && (asp.from_planet === activePlanet || asp.to_planet === activePlanet);
      svg
        .append("line")
        .attr("x1", from[0])
        .attr("y1", from[1])
        .attr("x2", to[0])
        .attr("y2", to[1])
        .style("stroke", color)
        .style("stroke-width", touchesActive ? 2 : 1)
        .style("stroke-dasharray", touchesActive ? "none" : "3 3")
        .style("stroke-opacity", touchesActive ? 0.9 : 0.25)
        .style("pointer-events", "none");
    }

    // ── Planet glyphs + names ─────────────────────────────────────────────
    for (const [houseStr, ps] of Object.entries(housePlanets)) {
      const house = Number(houseStr);
      const [px, py] = toPoint(HOUSE_CENTROIDS[house]);
      const houseCount = ps.length;
      const dense = houseCount >= 3;

      ps.forEach((planet, i) => {
        const abbrev = PLANET_ABBREV[planet.planet] ?? planet.planet.slice(0, 2);
        const symbol = PLANET_SYMBOLS[planet.planet] ?? "";
        const isAsc = house === 1 && i === 0;
        const isActive = activePlanet === planet.planet;
        const ascColor = "var(--chart-ascendant)";

        const { offsetX, offsetY } = getPlanetOffset(i, houseCount, house);
        const itemX = px + offsetX;
        const itemY = py + offsetY;

        const g = svg.append("g")
          .attr("transform", `translate(${itemX}, ${itemY})`)
          .style("cursor", onPlanetHover || onPlanetClick ? "pointer" : "default")
          .on("mouseenter", () => onPlanetHover?.(planet.planet))
          .on("mouseleave", () => onPlanetHover?.(null))
          .on("click", () => onPlanetClick?.(planet.planet));

        g.append("title")
          .text(`${planet.planet}${planet.is_retrograde ? " (Retrograde)" : ""} — ${planet.rashi}${planet.rashi_degree !== undefined ? ` ${planet.rashi_degree.toFixed(2)}°` : ""}`);

        if (isActive) {
          g.append("circle")
            .attr("cx", 0)
            .attr("cy", -2)
            .attr("r", 15)
            .style("fill", "var(--accent)")
            .style("opacity", 0.22);
        }

        const labelFontSize = dense ? 9.5 : 11.5;
        const symbolFontSize = dense ? 8.5 : 10;
        const degreeY = dense ? 10 : 12;
        const degreeFontSize = dense ? 7.5 : 8;

        // Render symbol, abbreviation, and retrograde marker inside a single text node with tspans
        const textNode = g.append("text")
          .attr("x", 0)
          .attr("y", 0)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "central");

        if (symbol) {
          textNode.append("tspan")
            .style("font-size", `${symbolFontSize}px`)
            .style("font-weight", "800")
            .style("fill", isAsc ? ascColor : "var(--text-primary)")
            .text(`${symbol} `);
        }

        textNode.append("tspan")
          .style("font-size", `${labelFontSize}px`)
          .style("font-weight", "800")
          .style("fill", isAsc ? ascColor : "var(--text-primary)")
          .text(abbrev);

        if (planet.is_retrograde) {
          textNode.append("tspan")
            .attr("dx", "3")
            .style("font-size", "8px")
            .style("font-weight", "800")
            .style("fill", "var(--danger-400, #f87171)")
            .text("R");
        }

        if (planet.rashi_degree !== undefined) {
          g.append("text")
            .attr("x", 0)
            .attr("y", degreeY)
            .attr("text-anchor", "middle")
            .style("font-size", `${degreeFontSize}px`)
            .style("font-weight", "600")
            .style("fill", "var(--text-secondary)")
            .style("opacity", 0.9)
            .text(`${planet.rashi_degree.toFixed(1)}°`);
        }
      });
    }

    // ── Ascendant marker (Lagna) ─────────────────────────────────────────────
    const [ascX, ascY] = toPoint(HOUSE_CENTROIDS[1]);
    svg.append("text")
      .attr("x", ascX)
      .attr("y", ascY - 24)
      .attr("text-anchor", "middle")
      .style("font-size", "9.5px")
      .style("font-weight", "800")
      .style("fill", "var(--chart-ascendant)")
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
    <div className="flex w-full min-w-0 flex-col items-center gap-2">
      {title && (
        <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-800 dark:text-cyan-300">
          {chartTitle}
        </h3>
      )}
      <svg
        ref={svgRef}
        viewBox={`-20 -20 ${size + 40} ${size + 40}`}
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-auto max-w-[400px] mx-auto block shrink-0"
        role="img"
        aria-label={`North Indian square chart: ${chartTitle} showing ${ascendant.rashi} ascendant with ${planets.length} planets`}
      />
      {/* Legend */}
      {showFullNames && (
        <div
          className="flex flex-wrap justify-center gap-1.5 pt-1 text-xs"
          aria-label="Planet legend"
        >
          {planets.map((p) => {
            const abbrev = PLANET_ABBREV[p.planet] ?? p.planet.slice(0, 2);
            const full = p.planet;
            const isActive = activePlanet === p.planet;
            const isClickable = Boolean(onPlanetHover || onPlanetClick);

            const Content = (
              <>
                <span className="font-bold" style={{ color: isActive ? "var(--accent-text)" : "var(--accent)" }}>
                  {abbrev}
                </span>
                <span className="font-medium" style={{ color: isActive ? "var(--accent-text)" : "var(--text-primary)" }}>
                  {full}
                </span>
                {p.is_retrograde && (
                  <span className="font-bold" style={{ color: isActive ? "var(--accent-text)" : "var(--danger-400, #f87171)" }}>
                    (R)
                  </span>
                )}
              </>
            );

            const buttonStyle = {
              backgroundColor: isActive ? "var(--accent)" : "var(--bg-card)",
              color: isActive ? "var(--accent-text)" : "var(--text-primary)",
              border: `1px solid ${isActive ? "var(--accent)" : "var(--border-primary)"}`,
            };

            if (isClickable) {
              return (
                <button
                  key={p.planet}
                  type="button"
                  className="flex items-center gap-1 rounded-md px-2 py-0.5 text-xs transition hover:border-[var(--border-hover)]"
                  style={buttonStyle}
                  onMouseEnter={() => onPlanetHover?.(p.planet)}
                  onMouseLeave={() => onPlanetHover?.(null)}
                  onClick={() => onPlanetClick?.(p.planet)}
                >
                  {Content}
                </button>
              );
            }

            return (
              <div
                key={p.planet}
                className="flex items-center gap-1 rounded-md px-2 py-0.5 text-xs border"
                style={buttonStyle}
              >
                {Content}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
