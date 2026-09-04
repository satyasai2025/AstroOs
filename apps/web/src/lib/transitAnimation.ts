/**
 * AstroOS — Animated Mixed Varga / Transit: Animation Utilities
 *
 * 60 FPS animation loop with velocity-aware interpolation.
 * Handles smooth planetary movement including retrograde transitions.
 */

import type {
  TransitTimelineKeyframe,
  TransitTimelinePlanet,
  InterpolatedPlanetState,
  PlaybackSpeed,
  TrailPoint,
} from "./transitTimelineTypes";

// ── Constants ─────────────────────────────────────────────────────────────────

const DEGREES_PER_RASHI = 30;
const DEGREES_PER_NAKSHATRA = 13 + 1 / 3; // 13.333...°
const DEGREES_PER_PADA = DEGREES_PER_NAKSHATRA / 4; // 3.333...°

// ── Easing Functions ──────────────────────────────────────────────────────────

/**
 * Smooth step interpolation - respects velocity changes.
 * Used for retrograde station transitions.
 */
export function smoothStep(t: number): number {
  return t * t * (3 - 2 * t);
}

/**
 * Ease in-out for natural motion.
 */
export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

/**
 * Calculate interpolation ease based on speed change between keyframes.
 * Handles retrograde station (speed → 0 → reverse) smoothly.
 */
export function calculateEaseFromSpeed(
  speed1: number,
  speed2: number,
  t: number
): number {
  const absSpeed1 = Math.abs(speed1);
  const absSpeed2 = Math.abs(speed2);

  // If both speeds are similar, use linear interpolation
  if (Math.abs(absSpeed1 - absSpeed2) < 0.1) {
    return t;
  }

  // If slowing down (approaching station), ease out
  if (absSpeed1 > absSpeed2) {
    return smoothStep(t);
  }

  // If speeding up (leaving station), ease in
  if (absSpeed1 < absSpeed2) {
    return 1 - smoothStep(1 - t);
  }

  return t;
}

// ── Interpolation Functions ────────────────────────────────────────────────────

/**
 * Linear interpolation between two values.
 */
function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * Angular interpolation - handles wraparound at 0/360°.
 */
function lerpAngle(a: number, b: number, t: number): number {
  // Normalize to [0, 360)
  a = ((a % 360) + 360) % 360;
  b = ((b % 360) + 360) % 360;

  // Find shortest path
  let diff = b - a;
  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;

  return ((a + diff * t) % 360 + 360) % 360;
}

/**
 * Get rashi info from longitude.
 */
function getRashiFromLongitude(longitude: number): { rashi: string; degree: number } {
  const normalized = ((longitude % 360) + 360) % 360;
  const rashiIndex = Math.floor(normalized / DEGREES_PER_RASHI);
  const degree = normalized - rashiIndex * DEGREES_PER_RASHI;

  const rashis = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
  ];

  return {
    rashi: rashis[rashiIndex],
    degree: degree,
  };
}

/**
 * Interpolate a single planet's state between two keyframes.
 * Uses velocity-aware interpolation for smooth retrograde transitions.
 */
export function interpolatePlanet(
  kf1: TransitTimelineKeyframe,
  kf2: TransitTimelineKeyframe,
  t: number,
  planetName: string
): InterpolatedPlanetState | null {
  const p1 = kf1.planets.find((p) => p.planet === planetName);
  const p2 = kf2.planets.find((p) => p.planet === planetName);

  if (!p1 || !p2) {
    return null;
  }

  // Calculate ease based on speed change
  const ease = calculateEaseFromSpeed(p1.speed_deg_per_day, p2.speed_deg_per_day, t);

  // Interpolate longitude with angular awareness
  const longitude = lerpAngle(p1.sidereal_longitude, p2.sidereal_longitude, ease);

  // Get current rashi and degree
  const { rashi, degree } = getRashiFromLongitude(longitude);

  // Determine retrograde state (use closest keyframe's state)
  const isRetrograde = t < 0.5 ? p1.is_direct === false : p2.is_direct === false;

  return {
    planet: planetName,
    longitude,
    rashi,
    rashi_degree: degree,
    is_retrograde: isRetrograde,
    screen_x: 0, // Calculated by chart renderer
    screen_y: 0,
    opacity: 1.0,
  };
}

/**
 * Interpolate all planets between two keyframes.
 */
export function interpolateAllPlanets(
  kf1: TransitTimelineKeyframe,
  kf2: TransitTimelineKeyframe,
  t: number
): InterpolatedPlanetState[] {
  const planets = kf1.planets.map((p1) => {
    const p2 = kf2.planets.find((p) => p.planet === p1.planet);
    if (!p2) {
      return {
        planet: p1.planet,
        longitude: p1.sidereal_longitude,
        rashi: p1.rashi,
        rashi_degree: p1.rashi_degree,
        is_retrograde: p1.is_direct === false,
        screen_x: 0,
        screen_y: 0,
        opacity: 1.0,
      } as InterpolatedPlanetState;
    }

    const ease = calculateEaseFromSpeed(p1.speed_deg_per_day, p2.speed_deg_per_day, t);
    const longitude = lerpAngle(p1.sidereal_longitude, p2.sidereal_longitude, ease);
    const { rashi, degree } = getRashiFromLongitude(longitude);
    const isRetrograde = t < 0.5 ? p1.is_direct === false : p2.is_direct === false;

    return {
      planet: p1.planet,
      longitude,
      rashi,
      rashi_degree: degree,
      is_retrograde: isRetrograde,
      screen_x: 0,
      screen_y: 0,
      opacity: 1.0,
    } as InterpolatedPlanetState;
  });

  return planets;
}

