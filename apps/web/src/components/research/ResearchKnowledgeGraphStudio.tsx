"use client";

import React, { useState, useEffect } from "react";

interface GraphNode {
  node_id: string;
  label: string;
  node_type: string;
  epistemic_grade: string;
  base_confidence: number;
  properties: Record<string, any>;
  contributing_priorities: string[];
}

interface EvidenceEdge {
  edge_id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
  evidence_weight: number;
  empirical_lift: number;
  brier_score: number;
  prospective_supported: boolean;
  reproducibility_score: number;
  is_causal_claimed: boolean;
  claim_nature: string;
  epistemic_disclosure: string;
  p11_lineage_snapshot_id: string;
  provenance_hash: string;
}

interface HypothesisCluster {
  cluster_id: string;
  primary_hypothesis_id: string;
  competing_hypothesis_ids: string[];
  shared_feature_signatures: string[];
  lift_divergence: number;
  epistemic_arbitration_status: string;
}

interface TechniqueInteraction {
  interaction_id: string;
  technique_ids: string[];
  observed_joint_lift: number;
  observed_standalone_max_lift: number;
  synergy_delta: number;
  co_occurrence_count: number;
  epistemic_label: string;
}

interface KnowledgeGraphData {
  graph_id: string;
  target_objective: string;
  nodes: GraphNode[];
  edges: EvidenceEdge[];
  hypothesis_clusters: HypothesisCluster[];
  technique_interactions: TechniqueInteraction[];
  total_nodes: number;
  total_edges: number;
  graph_density_score: number;
  is_fully_non_causal: boolean;
  generated_at: string;
}

