"use client";

import { Badge, Card } from "@/components/ui";
import type { PatternSummary } from "@/lib/types";

interface ActiveDatasetBoxProps {
  summary: PatternSummary | null;
  lastUpdated?: string | null;
  datasetName?: string;
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "var(--text-xs)" }}>
      <span style={{ color: "var(--text-tertiary)" }}>{label}</span>
      <span style={{ color: "var(--text-primary)", fontWeight: "var(--weight-semibold)" }}>{value}</span>
    </div>
  );
}

function fmt(n: number | undefined): string {
  if (n === undefined) return "—";
  return n.toLocaleString();
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return "—";
  }
}

/** No multi-dataset concept exists in the backend yet — "AstroOS Global Set"
 * is the single real dataset (all imported research cases), matching the
 * Dataset filter's "All Cases" scope elsewhere on this page. */
export function ActiveDatasetBox({ summary, lastUpdated, datasetName = "AstroOS Global Set" }: ActiveDatasetBoxProps) {
  return (
    <Card padding="var(--space-3)">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-2)" }}>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "var(--tracking-wide)" }}>
          Active Dataset
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "var(--space-3)" }}>
        <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
          {datasetName}
        </span>
        <Badge tone="success">Active</Badge>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <StatRow label="Cases" value={fmt(summary?.total_cases)} />
        <StatRow label="Events" value={fmt(summary?.total_events)} />
        <StatRow label="Snapshots" value={fmt(summary?.total_snapshots)} />
        <StatRow label="Last Updated" value={fmtDate(lastUpdated)} />
      </div>
    </Card>
  );
}
