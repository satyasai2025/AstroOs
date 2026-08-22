"use client";

/**
 * AstroOS — Unified Multi-System Event Timing Workspace
 *
 * Synchronizes 4 classical timing pillars:
 *   1. Vimshottari Dasha
 *   2. Gochara Transits (with Gochara Vedha & Ashtakavarga)
 *   3. Sarvatobhadra Chakra (28-Nakshatra Ray Paths & Sangya Hits)
 *   4. KP Cuspal Sub-Lord Triggers (CSL, Star/Sub Triggers, Dusthana Veto)
 *
 * Includes an interactive time-travel slider and complete technical evidence chains.
 */

import { useState, useMemo, useEffect, useRef } from "react";
import {
  useUnifiedTimingAnalysis,
  evaluateTimingMoment,
  type UnifiedEventType,
  type UnifiedTimingSnapshot,
  type UnifiedEventTimingWindow,
  type TimelineSamplePoint,
} from "@/lib/unifiedTiming";
import type { WorkflowAnalysisRequest, WorkflowAnalysisResponse } from "@/lib/types";

interface Props {
  request?: WorkflowAnalysisRequest | {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa?: string;
    house_system?: string;
  } | null;
  result?: WorkflowAnalysisResponse | null;
  initialEvent?: UnifiedEventType;
}

const EVENT_OPTIONS: { id: UnifiedEventType; label: string; icon: string; defaultCusp: number }[] = [
  { id: "marriage", label: "Marriage & Partnership", icon: "💍", defaultCusp: 7 },
  { id: "career", label: "Career & Promotion", icon: "💼", defaultCusp: 10 },
  { id: "wealth", label: "Wealth & Assets", icon: "💰", defaultCusp: 2 },
  { id: "property", label: "Property & Real Estate", icon: "🏡", defaultCusp: 4 },
  { id: "foreign_travel", label: "Foreign Travel & Relocation", icon: "✈️", defaultCusp: 12 },
  { id: "health", label: "Health & Vitality", icon: "🌿", defaultCusp: 1 },
  { id: "childbirth", label: "Childbirth & Progeny", icon: "👶", defaultCusp: 5 },
  { id: "education", label: "Education & Learning", icon: "📚", defaultCusp: 5 },
];

function tierColor(tier: string): string {
  switch (tier) {
    case "VERY_HIGH":
      return "#10b981"; // emerald-500
    case "HIGH":
      return "#3b82f6"; // blue-500
    case "MODERATE":
      return "#f59e0b"; // amber-500
    case "LOW":
      return "#f97316"; // orange-500
    case "UNFAVORABLE":
    default:
      return "#ef4444"; // red-500
  }
}

function scoreBg(score: number): string {
  if (score >= 75) return "rgba(16, 185, 129, 0.15)";
  if (score >= 60) return "rgba(59, 130, 246, 0.15)";
  if (score >= 45) return "rgba(245, 158, 11, 0.15)";
  return "rgba(239, 68, 68, 0.15)";
}

