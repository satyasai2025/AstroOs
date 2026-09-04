"use client";

import { useState } from "react";
import { Card, Table, type TableColumn } from "@/components/ui";
import { formatPosition } from "@/lib/formatAstro";
import type { AllVargaChartsResponse, VargaPlanetResponse } from "@/lib/types";

export function VargaPanel({ vargas }: { vargas: AllVargaChartsResponse | null }) {
  const codes = vargas ? Object.keys(vargas.charts).sort() : [];
  const [selected, setSelected] = useState(codes[0] ?? "");

  if (!vargas) {
    return (
      <Card>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
          Vargas were not computed for this analysis (unchecked at submission time).
        </p>
      </Card>
    );
  }

  const chart = vargas.charts[selected] ?? vargas.charts[codes[0]];

  const columns: TableColumn<VargaPlanetResponse>[] = [
    { key: "planet", label: "Planet" },
    { key: "varga_rashi", label: "Varga Rashi" },
    {
      key: "varga_rashi_degree",
      label: "Degree",
      render: (p) => formatPosition(p.varga_rashi, p.varga_rashi_degree),
    },
    { key: "varga_house_number", label: "House" },
    { key: "nakshatra", label: "Nakshatra", render: (p) => `${p.nakshatra} (${p.pada})` },
  ];

  return (
    <div className="space-y-4">
      {/* Horizontal scrollable D1..D60 pill selector, matching divisional-charts.html */}
      <div className="flex flex-wrap gap-2 overflow-x-auto pb-1">
        {codes.map((code) => {
          const active = code === (selected || codes[0]);
          return (
            <button
              key={code}
              type="button"
              onClick={() => setSelected(code)}
              className="rounded-full px-3 py-1 text-xs font-semibold transition"
              style={{
                backgroundColor: active ? "var(--accent)" : "var(--bg-card)",
                color: active ? "var(--accent-text)" : "var(--text-secondary)",
                border: `1px solid ${active ? "var(--accent)" : "var(--border-primary)"}`,
              }}
              aria-pressed={active}
            >
              {code}
            </button>
          );
        })}
      </div>

      {chart && (
        <Card>
          <h3
            className="mb-3 text-sm font-semibold uppercase tracking-wide"
            style={{ color: "var(--accent)" }}
          >
            {chart.varga} (÷{chart.divisor}) — Lagna {formatPosition(chart.ascendant.varga_rashi, chart.ascendant.varga_rashi_degree)}
          </h3>
          <Table columns={columns} rows={chart.planet_positions} />
        </Card>
      )}
    </div>
  );
}
