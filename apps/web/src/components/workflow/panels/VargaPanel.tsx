"use client";

import { useState } from "react";
import type { AllVargaChartsResponse } from "@/lib/types";

export function VargaPanel({ vargas }: { vargas: AllVargaChartsResponse | null }) {
  const codes = vargas ? Object.keys(vargas.charts).sort() : [];
  const [selected, setSelected] = useState(codes[0] ?? "");

  if (!vargas) {
    return (
      <div className="glass-card p-5 text-sm text-slate-400">
        Vargas were not computed for this analysis (unchecked at submission time).
      </div>
    );
  }

  const chart = vargas.charts[selected] ?? vargas.charts[codes[0]];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {codes.map((code) => (
          <button
            key={code}
            type="button"
            onClick={() => setSelected(code)}
            className={
              code === (selected || codes[0])
                ? "rounded-full bg-amber-500 px-3 py-1 text-xs font-semibold text-cosmos-950"
                : "rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300 hover:border-white/25"
            }
          >
            {code}
          </button>
        ))}
      </div>

      {chart && (
        <div className="glass-card overflow-x-auto p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-amber-300/80">
            {chart.varga} (÷{chart.divisor}) — Lagna {chart.ascendant.varga_rashi}{" "}
            {chart.ascendant.varga_rashi_degree.toFixed(2)}°
          </h3>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Planet</th>
                <th className="py-2 pr-4">Varga Rashi</th>
                <th className="py-2 pr-4">Degree</th>
                <th className="py-2 pr-4">House</th>
                <th className="py-2">Nakshatra</th>
              </tr>
            </thead>
            <tbody>
              {chart.planet_positions.map((p) => (
                <tr key={p.planet} className="border-b border-white/5 text-slate-200">
                  <td className="py-2 pr-4 font-medium capitalize">{p.planet}</td>
                  <td className="py-2 pr-4 capitalize">{p.varga_rashi}</td>
                  <td className="py-2 pr-4">{p.varga_rashi_degree.toFixed(2)}°</td>
                  <td className="py-2 pr-4">{p.varga_house_number}</td>
                  <td className="py-2">
                    {p.nakshatra} ({p.pada})
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
