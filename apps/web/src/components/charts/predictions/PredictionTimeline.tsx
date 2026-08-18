"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { WorkflowAnalysisResponse } from "@/lib/types";

interface PredictionWindowSchema {
  event_type: string;
  start_date: string;
  end_date: string;
  peak_date: string;
  peak_score: number;
  promise_status: "established" | "weak" | "absent";
  primary_drivers: string[];
  supporting_factors: string[];
  opposing_factors: string[];
  evidence_trace: string[];
  resolution_level: string;
  deterministic_hash: string;
}

interface PredictionOrchestrateResponse {
  event_type: string;
  target_start_date: string;
  target_end_date: string;
  consensus_profile_used: string;
  candidate_windows: PredictionWindowSchema[];
  total_slices_evaluated: number;
  macro_slices_count: number;
  refined_slices_count: number;
  deterministic_signature: string;
  summary: string;
}

export function PredictionTimeline({
  workflowResult,
}: {
  workflowResult?: WorkflowAnalysisResponse | null;
}) {
  const [objective, setObjective] = useState<string>("career");
  const [startDate, setStartDate] = useState<string>("2026-01-01");
  const [endDate, setEndDate] = useState<string>("2029-12-31");
  const [profileId, setProfileId] = useState<string>("parashari_standard_v1");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PredictionOrchestrateResponse | null>(null);
  const [expandedWindowHash, setExpandedWindowHash] = useState<string | null>(null);

  const handleSynthesize = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        objective,
        target_start_date: startDate,
        target_end_date: endDate,
        profile_id: profileId,
        enable_micro_zoom: true,
        birth_datetime_utc: "1990-01-01T12:00:00Z",
        latitude: 28.6139,
        longitude: 77.2090,
      };

      const res = await api.post<PredictionOrchestrateResponse>(
        "/api/v1/predictions/orchestrate",
        payload
      );
      setData(res);
      if (res.candidate_windows.length > 0) {
        setExpandedWindowHash(res.candidate_windows[0].deterministic_hash);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to synthesize timeline";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration Header */}
      <div
        className="glass-card p-5"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-primary)",
          borderRadius: "0.75rem",
        }}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
              Prediction Intelligence & Event Orchestrator
            </h3>
            <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
              Multi-scale adaptive timeline scanner combining Natal Promise, Dasha Activation, and Gochara Heuristics.
            </p>
          </div>

          <button
            onClick={handleSynthesize}
            disabled={loading}
            className="px-4 py-2 text-xs font-semibold rounded transition"
            style={{
              background: loading ? "var(--bg-muted)" : "var(--primary-color, #3b82f6)",
              color: "#fff",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Synthesizing Timeline..." : "Synthesize Event Timeline"}
          </button>
        </div>

        {/* Controls Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 pt-4" style={{ borderTop: "1px solid var(--border-subtle, #333)" }}>
          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Target Life Domain
            </label>
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full text-xs p-2 rounded bg-black/20"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
            >
              <option value="career">Career Elevation & Status</option>
              <option value="marriage_timing">Matrimonial Timing Window</option>
              <option value="wealth">Wealth & Dhana Accumulation</option>
              <option value="event_timing">Saturn Karmic Cycles (Sade Sati / Ashtama)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full text-xs p-2 rounded bg-black/20"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full text-xs p-2 rounded bg-black/20"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              Consensus Profile
            </label>
            <select
              value={profileId}
              onChange={(e) => setProfileId(e.target.value)}
              className="w-full text-xs p-2 rounded bg-black/20"
              style={{ border: "1px solid var(--border-primary)", color: "var(--text-primary)" }}
            >
              <option value="parashari_standard_v1">Parashari Classical Standard (40/35/25)</option>
              <option value="empirical_research_v1">Modern Empirical Research (K.N. Rao 35/35/30)</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded text-xs bg-red-900/20 text-red-400 border border-red-800">
          {error}
        </div>
      )}

      {/* Synthesis Metadata & Summary */}
      {data && (
        <div
          className="p-4 rounded flex flex-wrap items-center justify-between gap-4"
          style={{ background: "var(--bg-card-hover, rgba(255,255,255,0.03))", border: "1px solid var(--border-primary)" }}
        >
          <div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-900/40 text-blue-300 mr-2">
              Profile: {data.consensus_profile_used}
            </span>
            <span className="text-xs font-mono text-zinc-400">
              Signature: {data.deterministic_signature}
            </span>
            <p className="text-xs mt-1 text-zinc-300">{data.summary}</p>
          </div>

          <div className="text-right text-xs text-zinc-400">
            <div>Total Slices Evaluated: <span className="text-zinc-200 font-semibold">{data.total_slices_evaluated}</span></div>
            <div>Macro Slices: {data.macro_slices_count} | Refined Slices: {data.refined_slices_count}</div>
          </div>
        </div>
      )}

      {/* Candidate Windows Timeline */}
      {data && (
        <div className="space-y-4">
          <h4 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
            Ranked Prediction Windows ({data.candidate_windows.length})
          </h4>

          {data.candidate_windows.length === 0 ? (
            <div className="p-8 text-center text-xs text-zinc-500 glass-card">
              No continuous candidate windows crossed the activation threshold for this life domain in the selected range.
            </div>
          ) : (
            data.candidate_windows.map((win, idx) => {
              const isExpanded = expandedWindowHash === win.deterministic_hash;
              return (
                <div
                  key={win.deterministic_hash}
                  className="p-5 rounded-lg transition"
                  style={{
                    background: "var(--bg-card)",
                    border: `1px solid ${isExpanded ? "var(--primary-color, #3b82f6)" : "var(--border-primary)"}`,
                  }}
                >
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm"
                        style={{
                          background: win.peak_score >= 80 ? "rgba(16, 185, 129, 0.2)" : "rgba(59, 130, 246, 0.2)",
                          color: win.peak_score >= 80 ? "#10b981" : "#3b82f6",
                          border: `1px solid ${win.peak_score >= 80 ? "#10b981" : "#3b82f6"}`,
                        }}
                      >
                        {win.peak_score}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm text-zinc-100">
                            Window #{idx + 1}: {win.start_date} → {win.end_date}
                          </span>
                          <span
                            className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded"
                            style={{
                              background: win.promise_status === "established" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                              color: win.promise_status === "established" ? "#10b981" : "#ef4444",
                            }}
                          >
                            Promise: {win.promise_status}
                          </span>
                        </div>
                        <p className="text-xs text-zinc-400 mt-0.5">
                          Peak Alignment Date: <span className="text-zinc-200 font-semibold">{win.peak_date}</span> | Resolution: {win.resolution_level}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() => setExpandedWindowHash(isExpanded ? null : win.deterministic_hash)}
                      className="text-xs px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition"
                    >
                      {isExpanded ? "Hide Evidence" : "Drill-Down Evidence"}
                    </button>
                  </div>

                  {/* Evidence Drill-Down Panel */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 space-y-3" style={{ borderTop: "1px solid var(--border-subtle, #333)" }}>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div className="p-3 rounded bg-black/30 border border-zinc-800">
                          <h5 className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider mb-1.5">
                            Primary Drivers ({win.primary_drivers.length})
                          </h5>
                          <ul className="text-xs space-y-1 text-zinc-300">
                            {win.primary_drivers.map((d, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-emerald-500">✓</span> {d}
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="p-3 rounded bg-black/30 border border-zinc-800">
                          <h5 className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider mb-1.5">
                            Supporting Modifiers ({win.supporting_factors.length})
                          </h5>
                          <ul className="text-xs space-y-1 text-zinc-300">
                            {win.supporting_factors.length === 0 ? (
                              <li className="text-zinc-500 text-[11px]">None</li>
                            ) : (
                              win.supporting_factors.map((s, i) => (
                                <li key={i} className="flex items-start gap-1">
                                  <span className="text-blue-400">+</span> {s}
                                </li>
                              ))
                            )}
                          </ul>
                        </div>

                        <div className="p-3 rounded bg-black/30 border border-zinc-800">
                          <h5 className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider mb-1.5">
                            Opposing Factors / Penalties ({win.opposing_factors.length})
                          </h5>
                          <ul className="text-xs space-y-1 text-zinc-300">
                            {win.opposing_factors.length === 0 ? (
                              <li className="text-zinc-500 text-[11px]">Zero opposing penalties</li>
                            ) : (
                              win.opposing_factors.map((o, i) => (
                                <li key={i} className="flex items-start gap-1 text-amber-300">
                                  <span>⚠</span> {o}
                                </li>
                              ))
                            )}
                          </ul>
                        </div>
                      </div>

                      {/* Granular Sastric Evidence Trace */}
                      <div className="p-3 rounded bg-black/40 border border-zinc-800">
                        <h5 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
                          Granular Sastric Evidence Trace
                        </h5>
                        <ul className="text-xs space-y-1 text-zinc-300 font-mono text-[11px]">
                          {win.evidence_trace.map((ev, i) => (
                            <li key={i} className="text-zinc-400">
                              • {ev}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}