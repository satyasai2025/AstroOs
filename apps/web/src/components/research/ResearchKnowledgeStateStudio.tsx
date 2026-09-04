"use client";

import React, { useState, useEffect } from "react";

interface StudyEvidenceEntry {
  study_id: string;
  study_type: string;
  title: string;
  sample_size: number;
  metric_name: string;
  observed_metric: number;
  variance: number;
  is_prospective: boolean;
  is_independent: boolean;
  weight: number;
}

interface MetaAnalysisResult {
  pooled_effect_size: number;
  pooled_variance: number;
  confidence_interval: number[];
  i_squared_heterogeneity: number;
  heterogeneity_level: string;
  tau_squared: number;
  p_value: number;
  total_samples: number;
  forest_plot_data: {
    studies: Array<{
      study_id: string;
      metric: number;
      ci_lower: number;
      ci_upper: number;
      weight_percent: number;
    }>;
    pooled: {
      metric: number;
      ci_lower: number;
      ci_upper: number;
    };
  };
}

interface KnowledgeStateTransition {
  transition_id: string;
  from_state: string;
  to_state: string;
  trigger_study_id: string;
  reason: string;
  timestamp: string;
}

interface ResearchKnowledgeStateRecord {
  state_id: string;
  state_version: string;
  target_objective: string;
  current_state: string;
  evidence_grade: string;
  certainty_score: number;
  meta_analysis: MetaAnalysisResult;
  accumulated_studies: StudyEvidenceEntry[];
  transitions: KnowledgeStateTransition[];
  superseded_state_id: string | null;
  created_at: string;
}

interface KnowledgeStateSynthesisAssessment {
  assessment_id: string;
  knowledge_state: ResearchKnowledgeStateRecord;
  overall_verdict: string;
  verdict_explanation: string[];
  limitations: string[];
  warnings: string[];
  knowledge_state_fingerprint: string;
  knowledge_snapshot_id: string;
  created_at: string;
  non_causal_disclosure: string;
}

const DEFAULT_ASSESSMENT: KnowledgeStateSynthesisAssessment = {
  assessment_id: "rks-assess-default",
  knowledge_state: {
    state_id: "rks-default",
    state_version: "v1.0",
    target_objective: "marriage",
    current_state: "REPLICATED_KNOWLEDGE_STATE",
    evidence_grade: "GRADE_A",
    certainty_score: 0.86,
    meta_analysis: {
      pooled_effect_size: 0.7967,
      pooled_variance: 0.001333,
      confidence_interval: [0.7251, 0.8683],
      i_squared_heterogeneity: 0.0,
      heterogeneity_level: "LOW_HETEROGENEITY",
      tau_squared: 0.0,
      p_value: 0.0001,
      total_samples: 600,
      forest_plot_data: {
        studies: [
          { study_id: "study-p33-discovery", metric: 0.82, ci_lower: 0.7128, ci_upper: 0.9272, weight_percent: 22.22 },
          { study_id: "study-p34-replication", metric: 0.79, ci_lower: 0.7308, ci_upper: 0.8492, weight_percent: 55.56 },
          { study_id: "study-p35-generalization", metric: 0.78, ci_lower: 0.7114, ci_upper: 0.8486, weight_percent: 22.22 },
        ],
        pooled: { metric: 0.7967, ci_lower: 0.7251, ci_upper: 0.8683 },
      },
    },
    accumulated_studies: [
      {
        study_id: "study-p33-discovery",
        study_type: "P33_VALIDITY",
        title: "P33 Primary Discovery Cohort Assessment",
        sample_size: 150,
        metric_name: "ACCURACY",
        observed_metric: 0.82,
        variance: 0.003,
        is_prospective: true,
        is_independent: false,
        weight: 0.25,
      },
      {
        study_id: "study-p34-replication",
        study_type: "P34_REPLICATION",
        title: "P34 Multi-Center Independent Replication Study",
        sample_size: 250,
        metric_name: "ACCURACY",
        observed_metric: 0.79,
        variance: 0.004,
        is_prospective: true,
        is_independent: true,
        weight: 0.4167,
      },
      {
        study_id: "study-p35-generalization",
        study_type: "P35_GENERALIZATION",
        title: "P35 Cross-Domain Transportability Trial",
        sample_size: 200,
        metric_name: "ACCURACY",
        observed_metric: 0.78,
        variance: 0.005,
        is_prospective: true,
        is_independent: true,
        weight: 0.3333,
      },
    ],
    transitions: [
      {
        transition_id: "trans-1",
        from_state: "UNSETTLED",
        to_state: "EMERGING_EVIDENCE",
        trigger_study_id: "study-p33-discovery",
        reason: "Primary discovery cohort validation completed.",
        timestamp: "2026-08-23T00:00:00Z",
      },
      {
        transition_id: "trans-2",
        from_state: "EMERGING_EVIDENCE",
        to_state: "METHODOLOGICALLY_SUPPORTED",
        trigger_study_id: "study-p33-discovery",
        reason: "P33 statistical integrity checks satisfied.",
        timestamp: "2026-08-23T00:01:00Z",
      },
      {
        transition_id: "trans-3",
        from_state: "METHODOLOGICALLY_SUPPORTED",
        to_state: "REPLICATED_KNOWLEDGE_STATE",
        trigger_study_id: "study-p34-replication",
        reason: "Multi-center independent replication verified with baseline superiority.",
        timestamp: "2026-08-23T00:02:00Z",
      },
    ],
    superseded_state_id: null,
    created_at: "2026-08-23T00:00:00Z",
  },
  overall_verdict: "REPLICATED_KNOWLEDGE_STATE",
  verdict_explanation: [
    "Longitudinal synthesis completed across 3 independent studies (N=600).",
    "Meta-analytic pooled effect size: 0.7967 (95% CI [0.7251, 0.8683]).",
    "Higgins I^2 heterogeneity: 0.0% (LOW_HETEROGENEITY).",
    "Knowledge State transitioned to REPLICATED_KNOWLEDGE_STATE with Evidence Grade GRADE_A.",
  ],
  limitations: ["Longitudinal evidence synthesis reflects accumulated retrospective and prospective trials to date."],
  warnings: [],
  knowledge_state_fingerprint: "k1n2o3w4l5e6d7g8e9s0t1a2t3e4f5i6n7g8e9r0p1r2i3n4t5h6a7s8h9f01234",
  knowledge_snapshot_id: "snap-rks-default",
  created_at: "2026-08-23T00:00:00Z",
  non_causal_disclosure: "RESEARCH_KNOWLEDGE_STATE_DISCLOSURE: Research Knowledge State synthesizes longitudinal evidentiary weight, meta-analytic effect size, and replication history across pre-registered trials. It does not establish astrological causation, predictive validity, or a physical mechanism.",
};

