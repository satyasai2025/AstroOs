"use client";

import React, { useState, useEffect } from "react";

interface CandidateHypothesisRanking {
  hypothesis_id: string;
  rule_name: string;
  target_objective: string;
  formula_expression: string;
  discovery_lift: number;
  fdr_q_value: number;
  reproducibility_score_percent: number;
  knowledge_graph_centrality: number;
  sample_deficit: number;
  evidence_priority_score: number;
  priority_rank: number;
  assigned_tier: string;
  required_sample_size_target: number;
  statistical_power_estimate: number;
  epistemic_rationale: string;
}

interface ExperimentBudgetTierAllocation {
  tier: string;
  allocated_chart_evaluations: number;
  allocation_percentage: number;
  target_studies_count: number;
  recommended_worker_concurrency: number;
  estimated_throughput_charts_per_sec: number;
}

interface ResearchPortfolioBudgetPlan {
  total_compute_charts_budget: number;
  tier_allocations: ExperimentBudgetTierAllocation[];
  max_parallel_workers: number;
  ephemeris_cache_target_hit_rate_pct: number;
  budget_utilization_percent: number;
}

interface PlannedExperimentPackage {
  plan_id: string;
  target_objective: string;
  total_hypotheses_ranked: number;
  ranked_candidates: CandidateHypothesisRanking[];
  budget_plan: ResearchPortfolioBudgetPlan;
  p11_lineage_snapshot_id: string;
  plan_provenance_hash: string;
  epistemic_non_causal_statement: string;
  planned_at: string;
}

const DEFAULT_PLAN: PlannedExperimentPackage = {
  plan_id: "plan-marriage-2026-q3",
  target_objective: "marriage",
  total_hypotheses_ranked: 2,
  ranked_candidates: [
    {
      hypothesis_id: "hyp-m1",
      rule_name: "7th Lord Dasha + Jupiter Aspect Rule",
      target_objective: "marriage",
      formula_expression: 'DASHA == "7th_Lord" AND TRANSIT_ASPECT("Jupiter", 7) AND SAV_SCORE >= 30',
      discovery_lift: 1.60,
      fdr_q_value: 0.012,
      reproducibility_score_percent: 100.0,
      knowledge_graph_centrality: 0.85,
      sample_deficit: 0,
      evidence_priority_score: 92.4,
      priority_rank: 1,
      assigned_tier: "TIER_A_PRIMARY_TRIAL",
      required_sample_size_target: 277,
      statistical_power_estimate: 0.88,
      epistemic_rationale: "High empirical lift and FDR significance. Top candidate for blind prospective forward validation.",
    },
    {
      hypothesis_id: "hyp-m2",
      rule_name: "Venus Transit over 7th House Confluence",
      target_objective: "marriage",
      formula_expression: 'TRANSIT("Venus", 7) AND ASHTAKAVARGA("Venus", 7) >= 5',
      discovery_lift: 1.42,
      fdr_q_value: 0.035,
      reproducibility_score_percent: 100.0,
      knowledge_graph_centrality: 0.65,
      sample_deficit: 120,
      evidence_priority_score: 78.1,
      priority_rank: 2,
      assigned_tier: "TIER_B_REPLICATION_STUDY",
      required_sample_size_target: 350,
      statistical_power_estimate: 0.80,
      epistemic_rationale: "Promising combinatorial pattern. Queued for multi-dataset holdout replication.",
    },
  ],
  budget_plan: {
    total_compute_charts_budget: 5000,
    tier_allocations: [
      {
        tier: "TIER_A_PRIMARY_TRIAL",
        allocated_chart_evaluations: 2650,
        allocation_percentage: 53.0,
        target_studies_count: 1,
        recommended_worker_concurrency: 2,
        estimated_throughput_charts_per_sec: 12500.0,
      },
      {
        tier: "TIER_B_REPLICATION_STUDY",
        allocated_chart_evaluations: 1600,
        allocation_percentage: 32.0,
        target_studies_count: 1,
        recommended_worker_concurrency: 1,
        estimated_throughput_charts_per_sec: 8000.0,
      },
      {
        tier: "TIER_C_EXPLORATORY_SCAN",
        allocated_chart_evaluations: 750,
        allocation_percentage: 15.0,
        target_studies_count: 1,
        recommended_worker_concurrency: 1,
        estimated_throughput_charts_per_sec: 4000.0,
      },
    ],
    max_parallel_workers: 4,
    ephemeris_cache_target_hit_rate_pct: 94.2,
    budget_utilization_percent: 100.0,
  },
  p11_lineage_snapshot_id: "snap-p11-frozen-root",
  plan_provenance_hash: "b8c9d1e2f3a4b5c6",
  epistemic_non_causal_statement: "PORTFOLIO_OPTIMIZATION_ONLY: EvidencePriorityScores and dynamic budget allocations optimize empirical statistical power and information yield without asserting physical causality.",
  planned_at: "2026-08-22T09:20:00Z",
};

