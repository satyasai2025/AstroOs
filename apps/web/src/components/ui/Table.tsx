"use client";

import type { ReactNode } from "react";

export interface TableColumn<Row> {
  key: string;
  label: string;
  align?: "left" | "center" | "right";
  mono?: boolean;
  render?: (row: Row) => ReactNode;
}

interface TableProps<Row> {
  columns: TableColumn<Row>[];
  rows: Row[];
  onRowClick?: (row: Row) => void;
}

export function Table<Row extends object>({ columns = [], rows = [], onRowClick }: TableProps<Row>) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm shadow-slate-200/50 dark:shadow-none">
      <div className="w-full overflow-x-auto min-w-0">
        <table className="w-full text-xs" style={{ minWidth: "max-content", borderCollapse: "collapse", fontFamily: "var(--font-body)" }}>
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-700/80">
              {columns.map((c) => (
                <th
                  key={c.key}
                  className="text-slate-600 dark:text-slate-400 font-semibold text-[11px] uppercase tracking-wider px-3 py-2"
                  style={{
                    textAlign: c.align || "left",
                  }}
                >
                  {c.label || <span className="sr-only">{c.key}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {rows.map((r, i) => (
              <tr
                key={i}
                onClick={() => onRowClick && onRowClick(r)}
                style={{ cursor: onRowClick ? "pointer" : "default", transition: "background 120ms ease" }}
                className={`transition-colors ${
                  onRowClick
                    ? "hover:bg-slate-50 dark:hover:bg-slate-800/70"
                    : "hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
                }`}
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className="px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100"
                    style={{
                      textAlign: c.align || "left",
                      fontFamily: c.mono ? "var(--font-mono)" : "var(--font-body)",
                    }}
                  >
                    {c.render ? c.render(r) : ((r as Record<string, unknown>)[c.key] as ReactNode)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