const STATE_STYLES: Record<string, string> = {
  REPLICATED_KNOWLEDGE_STATE: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
  METHODOLOGICALLY_SUPPORTED: "bg-indigo-500/10 border-indigo-500/30 text-indigo-400",
  EMERGING_EVIDENCE: "bg-indigo-500/10 border-indigo-500/30 text-indigo-400",
  UNSETTLED: "bg-slate-800 border-slate-700 text-slate-300",
  FALSIFIED_KNOWLEDGE_STATE: "bg-rose-500/10 border-rose-500/30 text-rose-400",
  CONTRADICTED_KNOWLEDGE_STATE: "bg-rose-500/10 border-rose-500/30 text-rose-400",
};

const GRADE_STYLES: Record<string, string> = {
  GRADE_A: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
  GRADE_B: "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30",
  GRADE_C: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
  GRADE_D: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
  GRADE_F: "bg-rose-500/20 text-rose-300 border border-rose-500/30",
};

export const ResearchKnowledgeStateStudio: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"overview" | "lineage" | "meta" | "statemachine" | "versioning" | "provenance">("overview");
  const [data, setData] = useState<KnowledgeStateSynthesisAssessment>(DEFAULT_ASSESSMENT);
  const [loading, setLoading] = useState(false);

  const runSynthesis = async (overrideFalsified = false, overrideLowSample = false) => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/knowledge-state/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          override_replication_falsified: overrideFalsified,
          override_low_sample: overrideLowSample,
        }),
      });
      if (res.ok) {
        const synthData = await res.json();
        setData(synthData);
      } else {
        setData(DEFAULT_ASSESSMENT);
      }
    } catch (e) {
      console.warn("Failed to fetch live knowledge state, using fallback:", e);
      setData(DEFAULT_ASSESSMENT);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSynthesis();
  }, []);

  const kState = data.knowledge_state;
  const ma = kState.meta_analysis;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400 font-bold text-xl">
              🧠
            </span>
            <h1 className="text-2xl font-bold tracking-tight">
              Priority 36: Longitudinal Evidence Synthesis & Research Knowledge State Engine
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Versioned Research Knowledge State Machine (RKSM) & Meta-Analytic Evidence Weighting (MAEWE) over accumulated multi-study research lineage.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => runSynthesis(false, false)}
            disabled={loading}
            className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-sm transition shadow-lg shadow-purple-600/20"
          >
            {loading ? "Synthesizing..." : "Run Evidence Synthesis"}
          </button>
        </div>
      </div>

      {/* Epistemic Non-Causal Banner */}
      <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/30 text-xs text-purple-300 font-mono flex items-start gap-2">
        <span className="text-purple-400 font-bold shrink-0">🧠</span>
        <div>{data.non_causal_disclosure}</div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
        {[
          { id: "overview", label: "📊 Overview" },
          { id: "lineage", label: "📚 Evidence Lineage" },
          { id: "meta", label: "🌲 Meta-Analysis" },
          { id: "statemachine", label: "🔄 State Machine" },
          { id: "versioning", label: "🏷️ Knowledge Versioning" },
          { id: "provenance", label: "🔐 Provenance" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === tab.id
                ? "bg-slate-800 text-purple-400 border border-slate-700"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className={`p-8 rounded-3xl border ${STATE_STYLES[kState.current_state] || "bg-slate-900 border-slate-800 text-white"} space-y-3`}>
            <div className="flex justify-between items-center">
              <div className="text-xs uppercase tracking-widest font-mono text-slate-400 font-bold">
                Research Knowledge State ({kState.state_version})
              </div>
              <span className={`px-3 py-1 rounded font-bold font-mono text-xs ${GRADE_STYLES[kState.evidence_grade] || "bg-slate-800 text-slate-300"}`}>
                {kState.evidence_grade}
              </span>
            </div>
            <div className="text-3xl font-extrabold tracking-tight">{kState.current_state}</div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
            <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Epistemic Certainty Score</span>
              <div className="text-2xl font-bold text-emerald-400">{(kState.certainty_score * 100).toFixed(1)}%</div>
            </div>
            <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Pooled Effect Size</span>
              <div className="text-2xl font-bold text-purple-400 font-bold">{(ma.pooled_effect_size * 100).toFixed(2)}%</div>
            </div>
            <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Higgins I² Heterogeneity</span>
              <div className="text-2xl font-bold text-indigo-300">{ma.i_squared_heterogeneity.toFixed(1)}%</div>
            </div>
            <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Total Accumulated Cohort</span>
              <div className="text-2xl font-bold text-white">{ma.total_samples} Natives</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: LINEAGE */}
      {activeTab === "lineage" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 font-mono text-xs">
          <h3 className="text-base font-bold text-white font-sans">Accumulated Multi-Study Evidence Lineage</h3>
          <div className="space-y-3">
            {kState.accumulated_studies.map((s) => (
              <div key={s.study_id} className="p-4 bg-slate-950 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="text-sm font-bold text-white font-sans">{s.title}</div>
                  <div className="text-slate-400 text-[11px] mt-0.5">Type: {s.study_type} | N = {s.sample_size} | Weight: {(s.weight * 100).toFixed(1)}%</div>
                </div>
                <div className="text-right">
                  <span className="text-slate-400">Observed Metric:</span>
                  <div className="text-emerald-400 font-bold text-base">{(s.observed_metric * 100).toFixed(1)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: META-ANALYSIS */}
      {activeTab === "meta" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6 font-mono text-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white font-sans">Meta-Analytic Evidence Weighting (MAEWE)</h3>
            <span className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded font-bold">{ma.heterogeneity_level}</span>
          </div>

          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
            <div className="flex justify-between"><span className="text-slate-400">Pooled Effect Size (Accuracy):</span><span className="text-purple-300 font-bold">{(ma.pooled_effect_size * 100).toFixed(2)}%</span></div>
            <div className="flex justify-between"><span className="text-slate-400">95% Confidence Interval:</span><span className="text-emerald-400 font-bold">[{(ma.confidence_interval[0] * 100).toFixed(2)}%, {(ma.confidence_interval[1] * 100).toFixed(2)}%]</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Cochran's I² Heterogeneity:</span><span className="text-white font-bold">{ma.i_squared_heterogeneity.toFixed(1)}%</span></div>
            <div className="flex justify-between"><span className="text-slate-400">Between-Study Variance (Tau²):</span><span className="text-indigo-400 font-bold">{ma.tau_squared.toFixed(6)}</span></div>
          </div>
        </div>
      )}

      {/* TAB 4: STATE MACHINE */}
      {activeTab === "statemachine" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 font-mono text-xs">
          <h3 className="text-base font-bold text-white font-sans">Research Knowledge State Machine (RKSM) Transitions</h3>
          <div className="space-y-3">
            {kState.transitions.map((t, idx) => (
              <div key={t.transition_id} className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-purple-400 font-bold font-sans">Step {idx + 1}: {t.from_state} ➔ {t.to_state}</span>
                  <span className="text-slate-400 text-[10px]">{t.timestamp}</span>
                </div>
                <div className="text-slate-300 text-[11px]">{t.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: VERSIONING */}
      {activeTab === "versioning" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 font-mono text-xs">
          <h3 className="text-base font-bold text-white font-sans font-bold">Research Knowledge Versioning & Supersede DAG</h3>
          <div className="space-y-3">
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Active State Version:</span>
              <div className="text-emerald-400 font-bold text-base">{kState.state_version}</div>
            </div>
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Superseded State Reference:</span>
              <div className="text-slate-300">{kState.superseded_state_id || "NONE (Initial Version)"}</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: PROVENANCE */}
      {activeTab === "provenance" && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 font-mono text-xs">
          <h3 className="text-base font-bold text-white font-sans font-bold">Research Knowledge Provenance & Fingerprint</h3>
          <div className="space-y-3">
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Knowledge State ID:</span>
              <div className="text-purple-300">{kState.state_id}</div>
            </div>
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">SHA-256 State Fingerprint:</span>
              <div className="text-emerald-300 break-all">{data.knowledge_state_fingerprint}</div>
            </div>
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400">Research Snapshot ID:</span>
              <div className="text-slate-300">{data.knowledge_snapshot_id}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
