"use client";

import { PLANET_ABBREV, PLANET_SYMBOLS } from "@/lib/astro";
import { useAvastha } from "@/lib/avastha";
import type { WorkflowAnalysisRequest } from "@/lib/types";

interface AvasthaPanelProps {
  request: WorkflowAnalysisRequest | null;
}

const BALADI_COLOR: Record<string, string> = {
  Bala: "#60a5fa",
  Kumara: "#34d399",
  Yuva: "#facc15",
  Vriddha: "#fb923c",
  Mrita: "#f87171",
};

const DEEPTADI_COLOR: Record<string, string> = {
  Deepta: "#34d399",
  Swastha: "#4ade80",
  Pramudita: "#a3e635",
  Shanta: "#facc15",
  Sama: "var(--text-muted)",
  Dukhita: "#fb923c",
  Vikala: "#f87171",
  Kopa: "#dc2626",
};

/**
 * Baladi (age-state) and Deeptadi (dignity-state) Avastha per planet —
 * real classical calculations, see apps/api/services/avastha_engine.py.
 * Jagradadi Avastha is intentionally absent (that engine's docstring
 * explains the classical-source ambiguity that ruled it out here).
 */
export function AvasthaPanel({ request }: AvasthaPanelProps) {
  const { data, isLoading, isError } = useAvastha(request);

  if (!request) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        No birth data available to compute Avastha.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        Computing planetary states…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="glass-card p-6 text-sm" style={{ color: "var(--text-muted)" }}>
        Couldn't load Avastha for this chart.
      </div>
    );
  }

  return (
    <div className="glass-card p-5">
      <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Avastha (Planetary States)
      </h3>
      <p className="mb-4 text-xs" style={{ color: "var(--text-muted)" }}>
        Baladi (age-state, by degree) and Deeptadi (dignity-state). Jagradadi Avastha isn't shown —
        classical sources vary too much on its exact derivation to compute honestly here.
      </p>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            <th className="pb-2 pr-2">Planet</th>
            <th className="pb-2 pr-2">Baladi</th>
            <th className="pb-2">Deeptadi</th>
          </tr>
        </thead>
        <tbody>
          {data.avasthas.map((a) => (
            <tr key={a.planet} className="border-t" style={{ borderColor: "var(--border-primary)" }}>
              <td className="py-1.5 pr-2 font-medium" style={{ color: "var(--text-primary)" }}>
                {PLANET_SYMBOLS[a.planet] ?? ""} {PLANET_ABBREV[a.planet] ?? a.planet.slice(0, 2)}
              </td>
              <td className="py-1.5 pr-2">
                <span
                  className="rounded-full px-2 py-0.5 text-xs font-medium"
                  style={{ backgroundColor: `${BALADI_COLOR[a.baladi_avastha] ?? "var(--text-muted)"}26`, color: BALADI_COLOR[a.baladi_avastha] ?? "var(--text-muted)" }}
                  title={a.baladi_trace.join(" ")}
                >
                  {a.baladi_avastha}
                </span>
              </td>
              <td className="py-1.5">
                <span
                  className="rounded-full px-2 py-0.5 text-xs font-medium"
                  style={{ backgroundColor: `${DEEPTADI_COLOR[a.deeptadi_avastha] ?? "var(--text-muted)"}26`, color: DEEPTADI_COLOR[a.deeptadi_avastha] ?? "var(--text-muted)" }}
                  title={a.deeptadi_trace.join(" ")}
                >
                  {a.deeptadi_avastha}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
