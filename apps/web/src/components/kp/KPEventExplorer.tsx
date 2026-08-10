"use client";

/**
 * KP Event Explorer — config-driven event promise: each event reads its
 * classical house group, the CSL verdict on its primary cusp, and its
 * ranked significators. Verdicts are honest labels (STRONG/PARTIAL/WEAK),
 * never a manufactured yes/no.
 */

import { useMemo, useState } from "react";
import { computeEventPromise, EVENT_PRIMARY_CUSP } from "@/lib/kpAnalysis";
import { KP_EVENT_HOUSE_GROUPS, type KPEventKey } from "@/lib/kpSignificators";
import type { D1ChartResponse } from "@/lib/types";

interface Props {
  chart: D1ChartResponse;
}

const VERDICT_COLORS: Record<string, { fg: string; bg: string }> = {
  STRONG: { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  PARTIAL: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
  WEAK: { fg: "#f87171", bg: "rgba(248,113,113,0.15)" },
};

export function KPEventExplorer({ chart }: Props) {
  const [eventKey, setEventKey] = useState<KPEventKey>("career");
  const result = useMemo(() => computeEventPromise(chart, eventKey), [chart, eventKey]);
  const vc = VERDICT_COLORS[result.promise];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {(Object.keys(KP_EVENT_HOUSE_GROUPS) as KPEventKey[]).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setEventKey(key)}
            className="rounded-full px-3 py-1 text-xs font-semibold transition"
            style={{
              backgroundColor: eventKey === key ? "var(--accent)" : "var(--bg-card)",
              color: eventKey === key ? "var(--accent-text)" : "var(--text-secondary)",
              border: `1px solid ${eventKey === key ? "var(--accent)" : "var(--border-primary)"}`,
            }}
          >
            {KP_EVENT_HOUSE_GROUPS[key].label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="glass-card p-5" style={{ borderLeft: `4px solid ${vc.fg}` }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Event Promise</p>
          <p className="mt-1 text-2xl font-bold" style={{ color: vc.fg }}>{result.label}</p>
          <span
            className="mt-2 inline-block rounded-full px-3 py-1 text-xs font-bold"
            style={{ backgroundColor: vc.bg, color: vc.fg }}
          >
            {result.promise}
          </span>
          <p className="mt-3 text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {result.csl_verdict.detail}
          </p>
        </div>

        <div className="glass-card p-5">
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            CSL Decision Chain
          </p>
          <ol className="space-y-2 text-xs" style={{ color: "var(--text-secondary)" }}>
            <li className="rounded-lg border p-2" style={{ borderColor: "var(--border-primary)" }}>
              Primary cusp: <span className="font-semibold" style={{ color: "var(--text-primary)" }}>House {result.primary_cusp}</span>
            </li>
            <li className="rounded-lg border p-2" style={{ borderColor: "var(--border-primary)" }}>
              CSL (Sub Lord): <span className="font-semibold" style={{ color: "var(--accent)" }}>{result.csl_verdict.csl || "—"}</span>
            </li>
            <li className="rounded-lg border p-2" style={{ borderColor: "var(--border-primary)" }}>
              CSL Star Lord: <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{result.csl_verdict.csl_star_lord || "—"}</span>
            </li>
            <li className="rounded-lg border p-2" style={{ borderColor: "var(--border-primary)" }}>
              CSL signifies: <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{result.csl_verdict.csl_signifies.length ? result.csl_verdict.csl_signifies.join(", ") : "—"}</span>
            </li>
            <li className="rounded-lg border p-2" style={{ borderColor: "var(--border-primary)" }}>
              Required houses: <span className="font-semibold" style={{ color: "var(--text-primary)" }}>{result.csl_verdict.required_houses.join(", ")}</span>
            </li>
          </ol>
        </div>

        <div className="glass-card p-5">
          <p className="mb-2 text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
            Ranked Significators
          </p>
          {result.significators.length === 0 ? (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>No planets signify these houses.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-xs uppercase tracking-wide" style={{ borderColor: "var(--border-primary)", color: "var(--text-muted)" }}>
                  <th className="py-1.5 pr-3">Planet</th>
                  <th className="py-1.5 pr-3">Grade</th>
                  <th className="py-1.5">Houses</th>
                </tr>
              </thead>
              <tbody>
                {result.significators.map((s) => (
                  <tr key={s.planet} className="border-b" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)" }}>
                    <td className="py-1.5 pr-3 font-medium">{s.planet}</td>
                    <td className="py-1.5 pr-3" style={{ color: "var(--text-secondary)" }}>{s.grade}</td>
                    <td className="py-1.5" style={{ color: "var(--text-secondary)" }}>{s.housesSignified.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
