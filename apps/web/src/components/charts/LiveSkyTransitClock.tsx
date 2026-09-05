"use client";

import { useEffect, useState, useTransition } from "react";
import { api } from "@/lib/api";

export interface LiveSkyResponse {
  planets: LiveSkyPlanet[];
  ayanamsa?: string;
  ayanamsa_value_deg?: number;
}

interface LiveSkyPlanet {
  symbol: string;
  name: string;
  is_lunar_node: boolean;
  sidereal_longitude: number;
  rashi: string;
  rashi_sanskrit: string;
  degree_in_sign: number;
  degree_formatted: string;
  speed_deg_per_day: number;
  is_retrograde: boolean;
  is_combust: boolean;
  nakshatra: string;
  pada: number;
  nakshatra_lord: string;
  kakshya_index: number;
  kakshya_lord: string;
  kakshya_range: string;
  color: string;
}

const PLANET_COLORS: Record<string, string> = {
  Sun: "#f59e0b",
  Moon: "#e2e8f0",
  Mars: "#ef4444",
  Mercury: "#10b981",
  Jupiter: "#eab308",
  Venus: "#ec4899",
  Saturn: "#6366f1",
  Rahu: "#8b5cf6",
  Ketu: "#a855f7",
};

export function LiveSkyTransitClock() {
  const [isLiveMode, setIsLiveMode] = useState<boolean>(true);
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [planets, setPlanets] = useState<LiveSkyPlanet[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [ayanamsaName, setAyanamsaName] = useState<string>("Lahiri");
  const [ayanamsaVal, setAyanamsaVal] = useState<number>(24.23);
  const [, startTransition] = useTransition();

  // Fetch Swiss Ephemeris data from backend
  const fetchLiveSky = async (dt: Date) => {
    try {
      const resp = await api.post<LiveSkyResponse>("/api/v1/transit/live-sky", {
        datetime_utc: dt.toISOString(),
        latitude: 28.6139,
        longitude: 77.209,
        ayanamsa: "lahiri",
      });
      if (resp && resp.planets && resp.planets.length > 0) {
        startTransition(() => {
          setPlanets(
            resp.planets.map((p) => ({
              ...p,
              color: PLANET_COLORS[p.name] || "#e2e8f0",
            }))
          );
          setAyanamsaName(resp.ayanamsa ? resp.ayanamsa.toUpperCase() : "LAHIRI");
          setAyanamsaVal(resp.ayanamsa_value_deg || 24.23);
          setIsLoading(false);
        });
      }
    } catch (err) {
      console.error("LiveSky transit ephemeris error:", err);
      setIsLoading(false);
    }
  };

  // Live timer interval
  useEffect(() => {
    if (!isLiveMode) return;
    const initialNow = new Date();
    setCurrentDate(initialNow);
    fetchLiveSky(initialNow);

    const interval = setInterval(() => {
      const now = new Date();
      setCurrentDate(now);
      // Fetch backend ephemeris update periodically
      if (now.getSeconds() % 10 === 0) {
        fetchLiveSky(now);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isLiveMode]);

  // Step controls for historical scrubber
  const stepTime = (amount: number, unit: "hour" | "day" | "month" | "year") => {
    setIsLiveMode(false);
    const newDate = new Date(currentDate);
    if (unit === "hour") newDate.setHours(newDate.getHours() + amount);
    if (unit === "day") newDate.setDate(newDate.getDate() + amount);
    if (unit === "month") newDate.setMonth(newDate.getMonth() + amount);
    if (unit === "year") newDate.setFullYear(newDate.getFullYear() + amount);
    setCurrentDate(newDate);
    fetchLiveSky(newDate);
  };

  return (
    <div className="rounded-2xl border p-5 glass-card" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`flex h-3 w-3 rounded-full ${
                isLiveMode ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <h2 className="text-base font-bold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
              Live Celestial Transit &amp; Ephemeris Clock
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              SwissEph Sidereal ({ayanamsaName})
            </span>
          </div>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Real-time planetary motion stream with 8-fold Kakshya &amp; lunar node orbital indicators
          </p>
        </div>

        {/* Live / Scrubber Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Mode Switcher */}
          <div className="flex rounded-lg border p-0.5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <button
              type="button"
              onClick={() => {
                setIsLiveMode(true);
                const now = new Date();
                setCurrentDate(now);
                fetchLiveSky(now);
              }}
              className={`rounded-md px-3 py-1 text-xs font-bold transition-all flex items-center gap-1.5 ${
                isLiveMode ? "bg-emerald-500 text-slate-950 shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-slate-950" />
              LIVE NOW
            </button>
            <button
              type="button"
              onClick={() => setIsLiveMode(false)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
                !isLiveMode ? "bg-amber-500 text-slate-950 font-bold shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              Scrubber
            </button>
          </div>

          {/* Time Scrubber Buttons */}
          {!isLiveMode && (
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => stepTime(-1, "day")}
                className="rounded border px-2 py-1 text-xs font-mono bg-[var(--bg-input)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                style={{ borderColor: "var(--border-primary)" }}
              >
                -1d
              </button>
              <button
                type="button"
                onClick={() => stepTime(-1, "hour")}
                className="rounded border px-2 py-1 text-xs font-mono bg-[var(--bg-input)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                style={{ borderColor: "var(--border-primary)" }}
              >
                -1h
              </button>
              <button
                type="button"
                onClick={() => stepTime(1, "hour")}
                className="rounded border px-2 py-1 text-xs font-mono bg-[var(--bg-input)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                style={{ borderColor: "var(--border-primary)" }}
              >
                +1h
              </button>
              <button
                type="button"
                onClick={() => stepTime(1, "day")}
                className="rounded border px-2 py-1 text-xs font-mono bg-[var(--bg-input)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                style={{ borderColor: "var(--border-primary)" }}
              >
                +1d
              </button>
            </div>
          )}

          {/* Timestamp Display */}
          <div className="rounded-xl border px-3 py-1 font-mono text-xs flex items-center gap-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
            <span className="text-[var(--text-muted)]">{isLiveMode ? "UTC:" : "EPHEM:"}</span>
            <span className="text-[var(--accent)] font-bold">
              {currentDate.toISOString().replace("T", " ").slice(0, 19)}
            </span>
          </div>
        </div>
      </div>

      {/* 9 Planetary Cards Grid */}
      {isLoading && planets.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center gap-2 text-center text-xs text-slate-400">
          <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
          <p>Calculating live Swiss Ephemeris planetary positions…</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-5">
          {planets.map((p) => (
            <div
              key={p.name}
            className="rounded-xl border p-3.5 flex flex-col justify-between transition-all hover:border-[var(--accent)]"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
          >
            {/* Card Header: Symbol & Flags */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold" style={{ color: p.color }}>
                  {p.symbol}
                </span>
                <span className="font-semibold text-xs text-[var(--text-primary)]">{p.name}</span>
              </div>

              <div className="flex items-center gap-1">
                {p.is_lunar_node && (
                  <span
                    title="Calculated Lunar Orbital Node (not a physical mass body)"
                    className="rounded bg-purple-500/20 px-1 py-0.2 text-[9px] font-bold text-purple-300 border border-purple-500/30"
                  >
                    Node
                  </span>
                )}
                {p.is_retrograde && (
                  <span className="rounded bg-rose-500/20 px-1 py-0.2 text-[10px] font-bold text-rose-400 border border-rose-500/30">
                    Rx
                  </span>
                )}
                {p.is_combust && (
                  <span className="rounded bg-amber-500/20 px-1 py-0.2 text-[10px] font-bold text-amber-400 border border-amber-500/30">
                    C
                  </span>
                )}
              </div>
            </div>

            {/* Position Details */}
            <div className="mt-2.5 space-y-1">
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-bold text-amber-400">{p.rashi_sanskrit}</span>
                <span className="font-mono text-xs font-bold text-[var(--accent)]">{p.degree_formatted}</span>
              </div>

              <div className="text-[11px] flex items-center justify-between text-[var(--text-muted)]">
                <span>{p.nakshatra} (P{p.pada})</span>
                <span className="font-mono text-[10px]">{p.speed_deg_per_day > 0 ? `+${p.speed_deg_per_day.toFixed(2)}` : p.speed_deg_per_day.toFixed(2)}°/d</span>
              </div>
            </div>

            {/* Kakshya Lord Sub-Segment Badge */}
            <div className="mt-2.5 pt-2 border-t flex justify-between items-center text-[10px]" style={{ borderColor: "var(--border-primary)" }}>
              <span className="text-[var(--text-muted)]">Kakshya #{p.kakshya_index + 1}:</span>
              <span className="font-semibold text-cyan-300 font-mono">
                {p.kakshya_lord}
              </span>
            </div>
          </div>
        ))}
      </div>
      )}

      {/* Ephemeris Summary Banner */}
      <div className="rounded-xl border p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
        <div className="flex items-center gap-2">
          <span className="text-base">⚡</span>
          <span style={{ color: "var(--text-primary)" }}>
            Ayanamsa Offset: <span className="font-bold text-amber-400">{ayanamsaName} @ {ayanamsaVal.toFixed(4)}°</span> · Rahu &amp; Ketu computed as True/Mean Astronomical Lunar Nodes
          </span>
        </div>
        <span className="text-[11px] text-emerald-400 font-mono font-medium">
          Authoritative Engine: SwissEph v2.10.03
        </span>
      </div>
    </div>
  );
}