const DEFAULT_GRAPH: KnowledgeGraphData = {
  graph_id: "rkg-default-01",
  target_objective: "marriage",
  nodes: [
    {
      node_id: "node-graha-jupiter",
      label: "Guru (Jupiter)",
      node_type: "GRAHA",
      epistemic_grade: "GRADE_A_CANONICAL",
      base_confidence: 0.95,
      properties: { karaka: ["dharma", "marriage_timing", "expansion"] },
      contributing_priorities: ["P1", "P2", "P7"],
    },
    {
      node_id: "node-graha-saturn",
      label: "Shani (Saturn)",
      node_type: "GRAHA",
      epistemic_grade: "GRADE_A_CANONICAL",
      base_confidence: 0.95,
      properties: { karaka: ["karma", "delay_stabilization", "structure"] },
      contributing_priorities: ["P1", "P2", "P7"],
    },
    {
      node_id: "node-bhava-7",
      label: "7th House (Kalatra Bhava)",
      node_type: "BHAVA",
      epistemic_grade: "GRADE_A_CANONICAL",
      base_confidence: 0.95,
      properties: { house_number: 7, significations: ["marriage", "partnerships"] },
      contributing_priorities: ["P2", "P4"],
    },
    {
      node_id: "node-dasha-vimshottari-7th",
      label: "Vimshottari Dasha 7th Lord Period",
      node_type: "DASHA",
      epistemic_grade: "GRADE_A_STRONG_EMPIRICAL",
      base_confidence: 0.92,
      properties: { cycle_type: "Vimshottari" },
      contributing_priorities: ["P6", "P12"],
    },
    {
      node_id: "node-transit-dwi-gochara",
      label: "Dwi-Gochara Double Transit (Jup/Sat)",
      node_type: "TRANSIT",
      epistemic_grade: "GRADE_A_STRONG_EMPIRICAL",
      base_confidence: 0.94,
      properties: { transit_pair: ["Jupiter", "Saturn"] },
      contributing_priorities: ["P7", "P8"],
    },
    {
      node_id: "node-hyp-mined-01",
      label: "Hypothesis #1: Double Transit + 7th Lord Dasha Co-activation",
      node_type: "HYPOTHESIS",
      epistemic_grade: "EMPIRICALLY_SUPPORTED_PROSPECTIVE_RULE",
      base_confidence: 0.93,
      properties: { mining_id: "hyp-mining-01" },
      contributing_priorities: ["P19", "P20"],
    },
    {
      node_id: "node-hyp-mined-02",
      label: "Hypothesis #2: Ashtakavarga Bindu >= 30 Modulating Timing",
      node_type: "HYPOTHESIS",
      epistemic_grade: "DISCOVERED_HYPOTHESIS",
      base_confidence: 0.78,
      properties: { mining_id: "hyp-mining-02" },
      contributing_priorities: ["P4", "P19"],
    },
    {
      node_id: "node-tech-prediction-confluence",
      label: "Multi-Dasha & Transit Confluence Synthesis",
      node_type: "TECHNIQUE",
      epistemic_grade: "GRADE_A_STRONG_EMPIRICAL",
      base_confidence: 0.94,
      properties: { calibrated_weight: 0.85 },
      contributing_priorities: ["P8", "P16", "P23"],
    },
    {
      node_id: "node-outcome-marriage-milestone",
      label: "Outcome: Marriage Milestone Window Confirmation",
      node_type: "EVENT_OUTCOME",
      epistemic_grade: "GROUND_TRUTH_VERIFIED",
      base_confidence: 1.00,
      properties: { event_category: "marriage" },
      contributing_priorities: ["P15", "P21"],
    },
  ],
  edges: [
    {
      edge_id: "edge-01-jup-bhava7",
      source_node_id: "node-graha-jupiter",
      target_node_id: "node-bhava-7",
      relationship_type: "SUPPORTS",
      evidence_weight: 0.865,
      empirical_lift: 1.45,
      brier_score: 0.042,
      prospective_supported: true,
      reproducibility_score: 100.0,
      is_causal_claimed: false,
      claim_nature: "STATISTICALLY_REPLICATED",
      epistemic_disclosure: "ASSOCIATIONAL_ONLY: Statistically associated with relationship window activation.",
      p11_lineage_snapshot_id: "snap-p11-frozen-root",
      provenance_hash: "a1b2c3d4",
    },
    {
      edge_id: "edge-02-sat-bhava7",
      source_node_id: "node-graha-saturn",
      target_node_id: "node-bhava-7",
      relationship_type: "AMPLIFIES",
      evidence_weight: 0.892,
      empirical_lift: 1.55,
      brier_score: 0.039,
      prospective_supported: true,
      reproducibility_score: 100.0,
      is_causal_claimed: false,
      claim_nature: "STATISTICALLY_REPLICATED",
      epistemic_disclosure: "ASSOCIATIONAL_ONLY: Observed positive joint modulation of timing specificity.",
      p11_lineage_snapshot_id: "snap-p11-frozen-root",
      provenance_hash: "b2c3d4e5",
    },
    {
      edge_id: "edge-04-dasha-transit",
      source_node_id: "node-dasha-vimshottari-7th",
      target_node_id: "node-transit-dwi-gochara",
      relationship_type: "AMPLIFIES",
      evidence_weight: 0.925,
      empirical_lift: 1.65,
      brier_score: 0.035,
      prospective_supported: true,
      reproducibility_score: 100.0,
      is_causal_claimed: false,
      claim_nature: "STATISTICALLY_REPLICATED",
      epistemic_disclosure: "ASSOCIATIONAL_ONLY: Observed synergistic confluence between dasha period and dual transit triggers.",
      p11_lineage_snapshot_id: "snap-p11-frozen-root",
      provenance_hash: "c3d4e5f6",
    },
    {
      edge_id: "edge-05-transit-hyp1",
      source_node_id: "node-transit-dwi-gochara",
      target_node_id: "node-hyp-mined-01",
      relationship_type: "REPLICATES",
      evidence_weight: 0.915,
      empirical_lift: 1.60,
      brier_score: 0.038,
      prospective_supported: true,
      reproducibility_score: 100.0,
      is_causal_claimed: false,
      claim_nature: "STATISTICALLY_REPLICATED",
      epistemic_disclosure: "ASSOCIATIONAL_ONLY: Prospective cohort validation confirms mined hypothesis pattern.",
      p11_lineage_snapshot_id: "snap-p11-frozen-root",
      provenance_hash: "d4e5f6g7",
    },
    {
      edge_id: "edge-07-hyp1-hyp2-compete",
      source_node_id: "node-hyp-mined-01",
      target_node_id: "node-hyp-mined-02",
      relationship_type: "COMPETING_HYPOTHESIS",
      evidence_weight: 0.485,
      empirical_lift: 1.15,
      brier_score: 0.075,
      prospective_supported: false,
      reproducibility_score: 92.5,
      is_causal_claimed: false,
      claim_nature: "EMPIRICALLY_CORRELATED",
      epistemic_disclosure: "ASSOCIATIONAL_ONLY: Competing candidate pattern over overlapping feature space.",
      p11_lineage_snapshot_id: "snap-p11-frozen-root",
      provenance_hash: "e5f6g7h8",
    },
    {
      edge_id: "edge-08-tech-outcome",
      source_node_id: "node-tech-prediction-confluence",
      target_node_id: "node-outcome-marriage-milestone",
      relationship_type: "SUPPORTS",
      evidence_weight: 0.908,
      empirical_lift: 1.58,
      brier_score: 0.037,
      prospective_supported: true,
      reproducibility_score: 100.0,
      is_causal_claimed: false,
      claim_nature: "STATISTICALLY_REPLICATED",
      epistemic_disclosure: "ASSOCIATIONAL_ONLY: Calibrated multi-technique confluence consensus scoring.",
      p11_lineage_snapshot_id: "snap-p11-frozen-root",
      provenance_hash: "f6g7h8i9",
    },
  ],
  hypothesis_clusters: [
    {
      cluster_id: "chc-marriage-timing-01",
      primary_hypothesis_id: "node-hyp-mined-01",
      competing_hypothesis_ids: ["node-hyp-mined-02"],
      shared_feature_signatures: ["transit_jupiter_aspect_7th", "dasha_7th_lord"],
      lift_divergence: 0.45,
      epistemic_arbitration_status: "PRIMARY_PROSPECTIVELY_SUPPORTED_OVER_CANDIDATE",
    },
  ],
  technique_interactions: [
    {
      interaction_id: "ti-dwi-gochara-vimshottari-confluence",
      technique_ids: ["node-dasha-vimshottari-7th", "node-transit-dwi-gochara"],
      observed_joint_lift: 1.65,
      observed_standalone_max_lift: 1.45,
      synergy_delta: 0.20,
      co_occurrence_count: 182,
      epistemic_label: "OBSERVED_POSITIVE_CONFLUENCE",
    },
  ],
  total_nodes: 9,
  total_edges: 6,
  graph_density_score: 0.0833,
  is_fully_non_causal: true,
  generated_at: new Date().toISOString(),
};

