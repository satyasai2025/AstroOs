"use client";

import { useState } from "react";
import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import { useVimsopaka, type VimsopakaScheme, type VargaDignityScore } from "@/lib/vimsopaka";
import type { WorkflowAnalysisRequest } from "@/lib/types";

interface VimsopakaBalaPanelProps {
  request: WorkflowAnalysisRequest | null;
}

type SchemeKey = "shadvarga" | "saptavarga" | "dasavarga" | "shodasavarga";

const SCHEME_LABELS: { key: SchemeKey; label: string; desc: string }[] = [
  { key: "shadvarga", label: "Shadvarga (6)", desc: "D1, D2, D3, D9, D12, D30" },
  { key: "saptavarga", label: "Saptavarga (7)", desc: "D1, D2, D3, D7, D9, D12, D30" },
  { key: "dasavarga", label: "Dasavarga (10)", desc: "D1, D2, D3, D7, D9, D10, D12, D16, D30, D60" },
  { key: "shodasavarga", label: "Shodasavarga (16)", desc: "16 Parashari Divisional Charts" },
];

const CATEGORY_COLOR: Record<string, string> = {
  "Ati Purna": "#34d399",
  Purna: "#60a5fa",
  Madhya: "#facc15",
  Alpa: "#f87171",
};

export function VimsopakaBalaPanel({ request }: VimsopakaBalaPanelProps) {
  const { data, isLoading, isError } = useVimsopaka(request);
  const [activeScheme, setActiveScheme] = useState<SchemeKey>("shadvarga");
  const [expandedPlanet, setExpandedPlanet] = useState<string | null>(null);

  if (!request) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No birth data available to compute Vimsopaka Bala.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        Computing Vimsopaka Bala across divisional charts…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        Couldn't load Vimsopaka Bala for this chart.
      </div>
    );
  }

  const currentSchemeInfo = SCHEME_LABELS.find((s) => s.key === activeScheme);

  return (
    <div className="glass-card p-5 space-y-4">
      <div>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
          Vimsopaka Bala (20-Point Scale)
        </h3>
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          Parashari divisional strength score (0 to 20 points). Higher scores indicate harmonious placements
          and structural dignity across divisional charts.
        </p>
      </div>

      {/* Scheme Selector Tabs */}
      <div className="flex flex-wrap gap-2 border-b pb-3" style={{ borderColor: "var(--border-primary)" }}>
        {SCHEME_LABELS.map((s) => (
          <button
            key={s.key}
            type="button"
            onClick={() => setActiveScheme(s.key)}
            className={`px-3 py-1 text-xs rounded-full font-medium transition-all ${
              activeScheme === s.key ? "shadow-sm" : "opacity-70 hover:opacity-100"
            }`}
            style={{
              backgroundColor: activeScheme === s.key ? "var(--accent)" : "var(--bg-card)",
              color: activeScheme === s.key ? "#ffffff" : "var(--text-secondary)",
              border: "1px solid var(--border-primary)",
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      <p className="text-[11px] italic" style={{ color: "var(--text-muted)" }}>
        Includes: {currentSchemeInfo?.desc}
      </p>

      {/* Planet List */}
      <div className="space-y-3">
        {data.planets.map((p) => {
          const schemeData: VimsopakaScheme = p[activeScheme];
          const scorePct = (schemeData.vimsopaka_score / 20) * 100;
          const isExpanded = expandedPlanet === p.planet;
          const catColor = CATEGORY_COLOR[schemeData.category] ?? "var(--text-muted)";

          return (
            <div
              key={p.planet}
              className="rounded-lg p-3 border transition-all"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
            >
              <div className="flex items-center justify-between text-xs mb-1.5">
                <button
                  type="button"
                  onClick={() => setExpandedPlanet(isExpanded ? null : p.planet)}
                  className="flex items-center gap-1.5 font-medium hover:underline text-left"
                  style={{ color: "var(--text-primary)" }}
                >
                  <span>{PLANET_SYMBOLS[p.planet] ?? ""}</span>
                  <span className="capitalize">{PLANET_ABBREV[p.planet] ?? p.planet}</span>
                  <span className="text-[10px] text-muted-foreground ml-1">
                    {isExpanded ? "▲ Hide Varga breakdown" : "▼ Show breakdown"}
                  </span>
                </button>
                <div className="flex items-center gap-2">
                  <span className="font-semibold" style={{ color: catColor }}>
                    {schemeData.vimsopaka_score.toFixed(2)} / 20.0
                  </span>
                  <span
                    className="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                    style={{ backgroundColor: `${catColor}26`, color: catColor }}
                  >
                    {schemeData.category}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div
                className="h-2 w-full overflow-hidden rounded-full"
                style={{ backgroundColor: "var(--bg-main)", border: "1px solid var(--border-primary)" }}
              >
                <div
                  className="h-full transition-all duration-300"
                  style={{ width: `${scorePct}%`, backgroundColor: catColor }}
                />
              </div>

              {/* Expanded Varga Breakdown Table */}
              {isExpanded && (
                <div className="mt-3 overflow-x-auto border-t pt-2" style={{ borderColor: "var(--border-primary)" }}>
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr style={{ color: "var(--text-muted)" }}>
                        <th className="pb-1 pr-2">Varga</th>
                        <th className="pb-1 pr-2">Sign</th>
                        <th className="pb-1 pr-2">Dignity</th>
                        <th className="pb-1 pr-2">Weight</th>
                        <th className="pb-1">Points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {schemeData.varga_breakdown.map((vb: VargaDignityScore) => (
                        <tr key={vb.varga} className="border-t border-dashed" style={{ borderColor: "var(--border-primary)" }}>
                          <td className="py-1 pr-2 font-semibold" style={{ color: "var(--text-secondary)" }}>{vb.varga}</td>
                          <td className="py-1 pr-2 capitalize" style={{ color: "var(--text-secondary)" }}>{vb.varga_rashi}</td>
                          <td className="py-1 pr-2 capitalize" style={{ color: "var(--text-muted)" }}>{vb.dignity}</td>
                          <td className="py-1 pr-2" style={{ color: "var(--text-muted)" }}>{vb.weight}</td>
                          <td className="py-1 font-medium" style={{ color: "var(--text-primary)" }}>
                            {vb.weighted_points.toFixed(2)} / {vb.weight}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
