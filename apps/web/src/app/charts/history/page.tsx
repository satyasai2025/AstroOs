"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { useDeleteChart, useMyCharts, useSetDefaultChart } from "@/lib/charts";
import { ApiError } from "@/lib/api";
import { useWorkflowStore } from "@/lib/store";
import { RecomputeChartModal } from "@/components/charts/RecomputeChartModal";
import { initialsOf, paletteFor } from "@/components/dashboard/DashboardOverview";
import { Badge, Button, Card, SearchInput, Select, Table, type TableColumn } from "@/components/ui";
import type { BirthChartSummary } from "@/lib/types";

type SortMode = "recent" | "name" | "oldest";

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
  const setDefaultChart = useSetDefaultChart();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [defaultError, setDefaultError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortMode>("recent");

  const visibleCharts = useMemo(() => {
    const charts = data?.charts ?? [];
    const q = search.trim().toLowerCase();
    const filtered = q
      ? charts.filter(
          (c) =>
            c.subject_name.toLowerCase().includes(q) ||
            (c.place_name ?? "").toLowerCase().includes(q) ||
            (c.lagna_rashi ?? "").toLowerCase().includes(q),
        )
      : charts;
    const sorted = [...filtered];
    if (sort === "name") sorted.sort((a, b) => a.subject_name.localeCompare(b.subject_name));
    else if (sort === "oldest") sorted.sort((a, b) => a.created_at.localeCompare(b.created_at));
    else sorted.sort((a, b) => b.created_at.localeCompare(a.created_at));
    return sorted;
  }, [data, search, sort]);

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

  const handleSetDefault = (chart: BirthChartSummary) => {
    setDefaultError(null);
    setSettingDefaultId(chart.id);
    setDefaultChart.mutate(chart.id, {
      onError: (err) => {
        setDefaultError(
          err instanceof ApiError ? err.detail : "Could not set this chart as default. Please retry.",
        );
      },
      onSettled: () => setSettingDefaultId(null),
    });
  };

  const columns: TableColumn<BirthChartSummary>[] = [
    {
      key: "subject_name",
      label: "Native",
      render: (c) => {
        const color = paletteFor(c.id);
        return (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 30,
                height: 30,
                borderRadius: "50%",
                flexShrink: 0,
                background: color.fg,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 11,
                fontWeight: 700,
                color: "#fff",
              }}
            >
              {initialsOf(c.subject_name)}
            </div>
            <Link href={`/charts/${c.id}`} style={{ fontWeight: "var(--weight-medium)" }} className="hover:underline">
              {c.subject_name}
            </Link>
            {c.is_default && <Badge tone="success">Default</Badge>}
          </div>
        );
      },
    },
    { key: "birth_datetime_utc", label: "Birth (UTC)", render: (c) => formatDateTime(c.birth_datetime_utc), mono: true },
    { key: "place_name", label: "Place", render: (c) => c.place_name ?? "—" },
    { key: "lagna_rashi", label: "Lagna", render: (c) => <span style={{ textTransform: "capitalize" }}>{c.lagna_rashi ?? "—"}</span> },
    { key: "moon_nakshatra", label: "Moon Nakshatra", render: (c) => <span style={{ textTransform: "capitalize" }}>{c.moon_nakshatra ?? "—"}</span> },
    { key: "created_at", label: "Saved", render: (c) => formatDateTime(c.created_at), mono: true },
    { key: "type", label: "Type", render: () => <Badge tone="violet">D1 Chart</Badge> },
    {
      key: "actions",
      label: "",
      align: "right",
      render: (c) => (
        <div className="flex items-center justify-end gap-2">
          {!c.is_default && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleSetDefault(c)}
              disabled={settingDefaultId === c.id}
              title="Use this chart as your default"
            >
              {settingDefaultId === c.id ? "Setting…" : "Set as Default"}
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setRecomputeChart(c)}
            title="View this chart with a different Ayanamsa, House System, or Dasha System"
          >
            Recompute
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => handleDelete(c)}
            disabled={deletingId === c.id}
            title="Delete this saved chart"
          >
            {deletingId === c.id ? "Deleting…" : "Delete"}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Saved Charts
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            {data ? `${data.total} chart${data.total === 1 ? "" : "s"} saved to your account.` : "Charts you've generated while signed in, most recent first."}
          </p>
        </div>
        <Button
          onClick={() => {
            // Dashboard shows the last analysis result (from the shared
            // store) instead of the blank form if one exists — clear it
            // first so "Create Chart" always lands on a fresh form,
            // consistent with AnalysisResults' own onReset behavior.
            clearWorkflowResult();
            router.push("/dashboard");
          }}
        >
          + Create Chart
        </Button>
      </div>

      {deleteError && (
        <Card style={{ marginBottom: "1rem", padding: "0.75rem 1rem" }}>
          <p className="text-sm" style={{ color: "var(--danger-400)" }} role="alert">
            {deleteError}
          </p>
        </Card>
      )}

      {defaultError && (
        <Card style={{ marginBottom: "1rem", padding: "0.75rem 1rem" }}>
          <p className="text-sm" style={{ color: "var(--danger-400)" }} role="alert">
            {defaultError}
          </p>
        </Card>
      )}

      {isLoading && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Loading…</p>
        </Card>
      )}

      {isError && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--danger-400)" }} role="alert">
            {errorMessage}
          </p>
        </Card>
      )}

      {data && data.charts.length === 0 && (
        <Card style={{ padding: "2rem", textAlign: "center" }}>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            No saved charts yet. Charts you generate on the Dashboard will appear here.
          </p>
        </Card>
      )}

      {data && data.charts.length > 0 && (
        <div className="space-y-4">
          <div style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
            <div style={{ flex: 1, maxWidth: 340 }}>
              <SearchInput value={search} onChange={setSearch} placeholder="Search by name, place, lagna…" shortcut="" />
            </div>
            <div style={{ width: 200 }}>
              <Select
                value={sort}
                onChange={(v) => setSort(v as SortMode)}
                options={[
                  { label: "Most recent", value: "recent" },
                  { label: "Name (A–Z)", value: "name" },
                  { label: "Oldest first", value: "oldest" },
                ]}
              />
            </div>
          </div>

          <Card padding="0">
            <div style={{ padding: "12px 20px 20px" }}>
              <Table<BirthChartSummary> columns={columns} rows={visibleCharts} />
            </div>
          </Card>

          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            Showing {visibleCharts.length} of {data.total} saved chart{data.total === 1 ? "" : "s"}.
          </p>
        </div>
      )}

      {recomputeChart && (
        <RecomputeChartModal chart={recomputeChart} onClose={() => setRecomputeChart(null)} />
      )}
    </AppShell>
  );
}
