/**
 * AstroOS — Animated Mixed Varga / Transit: Time Controller UI
 *
 * Provides timeline controls for animated transit visualization:
 * - Date/time picker
 * - Play/pause button
 * - Speed selector
 * - Step controls (1 min, 1 hour, 1 day)
 * - Range slider with event markers
 * - Calendar integration
 */

"use client";

import { useCallback, useMemo, useState } from "react";
import type {
  TransitTimelineKeyframe,
  TransitEvent,
  PlaybackSpeed,
  TimelinePreset,
} from "@/lib/transitTimelineTypes";
import { TIMELINE_PRESETS } from "@/lib/transitTimelineTypes";
import { useCurrentUser } from "@/lib/auth";
import { zonedDatetimeLocalToUtcIso, utcIsoToZonedDatetimeLocalValue, utcIsoToZonedDateValue } from "@/lib/timezone";

interface TransitTimelineProps {
  /** Current playback time */
  currentTime: string;
  /** Timeline range */
  timelineStart: string;
  timelineEnd: string;
  /** Is animation playing */
  isPlaying: boolean;
  /** Playback speed */
  speed: PlaybackSpeed;
  /** Events for markers */
  events: TransitEvent[];
  /** Are events visible */
  showEvents: boolean;
  /** Currently selected planet */
  selectedPlanet: string | null;
  /** Is loading */
  isLoading: boolean;
  /** Animation actions */
  onPlay: () => void;
  onPause: () => void;
  onToggle: () => void;
  onSeek: (time: string) => void;
  onStepForward: (minutes: number) => void;
  onStepBackward: (minutes: number) => void;
  onSetSpeed: (speed: PlaybackSpeed) => void;
  onJumpToEvent: (event: TransitEvent) => void;
  onSetSelectedPlanet: (planet: string | null) => void;
  onToggleEvents: () => void;
  /** Reload the timeline centered on "now" at the given preset's range/resolution. */
  onLoadPreset?: (preset: TimelinePreset) => void;
  /** Jump straight to an exact date/time (reloads the window around it first if needed). */
  onJumpToDate?: (iso: string) => void;
  /** Load an explicit [from, to] range chosen by the user. */
  onLoadCustomRange?: (startIso: string, endIso: string, intervalMinutes?: number) => void;
}

const SPEED_OPTIONS: { value: PlaybackSpeed; label: string; description: string }[] = [
  { value: 1, label: "1x", description: "1 min/sec" },
  { value: 10, label: "10x", description: "10 min/sec" },
  { value: 60, label: "1hr", description: "1 hr/sec" },
  { value: 300, label: "6hr", description: "6 hr/sec" },
  { value: 1440, label: "1d", description: "1 day/sec" },
];

