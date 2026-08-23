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

      {/* Side-by-Side Row: Compact Panchanga (Left, 4 col) + Detailed Analysis (Right, 8 col) */}
      <div className="grid gap-4 lg:grid-cols-12">
        {/* Compact Panchanga Panel */}
        {currentPanchanga && (
          <div className="glass-card p-3.5 lg:col-span-4 flex flex-col justify-between">
            <div>
              <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-cyan-400">
                📅 Live Panchanga
              </h3>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Tithi</span>
                  <span className="font-bold text-white">
                    {currentPanchanga.tithi.name} ({currentPanchanga.tithi.paksha})
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Nakshatra</span>
                  <span className="font-bold text-amber-300">
                    {currentPanchanga.nakshatra.nakshatra} (P{currentPanchanga.nakshatra.pada})
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Yoga</span>
                  <span className="font-bold text-cyan-300">{currentPanchanga.yoga.name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Karana</span>
                  <span className="font-bold text-emerald-300">{currentPanchanga.karana.name}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Vara</span>
                  <span className="font-bold text-slate-200">{currentPanchanga.vara.name}</span>
                </div>
              </div>
            </div>

            {/* Planet Intelligence overlay inside Panchanga if planet selected */}
            {selectedPlanet && (
              <div className="mt-3 pt-2 border-t border-slate-800">
                <PlanetIntelligencePanel
                  planetName={selectedPlanet}
                  currentTime={currentTime}
                  natalChart={natalChart}
                />
              </div>
            )}
          </div>
        )}

        {/* Detailed Analysis Panel */}
        <div className="glass-card p-3.5 lg:col-span-8 flex flex-col justify-between">
          <div>
            <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-cyan-400">
              🪐 Detailed Analysis — Parashari Aspects &amp; Gochara
            </h3>
            {isPatternsLoading && !patterns ? (
              <p className="text-xs text-slate-400">Loading transit-to-natal aspects…</p>
            ) : !patterns ? (
              <p className="text-xs text-slate-400">No aspect data available for this moment.</p>
            ) : (
              <div className="space-y-2 text-xs">
                {(patterns.sade_sati.is_active || patterns.ashtama_shani.is_active) && (
                  <div className="flex flex-wrap gap-2 mb-1">
                    {patterns.sade_sati.is_active && (
                      <span className="rounded px-2 py-0.5 font-bold text-[11px] bg-rose-500/20 text-rose-300 border border-rose-500/30">
                        Sade Sati — {patterns.sade_sati.phase ?? "active"}
                      </span>
                    )}
                    {patterns.ashtama_shani.is_active && (
                      <span className="rounded px-2 py-0.5 font-bold text-[11px] bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        Ashtama Shani Active
                      </span>
                    )}
                  </div>
                )}

                {patterns.aspects.length === 0 ? (
                  <p className="text-slate-400 text-xs">No transit-to-natal aspects detected at this moment.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead>
                        <tr className="border-b border-slate-800 text-[10px] uppercase text-slate-400">
                          <th className="pb-1.5">Transit</th>
                          <th className="pb-1.5">Vedic Graha Drishti</th>
                          <th className="pb-1.5">To Natal</th>
                          <th className="pb-1.5 text-right">Orb</th>
                          <th className="pb-1.5 text-right">Nature</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {[...patterns.aspects]
                          .sort((a, b) => a.orb - b.orb)
                          .map((a, i) => {
                            const p = (a.transiting_planet || "").toLowerCase();
                            const type = (a.aspect_type || "").toLowerCase();

                            let vedicLabel = "Graha Drishti";
                            let natureLabel = "Neutral";
                            let natureColor = "var(--text-secondary)";

                            if (type === "opposition" || type === "7th") {
                              vedicLabel = "7th Full Drishti (Saptama)";
                              natureLabel = p === "jupiter" || p === "venus" || p === "mercury" || p === "moon" ? "Benefic" : "Challenging";
                              natureColor = natureLabel === "Benefic" ? "var(--status-success, #22c55e)" : "var(--status-danger)";
                            } else if (type === "trine" || type === "5th" || type === "9th") {
                              if (p === "jupiter") {
                                vedicLabel = "5th/9th Special Full Drishti";
                                natureLabel = "Benefic";
                                natureColor = "var(--status-success, #22c55e)";
                              } else {
                                vedicLabel = "5th/9th Parashari Drishti";
                                natureLabel = p === "venus" || p === "mercury" || p === "moon" ? "Benefic" : "Neutral";
                                natureColor = natureLabel === "Benefic" ? "var(--status-success, #22c55e)" : "var(--text-secondary)";
                              }
                            } else if (type === "square" || type === "4th" || type === "10th") {
                              if (p === "mars") {
                                vedicLabel = "4th Special Full Drishti";
                                natureLabel = "Challenging";
                                natureColor = "var(--status-danger)";
                              } else if (p === "saturn") {
                                vedicLabel = "10th Special Full Drishti";
                                natureLabel = "Challenging";
                                natureColor = "var(--status-danger)";
                              } else {
                                vedicLabel = "4th/10th Parashari Drishti";
                                natureLabel = "Neutral";
                                natureColor = "var(--text-secondary)";
                              }
                            } else if (type === "special_graha" || type === "special") {
                              if (p === "mars") {
                                vedicLabel = "8th Special Full Drishti";
                                natureLabel = "Challenging";
                                natureColor = "var(--status-danger)";
                              } else if (p === "saturn") {
                                vedicLabel = "3rd Special Full Drishti";
                                natureLabel = "Challenging";
                                natureColor = "var(--status-danger)";
                              } else if (p === "jupiter") {
                                vedicLabel = "5th/9th Special Full Drishti";
                                natureLabel = "Benefic";
                                natureColor = "var(--status-success, #22c55e)";
                              } else {
                                vedicLabel = "Special Graha Drishti";
                                natureLabel = "Neutral";
                                natureColor = "var(--text-secondary)";
                              }
                            } else if (type === "conjunction" || type === "0th") {
                              vedicLabel = "Yuti (Conjunction)";
                              natureLabel = p === "jupiter" || p === "venus" ? "Benefic" : "Neutral";
                              natureColor = natureLabel === "Benefic" ? "var(--status-success, #22c55e)" : "var(--text-secondary)";
                            } else {
                              vedicLabel = "Parashari Graha Drishti";
                            }

                            return (
                              <tr key={i} className="hover:bg-slate-900/50">
                                <td className="py-1.5 font-bold text-slate-100">{a.transiting_planet}</td>
                                <td className="py-1.5 font-semibold text-cyan-300">{vedicLabel}</td>
                                <td className="py-1.5 text-slate-200">{a.natal_planet}</td>
                                <td className="py-1.5 text-right text-slate-400">{a.orb.toFixed(1)}°</td>
                                <td className="py-1.5 text-right font-extrabold" style={{ color: natureColor }}>
                                  {natureLabel}
                                </td>
                              </tr>
                            );
                          })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}