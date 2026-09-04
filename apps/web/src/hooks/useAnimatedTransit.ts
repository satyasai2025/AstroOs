/**
 * AstroOS — Animated Mixed Varga / Transit: Main Controller Hook
 *
 * Manages the complete animation state machine:
 * - Timeline playback (play/pause/scrub)
 * - Keyframe caching and interpolation
 * - Panchanga update-on-change
 * - Trail management
 * - Event handling
 */

"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type {
  TransitTimelineKeyframe,
  TransitTimelineResponse,
  TransitEvent,
  AnimationControllerState,
  AnimationControllerActions,
  InterpolatedPlanetState,
  PlaybackSpeed,
  PanchangaKeyframe,
} from "@/lib/transitTimelineTypes";
import {
  interpolateAllPlanets,
  findSurroundingKeyframes,
  createAnimationLoopState,
  getDeltaTime,
  getTimeAdvancementPerSecond,
  calculateTimelineProgress,
} from "@/lib/transitAnimation";
import type { TrailPoint } from "@/lib/transitTimelineTypes";
import { api } from "@/lib/api";

// ── Configuration ─────────────────────────────────────────────────────────────

const DEFAULT_INTERVAL_MINUTES = 60;
const DEFAULT_SPEED: PlaybackSpeed = 60; // 1 hour per second
const MAX_TRAIL_POINTS = 100;
const DEFAULT_TRAIL_DURATION_HOURS = 24;

// ── Hook State ────────────────────────────────────────────────────────────────

interface UseAnimatedTransitState {
  // Timeline data
  keyframes: TransitTimelineKeyframe[];
  events: TransitEvent[];
  timelineStart: string;
  timelineEnd: string;

  // Animation state
  currentTime: string;
  isPlaying: boolean;
  speed: PlaybackSpeed;

  // UI state
  selectedPlanet: string | null;
  showTrail: boolean;
  trailDurationHours: number;
  showEvents: boolean;

  // Computed state
  interpolatedPlanets: InterpolatedPlanetState[];
  currentPanchanga: PanchangaKeyframe | null;
  trail: { timestamp: string; planet: string; longitude: number; screen_x: number; screen_y: number }[];
  activeEvents: TransitEvent[];

  // Status
  isLoading: boolean;
  error: string | null;
}

interface UseAnimatedTransitActions {
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (datetime_utc: string) => void;
  stepForward: (minutes: number) => void;
  stepBackward: (minutes: number) => void;
  setSpeed: (speed: PlaybackSpeed) => void;
  jumpToEvent: (event: TransitEvent) => void;
  setSelectedPlanet: (planet: string | null) => void;
  toggleTrail: () => void;
  setTrailDuration: (hours: number) => void;
  toggleEvents: () => void;
  loadTimeline: (params: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa: string;
    house_system: string;
    start_datetime_utc: string;
    end_datetime_utc: string;
    interval_minutes?: number;
  }) => Promise<void>;
  getExactPosition: (datetime_utc: string) => Promise<InterpolatedPlanetState[]>;
}

type UseAnimatedTransit = UseAnimatedTransitState & UseAnimatedTransitActions;

// ── Hook Implementation ───────────────────────────────────────────────────────

