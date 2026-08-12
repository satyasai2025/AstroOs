/**
 * AstroOS — Animated Mixed Varga / Transit: Main Animated View
 *
 * Combines:
 * - Natal D1 chart (static background)
 * - Transit planets (animated overlay)
 * - Time Controller
 * - Panchanga panel
 * - Planet Intelligence panel
 */

"use client";

import { useState, useMemo } from "react";
import { MixedVargaTransitChart } from "@/components/charts/transit/MixedVargaTransitChart";
import { TransitTimeline } from "@/components/charts/transit/TransitTimeline";
import { PlanetIntelligencePanel } from "@/components/charts/transit/PlanetIntelligencePanel";
import { TransitTrailOverlay } from "@/components/charts/transit/TransitTrailOverlay";
import type { D1ChartResponse, TransitResponse, TransitPatternsResponse } from "@/lib/types";
import type { InterpolatedPlanetState, TransitEvent, PanchangaKeyframe, TrailPoint, PlaybackSpeed, TimelinePreset } from "@/lib/transitTimelineTypes";

interface AnimatedTransitViewProps {
  /** Natal chart data */
  natalChart: D1ChartResponse;
  /** Real transit-to-natal aspects + Sade Sati/Ashtama Shani for the
   * currently displayed moment (bucketed to ~15min, not per-frame). */
  patterns?: TransitPatternsResponse;
  isPatternsLoading?: boolean;
  /** Transit timeline data */
  timelineData: {
    keyframes: any[];
    events: TransitEvent[];
    timelineStart: string;
    timelineEnd: string;
  } | null;
  /** Animation state */
  currentTime: string;
  isPlaying: boolean;
  speed: PlaybackSpeed;
  selectedPlanet: string | null;
  showTrail: boolean;
  showEvents: boolean;
  /** Interpolated planets for current frame */
  interpolatedPlanets: InterpolatedPlanetState[];
  /** Current Panchanga */
  currentPanchanga: PanchangaKeyframe | null;
  /** Loading state */
  isLoading: boolean;
  /** Trail points */
  trailPoints: TrailPoint[];
  /** Actions */
  onPlay: () => void;
  onPause: () => void;
  onToggle: () => void;
  onSeek: (time: string) => void;
  onStepForward: (minutes: number) => void;
  onStepBackward: (minutes: number) => void;
  onSetSpeed: (speed: PlaybackSpeed) => void;
  onJumpToEvent: (event: TransitEvent) => void;
  onSetSelectedPlanet: (planet: string | null) => void;
  onToggleTrail: () => void;
  onToggleEvents: () => void;
  onLoadTimeline: (params: any) => void;
  onLoadPreset?: (preset: TimelinePreset) => void;
  onJumpToDate?: (iso: string) => void;
  onLoadCustomRange?: (startIso: string, endIso: string, intervalMinutes?: number) => void;
}

