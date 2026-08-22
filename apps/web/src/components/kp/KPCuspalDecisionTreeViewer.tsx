"use client";

import { useState, useEffect } from "react";
import {
  evaluateKPCuspalDecisionTree,
  type KPCuspalDecisionTreeResponse,
  type KPCuspalSubLordDecisionNode,
  type KPEventDecisionTreeResult,
} from "@/lib/kpSbcAnalysis";

interface Props {
  chartData?: Record<string, unknown>;
}

const SAMPLE_DEFAULT_CHART = {
  planets: [
    { planet: "Jupiter", house_number: 1, rashi: "Cancer", sidereal_longitude: 104.5, star_lord: "Saturn" },
    { planet: "Moon", house_number: 4, rashi: "Libra", sidereal_longitude: 195.2, star_lord: "Rahu" },
    { planet: "Sun", house_number: 10, rashi: "Aries", sidereal_longitude: 15.8, star_lord: "Venus" },
    { planet: "Mercury", house_number: 10, rashi: "Aries", sidereal_longitude: 22.4, star_lord: "Venus" },
    { planet: "Mars", house_number: 10, rashi: "Capricorn", sidereal_longitude: 284.1, star_lord: "Mars" },
    { planet: "Venus", house_number: 11, rashi: "Taurus", sidereal_longitude: 48.0, star_lord: "Sun" },
    { planet: "Saturn", house_number: 7, rashi: "Capricorn", sidereal_longitude: 278.3, star_lord: "Mars" },
    { planet: "Rahu", house_number: 6, rashi: "Sagittarius", sidereal_longitude: 254.0, star_lord: "Venus" },
    { planet: "Ketu", house_number: 12, rashi: "Gemini", sidereal_longitude: 74.0, star_lord: "Rahu" },
  ],
  houses: [
    { house_number: 1, longitude: 95.0, rashi: "Cancer", sign_lord: "Moon", star_lord: "Saturn", sub_lord: "Jupiter" },
    { house_number: 2, longitude: 125.0, rashi: "Leo", sign_lord: "Sun", star_lord: "Ketu", sub_lord: "Venus" },
    { house_number: 3, longitude: 155.0, rashi: "Virgo", sign_lord: "Mercury", star_lord: "Sun", sub_lord: "Rahu" },
    { house_number: 4, longitude: 185.0, rashi: "Libra", sign_lord: "Venus", star_lord: "Mars", sub_lord: "Saturn" },
    { house_number: 5, longitude: 215.0, rashi: "Scorpio", sign_lord: "Mars", star_lord: "Jupiter", sub_lord: "Mercury" },
    { house_number: 6, longitude: 245.0, rashi: "Sagittarius", sign_lord: "Jupiter", star_lord: "Ketu", sub_lord: "Venus" },
    { house_number: 7, longitude: 275.0, rashi: "Capricorn", sign_lord: "Saturn", star_lord: "Mars", sub_lord: "Jupiter" },
    { house_number: 8, longitude: 305.0, rashi: "Aquarius", sign_lord: "Saturn", star_lord: "Rahu", sub_lord: "Moon" },
    { house_number: 9, longitude: 335.0, rashi: "Pisces", sign_lord: "Jupiter", star_lord: "Saturn", sub_lord: "Sun" },
    { house_number: 10, longitude: 5.0, rashi: "Aries", sign_lord: "Mars", star_lord: "Ketu", sub_lord: "Sun" },
    { house_number: 11, longitude: 35.0, rashi: "Taurus", sign_lord: "Venus", star_lord: "Sun", sub_lord: "Mars" },
    { house_number: 12, longitude: 65.0, rashi: "Gemini", sign_lord: "Mercury", star_lord: "Mars", sub_lord: "Rahu" },
  ],
};