export function useAnimatedTransit(): UseAnimatedTransit {
  // Core state
  const [keyframes, setKeyframes] = useState<TransitTimelineKeyframe[]>([]);
  const [events, setEvents] = useState<TransitEvent[]>([]);
  const [timelineStart, setTimelineStart] = useState<string>("");
  const [timelineEnd, setTimelineEnd] = useState<string>("");
  const [currentTime, setCurrentTime] = useState<string>("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<PlaybackSpeed>(DEFAULT_SPEED);
  const [selectedPlanet, setSelectedPlanet] = useState<string | null>(null);
  const [showTrail, setShowTrail] = useState(true);
  const [trailDurationHours, setTrailDurationHours] = useState(DEFAULT_TRAIL_DURATION_HOURS);
  const [showEvents, setShowEvents] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Computed state
  const [interpolatedPlanets, setInterpolatedPlanets] = useState<InterpolatedPlanetState[]>([]);
  const [currentPanchanga, setCurrentPanchanga] = useState<PanchangaKeyframe | null>(null);
  const [trail, setTrail] = useState<TrailPoint[]>([]);
  const [activeEvents, setActiveEvents] = useState<TransitEvent[]>([]);

  // Refs for animation loop
  const animationStateRef = useRef(createAnimationLoopState());
  const rafRef = useRef<number | null>(null);
  const lastPanchangaRef = useRef<string | null>(null);

  // ── Animation Loop ──────────────────────────────────────────────────────────

  const animate = useCallback(() => {
    if (!isPlaying) return;

    // currentTime is "" until loadTimeline resolves — bail out rather than
    // advancing an Invalid Date (setSeconds/toISOString throw on it).
    if (!currentTime || Number.isNaN(new Date(currentTime).getTime())) {
      rafRef.current = requestAnimationFrame(animate);
      return;
    }

    const state = animationStateRef.current;
    const delta = getDeltaTime(state);

    // Advance time based on speed
    const timeAdvancement = getTimeAdvancementPerSecond(speed);
    const currentDate = new Date(currentTime);
    currentDate.setSeconds(currentDate.getSeconds() + delta * timeAdvancement);

    const newTime = currentDate.toISOString();
    setCurrentTime(newTime);

    // Find surrounding keyframes and interpolate
    if (keyframes.length >= 2) {
      const result = findSurroundingKeyframes(keyframes, currentDate);
      if (result) {
        const { kf1, kf2, t } = result;
        const interpolated = interpolateAllPlanets(kf1, kf2, t);
        setInterpolatedPlanets(interpolated);

        // Update trail
        if (showTrail) {
          setTrail((prev) => {
            const newPoints = interpolated.flatMap((p) => [
              {
                timestamp: newTime,
                planet: p.planet,
                longitude: p.longitude,
                screen_x: p.screen_x,
                screen_y: p.screen_y,
              },
            ]);
            const updated = [...prev, ...newPoints];
            return updated.slice(-MAX_TRAIL_POINTS);
          });
        }

        // Update Panchanga only when it changes
        const panchanga = t < 0.5 ? kf1.panchanga : kf2.panchanga;
        const panchangaKey = panchanga
          ? `${panchanga.tithi.number}-${panchanga.nakshatra.nakshatra}-${panchanga.yoga.number}`
          : null;

        if (panchanga && panchangaKey !== lastPanchangaRef.current) {
          lastPanchangaRef.current = panchangaKey;
          setCurrentPanchanga(panchanga);
        }

        // Update active events
        const active = events.filter((e) => {
          const eventTime = new Date(e.datetime_utc).getTime();
          const currentTimeMs = currentDate.getTime();
          return Math.abs(eventTime - currentTimeMs) < 60000; // Within 1 minute
        });
        setActiveEvents(active);
      }
    }

    // Continue animation loop
    rafRef.current = requestAnimationFrame(animate);
  }, [isPlaying, speed, currentTime, keyframes, showTrail, events]);

  // Start/stop animation loop
  useEffect(() => {
    if (isPlaying) {
      animationStateRef.current = createAnimationLoopState();
      rafRef.current = requestAnimationFrame(animate);
    } else {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    }

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [isPlaying, animate]);

  // ── Actions ─────────────────────────────────────────────────────────────────

  const play = useCallback(() => {
    setIsPlaying(true);
  }, []);

  const pause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const toggle = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const seek = useCallback((datetime_utc: string) => {
    setIsPlaying(false);
    setCurrentTime(datetime_utc);

    // Find surrounding keyframes and interpolate
    if (keyframes.length >= 2) {
      const timestamp = new Date(datetime_utc);
      const result = findSurroundingKeyframes(keyframes, timestamp);
      if (result) {
        const { kf1, kf2, t } = result;
        const interpolated = interpolateAllPlanets(kf1, kf2, t);
        setInterpolatedPlanets(interpolated);

        // Update Panchanga
        const panchanga = t < 0.5 ? kf1.panchanga : kf2.panchanga;
        if (panchanga) {
          const panchangaKey = `${panchanga.tithi.number}-${panchanga.nakshatra.nakshatra}-${panchanga.yoga.number}`;
          lastPanchangaRef.current = panchangaKey;
          setCurrentPanchanga(panchanga);
        }
      }
    }
  }, [keyframes]);

  const stepForward = useCallback((minutes: number) => {
    const current = new Date(currentTime);
    current.setMinutes(current.getMinutes() + minutes);
    seek(current.toISOString());
  }, [currentTime, seek]);

  const stepBackward = useCallback((minutes: number) => {
    const current = new Date(currentTime);
    current.setMinutes(current.getMinutes() - minutes);
    seek(current.toISOString());
  }, [currentTime, seek]);

  const setSpeedAction = useCallback((newSpeed: PlaybackSpeed) => {
    setSpeed(newSpeed);
  }, []);

  const jumpToEvent = useCallback((event: TransitEvent) => {
    seek(event.datetime_utc);
  }, [seek]);

  const setSelectedPlanetAction = useCallback((planet: string | null) => {
    setSelectedPlanet(planet);
  }, []);

  const toggleTrail = useCallback(() => {
    setShowTrail((prev) => !prev);
  }, []);

  const setTrailDuration = useCallback((hours: number) => {
    setTrailDurationHours(hours);
  }, []);

  const toggleEvents = useCallback(() => {
    setShowEvents((prev) => !prev);
  }, []);

  // ── Data Loading ─────────────────────────────────────────────────────────────

  const loadTimeline = useCallback(async (params: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa: string;
    house_system: string;
    start_datetime_utc: string;
    end_datetime_utc: string;
    interval_minutes?: number;
  }) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<TransitTimelineResponse>("/api/v1/transit/timeline", {
        ...params,
        interval_minutes: params.interval_minutes || DEFAULT_INTERVAL_MINUTES,
        adaptive: true,
        include_panchanga: true,
        include_navamsha: true,
        include_combustion: true,
        include_dignity: true,
      });

      setKeyframes(response.keyframes);
      setEvents(response.events);
      setTimelineStart(response.request.start_datetime_utc);
      setTimelineEnd(response.request.end_datetime_utc);

      // Set initial time to first keyframe
      if (response.keyframes.length > 0) {
        const initialTime = response.keyframes[0].datetime_utc;
        setCurrentTime(initialTime);

        // Set initial interpolated state
        const initialPlanets = response.keyframes[0].planets.map((p) => ({
          planet: p.planet,
          longitude: p.sidereal_longitude,
          rashi: p.rashi,
          rashi_degree: p.rashi_degree,
          is_retrograde: !p.is_direct,
          screen_x: 0,
          screen_y: 0,
          opacity: 1.0,
        })) as InterpolatedPlanetState[];

        setInterpolatedPlanets(initialPlanets);

        // Set initial Panchanga
        if (response.keyframes[0].panchanga) {
          setCurrentPanchanga(response.keyframes[0].panchanga);
          lastPanchangaRef.current = `${response.keyframes[0].panchanga.tithi.number}-${response.keyframes[0].panchanga.nakshatra.nakshatra}-${response.keyframes[0].panchanga.yoga.number}`;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load timeline");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getExactPosition = useCallback(async (datetime_utc: string): Promise<InterpolatedPlanetState[]> => {
    try {
      const response = await api.post<{ planets: InterpolatedPlanetState[] }>("/api/v1/transit/exact", {
        datetime_utc,
      });

      return response.planets;
    } catch (err) {
      console.error("Failed to get exact position:", err);
      return [];
    }
  }, []);

  // ── Return Hook State ────────────────────────────────────────────────────────

  return {
    // State
    keyframes,
    events,
    timelineStart,
    timelineEnd,
    currentTime,
    isPlaying,
    speed,
    selectedPlanet,
    showTrail,
    trailDurationHours,
    showEvents,
    interpolatedPlanets,
    currentPanchanga,
    trail,
    activeEvents,
    isLoading,
    error,

    // Actions
    play,
    pause,
    toggle,
    seek,
    stepForward,
    stepBackward,
    setSpeed: setSpeedAction,
    jumpToEvent,
    setSelectedPlanet: setSelectedPlanetAction,
    toggleTrail,
    setTrailDuration,
    toggleEvents,
    loadTimeline,
    getExactPosition,
  };
}