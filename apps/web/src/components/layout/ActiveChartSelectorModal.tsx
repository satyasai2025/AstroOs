"use client";

import React, { useState } from "react";
import { useActiveChart } from "@/lib/charts";
import { useWorkflowStore } from "@/lib/store";
import type { BirthChartSummary } from "@/lib/types";

interface ActiveChartSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ActiveChartSelectorModal({ isOpen, onClose }: ActiveChartSelectorModalProps) {
  const { myCharts, activeSummary, selectChart, isLoading } = useActiveChart();
  const { openCreateModal } = useWorkflowStore();
  const [search, setSearch] = useState("");
  const [selectingId, setSelectingId] = useState<string | null>(null);

  if (!isOpen) return null;

  const filteredCharts = myCharts.filter((c) => {
    const q = search.toLowerCase();
    return (
      c.subject_name.toLowerCase().includes(q) ||
      (c.place_name && c.place_name.toLowerCase().includes(q))
    );
  });

  const handleSelect = async (chart: BirthChartSummary) => {
    setSelectingId(chart.id);
    try {
      await selectChart(chart);
      onClose();
    } catch (err) {
      console.error("Failed to select active chart:", err);
    } finally {
      setSelectingId(null);
    }
  };

  const handleCreateNew = () => {
    onClose();
    openCreateModal("birth_chart");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div
        className="relative z-10 w-full max-w-lg rounded-2xl border bg-background p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col"
        style={{ borderColor: "var(--border-primary)", background: "var(--bg-card, var(--bg-secondary))" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-500 font-bold text-lg border border-indigo-500/20">
              📊
            </div>
            <div>
              <h3 className="text-base font-bold text-foreground">Select Active Chart</h3>
              <p className="text-xs text-muted-foreground">
                Choose a natal profile to drive all charts, dashas, and predictions
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Search & Actions Bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search charts by name or city..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-xl border px-3 py-2 text-xs bg-background/60 text-foreground outline-none focus:ring-2 focus:ring-indigo-500/30"
              style={{ borderColor: "var(--border-primary)" }}
              autoFocus
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                className="absolute right-2.5 top-2 text-xs text-muted-foreground hover:text-foreground cursor-pointer"
              >
                ✕
              </button>
            )}
          </div>

          <button
            type="button"
            onClick={handleCreateNew}
            className="flex items-center gap-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-2 text-xs font-semibold shadow-sm transition shrink-0 cursor-pointer"
          >
            <span>+</span>
            <span>New Chart</span>
          </button>
        </div>

        {/* Charts List */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1 min-h-[220px]">
          {filteredCharts.length > 0 ? (
            filteredCharts.map((chart) => {
              const isActive = activeSummary?.id === chart.id;
              const isBusy = selectingId === chart.id;

              return (
                <div
                  key={chart.id}
                  onClick={() => handleSelect(chart)}
                  className={`flex items-center justify-between p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isActive
                      ? "border-indigo-500 bg-indigo-500/10 shadow-xs ring-1 ring-indigo-500/30"
                      : "border-border hover:border-indigo-500/40 bg-background/40 hover:bg-background/80"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-xl font-bold text-sm ${
                        isActive
                          ? "bg-indigo-600 text-white"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {chart.subject_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-foreground">
                          {chart.subject_name}
                        </span>
                        {chart.is_default && (
                          <span className="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.2 text-[9px] font-semibold text-emerald-400">
                            Default
                          </span>
                        )}
                        {isActive && (
                          <span className="rounded-full bg-indigo-500/20 border border-indigo-500/40 px-2 py-0.2 text-[9px] font-bold text-indigo-300 flex items-center gap-1">
                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {chart.birth_datetime_utc ? new Date(chart.birth_datetime_utc).toLocaleDateString() : "—"}
                        {chart.place_name ? ` · ${chart.place_name}` : ""}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isBusy ? (
                      <span className="text-xs text-indigo-400 animate-pulse font-medium">Loading…</span>
                    ) : isActive ? (
                      <span className="text-xs text-emerald-400 font-bold">Selected ✓</span>
                    ) : (
                      <button
                        type="button"
                        className="rounded-lg border px-2.5 py-1 text-xs font-semibold text-foreground hover:bg-indigo-600 hover:text-white transition cursor-pointer"
                        style={{ borderColor: "var(--border-primary)" }}
                      >
                        Select
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center space-y-2">
              <span className="text-2xl">📋</span>
              <p className="text-xs font-semibold text-foreground">
                {search ? "No charts found matching your search." : "No saved charts yet."}
              </p>
              <p className="text-[11px] text-muted-foreground max-w-xs">
                Create your first birth chart to automatically populate Navatara, SBC, Transits, and Dashas.
              </p>
              <button
                type="button"
                onClick={handleCreateNew}
                className="mt-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 text-xs font-semibold transition cursor-pointer"
              >
                + Create First Chart
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t pt-3 text-[11px] text-muted-foreground" style={{ borderColor: "var(--border-primary)" }}>
          <span>{myCharts.length} saved profile{myCharts.length === 1 ? "" : "s"}</span>
          <button
            type="button"
            onClick={onClose}
            className="hover:text-foreground font-medium cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
