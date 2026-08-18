"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { WorkflowAnalysisResponse } from "@/lib/types";

interface TriggerItem {
  rule_id: string;
  rule_name: string;
  role: "primary" | "supporting" | "contradicting" | "cancellation";
  status: "triggered" | "not_triggered" | "insufficient_data";
  provenance: string;
  matched_conditions: string[];
  failed_conditions: string[];
  missing_facts: string[];
  explanation: string;
}

interface TechniqueEvaluationItem {
  technique_id: string;
  technique_name: string;
  tradition: string;
  objective: string;
  version: number;
  confidence: number;
  confidence_basis: string;
  is_matched: boolean;
  triggers: TriggerItem[];
  evidence: string[];
  ai_explanation?: {
    title: string;
    summary: string;
    body: string;
  } | null;
}

interface EvaluateChartResponse {
  evaluations: TechniqueEvaluationItem[];
  total_evaluated: number;
}

interface TechniquesPanelProps {
  workflowResult: WorkflowAnalysisResponse | null;
}

const RASHI_LORD_MAP: Record<string, string> = {
  aries: "mars",
  taurus: "venus",
  gemini: "mercury",
  cancer: "moon",
  leo: "sun",
  virgo: "mercury",
  libra: "venus",
  scorpio: "mars",
  sagittarius: "jupiter",
  capricorn: "saturn",
  aquarius: "saturn",
  pisces: "jupiter",
};

/** Helper to extract canonical facts from a WorkflowAnalysisResponse */
function extractFactsFromWorkflow(result: WorkflowAnalysisResponse): Record<string, unknown> {
  const facts: Record<string, unknown> = {};

  // 1. Planets
  if (result.chart?.planets) {
    for (const p of result.chart.planets) {
      const name = p.planet.toLowerCase();
      facts[`planet.${name}.house`] = p.house_number;
      facts[`planet.${name}.rashi`] = p.rashi.toLowerCase();
      facts[`planet.${name}.retrograde`] = p.is_retrograde ?? false;
      facts[`planet.${name}.combust`] = p.is_combust ?? false;
      facts[`planet.${name}.exalted`] = p.dignity?.toLowerCase() === "exalted";
      facts[`planet.${name}.own_sign`] = p.dignity?.toLowerCase() === "own";
    }
  }

  // 2. Houses & Lord placements
  if (result.chart?.houses) {
    const planetHouseMap: Record<string, number> = {};
    if (result.chart.planets) {
      for (const p of result.chart.planets) {
        planetHouseMap[p.planet.toLowerCase()] = p.house_number;
      }
    }
    for (const h of result.chart.houses) {
      const rashiName = h.rashi.toLowerCase();
      facts[`house.${h.house_number}.rashi`] = rashiName;
      const lordName = RASHI_LORD_MAP[rashiName];
      if (lordName) {
        facts[`house.${h.house_number}.lord`] = lordName;
        if (planetHouseMap[lordName] !== undefined) {
          facts[`house.${h.house_number}.lord_house`] = planetHouseMap[lordName];
        }
      }
    }
  }

  // 3. Yogas
  if (result.yogas?.results) {
    for (const y of result.yogas.results) {
      const slug = y.yoga_id.toLowerCase();
      facts[`yoga.${slug}.is_present`] = y.is_present;
      if (y.strength) facts[`yoga.${slug}.strength`] = y.strength;
    }
  }

  // 4. Dashas
  if (result.dasha?.mahadashas && result.dasha.mahadashas.length > 0) {
    facts["dasha.current_mahadasha"] = result.dasha.mahadashas[0].lord.toLowerCase();
  }

  return facts;
}

