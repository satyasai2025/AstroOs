"use client";

import React, { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import { api } from "@/lib/api";
import { useActiveChart, chartKeys } from "@/lib/charts";
import { useQueryClient } from "@tanstack/react-query";
import { useAnalyzeWorkflow } from "@/lib/workflow";
import { Card, Button, Badge, Select, type SelectOption } from "@/components/ui";
import { CreateChartModal } from "@/components/dashboard/CreateChartModal";
import { RelocationStudio } from "@/components/research/RelocationStudio";
import type { WorkflowAnalysisRequest } from "@/lib/types";

interface CityKeyInfluence {
  planet_or_pair: string;
  orb_str: string;
  strength: string;
  theme: string;
}

interface CityDomainScores {
  career: number;
  finance: number;
  relationships: number;
  health: number;
  education: number;
  stability: number;
}

interface RecommendedCity {
  id: string;
  name: string;
  country: string;
  country_code: string;
  flag: string;
  image_url: string;
  latitude: number;
  longitude: number;
  overall_score: number;
  domain_scores: CityDomainScores;
  key_influences: CityKeyInfluence[];
  why_points: string[];
  astrological_themes: Record<string, string>;
  techniques_used: string[];
}

interface RelocationRecommendResponse {
  objective: string;
  region: string;
  cities: RecommendedCity[];
}

const OBJECTIVE_PILLS = [
  { id: "career", label: "Career Growth", icon: "💼" },
  { id: "business", label: "Business", icon: "📈" },
  { id: "wealth", label: "Wealth", icon: "💰" },
  { id: "marriage", label: "Marriage", icon: "❤️" },
  { id: "education", label: "Education", icon: "🎓" },
  { id: "peace", label: "Peace & Stability", icon: "🏡" },
  { id: "spiritual", label: "Spiritual Growth", icon: "🧘" },
  { id: "general", label: "General Relocation", icon: "🏠" },
];

const REGION_OPTIONS: SelectOption[] = [
  { value: "worldwide", label: "Worldwide" },
  { value: "asia", label: "Asia" },
  { value: "europe", label: "Europe" },
  { value: "north_america", label: "North America" },
  { value: "middle_east", label: "Middle East" },
  { value: "oceania", label: "Oceania / Australia" },
  { value: "india", label: "India Subcontinent" },
];

export function RelocationDiscoveryStudio() {
  const { activeSummary, myCharts, selectChart } = useActiveChart();
  const queryClient = useQueryClient();
  const analyzeWorkflow = useAnalyzeWorkflow();

  // Mode: "recommend" (Mockup Feed) vs "inspect" (Specific City / GPS Studio)
  const [viewMode, setViewMode] = useState<"recommend" | "inspect">("recommend");

  // Selection state
  const [selectedChartId, setSelectedChartId] = useState<string>("");
  const [objective, setObjective] = useState<string>("career");
  const [region, setRegion] = useState<string>("worldwide");

  // Recommendation query results
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [cities, setCities] = useState<RecommendedCity[]>([]);
  const [selectedCityId, setSelectedCityId] = useState<string | null>(null);
  const [dossierTab, setDossierTab] = useState<"overview" | "astro" | "techniques" | "map">("overview");

  // Modal state
  const [isCreateChartModalOpen, setIsCreateChartModalOpen] = useState<boolean>(false);

  // Hydration safety
  const [mounted, setMounted] = useState<boolean>(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  // Sync active chart
  useEffect(() => {
    if (activeSummary) {
      setSelectedChartId(activeSummary.id);
    }
  }, [activeSummary]);

  // Chart options
  const chartOptions: SelectOption[] = useMemo(() => {
    return myCharts.map((c) => ({
      value: c.id,
      label: `${c.subject_name} (${c.place_name || "Unknown"})${c.is_default ? " ★ Default" : ""}`,
    }));
  }, [myCharts]);

  const handleChartChange = (chartId: string) => {
    setSelectedChartId(chartId);
    const found = myCharts.find((c) => c.id === chartId);
    if (found) {
      selectChart(found);
    }
  };

  // Fetch recommendations
  const fetchRecommendations = async (overrideObjective?: string, overrideRegion?: string) => {
    if (!activeSummary) return;
    setLoading(true);
    setError(null);
    try {
      const obj = overrideObjective ?? objective;
      const reg = overrideRegion ?? region;
      const data = await api.post<RelocationRecommendResponse>("/api/v1/relocation/recommend", {
        birth_utc: activeSummary.birth_datetime_utc,
        birth_lat: activeSummary.birth_latitude,
        birth_lon: activeSummary.birth_longitude,
        ayanamsa: activeSummary.ayanamsa?.toLowerCase() || "lahiri",
        house_system: "P",
        objective: obj,
        region: reg,
      });
      setCities(data.cities);
      if (data.cities.length > 0) {
        setSelectedCityId(data.cities[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  };

  // Trigger initial fetch when activeSummary changes
  useEffect(() => {
    if (activeSummary && viewMode === "recommend") {
      fetchRecommendations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSummary?.id]);

  const activeCity = useMemo(() => {
    if (!cities.length) return null;
    return cities.find((c) => c.id === selectedCityId) || cities[0];
  }, [cities, selectedCityId]);

  const activeObjectiveLabel = useMemo(() => {
    return OBJECTIVE_PILLS.find((p) => p.id === objective)?.label || "Career Growth";
  }, [objective]);

  const handleCreateChartSubmit = async (req: WorkflowAnalysisRequest) => {
    try {
      const res = await analyzeWorkflow.mutateAsync(req);
      await queryClient.invalidateQueries({ queryKey: chartKeys.mine });
      setIsCreateChartModalOpen(false);
      if (res.chart_id) {
        setSelectedChartId(res.chart_id);
      }
      fetchRecommendations();
    } catch (err) {
      console.error("Failed to create new birth chart:", err);
    }
  };

  if (!mounted) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
              <span>🧭</span> Relocation &amp; Astro-Cartography Studio
            </h1>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed max-w-4xl">
              Find the best places in the world aligned with your chart, using Astro-Cartography, Paran Crossings, Sun Angularity, Midpoint-to-Angle and Harmonic techniques.
            </p>
          </div>
        </div>
        <div className="p-12 text-center text-slate-400 text-xs font-mono space-y-2">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
          <p>Loading Relocation Studio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <span>🧭</span> Relocation &amp; Astro-Cartography Studio
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed max-w-4xl">
            Find the best places in the world aligned with your chart, using Astro-Cartography, Paran Crossings, Sun Angularity, Midpoint-to-Angle and Harmonic techniques.
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="inline-flex rounded-xl border border-slate-200 dark:border-slate-800 p-1 bg-slate-100 dark:bg-slate-900/80 shrink-0">
          <button
            type="button"
            onClick={() => setViewMode("recommend")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer flex items-center gap-1.5 ${
              viewMode === "recommend"
                ? "bg-amber-500 text-slate-950 font-bold shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
            }`}
          >
            <span>🌟</span> Find Best Locations
          </button>
          <button
            type="button"
            onClick={() => setViewMode("inspect")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer flex items-center gap-1.5 ${
              viewMode === "inspect"
                ? "bg-cyan-500 text-slate-950 font-bold shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
            }`}
          >
            <span>📍</span> Inspect City / GPS
          </button>
        </div>
      </div>

      {viewMode === "inspect" ? (
        /* If user switches to Inspect mode, show our dedicated Custom/GPS Inspector */
        <RelocationStudio />
      ) : (
        /* Full Discovery & Recommendation Experience (Matching Mockup) */
        <div className="space-y-6">
          {/* Top Filter Bar Card */}
          <Card className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
              {/* Person Selector */}
              <div className="md:col-span-4">
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[11px] font-medium text-slate-700 dark:text-slate-300">
                    Person (Natal Chart)
                  </label>
                  <button
                    type="button"
                    onClick={() => setIsCreateChartModalOpen(true)}
                    className="text-[11px] text-amber-600 dark:text-amber-400 hover:underline font-mono cursor-pointer"
                  >
                    + New Chart
                  </button>
                </div>
                {chartOptions.length > 0 ? (
                  <Select
                    options={chartOptions}
                    value={selectedChartId}
                    onChange={handleChartChange}
                    placeholder="Select chart..."
                  />
                ) : (
                  <div className="text-xs text-amber-600 dark:text-amber-400 py-1.5">No saved charts found.</div>
                )}
              </div>

              {/* Primary Objective */}
              <div className="md:col-span-3">
                <label className="text-[11px] font-medium text-slate-700 dark:text-slate-300 block mb-1.5">
                  Primary Objective
                </label>
                <Select
                  options={OBJECTIVE_PILLS.map((p) => ({ value: p.id, label: `${p.icon} ${p.label}` }))}
                  value={objective}
                  onChange={(val) => {
                    setObjective(val);
                    fetchRecommendations(val, region);
                  }}
                />
              </div>

              {/* Region */}
              <div className="md:col-span-3">
                <label className="text-[11px] font-medium text-slate-700 dark:text-slate-300 block mb-1.5">
                  Region
                </label>
                <Select
                  options={REGION_OPTIONS}
                  value={region}
                  onChange={(val) => {
                    setRegion(val);
                    fetchRecommendations(objective, val);
                  }}
                />
              </div>

              {/* Find Best Locations Button */}
              <div className="md:col-span-2">
                <button
                  type="button"
                  onClick={() => fetchRecommendations()}
                  disabled={loading}
                  className="w-full h-10 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 cursor-pointer transition shadow-md disabled:opacity-50"
                >
                  {loading ? (
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
                  ) : (
                    <span>🔍</span>
                  )}
                  Find Best Locations
                </button>
              </div>
            </div>
          </Card>

          {/* Objective Category Horizontal Pills Bar */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            {OBJECTIVE_PILLS.map((pill) => {
              const isActive = objective === pill.id;
              return (
                <button
                  key={pill.id}
                  type="button"
                  onClick={() => {
                    setObjective(pill.id);
                    fetchRecommendations(pill.id, region);
                  }}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold shrink-0 transition flex items-center gap-2 cursor-pointer border ${
                    isActive
                      ? "bg-amber-500/15 border-amber-500 text-amber-600 dark:text-amber-400 shadow-xs"
                      : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 hover:border-slate-300 dark:hover:border-slate-700 shadow-2xs"
                  }`}
                >
                  <span>{pill.icon}</span>
                  <span>{pill.label}</span>
                </button>
              );
            })}
          </div>

          {error && (
            <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 text-xs text-rose-400">
              ⚠️ {error}
            </div>
          )}

          {/* Main Dual-Column Recommendation View */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Ranked Locations List (5 Cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
                <div>
                  <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                    Top Recommended Locations for {activeObjectiveLabel}
                  </h2>
                  <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                    Based on Astro-Cartography, Paran Crossings, Sun Angularity, and Midpoints
                  </p>
                </div>
                <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-800 p-0.5 bg-slate-100 dark:bg-slate-900 text-[11px] font-mono">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-white font-bold">List</span>
                  <span className="px-2 py-0.5 text-slate-500 cursor-not-allowed">Map</span>
                </div>
              </div>

              {loading ? (
                <div className="p-12 text-center text-slate-400 text-xs font-mono space-y-2">
                  <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-amber-400 border-t-transparent" />
                  <p>Scanning global horizons and paran crossings…</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cities.map((city, idx) => {
                    const isSelected = selectedCityId === city.id;
                    const rankNum = idx + 1;
                    return (
                      <div
                        key={city.id}
                        onClick={() => setSelectedCityId(city.id)}
                        className={`rounded-2xl border transition p-3.5 flex flex-col justify-between gap-3 cursor-pointer ${
                          isSelected
                            ? "bg-amber-500/5 dark:bg-slate-900 border-amber-500 ring-2 ring-amber-500/20 shadow-md"
                            : "bg-white dark:bg-slate-900/70 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900/90 shadow-2xs"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          {/* Rank Badge */}
                          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-amber-500/15 dark:bg-amber-500/20 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-black">
                            {rankNum}
                          </div>

                          {/* City Thumbnail */}
                          <div className="relative h-14 w-20 shrink-0 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
                            <Image
                              src={city.image_url}
                              alt={city.name}
                              fill
                              unoptimized
                              className="object-cover"
                            />
                          </div>

                          {/* City Name & Country */}
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between">
                              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 truncate">
                                {city.name}
                              </h3>
                              <div className="text-right">
                                <span className="text-base font-black text-slate-900 dark:text-slate-100 font-mono">
                                  {city.overall_score}
                                </span>
                                <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">/100</span>
                              </div>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
                              <span>{city.flag}</span>
                              <span className="truncate">{city.country}</span>
                            </p>
                            {/* Score Bar */}
                            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                              <div
                                className="bg-emerald-500 h-full rounded-full"
                                style={{ width: `${city.overall_score}%` }}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Domain Mini Scores & Key Influences */}
                        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2 text-[10px] font-mono">
                          <div className="flex items-center gap-2.5 text-slate-500 dark:text-slate-400">
                            <span>Career <strong className="text-slate-800 dark:text-slate-200">{city.domain_scores.career}</strong></span>
                            <span>Finance <strong className="text-slate-800 dark:text-slate-200">{city.domain_scores.finance}</strong></span>
                            <span>Stability <strong className="text-slate-800 dark:text-slate-200">{city.domain_scores.stability}</strong></span>
                          </div>

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedCityId(city.id);
                            }}
                            className="px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-300 font-bold text-[11px] cursor-pointer flex items-center gap-1 transition"
                          >
                            View Details →
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right Column: Selected City Detailed Dossier (7 Cols) */}
            {activeCity ? (
              <div className="lg:col-span-7 space-y-4">
                {/* Hero Header Card */}
                <Card className="overflow-hidden p-0">
                  <div className="relative h-44 w-full">
                    <Image
                      src={activeCity.image_url}
                      alt={activeCity.name}
                      fill
                      unoptimized
                      className="object-cover brightness-75"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />
                    <div className="absolute bottom-4 left-6 right-6 flex items-end justify-between">
                      <div>
                        <h2 className="text-2xl font-black text-white flex items-center gap-2">
                          {activeCity.name}
                        </h2>
                        <p className="text-xs text-slate-200 flex items-center gap-1.5 mt-0.5 font-medium">
                          <span>{activeCity.flag}</span>
                          <span>{activeCity.country}</span>
                        </p>
                      </div>

                      <div className="text-right">
                        <span className="text-xs text-slate-300 uppercase tracking-wider font-mono block">Overall Score</span>
                        <div className="flex items-baseline gap-1 justify-end">
                          <span className="text-3xl font-black text-emerald-400 font-mono">
                            {activeCity.overall_score}
                          </span>
                          <span className="text-xs text-slate-300 font-mono">/100</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Sub-Tabs */}
                  <div className="px-6 py-2.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950/50">
                    <div className="flex items-center gap-4 text-xs font-mono">
                      <button
                        type="button"
                        onClick={() => setDossierTab("overview")}
                        className={`pb-1 border-b-2 transition cursor-pointer ${
                          dossierTab === "overview"
                            ? "border-amber-500 text-amber-600 dark:text-amber-400 font-bold"
                            : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                        }`}
                      >
                        Overview
                      </button>
                      <button
                        type="button"
                        onClick={() => setDossierTab("astro")}
                        className={`pb-1 border-b-2 transition cursor-pointer ${
                          dossierTab === "astro"
                            ? "border-amber-500 text-amber-600 dark:text-amber-400 font-bold"
                            : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                        }`}
                      >
                        Astrological Analysis
                      </button>
                      <button
                        type="button"
                        onClick={() => setDossierTab("techniques")}
                        className={`pb-1 border-b-2 transition cursor-pointer ${
                          dossierTab === "techniques"
                            ? "border-amber-500 text-amber-600 dark:text-amber-400 font-bold"
                            : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                        }`}
                      >
                        Techniques &amp; Evidence
                      </button>
                    </div>

                    <button
                      type="button"
                      className="px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-[11px] text-slate-700 dark:text-slate-300 hover:text-slate-950 dark:hover:text-white font-mono cursor-pointer"
                    >
                      🔖 Add to Compare
                    </button>
                  </div>

                  {/* Tab Body */}
                  <div className="p-6 space-y-6">
                    {/* Relocation Profile Progress Bars */}
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-mono">
                          Relocation Profile
                        </span>
                        <span className="text-[11px] text-slate-400 dark:text-slate-500 font-mono">Score out of 100</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 font-mono text-xs">
                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-600 dark:text-slate-400">Career</span>
                            <span className="text-cyan-600 dark:text-cyan-400 font-bold">{activeCity.domain_scores.career}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${activeCity.domain_scores.career}%` }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-600 dark:text-slate-400">Finance</span>
                            <span className="text-amber-600 dark:text-amber-400 font-bold">{activeCity.domain_scores.finance}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div className="bg-amber-500 h-full rounded-full" style={{ width: `${activeCity.domain_scores.finance}%` }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-600 dark:text-slate-400">Relationships</span>
                            <span className="text-rose-600 dark:text-rose-400 font-bold">{activeCity.domain_scores.relationships}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div className="bg-rose-500 h-full rounded-full" style={{ width: `${activeCity.domain_scores.relationships}%` }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-600 dark:text-slate-400">Health</span>
                            <span className="text-emerald-600 dark:text-emerald-400 font-bold">{activeCity.domain_scores.health}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${activeCity.domain_scores.health}%` }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-600 dark:text-slate-400">Education</span>
                            <span className="text-purple-600 dark:text-purple-400 font-bold">{activeCity.domain_scores.education}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div className="bg-purple-500 h-full rounded-full" style={{ width: `${activeCity.domain_scores.education}%` }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-slate-600 dark:text-slate-400">Stability</span>
                            <span className="text-indigo-600 dark:text-indigo-400 font-bold">{activeCity.domain_scores.stability}</span>
                          </div>
                          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${activeCity.domain_scores.stability}%` }} />
                          </div>
                        </div>
                      </div>

                      {/* Callout Card */}
                      <div className="mt-4 p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs text-purple-900 dark:text-purple-300 flex items-center gap-2">
                        <span className="text-amber-500 text-sm">⭐</span>
                        <span>
                          Excellent for <strong>{activeObjectiveLabel.toLowerCase()}</strong>, professional visibility, and long-term expansion.
                        </span>
                      </div>
                    </div>

                    {/* Key Astrological Influences */}
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-mono mb-3">
                        Key Astrological Influences
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {activeCity.key_influences.map((inf, i) => (
                          <div
                            key={i}
                            className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 flex items-center justify-between"
                          >
                            <div className="space-y-0.5">
                              <span className="text-xs font-bold text-slate-900 dark:text-slate-100 block">
                                {inf.planet_or_pair}
                              </span>
                              <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono block">
                                {inf.orb_str} · {inf.strength}
                              </span>
                            </div>
                            <Badge tone="gold">{inf.theme}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Why this city? */}
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-mono mb-3">
                        Why {activeCity.name}?
                      </h3>
                      <div className="space-y-2.5">
                        {activeCity.why_points.map((point, i) => (
                          <div key={i} className="flex items-start gap-3 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
                            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-amber-600 dark:text-amber-400 font-mono text-[10px] font-bold">
                              {i + 1}
                            </span>
                            <span>{point}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Astrological Themes & Techniques */}
                    <div className="pt-4 border-t border-slate-200 dark:border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 font-mono mb-2">Astrological Themes</h4>
                        <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                          <li>💼 <strong>Career:</strong> {activeCity.astrological_themes.Career}</li>
                          <li>💰 <strong>Finance:</strong> {activeCity.astrological_themes.Finance}</li>
                          <li>❤️ <strong>Relationships:</strong> {activeCity.astrological_themes.Relationships}</li>
                          <li>🌐 <strong>Lifestyle:</strong> {activeCity.astrological_themes.Lifestyle}</li>
                        </ul>
                      </div>

                      <div>
                        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 font-mono mb-2">Techniques Used</h4>
                        <div className="space-y-1.5 text-xs font-mono text-emerald-600 dark:text-emerald-400">
                          {activeCity.techniques_used.map((t, i) => (
                            <div key={i} className="flex items-center gap-1.5">
                              <span>☑</span>
                              <span>{t}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Official Create New Natal Chart Modal */}
      <CreateChartModal
        open={isCreateChartModalOpen}
        onClose={() => setIsCreateChartModalOpen(false)}
        onSubmit={handleCreateChartSubmit}
        isPending={analyzeWorkflow.isPending}
        errorMessage={analyzeWorkflow.error?.message ?? null}
        initialChartType="birth_chart"
      />
    </div>
  );
}
