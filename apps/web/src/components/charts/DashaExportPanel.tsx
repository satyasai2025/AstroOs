"use client";

import { Card } from "@/components/ui";
import type { DashaPeriodResponse, DashaTreeResponse } from "@/lib/types";

const LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"];

function escapeCsvCell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

function toCsvLine(cells: string[]): string {
  return cells.map(escapeCsvCell).join(",");
}

function flattenPeriods(periods: DashaPeriodResponse[], rows: string[][]): void {
  for (const p of periods) {
    rows.push([
      LEVEL_NAMES[p.level - 1] ?? `Level ${p.level}`,
      p.lord,
      p.start_date,
      p.end_date,
      String(p.duration_days),
    ]);
    if (p.sub_periods.length > 0) flattenPeriods(p.sub_periods, rows);
  }
}

/**
 * "Reports" panel from the architecture diagram — a plain, honest
 * client-side CSV export of the displayed dasha tree (same Blob +
 * createObjectURL idiom as apps/web/src/app/charts/compare/components/
 * CsvExporter.tsx). CSV instead of JSON so the file opens directly and
 * readably in Excel/Sheets. No backend report-engine integration exists
 * for dasha, so this doesn't claim to generate a formatted PDF report.
 */
export function DashaExportPanel({ dasha }: { dasha: DashaTreeResponse }) {
  function handleExport() {
    const rows: string[][] = [
      ["Level", "Lord", "Start Date", "End Date", "Duration (days)"],
    ];
    flattenPeriods(dasha.mahadashas, rows);
    const csv = rows.map(toCsvLine).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `astroos-${dasha.system}-dasha-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <Card>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
        Export
      </h4>
      <p className="mb-3 text-sm" style={{ color: "var(--text-secondary)" }}>
        Download the currently-displayed {dasha.system} dasha tree ({dasha.mahadashas.length} mahadashas, computed
        to level {dasha.max_depth}) as a CSV — one row per period (Mahadasha through {LEVEL_NAMES[dasha.max_depth - 1] ?? `Level ${dasha.max_depth}`}),
        opens directly in Excel/Sheets.
      </p>
      <button type="button" onClick={handleExport} className="btn-primary text-xs px-3 py-1.5">
        Download as CSV
      </button>
    </Card>
  );
}
