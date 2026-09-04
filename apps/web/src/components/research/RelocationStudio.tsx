"use client";

import React, { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { useActiveChart } from "@/lib/charts";
import { Card, Button, Badge, Select, type SelectOption } from "@/components/ui";
import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import type { PlaceResultResponse } from "@/lib/types";

interface Trigger {
  rule_id: string;
  rule_name: string;
  role: string;
  status: "triggered" | "not_triggered" | "insufficient_data";
  provenance: string;
  matched_conditions: string[];
  failed_conditions: string[];
  missing_facts: string[];
  explanation: string;
}

interface TechniqueResult {
  technique_id: string;
  technique_name: string;
  confidence: number;
  confidence_basis: string;
  is_matched: boolean;
  triggers: Trigger[];
}

interface AngleInfo {
  degree: number;
  sign: string;
  label: number;
  harmonic_family: string;
}

interface RelocationAnalyzeResponse {
  birth: { lat: number; lon: number };
  target: { lat: number; lon: number };
  angles: { ascendant: AngleInfo; midheaven: AngleInfo };
  techniques: TechniqueResult[];
  facts: Record<string, unknown>;
}

const HARMONIC_LABELS: Record<string, string> = {
  ninth: "9th harmonic — comfort zone / natural alignment",
  fifth: "5th harmonic — creative / expressive intelligence",
  seventh: "7th harmonic — discipline / relationship focus",
};

const POPULAR_DESTINATIONS = [
  { name: "New York, USA", lat: 40.7128, lon: -74.0060 },
  { name: "London, UK", lat: 51.5074, lon: -0.1278 },
  { name: "Dubai, UAE", lat: 25.2048, lon: 55.2708 },
  { name: "Singapore", lat: 1.3521, lon: 103.8198 },
  { name: "Tokyo, Japan", lat: 35.6762, lon: 139.6503 },
  { name: "Sydney, Australia", lat: -33.8688, lon: 151.2093 },
  { name: "Toronto, Canada", lat: 43.6532, lon: -79.3832 },
  { name: "Mumbai, India", lat: 19.0760, lon: 72.8777 },
];

export function RelocationStudio() {
  const { activeSummary, myCharts, selectChart, isLoading: isLoadingCharts } = useActiveChart();

  // Birth state
  const [selectedChartId, setSelectedChartId] = useState<string>("");
  const [birthUtc, setBirthUtc] = useState<string>("1990-01-01T12:00:00Z");
  const [birthLat, setBirthLat] = useState<number>(28.6139);
  const [birthLon, setBirthLon] = useState<number>(77.2090);
  const [birthPlaceName, setBirthPlaceName] = useState<string>("New Delhi, India");

  // Target relocation state
  const [targetSearchText, setTargetSearchText] = useState<string>("New York, USA");
  const [targetPlace, setTargetPlace] = useState<PlaceResultResponse | null>(null);
  const [targetLat, setTargetLat] = useState<number>(40.7128);
  const [targetLon, setTargetLon] = useState<number>(-74.0060);
  const [ayanamsa, setAyanamsa] = useState<string>("lahiri");

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RelocationAnalyzeResponse | null>(null);

  // Sync with user's active/default chart
  useEffect(() => {
    if (activeSummary) {
      setSelectedChartId(activeSummary.id);
      setBirthUtc(activeSummary.birth_datetime_utc);
      setBirthLat(activeSummary.birth_latitude);
      setBirthLon(activeSummary.birth_longitude);
      setBirthPlaceName(activeSummary.place_name || "Birth Location");
      if (activeSummary.ayanamsa) {
        setAyanamsa(activeSummary.ayanamsa.toLowerCase());
      }
    }
  }, [activeSummary]);

  // Chart dropdown options
  const chartOptions: SelectOption[] = useMemo(() => {
    return myCharts.map((c) => ({
      value: c.id,
      label: `${c.subject_name} (${c.place_name || "Unknown"} · ${new Date(c.birth_datetime_utc).toLocaleDateString()})${c.is_default ? " ★ Default" : ""}`,
    }));
  }, [myCharts]);

  const handleChartChange = (chartId: string) => {
    setSelectedChartId(chartId);
    const found = myCharts.find((c) => c.id === chartId);
    if (found) {
      selectChart(found);
    }
  };

  const handleTargetSelect = (place: PlaceResultResponse) => {
    setTargetPlace(place);
    setTargetSearchText(place.display_name);
    setTargetLat(place.latitude);
    setTargetLon(place.longitude);
  };

  const handleDestinationPreset = (dest: { name: string; lat: number; lon: number }) => {
    setTargetSearchText(dest.name);
    setTargetLat(dest.lat);
    setTargetLon(dest.lon);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.post<RelocationAnalyzeResponse>(
        "/api/v1/relocation/analyze",
        {
          birth_utc: birthUtc,
          birth_lat: birthLat,
          birth_lon: birthLon,
          target_lat: targetLat,
          target_lon: targetLon,
          ayanamsa,
        },
      );
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  // Run analysis automatically when chart or target changes if ready
  useEffect(() => {
    if (birthUtc && birthLat != null && targetLat != null) {
      handleAnalyze();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedChartId]);

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xl font-bold">
                🧭
              </span>
              <div>
                <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  Relocation &amp; Astro-Cartography Studio
                </h1>
                <p className="text-xs text-slate-600 dark:text-slate-400 font-mono mt-0.5">
                  Evaluate world line projections, horizon shifts, paran crossings, and relocated Bhava angularities.
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="cyan" dot>
              Live Planetary Engine
            </Badge>
            <Badge tone="neutral">
              Astro-Cartography v2.3
            </Badge>
          </div>
        </div>
      </Card>

      {/* Input / Selector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Active Natal Chart */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-cyan-500 dark:text-cyan-400">
                1. Natal Birth Chart
              </span>
            </div>
            {activeSummary && (
              <Badge tone="gold">
                {activeSummary.subject_name}
              </Badge>
            )}
          </div>

          {chartOptions.length > 0 ? (
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Select Saved User Chart
              </label>
              <Select
                options={chartOptions}
                value={selectedChartId}
                onChange={handleChartChange}
                placeholder="Choose chart..."
              />
            </div>
          ) : (
            <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-xs text-amber-300">
              No saved birth charts found. Using default baseline coordinates.
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs">
              <span className="text-slate-500 dark:text-slate-400 block font-mono">Birth Place</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100 truncate block mt-0.5">
                {birthPlaceName}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs">
              <span className="text-slate-500 dark:text-slate-400 block font-mono">Birth UTC</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100 block mt-0.5 font-mono">
                {birthUtc ? new Date(birthUtc).toLocaleString() : "—"}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400 font-mono">Natal Latitude: </span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-200">{birthLat.toFixed(4)}°</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400 font-mono">Natal Longitude: </span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-200">{birthLon.toFixed(4)}°</span>
            </div>
          </div>
        </Card>

        {/* Right: Relocation Target Location */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-sm font-semibold text-violet-500 dark:text-violet-400">
              2. Relocation Target Destination
            </span>
            <Badge tone="violet">
              Target Horizon
            </Badge>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Search Target City / Location
            </label>
            <BirthPlaceSearch
              value={targetSearchText}
              onChange={setTargetSearchText}
              onSelect={handleTargetSelect}
            />
          </div>

          <div>
            <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 block mb-1.5 font-mono">
              Quick World Destinations:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {POPULAR_DESTINATIONS.map((dest) => (
                <button
                  key={dest.name}
                  type="button"
                  onClick={() => handleDestinationPreset(dest)}
                  className={`px-2.5 py-1 rounded-md text-xs font-mono transition border ${
                    targetSearchText === dest.name
                      ? "bg-violet-500/20 text-violet-400 border-violet-500/40 font-bold"
                      : "bg-slate-100 dark:bg-slate-800/70 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-violet-500/50"
                  }`}
                >
                  {dest.name}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1 text-xs">
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400 font-mono">Target Lat: </span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-200">{targetLat.toFixed(4)}°</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400 font-mono">Target Lon: </span>
              <span className="font-mono font-medium text-slate-900 dark:text-slate-200">{targetLon.toFixed(4)}°</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between gap-4">
        <Button
          variant="primary"
          onClick={handleAnalyze}
          disabled={loading}
          className="font-bold flex items-center gap-2"
        >
          {loading ? (
            <>
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
              Computing Relocation Matrix…
            </>
          ) : (
            <>
              <span>⚡</span> Run Relocation Analysis
            </>
          )}
        </Button>

        {result && (
          <span className="text-xs text-slate-500 font-mono">
            Evaluated {result.techniques.length} Shastric relocation techniques
          </span>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-xs font-medium text-rose-400">
          ⚠️ {error}
        </div>
      )}

      {/* Analysis Results Display */}
      {result && (
        <div className="space-y-6">
          {/* Relocated Angles Card */}
          <Card className="p-6">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Relocated Angles &amp; Axis Shift
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Astronomical horizon orientation at {targetSearchText}
                </p>
              </div>
              <Badge tone="cyan">Target Coordinates</Badge>
            </div>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              {(["ascendant", "midheaven"] as const).map((key) => {
                const angle = result.angles[key];
                return (
                  <div
                    key={key}
                    className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
                        {key === "ascendant" ? "Lagna / Ascendant (Relocated)" : "Midheaven (MC / Karma)"}
                      </span>
                      <Badge tone={key === "ascendant" ? "cyan" : "violet"}>
                        {angle.sign}
                      </Badge>
                    </div>
                    <div className="my-2">
                      <span className="text-2xl font-black text-slate-900 dark:text-slate-100 font-mono">
                        {angle.sign} {angle.degree.toFixed(2)}°
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-mono border-t border-slate-200 dark:border-slate-800/80 pt-2 mt-1">
                      {HARMONIC_LABELS[angle.harmonic_family] ?? angle.harmonic_family}
                    </p>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* 6 Comprehensive Shastric Life Domains */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <span>📊</span> Life Domain Relocation Suitability
                </h2>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  How moving to {targetSearchText} impacts various life spheres based on active Shastric techniques
                </p>
              </div>
              <Badge tone="cyan">
                {result.techniques.filter((t) => t.is_matched).length} Techniques Active
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* 1. Career & Public Status */}
              <Card className="p-5 border-l-4 border-l-amber-500 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>💼</span> Career &amp; Status
                    </span>
                    <Badge tone={result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "success" : "neutral"}>
                      {result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "High Support" : "Moderate"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                    Evaluates professional visibility, authority, leadership, and employment recognition at this longitude.
                  </p>
                  <div className="mt-3 space-y-1.5 text-[11px] font-mono">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>10th House Axis (MC):</span>
                      <span className="text-slate-900 dark:text-slate-200 font-bold">{result.angles.midheaven.sign}</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Sun Angularity:</span>
                      <span className={result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "text-emerald-500 font-bold" : "text-slate-400"}>
                        {result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "Active (You Shine)" : "Neutral"}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-600 dark:text-slate-400">
                  💡 Best for career expansions, interviews, and public enterprise.
                </div>
              </Card>

              {/* 2. Mental Peace & Domestic Comfort */}
              <Card className="p-5 border-l-4 border-l-cyan-500 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>🏡</span> Mental Peace &amp; Home
                    </span>
                    <Badge tone={result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched) ? "success" : "neutral"}>
                      {result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched) ? "Harmonic Comfort" : "Neutral"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                    Evaluates psychological well-being, feelings of belonging, family harmony, and emotional bonding.
                  </p>
                  <div className="mt-3 space-y-1.5 text-[11px] font-mono">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Comfort Zone Relation:</span>
                      <span className={result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched) ? "text-cyan-500 font-bold" : "text-slate-400"}>
                        {result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched) ? "9th-Harmonic Aligned" : "Standard"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Ascendant Harmony:</span>
                      <span className="text-slate-900 dark:text-slate-200">{result.angles.ascendant.harmonic_family}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-600 dark:text-slate-400">
                  💡 High emotional grounding and feeling at home without alienation.
                </div>
              </Card>

              {/* 3. Wealth & Financial Influx */}
              <Card className="p-5 border-l-4 border-l-emerald-500 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>💰</span> Wealth &amp; Commercial Gains
                    </span>
                    <Badge tone="gold">Dhana Potential</Badge>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                    Evaluates financial liquidity, business negotiations, asset generation, and commercial partnerships.
                  </p>
                  <div className="mt-3 space-y-1.5 text-[11px] font-mono">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Active Confluences (Parans):</span>
                      <span className="text-slate-900 dark:text-slate-200 font-bold">
                        {String(result.facts["relocation.paran.count"] ?? 0)} Active
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Midpoint Influx:</span>
                      <span className="text-slate-900 dark:text-slate-200">
                        {String(result.facts["relocation.midpoints.mc.count"] ?? 0)} MC Triggers
                      </span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-600 dark:text-slate-400">
                  💡 Commercial contacts and investment returns supported at this location.
                </div>
              </Card>

              {/* 4. Relationships & Marriage */}
              <Card className="p-5 border-l-4 border-l-rose-500 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>❤️</span> Marriage &amp; Partnerships
                    </span>
                    <Badge tone="violet">7th Axis Focus</Badge>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                    Evaluates relationship harmony, meeting significant others, mutual agreements, and marital stability.
                  </p>
                  <div className="mt-3 space-y-1.5 text-[11px] font-mono">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Relocated 7th Cusp (Desc):</span>
                      <span className="text-slate-900 dark:text-slate-200 font-bold">Opposite {result.angles.ascendant.sign}</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Venus/Moon Energy:</span>
                      <span className="text-slate-900 dark:text-slate-200">Relational Harmony</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-600 dark:text-slate-400">
                  💡 Favorable for cooperative partnerships and meeting influential companions.
                </div>
              </Card>

              {/* 5. Health, Stability & Risk Warnings */}
              <Card className="p-5 border-l-4 border-l-red-500 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>⚠️</span> Stability &amp; Risk Audit
                    </span>
                    <Badge tone={result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched) ? "danger" : "success"}>
                      {result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched) ? "Volatile / Sudden" : "Low Risk"}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                    Evaluates sudden unexpected shocks, volatility, health vulnerability, and need for grounding.
                  </p>
                  <div className="mt-3 space-y-1.5 text-[11px] font-mono">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Disruption Indicator:</span>
                      <span className={result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched) ? "text-rose-500 font-bold" : "text-emerald-500 font-bold"}>
                        {result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched) ? "Active Volatility" : "Calm & Stable"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Friction Index:</span>
                      <span className="text-slate-900 dark:text-slate-200">Normal Range</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-600 dark:text-slate-400">
                  {result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched)
                    ? "⚠️ Caution advised against hasty long-term commitments here."
                    : "✅ Safe for long-term physical health and predictable routines."}
                </div>
              </Card>

              {/* 6. Strategic Usage Recommendation */}
              <Card className="p-5 border-l-4 border-l-indigo-500 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>🎯</span> Optimal Engagement Mode
                    </span>
                    <Badge tone="cyan">Strategic Action</Badge>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                    Determines how native should tap into this location: Full Relocation, Short Trips, or Remote Business.
                  </p>
                  <div className="mt-3 space-y-1.5 text-[11px] font-mono">
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Recommended Mode:</span>
                      <span className="text-cyan-500 dark:text-cyan-400 font-bold">
                        {result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "Permanent Relocation" : "Travel / Remote Ventures"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500">
                      <span>Energy Absorption:</span>
                      <span className="text-slate-900 dark:text-slate-200">Direct Contact</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-600 dark:text-slate-400">
                  💡 Even if not moving permanently, traveling here charges beneficial natal promises.
                </div>
              </Card>
            </div>
          </div>

          {/* Research & Shastric Evidence Inspection Accordion */}
          <Card className="p-6">
            <details className="group">
              <summary className="cursor-pointer list-none flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    🔬 Technical Shastric &amp; Astro-Cartography Evidence (All 12 Evaluated Techniques)
                  </span>
                  <Badge tone="neutral">Researcher Audit</Badge>
                </div>
                <span className="text-xs text-slate-400 font-mono transition-transform group-open:rotate-180">
                  ▼
                </span>
              </summary>

              <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.techniques.map((tech) => (
                  <div
                    key={tech.technique_id}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
                            {tech.technique_name}
                          </h4>
                          <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                            {tech.confidence_basis}
                          </p>
                        </div>
                        <Badge tone={tech.is_matched ? "success" : "neutral"}>
                          {tech.confidence}%
                        </Badge>
                      </div>

                      <div className="mt-3 space-y-2">
                        {tech.triggers.map((t) => (
                          <div
                            key={t.rule_id}
                            className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800/60 bg-white dark:bg-slate-900/60 text-[11px]"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-semibold text-slate-800 dark:text-slate-200">
                                {t.rule_name}
                              </span>
                              <Badge
                                tone={
                                  t.status === "triggered"
                                    ? "success"
                                    : t.status === "insufficient_data"
                                    ? "gold"
                                    : "neutral"
                                }
                              >
                                {t.status.replace(/_/g, " ")}
                              </Badge>
                            </div>

                            {t.explanation && (
                              <p className="mt-1 text-[10px] text-slate-600 dark:text-slate-400 leading-relaxed">
                                {t.explanation}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </details>
          </Card>
        </div>
      )}
    </div>
  );
}
