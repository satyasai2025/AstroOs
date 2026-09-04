"use client";

import { useState } from "react";
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
 * Analytical Dasha Export Panel:
 * Supports CSV download (for Excel/Sheets analysis), JSON export (for computational pipelines),
 * and direct clipboard copying.
 */
export function DashaExportPanel({ dasha }: { dasha: DashaTreeResponse }) {
  const [copied, setCopied] = useState(false);

  function generateCsv(): string {
    const rows: string[][] = [
      ["Level", "Lord", "Start Date", "End Date", "Duration (days)"],
    ];
    flattenPeriods(dasha.mahadashas, rows);
    return rows.map(toCsvLine).join("\n");
  }

  function handleCsvExport() {
    const csv = generateCsv();
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

  function handleJsonExport() {
    const json = JSON.stringify(dasha, null, 2);
    const blob = new Blob([json], { type: "application/json;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `astroos-${dasha.system}-dasha-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function handleCopy() {
    const csv = generateCsv();
    try {
      await navigator.clipboard.writeText(csv);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-tertiary)" }}>
          Dataset Export & Tooling
        </h4>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded border" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
          {dasha.system} · Depth {dasha.max_depth}
        </span>
      </div>

      <p className="mb-4 text-xs" style={{ color: "var(--text-secondary)" }}>
        Export the computed {dasha.system} dasha timeline ({dasha.mahadashas.length} Mahadashas down to level {dasha.max_depth}) for tabular modeling, research notebooks, or custom analytics.
      </p>

      <div className="flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          onClick={handleCsvExport}
          className="btn-primary text-xs px-3.5 py-1.5 flex items-center gap-1.5"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          <span>Download CSV</span>
        </button>

        <button
          type="button"
          onClick={handleJsonExport}
          className="btn-ghost text-xs px-3.5 py-1.5 flex items-center gap-1.5 border"
          style={{ borderColor: "var(--border-primary)" }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <span>Export JSON</span>
        </button>

        <button
          type="button"
          onClick={handleCopy}
          className="btn-ghost text-xs px-3.5 py-1.5 flex items-center gap-1.5 border"
          style={{ borderColor: "var(--border-primary)" }}
        >
          {copied ? (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{ color: "var(--accent)" }}>
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span style={{ color: "var(--accent)" }}>Copied to Clipboard!</span>
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
              </svg>
              <span>Copy Data</span>
            </>
          )}
        </button>
      </div>
    </Card>
  );
}

