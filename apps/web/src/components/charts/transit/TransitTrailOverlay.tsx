/**
 * AstroOS — Animated Mixed Varga / Transit: Trail Overlay
 *
 * Renders the historical path of transit planets on the North Indian chart.
 * Shows planet movement including retrograde loops and station points.
 */

"use client";

import { useMemo } from "react";
import type { InterpolatedPlanetState, TrailPoint } from "@/lib/transitTimelineTypes";

interface TransitTrailOverlayProps {
  /** Trail points for all planets */
  trail: TrailPoint[];
  /** Currently selected planet (null = show all) */
  selectedPlanet: string | null;
  /** Trail duration in hours */
  trailDurationHours: number;
  /** Chart dimensions */
  chartSize: number;
  /** Chart center coordinates */
  centerX: number;
  centerY: number;
  /** Chart radius */
  radius: number;
}

export function TransitTrailOverlay({
  trail,
  selectedPlanet,
  trailDurationHours,
  chartSize,
  centerX,
  centerY,
  radius,
}: TransitTrailOverlayProps) {
  // Filter trail by planet and time
  const visibleTrail = useMemo(() => {
    let filtered = trail;

    // Filter by planet
    if (selectedPlanet) {
      filtered = filtered.filter((p) => p.planet === selectedPlanet);
    }

    // Filter by time (keep only recent points)
    if (trailDurationHours > 0) {
      const cutoff = Date.now() - trailDurationHours * 60 * 60 * 1000;
      filtered = filtered.filter((p) => new Date(p.timestamp).getTime() >= cutoff);
    }

    return filtered;
  }, [trail, selectedPlanet, trailDurationHours]);

  // Convert longitude to chart coordinates
  const longitudeToChart = (longitude: number) => {
    // Normalize longitude to 0-360
    const normalized = ((longitude % 360) + 360) % 360;

    // Convert to angle (0° = top of chart, clockwise)
    const angle = (normalized / 360) * 2 * Math.PI - Math.PI / 2;

    // Calculate position on chart circle
    const x = centerX + radius * 0.85 * Math.cos(angle);
    const y = centerY + radius * 0.85 * Math.sin(angle);

    return { x, y };
  };

  // Group trail points by planet
  const trailsByPlanet = useMemo(() => {
    const grouped = new Map<string, typeof visibleTrail>();
    visibleTrail.forEach((point) => {
      if (!grouped.has(point.planet)) {
        grouped.set(point.planet, []);
      }
      grouped.get(point.planet)!.push(point);
    });
    return grouped;
  }, [visibleTrail]);

  // Planet colors
  const planetColors: Record<string, string> = {
    sun: "#FFA500",
    moon: "#C0C0C0",
    mars: "#FF0000",
    mercury: "#00FF00",
    jupiter: "#FFD700",
    venus: "#FF69B4",
    saturn: "#8B4513",
    rahu: "#FF4500",
    ketu: "#9400D3",
  };

  if (visibleTrail.length === 0) {
    return null;
  }

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      width={chartSize}
      height={chartSize}
      style={{ zIndex: 10 }}
    >
      <defs>
        {/* Gradients for each planet */}
        {Array.from(trailsByPlanet.keys()).map((planet) => (
          <linearGradient
            key={`gradient-${planet}`}
            id={`trail-gradient-${planet}`}
            x1="0%"
            y1="0%"
            x2="100%"
            y2="0%"
          >
            <stop offset="0%" stopColor={planetColors[planet] || "#FFFFFF"} stopOpacity="0.1" />
            <stop offset="100%" stopColor={planetColors[planet] || "#FFFFFF"} stopOpacity="0.8" />
          </linearGradient>
        ))}
      </defs>

      {/* Render trail for each planet */}
      {Array.from(trailsByPlanet.entries()).map(([planet, points]) => {
        if (points.length < 2) return null;

        // Create path from trail points
        const pathData = points
          .map((point, index) => {
            const pos = longitudeToChart(point.longitude);
            const command = index === 0 ? "M" : "L";
            return `${command} ${pos.x.toFixed(2)} ${pos.y.toFixed(2)}`;
          })
          .join(" ");

        const color = planetColors[planet] || "#FFFFFF";

        return (
          <g key={`trail-${planet}`}>
            {/* Trail path with gradient */}
            <path
              d={pathData}
              stroke={`url(#trail-gradient-${planet})`}
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Trail dots (show every Nth point) */}
            {points
              .filter((_, index) => index % 5 === 0) // Show every 5th point
              .map((point, index) => {
                const pos = longitudeToChart(point.longitude);
                return (
                  <circle
                    key={`dot-${planet}-${index}`}
                    cx={pos.x}
                    cy={pos.y}
                    r="2"
                    fill={color}
                    opacity="0.6"
                  />
                );
              })}

            {/* Current position marker */}
            {points.length > 0 && (
              <circle
                cx={longitudeToChart(points[points.length - 1].longitude).x}
                cy={longitudeToChart(points[points.length - 1].longitude).y}
                r="4"
                fill={color}
                opacity="0.9"
              >
                <animate
                  attributeName="r"
                  values="3;5;3"
                  dur="2s"
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  values="0.7;1;0.7"
                  dur="2s"
                  repeatCount="indefinite"
                />
              </circle>
            )}
          </g>
        );
      })}
    </svg>
  );
}