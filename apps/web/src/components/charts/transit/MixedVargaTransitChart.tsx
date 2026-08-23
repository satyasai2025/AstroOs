"use client";

import { useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";
import {
  RASHIS,
  rashiIndexFromApiName,
  PLANET_ABBREV,
  PLANET_SYMBOLS,
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
  scaleFromCenter,
  interpolatePoint,
} from "@/lib/chartGeometry";

/** Midpoint of the edge two house polygons share (their two common
 * vertices) — e.g. house1 and house2 share the edge from the Lagna apex
 * to the upper-left rhombus corner. Used to sweep a transit planet across
 * the FULL width of its house cell (entry edge → exit edge) as its degree
 * advances, rather than nudging it a few pixels from the centroid. */
function sharedEdgeMidpoint(
  polyA: [number, number][],
  polyB: [number, number][],
): [number, number] | null {
  const shared = polyA.filter((pa) => polyB.some((pb) => pb[0] === pa[0] && pb[1] === pa[1]));
  if (shared.length < 2) return null;
  const cx = shared.reduce((s, p) => s + p[0], 0) / shared.length;
  const cy = shared.reduce((s, p) => s + p[1], 0) / shared.length;
  return [cx, cy];
}

/**
 * Per-planet gradient stops for a stylized "sphere" look on the outer
 * (transit) ring — no external image assets, just radial-gradient fills
 * approximating each body's real coloring (Sun's flare, Moon's grey,
 * Mars's rust, Saturn's tan + ring, the lunar nodes' smoky dark).
 */
const PLANET_SPHERE: Record<
  string,
  { stops: [string, string, string]; glow: string; hasRing?: boolean }
> = {
  sun: { stops: ["#fff6d6", "#ffb703", "#c9560a"], glow: "#ff8c00" },
  moon: { stops: ["#f4f4f6", "#c8c9cf", "#8d8f97"], glow: "#d9d9e0" },
  mars: { stops: ["#ffb199", "#c1440e", "#5e1c07"], glow: "#c1440e" },
  mercury: { stops: ["#e2ddd2", "#9c958a", "#5a5650"], glow: "#9c958a" },
  jupiter: { stops: ["#f2ddb8", "#c98a4b", "#7a4a20"], glow: "#c98a4b" },
  venus: { stops: ["#fff2d0", "#e8c27a", "#a3763a"], glow: "#e8c27a" },
  saturn: { stops: ["#f4e5c2", "#cf9f5f", "#8a6530"], glow: "#cf9f5f", hasRing: true },
  rahu: { stops: ["#5a5470", "#241f33", "#0a0812"], glow: "#4a3f66" },
  ketu: { stops: ["#6b3a3a", "#301414", "#0f0505"], glow: "#5a2a2a" },
};

interface RingPlanet {
  planet: string;
  rashi: string;
  /** Degree within the rashi [0, 30) — drives the live "creep" position
   * within a house cell as the animation advances. */
  rashi_degree?: number;
  is_retrograde?: boolean;
}

interface MixedVargaTransitChartProps {
  ascendant: { rashi: string };
  /** Inner ring — static natal D1 placements. */
  natalPlanets: RingPlanet[];
  /** Outer ring — live transit placements, re-rendered every animation frame. */
  transitPlanets: RingPlanet[];
  size?: number;
  onPlanetHover?: (planet: string | null) => void;
  onPlanetClick?: (planet: string) => void;
  activePlanet?: string | null;
}

/** House-from-lagna for a rashi, given the natal ascendant's rashi. */
function houseFor(rashi: string, ascRashi: string): number {
  const ascIdx = rashiIndexFromApiName(ascRashi);
  const pIdx = rashiIndexFromApiName(rashi);
  return ((pIdx - ascIdx + 12) % 12) + 1;
}

function groupByHouse(planets: RingPlanet[], ascRashi: string): Record<number, RingPlanet[]> {
  const map: Record<number, RingPlanet[]> = {};
  for (const p of planets) {
    const house = houseFor(p.rashi, ascRashi);
    (map[house] ??= []).push(p);
  }
  return map;
}

/**
 * Concentric "Mixed Varga" style chart: the natal D1 on an inner ring,
 * live transit planets on an outer ring, sharing the same 12 house
 * divisions (both drawn from the same construction lines, just scaled
 * around the shared center) — the layout used by Classical Vedic System's
 * Mixed Varga view. Outer-ring planets are nudged from their house's
 * centroid toward its outermost vertex by rashi_degree/30, so a planet
 * visibly creeps across its house cell as the animation loop advances
 * its longitude, then snaps to the next cell on a real sign change —
 * instead of sitting frozen at the centroid between keyframes.
 */
export function MixedVargaTransitChart({
  ascendant,
  natalPlanets,
  transitPlanets,
  size = 440,
  onPlanetHover,
  onPlanetClick,
  activePlanet,
}: MixedVargaTransitChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  const natalByHouse = useMemo(
    () => groupByHouse(natalPlanets, ascendant.rashi),
    [natalPlanets, ascendant.rashi],
  );
  const transitByHouse = useMemo(
    () => groupByHouse(transitPlanets, ascendant.rashi),
    [transitPlanets, ascendant.rashi],
  );
  const houseRashis = useMemo(() => {
    const ascIdx = rashiIndexFromApiName(ascendant.rashi);
    const map: Record<number, string> = {};
    for (let h = 1; h <= 12; h++) map[h] = RASHIS[(ascIdx + h - 1) % 12];
    return map;
  }, [ascendant.rashi]);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const INNER_SCALE = 0.52;
    const pad = size * 0.1;
    const squareSize = size - pad * 2;
    const toPoint = ([ux, uy]: [number, number]): [number, number] => [
      pad + (ux / 100) * squareSize,
      pad + (uy / 100) * squareSize,
    ];
    const toInnerPoint = (p: [number, number]): [number, number] => toPoint(scaleFromCenter(p, INNER_SCALE));

    svg.append("rect").attr("width", size).attr("height", size).attr("rx", 12).style("fill", "var(--chart-bg)");

    // ── Sphere gradients + glow filter for the outer (transit) ring ──────
    const defs = svg.append("defs");
    for (const [planet, spec] of Object.entries(PLANET_SPHERE)) {
      const grad = defs.append("radialGradient")
        .attr("id", `sphere-${planet}`)
        .attr("cx", "35%").attr("cy", "30%").attr("r", "75%");
      grad.append("stop").attr("offset", "0%").attr("stop-color", spec.stops[0]);
      grad.append("stop").attr("offset", "55%").attr("stop-color", spec.stops[1]);
      grad.append("stop").attr("offset", "100%").attr("stop-color", spec.stops[2]);
    }
    const glow = defs.append("filter").attr("id", "sphere-glow").attr("x", "-100%").attr("y", "-100%").attr("width", "300%").attr("height", "300%");
    glow.append("feGaussianBlur").attr("stdDeviation", "3").attr("result", "blur");
    const glowMerge = glow.append("feMerge");
    glowMerge.append("feMergeNode").attr("in", "blur");
    glowMerge.append("feMergeNode").attr("in", "SourceGraphic");

    const lineColor = "var(--chart-border)";
    const chartText = "var(--chart-text)";
    const accentColor = "var(--accent)";
    const ascColor = "var(--chart-ascendant)";
    const transitColor = "var(--chart-transit, #f97316)";

    function drawConstruction(project: (p: [number, number]) => [number, number], strokeScale: number) {
      const [pA, pB, pC, pD] = [A, B, C, D].map(project);
      const [pMAB, pMBC, pMCD, pMDA] = [M_AB, M_BC, M_CD, M_DA].map(project);

      svg.append("polygon")
        .attr("points", [pA, pB, pC, pD].map((p) => p.join(",")).join(" "))
        .style("fill", "none").style("stroke", lineColor).style("stroke-width", 2 * strokeScale);

      svg.append("line").attr("x1", pA[0]).attr("y1", pA[1]).attr("x2", pC[0]).attr("y2", pC[1])
        .style("stroke", lineColor).style("stroke-width", 1 * strokeScale);
      svg.append("line").attr("x1", pB[0]).attr("y1", pB[1]).attr("x2", pD[0]).attr("y2", pD[1])
        .style("stroke", lineColor).style("stroke-width", 1 * strokeScale);

      svg.append("polygon")
        .attr("points", [pMAB, pMBC, pMCD, pMDA].map((p) => p.join(",")).join(" "))
        .style("fill", "none").style("stroke", lineColor).style("stroke-width", 1 * strokeScale);
    }

    // ── Outer ring construction (full size) ──────────────────────────────
    drawConstruction(toPoint, 1);
    // ── Inner ring construction (scaled down, same center) ───────────────
    drawConstruction(toInnerPoint, 0.75);

    // Scale factor relative to the original 440px design size — every
    // font-size/stroke-width below is multiplied by this so labels stay
    // legible (not fixed-tiny) as the chart is rendered larger.
    const fs = size / 440;

    // ── Ring labels ────────────────────────────────────────────────────
    svg.append("text").attr("x", pad).attr("y", pad * 0.5)
      .style("font-size", `${14 * fs}px`).style("font-weight", "700").style("fill", transitColor)
      .text("Outer: Transit");
    svg.append("text").attr("x", pad).attr("y", pad * 0.5 + 18 * fs)
      .style("font-size", `${14 * fs}px`).style("font-weight", "700").style("fill", accentColor)
      .text("Inner: Natal Chart");

    // ── Rashi number labels (outer ring only, avoids clutter) — the
    // absolute zodiac sign number (Mesha/Aries=1 … Meena/Pisces=12), not
    // the house-from-Lagna number, and no rashi-name text alongside it.
    for (let house = 1; house <= 12; house++) {
      const [lx, ly] = toPoint(HOUSE_NUMBER_UNIT_POS[house]);
      const rashiName = houseRashis[house] ?? "";
      const rashiNumber = rashiName ? rashiIndexFromApiName(rashiName) + 1 : house;
      svg.append("text")
        .attr("x", lx).attr("y", ly)
        .attr("text-anchor", "middle").attr("dominant-baseline", "central")
        .attr("paint-order", "stroke")
        .style("font-size", `${13 * fs}px`).style("stroke", "var(--chart-bg)").style("stroke-width", `${3 * fs}px`)
        .style("fill", chartText).style("opacity", 0.75)
        .text(rashiNumber);
    }

    // ── Inner ring: natal planets, static at house centroids ─────────────
    // Glyph scale and line spacing must shrink by INNER_SCALE too (not
    // just by the chart-wide `fs` factor) — the inner ring's positions
    // are already compressed to 52% of the outer ring, so text sized as
    // if it belonged to the full-size ring is proportionally oversized
    // for its shrunken house cells and collides with its neighbors.
    const innerGlyphScale = 0.55 * INNER_SCALE * 1.6; // net ≈0.46, tuned to stay legible
    for (const [houseStr, ps] of Object.entries(natalByHouse)) {
      const house = Number(houseStr);
      const [px, py] = toInnerPoint(HOUSE_CENTROIDS[house]);
      const denseInner = ps.length >= 4;
      const lineHeight = (denseInner ? 13 : 15) * fs * INNER_SCALE;
      ps.forEach((planet, i) => {
        const offsetY = (i - (ps.length - 1) / 2) * lineHeight;
        renderGlyph(svg, planet, px, py + offsetY, house === 1 && i === 0, false, innerGlyphScale);
      });
    }

    // ── Outer ring: transit planets sweep across the FULL house cell as
    // rashi_degree advances 0→30 — from the edge shared with the previous
    // house (entry, degree≈0) to the edge shared with the next house
    // (exit, degree≈30) — instead of a small nudge from the centroid.
    // This is what makes motion actually visible frame to frame instead
    // of an imperceptible sub-pixel creep; the planet still only jumps to
    // a different house on a real sign change, so it stays astronomically
    // honest, not decorative.
    for (const [houseStr, ps] of Object.entries(transitByHouse)) {
      const house = Number(houseStr);
      const prevHouse = ((house - 2 + 12) % 12) + 1;
      const nextHouse = (house % 12) + 1;
      const entryPt = sharedEdgeMidpoint(HOUSE_UNIT_POLYGONS[house], HOUSE_UNIT_POLYGONS[prevHouse]) ?? HOUSE_CENTROIDS[house];
      const exitPt = sharedEdgeMidpoint(HOUSE_UNIT_POLYGONS[house], HOUSE_UNIT_POLYGONS[nextHouse]) ?? HOUSE_CENTROIDS[house];
      // Denser houses get smaller spheres and tighter spacing so 2-3
      // planets sharing a house (e.g. a conjunction) don't overlap.
      const sphereScale = ps.length >= 3 ? 0.6 : ps.length === 2 ? 0.78 : 1;
      const lineHeight = (size / 440) * 30 * sphereScale;
      ps.forEach((planet, i) => {
        const degreeFrac = Math.max(0, Math.min(1, (planet.rashi_degree ?? 0) / 30));
        // Inset the sweep (15%–85% instead of the full 0%–100%) so a
        // planet near 0° or 30° doesn't sit right on top of the shared
        // edge with the neighboring house — which is exactly where that
        // house's own sphere/label can be sitting too. Keeps the motion
        // clearly visible across the cell without the boundary collision.
        const insetFrac = 0.15 + degreeFrac * 0.7;
        const driftPt = interpolatePoint(entryPt, exitPt, insetFrac);
        const [px, py] = toPoint(driftPt);
        const offsetY = (i - (ps.length - 1) / 2) * lineHeight;
        renderPlanetSphere(svg, planet, px, py + offsetY, sphereScale);
      });
    }

    function renderGlyph(
      svgSel: d3.Selection<SVGSVGElement, unknown, null, undefined>,
      planet: RingPlanet,
      x: number,
      y: number,
      isAsc: boolean,
      isTransitRing: boolean,
      scale: number,
    ) {
      const abbrev = PLANET_ABBREV[planet.planet] ?? planet.planet.slice(0, 2);
      const symbol = PLANET_SYMBOLS[planet.planet] ?? "";
      const isActive = activePlanet === planet.planet;
      const color = isAsc ? ascColor : isTransitRing ? transitColor : accentColor;

      const g = svgSel.append("g")
        .attr("transform", `translate(${x}, ${y})`)
        .style("cursor", onPlanetHover || onPlanetClick ? "pointer" : "default")
        .on("mouseenter", () => onPlanetHover?.(planet.planet))
        .on("mouseleave", () => onPlanetHover?.(null))
        .on("click", () => onPlanetClick?.(planet.planet));

      g.append("title").text(
        `${planet.planet}${planet.is_retrograde ? " (Retrograde)" : ""} — ${planet.rashi}${
          planet.rashi_degree !== undefined ? ` ${planet.rashi_degree.toFixed(2)}°` : ""
        } (${isTransitRing ? "transit" : "natal"})`,
      );

      if (isActive) {
        g.append("circle").attr("cx", 0).attr("cy", -2 * fs).attr("r", 10 * scale * fs)
          .style("fill", color).style("opacity", 0.2);
      }

      const fontSize = 13 * scale * fs;
      g.append("text")
        .attr("x", -10 * scale * fs).attr("y", 0)
        .attr("text-anchor", "middle").attr("dominant-baseline", "central")
        .style("font-size", `${fontSize}px`).style("fill", color)
        .text(symbol);

      g.append("text")
        .attr("x", 5 * scale * fs).attr("y", 0)
        .attr("text-anchor", "middle").attr("dominant-baseline", "central")
        .style("font-size", `${fontSize + 1}px`).style("font-weight", isActive ? "900" : "bold")
        .style("fill", color)
        .text(abbrev);

      if (planet.is_retrograde) {
        g.append("text")
          .attr("x", 18 * scale * fs).attr("y", 0)
          .attr("text-anchor", "start").attr("dominant-baseline", "central")
          .style("font-size", `${10 * scale * fs}px`).style("fill", ascColor)
          .text("R");
      }
    }

    /** Stylized textured sphere for a transit-ring planet — a gradient-fill
     * circle (Saturn additionally gets a tilted ring ellipse), a soft glow,
     * and a small abbreviation + retrograde marker underneath. */
    function renderPlanetSphere(
      svgSel: d3.Selection<SVGSVGElement, unknown, null, undefined>,
      planet: RingPlanet,
      x: number,
      y: number,
      scale: number,
    ) {
      const key = planet.planet.toLowerCase();
      const spec = PLANET_SPHERE[key];
      const isActive = activePlanet === planet.planet;
      const radius = (size / 440) * 14 * scale;

      const g = svgSel.append("g")
        .attr("transform", `translate(${x}, ${y})`)
        .style("cursor", onPlanetHover || onPlanetClick ? "pointer" : "default")
        .on("mouseenter", () => onPlanetHover?.(planet.planet))
        .on("mouseleave", () => onPlanetHover?.(null))
        .on("click", () => onPlanetClick?.(planet.planet));

      g.append("title").text(
        `${planet.planet}${planet.is_retrograde ? " (Retrograde)" : ""} — ${planet.rashi}${
          planet.rashi_degree !== undefined ? ` ${planet.rashi_degree.toFixed(2)}°` : ""
        } (transit)`,
      );

      if (isActive) {
        g.append("circle").attr("r", radius * 1.6)
          .style("fill", spec?.glow ?? transitColor).style("opacity", 0.25);
      }

      if (spec) {
        if (spec.hasRing) {
          g.append("ellipse")
            .attr("rx", radius * 1.7).attr("ry", radius * 0.55)
            .attr("transform", "rotate(-18)")
            .style("fill", "none").style("stroke", spec.stops[1]).style("stroke-width", radius * 0.18)
            .style("opacity", 0.85);
        }
        g.append("circle")
          .attr("r", radius)
          .style("fill", `url(#sphere-${key})`)
          .style("filter", "url(#sphere-glow)")
          .style("stroke", isActive ? "#fff" : "none")
          .style("stroke-width", 1.5);
      } else {
        // Fallback for any planet name not in PLANET_SPHERE (shouldn't
        // happen for the standard 9 grahas) — plain accent-colored dot.
        g.append("circle").attr("r", radius).style("fill", transitColor);
      }

      const abbrev = PLANET_ABBREV[planet.planet] ?? planet.planet.slice(0, 2);
      const labelFontSize = 13 * scale * fs;
      g.append("text")
        .attr("x", 0).attr("y", radius + 14 * scale * fs)
        .attr("text-anchor", "middle").attr("dominant-baseline", "central")
        .attr("paint-order", "stroke")
        .style("font-size", `${labelFontSize}px`).style("font-weight", isActive ? "900" : "700")
        .style("stroke", "var(--chart-bg)").style("stroke-width", `${3 * fs}px`)
        .style("fill", chartText)
        .text(abbrev + (planet.is_retrograde ? " (R)" : ""));
    }
  }, [size, natalByHouse, transitByHouse, houseRashis, ascendant.rashi, activePlanet, onPlanetHover, onPlanetClick]);

  return (
    <div
      className="flex flex-col items-center gap-2"
      role="img"
      aria-label={`Mixed transit chart: natal ${ascendant.rashi} ascendant on the inner ring, live transit planets on the outer ring`}
    >
      <svg
        ref={svgRef}
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="h-auto w-full"
        role="img"
        aria-label="Concentric natal + transit chart"
      />
    </div>
  );
}
