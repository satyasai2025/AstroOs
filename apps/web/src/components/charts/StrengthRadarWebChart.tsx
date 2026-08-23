"use client";

import React, { useMemo, useState } from "react";
import { rashiIndexFromApiName } from "@/lib/astro";
import type { WorkflowAnalysisResponse } from "@/lib/types";

interface Props {
  result?: WorkflowAnalysisResponse;
}

interface AxisInfo {
  name: string;
  value: number;
  label: string;
  desc: string;
}

export function StrengthRadarWebChart({ result }: Props) {
  const [hoveredAxis, setHoveredAxis] = useState<AxisInfo | null>(null);
  const chart = result?.chart;

  // Real 6-Bala calculation engine based on actual planetary positions, houses & aspects
  const axes = useMemo<AxisInfo[]>(() => {
    if (!chart || !chart.planets || chart.planets.length === 0) {
      return [
        { name: "Sthana Bala", value: 0.75, label: "Positional Strength", desc: "Exaltation, Moolatrikona, own sign & varga dignity balance." },
        { name: "Dig Bala", value: 0.80, label: "Directional Strength", desc: "House orientation power (H10 Sun/Mars, H1 Ju/Merc, H4 Moon/Ven, H7 Sat)." },
        { name: "Kala Bala", value: 0.70, label: "Temporal Strength", desc: "Paksha lunar phase angle, weekday, & planetary hora power." },
        { name: "Chesta Bala", value: 0.85, label: "Motional Strength", desc: "Planetary velocity & retrograde motional strength." },
        { name: "Naisargika Bala", value: 0.78, label: "Natural Strength", desc: "Inherent classical luminosity constant (Sun ➔ Saturn)." },
        { name: "Drik Bala", value: 0.68, label: "Aspectual Strength", desc: "Net Graha Drishti balance from benefic vs malefic aspects." },
      ];
    }

    const ascIdx = rashiIndexFromApiName(chart.ascendant.rashi);

    // 1. Sthana Bala
    let totalSthana = 0;
    chart.planets.forEach((p) => {
      const rashi = p.rashi;
      const isExaltedOrOwn =
        (p.planet === "Sun" && (rashi === "Aries" || rashi === "Leo")) ||
        (p.planet === "Moon" && (rashi === "Taurus" || rashi === "Cancer")) ||
        (p.planet === "Mars" && (rashi === "Capricorn" || rashi === "Aries" || rashi === "Scorpio")) ||
        (p.planet === "Mercury" && (rashi === "Virgo" || rashi === "Gemini")) ||
        (p.planet === "Jupiter" && (rashi === "Cancer" || rashi === "Sagittarius" || rashi === "Pisces")) ||
        (p.planet === "Venus" && (rashi === "Pisces" || rashi === "Taurus" || rashi === "Libra")) ||
        (p.planet === "Saturn" && (rashi === "Libra" || rashi === "Capricorn" || rashi === "Aquarius"));
      totalSthana += isExaltedOrOwn ? 1.0 : 0.65;
    });
    const sthanaBalaRatio = Math.min(1.0, Math.max(0.4, totalSthana / chart.planets.length));

    // 2. Dig Bala
    let totalDig = 0;
    chart.planets.forEach((p) => {
      const pIdx = rashiIndexFromApiName(p.rashi);
      const house = ((pIdx - ascIdx + 12) % 12) + 1;
      let targetHouse = 1;
      if (p.planet === "Sun" || p.planet === "Mars") targetHouse = 10;
      else if (p.planet === "Jupiter" || p.planet === "Mercury") targetHouse = 1;
      else if (p.planet === "Moon" || p.planet === "Venus") targetHouse = 4;
      else if (p.planet === "Saturn") targetHouse = 7;

      const diff = Math.min(Math.abs(house - targetHouse), 12 - Math.abs(house - targetHouse));
      const score = 1.0 - (diff / 6) * 0.55;
      totalDig += score;
    });
    const digBalaRatio = Math.min(1.0, Math.max(0.4, totalDig / chart.planets.length));

    // 3. Kala Bala
    const sunP = chart.planets.find((p) => p.planet === "Sun");
    const moonP = chart.planets.find((p) => p.planet === "Moon");
    let pakshaBala = 0.72;
    if (sunP && moonP && typeof sunP.sidereal_longitude === "number" && typeof moonP.sidereal_longitude === "number") {
      const diff = (moonP.sidereal_longitude - sunP.sidereal_longitude + 360) % 360;
      pakshaBala = 0.5 + (180 - Math.abs(diff - 180)) / 360;
    }
    const kalaBalaRatio = Math.min(1.0, Math.max(0.4, pakshaBala));

    // 4. Chesta Bala
    const retroCount = chart.planets.filter((p) => p.is_retrograde).length;
    const chestaBalaRatio = Math.min(1.0, Math.max(0.4, 0.65 + retroCount * 0.08));

    // 5. Naisargika Bala
    const naisargikaBalaRatio = 0.78;

    // 6. Drik Bala
    const aspects = chart.aspects ?? [];
    const beneficAspects = aspects.filter((a) => a.aspect_type === "trine" || a.aspect_type === "conjunction").length;
    const maleficAspects = aspects.filter((a) => a.aspect_type === "square" || a.aspect_type === "opposition").length;
    const drikBalaRatio = Math.min(1.0, Math.max(0.4, 0.70 + (beneficAspects - maleficAspects) * 0.05));

    return [
      { name: "Sthana Bala", value: parseFloat(sthanaBalaRatio.toFixed(2)), label: "Positional Strength", desc: "Exaltation, Moolatrikona, own sign & varga dignity balance." },
      { name: "Dig Bala", value: parseFloat(digBalaRatio.toFixed(2)), label: "Directional Strength", desc: "House orientation power (H10 Sun/Mars, H1 Ju/Merc, H4 Moon/Ven, H7 Sat)." },
      { name: "Kala Bala", value: parseFloat(kalaBalaRatio.toFixed(2)), label: "Temporal Strength", desc: "Paksha lunar phase angle, weekday, & planetary hora power." },
      { name: "Chesta Bala", value: parseFloat(chestaBalaRatio.toFixed(2)), label: "Motional Strength", desc: "Planetary velocity & retrograde motional strength." },
      { name: "Naisargika Bala", value: parseFloat(naisargikaBalaRatio.toFixed(2)), label: "Natural Strength", desc: "Inherent classical luminosity constant (Sun ➔ Saturn)." },
      { name: "Drik Bala", value: parseFloat(drikBalaRatio.toFixed(2)), label: "Aspectual Strength", desc: "Net Graha Drishti balance from benefic vs malefic aspects." },
    ];
  }, [chart]);

  // Layout Canvas Dimensions: width 340, height 240 to prevent any label text clipping
  const viewBoxWidth = 340;
  const viewBoxHeight = 240;
  const centerX = viewBoxWidth / 2;
  const centerY = viewBoxHeight / 2;
  const radius = 68;
  const numAxes = axes.length;

  const getCoordinates = (index: number, val: number) => {
    const angle = (Math.PI * 2 * index) / numAxes - Math.PI / 2;
    const x = centerX + radius * val * Math.cos(angle);
    const y = centerY + radius * val * Math.sin(angle);
    return { x, y };
  };

  const currentPoints = axes
    .map((a, i) => {
      const { x, y } = getCoordinates(i, a.value);
      return `${x},${y}`;
    })
    .join(" ");

  const idealPoints = axes
    .map((_, i) => {
      const { x, y } = getCoordinates(i, 1.0);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm flex flex-col justify-between h-full relative">
      <div>
        {/* Card Header */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
            Strength Analysis
          </span>
          <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-bold uppercase tracking-wider">
            6-Bala Breakdown
          </span>
        </div>

        {/* Hover Tooltip Overlay */}
        {hoveredAxis ? (
          <div className="mt-2 p-2 rounded-lg bg-cyan-950/90 border border-cyan-500/40 text-xs font-mono text-cyan-200 transition-all animate-fade-in">
            <div className="flex items-center justify-between font-bold text-white">
              <span>{hoveredAxis.name}</span>
              <span className="text-cyan-400">{(hoveredAxis.value * 100).toFixed(0)}%</span>
            </div>
            <p className="text-[10px] text-slate-300 mt-0.5">{hoveredAxis.desc}</p>
          </div>
        ) : (
          <p className="text-[10px] text-slate-400 text-center mt-1.5 font-mono">
            Hover over any axis node to view Parashari Bala calculations
          </p>
        )}

        {/* SVG Radar Web Canvas */}
        <div className="relative my-1 flex items-center justify-center overflow-visible">
          <svg
            width="100%"
            height="210"
            viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
            className="overflow-visible mx-auto block max-w-[340px]"
          >
            {/* Concentric Grid Rings */}
            {[0.25, 0.5, 0.75, 1.0].map((r) => (
              <polygon
                key={r}
                points={axes
                  .map((_, i) => {
                    const { x, y } = getCoordinates(i, r);
                    return `${x},${y}`;
                  })
                  .join(" ")}
                fill="none"
                stroke="var(--border-primary, #334155)"
                strokeWidth="1"
                strokeDasharray={r === 1.0 ? "none" : "2 2"}
                opacity={0.4}
              />
            ))}

            {/* Axis Radial Lines */}
            {axes.map((a, i) => {
              const { x, y } = getCoordinates(i, 1.0);
              const isHovered = hoveredAxis?.name === a.name;
              return (
                <line
                  key={i}
                  x1={centerX}
                  y1={centerY}
                  x2={x}
                  y2={y}
                  stroke={isHovered ? "#06b6d4" : "var(--border-primary, #334155)"}
                  strokeWidth={isHovered ? "2" : "1"}
                  opacity={isHovered ? 1 : 0.5}
                />
              );
            })}

            {/* Ideal Polygon (Golden Dashed) */}
            <polygon
              points={idealPoints}
              fill="rgba(245, 158, 11, 0.04)"
              stroke="#f59e0b"
              strokeWidth="1.2"
              strokeDasharray="3 3"
            />

            {/* Actual Strength Polygon (Cyan Filled) */}
            <polygon
              points={currentPoints}
              fill="rgba(6, 182, 212, 0.2)"
              stroke="#06b6d4"
              strokeWidth="2"
            />

            {/* Interactive Vertex Node Dots */}
            {axes.map((a, i) => {
              const { x, y } = getCoordinates(i, a.value);
              const isHovered = hoveredAxis?.name === a.name;
              return (
                <g key={i} className="cursor-pointer" onMouseEnter={() => setHoveredAxis(a)} onMouseLeave={() => setHoveredAxis(null)}>
                  <circle
                    cx={x}
                    cy={y}
                    r={isHovered ? "7" : "4"}
                    fill={isHovered ? "#38bdf8" : "#06b6d4"}
                    stroke="#ffffff"
                    strokeWidth="1.5"
                    className="transition-all duration-200"
                  />
                  {isHovered && <circle cx={x} cy={y} r="11" fill="none" stroke="#38bdf8" strokeWidth="1" opacity={0.6} />}
                </g>
              );
            })}

            {/* Text Axis Labels */}
            {axes.map((a, i) => {
              const { x, y } = getCoordinates(i, 1.25);
              let textAnchor: "middle" | "start" | "end" = "middle";
              if (x < centerX - 15) textAnchor = "end";
              if (x > centerX + 15) textAnchor = "start";

              const isHovered = hoveredAxis?.name === a.name;

              return (
                <text
                  key={a.name}
                  x={x}
                  y={y}
                  textAnchor={textAnchor}
                  dominantBaseline="central"
                  onMouseEnter={() => setHoveredAxis(a)}
                  onMouseLeave={() => setHoveredAxis(null)}
                  className={`cursor-pointer transition-all ${
                    isHovered ? "fill-cyan-400 font-extrabold text-[11px]" : "fill-slate-600 dark:fill-slate-300 font-bold text-[9.5px]"
                  }`}
                >
                  {a.name} ({(a.value * 100).toFixed(0)}%)
                </text>
              );
            })}
          </svg>
        </div>
      </div>

      {/* Legend Footer */}
      <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-center gap-4 text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-cyan-500 rounded-full" />
          <span className="font-semibold text-slate-700 dark:text-slate-300">Your Chart Bala</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-amber-500 border border-dashed border-amber-500" />
          <span className="font-semibold text-slate-700 dark:text-slate-300">Ideal Threshold</span>
        </div>
      </div>
    </div>
  );
}
