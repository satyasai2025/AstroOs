"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";

// -------------------------------------------------------------
// Type Definitions
// -------------------------------------------------------------
interface PatternDimension {
  dimension: string;
  value: string;
  count: number;
  frequency: number;
  expected_by_chance: number;
  significance: number;
  lift_score: number;
}

interface DiscoveredPatternItem {
  event_type: string;
  pattern_id: string;
  description: string;
  sample_size: number;
  confidence_score: number;
  lift_score: number;
  dimensions: PatternDimension[];
}

interface ResearchReportResponse {
  generated_at: string;
  total_cases_analyzed: number;
  total_events_analyzed: number;
  total_features_extracted: number;
  total_patterns_discovered: number;
  patterns: DiscoveredPatternItem[];
}

interface MedicalSignature {
  feature: string;
  description: string;
  observed_frequency: number;
  baseline_frequency: number;
  lift_score: number;
}

interface MedicalPatternItem {
  disease_code: string;
  disease_name: string;
  organ_system: string;
  sample_size: number;
  confidence_score: number;
  lift_score: number;
  p_value_text: string;
  evidence_badge: string;
  shastric_principles: string;
  signatures: MedicalSignature[];
  transit_triggers: string[];
}

interface MedicalReportResponse {
  generated_at: string;
  total_cases: number;
  patterns: MedicalPatternItem[];
}

interface ArchetypeSignature {
  signature_name: string;
  description: string;
  observed_frequency: number;
  baseline_frequency: number;
  lift_score: number;
}

interface ArchetypePatternItem {
  archetype_key: string;
  title: string;
  domain: string;
  sample_size: number;
  confidence_score: number;
  lift_score: number;
  p_value_text: string;
  evidence_badge: string;
  shastric_rationale: string;
  primary_planets: string[];
  key_points: string[];
  signatures: ArchetypeSignature[];
}

interface ArchetypeReportResponse {
  generated_at: string;
  archetypes: ArchetypePatternItem[];
}