// ── Animation Loop Utilities ───────────────────────────────────────────────────

export interface AnimationLoopState {
  lastFrameTime: number;
  accumulatedTime: number;
  currentKeyframeIndex: number;
  isPlaying: boolean;
}

/**
 * Create animation loop state.
 */
export function createAnimationLoopState(): AnimationLoopState {
  return {
    lastFrameTime: performance.now(),
    accumulatedTime: 0,
    currentKeyframeIndex: 0,
    isPlaying: false,
  };
}

/**
 * Calculate animation delta time (in seconds) since last frame.
 */
export function getDeltaTime(state: AnimationLoopState): number {
  const now = performance.now();
  const delta = (now - state.lastFrameTime) / 1000; // Convert to seconds
  state.lastFrameTime = now;
  return delta;
}

/**
 * Convert playback speed to time advancement per real second.
 * speed is in "minutes of timeline per real second"
 */
export function getTimeAdvancementPerSecond(speed: PlaybackSpeed): number {
  // speed is in minutes per second
  return speed * 60; // Convert to seconds per second
}

/**
 * Find the keyframe index for a given timestamp.
 */
export function findKeyframeIndex(
  keyframes: TransitTimelineKeyframe[],
  timestamp: Date
): number {
  const ts = timestamp.toISOString();

  // Binary search for the keyframe
  let left = 0;
  let right = keyframes.length - 1;

  while (left < right) {
    const mid = Math.floor((left + right) / 2);
    const midTime = keyframes[mid].datetime_utc;

    if (midTime < ts) {
      left = mid + 1;
    } else if (midTime > ts) {
      right = mid;
    } else {
      return mid;
    }
  }

  return left;
}

/**
 * Find the two keyframes surrounding a timestamp for interpolation.
 */
export function findSurroundingKeyframes(
  keyframes: TransitTimelineKeyframe[],
  timestamp: Date
): { kf1: TransitTimelineKeyframe; kf2: TransitTimelineKeyframe; t: number } | null {
  if (keyframes.length === 0) return null;
  if (keyframes.length === 1) return null;

  const ts = timestamp.getTime();

  // Find surrounding keyframes
  for (let i = 0; i < keyframes.length - 1; i++) {
    const kf1Time = new Date(keyframes[i].datetime_utc).getTime();
    const kf2Time = new Date(keyframes[i + 1].datetime_utc).getTime();

    if (ts >= kf1Time && ts <= kf2Time) {
      const t = (ts - kf1Time) / (kf2Time - kf1Time);
      return {
        kf1: keyframes[i],
        kf2: keyframes[i + 1],
        t: Math.max(0, Math.min(1, t)), // Clamp to [0, 1]
      };
    }
  }

  // If timestamp is beyond the last keyframe, use the last two
  if (ts > new Date(keyframes[keyframes.length - 1].datetime_utc).getTime()) {
    const kf1 = keyframes[keyframes.length - 2];
    const kf2 = keyframes[keyframes.length - 1];
    return { kf1, kf2, t: 1.0 };
  }

  // If timestamp is before the first keyframe, use the first two
  if (ts < new Date(keyframes[0].datetime_utc).getTime()) {
    const kf1 = keyframes[0];
    const kf2 = keyframes[1];
    return { kf1, kf2, t: 0.0 };
  }

  return null;
}

// ── Trail Management ──────────────────────────────────────────────────────────

/**
 * Add a point to the trail history.
 */
export function addTrailPoint(
  trail: TrailPoint[],
  point: TrailPoint,
  maxPoints: number = 100
): TrailPoint[] {
  const updated = [...trail, point];

  // Keep only the most recent points
  if (updated.length > maxPoints) {
    return updated.slice(updated.length - maxPoints);
  }

  return updated;
}

/**
 * Filter trail for a specific planet.
 */
export function filterTrailByPlanet(
  trail: TrailPoint[],
  planetName: string
): TrailPoint[] {
  return trail.filter((p) => p.planet === planetName);
}

/**
 * Filter trail by time window (last N hours).
 */
export function filterTrailByTime(
  trail: TrailPoint[],
  currentTime: Date,
  hours: number
): TrailPoint[] {
  const cutoff = new Date(currentTime.getTime() - hours * 60 * 60 * 1000);
  return trail.filter((p) => new Date(p.timestamp) >= cutoff);
}

// ── Time Utilities ─────────────────────────────────────────────────────────────

/**
 * Format ISO timestamp for display.
 */
export function formatTimelineTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * Format time for timeline axis.
 */
export function formatTimelineAxis(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Add minutes to an ISO timestamp.
 */
export function addMinutesToTimestamp(isoString: string, minutes: number): string {
  const date = new Date(isoString);
  date.setMinutes(date.getMinutes() + minutes);
  return date.toISOString();
}

/**
 * Calculate progress through timeline (0-1).
 */
export function calculateTimelineProgress(
  currentTime: string,
  startTime: string,
  endTime: string
): number {
  const current = new Date(currentTime).getTime();
  const start = new Date(startTime).getTime();
  const end = new Date(endTime).getTime();

  if (end === start) return 0;
  return (current - start) / (end - start);
}