/**
 * AstroOS — Animated Mixed Varga / Transit: Type Definitions
 *
 * New types for the time-driven transit animation system.
 */

// ── Timeline Keyframe ──────────────────────────────────────────────────────────

/**
 * One computed moment in a transit timeline.
 * Contains all planetary data needed for interpolation and display.
 */
export interface TransitTimelineKeyframe {
  /** ISO-8601 timestamp for this keyframe */
  datetime_utc: string;
  /** Planetary positions at this moment */
  planets: TransitTimelinePlanet[];
  /** Panchanga data at this moment (optional, included when requested) */
  panchanga?: PanchangaKeyframe;
  /** Events that occurred between this keyframe and the previous one */
  events?: TransitEvent[];
}

/**
 * One planet's state at a timeline keyframe.
 */
export interface TransitTimelinePlanet {
  planet: string;
  /** Sidereal longitude in degrees [0, 360) */
  sidereal_longitude: number;
  /** Rashi (sign) name */
  rashi: string;
  /** Degree within the rashi [0, 30) */
  rashi_degree: number;
  /** Minute within the rashi degree [0, 60) */
  rashi_minute: number;
  /** Second within the rashi minute [0, 60) */
  rashi_second: number;
  /** True = direct motion, False = retrograde */
  is_direct: boolean;
  /** True if at station (about to change direction) */
  is_station: boolean;
  /** Speed in degrees per day (negative = retrograde) */
  speed_deg_per_day: number;
  /** Nakshatra at this longitude */
  nakshatra: string;
  /** Nakshatra pada (1-4) */
  pada: number;
  /** Degree within nakshatra [0, 13°20') */
  degree_in_nakshatra: number;
  /** D9 Navamsha rashi */
  navamsha_rashi: string;
  /** D9 Navamsha lord */
  navamsha_lord: string;
  /** Combustion state */
  is_combust: boolean;
  /** Combustion orb in degrees (if combust) */
  combustion_orb: number | null;
  /** Dignity state: exalted, debilitated, own_sign, friend, neutral, enemy, etc. */
  dignity: string | null;
  /** Transit house from natal Moon */
  house_from_natal_moon: number;
  /** Transit house from natal Ascendant */
  house_from_natal_ascendant: number;
  /** Graha drishti aspects cast by this planet */
  aspects: string[];
}

// ── Panchanga at a Moment ──────────────────────────────────────────────────────

export interface PanchangaKeyframe {
  tithi: {
    number: number;
    name: string;
    paksha: string;
    completion_percent: number;
  };
  nakshatra: {
    nakshatra: string;
    nakshatra_number: number;
    pada: number;
    lord: string;
    degree_in_nakshatra: number;
    degree_in_pada: number;
  };
  yoga: {
    number: number;
    name: string;
    completion_percent: number;
  };
  karana: {
    number: number;
    name: string;
    is_fixed: boolean;
  };
  vara: {
    number: number;
    name: string;
    lord: string;
  };
  sunrise: string; // ISO-8601
  sunset: string; // ISO-8601
  rahu_kalam: {
    start: string;
    end: string;
  };
  gulika: {
    start: string;
    end: string;
  };
  yamaganda: {
    start: string;
    end: string;
  };
  hora: HoraEntry[];
}

export interface HoraEntry {
  planet: string;
  start: string;
  end: string;
}

// ── Transit Events ─────────────────────────────────────────────────────────────

/**
 * An event detected by the backend between keyframes.
 * The frontend uses these to mark the timeline and trigger recalculations.
 */
export interface TransitEvent {
  /** ISO-8601 timestamp when this event occurs */
  datetime_utc: string;
  /** Planet involved */
  planet: string;
  /** Event type */
  event_type: TransitEventType;
  /** Human-readable description */
  description: string;
  /** Previous value (for transitions) */
  from_value: string | null;
  /** New value (for transitions) */
  to_value: string | null;
}

export type TransitEventType =
  | "sign_ingress"
  | "nakshatra_change"
  | "pada_change"
  | "retrograde_start"
  | "retrograde_end"
  | "station_retrograde"
  | "station_direct"
  | "combustion_start"
  | "combustion_end"
  | "exaltation_ingress"
  | "debilitation_ingress"
  | "own_sign_ingress"
  | "aspect_exact"
  | "house_change";

// ── Timeline API Request/Response ──────────────────────────────────────────────

export interface TransitTimelineRequest {
  /** Birth data */
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: string;
  house_system: string;

  /** Timeline range */
  start_datetime_utc: string;
  end_datetime_utc: string;
  /** Preferred interval in minutes (backend may adjust adaptively) */
  interval_minutes: number;
  /** Enable adaptive density (default: true) */
  adaptive: boolean;

  /** Include Panchanga data (adds ~30% payload size) */
  include_panchanga: boolean;
  /** Include Navamsha (D9) data */
  include_navamsha: boolean;
  /** Include combustion calculations */
  include_combustion: boolean;
  /** Include dignity calculations */
  include_dignity: boolean;

  /** Specific planets to track (null = all 9 grahas) */
  planets?: string[] | null;
}

export interface TransitTimelineResponse {
  /** Request parameters echoed back */
  request: {
    start_datetime_utc: string;
    end_datetime_utc: string;
    interval_minutes: number;
    adaptive: boolean;
  };
  /** Computed keyframes */
  keyframes: TransitTimelineKeyframe[];
  /** All detected events across the timeline */
  events: TransitEvent[];
  /** Time range actually computed */
  computed_range: {
    start: string;
    end: string;
    keyframe_count: number;
    event_count: number;
  };
  /** Adaptive intervals actually used (if adaptive=true) */
  actual_intervals?: number[];
}

