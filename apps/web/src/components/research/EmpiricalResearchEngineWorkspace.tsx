"use client";

import { useState, useEffect, useMemo } from "react";
import {
  fetchBenchmarkDatasets,
  fetchStandardHypotheses,
  runCohortSweep,
  exportResultsToCsv,
  type BenchmarkCohortDataset,
  type HypothesisDefinition,
  type HypothesisResult,
  type CohortSweepResponse,
} from "@/lib/empiricalResearch";

const CATEGORIES = [
  { id: "all", label: "All Domains" },
  { id: "career", label: "Career & Leadership" },
  { id: "marriage", label: "Marriage & Timing" },
  { id: "wealth", label: "Wealth & Dhana" },
  { id: "longevity", label: "Longevity & Ayurdaya" },
  { id: "health", label: "Health & Medical" },
  { id: "education", label: "Education & Intellect" },
  { id: "general", label: "Classical Yogas" },
];

export function EmpiricalResearchEngineWorkspace() {
  const [datasets, setDatasets] = useState<BenchmarkCohortDataset[]>([]);
  const [hypotheses, setHypotheses] = useState<HypothesisDefinition[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedHypothesisIds, setSelectedHypothesisIds] = useState<string[]>([]);
  const [nominalAlpha, setNominalAlpha] = useState<number>(0.05);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sweepResult, setSweepResult] = useState<CohortSweepResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"volcano" | "forest" | "contingency">("volcano");
  const [inspectedHypothesisId, setInspectedHypothesisId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Initial load: datasets and hypotheses
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [dsList, hypList] = await Promise.all([
          fetchBenchmarkDatasets(),
          fetchStandardHypotheses(),
        ]);
        setDatasets(dsList);
        setHypotheses(hypList);
        if (dsList.length > 0) {
          setSelectedDatasetId(dsList[0].cohort_id);
        }
        if (hypList.length > 0) {
          setSelectedHypothesisIds(hypList.map((h) => h.id));
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load research metadata.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Execute initial sweep once data is loaded
  useEffect(() => {
    if (datasets.length > 0 && hypotheses.length > 0 && !sweepResult) {
      handleExecuteSweep();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasets, hypotheses]);

  const handleExecuteSweep = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await runCohortSweep({
        cohort_id: selectedDatasetId,
        category: selectedCategory === "all" ? undefined : selectedCategory,
        hypothesis_ids: selectedHypothesisIds.length > 0 ? selectedHypothesisIds : undefined,
        nominal_alpha: nominalAlpha,
      });
      setSweepResult(res);
      if (res.results.length > 0) {
        setInspectedHypothesisId(res.results[0].hypothesis.id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to execute statistical sweep.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportCsv = () => {
    if (!sweepResult) return;
    const csvContent = exportResultsToCsv(sweepResult);
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `astroos_research_sweep_${sweepResult.sweep_id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportJson = () => {
    if (!sweepResult) return;
    const jsonContent = JSON.stringify(sweepResult, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `astroos_research_sweep_${sweepResult.sweep_id}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredResults = useMemo(() => {
    if (!sweepResult) return [];
    return sweepResult.results.filter((r) => {
      const matchSearch =
        r.hypothesis.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.hypothesis.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.hypothesis.classical_reference || "").toLowerCase().includes(searchQuery.toLowerCase());
      const matchCat =
        selectedCategory === "all" || r.hypothesis.category.toLowerCase() === selectedCategory.toLowerCase();
      return matchSearch && matchCat;
    });
  }, [sweepResult, searchQuery, selectedCategory]);

  const inspectedResult = useMemo(() => {
    if (!sweepResult || !inspectedHypothesisId) return null;
    return sweepResult.results.find((r) => r.hypothesis.id === inspectedHypothesisId) || null;
  }, [sweepResult, inspectedHypothesisId]);

  const activeDataset = datasets.find((d) => d.cohort_id === selectedDatasetId);

  return (
    <div className="space-y-8" data-testid="empirical-research-engine-workspace">
      {/* 1. Header & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-6" style={{ borderColor: "var(--border-subtle)" }}>
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 border border-indigo-500/20">
              EMPIRICAL RESEARCH ENGINE
            </span>
            <span className="text-xs text-zinc-400">• Pre-Registered Hypothesis Testing</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-100 flex items-center gap-3">
            <span className="text-indigo-600">🔬</span> Classical Jyotish Statistical Sweep Infrastructure
          </h1>
          <p className="text-sm text-zinc-400 mt-1 max-w-3xl">
            Automated hypothesis testing across validated cohort registries using exact Fisher distributions, Yates $\chi^2$, 
            Haldane-Anscombe Odds Ratios, Relative Risk, and Benjamini-Hochberg False Discovery Rate (FDR) corrections.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCsv}
            disabled={!sweepResult || loading}
            className="px-3.5 py-2 rounded-lg text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 transition flex items-center gap-2 disabled:opacity-50"
          >
            <span>📥</span> Export CSV
          </button>
          <button
            onClick={handleExportJson}
            disabled={!sweepResult || loading}
            className="px-3.5 py-2 rounded-lg text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 transition flex items-center gap-2 disabled:opacity-50"
          >
            <span>📄</span> Export JSON
          </button>
          <button
            onClick={handleExecuteSweep}
            disabled={loading}
            className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? <span className="animate-spin">⏳</span> : <span>⚡</span>}
            Run Statistical Sweep
          </button>
        </div>
      </div>

      {/* 2. Scientific Epistemology & Causal Rigor Notice */}
      <div className="rounded-xl p-4 bg-amber-500/10 border border-amber-500/20 flex items-start gap-3">
        <span className="text-amber-400 text-lg leading-none mt-0.5">⚠️</span>
        <div className="text-xs text-amber-200/90 leading-relaxed">
          <strong className="text-amber-300 font-semibold block mb-0.5">Scientific Rigor & Epistemological Boundary</strong>
          All computed inferential statistics ($\chi^2$, Fisher Exact, Odds Ratios, Relative Risk, and Cohen&apos;s $w$) quantify observational 
          correlation within the defined cohort dataset. Observational statistical significance does <strong>NOT</strong> prove direct physical, 
          astronomical, or astrological causality. Any positive statistical association requires independent replication across external cohorts.
        </div>
      </div>

      {/* 3. Cohort & Sweep Configuration Bar */}
      <div className="rounded-xl p-5 border glass-card space-y-4" style={{ borderColor: "var(--border-subtle)" }}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Dataset Selector */}
          <div>
            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block mb-1.5">
              Select Cohort Dataset
            </label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full text-xs rounded-lg p-2.5 bg-zinc-900 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-indigo-500"
            >
              {datasets.map((d) => (
                <option key={d.cohort_id} value={d.cohort_id}>
                  {d.title} (N={d.sample_size}, Rodden: {d.rodden_rating})
                </option>
              ))}
            </select>
          </div>

          {/* Life Domain Filter */}
          <div>
            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block mb-1.5">
              Classical Domain Filter
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full text-xs rounded-lg p-2.5 bg-zinc-900 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-indigo-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Nominal Alpha */}
          <div>
            <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block mb-1.5">
              Significance Level ($\alpha$)
            </label>
            <div className="flex items-center gap-3">
              <input 
                type="number"
                step="0.01"
                min="0.001"
                max="0.20"
                value={nominalAlpha}
                onChange={(e) => setNominalAlpha(parseFloat(e.target.value) || 0.05)}
                aria-label="Nominal Alpha FDR Target"
                className="w-24 text-xs rounded-lg p-2.5 bg-zinc-900 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-indigo-500"
              />
              <span className="text-xs text-zinc-400">
                FDR Target: $\alpha = {nominalAlpha}$
              </span>
            </div>
          </div>
        </div>

        {activeDataset && (
          <div className="pt-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-400">
            <div>
              <span className="font-semibold text-zinc-300">Active Cohort: </span>
              {activeDataset.description}
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-[10px]">
                RODDEN RATING: {activeDataset.rodden_rating}
              </span>
              <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px]">
                N = {activeDataset.sample_size} NATALS
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 4. Statistical Summary KPI Cards */}
      {sweepResult && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl border glass-card" style={{ borderColor: "var(--border-subtle)" }}>
            <div className="text-[11px] font-medium text-zinc-400 uppercase">Cohort Size (N)</div>
            <div className="text-xl font-bold text-zinc-100 mt-1">{sweepResult.total_cohort_size}</div>
            <div className="text-[10px] text-zinc-400 mt-0.5">Validated Records</div>
          </div>

          <div className="p-3.5 rounded-xl border glass-card" style={{ borderColor: "var(--border-subtle)" }}>
            <div className="text-[11px] font-medium text-zinc-400 uppercase">Hypotheses Tested</div>
            <div className="text-xl font-bold text-zinc-100 mt-1">{sweepResult.hypotheses_tested_count}</div>
            <div className="text-[10px] text-zinc-400 mt-0.5">Pre-registered H1</div>
          </div>

          <div className="p-3.5 rounded-xl border glass-card" style={{ borderColor: "var(--border-subtle)" }}>
            <div className="text-[11px] font-medium text-zinc-400 uppercase">Nominal Sig (p &lt; 0.05)</div>
            <div className="text-xl font-bold text-amber-400 mt-1">{sweepResult.nominal_significant_count}</div>
            <div className="text-[10px] text-amber-300/70 mt-0.5">Unadjusted Tests</div>
          </div>

          <div className="p-3.5 rounded-xl border glass-card bg-emerald-500/5 border-emerald-500/20">
            <div className="text-[11px] font-medium text-emerald-400 uppercase">FDR Significant (q &lt; 0.05)</div>
            <div className="text-xl font-bold text-emerald-400 mt-1">{sweepResult.fdr_significant_count}</div>
            <div className="text-[10px] text-emerald-300/70 mt-0.5">Benjamini-Hochberg</div>
          </div>

          <div className="p-3.5 rounded-xl border glass-card" style={{ borderColor: "var(--border-subtle)" }}>
            <div className="text-[11px] font-medium text-zinc-400 uppercase">Bonferroni Sig</div>
            <div className="text-xl font-bold text-indigo-600 mt-1">{sweepResult.bonferroni_significant_count}</div>
            <div className="text-[10px] text-zinc-400 mt-0.5">$\alpha \le {sweepResult.bonferroni_alpha}$</div>
          </div>

          <div className="p-3.5 rounded-xl border glass-card" style={{ borderColor: "var(--border-subtle)" }}>
            <div className="text-[11px] font-medium text-zinc-400 uppercase">Family-Wise Error</div>
            <div className="text-xl font-bold text-zinc-100 mt-1">&le; 5.0%</div>
            <div className="text-[10px] text-zinc-400 mt-0.5">Multiple Testing QC</div>
          </div>
        </div>
      )}

      {/* 5. Interactive Visualizations (Volcano Plot, Forest Plot, Contingency Matrix) */}
      <div className="rounded-xl border glass-card p-6 space-y-6" style={{ borderColor: "var(--border-subtle)" }}>
        <div className="flex items-center justify-between border-b pb-4" style={{ borderColor: "var(--border-subtle)" }}>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab("volcano")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === "volcano" ? "bg-indigo-600 text-white" : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              🌋 Volcano Plot (-log10 p vs Odds Ratio)
            </button>
            <button
              onClick={() => setActiveTab("forest")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === "forest" ? "bg-indigo-600 text-white" : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              🌲 Forest Plot (Odds Ratio 95% CI)
            </button>
            <button
              onClick={() => setActiveTab("contingency")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === "contingency" ? "bg-indigo-600 text-white" : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              📊 2x2 Contingency Matrix Inspector
            </button>
          </div>

          <div className="text-xs text-zinc-400">
            {sweepResult ? `Displaying ${sweepResult.results.length} hypotheses` : "No sweep executed"}
          </div>
        </div>

        {/* Tab 1: Interactive Volcano Plot */}
        {activeTab === "volcano" && sweepResult && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-zinc-400">
              <span>Y-Axis: -log10(Fisher p) &nbsp;|&nbsp; X-Axis: log2(Odds Ratio)</span>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span> FDR $q &lt; 0.05$ (Significant)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block"></span> Nominal $p &lt; 0.05$
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-zinc-500 inline-block"></span> Null / Inconclusive
                </span>
              </div>
            </div>

            <div className="w-full h-80 bg-zinc-950/80 rounded-xl border border-zinc-800 relative overflow-hidden flex items-center justify-center p-6">
              {/* Volcano SVG Canvas */}
              <svg className="w-full h-full" viewBox="0 0 800 280">
                {/* Grid & Axis Lines */}
                <line x1="50" y1="240" x2="750" y2="240" stroke="#374151" strokeWidth="1" />
                <line x1="400" y1="20" x2="400" y2="240" stroke="#374151" strokeDasharray="4 4" strokeWidth="1" />
                {/* Nominal p=0.05 threshold line: -log10(0.05) ~= 1.30 */}
                <line x1="50" y1="160" x2="750" y2="160" stroke="#f59e0b" strokeDasharray="3 3" strokeWidth="1" />
                <text x="755" y="164" fill="#f59e0b" fontSize="10" fontFamily="monospace">p=0.05</text>

                {/* X-Axis Labels */}
                <text x="50" y="260" fill="#9ca3af" fontSize="10" textAnchor="middle">&lt; 0.25 (Inverse)</text>
                <text x="400" y="260" fill="#9ca3af" fontSize="10" textAnchor="middle">OR = 1.0 (Null)</text>
                <text x="750" y="260" fill="#9ca3af" fontSize="10" textAnchor="middle">&gt; 4.0 (Strong Effect)</text>

                {/* Plot Data Points */}
                {sweepResult.results.map((r) => {
                  const logOr = Math.log2(Math.max(0.1, Math.min(10.0, r.odds_ratio)));
                  // Map logOr from -3..+3 to x: 50..750 (center 400)
                  const cx = 400 + (logOr / 3.0) * 320;
                  const logP = -Math.log10(Math.max(1e-6, r.fisher_exact_p_value));
                  // Map logP from 0..5 to y: 240..30
                  const cy = 240 - (logP / 5.0) * 210;

                  const isSelected = r.hypothesis.id === inspectedHypothesisId;
                  const color = r.is_significant_fdr
                    ? "#34d399"
                    : r.is_significant_nominal
                    ? "#fbbf24"
                    : "#71717a";

                  return (
                    <g
                      key={r.hypothesis.id}
                      className="cursor-pointer transition-transform hover:scale-125"
                      onClick={() => {
                        setInspectedHypothesisId(r.hypothesis.id);
                        setActiveTab("contingency");
                      }}
                    >
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isSelected ? 7 : 5}
                        fill={color}
                        stroke={isSelected ? "#ffffff" : "#18181b"}
                        strokeWidth={isSelected ? 2 : 1}
                      />
                      <text
                        x={cx}
                        y={cy - 8}
                        fill="#e4e4e7"
                        fontSize="9"
                        textAnchor="middle"
                        className="pointer-events-none select-none font-mono"
                      >
                        {r.hypothesis.id.replace("HYP-", "")}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
            <p className="text-[11px] text-zinc-400 text-center">
              Click any data point above to inspect its exact 2x2 contingency matrix and classical rule derivation.
            </p>
          </div>
        )}

        {/* Tab 2: Forest Plot */}
        {activeTab === "forest" && sweepResult && (
          <div className="space-y-4">
            <div className="text-xs text-zinc-400 mb-2">
              Forest Plot: Odds Ratios and 95% Wald Confidence Intervals across all pre-registered hypotheses.
            </div>

            <div className="space-y-3">
              {sweepResult.results.map((r) => {
                const isSelected = r.hypothesis.id === inspectedHypothesisId;
                const isSig = r.is_significant_fdr;
                return (
                  <div
                    key={r.hypothesis.id}
                    onClick={() => {
                      setInspectedHypothesisId(r.hypothesis.id);
                      setActiveTab("contingency");
                    }}
                    className={`p-3 rounded-lg border transition cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-3 ${
                      isSelected
                        ? "bg-indigo-950/30 border-indigo-500/50"
                        : "bg-zinc-900/50 border-zinc-800 hover:border-zinc-700"
                    }`}
                  >
                    <div className="w-full md:w-1/3">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300">
                          {r.hypothesis.id}
                        </span>
                        <span className="text-xs font-semibold text-zinc-200 truncate">
                          {r.hypothesis.title}
                        </span>
                      </div>
                      <div className="text-[11px] text-zinc-400 truncate mt-0.5">
                        {r.hypothesis.classical_reference || "Classical Jyotish Rule"}
                      </div>
                    </div>

                    {/* Odds Ratio Bar Visualization */}
                    <div className="w-full md:w-1/2 flex items-center gap-3">
                      <div className="w-full bg-zinc-950 h-6 rounded border border-zinc-800 relative flex items-center px-2">
                        {/* Null line at OR=1.0 */}
                        <div className="absolute top-0 bottom-0 left-1/3 w-[1px] bg-zinc-600 z-0"></div>
                        {/* Error Bar */}
                        <div
                          className="h-1.5 bg-indigo-500/40 rounded absolute z-10"
                          style={{
                            left: `${Math.max(5, Math.min(85, (r.odds_ratio_ci_lower / 6) * 100))}%`,
                            width: `${Math.max(5, Math.min(90, ((r.odds_ratio_ci_upper - r.odds_ratio_ci_lower) / 6) * 100))}%`,
                          }}
                        ></div>
                        {/* Center Point */}
                        <div
                          className={`w-3 h-3 rounded-full absolute z-20 shadow ${
                            isSig ? "bg-emerald-400" : "bg-zinc-400"
                          }`}
                          style={{
                            left: `${Math.max(5, Math.min(95, (r.odds_ratio / 6) * 100))}%`,
                            transform: "translateX(-50%)",
                          }}
                        ></div>
                      </div>
                    </div>

                    <div className="w-full md:w-1/6 text-right font-mono text-xs">
                      <div className={isSig ? "text-emerald-400 font-bold" : "text-zinc-300"}>
                        OR: {r.odds_ratio.toFixed(2)}
                      </div>
                      <div className="text-[10px] text-zinc-400">
                        [{r.odds_ratio_ci_lower.toFixed(2)} - {r.odds_ratio_ci_upper.toFixed(2)}]
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 3: 2x2 Contingency Matrix Inspector */}
        {activeTab === "contingency" && inspectedResult && (
          <div className="space-y-6">
            <div className="border-b pb-4 border-zinc-800 flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div>
                <span className="text-xs font-mono text-indigo-600">{inspectedResult.hypothesis.id}</span>
                <h2 className="text-base font-bold text-zinc-100">{inspectedResult.hypothesis.title}</h2>
                <p className="text-xs text-zinc-400 mt-0.5">{inspectedResult.hypothesis.description}</p>
              </div>
              <div className="text-right">
                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-semibold ${
                    inspectedResult.verdict === "CONFIRMED_SIGNIFICANT"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      : inspectedResult.verdict === "TREND_SUGGESTIVE"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : "bg-zinc-800 text-zinc-300 border border-zinc-700"
                  }`}
                >
                  {inspectedResult.verdict.replace(/_/g, " ")}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 2x2 Table */}
              <div className="space-y-3">
                <div className="text-xs font-semibold uppercase text-zinc-400 tracking-wider">
                  2x2 Contingency Matrix ($N = {inspectedResult.sample_size_n}$)
                </div>
                <div className="border border-zinc-800 rounded-xl overflow-hidden text-xs">
                  <table className="w-full text-center">
                    <thead className="bg-zinc-900 text-zinc-400 font-semibold border-b border-zinc-800">
                      <tr>
                        <th className="p-3 text-left">Astrological Exposure</th>
                        <th className="p-3 text-emerald-400">Target Outcome (+)</th>
                        <th className="p-3 text-zinc-400">Control (-)</th>
                        <th className="p-3 text-zinc-400">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800 font-mono">
                      <tr className="bg-zinc-900/30">
                        <td className="p-3 text-left font-sans font-medium text-zinc-300">
                          Exposed (Rule Satisfied)
                        </td>
                        <td className="p-3 text-emerald-400 font-bold bg-emerald-500/5">
                          {inspectedResult.contingency_table.a_exposed_cases} <span className="text-[10px] text-zinc-400">(a)</span>
                        </td>
                        <td className="p-3 text-zinc-300">
                          {inspectedResult.contingency_table.b_exposed_controls} <span className="text-[10px] text-zinc-400">(b)</span>
                        </td>
                        <td className="p-3 text-zinc-200 font-bold">
                          {inspectedResult.contingency_table.total_exposed}
                        </td>
                      </tr>
                      <tr className="bg-zinc-900/10">
                        <td className="p-3 text-left font-sans font-medium text-zinc-400">
                          Unexposed (Rule Absent)
                        </td>
                        <td className="p-3 text-zinc-300">
                          {inspectedResult.contingency_table.c_unexposed_cases} <span className="text-[10px] text-zinc-400">(c)</span>
                        </td>
                        <td className="p-3 text-zinc-400">
                          {inspectedResult.contingency_table.d_unexposed_controls} <span className="text-[10px] text-zinc-400">(d)</span>
                        </td>
                        <td className="p-3 text-zinc-200 font-bold">
                          {inspectedResult.contingency_table.total_unexposed}
                        </td>
                      </tr>
                      <tr className="bg-zinc-900/80 font-bold text-zinc-200">
                        <td className="p-3 text-left font-sans">Marginal Total</td>
                        <td className="p-3 text-emerald-400">{inspectedResult.contingency_table.total_cases}</td>
                        <td className="p-3">{inspectedResult.contingency_table.total_controls}</td>
                        <td className="p-3 text-indigo-600">{inspectedResult.contingency_table.total_n}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="flex items-center justify-between text-xs text-zinc-400 pt-2">
                  <div>
                    Exposure in Cases:{" "}
                    <strong className="text-zinc-200 font-mono">
                      {inspectedResult.contingency_table.exposure_rate_cases}%
                    </strong>
                  </div>
                  <div>
                    Exposure in Controls:{" "}
                    <strong className="text-zinc-200 font-mono">
                      {inspectedResult.contingency_table.exposure_rate_controls}%
                    </strong>
                  </div>
                </div>
              </div>

              {/* Inferential Metrics Breakdown */}
              <div className="space-y-3">
                <div className="text-xs font-semibold uppercase text-zinc-400 tracking-wider">
                  Mathematical &amp; Inferential Profile
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div className="text-zinc-400">Odds Ratio (Haldane)</div>
                    <div className="text-sm font-bold text-zinc-100 mt-1 font-mono">
                      {inspectedResult.odds_ratio.toFixed(3)}
                    </div>
                    <div className="text-[10px] text-zinc-400">
                      95% CI: [{inspectedResult.odds_ratio_ci_lower.toFixed(2)} - {inspectedResult.odds_ratio_ci_upper.toFixed(2)}]
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div className="text-zinc-400">Relative Risk (RR)</div>
                    <div className="text-sm font-bold text-zinc-100 mt-1 font-mono">
                      {inspectedResult.relative_risk.toFixed(3)}
                    </div>
                    <div className="text-[10px] text-zinc-400">
                      95% CI: [{inspectedResult.relative_risk_ci_lower.toFixed(2)} - {inspectedResult.relative_risk_ci_upper.toFixed(2)}]
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div className="text-zinc-400">Fisher Exact p-value</div>
                    <div className="text-sm font-bold text-amber-400 mt-1 font-mono">
                      {inspectedResult.fisher_exact_p_value.toExponential(3)}
                    </div>
                    <div className="text-[10px] text-zinc-400">Hypergeometric Sum</div>
                  </div>

                  <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                    <div className="text-zinc-400">FDR q-value (B-H)</div>
                    <div className="text-sm font-bold text-emerald-400 mt-1 font-mono">
                      {inspectedResult.fdr_q_value.toExponential(3)}
                    </div>
                    <div className="text-[10px] text-zinc-400">
                      {inspectedResult.is_significant_fdr ? "Significant" : "Not Significant"}
                    </div>
                  </div>
                </div>

                {/* Audit Trace */}
                <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 space-y-1">
                  <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Classical Citation &amp; Proof Trace
                  </div>
                  <div className="text-xs text-zinc-300 font-serif italic">
                    {inspectedResult.hypothesis.classical_reference || "Classical Vedic Source"}
                  </div>
                  <div className="text-[11px] text-zinc-400 mt-2">
                    Rule Parameters: {JSON.stringify(inspectedResult.hypothesis.exposure_rule.parameters)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 6. Comprehensive Evidence Table */}
      <div className="rounded-xl border glass-card p-6 space-y-4" style={{ borderColor: "var(--border-subtle)" }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-4" style={{ borderColor: "var(--border-subtle)" }}>
          <div>
            <h2 className="text-base font-bold text-zinc-100">Hypothesis Evidence Matrix</h2>
            <p className="text-xs text-zinc-400">Complete inferential results across all evaluated classical hypotheses.</p>
          </div>

          <div className="w-full sm:w-64">
            <input 
              type="text"
              placeholder="Search hypotheses, classical sources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search hypotheses, classical sources"
              className="w-full text-xs rounded-lg p-2 bg-zinc-900 border border-zinc-700 text-zinc-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 font-semibold bg-zinc-900/50">
                <th className="py-3 px-3">Hypothesis</th>
                <th className="py-3 px-2 text-center">Category</th>
                <th className="py-3 px-2 text-center">Sample N</th>
                <th className="py-3 px-2 text-center">Odds Ratio [95% CI]</th>
                <th className="py-3 px-2 text-center">Relative Risk</th>
                <th className="py-3 px-2 text-center">Yates $\chi^2$</th>
                <th className="py-3 px-2 text-center">Fisher $p$</th>
                <th className="py-3 px-2 text-center">FDR $q$</th>
                <th className="py-3 px-2 text-center">Cohen $w$</th>
                <th className="py-3 px-3 text-right">Verdict</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono">
              {filteredResults.map((r) => {
                const isSelected = r.hypothesis.id === inspectedHypothesisId;
                return (
                  <tr
                    key={r.hypothesis.id}
                    onClick={() => {
                      setInspectedHypothesisId(r.hypothesis.id);
                      setActiveTab("contingency");
                    }}
                    className={`transition cursor-pointer ${
                      isSelected ? "bg-indigo-950/40 text-zinc-100" : "hover:bg-zinc-900/40 text-zinc-300"
                    }`}
                  >
                    <td className="py-3 px-3 font-sans">
                      <div className="font-semibold text-zinc-200 flex items-center gap-1.5">
                        <span className="font-mono text-[10px] text-indigo-600">{r.hypothesis.id}</span>
                        <span>{r.hypothesis.title}</span>
                      </div>
                      <div className="text-[10px] text-zinc-400 truncate max-w-xs font-serif italic">
                        {r.hypothesis.classical_reference || "Classical Jyotish Source"}
                      </div>
                    </td>
                    <td className="py-3 px-2 text-center font-sans capitalize text-zinc-400">
                      {r.hypothesis.category}
                    </td>
                    <td className="py-3 px-2 text-center text-zinc-300">{r.sample_size_n}</td>
                    <td className="py-3 px-2 text-center">
                      <span className={r.odds_ratio > 1.5 ? "text-emerald-400 font-bold" : "text-zinc-200"}>
                        {r.odds_ratio.toFixed(2)}
                      </span>{" "}
                      <span className="text-[10px] text-zinc-400">
                        [{r.odds_ratio_ci_lower.toFixed(1)}-{r.odds_ratio_ci_upper.toFixed(1)}]
                      </span>
                    </td>
                    <td className="py-3 px-2 text-center text-zinc-300">{r.relative_risk.toFixed(2)}</td>
                    <td className="py-3 px-2 text-center text-zinc-400">{r.chi_square_stat.toFixed(2)}</td>
                    <td className="py-3 px-2 text-center text-amber-400">
                      {r.fisher_exact_p_value < 0.001
                        ? r.fisher_exact_p_value.toExponential(2)
                        : r.fisher_exact_p_value.toFixed(3)}
                    </td>
                    <td className="py-3 px-2 text-center text-emerald-400 font-semibold">
                      {r.fdr_q_value < 0.001 ? r.fdr_q_value.toExponential(2) : r.fdr_q_value.toFixed(3)}
                    </td>
                    <td className="py-3 px-2 text-center text-zinc-300">{r.cohen_w_effect_size.toFixed(2)}</td>
                    <td className="py-3 px-3 text-right font-sans">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          r.is_significant_fdr
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : r.is_significant_nominal
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-zinc-800 text-zinc-400"
                        }`}
                      >
                        {r.verdict === "CONFIRMED_SIGNIFICANT"
                          ? "CONFIRMED"
                          : r.verdict === "TREND_SUGGESTIVE"
                          ? "TREND"
                          : "NULL"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
