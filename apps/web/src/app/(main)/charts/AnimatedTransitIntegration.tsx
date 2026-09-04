/**
 * Animated Transit Integration Component
 * Client component for the animated transit feature
 */

"use client";

import { useState, useCallback, useMemo } from "react";
import { AnimatedTransitView } from "@/components/charts/transit/AnimatedTransitView";
import { useAnimatedTransit } from "@/hooks/useAnimatedTransit";
import { useTransitPatterns } from "@/lib/transitPatterns";
import type { D1ChartResponse, TransitPatternsRequest } from "@/lib/types";
import type { WorkflowAnalysisRequest } from "@/lib/types";
import type { TimelinePreset } from "@/lib/transitTimelineTypes";

/** Total timeline span (in days, centered on "now") for each Timeline
 * Preset label — the presets themselves only carry a keyframe interval,
 * not a range, so the range has to be defined once, here. */
const PRESET_SPAN_DAYS: Record<string, number> = {
  "1 Day": 1,
  "1 Week": 7,
  "1 Month": 30,
  "1 Year": 365,
};

interface AnimatedTransitIntegrationProps {
  chart: D1ChartResponse;
  request: WorkflowAnalysisRequest | null;
}

export function AnimatedTransitIntegration({ chart, request }: AnimatedTransitIntegrationProps) {
  const [timelineData, setTimelineData] = useState<{
    keyframes: any[];
    events: any[];
    timelineStart: string;
    timelineEnd: string;
  } | null>(null);

  const {
    currentTime,
    isPlaying,
    speed,
    selectedPlanet,
    showTrail,
    showEvents,
    interpolatedPlanets,
    currentPanchanga,
    isLoading,
    trail,
    play,
    pause,
    toggle,
    seek,
    stepForward,
    stepBackward,
    setSpeed,
    jumpToEvent,
    setSelectedPlanet,
    toggleTrail,
    toggleEvents,
    loadTimeline,
  } = useAnimatedTransit();

  /** Load an explicit [startDate, endDate] window at the given keyframe
   * resolution. Every other loader (preset, "centered on now", jump-to-
   * date) is just a convenience wrapper that computes a range and calls
   * this. */
  const handleLoadRange = useCallback(
    async (startDate: Date, endDate: Date, intervalMinutes = 60) => {
      if (!request) return;

      await loadTimeline({
        birth_datetime_utc: request.birth_datetime_utc,
        latitude: request.latitude,
        longitude: request.longitude,
        ayanamsa: request.ayanamsa,
        house_system: request.house_system,
        start_datetime_utc: startDate.toISOString(),
        end_datetime_utc: endDate.toISOString(),
        interval_minutes: intervalMinutes,
      });

      setTimelineData({
        keyframes: [],
        events: [],
        timelineStart: startDate.toISOString(),
        timelineEnd: endDate.toISOString(),
      });
    },
    [request, loadTimeline],
  );

  const handleLoadTimeline = useCallback(
    async (spanDays = 14, intervalMinutes = 60, centerOn: Date = new Date()) => {
      const startDate = new Date(centerOn.getTime() - (spanDays / 2) * 24 * 60 * 60 * 1000);
      const endDate = new Date(centerOn.getTime() + (spanDays / 2) * 24 * 60 * 60 * 1000);
      await handleLoadRange(startDate, endDate, intervalMinutes);
    },
    [handleLoadRange],
  );

  // Auto-load timeline on mount (14-day default window, centered on now)
  useState(() => {
    handleLoadTimeline();
  });

  const handleLoadPreset = useCallback(
    (preset: TimelinePreset) => {
      const spanDays = PRESET_SPAN_DAYS[preset.label] ?? 14;
      handleLoadTimeline(spanDays, preset.interval_minutes);
    },
    [handleLoadTimeline],
  );

  /** Jump to an exact date/time. If it already falls inside the loaded
   * window, this is just a scrub (instant). Otherwise it reloads a fresh
   * 14-day window centered on the target date first, then seeks — same
   * pattern as the presets, just centered on a chosen moment instead of
   * "now". */
  const handleJumpToDate = useCallback(
    async (targetIso: string) => {
      const targetMs = new Date(targetIso).getTime();
      if (Number.isNaN(targetMs)) return;

      const inRange =
        timelineData &&
        targetMs >= new Date(timelineData.timelineStart).getTime() &&
        targetMs <= new Date(timelineData.timelineEnd).getTime();

      if (!inRange) {
        await handleLoadTimeline(14, 60, new Date(targetMs));
      }
      seek(new Date(targetMs).toISOString());
    },
    [timelineData, handleLoadTimeline, seek],
  );

  /** Load an explicit custom [from, to] range chosen by the user, rather
   * than a fixed-span preset centered on now. */
  const handleLoadCustomRange = useCallback(
    (startIso: string, endIso: string, intervalMinutes = 60) => {
      const startDate = new Date(startIso);
      const endDate = new Date(endIso);
      if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime()) || startDate >= endDate) return;
      handleLoadRange(startDate, endDate, intervalMinutes);
    },
    [handleLoadRange],
  );

  // Real transit-to-natal aspects + Sade Sati/Ashtama Shani for the
  // "Detailed Analysis" panel — bucketed to the nearest 15 minutes so the
  // 60fps interpolation loop doesn't refetch on every animation frame
  // (aspect orbs don't meaningfully change faster than that).
  const patternsBucketTime = useMemo(() => {
    if (!currentTime) return undefined;
    const ms = new Date(currentTime).getTime();
    if (Number.isNaN(ms)) return undefined;
    const bucketMs = 15 * 60 * 1000;
    return new Date(Math.round(ms / bucketMs) * bucketMs).toISOString();
  }, [currentTime]);

  const patternsRequest: TransitPatternsRequest | null = request
    ? {
        birth_datetime_utc: request.birth_datetime_utc,
        latitude: request.latitude,
        longitude: request.longitude,
        ayanamsa: request.ayanamsa,
        house_system: request.house_system,
        transit_datetime_utc: patternsBucketTime,
      }
    : null;
  const patternsQuery = useTransitPatterns(patternsRequest);

  if (!request) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
          No chart data available
        </div>
      </div>
    );
  }

  return (
    <AnimatedTransitView
      natalChart={chart}
      patterns={patternsQuery.data}
      isPatternsLoading={patternsQuery.isLoading}
      timelineData={timelineData}
      currentTime={currentTime}
      isPlaying={isPlaying}
      speed={speed}
      selectedPlanet={selectedPlanet}
      showTrail={showTrail}
      showEvents={showEvents}
      interpolatedPlanets={interpolatedPlanets}
      currentPanchanga={currentPanchanga}
      isLoading={isLoading}
      trailPoints={trail}
      onPlay={play}
      onPause={pause}
      onToggle={toggle}
      onSeek={seek}
      onStepForward={stepForward}
      onStepBackward={stepBackward}
      onSetSpeed={setSpeed}
      onJumpToEvent={jumpToEvent}
      onSetSelectedPlanet={setSelectedPlanet}
      onToggleTrail={toggleTrail}
      onToggleEvents={toggleEvents}
      onLoadTimeline={handleLoadTimeline}
      onLoadPreset={handleLoadPreset}
      onJumpToDate={handleJumpToDate}
      onLoadCustomRange={handleLoadCustomRange}
    />
  );
}