// ── Animation Controller State ─────────────────────────────────────────────────

export type PlaybackSpeed = 1 | 10 | 60 | 300 | 1440; // 1min, 10min, 1hr, 6hr, 1day per real second

export interface AnimationControllerState {
  /** Current playback time */
  current_time: string; // ISO-8601
  /** Is animation playing */
  is_playing: boolean;
  /** Playback speed multiplier */
  speed: PlaybackSpeed;
  /** Timeline range */
  timeline_start: string;
  timeline_end: string;
  /** Currently selected planet (for trail focus) */
  selected_planet: string | null;
  /** Trail visibility */
  show_trail: boolean;
  /** Trail duration in hours */
  trail_duration_hours: number;
  /** Show event markers */
  show_events: boolean;
}

export interface AnimationControllerActions {
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (datetime_utc: string) => void;
  step_forward: (minutes: number) => void;
  step_backward: (minutes: number) => void;
  set_speed: (speed: PlaybackSpeed) => void;
  jump_to_event: (event: TransitEvent) => void;
  set_selected_planet: (planet: string | null) => void;
  toggle_trail: () => void;
  set_trail_duration: (hours: number) => void;
  toggle_events: () => void;
}

export type AnimationController = AnimationControllerState & AnimationControllerActions;

// ── Interpolated Planet State (for 60fps rendering) ────────────────────────────

export interface InterpolatedPlanetState {
  planet: string;
  /** Interpolated sidereal longitude */
  longitude: number;
  /** Current rashi (from longitude) */
  rashi: string;
  /** Degree within rashi */
  rashi_degree: number;
  /** Is retrograde (from current keyframe) */
  is_retrograde: boolean;
  /** Interpolated screen position (pixels) */
  screen_x: number;
  screen_y: number;
  /** Opacity for trail fade effect */
  opacity: number;
}

// ── Planet Intelligence Panel ──────────────────────────────────────────────────

export interface PlanetIntelligenceData {
  planet: string;
  /** Current longitude */
  longitude: number;
  rashi: string;
  rashi_degree: number;
  rashi_minute: number;
  rashi_second: number;
  nakshatra: string;
  pada: number;
  degree_in_nakshatra: number;
  /** Motion state */
  motion: "direct" | "retrograde" | "station_retrograde" | "station_direct";
  /** Speed in deg/day */
  speed: number;
  /** Combustion */
  is_combust: boolean;
  combustion_orb: number | null;
  /** Dignity */
  dignity: string | null;
  is_exalted: boolean;
  is_debilitated: boolean;
  is_own_sign: boolean;
  /** Classical properties */
  guna: "sattvic" | "rajasic" | "tamasic";
  tatva: "fire" | "water" | "air" | "earth" | "ether";
  gender: "male" | "female" | "neutral";
  mobility: "chara" | "sthira" | "chara-sthira";
  kalapurusha_house: number;
  /** D9 Navamsha */
  navamsha_rashi: string;
  navamsha_lord: string;
  /** Houses */
  natal_house: number;
  transit_house_from_moon: number;
  transit_house_from_lagna: number;
  /** Aspects being cast */
  aspects_cast: string[];
  aspects_received: string[];
}

// ── Chart Layers (for Animated Transit) ────────────────────────────────────────

export type ChartLayer =
  | "natal_planets"
  | "transit_planets"
  | "transit_trails"
  | "aspects"
  | "event_indicators";

export interface LayerConfig {
  layer: ChartLayer;
  visible: boolean;
  opacity: number;
  z_index: number;
}

// ── Timeline Presets ───────────────────────────────────────────────────────────

export interface TimelinePreset {
  label: string;
  start_datetime_utc: string;
  end_datetime_utc: string;
  interval_minutes: number;
  description?: string;
}

export const TIMELINE_PRESETS: TimelinePreset[] = [
  {
    label: "1 Day",
    start_datetime_utc: "",
    end_datetime_utc: "",
    interval_minutes: 15,
    description: "24 hours with 15-minute keyframes",
  },
  {
    label: "1 Week",
    start_datetime_utc: "",
    end_datetime_utc: "",
    interval_minutes: 60,
    description: "7 days with 1-hour keyframes",
  },
  {
    label: "1 Month",
    start_datetime_utc: "",
    end_datetime_utc: "",
    interval_minutes: 360,
    description: "30 days with 6-hour keyframes",
  },
  {
    label: "1 Year",
    start_datetime_utc: "",
    end_datetime_utc: "",
    interval_minutes: 1440,
    description: "365 days with 1-day keyframes",
  },
];

// ── Trail Point ─────────────────────────────────────────────────────────────────

export interface TrailPoint {
  timestamp: string;
  planet: string;
  longitude: number;
  screen_x: number;
  screen_y: number;
}

// ── Animation Frame Cache ──────────────────────────────────────────────────────

export interface FrameCacheEntry {
  timestamp: string;
  planets: InterpolatedPlanetState[];
  panchanga?: PanchangaKeyframe;
}

export interface FrameCache {
  /** Cached keyframes from backend */
  keyframes: TransitTimelineKeyframe[];
  /** Index by timestamp for fast lookup */
  index: Map<string, number>;
  /** Interpolated frames in memory (for trail) */
  frames: FrameCacheEntry[];
  /** LRU eviction policy — max cached interpolated frames */
  max_frames: number;
}