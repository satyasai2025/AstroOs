"use client";

import { useState, useEffect } from "react";
import { researchModeApi } from "@/lib/research";
import type { ResearchMode } from "@/lib/research";

/**
 * Global research mode toggle that can be placed anywhere in the app.
 *
 * When enabled, all research queries/analyses are logged for reproducibility.
 * Persists across sessions.
 */
export function ResearchModeToggle({ compact = false }: { compact?: boolean }) {
  const [mode, setMode] = useState<ResearchMode | null>(null);
  const [toggling, setToggling] = useState(false);

  useEffect(() => {
    researchModeApi.get().then(setMode).catch(() => {});
  }, []);

  async function handleToggle() {
    setToggling(true);
    try {
      const newMode = await researchModeApi.set(!mode?.enabled);
      setMode(newMode);
    } catch (err) {
      console.error("Failed to toggle research mode", err);
    } finally {
      setToggling(false);
    }
  }

  if (compact) {
    return (
      <button
        type="button"
        onClick={handleToggle}
        disabled={toggling}
        className="flex items-center gap-1.5 rounded-full px-2 py-1 text-[10px] font-medium transition-colors"
        style={{
          backgroundColor: mode?.enabled
            ? "rgba(34, 197, 94, 0.15)"
            : "var(--bg-card)",
          color: mode?.enabled ? "#22c55e" : "var(--text-muted)",
          border: `1px solid ${
            mode?.enabled ? "rgba(34, 197, 94, 0.3)" : "var(--border-primary)"
          }`,
        }}
        aria-label={`Research mode: ${mode?.enabled ? "ON" : "OFF"}. Click to toggle.`}
      >
        <span
          className="inline-block h-1.5 w-1.5 rounded-full"
          style={{
            backgroundColor: mode?.enabled ? "#22c55e" : "var(--text-muted)",
          }}
        />
        {mode?.enabled ? "Research ON" : "Research OFF"}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      disabled={toggling}
      className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
      style={{
        backgroundColor: mode?.enabled
          ? "rgba(34, 197, 94, 0.15)"
          : "var(--bg-card)",
        color: mode?.enabled ? "#22c55e" : "var(--text-secondary)",
        border: `1px solid ${
          mode?.enabled ? "rgba(34, 197, 94, 0.3)" : "var(--border-primary)"
        }`,
      }}
      aria-label={`Research mode is ${mode?.enabled ? "on" : "off"}. Click to toggle.`}
    >
      <span
        className="inline-block h-2 w-2 rounded-full"
        style={{
          backgroundColor: mode?.enabled ? "#22c55e" : "var(--text-muted)",
        }}
      />
      Research Mode {mode?.enabled ? "ON" : "OFF"}
      {mode?.enabled && mode.total_logged_queries > 0 && (
        <span className="rounded-full px-1.5 py-0.5 text-[10px]" style={{ backgroundColor: "rgba(34, 197, 94, 0.2)" }}>
          {mode.total_logged_queries}
        </span>
      )}
    </button>
  );
}