export function TechniquesPanel({ workflowResult }: TechniquesPanelProps) {
  const [selectedObjective, setSelectedObjective] = useState<string>("all");
  const [selectedTechniqueId, setSelectedTechniqueId] = useState<string | null>(null);

  const facts = useMemo(() => {
    if (!workflowResult) return {};
    return extractFactsFromWorkflow(workflowResult);
  }, [workflowResult]);

  const { data, isLoading, error } = useQuery<EvaluateChartResponse>({
    queryKey: ["technique-evaluations", facts, selectedObjective],
    queryFn: async () => {
      const payload: { facts: Record<string, unknown>; objective?: string } = { facts };
      if (selectedObjective !== "all") {
        payload.objective = selectedObjective;
      }
      return api.post<EvaluateChartResponse>("/api/v1/techniques/evaluate-chart", payload);
    },
    enabled: Object.keys(facts).length > 0,
  });

  const evaluations = data?.evaluations ?? [];
  const activeTechnique =
    evaluations.find((e) => e.technique_id === selectedTechniqueId) ?? evaluations[0] ?? null;

  const matchedCount = evaluations.filter((e) => e.is_matched).length;

  if (!workflowResult) {
    return (
      <div className="glass-card p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
        No chart analysis loaded. Please calculate or select a birth chart first.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Top Banner / Metrics */}
      <div className="glass-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl font-bold"
              style={{ background: "rgba(99, 102, 241, 0.15)", color: "#818cf8" }}
            >
              ✦
            </div>
            <div>
              <h2 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
                Technique Intelligence Catalog
              </h2>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                Declarative classical Jyotish techniques evaluated deterministically against active chart facts.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right">
              <span className="text-xs block uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Evaluated
              </span>
              <span className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                {evaluations.length}
              </span>
            </div>
            <div className="text-right">
              <span className="text-xs block uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Triggered
              </span>
              <span className="text-lg font-bold text-emerald-400">
                {matchedCount}
              </span>
            </div>
          </div>
        </div>

        {/* Objective Filters */}
        <div className="mt-4 flex flex-wrap items-center gap-2 pt-3 border-t border-white/5">
          <span className="text-xs mr-1" style={{ color: "var(--text-muted)" }}>Filter:</span>
          {[
            { id: "all", label: "All Techniques" },
            { id: "panch_mahapurusha", label: "Panch Mahapurusha" },
            { id: "raja_yoga", label: "Raja Yogas" },
            { id: "marriage_timing", label: "Marriage Timing" },
            { id: "wealth", label: "Wealth & Dhana" },
            { id: "ocular_health", label: "Medical / Health" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setSelectedObjective(tab.id);
                setSelectedTechniqueId(null);
              }}
              className={`px-3 py-1 text-xs font-medium rounded-lg transition ${
                selectedObjective === tab.id
                  ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                  : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="glass-card p-12 text-center text-sm" style={{ color: "var(--text-muted)" }}>
          Evaluating classical techniques against canonical chart facts...
        </div>
      ) : error ? (
        <div className="glass-card p-6 text-sm text-red-400 border border-red-500/20">
          Failed to evaluate techniques: {String(error)}
        </div>
      ) : evaluations.length === 0 ? (
        <div className="glass-card p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
          No techniques matched the selected objective filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Technique List */}
          <div className="lg:col-span-5 flex flex-col gap-2">
            {evaluations.map((item) => {
              const isSelected = activeTechnique?.technique_id === item.technique_id;
              return (
                <button
                  key={item.technique_id}
                  onClick={() => setSelectedTechniqueId(item.technique_id)}
                  className={`flex flex-col text-left p-4 rounded-xl transition border ${
                    isSelected
                      ? "bg-indigo-950/40 border-indigo-500/40 shadow-lg shadow-indigo-500/5"
                      : "bg-white/[0.02] border-white/5 hover:bg-white/[0.04] hover:border-white/10"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                        {item.technique_name}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-gray-300">
                        v{item.version}
                      </span>
                    </div>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        item.is_matched
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-gray-500/10 text-gray-400"
                      }`}
                    >
                      {item.confidence}%
                    </span>
                  </div>

                  <p className="mt-1 text-xs line-clamp-1" style={{ color: "var(--text-secondary)" }}>
                    {item.confidence_basis}
                  </p>

                  <div className="mt-2 flex items-center gap-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
                    <span className="capitalize">{item.tradition}</span>
                    <span>•</span>
                    <span className="capitalize">{item.objective.replace(/_/g, " ")}</span>
                    <span>•</span>
                    <span>{item.triggers.length} rules</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right Column: Selected Technique Detail */}
          {activeTechnique && (
            <div className="lg:col-span-7 flex flex-col gap-4">
              {/* Card Header & Confidence */}
              <div className="glass-card p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                        {activeTechnique.technique_name}
                      </h3>
                      <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
                        {activeTechnique.tradition}
                      </span>
                    </div>
                    <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                      Objective: <span className="capitalize">{activeTechnique.objective.replace(/_/g, " ")}</span>
                    </p>
                  </div>

                  <div className="text-right">
                    <div className="text-2xl font-black text-indigo-400">
                      {activeTechnique.confidence}%
                    </div>
                    <span className="text-[10px] uppercase tracking-wider block" style={{ color: "var(--text-muted)" }}>
                      Confidence
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-4 h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-500"
                    style={{ width: `${activeTechnique.confidence}%` }}
                  />
                </div>

                <p className="mt-2 text-xs italic" style={{ color: "var(--text-muted)" }}>
                  Basis: {activeTechnique.confidence_basis}
                </p>
              </div>

              {/* AI Explanation Card */}
              {activeTechnique.ai_explanation && (
                <div className="glass-card p-5 border-l-4 border-l-indigo-400">
                  <div className="flex items-center gap-2 text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2">
                    <span>✦</span> AI Technique Synthesis
                  </div>
                  <h4 className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
                    {activeTechnique.ai_explanation.title}
                  </h4>
                  <p className="text-xs mb-3 font-medium" style={{ color: "var(--text-secondary)" }}>
                    {activeTechnique.ai_explanation.summary}
                  </p>
                  <div className="text-xs leading-relaxed whitespace-pre-line p-3 rounded-lg bg-black/20 text-gray-300 border border-white/5">
                    {activeTechnique.ai_explanation.body}
                  </div>
                </div>
              )}

              {/* Rule Triggers Breakdown */}
              <div className="glass-card p-5">
                <h4 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--text-secondary)" }}>
                  Evaluated Rules & Factual Evidence
                </h4>

                <div className="flex flex-col gap-3">
                  {activeTechnique.triggers.map((trigger) => {
                    const isTriggered = trigger.status === "triggered";
                    const isInsufficient = trigger.status === "insufficient_data";

                    return (
                      <div
                        key={trigger.rule_id}
                        className="p-3 rounded-lg border border-white/5 bg-white/[0.02] flex flex-col gap-2"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm">
                              {isTriggered ? "✅" : isInsufficient ? "⚠️" : "❌"}
                            </span>
                            <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                              {trigger.rule_name}
                            </span>
                            <span className="text-[10px] font-mono px-1 rounded bg-white/5 text-gray-400">
                              {trigger.rule_id}
                            </span>
                          </div>

                          <span
                            className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded ${
                              trigger.role === "primary"
                                ? "bg-indigo-500/20 text-indigo-300"
                                : trigger.role === "supporting"
                                ? "bg-emerald-500/20 text-emerald-300"
                                : "bg-red-500/20 text-red-300"
                            }`}
                          >
                            {trigger.role}
                          </span>
                        </div>

                        <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                          {trigger.explanation}
                        </p>

                        {/* Matched Conditions */}
                        {trigger.matched_conditions.length > 0 && (
                          <div className="mt-1 flex flex-col gap-1">
                            <span className="text-[11px] font-medium text-emerald-400">
                              Matched Conditions:
                            </span>
                            {trigger.matched_conditions.map((c, idx) => (
                              <span key={idx} className="text-[11px] text-gray-300 pl-2 border-l border-emerald-500/40">
                                • {c}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Missing Facts */}
                        {trigger.missing_facts.length > 0 && (
                          <div className="mt-1 flex flex-col gap-1">
                            <span className="text-[11px] font-medium text-amber-400">
                              Missing Data:
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {trigger.missing_facts.map((mf, idx) => (
                                <span key={idx} className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300">
                                  {mf}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}