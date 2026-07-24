"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { useDeleteChart, useMyCharts } from "@/lib/charts";
import { ApiError } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import { RecomputeChartModal } from "@/components/charts/RecomputeChartModal";
import type { BirthChartSummary } from "@/lib/types";

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export default function ChartHistoryPage() {
  const router = useRouter();
  const { data, isLoading, isError, error } = useMyCharts();
  const [recomputeChart, setRecomputeChart] = useState<BirthChartSummary | null>(null);
  const clearWorkflowResult = useWorkflowStore((s) => s.clear);
  const deleteChart = useDeleteChart();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const errorMessage =
    error instanceof ApiError
      ? error.detail
      : error
        ? "Could not load your saved charts."
        : null;

  const handleDelete = (chart: BirthChartSummary) => {
    if (!window.confirm(`Delete the saved chart for "${chart.subject_name}"? This can't be undone.`)) {
      return;
    }
    setDeleteError(null);
    setDeletingId(chart.id);
    deleteChart.mutate(chart.id, {
      onError: (err) => {
        setDeleteError(
          err instanceof ApiError ? err.detail : "Could not delete this chart. Please retry.",
        );
      },
      onSettled: () => setDeletingId(null),
    });
  };

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Saved Charts
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Charts you&apos;ve generated while signed in, most recent first.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            // Dashboard shows the last analysis result (from the shared
            // store) instead of the blank form if one exists — clear it
            // first so "Create Chart" always lands on a fresh form,
            // consistent with AnalysisResults' own onReset behavior.
            clearWorkflowResult();
            router.push("/dashboard");
          }}
          className="btn-primary px-4 py-2 text-sm"
        >
          + Create Chart
        </button>
      </div>

      {deleteError && (
        <div
          className="glass-card mb-4 p-3 text-sm"
          style={{ color: "var(--chart-ascendant)" }}
          role="alert"
        >
          {deleteError}
        </div>
      )}

      {isLoading && (
        <div className="glass-card p-8 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
          Loading…
        </div>
      )}

      {isError && (
        <div
          className="glass-card p-8 text-center text-sm"
          style={{ color: "var(--chart-ascendant)" }}
          role="alert"
        >
          {errorMessage}
        </div>
      )}

      {data && data.charts.length === 0 && (
        <div className="glass-card p-8 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
          No saved charts yet. Charts you generate on the Dashboard will appear here.
        </div>
      )}

      {data && data.charts.length > 0 && (
        <div className="glass-card overflow-x-auto p-5">
          <table className="w-full text-left text-sm" role="table">
            <thead>
              <tr
                className="border-b text-xs uppercase tracking-wide"
                style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}
              >
                <th className="py-2 pr-3" scope="col">Subject</th>
                <th className="py-2 pr-3" scope="col">Birth (UTC)</th>
                <th className="py-2 pr-3" scope="col">Place</th>
                <th className="py-2 pr-3" scope="col">Lagna</th>
                <th className="py-2 pr-3" scope="col">Moon Nakshatra</th>
                <th className="py-2 pr-3" scope="col">Saved</th>
                <th className="py-2" scope="col">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {data.charts.map((c) => (
                <tr
                  key={c.id}
                  className="border-b"
                  style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}
                >
                  <td className="py-2 pr-3 font-medium">{c.subject_name}</td>
                  <td className="py-2 pr-3">{formatDateTime(c.birth_datetime_utc)}</td>
                  <td className="py-2 pr-3" style={{ color: "var(--text-secondary)" }}>
                    {c.place_name ?? "—"}
                  </td>
                  <td className="py-2 pr-3 capitalize">{c.lagna_rashi ?? "—"}</td>
                  <td className="py-2 pr-3 capitalize">{c.moon_nakshatra ?? "—"}</td>
                  <td className="py-2 pr-3" style={{ color: "var(--text-secondary)" }}>
                    {formatDateTime(c.created_at)}
                  </td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setRecomputeChart(c)}
                        className="btn-ghost px-2 py-1 text-xs"
                        title="View this chart with a different Ayanamsa, House System, or Dasha System"
                      >
                        Recompute
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(c)}
                        disabled={deletingId === c.id}
                        className="px-2 py-1 text-xs font-medium transition disabled:opacity-50"
                        style={{ color: "var(--chart-ascendant)" }}
                        title="Delete this saved chart"
                      >
                        {deletingId === c.id ? "Deleting…" : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
            Showing {data.charts.length} of {data.total} saved chart{data.total === 1 ? "" : "s"}.
          </p>
        </div>
      )}

      {recomputeChart && (
        <RecomputeChartModal chart={recomputeChart} onClose={() => setRecomputeChart(null)} />
      )}
    </AppShell>
  );
}
