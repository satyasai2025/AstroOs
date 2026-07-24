/**
 * AstroOS — System Health Panel
 *
 * Live health monitoring for all backend modules.
 */

"use client";

import { useEffect, useState } from "react";

interface ModuleHealth {
  name: string;
  status: "healthy" | "degraded" | "down";
  version: string;
  message: string;
  lastChecked: string;
}

const MOCK_MODULES: ModuleHealth[] = [
  { name: "Swiss Ephemeris Engine", status: "healthy", version: "2.3.0", message: "Operational", lastChecked: "Just now" },
  { name: "Yoga Evaluator", status: "healthy", version: "1.5.0", message: "Operational", lastChecked: "Just now" },
  { name: "BPHS Rules Engine", status: "healthy", version: "1.2.0", message: "Operational", lastChecked: "Just now" },
  { name: "Reverse Pattern Search", status: "degraded", version: "1.0.0", message: "Limited capacity", lastChecked: "Just now" },
  { name: "Workflow Orchestrator", status: "healthy", version: "2.0.0", message: "Operational", lastChecked: "Just now" },
  { name: "AI Insights Engine", status: "down", version: "0.9.0", message: "Service unavailable", lastChecked: "Just now" },
];

function StatusBadge({ status }: { status: string }) {
  const colors = {
    healthy: "bg-emerald-400",
    degraded: "bg-amber-400",
    down: "bg-red-400",
  };
  const labels = {
    healthy: "Healthy",
    degraded: "Degraded",
    down: "Down",
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full ${
      status === "healthy" ? "bg-emerald-400/15 text-emerald-300" :
      status === "degraded" ? "bg-amber-400/15 text-amber-300" :
      "bg-red-400/15 text-red-300"
    }`}>
      <span className={`h-1.5 w-1.5 rounded-full ${colors[status as keyof typeof colors]}`} />
      {labels[status as keyof typeof labels] || status}
    </span>
  );
}

export function SystemHealthPanel() {
  const [modules, setModules] = useState(MOCK_MODULES);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setModules((prev) =>
        prev.map((m) => ({
          ...m,
          lastChecked: "Just now",
          // Simulate occasional status changes
          status: Math.random() < 0.05 && m.status === "healthy" ? "degraded" : m.status,
        }))
      );
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border-primary)] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-primary)]">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">System Health</h3>
          <p className="text-xs text-[var(--text-muted)]">Backend module status</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh (30s)
          </label>
          <button
            onClick={() => setModules((prev) => prev.map((m) => ({ ...m, lastChecked: "Just now" })))}
            className="text-xs text-[var(--accent)] hover:underline"
          >
            Refresh now
          </button>
        </div>
      </div>

      <div className="divide-y divide-[var(--border-primary)]">
        {modules.map((module) => (
          <div key={module.name} className="flex items-center justify-between px-4 py-3 hover:bg-[var(--bg-card-hover)] transition-colors">
            <div className="flex items-center gap-3">
              <StatusBadge status={module.status} />
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">{module.name}</p>
                <p className="text-xs text-[var(--text-muted)]">{module.message}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-[var(--text-muted)]">v{module.version}</p>
              <p className="text-xs text-[var(--text-muted)]">{module.lastChecked}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