export const ResearchPortfolioPlannerStudio: React.FC = () => {
  const [targetObjective, setTargetObjective] = useState("marriage");
  const [computeBudget, setComputeBudget] = useState(5000);
  const [workers, setWorkers] = useState(4);
  const [snapshotId, setSnapshotId] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"leaderboard" | "budget" | "manifest" | "governance">("leaderboard");
  const [plan, setPlan] = useState<PlannedExperimentPackage>(DEFAULT_PLAN);

  const fetchPlan = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/portfolio-planner/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_objective: targetObjective,
          total_compute_charts_budget: computeBudget,
          max_parallel_workers: workers,
          snapshot_id: snapshotId || null,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPlan(data);
      }
    } catch (e) {
      console.warn("Failed to fetch live portfolio plan, using fallback state:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan();
  }, [targetObjective]);

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case "TIER_A_PRIMARY_TRIAL":
        return {
          bg: "bg-indigo-500/10 border-indigo-500/30 text-indigo-400",
          label: "TIER A (PRIMARY TRIAL)",
        };
      case "TIER_B_REPLICATION_STUDY":
        return {
          bg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
          label: "TIER B (REPLICATION STUDY)",
        };
      default:
        return {
          bg: "bg-amber-500/10 border-amber-500/30 text-amber-400",
          label: "TIER C (EXPLORATORY SCAN)",
        };
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400 font-bold text-lg">
              🎯
            </span>
            <h1 className="text-2xl font-bold tracking-tight">
              Priority 26: Research Portfolio & Experiment Planner
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic EvidencePriorityScore ranking & dynamically constrained scientific compute allocation.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={targetObjective}
            onChange={(e) => setTargetObjective(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="marriage">Objective: Marriage</option>
            <option value="career">Objective: Career</option>
            <option value="wealth">Objective: Wealth</option>
            <option value="health">Objective: Health</option>
          </select>

          <input
            type="number"
            placeholder="Compute Budget"
            value={computeBudget}
            onChange={(e) => setComputeBudget(Number(e.target.value))}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 w-32"
          />

          <button
            onClick={fetchPlan}
            disabled={loading}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition shadow-lg shadow-indigo-600/20"
          >
            <span>{loading ? "Planning..." : "Generate Portfolio Plan"}</span>
          </button>
        </div>
      </div>

      {/* Top Banner: Portfolio Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Compute Budget */}
        <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/30 flex flex-col justify-between">
          <div>
            <span className="text-xs uppercase tracking-wider font-semibold text-indigo-400">
              Total Compute Budget
            </span>
            <div className="text-3xl font-extrabold text-white mt-1">
              {plan.budget_plan.total_compute_charts_budget.toLocaleString()} Charts
            </div>
          </div>
          <span className="text-xs text-indigo-300 mt-2">
            Max Workers: {plan.budget_plan.max_parallel_workers} • Cache Hit: {plan.budget_plan.ephemeris_cache_target_hit_rate_pct}%
          </span>
        </div>

        {/* Hypotheses Ranked */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Hypotheses Ranked
            </span>
            <div className="text-3xl font-extrabold text-white mt-1">
              {plan.total_hypotheses_ranked} Candidates
            </div>
          </div>
          <span className="text-xs text-emerald-400">
            Top Priority: {plan.ranked_candidates[0]?.rule_name || "None"}
          </span>
        </div>

        {/* Primary Prospective Allocations */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Tier A Allocation
            </span>
            <div className="text-3xl font-extrabold text-white mt-1">
              {plan.budget_plan.tier_allocations.find((t) => t.tier === "TIER_A_PRIMARY_TRIAL")?.allocation_percentage.toFixed(1)}%
            </div>
          </div>
          <span className="text-xs text-indigo-400">
            {plan.budget_plan.tier_allocations.find((t) => t.tier === "TIER_A_PRIMARY_TRIAL")?.allocated_chart_evaluations.toLocaleString()} Charts Reserved
          </span>
        </div>

        {/* Plan Provenance */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
              Plan Provenance
            </span>
            <div className="text-base font-mono font-bold text-slate-200 mt-1">
              {plan.plan_provenance_hash}
            </div>
          </div>
          <span className="text-xs text-slate-400">
            Snapshot: <span className="font-mono text-slate-300">{plan.p11_lineage_snapshot_id}</span>
          </span>
        </div>
      </div>

      {/* Studio Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("leaderboard")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "leaderboard"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>🏆 Prioritization Leaderboard ({plan.ranked_candidates.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("budget")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "budget"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>📊 Dynamic Budget Allocation Matrix</span>
        </button>

        <button
          onClick={() => setActiveTab("manifest")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "manifest"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>📜 Pre-Registration Experiment Manifest</span>
        </button>

        <button
          onClick={() => setActiveTab("governance")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
            activeTab === "governance"
              ? "bg-slate-800 text-indigo-400 border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <span>⚖️ Non-Causal Epistemic Governance</span>
        </button>
      </div>

      {/* Tab 1: Leaderboard */}
      {activeTab === "leaderboard" && (
        <div className="space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Rank</th>
                  <th className="py-3 px-4">Candidate Rule</th>
                  <th className="py-3 px-4">Formula Expression</th>
                  <th className="py-3 px-4">Lift / FDR q</th>
                  <th className="py-3 px-4">EvidencePriorityScore</th>
                  <th className="py-3 px-4">Target N (Power)</th>
                  <th className="py-3 px-4">Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm">
                {plan.ranked_candidates.map((c) => {
                  const tierBadge = getTierBadge(c.assigned_tier);
                  return (
                    <tr key={c.hypothesis_id} className="hover:bg-slate-900/40 transition">
                      <td className="py-4 px-4 font-mono font-bold text-indigo-400">
                        #{c.priority_rank}
                      </td>
                      <td className="py-4 px-4">
                        <div className="font-semibold text-slate-200">{c.rule_name}</div>
                        <div className="text-xs text-slate-500 font-mono">{c.hypothesis_id}</div>
                      </td>
                      <td className="py-4 px-4 font-mono text-xs text-slate-300 max-w-xs truncate">
                        {c.formula_expression}
                      </td>
                      <td className="py-4 px-4 text-xs font-mono">
                        <span className="text-emerald-400 font-bold">{c.discovery_lift.toFixed(2)}x</span>
                        <span className="text-slate-500"> (q: {c.fdr_q_value.toFixed(3)})</span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-sm">{c.evidence_priority_score.toFixed(1)}</span>
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-indigo-500 rounded-full"
                              style={{ width: `${Math.min(100, c.evidence_priority_score)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-xs font-mono text-slate-300">
                        N={c.required_sample_size_target} ({(c.statistical_power_estimate * 100).toFixed(0)}%)
                      </td>
                      <td className="py-4 px-4">
                        <span className={`text-xs px-2.5 py-1 rounded-md border font-mono font-semibold ${tierBadge.bg}`}>
                          {tierBadge.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Dynamic Budget Allocation Matrix */}
      {activeTab === "budget" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plan.budget_plan.tier_allocations.map((t) => {
              const tierBadge = getTierBadge(t.tier);
              return (
                <div
                  key={t.tier}
                  className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 flex flex-col justify-between"
                >
                  <div>
                    <span className={`text-xs px-2.5 py-1 rounded-md border font-mono font-semibold ${tierBadge.bg}`}>
                      {tierBadge.label}
                    </span>
                    <div className="text-3xl font-extrabold text-white mt-4">
                      {t.allocated_chart_evaluations.toLocaleString()}
                      <span className="text-sm font-normal text-slate-400 ml-1">charts</span>
                    </div>
                    <div className="text-sm text-indigo-400 font-semibold mt-1">
                      {t.allocation_percentage.toFixed(1)}% of total compute budget
                    </div>
                  </div>

                  <div className="space-y-2 pt-4 border-t border-slate-800/80 text-xs">
                    <div className="flex justify-between text-slate-400">
                      <span>Target Studies:</span>
                      <span className="font-mono text-slate-200">{t.target_studies_count} studies</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Worker Concurrency:</span>
                      <span className="font-mono text-slate-200">{t.recommended_worker_concurrency} threads</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Estimated Throughput:</span>
                      <span className="font-mono text-emerald-400">{t.estimated_throughput_charts_per_sec.toLocaleString()} charts/s</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 3: Pre-Registration Manifest */}
      {activeTab === "manifest" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Pre-Registration Experiment Execution Manifest
                </span>
                <h3 className="text-lg font-bold text-white mt-1 font-mono">{plan.plan_id}</h3>
              </div>
              <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-xs font-mono font-semibold">
                Status: PRE_REGISTERED_FOR_EXECUTION
              </span>
            </div>

            <pre className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-xs font-mono text-indigo-300 overflow-x-auto leading-relaxed">
              {JSON.stringify(
                {
                  plan_id: plan.plan_id,
                  target_objective: plan.target_objective,
                  planned_at: plan.planned_at,
                  total_hypotheses_ranked: plan.total_hypotheses_ranked,
                  tier_a_primary_candidates: plan.ranked_candidates.filter((c) => c.assigned_tier === "TIER_A_PRIMARY_TRIAL"),
                  compute_allocation_charts: plan.budget_plan.total_compute_charts_budget,
                  p11_lineage_snapshot: plan.p11_lineage_snapshot_id,
                  plan_provenance_hash: plan.plan_provenance_hash,
                },
                null,
                2
              )}
            </pre>
          </div>
        </div>
      )}

      {/* Tab 4: Non-Causal Epistemic Governance */}
      {activeTab === "governance" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>⚖️</span>
              <span>Epistemic Scope & Information Gain Boundary Disclosures</span>
            </h3>
            <p className="text-sm text-slate-300 bg-slate-950/60 p-4 rounded-xl border border-slate-800 font-mono text-xs leading-relaxed">
              {plan.epistemic_non_causal_statement}
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>🌿</span>
              <span>P11 Cryptographic Snapshot Lineage & Reproducibility</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400">P11 Lineage Snapshot:</span>
                <div className="text-slate-200 mt-1">{plan.p11_lineage_snapshot_id}</div>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                <span className="text-slate-400">Plan Provenance Hash:</span>
                <div className="text-slate-200 mt-1">{plan.plan_provenance_hash}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
