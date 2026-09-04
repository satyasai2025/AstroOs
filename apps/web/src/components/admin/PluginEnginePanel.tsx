/**
 * AstroOS — Plugin Engine Panel
 *
 * Plugin management: enable/disable, health monitoring, API key rotation.
 */

"use client";

import { useState } from "react";

interface Plugin {
  id: string;
  name: string;
  displayName: string;
  version: string;
  status: "active" | "inactive" | "error";
  description: string;
  apiKey: string;
  lastHealthCheck: string;
}

const MOCK_PLUGINS: Plugin[] = [
  { id: "plugin-swiss-ephemeris", name: "swiss-ephemeris", displayName: "Swiss Ephemeris Engine", version: "2.3.0", status: "active", description: "Core planetary position calculator", apiKey: "ephe_skey123456789", lastHealthCheck: "2026-01-15T10:30:00Z" },
  { id: "plugin-yoga-evaluator", name: "yoga-evaluator", displayName: "Yoga Evaluator", version: "1.5.0", status: "active", description: "Evaluates planetary combinations (yogas)", apiKey: "yoga_key_987654321", lastHealthCheck: "2026-01-15T10:30:00Z" },
  { id: "plugin-bphs-rules", name: "bphs-rules", displayName: "BPHS Rules Engine", version: "1.2.0", status: "active", description: "BPHS-based interpretive rules", apiKey: "bphs_key_456789123", lastHealthCheck: "2026-01-15T10:30:00Z" },
  { id: "plugin-ai-insights", name: "ai-insights", displayName: "AI Insights Module", version: "0.9.0", status: "inactive", description: "Machine learning powered insights", apiKey: "ai_key_789123456", lastHealthCheck: "2026-01-15T09:00:00Z" },
];

function PluginStatusBadge({ status }: { status: string }) {
  const colors = {
    active: "text-emerald-400",
    inactive: "text-slate-400",
    error: "text-red-400",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-${status}/10 text-${status}`}>
      <span className={`h-1.5 w-1.5 rounded-full bg-current`} />
      {status === "active" ? "Active" : status === "inactive" ? "Inactive" : "Error"}
    </span>
  );
}

export function PluginEnginePanel() {
  const [plugins, setPlugins] = useState(MOCK_PLUGINS);
  const [rotatingKey, setRotatingKey] = useState<string | null>(null);

  const toggleStatus = (pluginId: string) => {
    setPlugins((prev) =>
      prev.map((p) => {
        if (p.id === pluginId) {
          const newStatus = p.status === "active" ? "inactive" : "active";
          return { ...p, status: newStatus as "active" | "inactive" };
        }
        return p;
      })
    );
  };

  const rotateKey = async (pluginId: string) => {
    setRotatingKey(pluginId);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setPlugins((prev) =>
      prev.map((p) =>
        p.id === pluginId
          ? { ...p, apiKey: `key_${Math.random().toString(36).substring(2, 30)}` }
          : p
      )
    );
    setRotatingKey(null);
  };

  const maskApiKey = (key: string) => {
    if (key.length <= 12) return "••••••••••••";
    return `${key.substring(0, 4)}...${key.substring(key.length - 4)}`;
  };

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border-primary)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--border-primary)]">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Plugin Engine</h3>
        <p className="text-xs text-[var(--text-muted)]">Manage plugins, API keys, and health</p>
      </div>

      <div className="divide-y divide-[var(--border-primary)]">
        {plugins.map((plugin) => (
          <div key={plugin.id} className="p-4 hover:bg-[var(--bg-card-hover)] transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-medium text-[var(--text-primary)]">{plugin.displayName}</h4>
                  <PluginStatusBadge status={plugin.status} />
                </div>
                <p className="text-xs text-[var(--text-muted)] mt-1">{plugin.description}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-[var(--text-muted)]">
                  <span>v{plugin.version}</span>
                  <span className="font-mono">{maskApiKey(plugin.apiKey)}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleStatus(plugin.id)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    plugin.status === "active"
                      ? "bg-red-400/15 text-red-300 hover:bg-red-400/25"
                      : "bg-emerald-400/15 text-emerald-300 hover:bg-emerald-400/25"
                  }`}
                >
                  {plugin.status === "active" ? "Disable" : "Enable"}
                </button>

                <button
                  onClick={() => rotateKey(plugin.id)}
                  disabled={rotatingKey === plugin.id}
                  className="px-3 py-1 text-xs font-medium rounded-md bg-[rgba(139,92,246,0.15)] text-[rgba(139,92,246,0.9)] hover:bg-[rgba(139,92,246,0.25)] disabled:opacity-50 transition-colors"
                >
                  {rotatingKey === plugin.id ? (
                    <span className="flex items-center gap-2">
                      <div className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent" />
                      Rotating...
                    </span>
                  ) : (
                    "Rotate Key"
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
