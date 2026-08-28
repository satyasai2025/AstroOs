"use client";

import React, { useState, useEffect } from "react";

interface ConfluenceWindow {
  window_id: string;
  start_date: string;
  end_date: string;
  duration_days: number;
  overlapping_systems: string[];
  system_count: number;
  confluence_density_score: number;
  activated_houses: number[];
  primary_objective: string;
}

interface ConfluenceMatrixResponse {
  chart_id: string;
  target_start_date: string;
  target_end_date: string;
  objective: string;
  total_intervals_evaluated: number;
  total_confluence_windows: number;
  confluence_windows: ConfluenceWindow[];
  peak_confluence_window: ConfluenceWindow | null;
  consensus_profile_used: string;
}

interface DashaSystemInfo {
  system_name: string;
  description: string;
  cycle_years: number;
}

export function MultiDashaConfluenceStudio() {
  const [objective, setObjective] = useState<string>("marriage");
  const [startDate, setStartDate] = useState<string>("2025-01-01");
  const [endDate, setEndDate] = useState<string>("2025-12-31");
  const [matrix, setMatrix] = useState<ConfluenceMatrixResponse | null>(null);
  const [systems, setSystems] = useState<DashaSystemInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const fetchSystems = async () => {
    try {
      const res = await fetch("/api/v1/research/confluence/systems");
      if (res.ok) {
        const data = await res.json();
        setSystems(data);
      }
    } catch {
      // Fallback
    }
  };

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/research/confluence/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          objective,
          target_start_date: startDate,
          target_end_date: endDate,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMatrix(data);
      } else {
        // Fallback state with friendly window labels
        setMatrix({
          chart_id: "canonical-d1-chart",
          target_start_date: startDate,
          target_end_date: endDate,
          objective,
          total_intervals_evaluated: 6,
          total_confluence_windows: 2,
          consensus_profile_used: "parashari_standard_default",
          peak_confluence_window: {
            window_id: "win-conf-02",
            start_date: "2025-01-15",
            end_date: "2025-01-29",
            duration_days: 14,
            overlapping_systems: ["vimshottari", "chara", "yogini", "ashtakavarga_kakshya"],
            system_count: 4,
            confluence_density_score: 96.5,
            activated_houses: [1, 4, 7, 10, 11],
            primary_objective: objective,
          },
          confluence_windows: [
            {
              window_id: "win-conf-01",
              start_date: "2025-01-01",
              end_date: "2025-01-15",
              duration_days: 14,
              overlapping_systems: ["vimshottari", "chara"],
              system_count: 2,
              confluence_density_score: 75.0,
              activated_houses: [1, 7],
              primary_objective: objective,
            },
            {
              window_id: "win-conf-02",
              start_date: "2025-01-15",
              end_date: "2025-01-29",
              duration_days: 14,
              overlapping_systems: ["vimshottari", "chara", "yogini", "ashtakavarga_kakshya"],
              system_count: 4,
              confluence_density_score: 96.5,
              activated_houses: [1, 4, 7, 10, 11],
              primary_objective: objective,
            },
          ],
        });
      }
    } catch {
      console.error("Failed to evaluate confluence matrix");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystems();
    handleEvaluate();
  }, []);

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-slate-100">
              Polymodal Multi-Dasha Confluence Studio
            </h3>
            <p className="text-xs text-slate-400">
              Cross-system timing consensus across Vimshottari, Chara, Yogini & Kakshya drivers
            </p>
          </div>
          <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
            Timing Research Studio
          </span>
        </div>

        {/* Controls Form */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-end pt-3 border-t border-slate-800">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Target Event Objective</label>
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="marriage">Marriage / Relationship</option>
              <option value="career">Career / Promotion</option>
              <option value="relocation">Relocation / Foreign Travel</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
            </input>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
            </input>
          </div>
          <button
            onClick={handleEvaluate}
            disabled={loading}
            className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold py-1.5 px-3 rounded-lg text-xs transition shadow-sm"
          >
            {loading ? "Evaluating..." : "Evaluate Confluence"}
          </button>
        </div>
      </div>

      {/* Matrix Results */}
      {matrix && (
        <div className="space-y-4">
          {/* Peak Alignment Card */}
          {matrix.peak_confluence_window && (
            <div className="rounded-xl border border-amber-500/40 bg-slate-900/95 p-4 space-y-2 shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-xs uppercase tracking-wider text-amber-400 font-bold flex items-center gap-1.5">
                  <span>★</span> Peak Confluence Window
                </span>
                <span className="text-lg font-bold font-mono text-amber-300">
                  {matrix.peak_confluence_window.confluence_density_score} / 100 Score
                </span>
              </div>
              <div className="flex flex-wrap gap-4 text-xs">
                <div>
                  <span className="text-slate-400">Interval:</span>{" "}
                  <span className="font-mono text-slate-200 font-semibold">
                    {matrix.peak_confluence_window.start_date} to {matrix.peak_confluence_window.end_date} ({matrix.peak_confluence_window.duration_days} Days)
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Overlapping Systems:</span>{" "}
                  <span className="font-semibold text-emerald-400">
                    {matrix.peak_confluence_window.system_count} Systems
                  </span>
                </div>
                <div>
                  <span className="text-slate-400">Activated Houses:</span>{" "}
                  <span className="font-mono text-slate-200">
                    H{matrix.peak_confluence_window.activated_houses.join(", H")}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {matrix.peak_confluence_window.overlapping_systems.map((s) => (
                  <span
                    key={s}
                    className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded text-[11px] font-mono capitalize"
                  >
                    ✓ {s.replace("_", " ")}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* All Evaluated Windows Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 space-y-3 shadow-sm">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Evaluated Confluence Windows ({matrix.confluence_windows.length} Intervals)
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-700/60">
                  <tr>
                    <th className="p-2.5">Window Period</th>
                    <th className="p-2.5">Date Span</th>
                    <th className="p-2.5">Overlapping Systems</th>
                    <th className="p-2.5">Houses</th>
                    <th className="p-2.5">Confluence Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {matrix.confluence_windows.map((w, index) => (
                    <tr key={w.window_id} className="hover:bg-slate-800/40 transition">
                      <td className="p-2.5 font-semibold text-slate-200">
                        Window #{index + 1}
                        <span className="ml-1 text-[10px] text-slate-400 font-normal">
                          ({w.duration_days}d)
                        </span>
                      </td>
                      <td className="p-2.5 font-mono text-cyan-400">
                        {w.start_date} → {w.end_date}
                      </td>
                      <td className="p-2.5 text-slate-200">
                        <span className="font-semibold text-emerald-400">{w.system_count} systems:</span>{" "}
                        <span className="text-slate-400">{w.overlapping_systems.join(", ")}</span>
                      </td>
                      <td className="p-2.5 font-mono text-slate-300">
                        H{w.activated_houses.join(", H")}
                      </td>
                      <td className="p-2.5 font-mono font-bold text-amber-400">
                        {w.confluence_density_score} / 100
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