export function AnimatedTransitView({
  natalChart,
  patterns,
  isPatternsLoading,
  timelineData,
  currentTime,
  isPlaying,
  speed,
  selectedPlanet,
  showTrail,
  showEvents,
  interpolatedPlanets,
  currentPanchanga,
  isLoading,
  trailPoints,
  onPlay,
  onPause,
  onToggle,
  onSeek,
  onStepForward,
  onStepBackward,
  onSetSpeed,
  onJumpToEvent,
  onSetSelectedPlanet,
  onToggleTrail,
  onToggleEvents,
  onLoadTimeline,
  onLoadPreset,
  onJumpToDate,
  onLoadCustomRange,
}: AnimatedTransitViewProps) {
  // Prepare natal planets for static background
  const natalPlanets = useMemo(() => {
    return natalChart.planets.map((p) => ({
      planet: p.planet,
      rashi: p.rashi,
      house_number: p.house_number,
      is_retrograde: p.is_retrograde,
      rashi_degree: p.rashi_degree,
    }));
  }, [natalChart.planets]);

  // Prepare transit planets for animated overlay
  const transitPlanets = useMemo(() => {
    return interpolatedPlanets.map((p) => ({
      planet: p.planet,
      rashi: p.rashi,
      house_number: undefined,
      is_retrograde: p.is_retrograde,
      rashi_degree: p.rashi_degree,
    }));
  }, [interpolatedPlanets]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Loading animated transit...
        </div>
      </div>
    );
  }

  if (!timelineData) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No timeline data loaded
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Chart — full width for maximum clarity */}
      <div className="glass-card flex flex-col items-center p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Animated Transit
        </h2>
        <div className="relative w-full max-w-[820px]">
          <MixedVargaTransitChart
            ascendant={natalChart.ascendant}
            natalPlanets={natalPlanets}
            transitPlanets={transitPlanets}
            size={780}
            onPlanetClick={onSetSelectedPlanet}
            onPlanetHover={onSetSelectedPlanet}
            activePlanet={selectedPlanet}
          />
          {/* Transit Trail Overlay */}
          {showTrail && trailPoints.length > 1 && (
            <TransitTrailOverlay
              trail={trailPoints}
              selectedPlanet={selectedPlanet}
              trailDurationHours={24}
              chartSize={780}
              centerX={390}
              centerY={390}
              radius={351}
            />
          )}
        </div>
        <div className="mt-4 text-xs" style={{ color: "var(--text-muted)" }}>
          Natal D1 (static) • Transit overlay (animated)
        </div>
      </div>

      {/* Playback controls — right below the chart */}
      <TransitTimeline
        currentTime={currentTime}
        timelineStart={timelineData.timelineStart}
        timelineEnd={timelineData.timelineEnd}
        isPlaying={isPlaying}
        speed={speed as any}
        events={timelineData.events}
        showEvents={showEvents}
        selectedPlanet={selectedPlanet}
        isLoading={isLoading}
        onPlay={onPlay}
        onPause={onPause}
        onToggle={onToggle}
        onSeek={onSeek}
        onStepForward={onStepForward}
        onStepBackward={onStepBackward}
        onSetSpeed={onSetSpeed}
        onJumpToEvent={onJumpToEvent}
        onSetSelectedPlanet={onSetSelectedPlanet}
        onToggleEvents={onToggleEvents}
        onLoadPreset={onLoadPreset}
        onJumpToDate={onJumpToDate}
        onLoadCustomRange={onLoadCustomRange}
      />

      {/* Panchanga + Planet Intelligence — below the chart, side by side */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Panchanga Panel */}
        {currentPanchanga && (
          <div className="glass-card p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
              Panchanga
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span style={{ color: "var(--text-muted)" }}>Tithi</span>
                <span style={{ color: "var(--text-primary)" }}>
                  {currentPanchanga.tithi.name} ({currentPanchanga.tithi.paksha})
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "var(--text-muted)" }}>Nakshatra</span>
                <span style={{ color: "var(--text-primary)" }}>
                  {currentPanchanga.nakshatra.nakshatra} - Pad {currentPanchanga.nakshatra.pada}
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "var(--text-muted)" }}>Yoga</span>
                <span style={{ color: "var(--text-primary)" }}>{currentPanchanga.yoga.name}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "var(--text-muted)" }}>Karana</span>
                <span style={{ color: "var(--text-primary)" }}>{currentPanchanga.karana.name}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: "var(--text-muted)" }}>Vara</span>
                <span style={{ color: "var(--text-primary)" }}>{currentPanchanga.vara.name}</span>
              </div>
            </div>
          </div>
        )}

        {/* Planet Intelligence Panel */}
        {selectedPlanet && (
          <PlanetIntelligencePanel
            planetName={selectedPlanet}
            currentTime={currentTime}
            natalChart={natalChart}
          />
        )}
      </div>

      {/* Detailed Analysis — real transit-to-natal aspects + Sade Sati /
          Ashtama Shani for the currently displayed moment, same underlying
          data as the Overview tab's aspect table (not fabricated AI text). */}
      <div className="glass-card p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Detailed Analysis
        </h3>
        {isPatternsLoading && !patterns ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Loading transit-to-natal aspects…
          </p>
        ) : !patterns ? (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No aspect data available for this moment.
          </p>
        ) : (
          <div className="space-y-3 text-xs">
            {(patterns.sade_sati.is_active || patterns.ashtama_shani.is_active) && (
              <div className="flex flex-wrap gap-2">
                {patterns.sade_sati.is_active && (
                  <span
                    className="rounded px-2 py-1 font-medium"
                    style={{ background: "var(--status-danger-soft, rgba(239,68,68,.12))", color: "var(--status-danger)" }}
                  >
                    Sade Sati — {patterns.sade_sati.phase ?? "active"}
                  </span>
                )}
                {patterns.ashtama_shani.is_active && (
                  <span
                    className="rounded px-2 py-1 font-medium"
                    style={{ background: "var(--status-danger-soft, rgba(239,68,68,.12))", color: "var(--status-danger)" }}
                  >
                    Ashtama Shani active
                  </span>
                )}
              </div>
            )}

            {patterns.aspects.length === 0 ? (
              <p style={{ color: "var(--text-muted)" }}>No transit-to-natal aspects detected at this moment.</p>
            ) : (
              <table className="w-full">
                <thead>
                  <tr style={{ color: "var(--text-tertiary)" }}>
                    <th className="pb-1 text-left font-medium">Transit</th>
                    <th className="pb-1 text-left font-medium">Aspect</th>
                    <th className="pb-1 text-left font-medium">To Natal</th>
                    <th className="pb-1 text-right font-medium">Orb</th>
                    <th className="pb-1 text-right font-medium">Nature</th>
                  </tr>
                </thead>
                <tbody>
                  {[...patterns.aspects]
                    .sort((a, b) => a.orb - b.orb)
                    .map((a, i) => {
                      const harmonious = a.aspect_type === "trine";
                      const tense = a.aspect_type === "square" || a.aspect_type === "opposition";
                      const natureColor = harmonious
                        ? "var(--status-success, #22c55e)"
                        : tense
                          ? "var(--status-danger)"
                          : "var(--text-secondary)";
                      const natureLabel = harmonious ? "Benefic" : tense ? "Challenging" : "Neutral";
                      return (
                        <tr key={i} style={{ borderTop: "1px solid var(--border-subtle)" }}>
                          <td className="py-1" style={{ color: "var(--text-primary)" }}>{a.transiting_planet}</td>
                          <td className="py-1 capitalize" style={{ color: "var(--text-secondary)" }}>
                            {a.aspect_type === "special_graha" ? "Special" : a.aspect_type}
                          </td>
                          <td className="py-1" style={{ color: "var(--text-primary)" }}>{a.natal_planet}</td>
                          <td className="py-1 text-right font-mono" style={{ color: "var(--text-secondary)" }}>
                            {a.orb.toFixed(1)}°
                          </td>
                          <td className="py-1 text-right font-medium" style={{ color: natureColor }}>
                            {natureLabel}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}