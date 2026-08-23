"use client";

import { useMemo } from "react";
import {
  rashiIndexFromApiName,
  PLANET_SYMBOLS,
} from "@/lib/astro";

const PLANET_COLORS: Record<string, string> = {
  Sun: "#F5A623",
  Moon: "#94a3b8",
  Mars: "#EF4444",
  Mercury: "#10B981",
  Jupiter: "#F59E0B",
  Venus: "#EC4899",
  Saturn: "#6366F1",
  Rahu: "#8B5CF6",
  Ketu: "#8B5CF6",
  Ascendant: "#06B6D4",
};

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

interface SouthIndianChartProps {
  /** Title shown in center of chart (e.g. "D1 — Rashi Chart"). */
  title?: string;
  /** Ascendant position. */
  ascendant: AscendantPlacement;
  /** Planets to render in the chart. */
  planets: PlanetPlacement[];
  /** Optional: size in pixels (default 400). */
  size?: number;
  /** Whether this is a varga chart. */
  isVarga?: boolean;
  /** Varga divisor (e.g. 9 for D9). */
  vargaDivisor?: number;
  /** Called with a planet name on hover-in, and null on hover-out. */
  onPlanetHover?: (planet: string | null) => void;
  /** Called with a planet name when clicked. */
  onPlanetClick?: (planet: string) => void;
  /** Currently hovered or selected planet. */
  activePlanet?: string | null;
  /** Called with a house number on hover-in, and null on hover-out. */
  onHouseHover?: (house: number | null) => void;
  /** Called with a house number when clicked. */
  onHouseClick?: (house: number) => void;
  /** Currently hovered or selected house. */
  activeHouse?: number | null;
}

/**
 * South Indian 4x4 Grid layout specification:
 * Clockwise fixed signs starting at top-left:
 * Row 0: Pisces (11), Aries (0), Taurus (1), Gemini (2)
 * Col 3: Cancer (3), Leo (4)
 * Row 3: Virgo (5), Libra (6), Scorpio (7), Sagittarius (8) (from right to left)
 * Col 0: Capricorn (9), Aquarius (10) (from bottom to top)
 */
interface SignCellConfig {
  rashiIndex: number;
  rashiName: string;
  rashiShort: string;
  col: number;
  row: number;
}

const SIGN_CELLS: SignCellConfig[] = [
  { rashiIndex: 11, rashiName: "Pisces", rashiShort: "Pis", col: 0, row: 0 },
  { rashiIndex: 0,  rashiName: "Aries", rashiShort: "Ari", col: 1, row: 0 },
  { rashiIndex: 1,  rashiName: "Taurus", rashiShort: "Tau", col: 2, row: 0 },
  { rashiIndex: 2,  rashiName: "Gemini", rashiShort: "Gem", col: 3, row: 0 },
  { rashiIndex: 3,  rashiName: "Cancer", rashiShort: "Can", col: 3, row: 1 },
  { rashiIndex: 4,  rashiName: "Leo", rashiShort: "Leo", col: 3, row: 2 },
  { rashiIndex: 5,  rashiName: "Virgo", rashiShort: "Vir", col: 3, row: 3 },
  { rashiIndex: 6,  rashiName: "Libra", rashiShort: "Lib", col: 2, row: 3 },
  { rashiIndex: 7,  rashiName: "Scorpio", rashiShort: "Sco", col: 1, row: 3 },
  { rashiIndex: 8,  rashiName: "Sagittarius", rashiShort: "Sag", col: 0, row: 3 },
  { rashiIndex: 9,  rashiName: "Capricorn", rashiShort: "Cap", col: 0, row: 2 },
  { rashiIndex: 10, rashiName: "Aquarius", rashiShort: "Aqu", col: 0, row: 1 },
];