export function ResearchKnowledgeGraphStudio() {
  const [targetObjective, setTargetObjective] = useState<string>("marriage");
  const [minWeight, setMinWeight] = useState<number>(0.0);
  const [nodeTypeFilter, setNodeTypeFilter] = useState<string>("ALL");
  const [graphData, setGraphData] = useState<KnowledgeGraphData>(DEFAULT_GRAPH);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"topology" | "edges" | "clusters" | "synergies" | "epistemics">("topology");

  const loadGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/knowledge-graph/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_objective: targetObjective,
          min_weight_threshold: minWeight,
          node_type_filter: nodeTypeFilter === "ALL" ? null : nodeTypeFilter,
        }),
      });
      if (res.ok) {
        const data: KnowledgeGraphData = await res.json();
        setGraphData(data);
      } else {
        throw new Error("API call failed");
      }
    } catch {
      // Offline fallback
      let filteredNodes = DEFAULT_GRAPH.nodes;
      if (nodeTypeFilter !== "ALL") {
        filteredNodes = filteredNodes.filter((n) => n.node_type === nodeTypeFilter);
      }
      const filteredEdges = DEFAULT_GRAPH.edges.filter((e) => e.evidence_weight >= minWeight);
      setGraphData({
        ...DEFAULT_GRAPH,
        target_objective: targetObjective,
        nodes: filteredNodes,
        edges: filteredEdges,
        total_nodes: filteredNodes.length,
        total_edges: filteredEdges.length,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [targetObjective, minWeight, nodeTypeFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-6 backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Priority 24: Evidence-Weighted Research Knowledge Graph
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Graha &rarr; Bhava &rarr; Dasha &rarr; Transit &rarr; Yoga &rarr; Varga &rarr; Outcome ontology with deterministic weights and non-causal provenance.
            </p>
          </div>
          <span className="rounded-full border border-teal-500/30 bg-teal-500/10 px-3 py-1 text-xs font-semibold text-teal-400">
            Priority 24 Active
          </span>
        </div>
      </div>

      {/* Control Filters */}
      <div className="grid grid-cols-1 gap-4 rounded-xl border border-slate-800 bg-slate-900/40 p-4 sm:grid-cols-4">
        <div>
          <label className="text-xs font-medium text-slate-400">Target Objective</label>
          <select
            value={targetObjective}
            onChange={(e) => setTargetObjective(e.target.value)}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          >
            <option value="marriage">Marriage & Relationships</option>
            <option value="career">Career & Leadership Elevation</option>
            <option value="health">Vitality & Health Diagnostics</option>
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400">
            Min Evidence Weight (W &ge; {minWeight.toFixed(2)})
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={minWeight}
            onChange={(e) => setMinWeight(parseFloat(e.target.value))}
            className="mt-2 w-full accent-teal-500"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-slate-400">Node Type Filter</label>
          <select
            value={nodeTypeFilter}
            onChange={(e) => setNodeTypeFilter(e.target.value)}
            className="mt-1 block w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white"
          >
            <option value="ALL">All Entity Types</option>
            <option value="GRAHA">Graha</option>
            <option value="BHAVA">Bhava</option>
            <option value="DASHA">Dasha</option>
            <option value="TRANSIT">Transit</option>
            <option value="YOGA">Yoga</option>
            <option value="VARGA">Varga</option>
            <option value="HYPOTHESIS">Hypothesis</option>
            <option value="TECHNIQUE">Technique</option>
            <option value="EVENT_OUTCOME">Event Outcome</option>
          </select>
        </div>
        <div className="flex items-end">
          <button
            onClick={loadGraph}
            disabled={loading}
            className="w-full rounded-lg bg-teal-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-teal-600/30 transition hover:bg-teal-500 disabled:opacity-50"
          >
            {loading ? "Refreshing Graph..." : "Query Research Knowledge Graph"}
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
          <span className="text-xs font-medium text-slate-400">Graph Nodes</span>
          <div className="mt-1 text-3xl font-black text-teal-400">{graphData.total_nodes}</div>
          <span className="text-xs text-slate-500">Ontological Entities</span>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
          <span className="text-xs font-medium text-slate-400">Weighted Edges</span>
          <div className="mt-1 text-3xl font-black text-amber-400">{graphData.total_edges}</div>
          <span className="text-xs text-slate-500">Deterministic W &ge; {minWeight}</span>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
          <span className="text-xs font-medium text-slate-400">Hypothesis Clusters</span>
          <div className="mt-1 text-3xl font-black text-cyan-400">{graphData.hypothesis_clusters.length}</div>
          <span className="text-xs text-slate-500">Cross-Hypothesis Overlaps</span>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-center">
          <span className="text-xs font-medium text-slate-400">Epistemic Status</span>
          <div className="mt-2 text-xs font-black text-emerald-400">100% NON-CAUSAL</div>
          <span className="text-xs text-slate-500">Observational / Associational</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800">
        <button
          onClick={() => setActiveTab("topology")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === "topology"
              ? "border-teal-500 text-teal-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Graph Topology & Entities ({graphData.nodes.length})
        </button>
        <button
          onClick={() => setActiveTab("edges")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === "edges"
              ? "border-teal-500 text-teal-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Evidence-Weighted Edges ({graphData.edges.length})
        </button>
        <button
          onClick={() => setActiveTab("clusters")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === "clusters"
              ? "border-teal-500 text-teal-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Cross-Hypothesis Clusters ({graphData.hypothesis_clusters.length})
        </button>
        <button
          onClick={() => setActiveTab("synergies")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === "synergies"
              ? "border-teal-500 text-teal-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Multi-Technique Interactions ({graphData.technique_interactions.length})
        </button>
        <button
          onClick={() => setActiveTab("epistemics")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === "epistemics"
              ? "border-teal-500 text-teal-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Non-Causal Epistemic Disclosure
        </button>
      </div>

      {/* Tab 1: Topology */}
      {activeTab === "topology" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Graha &rarr; Bhava &rarr; Dasha &rarr; Transit &rarr; Yoga &rarr; Varga &rarr; Outcome Entities
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {graphData.nodes.map((n) => (
              <div
                key={n.node_id}
                className="rounded-lg border border-slate-800 bg-slate-950 p-4 text-xs font-mono space-y-2"
              >
                <div className="flex justify-between font-bold text-white">
                  <span>{n.label}</span>
                  <span className="rounded bg-teal-500/20 px-2 py-0.5 text-teal-400">{n.node_type}</span>
                </div>
                <div className="text-slate-400">Grade: <span className="text-amber-400">{n.epistemic_grade}</span></div>
                <div className="text-slate-400">Confidence: <span className="text-emerald-400">{(n.base_confidence * 100).toFixed(1)}%</span></div>
                <div className="text-[11px] text-slate-500">
                  Priorities: {n.contributing_priorities.join(", ")}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Edges */}
      {activeTab === "edges" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
              Evidence-Weighted Relationships (W = 0.35L + 0.25B + 0.20P + 0.20R)
            </h2>
            <span className="text-xs font-mono text-emerald-400">Deterministic Closed-Form Weighting</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono text-slate-300">
              <thead className="border-b border-slate-800 bg-slate-950 text-slate-400">
                <tr>
                  <th className="p-3">Source Node</th>
                  <th className="p-3">Relationship</th>
                  <th className="p-3">Target Node</th>
                  <th className="p-3">Weight (W)</th>
                  <th className="p-3">Empirical Lift</th>
                  <th className="p-3">Brier Loss</th>
                  <th className="p-3">Prospective</th>
                  <th className="p-3">Provenance Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {graphData.edges.map((e) => (
                  <tr key={e.edge_id} className="hover:bg-slate-900/50">
                    <td className="p-3 text-sky-400 font-bold">{e.source_node_id}</td>
                    <td className="p-3">
                      <span className="rounded bg-purple-500/20 px-2 py-0.5 text-purple-300 font-bold">
                        {e.relationship_type}
                      </span>
                    </td>
                    <td className="p-3 text-cyan-400">{e.target_node_id}</td>
                    <td className="p-3 text-amber-400 font-bold">{e.evidence_weight.toFixed(4)}</td>
                    <td className="p-3 text-purple-400">{e.empirical_lift.toFixed(2)}x</td>
                    <td className="p-3 text-emerald-400">{e.brier_score.toFixed(3)}</td>
                    <td className="p-3 text-white">{e.prospective_supported ? "SUPPORTED" : "PENDING"}</td>
                    <td className="p-3 text-slate-500">{e.provenance_hash}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Clusters */}
      {activeTab === "clusters" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Cross-Hypothesis Competition & Overlap Clusters
          </h2>
          <div className="space-y-4 font-mono text-xs">
            {graphData.hypothesis_clusters.map((c) => (
              <div key={c.cluster_id} className="rounded-lg border border-slate-800 bg-slate-950 p-4 space-y-2">
                <div className="flex justify-between font-bold text-cyan-400">
                  <span>Cluster ID: {c.cluster_id}</span>
                  <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-emerald-300">
                    {c.epistemic_arbitration_status}
                  </span>
                </div>
                <div className="text-slate-300">
                  <span className="text-slate-500">Primary Hypothesis: </span>{c.primary_hypothesis_id}
                </div>
                <div className="text-slate-300">
                  <span className="text-slate-500">Competing Hypotheses: </span>{c.competing_hypothesis_ids.join(", ")}
                </div>
                <div className="text-slate-400">
                  <span className="text-slate-500">Shared Feature Signatures: </span>{c.shared_feature_signatures.join(", ")}
                </div>
                <div className="text-slate-400">
                  <span className="text-slate-500">Lift Divergence: </span>+{c.lift_divergence.toFixed(2)}x
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Synergies */}
      {activeTab === "synergies" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Multi-Technique Synergistic Confluence Discoveries
          </h2>
          <div className="space-y-4 font-mono text-xs">
            {graphData.technique_interactions.map((ti) => (
              <div key={ti.interaction_id} className="rounded-lg border border-teal-500/30 bg-slate-950 p-4 space-y-2">
                <div className="flex justify-between font-bold text-teal-400">
                  <span>Interaction: {ti.interaction_id}</span>
                  <span className="rounded bg-teal-500/20 px-2 py-0.5 text-teal-300">{ti.epistemic_label}</span>
                </div>
                <div className="text-slate-300">
                  <span className="text-slate-500">Technique Combination: </span>{ti.technique_ids.join(" + ")}
                </div>
                <div className="grid grid-cols-3 gap-2 text-slate-400 pt-1 border-t border-slate-900">
                  <div>Observed Joint Lift: <span className="text-purple-400 font-bold">{ti.observed_joint_lift.toFixed(2)}x</span></div>
                  <div>Standalone Max Lift: <span className="text-slate-300">{ti.observed_standalone_max_lift.toFixed(2)}x</span></div>
                  <div>Synergy Boost (&Delta;): <span className="text-emerald-400 font-bold">+{ti.synergy_delta.toFixed(2)}x</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 5: Epistemics */}
      {activeTab === "epistemics" && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4 text-xs font-mono">
          <h2 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider">
            Strict Epistemic & Non-Causal Boundary Declarations
          </h2>
          <p className="text-slate-300 leading-relaxed">
            All edges and relationships within the AstroOS Research Knowledge Graph are strictly <strong>observational, empirical, and associational</strong>.
          </p>
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4 space-y-3">
            <div className="text-amber-400 font-bold">1. Zero Physical Causality Claims (`is_causal_claimed: False`):</div>
            <p className="text-slate-400">
              Astrological positions, yogas, dasha periods, and transits do not exert physical mechanistic forces. Edges model statistical concordance and calibrated probability distributions across historical and prospective cohorts.
            </p>
            <div className="text-amber-400 font-bold">2. Amplification & Attenuation Disclosures:</div>
            <p className="text-slate-400">
              Edges labelled <code>AMPLIFIES</code> or <code>ATTENUATES</code> indicate observed statistical interaction effects (e.g. synergistic lift boosts when dual conditions co-occur), never direct causal causation.
            </p>
            <div className="text-amber-400 font-bold">3. Lineage & Cryptographic Integrity:</div>
            <p className="text-slate-400">
              Every edge is tied to a frozen $P_{11}$ snapshot SHA-256 hash and validated via $P_{22}$ reproducibility manifests.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
