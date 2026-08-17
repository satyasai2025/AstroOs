"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
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

/** Format raw decimal coordinates into compact directional notation.
 * e.g. (23.03714521, 72.55123910) → "23.037° N, 72.551° E" */
function formatCoords(lat: number | null | undefined, lng: number | null | undefined): string {
  if (lat == null || lng == null) return "—";
  const latDir = lat >= 0 ? "N" : "S";
  const lngDir = lng >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(3)}° ${latDir}, ${Math.abs(lng).toFixed(3)}° ${lngDir}`;
}

/** Display value for the Place cell: prefer place_name if non-empty,
 * else fall back to formatted coords, else em-dash. */
function placeDisplay(c: BirthChartSummary): string {
  if (c.place_name && c.place_name.trim()) return c.place_name.trim();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw = c as any;
  if (raw.latitude != null && raw.longitude != null) {
    return formatCoords(raw.latitude as number, raw.longitude as number);
  }
  return "—";
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
  const [activeFilter, setActiveFilter] = useState<"all" | "research" | "recent">("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchSuccessMessage, setBatchSuccessMessage] = useState<string | null>(null);

  const toggleSelectAll = () => {
    if (selectedIds.size === visibleCharts.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(visibleCharts.map((c) => c.id)));
    }
  };

  const toggleSelectOne = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleAddSelectedToDataset = () => {
    if (selectedIds.size === 0) return;
    try {
      const existing: string[] = JSON.parse(localStorage.getItem("astroos_research_dataset_charts") || "[]");
      const combined = Array.from(new Set([...existing, ...Array.from(selectedIds)]));
      localStorage.setItem("astroos_research_dataset_charts", JSON.stringify(combined));
      setBatchSuccessMessage(`Added ${selectedIds.size} chart(s) to Research Dataset!`);
      setSelectedIds(new Set());
      setTimeout(() => setBatchSuccessMessage(null), 3000);
    } catch {
      setBatchSuccessMessage("Failed to save to research dataset.");
    }
  };

  const visibleCharts = useMemo(() => {
    const charts = data?.charts ?? [];
    const q = search.trim().toLowerCase();
    let filtered = q
      ? charts.filter(
          (c) =>
            c.subject_name.toLowerCase().includes(q) ||
            (c.place_name ?? "").toLowerCase().includes(q) ||
            (c.lagna_rashi ?? "").toLowerCase().includes(q),
        )
      : charts;

    if (activeFilter === "research") {
      try {
        const researchIds: string[] = JSON.parse(localStorage.getItem("astroos_research_dataset_charts") || "[]");
        filtered = filtered.filter((c) => researchIds.includes(c.id));
      } catch {
        // ignore
      }
    } else if (activeFilter === "recent") {
      filtered = filtered.slice(0, 10);
    }

    const sorted = [...filtered];
    if (sort === "name") sorted.sort((a, b) => a.subject_name.localeCompare(b.subject_name));
    else if (sort === "oldest") sorted.sort((a, b) => a.created_at.localeCompare(b.created_at));
    else sorted.sort((a, b) => b.created_at.localeCompare(a.created_at));
    return sorted;
  }, [data, search, sort, activeFilter]);

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
      key: "select",
      label: "",
      render: (c) => (
        <input
          type="checkbox"
          checked={selectedIds.has(c.id)}
          onClick={(e) => toggleSelectOne(c.id, e)}
          onChange={() => {}}
          className="h-4 w-4 rounded cursor-pointer"
          aria-label={`Select ${c.subject_name}`}
        />
      ),
    },
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
    {
      key: "place_name",
      label: "Place",
      render: (c) => {
        const display = placeDisplay(c);
        return (
          <span
            className="block max-w-[180px] sm:max-w-[220px] truncate"
            title={display}
          >
            {display}
          </span>
        );
      },
    },

    { key: "lagna_rashi", label: "Lagna", render: (c) => <span style={{ textTransform: "capitalize" }}>{c.lagna_rashi ?? "—"}</span> },
    { key: "moon_nakshatra", label: "Moon Nakshatra", render: (c) => <span style={{ textTransform: "capitalize" }}>{c.moon_nakshatra ?? "—"}</span> },
    { key: "created_at", label: "Saved", render: (c) => formatDateTime(c.created_at), mono: true },
    { key: "type", label: "Type", render: () => <Badge tone="violet">D1 Chart</Badge> },
    {
      key: "actions",
      label: "",
      align: "right",
      render: (c) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Link
            href={`/ai/explain`}
            className="rounded px-2 py-1 text-[11px] font-medium border border-purple-500/30 bg-purple-500/10 text-purple-300 hover:bg-purple-500/20"
            title="Ask AI questions about this chart"
          >
            AI Explain
          </Link>
          <Link
            href={`/charts/transit?chart_id=${c.id}`}
            className="rounded px-2 py-1 text-[11px] font-medium border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20"
            title="View transits for this chart"
          >
            Transits
          </Link>
          <Link
            href={`/charts/compare`}
            className="rounded px-2 py-1 text-[11px] font-medium border border-amber-500/30 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20"
            title="Compare with another chart"
          >
            Compare
          </Link>
          {!c.is_default && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleSetDefault(c)}
              disabled={settingDefaultId === c.id}
              title="Use this chart as your default"
            >
              {settingDefaultId === c.id ? "Setting…" : "Set Default"}
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
    <>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Saved Charts
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            {data ? `${data.total} chart${data.total === 1 ? "" : "s"} saved to your account.` : "Charts you've generated while signed in, most recent first."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            clearWorkflowResult();
            router.push("/dashboard");
          }}
          className="flex items-center gap-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800/50 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:border-cyan-500/60 hover:text-cyan-600 dark:hover:text-cyan-400 shadow-sm transition"
        >
          + Create Chart
        </button>
      </div>

      {batchSuccessMessage && (
        <div className="mb-4 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3 text-xs font-semibold text-emerald-400">
          ✓ {batchSuccessMessage}
        </div>
      )}

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
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveFilter("all")}
                className={`rounded-full px-3 py-1 text-xs font-semibold border transition ${
                  activeFilter === "all"
                    ? "border-amber-500 bg-amber-500/10 text-amber-400"
                    : "border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400"
                }`}
              >
                All Charts
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter("research")}
                className={`rounded-full px-3 py-1 text-xs font-semibold border transition ${
                  activeFilter === "research"
                    ? "border-amber-500 bg-amber-500/10 text-amber-400"
                    : "border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400"
                }`}
              >
                Research Cases
              </button>
              <button
                type="button"
                onClick={() => setActiveFilter("recent")}
                className={`rounded-full px-3 py-1 text-xs font-semibold border transition ${
                  activeFilter === "recent"
                    ? "border-amber-500 bg-amber-500/10 text-amber-400"
                    : "border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400"
                }`}
              >
                Recently Saved
              </button>
              {selectedIds.size > 0 && (
                <Button variant="gold" size="sm" onClick={handleAddSelectedToDataset}>
                  + Add Selected ({selectedIds.size}) to Research Dataset
                </Button>
              )}
            </div>

            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ width: 220 }}>
                <SearchInput value={search} onChange={setSearch} placeholder="Search name, place…" shortcut="" />
              </div>
              <div style={{ width: 160 }}>
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
          </div>

          <Card padding="0">
            <div style={{ padding: "12px 20px 20px" }}>
              <Table<BirthChartSummary>
                columns={columns}
                rows={visibleCharts}
                onRowClick={(c) => router.push(`/charts/${c.id}`)}
              />
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
    </>
  );
}