export function SouthIndianChart({
  title = "D1 Rashi",
  ascendant,
  planets,
  size = 400,
  isVarga = false,
  vargaDivisor,
  onPlanetHover,
  onPlanetClick,
  activePlanet,
  onHouseHover,
  onHouseClick,
  activeHouse,
}: SouthIndianChartProps) {
  const ascIdx = useMemo(
    () => rashiIndexFromApiName(ascendant.rashi),
    [ascendant.rashi],
  );

  // Group planets by sign index (0..11)
  const planetsBySign = useMemo(() => {
    const map: Record<number, PlanetPlacement[]> = {};
    for (const p of planets) {
      const idx = rashiIndexFromApiName(p.rashi);
      if (!map[idx]) map[idx] = [];
      map[idx].push(p);
    }
    return map;
  }, [planets]);

  const cellSize = size / 4;

  return (
    <div className="relative w-full select-none flex justify-center">
      <svg
        viewBox={`-20 -20 ${size + 40} ${size + 40}`}
        preserveAspectRatio="xMidYMid meet"
        className="w-full h-auto max-w-[400px] mx-auto block shrink-0 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800"
        style={{
          backgroundColor: "var(--chart-bg, #ffffff)",
          fontFamily: "var(--font-inter, sans-serif)",
        }}
      >
        {/* Background */}
        <rect
          x={-20}
          y={-20}
          width={size + 40}
          height={size + 40}
          className="fill-white dark:fill-slate-900"
        />

        {/* 12 Sign Boxes */}
        {SIGN_CELLS.map((cell) => {
          const x = cell.col * cellSize;
          const y = cell.row * cellSize;
          const isLagnaSign = cell.rashiIndex === ascIdx;
          const houseNumber = ((cell.rashiIndex - ascIdx + 12) % 12) + 1;
          const isHouseActive = activeHouse === houseNumber;
          const cellPlanets = planetsBySign[cell.rashiIndex] || [];

          return (
            <g
              key={cell.rashiIndex}
              className="transition-colors"
              onMouseEnter={() => onHouseHover?.(houseNumber)}
              onMouseLeave={() => onHouseHover?.(null)}
              onClick={() => onHouseClick?.(houseNumber)}
              style={{ cursor: onHouseClick || onHouseHover ? "pointer" : "default" }}
            >
              {/* Cell Box */}
              <rect
                x={x}
                y={y}
                width={cellSize}
                height={cellSize}
                fill={
                  isHouseActive
                    ? "rgba(6, 182, 212, 0.12)"
                    : isLagnaSign
                      ? "rgba(245, 158, 11, 0.06)"
                      : "transparent"
                }
                stroke="var(--chart-border, #cbd5e1)"
                strokeWidth={1.2}
              />

              {/* Lagna Double Diagonal Marking if Lagna Sign */}
              {isLagnaSign && (
                <g opacity={0.35}>
                  <line
                    x1={x}
                    y1={y}
                    x2={x + cellSize * 0.4}
                    y2={y}
                    stroke="var(--accent, #06b6d4)"
                    strokeWidth={2}
                  />
                  <line
                    x1={x}
                    y1={y}
                    x2={x}
                    y2={y + cellSize * 0.4}
                    stroke="var(--accent, #06b6d4)"
                    strokeWidth={2}
                  />
                  <line
                    x1={x}
                    y1={y}
                    x2={x + cellSize * 0.35}
                    y2={y + cellSize * 0.35}
                    stroke="var(--accent, #06b6d4)"
                    strokeWidth={1.5}
                  />
                </g>
              )}

              {/* Sign Header & House Number Badge */}
              <text
                x={x + 6}
                y={y + 14}
                className="text-[10px] font-bold uppercase tracking-wider fill-slate-400 dark:fill-slate-500"
              >
                {cell.rashiShort}
              </text>

              {/* House Number from Lagna */}
              <text
                x={x + cellSize - 6}
                y={y + 14}
                textAnchor="end"
                className={`text-[10px] font-bold ${
                  isLagnaSign
                    ? "fill-cyan-500 font-extrabold"
                    : "fill-slate-400 dark:fill-slate-500"
                }`}
              >
                {isLagnaSign ? "ASC (H1)" : `H${houseNumber}`}
              </text>

              {/* Planets inside this Sign */}
              <g transform={`translate(${x + 6}, ${y + 24})`}>
                {cellPlanets.map((p, pIdx) => {
                  const isPlanetActive = activePlanet === p.planet;
                  const rowY = pIdx * 15;
                  const pColor = PLANET_COLORS[p.planet] || "#ea580c";

                  return (
                    <g
                      key={p.planet}
                      className="cursor-pointer transition hover:opacity-80"
                      transform={`translate(0, ${rowY})`}
                      onMouseEnter={(e) => {
                        e.stopPropagation();
                        onPlanetHover?.(p.planet);
                      }}
                      onMouseLeave={(e) => {
                        e.stopPropagation();
                        onPlanetHover?.(null);
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        onPlanetClick?.(p.planet);
                      }}
                    >
                      {/* Active Planet Highlight Pill */}
                      {isPlanetActive && (
                        <rect
                          x={-3}
                          y={0}
                          width={cellSize - 6}
                          height={14}
                          rx={3}
                          fill="rgba(6, 182, 212, 0.2)"
                          stroke="#06b6d4"
                          strokeWidth={1}
                        />
                      )}

                      {/* Planet Symbol */}
                      <text
                        x={3}
                        y={10}
                        fontSize="10px"
                        fontWeight="bold"
                        fill={pColor}
                      >
                        {PLANET_SYMBOLS[p.planet] ?? ""}
                      </text>

                      {/* Planet Name */}
                      <text
                        x={15}
                        y={10}
                        fontSize="9.5px"
                        fontWeight={isPlanetActive ? "700" : "600"}
                        className="fill-slate-800 dark:fill-slate-100"
                      >
                        {p.planet.slice(0, 3)}
                        {p.is_retrograde && (
                          <tspan fill="#ef4444" fontWeight="800" fontSize="8.5px" dx="2">
                            R
                          </tspan>
                        )}
                      </text>

                      {/* Planet Degree if available */}
                      {typeof p.rashi_degree === "number" && (
                        <text
                          x={cellSize - 4}
                          y={10}
                          textAnchor="end"
                          fontSize="8.5px"
                          fontFamily="monospace"
                          className="fill-slate-500 dark:fill-slate-400 font-semibold"
                        >
                          {Math.floor(p.rashi_degree)}°{Math.floor((p.rashi_degree % 1) * 60)}′
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </g>
          );
        })}

        {/* Center 2x2 Box */}
        <g transform={`translate(${cellSize}, ${cellSize})`}>
          <rect
            x={0}
            y={0}
            width={cellSize * 2}
            height={cellSize * 2}
            className="fill-slate-50/80 dark:fill-slate-900/60"
            stroke="var(--chart-border, #cbd5e1)"
            strokeWidth={1.5}
          />

          <g transform={`translate(${cellSize}, ${cellSize * 0.6})`} textAnchor="middle">
            {/* Title */}
            <text
              y={0}
              className="text-sm font-bold fill-slate-900 dark:fill-slate-100"
            >
              {title}
            </text>

            <text
              y={18}
              className="text-[11px] font-semibold fill-cyan-600 dark:fill-cyan-400"
            >
              Lagna: {ascendant.rashi} {ascendant.rashi_degree?.toFixed(2)}°
            </text>

            <text
              y={34}
              className="text-[10px] font-medium fill-slate-500 dark:fill-slate-400"
            >
              South Indian Fixed-Sign Grid
            </text>

            {isVarga && vargaDivisor && (
              <text
                y={48}
                className="text-[10px] font-mono fill-amber-600 dark:fill-amber-400"
              >
                Varga Divisor: 1/{vargaDivisor}
              </text>
            )}
          </g>
        </g>
      </svg>
    </div>
  );
}