export function UnifiedEventTimingWorkspace({ request, result, initialEvent = "marriage" }: Props) {
  const [eventType, setEventType] = useState<UnifiedEventType>(initialEvent);
  const [startDate, setStartDate] = useState<string>(() => {
    const d = new Date();
    return d.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState<string>(() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() + 2);
    return d.toISOString().split("T")[0];
  });

  const [scrubDate, setScrubDate] = useState<string>(startDate);
  const [liveSnapshot, setLiveSnapshot] = useState<UnifiedTimingSnapshot | null>(null);
  const [isScrubbing, setIsScrubbing] = useState(false);

  // Prepare payload for full timeline scan
  const scanPayload = useMemo(() => {
    if (!request?.birth_datetime_utc) {
      // Fallback sample coordinates if not yet selected
      return {
        birth_datetime_utc: "1990-05-15T08:30:00Z",
        latitude: 28.6139,
        longitude: 77.209,
        ayanamsa: "lahiri",
        house_system: "P",
        event_type: eventType,
        start_date: startDate,
        end_date: endDate,
        step_days: 30,
      };
    }
    return {
      birth_datetime_utc: request.birth_datetime_utc,
      latitude: request.latitude,
      longitude: request.longitude,
      ayanamsa: request.ayanamsa || "lahiri",
      house_system: request.house_system || "P",
      event_type: eventType,
      start_date: startDate,
      end_date: endDate,
      step_days: 30,
    };
  }, [request, eventType, startDate, endDate]);

  const { data: scanData, isLoading, error } = useUnifiedTimingAnalysis(scanPayload);

  // Sync snapshot when scanData arrives
  useEffect(() => {
    if (scanData?.evaluated_moment_snapshot) {
      setLiveSnapshot(scanData.evaluated_moment_snapshot);
    }
  }, [scanData]);

  // Handle Scrubbing (Time-Travel Slider)
  const handleSliderChange = async (dateVal: string) => {
    setScrubDate(dateVal);
    // Find closest point in time_series if available for instant display
    if (scanData?.time_series) {
      const match = scanData.time_series.find((p) => p.date === dateVal);
      if (match) {
        // Debounce actual server fetch for full snapshot details
      }
    }
  };

  const handleSliderCommit = async (dateVal: string) => {
    if (!scanPayload) return;
    setIsScrubbing(true);
    try {
      const targetUtc = `${dateVal}T12:00:00Z`;
      const res = await evaluateTimingMoment({
        birth_datetime_utc: scanPayload.birth_datetime_utc,
        latitude: scanPayload.latitude,
        longitude: scanPayload.longitude,
        ayanamsa: scanPayload.ayanamsa,
        house_system: scanPayload.house_system,
        event_type: eventType,
        target_datetime_utc: targetUtc,
      });
      if (res?.snapshot) {
        setLiveSnapshot(res.snapshot);
      }
    } catch (e) {
      console.error("Failed to evaluate moment:", e);
    } finally {
      setIsScrubbing(false);
    }
  };

  const currentSnapshot = liveSnapshot || scanData?.evaluated_moment_snapshot;
  const timeSeries = scanData?.time_series || [];
  const candidateWindows = scanData?.candidate_windows || [];

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto p-4 sm:p-6" data-testid="unified-event-timing-workspace">
      {/* ── Header & Event Switcher ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-5" style={{ borderColor: "var(--border-primary)" }}>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">⏳</span>
            <h1 className="text-2xl font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
              Unified Multi-System Event Timing Matrix
            </h1>
          </div>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            Synchronized Vimshottari Dasha + Gochara Transits + SBC Vedha + KP Cuspal Sub-Lord Triggers
          </p>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center gap-2 bg-[var(--bg-card)] p-2 rounded-xl border border-[var(--border-primary)]">
          <label className="text-xs font-medium text-[var(--text-muted)]">Range:</label>
          <input 
            type="date"
            aria-label="Start date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="text-xs rounded-lg px-2 py-1 bg-[var(--bg-input)] border border-[var(--border-secondary)] text-[var(--text-primary)]"
          />
          <span className="text-xs text-[var(--text-muted)]">→</span>
          <input 
            type="date"
            aria-label="End date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="text-xs rounded-lg px-2 py-1 bg-[var(--bg-input)] border border-[var(--border-secondary)] text-[var(--text-primary)]"
          />
        </div>
      </div>

      {/* Event Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none" role="tablist">
        {EVENT_OPTIONS.map((opt) => {
          const active = eventType === opt.id;
          return (
            <button
              key={opt.id}
              role="tab"
              aria-selected={active}
              onClick={() => setEventType(opt.id)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all"
              style={{
                backgroundColor: active ? "var(--accent)" : "var(--bg-card)",
                color: active ? "var(--accent-text)" : "var(--text-secondary)",
                border: `1px solid ${active ? "transparent" : "var(--border-primary)"}`,
                boxShadow: active ? "0 2px 8px rgba(0,0,0,0.15)" : "none",
              }}
            >
              <span>{opt.icon}</span>
              <span>{opt.label}</span>
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center p-16 glass-card rounded-2xl">
          <div className="animate-spin h-8 w-8 border-3 border-emerald-500 border-t-transparent rounded-full mb-3" />
          <p className="text-sm font-medium text-[var(--text-secondary)]">
            Synchronizing Dasha, Gochara, SBC and KP timing systems...
          </p>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-500/10 border border-red-500/30 rounded-2xl text-sm text-red-400">
          Failed to compute multi-system event timing. Please check chart parameters.
        </div>
      ) : (
        <>
          {/* ── Interactive Time-Travel Chronological Timeline ── */}
          <div className="glass-card p-5 sm:p-6 rounded-2xl border border-[var(--border-primary)] flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
                  Multi-System Synchronized Confluence Curve
                </h2>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Timeline synchronized across {timeSeries.length} points ({startDate} → {endDate})
                </p>
              </div>

              {/* Time-Travel Scrubber Badge */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-secondary)]">
                <span className="text-xs text-[var(--text-muted)]">Scrubbed Moment:</span>
                <span className="text-xs font-mono font-bold text-[var(--text-primary)]">{scrubDate}</span>
                {isScrubbing && <span className="animate-pulse text-[10px] text-emerald-400">updating...</span>}
              </div>
            </div>

            {/* Visual SVG Timeline Chart */}
            <div className="relative w-full h-44 bg-[var(--bg-input)]/40 rounded-xl overflow-hidden p-2 border border-[var(--border-secondary)]">
              {timeSeries.length > 1 ? (
                <svg className="w-full h-full" viewBox={`0 0 ${timeSeries.length * 10} 100`} preserveAspectRatio="none">
                  {/* Grid Lines */}
                  <line x1="0" y1="25" x2={timeSeries.length * 10} y2="25" stroke="var(--border-secondary)" strokeDasharray="3,3" opacity="0.4" />
                  <line x1="0" y1="50" x2={timeSeries.length * 10} y2="50" stroke="var(--border-secondary)" strokeDasharray="3,3" opacity="0.4" />
                  <line x1="0" y1="75" x2={timeSeries.length * 10} y2="75" stroke="var(--border-secondary)" strokeDasharray="3,3" opacity="0.4" />

                  {/* Candidate Windows Background Highlights */}
                  {candidateWindows.map((win, idx) => {
                    const startIdx = Math.max(0, timeSeries.findIndex((p) => p.date >= win.start_date));
                    const endIdx = Math.max(startIdx, timeSeries.findIndex((p) => p.date >= win.end_date));
                    const w = Math.max(10, (endIdx - startIdx) * 10);
                    return (
                      <rect
                        key={idx}
                        x={startIdx * 10}
                        y="0"
                        width={w}
                        height="100"
                        fill="rgba(16, 185, 129, 0.12)"
                        stroke="rgba(16, 185, 129, 0.3)"
                        strokeWidth="1"
                      />
                    );
                  })}

                  {/* Dasha Sub-Curve (Yellow) */}
                  <polyline
                    fill="none"
                    stroke="#eab308"
                    strokeWidth="1"
                    opacity="0.5"
                    points={timeSeries.map((p, i) => `${i * 10},${100 - p.dasha_score}`).join(" ")}
                  />

                  {/* Gochara Sub-Curve (Cyan) */}
                  <polyline
                    fill="none"
                    stroke="#06b6d4"
                    strokeWidth="1"
                    opacity="0.5"
                    points={timeSeries.map((p, i) => `${i * 10},${100 - p.gochara_score}`).join(" ")}
                  />

                  {/* SBC Sub-Curve (Purple) */}
                  <polyline
                    fill="none"
                    stroke="#a855f7"
                    strokeWidth="1"
                    opacity="0.5"
                    points={timeSeries.map((p, i) => `${i * 10},${100 - p.sbc_score}`).join(" ")}
                  />

                  {/* KP Sub-Curve (Orange) */}
                  <polyline
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="1"
                    opacity="0.5"
                    points={timeSeries.map((p, i) => `${i * 10},${100 - p.kp_score}`).join(" ")}
                  />

                  {/* Synchronized Confluence Master Curve (Emerald Bold) */}
                  <polyline
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2.5"
                    points={timeSeries.map((p, i) => `${i * 10},${100 - p.confluence_score}`).join(" ")}
                  />

                  {/* Peak Marker Circles */}
                  {timeSeries.map((p, i) => {
                    if (!p.peak_flag) return null;
                    return (
                      <g key={i}>
                        <circle cx={i * 10} cy={100 - p.confluence_score} r="4" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />
                      </g>
                    );
                  })}
                </svg>
              ) : null}
            </div>

            {/* Legend & Time-Travel Slider Control */}
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center justify-between text-xs gap-2">
                <div className="flex items-center gap-4 text-[var(--text-secondary)]">
                  <div className="flex items-center gap-1.5 font-medium">
                    <span className="h-2 w-4 rounded-full bg-emerald-500" />
                    <span>Confluence Master</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-1.5 w-3 rounded-full bg-yellow-500" />
                    <span>Dasha</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-1.5 w-3 rounded-full bg-cyan-500" />
                    <span>Gochara</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-1.5 w-3 rounded-full bg-purple-500" />
                    <span>SBC Vedha</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-1.5 w-3 rounded-full bg-orange-500" />
                    <span>KP Sub-Lord</span>
                  </div>
                </div>
                <span className="text-[var(--text-muted)] font-mono">
                  Range: {startDate} → {endDate}
                </span>
              </div>

              {/* Slider Input */}
              <div className="flex items-center gap-3 pt-1">
                <span className="text-xs font-semibold text-[var(--text-muted)]">Time-Travel:</span>
                <input 
                  type="range"
                  aria-label="Time travel timeline scrubber"
                  min="0"
                  max={Math.max(0, timeSeries.length - 1)}
                  value={Math.max(0, timeSeries.findIndex((p) => p.date >= scrubDate))}
                  onChange={(e) => {
                    const idx = Number(e.target.value);
                    if (timeSeries[idx]) {
                      handleSliderChange(timeSeries[idx].date);
                    }
                  }}
                  onMouseUp={(e) => {
                    const idx = Number((e.target as HTMLInputElement).value);
                    if (timeSeries[idx]) {
                      handleSliderCommit(timeSeries[idx].date);
                    }
                  }}
                  onTouchEnd={(e) => {
                    const idx = Number((e.target as HTMLInputElement).value);
                    if (timeSeries[idx]) {
                      handleSliderCommit(timeSeries[idx].date);
                    }
                  }}
                  className="w-full h-2 bg-[var(--bg-input)] rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
              </div>
            </div>
          </div>

          {/* ── Moment Snapshot & 4-Pillar Evidence Matrix ── */}
          {currentSnapshot && (
            <div className="flex flex-col gap-5">
              {/* Snapshot Score Banner */}
              <div
                className="p-5 rounded-2xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all"
                style={{
                  backgroundColor: scoreBg(currentSnapshot.confluence_score),
                  borderColor: tierColor(currentSnapshot.confidence_tier),
                }}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
                      Evaluated Moment Snapshot
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: tierColor(currentSnapshot.confidence_tier), color: "#fff" }}>
                      {currentSnapshot.confidence_tier} CONFLUENCE
                    </span>
                  </div>
                  <h2 className="text-xl font-bold mt-1 text-[var(--text-primary)]">
                    {EVENT_OPTIONS.find((o) => o.id === eventType)?.label}: {currentSnapshot.confluence_score}% Synchronization
                  </h2>
                  <p className="text-xs mt-1 text-[var(--text-secondary)] max-w-3xl leading-relaxed">
                    {currentSnapshot.summary_narrative}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)]">Confluence Score</span>
                    <span className="text-3xl font-extrabold" style={{ color: tierColor(currentSnapshot.confidence_tier) }}>
                      {currentSnapshot.confluence_score}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 4 Pillars Grid Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* 1. Vimshottari Dasha Pillar */}
                <div className="glass-card p-4 rounded-xl border border-[var(--border-primary)] flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[var(--border-secondary)]">
                      <span className="text-xs font-bold text-yellow-500 uppercase tracking-wide">1. Vimshottari Dasha</span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded bg-yellow-500/15 text-yellow-500">
                        {currentSnapshot.dasha.score}%
                      </span>
                    </div>

                    <div className="mt-3 space-y-2">
                      <div className="text-xs">
                        <span className="text-[var(--text-muted)]">Active Periods:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {currentSnapshot.dasha.active_chain.map((p, idx) => (
                            <span key={idx} className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--bg-input)] text-[var(--text-primary)] border border-[var(--border-secondary)]">
                              {p.level.slice(0, 2)}: {p.lord}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="text-xs">
                        <span className="text-[var(--text-muted)]">Significators:</span>
                        <p className="text-[11px] font-mono text-[var(--text-secondary)] mt-0.5">
                          {currentSnapshot.dasha.significator_lords.join(", ") || "None"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-[var(--text-secondary)] mt-3 pt-2 border-t border-[var(--border-secondary)] leading-relaxed">
                    {currentSnapshot.dasha.detail}
                  </p>
                </div>

                {/* 2. Gochara Transits Pillar */}
                <div className="glass-card p-4 rounded-xl border border-[var(--border-primary)] flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[var(--border-secondary)]">
                      <span className="text-xs font-bold text-cyan-700 uppercase tracking-wide">2. Gochara Transits</span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-700">
                        {currentSnapshot.gochara.score}%
                      </span>
                    </div>

                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">Vedha Clear:</span>
                        <span className={`text-xs font-semibold ${currentSnapshot.gochara.gochara_vedha_clear ? "text-emerald-400" : "text-amber-400"}`}>
                          {currentSnapshot.gochara.gochara_vedha_clear ? "✓ Clear" : "⚠ Obstructed"}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">SAV Bindus:</span>
                        <span className="font-mono font-semibold text-[var(--text-primary)]">
                          {currentSnapshot.gochara.ashtakavarga_support} pts
                        </span>
                      </div>

                      <div className="text-xs">
                        <span className="text-[var(--text-muted)]">Key Placements:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {currentSnapshot.gochara.key_transits.slice(0, 3).map((t, idx) => (
                            <span key={idx} className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--bg-input)] text-[var(--text-secondary)] border border-[var(--border-secondary)]">
                              {t.planet} in H{t.house_from_lagna}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-[var(--text-secondary)] mt-3 pt-2 border-t border-[var(--border-secondary)] leading-relaxed">
                    {currentSnapshot.gochara.detail}
                  </p>
                </div>

                {/* 3. Sarvatobhadra Chakra Pillar */}
                <div className="glass-card p-4 rounded-xl border border-[var(--border-primary)] flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[var(--border-secondary)]">
                      <span className="text-xs font-bold text-purple-500 uppercase tracking-wide">3. SBC Vedha</span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded bg-purple-500/15 text-purple-500">
                        {currentSnapshot.sbc.score}%
                      </span>
                    </div>

                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">Benefic Rays:</span>
                        <span className="text-emerald-400 font-bold font-mono">+{currentSnapshot.sbc.benefic_count}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">Malefic Rays:</span>
                        <span className="text-red-400 font-bold font-mono">-{currentSnapshot.sbc.malefic_count}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">Net Protection:</span>
                        <span className="font-bold text-[var(--text-primary)]">
                          {currentSnapshot.sbc.net_protection >= 0 ? `+${currentSnapshot.sbc.net_protection}` : currentSnapshot.sbc.net_protection}
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-[var(--text-secondary)] mt-3 pt-2 border-t border-[var(--border-secondary)] leading-relaxed">
                    {currentSnapshot.sbc.detail}
                  </p>
                </div>

                {/* 4. KP Cuspal Sub-Lord Pillar */}
                <div className="glass-card p-4 rounded-xl border border-[var(--border-primary)] flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[var(--border-secondary)]">
                      <span className="text-xs font-bold text-orange-500 uppercase tracking-wide">4. KP Sub-Lord</span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded bg-orange-500/15 text-orange-500">
                        {currentSnapshot.kp.score}%
                      </span>
                    </div>

                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">Primary CSL:</span>
                        <span className="font-semibold text-[var(--text-primary)]">
                          {currentSnapshot.kp.csl} (★ {currentSnapshot.kp.csl_star_lord})
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">Fructification:</span>
                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                          currentSnapshot.kp.fructification === "OPEN" ? "bg-emerald-500/15 text-emerald-400" : (
                            currentSnapshot.kp.fructification === "PARTIAL" ? "bg-amber-500/15 text-amber-400" : "bg-red-500/15 text-red-400"
                          )
                        }`}>
                          {currentSnapshot.kp.fructification}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="text-[var(--text-muted)]">Dusthana Veto:</span>
                        <span className={`text-xs font-semibold ${currentSnapshot.kp.dusthana_veto ? "text-red-400" : "text-emerald-400"}`}>
                          {currentSnapshot.kp.dusthana_veto ? "⚠ Active Veto" : "✓ None"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-[11px] text-[var(--text-secondary)] mt-3 pt-2 border-t border-[var(--border-secondary)] leading-relaxed">
                    {currentSnapshot.kp.detail}
                  </p>
                </div>
              </div>

              {/* Triggers & Inhibitors Pills */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="glass-card p-4 rounded-xl border border-[var(--border-primary)]">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2 flex items-center gap-1.5">
                    <span>✓</span> Positive Astrological Triggers
                  </h2>
                  <ul className="space-y-1.5">
                    {currentSnapshot.primary_positive_triggers.map((trig, idx) => (
                      <li key={idx} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                        <span className="text-emerald-400 mt-0.5">•</span>
                        <span>{trig}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="glass-card p-4 rounded-xl border border-[var(--border-primary)]">
                  <h2 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2 flex items-center gap-1.5">
                    <span>⚠</span> Inhibiting Factors & Resistance
                  </h2>
                  <ul className="space-y-1.5">
                    {currentSnapshot.primary_inhibiting_factors.map((inh, idx) => (
                      <li key={idx} className="text-xs text-[var(--text-secondary)] flex items-start gap-2">
                        <span className="text-amber-400 mt-0.5">•</span>
                        <span>{inh}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* ── Candidate Event Timing Windows Table ── */}
          <div className="glass-card p-5 sm:p-6 rounded-2xl border border-[var(--border-primary)]">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-1">
              Detected Candidate Timing Windows
            </h2>
            <p className="text-xs text-[var(--text-muted)] mb-4">
              High-confluence periods where Dasha, Gochara, SBC and KP alignments intersect favorably
            </p>

            {candidateWindows.length === 0 ? (
              <div className="p-8 text-center text-xs text-[var(--text-muted)] border border-dashed border-[var(--border-secondary)] rounded-xl">
                No high-confluence window identified above threshold (55%) in the scanned range.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {candidateWindows.map((win, idx) => (
                  <div
                    key={win.window_id || idx}
                    className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-card)] flex flex-col justify-between gap-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold bg-emerald-500/15 text-emerald-400">
                          {win.confluence_status}
                        </span>
                        <h2 className="text-sm font-bold text-[var(--text-primary)] mt-1.5">
                          {win.start_date} → {win.end_date}
                        </h2>
                        <p className="text-xs text-[var(--text-muted)] mt-0.5">
                          Peak Date: <strong className="text-[var(--text-primary)]">{win.peak_date}</strong>
                        </p>
                      </div>

                      <div className="text-right">
                        <span className="text-2xl font-black text-emerald-400">
                          {win.peak_score}%
                        </span>
                        <span className="block text-[10px] text-[var(--text-muted)]">peak confluence</span>
                      </div>
                    </div>

                    {/* Sub-scores radar pills */}
                    <div className="flex items-center gap-2 pt-2 border-t border-[var(--border-secondary)]">
                      <span className="text-[10px] px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-500">
                        Dasha: {win.system_scores.dasha}%
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-700">
                        Gochara: {win.system_scores.gochara}%
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-500">
                        SBC: {win.system_scores.sbc}%
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-orange-500/10 text-orange-500">
                        KP: {win.system_scores.kp}%
                      </span>
                    </div>

                    <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                      {win.narrative}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
