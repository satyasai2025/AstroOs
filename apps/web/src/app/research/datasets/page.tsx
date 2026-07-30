"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, FilterBar, Table, type TableColumn } from "@/components/ui";

interface DatasetRow {
  id: string;
  name: string;
  charts: number;
  size: string;
  status: "ready" | "processing" | "error";
  updated: string;
}

/**
 * Illustrative dataset catalog matching the "Datasets" mockup — this app
 * has no dataset-management backend (upload/tag/derive collections of
 * charts), so every row here is a fabricated sample, not live data.
 */
const DATASETS: DatasetRow[] = [
  { id: "ds-1", name: "Marriage Timing Dataset", charts: 12431, size: "1.2 GB", status: "ready", updated: "2026-07-18" },
  { id: "ds-2", name: "Career Success Cohort", charts: 8320, size: "740 MB", status: "ready", updated: "2026-07-12" },
  { id: "ds-3", name: "Sade Sati Life Events", charts: 4110, size: "410 MB", status: "processing", updated: "2026-07-25" },
  { id: "ds-4", name: "Twin Studies Sample", charts: 212, size: "18 MB", status: "ready", updated: "2026-06-30" },
  { id: "ds-5", name: "Historical Figures Archive", charts: 1840, size: "160 MB", status: "error", updated: "2026-06-14" },
];

const STATUS_TONE: Record<DatasetRow["status"], "success" | "gold" | "danger"> = {
  ready: "success",
  processing: "gold",
  error: "danger",
};

export default function DatasetsPage() {
  const [statusFilter, setStatusFilter] = useState<Record<string, string>>({});

  const filtered = DATASETS.filter((d) => !statusFilter.status || d.status === statusFilter.status);

  const columns: TableColumn<DatasetRow>[] = [
    { key: "name", label: "Dataset" },
    { key: "charts", label: "Charts", align: "right", render: (r) => r.charts.toLocaleString() },
    { key: "size", label: "Size" },
    { key: "status", label: "Status", render: (r) => <Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge> },
    { key: "updated", label: "Updated" },
    {
      key: "actions",
      label: "",
      render: (r) => (
        <Button href={`/research/query-builder?dataset=${r.id}`} variant="ghost" size="sm">
          Open in Query Builder
        </Button>
      ),
    },
  ];

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Datasets
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Vedic Astrology Research — curated chart collections for pattern queries.
          </p>
        </div>
        <Button variant="primary">New Dataset</Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <FilterBar
          filters={[
            {
              key: "status",
              label: "Status",
              options: [
                { value: "ready", label: "Ready" },
                { value: "processing", label: "Processing" },
                { value: "error", label: "Error" },
              ],
            },
          ]}
          activeValues={statusFilter}
          onChange={(key, value) => setStatusFilter((prev) => ({ ...prev, [key]: value }))}
          onClear={() => setStatusFilter({})}
        />
      </Card>

      <Table columns={columns} rows={filtered} />

      <p className="mt-3 text-xs" style={{ color: "var(--text-tertiary)" }}>
        All dataset figures above are illustrative — chart-collection management isn't backed by a
        real data pipeline yet.
      </p>
    </AppShell>
  );
}
