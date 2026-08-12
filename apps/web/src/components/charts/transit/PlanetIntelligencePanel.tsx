/**
 * AstroOS — Animated Mixed Varga / Transit: Planet Intelligence Panel
 *
 * Displays detailed astrological information for a selected planet:
 * - Longitude, Rashi, Nakshatra, Pada
 * - Motion state (direct/retrograde/station)
 * - Combustion, Dignity
 * - Classical properties (Guna, Tatva, Gender, Mobility)
 * - D9 Navamsha
 * - Houses (natal, transit from Moon/Lagna)
 * - Aspects
 */

"use client";

import { useMemo } from "react";
import type { TransitTimelineKeyframe, TransitTimelinePlanet } from "@/lib/transitTimelineTypes";

interface PlanetIntelligencePanelProps {
  planetName: string;
  currentTime: string;
  natalChart: {
    ascendant: { rashi: string };
    planets: Array<{
      planet: string;
      rashi: string;
      house_number: number;
      nakshatra: string;
      pada: number;
    }>;
  };
}

export function PlanetIntelligencePanel({
  planetName,
  currentTime,
  natalChart,
}: PlanetIntelligencePanelProps) {
  // In a real implementation, this would fetch exact position data
  // For now, show placeholder structure
  const planetData = useMemo(() => {
    // Find natal planet data
    const natalPlanet = natalChart.planets.find((p) => p.planet === planetName);
    
    return {
      planet: planetName,
      longitude: 0, // Would come from exact API call
      rashi: natalPlanet?.rashi || "aries",
      rashi_degree: 0,
      rashi_minute: 0,
      rashi_second: 0,
      nakshatra: natalPlanet?.nakshatra || "",
      pada: natalPlanet?.pada || 1,
      degree_in_nakshatra: 0,
      motion: "direct" as const,
      speed: 0,
      is_combust: false,
      combustion_orb: null as number | null,
      dignity: null as string | null,
      is_exalted: false,
      is_debilitated: false,
      is_own_sign: false,
      guna: "sattvic" as const,
      tatva: "fire" as const,
      gender: "male" as const,
      mobility: "chara" as const,
      kalapurusha_house: 1,
      navamsha_rashi: "",
      navamsha_lord: "",
      natal_house: natalPlanet?.house_number || 1,
      transit_house_from_moon: 1,
      transit_house_from_lagna: 1,
      aspects_cast: [],
      aspects_received: [],
    };
  }, [planetName, natalChart]);

  const motionColor = planetData.motion === "direct" ? "var(--text-success)" :
                      planetData.motion === "retrograde" ? "var(--text-warning)" :
                      "var(--text-muted)";

  const dignityColor = planetData.is_exalted ? "var(--text-success)" :
                       planetData.is_debilitated ? "var(--text-danger)" :
                       planetData.is_own_sign ? "var(--accent)" :
                       "var(--text-secondary)";

  return (
    <div className="glass-card p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        {planetData.planet.charAt(0).toUpperCase() + planetData.planet.slice(1)} Intelligence
      </h3>

      <div className="space-y-3 text-xs">
        {/* Position */}
        <div className="space-y-1.5">
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Longitude</span>
            <span className="font-mono" style={{ color: "var(--text-primary)" }}>
              {planetData.rashi_degree.toFixed(2)}° {planetData.rashi_minute}' {planetData.rashi_second}"
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Rashi</span>
            <span style={{ color: "var(--text-primary)" }}>
              {planetData.rashi.charAt(0).toUpperCase() + planetData.rashi.slice(1)}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Nakshatra</span>
            <span style={{ color: "var(--text-primary)" }}>
              {planetData.nakshatra} - Pada {planetData.pada}
            </span>
          </div>
        </div>

        {/* Motion */}
        <div className="space-y-1.5 border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Motion</span>
            <span style={{ color: motionColor }}>
              {planetData.motion.charAt(0).toUpperCase() + planetData.motion.slice(1)}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Speed</span>
            <span className="font-mono" style={{ color: "var(--text-primary)" }}>
              {planetData.speed.toFixed(2)}°/day
            </span>
          </div>
        </div>

        {/* Dignity & Combustion */}
        <div className="space-y-1.5 border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Dignity</span>
            <span style={{ color: dignityColor }}>
              {planetData.dignity || "Neutral"}
            </span>
          </div>
          {planetData.is_combust && (
            <div className="flex justify-between">
              <span style={{ color: "var(--text-muted)" }}>Combustion</span>
              <span style={{ color: "var(--text-warning)" }}>
                Yes (orb: {planetData.combustion_orb?.toFixed(1)}°)
              </span>
            </div>
          )}
        </div>

        {/* Classical Properties */}
        <div className="space-y-1.5 border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Guna</span>
            <span style={{ color: "var(--text-primary)" }}>
              {planetData.guna.charAt(0).toUpperCase() + planetData.guna.slice(1)}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Tatva</span>
            <span style={{ color: "var(--text-primary)" }}>
              {planetData.tatva.charAt(0).toUpperCase() + planetData.tatva.slice(1)}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Gender</span>
            <span style={{ color: "var(--text-primary)" }}>
              {planetData.gender.charAt(0).toUpperCase() + planetData.gender.slice(1)}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Mobility</span>
            <span style={{ color: "var(--text-primary)" }}>
              {planetData.mobility.charAt(0).toUpperCase() + planetData.mobility.slice(1)}
            </span>
          </div>
        </div>

        {/* D9 Navamsha */}
        {planetData.navamsha_rashi && (
          <div className="space-y-1.5 border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
            <div className="flex justify-between">
              <span style={{ color: "var(--text-muted)" }}>Navamsha</span>
              <span style={{ color: "var(--text-primary)" }}>
                {planetData.navamsha_rashi}
              </span>
            </div>
            {planetData.navamsha_lord && (
              <div className="flex justify-between">
                <span style={{ color: "var(--text-muted)" }}>Navamsha Lord</span>
                <span style={{ color: "var(--text-primary)" }}>
                  {planetData.navamsha_lord}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Houses */}
        <div className="space-y-1.5 border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Natal House</span>
            <span style={{ color: "var(--text-primary)" }}>{planetData.natal_house}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Transit (from Moon)</span>
            <span style={{ color: "var(--text-primary)" }}>{planetData.transit_house_from_moon}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--text-muted)" }}>Transit (from Lagna)</span>
            <span style={{ color: "var(--text-primary)" }}>{planetData.transit_house_from_lagna}</span>
          </div>
        </div>
      </div>
    </div>
  );
}