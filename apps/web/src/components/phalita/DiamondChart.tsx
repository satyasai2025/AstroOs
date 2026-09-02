'use client';


import React from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import { VargaChartData } from "@/lib/vargaCalculator";

interface Props {
  vargaData: VargaChartData;
}

export const DiamondChart: React.FC<Props> = ({ vargaData }) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const chartBg = isDark ? "#09111e" : "#f8fafc";
  const frameBorder = isDark ? "#1e2c40" : "#334155";
  const innerLine = isDark ? "#283950" : "#94a3b8";
  const rashiColor = isDark ? "#4ade80" : "#047857"; // Emerald green rashi numbers
  const planetColor = isDark ? "#fca5a5" : "#b91c1c"; // Deep red/maroon planets
  const lagnaColor = isDark ? "#e879f9" : "#7e22ce"; // Purple/Magenta Lagna (As)

  const h = vargaData.houses;

  // Helper to render planets inside a house safely
  const renderHousePlanets = (houseNum: number, baseX: number, baseY: number) => {
    const planets = h[houseNum]?.planets || [];
    if (planets.length === 0) return null;

    if (planets.length === 1) {
      return (
        <g>
          <text x={baseX} y={baseY} fill={planetColor} fontSize="20" fontWeight="800" textAnchor="middle">
            {planets[0].glyph}
          </text>
        </g>
      );
    }

    if (planets.length === 2) {
      return (
        <g>
          <text x={baseX} y={baseY - 12} fill={planetColor} fontSize="17" fontWeight="800" textAnchor="middle">
            {planets[0].glyph}
          </text>
          <text x={baseX} y={baseY + 12} fill={planetColor} fontSize="17" fontWeight="800" textAnchor="middle">
            {planets[1].glyph}
          </text>
        </g>
      );
    }

    // 3+ planets: 2-column cluster
    return (
      <g>
        {planets.map((p, idx) => {
          const col = idx % 2 === 0 ? -16 : 16;
          const row = Math.floor(idx / 2) * 20 - 10;
          return (
            <text key={idx} x={baseX + col} y={baseY + row} fill={planetColor} fontSize="15" fontWeight="800" textAnchor="middle">
              {p.glyph}
            </text>
          );
        })}
      </g>
    );
  };

  return (
    <div className="w-full flex flex-col items-center">
      {/* Top Header Strip */}
      <div className="w-full max-w-[320px] flex justify-between items-center text-xs font-sans font-bold text-slate-800 dark:text-slate-200 mb-1 px-1">
        <span>Natal Chart</span>
        <span className="text-sm font-extrabold text-cyan-600 dark:text-cyan-400">
          {vargaData.vargaCode} — {vargaData.vargaName}
        </span>
      </div>

      {/* SVG Chart Box */}
      <div className={`w-full max-w-[320px] aspect-square p-1 rounded-sm border shadow-md transition-colors ${
        isDark ? "bg-[#09111e] border-[#1e2c40]" : "bg-[#f8fafc] border-slate-300"
      }`}>
        <svg
          viewBox="0 0 400 400"
          className="w-full h-full font-sans select-none"
        >
          {/* Background fill */}
          <rect x="0" y="0" width="400" height="400" fill={chartBg} />

          {/* 1. Outer Square Frame */}
          <rect
            x="4"
            y="4"
            width="392"
            height="392"
            fill="none"
            stroke={frameBorder}
            strokeWidth="3"
          />

          {/* 2. Main Diagonals */}
          <line x1="4" y1="4" x2="396" y2="396" stroke={innerLine} strokeWidth="1.8" />
          <line x1="396" y1="4" x2="4" y2="396" stroke={innerLine} strokeWidth="1.8" />

          {/* 3. Inner Diamond */}
          <polygon
            points="200,4 396,200 200,396 4,200"
            fill="none"
            stroke={innerLine}
            strokeWidth="2.0"
          />

          {/* ── 🌟 CENTER RASHI NUMBERS (Around (200,200) intersection) ── */}
          <text x="200" y="188" fill={rashiColor} fontSize="14" fontWeight="bold" textAnchor="middle">
            {h[1]?.rashiNumber}
          </text>
          <text x="180" y="205" fill={rashiColor} fontSize="14" fontWeight="bold" textAnchor="middle">
            {h[4]?.rashiNumber}
          </text>
          <text x="220" y="205" fill={rashiColor} fontSize="14" fontWeight="bold" textAnchor="middle">
            {h[10]?.rashiNumber}
          </text>
          <text x="200" y="224" fill={rashiColor} fontSize="14" fontWeight="bold" textAnchor="middle">
            {h[7]?.rashiNumber}
          </text>

          {/* ── 🌟 HOUSE 1 (Top Center Rhombus - Lagna) ── */}
          <g>
            <text x="200" y="115" fill={lagnaColor} fontSize="28" fontWeight="800" textAnchor="middle">
              As
            </text>
            {renderHousePlanets(1, 200, 150)}
          </g>

          {/* ── 🌟 HOUSE 2 (Top Left Triangle) ── */}
          <g>
            <text x="95" y="105" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[2]?.rashiNumber}
            </text>
            {renderHousePlanets(2, 95, 60)}
          </g>

          {/* ── 🌟 HOUSE 3 (Left Top Triangle) ── */}
          <g>
            <text x="105" y="115" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[3]?.rashiNumber}
            </text>
            {renderHousePlanets(3, 45, 125)}
          </g>

          {/* ── 🌟 HOUSE 4 (Left Center Rhombus) ── */}
          <g>
            {renderHousePlanets(4, 115, 205)}
          </g>

          {/* ── 🌟 HOUSE 5 (Left Bottom Triangle) ── */}
          <g>
            <text x="105" y="295" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[5]?.rashiNumber}
            </text>
            {renderHousePlanets(5, 45, 285)}
          </g>

          {/* ── 🌟 HOUSE 6 (Bottom Left Triangle) ── */}
          <g>
            <text x="95" y="305" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[6]?.rashiNumber}
            </text>
            {renderHousePlanets(6, 95, 345)}
          </g>

          {/* ── 🌟 HOUSE 7 (Bottom Center Rhombus) ── */}
          <g>
            {renderHousePlanets(7, 200, 295)}
          </g>

          {/* ── 🌟 HOUSE 8 (Bottom Right Triangle) ── */}
          <g>
            <text x="305" y="305" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[8]?.rashiNumber}
            </text>
            {renderHousePlanets(8, 305, 345)}
          </g>

          {/* ── 🌟 HOUSE 9 (Right Bottom Triangle) ── */}
          <g>
            <text x="295" y="295" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[9]?.rashiNumber}
            </text>
            {renderHousePlanets(9, 355, 285)}
          </g>

          {/* ── 🌟 HOUSE 10 (Right Center Rhombus) ── */}
          <g>
            {renderHousePlanets(10, 285, 205)}
          </g>

          {/* ── 🌟 HOUSE 11 (Right Upper Triangle) ── */}
          <g>
            <text x="295" y="115" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[11]?.rashiNumber}
            </text>
            {renderHousePlanets(11, 355, 125)}
          </g>

          {/* ── 🌟 HOUSE 12 (Top Right Triangle) ── */}
          <g>
            <text x="305" y="105" fill={rashiColor} fontSize="13" fontWeight="bold" textAnchor="middle">
              {h[12]?.rashiNumber}
            </text>
            {renderHousePlanets(12, 305, 60)}
          </g>
        </svg>
      </div>

      {/* Bottom Subtitle Strip */}
      <div className="w-full max-w-[320px] flex justify-between items-center text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-1 px-1">
        <span>Vimshopaka Weight: {vargaData.weight} pts</span>
        <span className="font-bold">{vargaData.vargaCode}</span>
      </div>
    </div>
  );
};