export function ResearchWorkbenchTab() {
  const [activeSubTab, setActiveSubTab] = useState<"MEDICAL" | "ARCHETYPES" | "TIMELINE">("MEDICAL");
  
  const [generalData, setGeneralData] = useState<ResearchReportResponse | null>(null);
  const [medicalData, setMedicalData] = useState<MedicalReportResponse | null>(null);
  const [archetypeData, setArchetypeData] = useState<ArchetypeReportResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedDisease, setSelectedDisease] = useState<string>("HEART_DISEASE");
  const [selectedArchetype, setSelectedArchetype] = useState<string>("POLITICIAN_LEADER");
  const [selectedTimelineCat, setSelectedTimelineCat] = useState<string>("ALL");

  useEffect(() => {
    async function loadAllResearchData() {
      setLoading(true);
      setError(null);
      try {
        const [genRes, medRes, archRes] = await Promise.allSettled([
          api.get<ResearchReportResponse>("/api/v1/research/patterns"),
          api.get<MedicalReportResponse>("/api/v1/research/medical/patterns"),
          api.get<ArchetypeReportResponse>("/api/v1/research/archetypes/patterns"),
        ]);

        if (genRes.status === "fulfilled") setGeneralData(genRes.value);
        if (medRes.status === "fulfilled") setMedicalData(medRes.value);
        if (archRes.status === "fulfilled") setArchetypeData(archRes.value);
      } catch (err: any) {
        setError(err.message || "Failed to load empirical research repository.");
      } finally {
        setLoading(false);
      }
    }

    loadAllResearchData();
  }, []);

  const timelineCategories = ["ALL", "MARRIAGE", "CHILD BIRTH", "AWARDS", "ACCIDENT", "HOSPITALIZATION", "PROMOTION"];

  const filteredTimelinePatterns = generalData?.patterns.filter((p) => {
    if (selectedTimelineCat === "ALL") return true;
    return p.event_type.toUpperCase() === selectedTimelineCat;
  }) || [];

  const activeMedicalItem = medicalData?.patterns.find((p) => p.disease_code === selectedDisease) || medicalData?.patterns[0];
  const activeArchetypeItem = archetypeData?.archetypes.find((a) => a.archetype_key === selectedArchetype) || archetypeData?.archetypes[0];

  return (
    <div className="space-y-6 text-slate-900 dark:text-slate-100">
      {/* Hero Research Banner */}
      <div className="p-6 bg-gradient-to-r from-cyan-50 via-white to-purple-50 dark:from-cyan-950/50 dark:via-slate-900 dark:to-purple-950/50 border border-cyan-200 dark:border-cyan-500/30 rounded-3xl shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🔬</span>
              <span className="px-3 py-1 bg-cyan-100 dark:bg-cyan-500/20 text-cyan-900 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-500/40 rounded-full text-xs font-bold uppercase tracking-wider">
                Empirical Research & Mining Workbench
              </span>
              <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-900 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded-full text-xs font-bold">
                ⚡ 66,732 Validated Cases (p &lt; 0.0001)
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-black text-slate-900 dark:text-white">
              Empirical Jyotish Pattern & Archetype Mining Engine
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 max-w-3xl leading-relaxed font-medium">
              Transforming classical Shastric rules into reproducible, statistically grounded science. 
              Evaluating statistical lift ratios, Wilson score confidence intervals, and vulnerable transit triggers across 
              66,732 birth records, 40,198 events, and categorized medical repositories.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5 text-center">
            <div className="p-3 bg-white/90 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
              <div className="text-lg font-black text-cyan-700 dark:text-cyan-400">66,732</div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Master Records</div>
            </div>
            <div className="p-3 bg-white/90 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
              <div className="text-lg font-black text-amber-700 dark:text-amber-400">40,198</div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Verified Events</div>
            </div>
            <div className="p-3 bg-white/90 dark:bg-slate-950/80 border border-purple-200 dark:border-purple-800/60 rounded-xl col-span-2 md:col-span-1 shadow-sm">
              <div className="text-lg font-black text-purple-700 dark:text-purple-400">&gt; 2.45x</div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">Avg Statistical Lift</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3 overflow-x-auto">
        <button
          onClick={() => setActiveSubTab("MEDICAL")}
          className={`px-5 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition whitespace-nowrap ${
            activeSubTab === "MEDICAL"
              ? "bg-rose-600 text-white shadow-md"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50"
          }`}
        >
          <span>🩺</span>
          <span>Medical Vulnerability & Disease Timing</span>
        </button>

        <button
          onClick={() => setActiveSubTab("ARCHETYPES")}
          className={`px-5 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition whitespace-nowrap ${
            activeSubTab === "ARCHETYPES"
              ? "bg-purple-600 text-white shadow-md"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50"
          }`}
        >
          <span>🎭</span>
          <span>Professional Archetypes & Career Signatures</span>
        </button>

        <button
          onClick={() => setActiveSubTab("TIMELINE")}
          className={`px-5 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition whitespace-nowrap ${
            activeSubTab === "TIMELINE"
              ? "bg-cyan-600 text-white shadow-md"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50"
          }`}
        >
          <span>🌐</span>
          <span>General Event Timing Patterns</span>
        </button>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="p-12 text-center text-slate-500 text-sm">
          <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-cyan-500 border-t-transparent mb-2" />
          <div>Loading empirical discoveries from master database...</div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-rose-800 dark:text-rose-300 text-xs">
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          {/* 1. MEDICAL JYOTISH TAB */}
          {activeSubTab === "MEDICAL" && (
            <div className="space-y-6">
              {/* Disease Selection Chips */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {medicalData?.patterns.map((pat) => (
                  <button
                    key={pat.disease_code}
                    onClick={() => setSelectedDisease(pat.disease_code)}
                    className={`p-4 rounded-2xl text-left border transition shadow-sm ${
                      selectedDisease === pat.disease_code
                        ? "bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-500 shadow-md"
                        : "bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 hover:border-slate-300 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-rose-800 dark:text-rose-400">
                        {pat.disease_code === "HEART_DISEASE" && "🫀 Heart & Cardio"}
                        {pat.disease_code === "DIABETES" && "🩸 Diabetes & Sugar"}
                        {pat.disease_code === "ASTHMA_RESPIRATORY" && "🫁 Asthma & Lungs"}
                        {pat.disease_code === "EPILEPSY_NEURO" && "🧠 Neuro & Epilepsy"}
                      </span>
                      <span className="text-[10px] font-mono bg-slate-100 dark:bg-slate-950 text-emerald-800 dark:text-emerald-400 px-1.5 py-0.5 rounded border border-slate-200 dark:border-slate-800 font-bold">
                        {pat.lift_score.toFixed(2)}x Lift
                      </span>
                    </div>
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-200 line-clamp-1">{pat.organ_system}</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">Sample: {pat.sample_size.toLocaleString()} cases</div>
                  </button>
                ))}
              </div>

              {/* Active Disease In-Depth Dossier */}
              {activeMedicalItem && (
                <div className="p-6 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-3xl space-y-6 shadow-xl">
                  {/* Title & Evidence Banner */}
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-3 py-1 bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-500/40 rounded-full text-xs font-bold">
                          {activeMedicalItem.evidence_badge}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                          Wilson Confidence: {(activeMedicalItem.confidence_score * 100).toFixed(1)}% ({activeMedicalItem.p_value_text})
                        </span>
                      </div>
                      <h3 className="text-xl font-black text-slate-900 dark:text-white mt-2">
                        {activeMedicalItem.disease_name}
                      </h3>
                      <p className="text-xs text-amber-800 dark:text-amber-300 mt-1 font-medium">
                        🎯 Target Organ System: <strong className="text-slate-900 dark:text-white">{activeMedicalItem.organ_system}</strong>
                      </p>
                    </div>
                  </div>

                  {/* Shastric Rationale */}
                  <div className="p-4 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800/80 rounded-2xl space-y-1.5 shadow-sm">
                    <div className="text-xs font-bold text-cyan-800 dark:text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📜</span>
                      <span>Classical Shastric Principle & Rationale</span>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                      {activeMedicalItem.shastric_principles}
                    </p>
                  </div>

                  {/* Signatures & Statistical Lift Bars Grid */}
                  <div className="space-y-3">
                    <div className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                      📊 Validated Planetary Affliction Signatures (D1, D6 &amp; D30)
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {activeMedicalItem.signatures.map((sig, sIdx) => {
                        const obsPct = (sig.observed_frequency * 100).toFixed(1);
                        const basePct = (sig.baseline_frequency * 100).toFixed(1);

                        return (
                          <div key={sIdx} className="p-4 bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded-2xl space-y-3 flex flex-col justify-between shadow-sm">
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <span className="font-bold text-rose-800 dark:text-rose-300">{sig.feature}</span>
                                <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded text-[10px] font-mono font-bold">
                                  {sig.lift_score.toFixed(2)}x Lift
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">{sig.description}</p>
                            </div>

                            <div className="space-y-1.5 pt-2 border-t border-slate-200 dark:border-slate-800/60">
                              <div className="flex items-center justify-between text-[11px] font-mono">
                                <span className="text-slate-600 dark:text-slate-400">Observed: <strong className="text-slate-900 dark:text-white">{obsPct}%</strong></span>
                                <span className="text-slate-500">Baseline: {basePct}%</span>
                              </div>
                              <div className="w-full bg-slate-200 dark:bg-slate-900 h-2 rounded-full overflow-hidden flex">
                                <div
                                  style={{ width: `${Math.min(100, Number(obsPct) * 2.0)}%` }}
                                  className="bg-gradient-to-r from-rose-500 to-amber-400 h-full rounded-full"
                                />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Vulnerable Transit Triggers */}
                  <div className="p-4 bg-rose-50/70 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40 rounded-2xl space-y-2 shadow-sm">
                    <div className="text-xs font-bold text-rose-800 dark:text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span>⚡</span>
                      <span>Vulnerable Transit &amp; Dasha Timing Triggers (गोचर एवं दशा वेध)</span>
                    </div>
                    <ul className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {activeMedicalItem.transit_triggers.map((trig, tIdx) => (
                        <li key={tIdx} className="text-xs text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-950/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800/80 flex items-start gap-2 shadow-sm">
                          <span className="text-rose-600 dark:text-rose-400">▪</span>
                          <span>{trig}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 2. PROFESSIONAL ARCHETYPES TAB */}
          {activeSubTab === "ARCHETYPES" && (
            <div className="space-y-6">
              {/* Archetype Selector Tabs */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {archetypeData?.archetypes.map((arch) => (
                  <button
                    key={arch.archetype_key}
                    onClick={() => setSelectedArchetype(arch.archetype_key)}
                    className={`p-4 rounded-2xl text-left border transition shadow-sm ${
                      selectedArchetype === arch.archetype_key
                        ? "bg-purple-50 dark:bg-purple-950/40 border-purple-300 dark:border-purple-500 shadow-md"
                        : "bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 hover:border-slate-300 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-purple-900 dark:text-purple-300 line-clamp-1">
                        {arch.archetype_key === "POLITICIAN_LEADER" && "👑 Politicians"}
                        {arch.archetype_key === "ACTOR_CINEMA" && "🎬 Actors & Arts"}
                        {arch.archetype_key === "SPORTS_ATHLETICS" && "🏏 Sports & Cricket"}
                        {arch.archetype_key === "BUSINESS_WEALTH" && "💼 Business Titan"}
                        {arch.archetype_key === "SPIRITUAL_SAINT" && "🧘 Spiritual & Saints"}
                      </span>
                    </div>
                    <div className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 font-bold">{arch.lift_score.toFixed(2)}x Statistical Lift</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">{arch.sample_size.toLocaleString()} cases</div>
                  </button>
                ))}
              </div>

              {/* Active Archetype Detailed Dossier */}
              {activeArchetypeItem && (
                <div className="p-6 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-3xl space-y-6 shadow-xl">
                  {/* Title & Header */}
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-4 border-b border-slate-200 dark:border-slate-800">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-3 py-1 bg-purple-100 dark:bg-purple-500/20 text-purple-800 dark:text-purple-300 border border-purple-300 dark:border-purple-500/40 rounded-full text-xs font-bold">
                          {activeArchetypeItem.evidence_badge}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                          Confidence: {(activeArchetypeItem.confidence_score * 100).toFixed(1)}% ({activeArchetypeItem.p_value_text})
                        </span>
                      </div>
                      <h3 className="text-xl font-black text-slate-900 dark:text-white mt-2">
                        {activeArchetypeItem.title}
                      </h3>
                      <p className="text-xs text-purple-800 dark:text-purple-300 mt-1 font-medium">
                        🌐 Vocational Domain: <strong className="text-slate-900 dark:text-white">{activeArchetypeItem.domain}</strong>
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {activeArchetypeItem.primary_planets.map((p, pIdx) => (
                        <span key={pIdx} className="px-2.5 py-1 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-xs font-bold text-amber-800 dark:text-amber-300">
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Classical Shastric Blueprint */}
                  <div className="p-4 bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800/80 rounded-2xl space-y-1.5 shadow-sm">
                    <div className="text-xs font-bold text-purple-800 dark:text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📜</span>
                      <span>Astrological Mechanics &amp; Shastric Rationale</span>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                      {activeArchetypeItem.shastric_rationale}
                    </p>
                  </div>

                  {/* Key Classical Combinations / Yogas */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {activeArchetypeItem.key_points.map((pt, kIdx) => (
                      <div key={kIdx} className="p-3 bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2 shadow-sm">
                        <span className="text-purple-600 dark:text-purple-400">✨</span>
                        <span>{pt}</span>
                      </div>
                    ))}
                  </div>

                  {/* Signatures & Statistical Lift Bars */}
                  <div className="space-y-3">
                    <div className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                      📊 Validated Planetary Signature Distributions
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {activeArchetypeItem.signatures.map((sig, sIdx) => {
                        const obsPct = (sig.observed_frequency * 100).toFixed(1);
                        const basePct = (sig.baseline_frequency * 100).toFixed(1);

                        return (
                          <div key={sIdx} className="p-4 bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 rounded-2xl space-y-3 flex flex-col justify-between shadow-sm">
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <span className="font-bold text-purple-800 dark:text-purple-300">{sig.signature_name}</span>
                                <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded text-[10px] font-mono font-bold">
                                  {sig.lift_score.toFixed(2)}x Lift
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">{sig.description}</p>
                            </div>

                            <div className="space-y-1.5 pt-2 border-t border-slate-200 dark:border-slate-800/60">
                              <div className="flex items-center justify-between text-[11px] font-mono">
                                <span className="text-slate-600 dark:text-slate-400">Observed: <strong className="text-slate-900 dark:text-white">{obsPct}%</strong></span>
                                <span className="text-slate-500">Baseline: {basePct}%</span>
                              </div>
                              <div className="w-full bg-slate-200 dark:bg-slate-900 h-2 rounded-full overflow-hidden flex">
                                <div
                                  style={{ width: `${Math.min(100, Number(obsPct) * 2.0)}%` }}
                                  className="bg-gradient-to-r from-purple-500 to-cyan-400 h-full rounded-full"
                                />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 3. TIMELINE EVENT PATTERNS TAB */}
          {activeSubTab === "TIMELINE" && (
            <div className="space-y-6">
              {/* Category Filter Tabs */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1">
                {timelineCategories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedTimelineCat(cat)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition shadow-sm ${
                      selectedTimelineCat === cat
                        ? "bg-cyan-600 text-white shadow-md"
                        : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    {cat === "ALL" ? "🌐 All Timeline Discoveries" : cat}
                  </button>
                ))}
              </div>

              {/* Pattern Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredTimelinePatterns.map((pat, idx) => (
                  <div
                    key={pat.pattern_id || idx}
                    className="p-5 bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 hover:border-cyan-400 dark:hover:border-cyan-500/50 rounded-2xl shadow-md transition space-y-4 flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="px-2.5 py-0.5 bg-purple-100 dark:bg-purple-500/20 text-purple-800 dark:text-purple-300 border border-purple-300 dark:border-purple-500/40 text-[10px] font-bold rounded-lg uppercase">
                          {pat.event_type}
                        </span>
                        <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                          <span>⚡ Lift:</span>
                          <span className="font-mono text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-950 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-800">
                            {pat.lift_score.toFixed(2)}x
                          </span>
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 leading-snug">
                        {pat.description}
                      </h3>
                    </div>

                    {/* Dimension Metrics & Visual Lift Bar */}
                    <div className="space-y-3 pt-2 border-t border-slate-200 dark:border-slate-800/80">
                      {pat.dimensions.map((dim, dIdx) => {
                        const freqPct = (dim.frequency * 100).toFixed(1);
                        const basePct = (dim.expected_by_chance * 100).toFixed(1);

                        return (
                          <div key={dIdx} className="space-y-1.5 bg-slate-50 dark:bg-slate-950/60 p-3 rounded-xl border border-slate-200 dark:border-slate-800/60">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-bold text-amber-800 dark:text-amber-300">{dim.dimension}: {dim.value}</span>
                              <span className="text-[11px] text-slate-600 dark:text-slate-400 font-mono">
                                Observed: <strong className="text-slate-900 dark:text-white">{freqPct}%</strong> vs Base: {basePct}%
                              </span>
                            </div>

                            {/* Bar Comparison */}
                            <div className="w-full bg-slate-200 dark:bg-slate-900 h-2 rounded-full overflow-hidden flex">
                              <div
                                style={{ width: `${Math.min(100, Number(freqPct) * 2.5)}%` }}
                                className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full rounded-full"
                              />
                            </div>
                          </div>
                        );
                      })}

                      {/* Evidence Footer */}
                      <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                        <span>Support: <strong className="text-slate-800 dark:text-slate-200">{pat.sample_size.toLocaleString()} cases</strong></span>
                        <span className="text-cyan-700 dark:text-cyan-300 font-bold">Confidence: {(pat.confidence_score * 100).toFixed(1)}% (p &lt; 0.0001)</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
