"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface LiveGrahaPosition {
  name: string;
  symbol: string;
  rashi: string;
  rashi_index: number;
  degree_in_rashi: number;
  total_degree: number;
  speed_deg_per_day: number;
  is_retrograde: boolean;
  nakshatra: string;
  pada: number;
}

interface TransitAspectAlert {
  transiting_planet: string;
  natal_planet: string;
  aspect_type: string;
  orb_degree: number;
  is_exact: boolean;
  description: string;
  impact_level: string;
}

interface LiveSkyTransitReport {
  timestamp_utc: string;
  planets: LiveGrahaPosition[];
  aspect_alerts: TransitAspectAlert[];
  summary_message: string;
}

interface LiveSkyTransitClockProps {
  nativeName?: string;
  natalLagnaRashi?: string;
}

export function LiveSkyTransitClock({ nativeName = "Native" }: LiveSkyTransitClockProps) {
  const [data, setData] = useState<LiveSkyTransitReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchLiveSky() {
      setLoading(true);
      try {
        const res = await api.get<LiveSkyTransitReport>("/api/v1/phalita/live-sky");
        setData(res);
      } catch (err: any) {
        setError(err.message || "Failed to load live celestial transits.");
      } finally {
        setLoading(false);
      }
    }
    fetchLiveSky();
  }, []);

  return (
    <div className="space-y-6 text-slate-900 dark:text-slate-100">
      {/* Header Banner */}
      <div className="p-6 bg-gradient-to-r from-amber-50 via-white to-cyan-50 dark:from-amber-950/30 dark:via-slate-900 dark:to-cyan-950/40 border border-amber-200 dark:border-amber-500/30 rounded-3xl shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🪐</span>
              <span className="px-3 py-1 bg-amber-100 dark:bg-amber-500/20 text-amber-900 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40 rounded-full text-xs font-bold uppercase tracking-wider">
                Live Sky Gochara Orbit & Real-Time Ephemeris Clock
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-black text-slate-900 dark:text-white">
              Real-Time Celestial Transit Engine
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 max-w-3xl leading-relaxed font-medium">
              Tracking real-time sidereal graha positions across the 360° Nirayana zodiac with day-level micro-timing alerts.
            </p>
          </div>

          <div className="text-right">
            <div className="text-xs font-mono text-cyan-800 dark:text-cyan-400 bg-white/90 dark:bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm font-bold">
              Live UTC: {data ? new Date(data.timestamp_utc).toUTCString() : "Syncing..."}
            </div>
          </div>
        </div>
      </div>

      {loading && (
        <div className="p-12 text-center text-slate-500 text-sm">
          <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-amber-500 border-t-transparent mb-2" />
          <div>Calculating real-time celestial ephemeris coordinates...</div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-rose-800 dark:text-rose-300 text-xs">
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Live Planetary Table */}
          <div className="lg:col-span-7 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span>🌌</span> Today&apos;s Sky Graha Positions (Gochara)
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">Nirayana Lahiri</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {data.planets.map((p) => (
                <div
                  key={p.name}
                  className="p-3.5 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800/90 rounded-xl space-y-1 hover:border-amber-400 dark:hover:border-amber-500/50 transition shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
                      <span>{p.symbol}</span>
                      <span>{p.name}</span>
                    </span>
                    {p.is_retrograde && (
                      <span className="px-1.5 py-0.2 bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-500/40 text-[9px] font-bold rounded">
                        Rx
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    {p.degree_in_rashi.toFixed(2)}° {p.rashi}
                  </div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate">
                    {p.nakshatra} (P{p.pada})
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Micro-Timing Aspect Alerts */}
          <div className="lg:col-span-5 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>⚡</span> Real-Time Transit Aspect Alerts
            </h3>

            {data.aspect_alerts.length === 0 ? (
              <div className="p-6 bg-slate-50 dark:bg-slate-950/60 rounded-xl border border-slate-200 dark:border-slate-800/80 text-center text-xs text-slate-500 dark:text-slate-400">
                No acute close-orb (&lt; 1.5°) conjunctions today. Celestial transit motions are steady and progressive.
              </div>
            ) : (
              <div className="space-y-2.5">
                {data.aspect_alerts.map((alert, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-50 dark:bg-slate-950/80 border border-amber-200 dark:border-amber-500/30 rounded-xl space-y-1.5 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-800 dark:text-amber-300">
                        {alert.transiting_planet} ➔ {alert.natal_planet}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                          alert.impact_level === "Landmark"
                            ? "bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40"
                            : alert.impact_level === "Favorable"
                            ? "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40"
                            : "bg-cyan-100 dark:bg-cyan-500/20 text-cyan-800 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-500/40"
                        }`}
                      >
                        {alert.aspect_type}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-700 dark:text-slate-300 leading-snug font-medium">
                      {alert.description}
                    </p>
                    <div className="text-[10px] text-slate-500 font-mono">
                      Exact Orb: {alert.orb_degree.toFixed(2)}°
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
