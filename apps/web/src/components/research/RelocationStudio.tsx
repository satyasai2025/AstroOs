"use client";

import React, { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { useActiveChart } from "@/lib/charts";
import { Card, Button, Badge, Select, Modal, type SelectOption } from "@/components/ui";
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

const MOTIVE_OPTIONS = [
  { id: "all", label: "General Audit", icon: "🌐" },
  { id: "career", label: "Career & Business", icon: "💼" },
  { id: "mental_peace", label: "Peace of Mind & Home", icon: "🏡" },
  { id: "wealth", label: "Wealth & Finance", icon: "💰" },
  { id: "marriage", label: "Marriage & Love", icon: "❤️" },
  { id: "health_risk", label: "Health & Stability", icon: "🛡️" },
];

function CoordinatesHelpButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="What are Target Coordinates?"
      className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-slate-200 dark:bg-slate-700/80 hover:bg-violet-500 hover:text-white dark:hover:bg-violet-600 text-slate-600 dark:text-slate-300 text-[10px] font-bold cursor-pointer transition"
      title="Click to learn about Target Coordinates & Orbs"
    >
      ?
    </button>
  );
}

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
  const [selectedMotive, setSelectedMotive] = useState<string>("all");
  const [isCustomCoords, setIsCustomCoords] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RelocationAnalyzeResponse | null>(null);

  // Modals state
  const [isCoordsModalOpen, setIsCoordsModalOpen] = useState<boolean>(false);
  const [selectedDomainForModal, setSelectedDomainForModal] = useState<string | null>(null);

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

          {/* Moving Motive / Priority */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 font-mono">
                Your Primary Motive (Optional):
              </span>
              {selectedMotive !== "all" && (
                <button
                  type="button"
                  onClick={() => setSelectedMotive("all")}
                  className="text-[10px] text-violet-500 hover:underline font-mono"
                >
                  Clear
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {MOTIVE_OPTIONS.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedMotive(m.id)}
                  className={`px-2.5 py-1 rounded-md text-xs font-mono transition border ${
                    selectedMotive === m.id
                      ? "bg-violet-600 text-white border-violet-600 font-bold shadow-sm"
                      : "bg-slate-100 dark:bg-slate-800/70 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-violet-500/50"
                  }`}
                >
                  <span className="mr-1">{m.icon}</span> {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-1">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 font-mono">
                  Target Coordinates
                </span>
                <CoordinatesHelpButton onClick={() => setIsCoordsModalOpen(true)} />
                <button
                  type="button"
                  onClick={() => setIsCustomCoords(!isCustomCoords)}
                  className="text-[10px] text-violet-500 hover:text-violet-600 dark:hover:text-violet-400 font-mono underline ml-1 cursor-pointer font-bold"
                >
                  {isCustomCoords ? "✓ Done" : "✎ Custom Lat/Lon"}
                </button>
              </div>
              <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                Core radius: ≤ 1.0° (~110 km)
              </span>
            </div>

            {isCustomCoords ? (
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-violet-500/10 border border-violet-500/30">
                  <label className="text-[10px] font-mono text-violet-600 dark:text-violet-400 font-bold block mb-1">
                    Custom Latitude (-90° to +90°):
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    min="-90"
                    max="90"
                    value={targetLat}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0;
                      setTargetLat(val);
                      setTargetSearchText(`Custom Coordinates (${val.toFixed(2)}°, ${targetLon.toFixed(2)}°)`);
                    }}
                    className="w-full px-2 py-1 rounded bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 font-mono font-bold text-slate-900 dark:text-slate-100 text-xs focus:ring-1 focus:ring-violet-500 focus:outline-hidden"
                  />
                </div>
                <div className="p-2.5 rounded-lg bg-violet-500/10 border border-violet-500/30">
                  <label className="text-[10px] font-mono text-violet-600 dark:text-violet-400 font-bold block mb-1">
                    Custom Longitude (-180° to +180°):
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    min="-180"
                    max="180"
                    value={targetLon}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0;
                      setTargetLon(val);
                      setTargetSearchText(`Custom Coordinates (${targetLat.toFixed(2)}°, ${val.toFixed(2)}°)`);
                    }}
                    className="w-full px-2 py-1 rounded bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 font-mono font-bold text-slate-900 dark:text-slate-100 text-xs focus:ring-1 focus:ring-violet-500 focus:outline-hidden"
                  />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-500 dark:text-slate-400 font-mono">Latitude: </span>
                  <span className="font-mono font-medium text-slate-900 dark:text-slate-200">{targetLat.toFixed(4)}°</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-500 dark:text-slate-400 font-mono">Longitude: </span>
                  <span className="font-mono font-medium text-slate-900 dark:text-slate-200">{targetLon.toFixed(4)}°</span>
                </div>
              </div>
            )}
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
              <div className="flex items-center gap-1.5">
                <Badge tone="cyan">Target Coordinates</Badge>
                <CoordinatesHelpButton onClick={() => setIsCoordsModalOpen(true)} />
              </div>
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
                  <span>📊</span> 6 Life Domains Relocation Suitability
                </h2>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  Synthesized from all {result.techniques.length} Shastric relocation techniques into 6 actionable life spheres for {targetSearchText}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge tone="cyan">
                  {result.techniques.filter((t) => t.is_matched).length} of {result.techniques.length} Techniques Active
                </Badge>
                <Badge tone="violet">
                  6 Life Domains
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* 1. Career & Public Status */}
              <Card
                className={`p-5 border-l-4 border-l-amber-500 flex flex-col justify-between cursor-pointer hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-700 transition-all ${
                  selectedMotive === "career" ? "ring-2 ring-amber-500/80 bg-amber-500/5 shadow-md" : ""
                }`}
                onClick={() => setSelectedDomainForModal("career")}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>💼</span> Career &amp; Status
                    </span>
                    <div className="flex items-center gap-1">
                      {selectedMotive === "career" && (
                        <Badge tone="gold">🎯 Motive</Badge>
                      )}
                      <Badge tone={result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "success" : "neutral"}>
                        {result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "High Support" : "Moderate"}
                      </Badge>
                    </div>
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
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400">
                  <span>💡 Best for career expansions &amp; authority.</span>
                  <span className="text-amber-500 dark:text-amber-400 font-bold font-mono hover:underline">Deep Dive ↗</span>
                </div>
              </Card>

              {/* 2. Mental Peace & Domestic Comfort */}
              <Card
                className={`p-5 border-l-4 border-l-cyan-500 flex flex-col justify-between cursor-pointer hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-700 transition-all ${
                  selectedMotive === "mental_peace" ? "ring-2 ring-cyan-500/80 bg-cyan-500/5 shadow-md" : ""
                }`}
                onClick={() => setSelectedDomainForModal("mental_peace")}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>🏡</span> Mental Peace &amp; Home
                    </span>
                    <div className="flex items-center gap-1">
                      {selectedMotive === "mental_peace" && (
                        <Badge tone="cyan">🎯 Motive</Badge>
                      )}
                      <Badge tone={result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched) ? "success" : "neutral"}>
                        {result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched) ? "Harmonic Comfort" : "Neutral"}
                      </Badge>
                    </div>
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
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400">
                  <span>💡 Emotional grounding &amp; home feeling.</span>
                  <span className="text-cyan-500 dark:text-cyan-400 font-bold font-mono hover:underline">Deep Dive ↗</span>
                </div>
              </Card>

              {/* 3. Wealth & Financial Influx */}
              <Card
                className={`p-5 border-l-4 border-l-emerald-500 flex flex-col justify-between cursor-pointer hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-700 transition-all ${
                  selectedMotive === "wealth" ? "ring-2 ring-emerald-500/80 bg-emerald-500/5 shadow-md" : ""
                }`}
                onClick={() => setSelectedDomainForModal("wealth")}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>💰</span> Wealth &amp; Gains
                    </span>
                    <div className="flex items-center gap-1">
                      {selectedMotive === "wealth" && (
                        <Badge tone="success">🎯 Motive</Badge>
                      )}
                      <Badge tone="gold">Dhana Potential</Badge>
                    </div>
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
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400">
                  <span>💡 Commercial contacts &amp; investments.</span>
                  <span className="text-emerald-500 dark:text-emerald-400 font-bold font-mono hover:underline">Deep Dive ↗</span>
                </div>
              </Card>

              {/* 4. Relationships & Marriage */}
              <Card
                className={`p-5 border-l-4 border-l-rose-500 flex flex-col justify-between cursor-pointer hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-700 transition-all ${
                  selectedMotive === "marriage" ? "ring-2 ring-rose-500/80 bg-rose-500/5 shadow-md" : ""
                }`}
                onClick={() => setSelectedDomainForModal("marriage")}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>❤️</span> Marriage &amp; Partnerships
                    </span>
                    <div className="flex items-center gap-1">
                      {selectedMotive === "marriage" && (
                        <Badge tone="violet">🎯 Motive</Badge>
                      )}
                      <Badge tone="violet">7th Axis Focus</Badge>
                    </div>
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
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400">
                  <span>💡 Cooperative bonds &amp; romance.</span>
                  <span className="text-rose-500 dark:text-rose-400 font-bold font-mono hover:underline">Deep Dive ↗</span>
                </div>
              </Card>

              {/* 5. Health, Stability & Risk Warnings */}
              <Card
                className={`p-5 border-l-4 border-l-red-500 flex flex-col justify-between cursor-pointer hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-700 transition-all ${
                  selectedMotive === "health_risk" ? "ring-2 ring-red-500/80 bg-red-500/5 shadow-md" : ""
                }`}
                onClick={() => setSelectedDomainForModal("health_risk")}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>⚠️</span> Stability &amp; Risk Audit
                    </span>
                    <div className="flex items-center gap-1">
                      {selectedMotive === "health_risk" && (
                        <Badge tone="danger">🎯 Motive</Badge>
                      )}
                      <Badge tone={result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched) ? "danger" : "success"}>
                        {result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched) ? "Volatile / Sudden" : "Low Risk"}
                      </Badge>
                    </div>
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
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400">
                  <span>
                    {result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched)
                      ? "⚠️ Caution: High volatility."
                      : "✅ Safe for physical health."}
                  </span>
                  <span className="text-rose-500 dark:text-rose-400 font-bold font-mono hover:underline">Deep Dive ↗</span>
                </div>
              </Card>

              {/* 6. Strategic Usage Recommendation */}
              <Card
                className="p-5 border-l-4 border-l-indigo-500 flex flex-col justify-between cursor-pointer hover:shadow-lg hover:border-slate-300 dark:hover:border-slate-700 transition-all"
                onClick={() => setSelectedDomainForModal("strategy")}
              >
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
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-400">
                  <span>💡 Timing &amp; engagement style.</span>
                  <span className="text-indigo-500 dark:text-indigo-400 font-bold font-mono hover:underline">Deep Dive ↗</span>
                </div>
              </Card>
            </div>
          </div>

          {/* Research & Shastric Evidence Inspection Accordion */}
          <Card className="p-6">
            <details className="group">
              <summary className="cursor-pointer list-none flex items-center justify-between">
                <div className="flex items-center flex-wrap gap-2">
                  <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    🔬 Shastric &amp; Astro-Cartography Evidence Audit
                  </span>
                  <Badge tone="violet">{result.techniques.length} Techniques Evaluated</Badge>
                  <span className="text-xs text-violet-500 dark:text-violet-400 font-mono">
                    (Click to inspect all {result.techniques.length} individual mathematical techniques)
                  </span>
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

      {/* Target Coordinates & Orbs Guide Modal */}
      <Modal
        open={isCoordsModalOpen}
        onClose={() => setIsCoordsModalOpen(false)}
        title="📍 Target Coordinates & Relocation Orbs Guide"
        width={580}
      >
        <div className="space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-slate-800 dark:text-slate-200">
            <h4 className="font-bold text-violet-600 dark:text-violet-400 text-sm mb-1 flex items-center gap-1.5">
              <span>🌐</span> Why Relocation is Coordinate-Based (Not Country-Based)
            </h4>
            <p className="leading-relaxed">
              Astrology maps the celestial sky and planetary kendras (angles) at the exact moment of your birth. A single country like the USA, India, or Canada covers thousands of kilometers and spans several time zones.
            </p>
            <p className="mt-1.5 leading-relaxed text-slate-600 dark:text-slate-400">
              For example, New York and Los Angeles are ~43° apart in longitude — shifting your chart by 3 full houses! Therefore, AstroOS evaluates the <strong>exact Latitude and Longitude</strong> of your destination city to ensure 100% astronomical accuracy.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-slate-900 dark:text-slate-100 text-sm mb-2">
              The 3 Proximity &amp; Degree Zones (Orbs of Influence)
            </h4>
            <div className="space-y-2">
              <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5">
                <div className="flex items-center justify-between font-bold text-emerald-600 dark:text-emerald-400 mb-0.5">
                  <span>Zone 1: Peak Core Zone</span>
                  <Badge tone="success">≤ 1.0° Orb (~110 km / 70 mi)</Badge>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-300">
                  Direct, maximum manifestation. Living inside this radius brings the full, acute power of planetary lines and relocated kendras into your daily life and external events.
                </p>
              </div>

              <div className="p-3 rounded-lg border border-cyan-500/30 bg-cyan-500/5">
                <div className="flex items-center justify-between font-bold text-cyan-600 dark:text-cyan-400 mb-0.5">
                  <span>Zone 2: Active Regional Zone</span>
                  <Badge tone="cyan">1.0° - 3.0° Orb (~110 - 330 km)</Badge>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-300">
                  Strong background resonance. Ideal for living in commuter suburbs, neighboring towns, or regional metros without feeling overwhelmed.
                </p>
              </div>

              <div className="p-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/40">
                <div className="flex items-center justify-between font-bold text-slate-700 dark:text-slate-300 mb-0.5">
                  <span>Zone 3: Outer Horizon</span>
                  <Badge tone="neutral">3.0° - 6.0° Orb (~330 - 650 km)</Badge>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  Subtle, secondary background theme. Beyond 6.0°, the direct angular impact of the line dissipates completely.
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-slate-200 dark:border-slate-800">
            <Button variant="secondary" onClick={() => setIsCoordsModalOpen(false)}>
              Close Guide
            </Button>
          </div>
        </div>
      </Modal>

      {/* Interactive Domain Detail Modal */}
      {result && selectedDomainForModal && (
        <Modal
          open={Boolean(selectedDomainForModal)}
          onClose={() => setSelectedDomainForModal(null)}
          title={
            selectedDomainForModal === "career"
              ? "💼 Career & Social Status — Deep Dive Guide"
              : selectedDomainForModal === "mental_peace"
              ? "🏡 Mental Peace & Home Comfort — Deep Dive Guide"
              : selectedDomainForModal === "wealth"
              ? "💰 Wealth & Financial Influx — Deep Dive Guide"
              : selectedDomainForModal === "marriage"
              ? "❤️ Marriage & Partnerships — Deep Dive Guide"
              : selectedDomainForModal === "health_risk"
              ? "🛡️ Health & Stability Risk Audit — Deep Dive Guide"
              : "🎯 Optimal Engagement Strategy — Deep Dive Guide"
          }
          width={640}
        >
          <div className="space-y-4 text-xs">
            {/* Header info badge */}
            <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
              <div>
                <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  {targetSearchText}
                </span>
                <span className="text-slate-500 dark:text-slate-400 font-mono ml-2">
                  ({targetLat.toFixed(2)}°, {targetLon.toFixed(2)}°)
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                {selectedMotive === selectedDomainForModal && (
                  <Badge tone="violet">🎯 Your Stated Primary Motive</Badge>
                )}
                <Badge tone="cyan">Radius: ≤ 1.0° (~110 km)</Badge>
              </div>
            </div>

            {/* Career details */}
            {selectedDomainForModal === "career" && (
              <>
                <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <h4 className="font-bold text-amber-600 dark:text-amber-400 text-sm mb-1">
                    Vedic &amp; Shastric Foundation: Karma Sthana (10th House / MC)
                  </h4>
                  <p className="leading-relaxed text-slate-700 dark:text-slate-300">
                    The 10th House (Dashama Bhava) and Midheaven (MC) rule worldly achievement, authority, leadership, and public reputation. In relocation astrology, shifting longitudes rotates the 10th cusp, placing different zodiac signs and natal planets at the zenith of the sky.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                    <span className="text-slate-500">Relocated Midheaven (MC):</span>
                    <span className="font-bold text-slate-900 dark:text-slate-100">
                      {result.angles.midheaven.sign} {result.angles.midheaven.degree.toFixed(2)}°
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                    <span className="text-slate-500">Harmonic Frequency:</span>
                    <span className="text-slate-900 dark:text-slate-200">
                      {HARMONIC_LABELS[result.angles.midheaven.harmonic_family] ?? result.angles.midheaven.harmonic_family}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Sun Angularity (Ravi):</span>
                    <span className={result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched) ? "text-emerald-500 font-bold" : "text-slate-400"}>
                      {result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched)
                        ? "Active on Kendra (Leadership & Recognition Amplified)"
                        : "Neutral Baseline"}
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-bold text-slate-900 dark:text-slate-100">Actionable Relocation Advice:</h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 leading-relaxed">
                    <li><strong>Best For:</strong> Seeking senior managerial promotions, enterprise founding, public consulting, and building institutional authority.</li>
                    <li><strong>Moving Decision:</strong> If career acceleration is your #1 goal, this longitude provides significant astrological tailwinds. If you are seeking quiet rest, the constant drive for recognition here can cause burnout.</li>
                  </ul>
                </div>
              </>
            )}

            {/* Mental Peace details */}
            {selectedDomainForModal === "mental_peace" && (
              <>
                <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                  <h4 className="font-bold text-cyan-600 dark:text-cyan-400 text-sm mb-1">
                    Vedic &amp; Shastric Foundation: Sukh Sthana (4th House / IC)
                  </h4>
                  <p className="leading-relaxed text-slate-700 dark:text-slate-300">
                    The 4th House (Chaturtha Bhava) and Nadir (IC) govern domestic tranquility, motherly warmth, emotional security, and mental tranquility. When an individual relocates, harmonious angles here create a deep feeling of 'home' and belonging.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                    <span className="text-slate-500">Harmonic Comfort Zone:</span>
                    <span className={result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched) ? "text-cyan-500 font-bold" : "text-slate-400"}>
                      {result.techniques.some((t) => t.technique_id === "comfort_zones" && t.is_matched)
                        ? "9th-Harmonic Resonant (High Emotional Ease)"
                        : "Standard Domestic Rhythm"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Ascendant Vibration:</span>
                    <span className="font-bold text-slate-900 dark:text-slate-100">
                      {result.angles.ascendant.sign} ({result.angles.ascendant.harmonic_family})
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-bold text-slate-900 dark:text-slate-100">Actionable Relocation Advice:</h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 leading-relaxed">
                    <li><strong>Best For:</strong> Family relocation, raising children, long-term property acquisition, and restoring mental wellness.</li>
                    <li><strong>Moving Decision:</strong> You will adapt rapidly to this environment without severe culture shock or chronic homesickness.</li>
                  </ul>
                </div>
              </>
            )}

            {/* Wealth details */}
            {selectedDomainForModal === "wealth" && (
              <>
                <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                  <h4 className="font-bold text-emerald-600 dark:text-emerald-400 text-sm mb-1">
                    Vedic &amp; Shastric Foundation: Dhana &amp; Labha Sthanas (2nd &amp; 11th)
                  </h4>
                  <p className="leading-relaxed text-slate-700 dark:text-slate-300">
                    Material wealth in relocation is driven by planetary crossing lines (Parans) and midpoint connections to the relocated kendras. Strong financial confluences stimulate commerce, deal-making, and asset liquidity.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                    <span className="text-slate-500">Active Latitude Parans:</span>
                    <span className="font-bold text-slate-900 dark:text-slate-100">
                      {String(result.facts["relocation.paran.count"] ?? 0)} Active Crossing Lines
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Midpoints to Career Zenith (MC):</span>
                    <span className="font-bold text-slate-900 dark:text-slate-100">
                      {String(result.facts["relocation.midpoints.mc.count"] ?? 0)} Triggers
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-bold text-slate-900 dark:text-slate-100">Actionable Relocation Advice:</h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 leading-relaxed">
                    <li><strong>Best For:</strong> High-income contracts, expanding customer pipelines, raising venture capital, and commercial investments.</li>
                    <li><strong>Moving Decision:</strong> High revenue generation is strongly activated. Keep living expenses prudent to maximize savings.</li>
                  </ul>
                </div>
              </>
            )}

            {/* Marriage details */}
            {selectedDomainForModal === "marriage" && (
              <>
                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20">
                  <h4 className="font-bold text-rose-600 dark:text-rose-400 text-sm mb-1">
                    Vedic &amp; Shastric Foundation: Kalatra Sthana (7th House / Descendant)
                  </h4>
                  <p className="leading-relaxed text-slate-700 dark:text-slate-300">
                    The 7th House (Saptama Bhava) and Descendant axis govern intimate partnerships, marriage, and long-term contracts. Moving places your 7th axis in direct relationship with the local community.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                    <span className="text-slate-500">Relocated 7th Axis:</span>
                    <span className="font-bold text-slate-900 dark:text-slate-100">
                      Opposite {result.angles.ascendant.sign}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Relational Harmony:</span>
                    <span className="text-slate-900 dark:text-slate-200">
                      Active Interpersonal Axis
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-bold text-slate-900 dark:text-slate-100">Actionable Relocation Advice:</h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 leading-relaxed">
                    <li><strong>Best For:</strong> Relocating with a spouse, finding a life partner, or establishing trust-based joint ventures.</li>
                    <li><strong>Moving Decision:</strong> Fosters diplomacy and mutual understanding. If moving for marriage, this location provides solid interpersonal support.</li>
                  </ul>
                </div>
              </>
            )}

            {/* Health & Risk details */}
            {selectedDomainForModal === "health_risk" && (
              <>
                <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20">
                  <h4 className="font-bold text-red-600 dark:text-red-400 text-sm mb-1">
                    Vedic &amp; Shastric Foundation: Trik Bhavas (6th/8th/12th) &amp; Volatility Lines
                  </h4>
                  <p className="leading-relaxed text-slate-700 dark:text-slate-300">
                    Before committing to a relocation, auditing sudden disruptive lines (Uranus / Mars / Saturn parans) is essential. High volatility can trigger unexpected abrupt disruptions, litigation, or health vulnerability.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                    <span className="text-slate-500">Volatility &amp; Disruption:</span>
                    <span className={result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched) ? "text-rose-500 font-bold" : "text-emerald-500 font-bold"}>
                      {result.techniques.some((t) => t.technique_id === "uranus_instability" && t.is_matched)
                        ? "⚠️ Volatile Disruption Alert"
                        : "✅ Stable / Low Disruption"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Physical Routine Risk:</span>
                    <span className="text-slate-900 dark:text-slate-200">
                      Normal Predictable Range
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-bold text-slate-900 dark:text-slate-100">Actionable Relocation Advice:</h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 leading-relaxed">
                    <li><strong>If Low Risk:</strong> Excellent location for steady, predictable long-term routine and physical well-being.</li>
                    <li><strong>If Volatile:</strong> Avoid entering binding, illiquid multi-year contracts immediately. Maintain active insurance and emergency cash reserves.</li>
                  </ul>
                </div>
              </>
            )}

            {/* Strategy details */}
            {selectedDomainForModal === "strategy" && (
              <>
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                  <h4 className="font-bold text-indigo-600 dark:text-indigo-400 text-sm mb-1">
                    Optimal Engagement Strategy (How to Tap This City's Energy)
                  </h4>
                  <p className="leading-relaxed text-slate-700 dark:text-slate-300">
                    Astrocartography allows you to extract the astrological blessings of a location without necessarily moving there permanently. You can engage via Permanent Relocation, Short Working Trips, or Remote Commercial Ventures.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 font-mono">
                  <div className="flex justify-between border-b border-slate-200 dark:border-slate-800 pb-1.5">
                    <span className="text-slate-500">Recommended Engagement Mode:</span>
                    <span className="text-indigo-500 dark:text-indigo-400 font-bold">
                      {result.techniques.some((t) => t.technique_id === "sun_angular" && t.is_matched)
                        ? "Permanent Relocation Recommended"
                        : "Travel / Remote / Project-Based"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Core Impact Radius:</span>
                    <span className="text-slate-900 dark:text-slate-100 font-bold">
                      ≤ 1.0° (~110 km from {targetSearchText})
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <h5 className="font-bold text-slate-900 dark:text-slate-100">Next Steps:</h5>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 leading-relaxed">
                    <li><strong>Timing the Move:</strong> Check your active Vimshottari Dasha period. Moving during supportive dasha lords amplifies favorable relocated kendras.</li>
                    <li><strong>Remote Work:</strong> Even from home, scheduling meetings or conducting business with clients based in {targetSearchText} taps into this angular power.</li>
                  </ul>
                </div>
              </>
            )}

            <div className="flex justify-end pt-3 border-t border-slate-200 dark:border-slate-800">
              <Button variant="secondary" onClick={() => setSelectedDomainForModal(null)}>
                Close Guide
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