export function KPCuspalDecisionTreeViewer({ chartData }: Props) {
  const [data, setData] = useState<KPCuspalDecisionTreeResponse | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<string>("Career");
  const [selectedCusp, setSelectedCusp] = useState<number>(10);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTree() {
      try {
        setLoading(true);
        setError(null);
        const activeChart = chartData || SAMPLE_DEFAULT_CHART;
        const res = await evaluateKPCuspalDecisionTree(activeChart, {
          event_domain: selectedDomain,
        });
        setData(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to compute KP decision tree.");
      } finally {
        setLoading(false);
      }
    }
    loadTree();
  }, [chartData, selectedDomain]);

  const activeEvent = data?.event_decision_trees.find((e) => e.event_domain.toLowerCase() === selectedDomain.toLowerCase()) || data?.event_decision_trees[0];
  const activeNode = data?.cuspal_decision_nodes.find((n) => n.house_number === selectedCusp) || data?.cuspal_decision_nodes[0];

  return (
    <div className="space-y-6" data-testid="kp-cuspal-decision-tree-viewer">
      {/* 1. Header & Domain Filter */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4" style={{ borderColor: "var(--border-subtle)" }}>
        <div>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            KRISHNAMURTI PADDHATI (KP) ANALYSIS
          </span>
          <h2 className="text-xl font-bold text-zinc-100 mt-1 flex items-center gap-2">
            <span>🌳</span> Cuspal Sub-Lord Decision Tree &amp; 4-Tier Significators
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Deterministic Cusp → Sub-Lord → Star-Lord calculation chain with 12th-from-bhava negation veto detection.
          </p>
        </div>

        {/* Event Domain Tabs */}
        <div className="flex flex-wrap gap-1.5 bg-zinc-900/80 p-1 rounded-xl border border-zinc-800">
          {["Career", "Marriage", "Finance", "Health", "All"].map((d) => (
            <button
              key={d}
              onClick={() => {
                setSelectedDomain(d);
                if (d === "Career") setSelectedCusp(10);
                if (d === "Marriage") setSelectedCusp(7);
                if (d === "Finance") setSelectedCusp(2);
                if (d === "Health") setSelectedCusp(6);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                selectedDomain === d
                  ? "bg-cyan-500 text-zinc-950 shadow"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-zinc-400">Computing KP 4-Tier Matrix &amp; Decision Trees…</div>
      ) : error ? (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-300">{error}</div>
      ) : data ? (
        <div className="space-y-6">
          {/* 2. Event-Specific Fructification Banner */}
          {activeEvent && (
            <div className="p-4 rounded-2xl bg-zinc-900/70 border border-zinc-800 glass-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="font-semibold text-zinc-300">Target Event:</span>
                  <span className="font-bold text-cyan-400">{activeEvent.event_domain}</span>
                  <span className="text-zinc-400">• Primary Cusp {activeEvent.primary_cusp}</span>
                </div>
                <div className="text-sm font-semibold text-zinc-100 mt-1">{activeEvent.summary_verdict}</div>
                <div className="text-xs text-zinc-400 mt-0.5">
                  Supporting Houses: [{activeEvent.supporting_cusps.join(", ")}] | Negation Veto Houses: [{activeEvent.negating_cusps.join(", ")}]
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider ${
                    activeEvent.fructification_verdict === "PROMISED_FRUCTIFY"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      : activeEvent.fructification_verdict === "VETOED_NEGATED"
                      ? "bg-red-500/20 text-red-300 border border-red-500/30"
                      : activeEvent.fructification_verdict === "DELAYED_MODERATE"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : "bg-zinc-800 text-zinc-400"
                  }`}
                >
                  {activeEvent.fructification_verdict.replace(/_/g, " ")}
                </span>
              </div>
            </div>
          )}

          {/* 3. Main Split: 4-Tier Matrix & CSL Decision Tree Flow */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: 4-Tier Significators Matrix */}
            <div className="lg:col-span-5 space-y-3">
              <div className="flex items-center justify-between text-xs text-zinc-400">
                <span className="font-semibold uppercase tracking-wider">KP 4-Tier Significator Matrix</span>
                <span>12 Houses</span>
              </div>

              <div className="border rounded-xl overflow-hidden border-zinc-800 max-h-[580px] overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900/90 text-zinc-400 border-b border-zinc-800 text-[10px] uppercase">
                    <tr>
                      <th className="p-2.5">House</th>
                      <th className="p-2.5">Tier A (Star-Occ)</th>
                      <th className="p-2.5">Tier B (Occupant)</th>
                      <th className="p-2.5">Tier C (Star-Lord)</th>
                      <th className="p-2.5">Tier D (Sign Lord)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                    {data.four_tier_significator_matrix.map((t) => {
                      const isHighlighted = t.house_number === selectedCusp;
                      return (
                        <tr
                          key={t.house_number}
                          onClick={() => setSelectedCusp(t.house_number)}
                          className={`cursor-pointer transition ${
                            isHighlighted ? "bg-cyan-950/40 font-semibold text-cyan-200" : "hover:bg-zinc-900/40"
                          }`}
                        >
                          <td className="p-2.5 font-mono text-cyan-400">H{t.house_number}</td>
                          <td className="p-2.5 text-zinc-300 font-mono text-[11px]">{t.tier_a_planets.join(", ") || "-"}</td>
                          <td className="p-2.5 text-zinc-300 font-mono text-[11px]">{t.tier_b_planets.join(", ") || "-"}</td>
                          <td className="p-2.5 text-zinc-300 font-mono text-[11px]">{t.tier_c_planets.join(", ") || "-"}</td>
                          <td className="p-2.5 text-zinc-400 font-mono text-[11px]">{t.tier_d_planets.join(", ") || "-"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right: Cuspal Sub-Lord Decision Node Visualizer */}
            <div className="lg:col-span-7 space-y-4">
              {activeNode && (
                <div className="p-5 rounded-2xl border glass-card border-zinc-800 space-y-5">
                  {/* Decision Tree Header */}
                  <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                    <div>
                      <span className="text-xs font-mono text-cyan-400 font-bold">CUSP {activeNode.house_number} DECISION TREE</span>
                      <h2 className="text-lg font-bold text-zinc-100 mt-0.5">
                        House {activeNode.house_number} ({activeNode.cusp_rashi} at {activeNode.cusp_degree.toFixed(2)}°)
                      </h2>
                    </div>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                        activeNode.verdict === "PROMISED_FRUCTIFY"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : activeNode.verdict === "VETOED_NEGATED"
                          ? "bg-red-500/20 text-red-300 border border-red-500/30"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {activeNode.verdict.replace(/_/g, " ")}
                    </span>
                  </div>

                  {/* Flow Diagram Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 space-y-1">
                      <div className="text-[10px] uppercase tracking-wider text-zinc-400">Sign &amp; Star Lord</div>
                      <div className="text-xs font-bold text-zinc-200">{activeNode.sign_lord} / {activeNode.star_lord}</div>
                      <div className="text-[10px] text-zinc-400">Rashi Base Layer</div>
                    </div>

                    <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/30 space-y-1">
                      <div className="text-[10px] uppercase tracking-wider text-cyan-400 font-semibold">Cuspal Sub-Lord</div>
                      <div className="text-sm font-bold text-cyan-200">{activeNode.sub_lord}</div>
                      <div className="text-[10px] text-cyan-300/80">Star Lord: {activeNode.sub_lord_star_lord}</div>
                    </div>

                    <div className="p-3 rounded-xl bg-zinc-900/80 border border-zinc-800 space-y-1">
                      <div className="text-[10px] uppercase tracking-wider text-zinc-400">Sub-Sub Lord</div>
                      <div className="text-xs font-bold text-zinc-200">{activeNode.sub_sub_lord}</div>
                      <div className="text-[10px] text-zinc-400">Micro-Trigger</div>
                    </div>
                  </div>

                  {/* Signified Houses & Veto Detection */}
                  <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 space-y-3">
                    <div className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                      Houses Signified by Sub-Lord {activeNode.sub_lord}
                    </div>

                    <div className="flex flex-wrap gap-2 text-xs">
                      {activeNode.primary_houses_signified.map((h) => (
                        <span key={h} className="px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                          Primary House {h} (Anchored)
                        </span>
                      ))}
                      {activeNode.supporting_houses_signified.map((h) => (
                        <span key={h} className="px-2.5 py-1 rounded-lg bg-cyan-500/15 text-cyan-300 font-semibold border border-cyan-500/25">
                          Supporting House {h}
                        </span>
                      ))}
                      {activeNode.negating_houses_signified.map((h) => (
                        <span key={h} className="px-2.5 py-1 rounded-lg bg-red-500/20 text-red-300 font-bold border border-red-500/30">
                          ⚠️ Negating House {h} (12th-Veto)
                        </span>
                      ))}
                    </div>

                    <div className="text-xs text-zinc-300 leading-relaxed border-t border-zinc-800/80 pt-2 font-medium">
                      {activeNode.verdict_explanation}
                    </div>
                  </div>

                  {/* Step-by-Step Mathematical Audit Chain */}
                  <div className="space-y-2">
                    <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                      Technical Audit Trace
                    </div>
                    <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80 space-y-1.5 font-mono text-[11px] text-zinc-300">
                      {activeNode.audit_chain.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-2">
                          <span className="text-cyan-400 font-bold">›</span>
                          <span>{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