export function TransitTimeline({
  currentTime,
  timelineStart,
  timelineEnd,
  isPlaying,
  speed,
  events,
  showEvents,
  selectedPlanet,
  isLoading,
  onPlay,
  onPause,
  onToggle,
  onSeek,
  onStepForward,
  onStepBackward,
  onSetSpeed,
  onJumpToEvent,
  onSetSelectedPlanet,
  onToggleEvents,
  onLoadPreset,
  onJumpToDate,
  onLoadCustomRange,
}: TransitTimelineProps) {
  // Account timezone (Settings > Profile) — used to interpret/display the
  // date/time pickers below instead of silently assuming the browser's
  // timezone. Falls back to the browser's own zone until the user record
  // loads (or for guests without one).
  const { data: currentUser } = useCurrentUser();
  const userTimezone = currentUser?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

  const currentDate = useMemo(() => new Date(currentTime), [currentTime]);
  const startDate = useMemo(() => new Date(timelineStart), [timelineStart]);
  const endDate = useMemo(() => new Date(timelineEnd), [timelineEnd]);

  const progress = useMemo(() => {
    if (!timelineStart || !timelineEnd || !currentTime) return 0;
    const total = endDate.getTime() - startDate.getTime();
    if (total === 0) return 0;
    const current = currentDate.getTime();
    return Math.max(0, Math.min(1, (current - startDate.getTime()) / total));
  }, [currentTime, timelineStart, timelineEnd, currentDate, startDate, endDate]);

  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseFloat(e.target.value);
      const total = endDate.getTime() - startDate.getTime();
      const newTime = new Date(startDate.getTime() + value * total);
      onSeek(newTime.toISOString());
    },
    [startDate, endDate, onSeek]
  );

  // Local (uncontrolled-ish) input state for the "jump to date/time" and
  // "custom range" pickers — seeded from the current playback time /
  // loaded window (read in the account's timezone) so the inputs start
  // somewhere sensible.
  const [jumpInput, setJumpInput] = useState(() => utcIsoToZonedDatetimeLocalValue(currentTime, userTimezone));
  const [rangeFromInput, setRangeFromInput] = useState(() => utcIsoToZonedDateValue(timelineStart, userTimezone));
  const [rangeToInput, setRangeToInput] = useState(() => utcIsoToZonedDateValue(timelineEnd, userTimezone));

  const handleJumpSubmit = useCallback(() => {
    if (!jumpInput || !onJumpToDate) return;
    const iso = zonedDatetimeLocalToUtcIso(jumpInput, userTimezone);
    onJumpToDate(iso);
  }, [jumpInput, onJumpToDate, userTimezone]);

  const handleCustomRangeSubmit = useCallback(() => {
    if (!rangeFromInput || !rangeToInput || !onLoadCustomRange) return;
    const startIso = zonedDatetimeLocalToUtcIso(`${rangeFromInput}T00:00`, userTimezone);
    const endIso = zonedDatetimeLocalToUtcIso(`${rangeToInput}T23:59`, userTimezone);
    onLoadCustomRange(startIso, endIso);
  }, [rangeFromInput, rangeToInput, onLoadCustomRange, userTimezone]);

  const handleJumpToEvent = useCallback(
    (event: TransitEvent) => {
      onJumpToEvent(event);
    },
    [onJumpToEvent]
  );

  const eventMarkers = useMemo(() => {
    if (!showEvents || !events.length) return null;

    return events.map((event, index) => {
      const eventDate = new Date(event.datetime_utc);
      const eventProgress = (eventDate.getTime() - startDate.getTime()) / (endDate.getTime() - startDate.getTime());

      return (
        <button
          key={index}
          type="button"
          className="absolute -top-1 -translate-x-1/2 group"
          style={{ left: `${eventProgress * 100}%` }}
          onClick={() => handleJumpToEvent(event)}
          title={`${event.description}\n${new Date(event.datetime_utc).toLocaleString()}`}
        >
          <div
            className="h-3 w-1 rounded-full"
            style={{
              backgroundColor: event.event_type.includes("ingress") ? "var(--accent)" :
                           event.event_type.includes("retrograde") || event.event_type.includes("station") ? "var(--warning)" :
                           event.event_type.includes("combustion") ? "var(--danger)" :
                           "var(--text-muted)",
            }}
          />
          <div
            className="absolute bottom-4 left-1/2 -translate-x-1/2 whitespace-nowrap rounded px-2 py-1 text-xs opacity-0 transition-opacity group-hover:opacity-100"
            style={{ backgroundColor: "var(--bg-surface-700)", color: "var(--text-primary)" }}
          >
            {event.description}
          </div>
        </button>
      );
    });
  }, [events, showEvents, startDate, endDate, handleJumpToEvent]);

  if (isLoading) {
    return (
      <div className="glass-card p-4">
        <div className="flex items-center justify-center py-8">
          <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Loading timeline...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Main Time Controller */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Play/Pause — big round button, the primary control */}
          <button
            type="button"
            onClick={onToggle}
            className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-full shadow-lg transition hover:scale-105 active:scale-95"
            style={{
              backgroundColor: "var(--accent)",
              color: "var(--accent-text)",
              boxShadow: "0 4px 20px color-mix(in srgb, var(--accent) 45%, transparent)",
            }}
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? (
              <svg width="24" height="24" viewBox="0 0 16 16" fill="currentColor">
                <rect x="3" y="2" width="3" height="12" />
                <rect x="10" y="2" width="3" height="12" />
              </svg>
            ) : (
              <svg width="26" height="26" viewBox="0 0 16 16" fill="currentColor">
                <path d="M4 2l10 6-10 6V2z" />
              </svg>
            )}
          </button>

          {/* Step Backward */}
          <button
            type="button"
            onClick={() => onStepBackward(1)}
            className="flex h-10 w-10 items-center justify-center rounded-lg transition"
            style={{
              backgroundColor: "var(--bg-surface-700)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-primary)",
            }}
            aria-label="Step backward 1 minute"
            title="Backward 1 min"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M11 3l-6 5 6 5V3z" />
              <rect x="2" y="3" width="2" height="10" />
            </svg>
          </button>

          {/* Step Forward */}
          <button
            type="button"
            onClick={() => onStepForward(1)}
            className="flex h-10 w-10 items-center justify-center rounded-lg transition"
            style={{
              backgroundColor: "var(--bg-surface-700)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-primary)",
            }}
            aria-label="Step forward 1 minute"
            title="Forward 1 min"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M5 3l6 5-6 5V3z" />
              <rect x="12" y="3" width="2" height="10" />
            </svg>
          </button>

          {/* Time Display — shown in the account's timezone (Settings >
              Profile), with the zone spelled out so it's never ambiguous. */}
          <div
            className="rounded-lg px-4 py-2 text-sm font-mono"
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-primary)",
              color: "var(--text-primary)",
            }}
            title={`Timezone: ${userTimezone}`}
          >
            {currentDate.toLocaleString("en-US", {
              timeZone: userTimezone,
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
              timeZoneName: "shortOffset",
            })}
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1">
            {SPEED_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onSetSpeed(option.value)}
                className="rounded-lg px-2 py-1.5 text-xs font-medium transition"
                style={{
                  backgroundColor: speed === option.value ? "var(--accent)" : "var(--bg-card)",
                  color: speed === option.value ? "var(--accent-text)" : "var(--text-secondary)",
                  border: `1px solid ${speed === option.value ? "var(--accent)" : "var(--border-primary)"}`,
                }}
                title={option.description}
              >
                {option.label}
              </button>
            ))}
          </div>

          {/* Events Toggle */}
          <button
            type="button"
            onClick={onToggleEvents}
            className="flex h-10 items-center gap-1.5 rounded-lg px-3 transition"
            style={{
              backgroundColor: showEvents ? "var(--accent)" : "var(--bg-card)",
              color: showEvents ? "var(--accent-text)" : "var(--text-secondary)",
              border: `1px solid ${showEvents ? "var(--accent)" : "var(--border-primary)"}`,
            }}
            aria-label="Toggle event markers"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
              <circle cx="8" cy="8" r="2" />
              <path d="M8 1v2M8 13v2M1 8h2M13 8h2" stroke="currentColor" strokeWidth="2" />
            </svg>
            <span className="text-xs font-medium">Events</span>
          </button>
        </div>

        {/* Timeline Slider */}
        <div className="mt-4 relative">
          <div className="flex items-center gap-3">
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              {startDate.toLocaleDateString("en-US", { timeZone: userTimezone, month: "short", day: "numeric" })}
            </span>
            <div className="relative flex-1">
              <input
                type="range"
                min="0"
                max="1"
                step="0.001"
                value={progress}
                onChange={handleSliderChange}
                className="h-2 w-full cursor-pointer appearance-none rounded-lg"
                style={{
                  background: `linear-gradient(to right, var(--accent) 0%, var(--accent) ${progress * 100}%, var(--bg-surface-700) ${progress * 100}%, var(--bg-surface-700) 100%)`,
                }}
                aria-label="Timeline scrubber"
              />
              {/* Event Markers */}
              <div className="absolute -top-1 left-0 right-0 h-4">{eventMarkers}</div>
            </div>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              {endDate.toLocaleDateString("en-US", { timeZone: userTimezone, month: "short", day: "numeric" })}
            </span>
          </div>
        </div>

        {/* Quick Step Controls */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>Step:</span>
          {[
            { label: "1 min", minutes: 1 },
            { label: "1 hour", minutes: 60 },
            { label: "1 day", minutes: 1440 },
          ].map(({ label, minutes }) => (
            <button
              key={label}
              type="button"
              onClick={() => onStepBackward(minutes)}
              className="rounded px-2 py-1 text-xs transition"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-primary)",
              }}
            >
              -{label}
            </button>
          ))}
          {[
            { label: "1 min", minutes: 1 },
            { label: "1 hour", minutes: 60 },
            { label: "1 day", minutes: 1440 },
          ].map(({ label, minutes }) => (
            <button
              key={label}
              type="button"
              onClick={() => onStepForward(minutes)}
              className="rounded px-2 py-1 text-xs transition"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-primary)",
              }}
            >
              +{label}
            </button>
          ))}
        </div>
      </div>

      {/* Jump to an exact date/time + pick a custom range */}
      <div className="glass-card grid gap-4 p-4 sm:grid-cols-2">
        <div>
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            Jump to Date &amp; Time
          </h3>
          <p className="mb-2 text-[10px]" style={{ color: "var(--text-muted)" }}>
            Interpreted as {userTimezone} (Settings &gt; Profile)
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="datetime-local"
              value={jumpInput}
              onChange={(e) => setJumpInput(e.target.value)}
              className="rounded-lg px-2 py-1.5 text-xs"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-primary)",
              }}
              aria-label="Jump to date and time"
            />
            <button
              type="button"
              onClick={handleJumpSubmit}
              disabled={!onJumpToDate || !jumpInput}
              className="rounded-lg px-3 py-1.5 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-50"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              Go
            </button>
          </div>
        </div>

        <div>
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            Custom Range
          </h3>
          <p className="mb-2 text-[10px]" style={{ color: "var(--text-muted)" }}>
            Interpreted as {userTimezone} (Settings &gt; Profile)
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="date"
              value={rangeFromInput}
              onChange={(e) => setRangeFromInput(e.target.value)}
              className="rounded-lg px-2 py-1.5 text-xs"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-primary)",
              }}
              aria-label="Range start date"
            />
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>to</span>
            <input
              type="date"
              value={rangeToInput}
              onChange={(e) => setRangeToInput(e.target.value)}
              className="rounded-lg px-2 py-1.5 text-xs"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-primary)",
                border: "1px solid var(--border-primary)",
              }}
              aria-label="Range end date"
            />
            <button
              type="button"
              onClick={handleCustomRangeSubmit}
              disabled={!onLoadCustomRange || !rangeFromInput || !rangeToInput}
              className="rounded-lg px-3 py-1.5 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-50"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              Load
            </button>
          </div>
        </div>
      </div>

      {/* Timeline Presets */}
      <div className="glass-card p-4">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Timeline Presets
        </h3>
        <div className="flex flex-wrap gap-2">
          {TIMELINE_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => onLoadPreset?.(preset)}
              disabled={!onLoadPreset}
              className="rounded-lg px-3 py-2 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-50"
              style={{
                backgroundColor: "var(--bg-card)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-primary)",
              }}
              title={preset.description}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Event List */}
      {showEvents && events.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            Events ({events.length})
          </h3>
          <div className="max-h-48 overflow-y-auto space-y-1">
            {events.slice(0, 20).map((event, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleJumpToEvent(event)}
                className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs transition hover:bg-opacity-50"
                style={{
                  backgroundColor: "transparent",
                  color: "var(--text-secondary)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "var(--bg-surface-700)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{
                    backgroundColor:
                      event.event_type.includes("ingress") ? "var(--accent)" :
                      event.event_type.includes("retrograde") ? "var(--warning)" :
                      event.event_type.includes("combustion") ? "var(--danger)" :
                      "var(--text-muted)",
                  }}
                />
                <span className="flex-1">
                  {new Date(event.datetime_utc).toLocaleString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
                <span style={{ color: "var(--text-muted)" }}>
                  {event.description}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}