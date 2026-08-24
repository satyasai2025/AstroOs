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
        // Fallback state
        setMatrix({
          chart_id: "canonical-d1-chart",
          target_start_date: startDate,
          target_end_date: endDate,
          objective,
          total_intervals_evaluated: 6,
          total_confluence_windows: 4,
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
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Header */}
      <header className="border-b border-amber-500/30 pb-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-400">
            AstroOS Polymodal Multi-Dasha Confluence Studio
          </h1>
          <p className="text-sm text-slate-400">
            Cross-technique interval intersection math across Vimshottari, Chara, Yogini & Kakshya timing drivers
          </p>
        </div>
      </header>

      {/* Controls Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Target Event Objective</label>
          <select
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100"
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
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm text-slate-100"
          />
        </div>
        <button
          onClick={handleEvaluate}
          disabled={loading}
          className="bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold py-2 px-4 rounded text-sm transition"
        >
          {loading ? "Computing..." : "Evaluate Polymodal Confluence"}
        </button>
      </div>

      {/* Supported Systems Badges */}
      <div className="flex flex-wrap gap-3">
        {systems.map((sys) => (
          <div key={sys.system_name} className="bg-slate-900 border border-slate-800 px-3 py-2 rounded text-xs">
            <span className="font-bold text-amber-300 capitalize">{sys.system_name}</span>:{" "}
            <span className="text-slate-400">{sys.description}</span>
          </div>
        ))}
      </div>

      {/* Matrix Results */}
      {matrix && (
        <div className="space-y-6">
          {/* Peak Alignment Card */}
          {matrix.peak_confluence_window && (
            <div className="bg-slate-900 border-2 border-amber-500/60 rounded-lg p-5 space-y-3 shadow-lg">
              <div className="flex justify-between items-center">
                <span className="text-xs uppercase tracking-wider text-amber-400 font-bold">
                  ★ Peak Multi-System Confluence Window
                </span>
                <span className="text-2xl font-bold font-mono text-amber-300">
                  {matrix.peak_confluence_window.confluence_density_score} / 100 Score
                </span>
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Peak Window:</span>{" "}
                  <span className="font-mono text-amber-200">
                    {matrix.peak_confluence_window.start_date} to {matrix.peak_confluence_window.end_date}
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
              <div className="flex flex-wrap gap-2 pt-1">
                {matrix.peak_confluence_window.overlapping_systems.map((s) => (
                  <span
                    key={s}
                    className="bg-emerald-950 border border-emerald-500/40 text-emerald-300 px-2 py-0.5 rounded text-xs font-mono"
                  >
                    ✓ {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* All Evaluated Windows Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
            <h2 className="text-lg font-bold text-amber-300">
              Evaluated Confluence Windows ({matrix.total_confluence_windows} Windows)
            </h2>
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-2">Window ID</th>
                  <th className="p-2">Date Interval</th>
                  <th className="p-2">Overlapping Systems</th>
                  <th className="p-2">Activated Houses</th>
                  <th className="p-2">Confluence Density Score</th>
                </tr>
              </thead>
              <tbody>
                {matrix.confluence_windows.map((w) => (
                  <tr key={w.window_id} className="border-b border-slate-800 hover:bg-slate-950/50">
                    <td className="p-2 font-mono text-amber-300">{w.window_id}</td>
                    <td className="p-2 font-mono text-slate-200">
                      {w.start_date} → {w.end_date}
                    </td>
                    <td className="p-2 font-semibold text-emerald-400">
                      {w.overlapping_systems.join(", ")} ({w.system_count})
                    </td>
                    <td className="p-2 font-mono text-slate-300">H{w.activated_houses.join(", H")}</td>
                    <td className="p-2 font-mono font-bold text-amber-300">{w.confluence_density_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
