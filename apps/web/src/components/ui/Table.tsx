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
    <div style={{ border: "1px solid var(--border-default)", borderRadius: "var(--radius-lg)", overflow: "hidden", background: "var(--bg-surface-800)" }}>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", minWidth: "max-content", borderCollapse: "collapse", fontFamily: "var(--font-body)" }}>
          <thead>
            <tr style={{ background: "var(--bg-surface-700)" }}>
              {columns.map((c) => (
                <th
                  key={c.key}
                  style={{
                    textAlign: c.align || "left",
                    padding: "11px 16px",
                    fontSize: "var(--text-xs)",
                    color: "var(--text-tertiary)",
                    textTransform: "uppercase",
                    letterSpacing: "var(--tracking-wide)",
                    fontWeight: "var(--weight-semibold)",
                    borderBottom: "1px solid var(--border-default)",
                  }}
                >
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr
                key={i}
                onClick={() => onRowClick && onRowClick(r)}
                style={{ cursor: onRowClick ? "pointer" : "default", transition: "background var(--duration-fast)" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface-glass)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    style={{
                      padding: "13px 16px",
                      fontSize: "var(--text-base)",
                      color: "var(--text-primary)",
                      textAlign: c.align || "left",
                      borderBottom: i === rows.length - 1 ? "none" : "1px solid var(--border-subtle)",
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
