"use client";

/**
 * KP Evidence / Reasoning Chain — for a selected event, the full evidence
 * chain behind the verdict: required houses → primary cusp → CSL → CSL
 * Star Lord → CSL significations → RP intersection → timing. This is the
 * "every conclusion carries an evidence chain" layer.
 */

import { useMemo, useState } from "react";
import { computeEventPromise, computeFruitfulSignificators } from "@/lib/kpAnalysis";
import { KP_EVENT_HOUSE_GROUPS, type KPEventKey } from "@/lib/kpSignificators";
import type { D1ChartResponse, DashaTreeResponse } from "@/lib/types";
import { getCurrentDashaChain } from "@/lib/kpiScoring";

interface Props {
  chart: D1ChartResponse;
  dasha?: DashaTreeResponse;
}

export function KPReasoningChain({ chart, dasha }: Props) {
  const [eventKey, setEventKey] = useState<KPEventKey>("career");
  const result = useMemo(() => computeEventPromise(chart, eventKey), [chart, eventKey]);
  const fruitful = useMemo(
    () => computeFruitfulSignificators(chart, result.houses),
    [chart, result.houses],
  );
  const activeChain = useMemo(
    () => (dasha ? getCurrentDashaChain(dasha.mahadashas) : []),
    [dasha],
  );

  const topSignificator = result.significators[0];
  const activeLevel = topSignificator
    ? activeChain.find((p) => p.lord === topSignificator.planet)
    : undefined;

  const rpIntersection = fruitful
    .filter((f) => result.csl_verdict.csl === f.planet)
    .map((f) => f.planet);

  const steps = [
    { label: "Required Houses", value: result.houses.join(", ") },
    { label: "Primary Cusp", value: `House ${result.primary_cusp}` },
    { label: "CSL (Sub Lord)", value: result.csl_verdict.csl || "—" },
    { label: "CSL Star Lord", value: result.csl_verdict.csl_star_lord || "—" },
    { label: "CSL Significations", value: result.csl_verdict.csl_signifies.length ? result.csl_verdict.csl_signifies.join(", ") : "—" },
    { label: "Required ∩ CSL", value: result.csl_verdict.required_houses.filter((h) => result.csl_verdict.csl_signifies.includes(h)).join(", ") || "—" },
    { label: "RP Intersection", value: rpIntersection.length ? rpIntersection.join(", ") : "—" },
    { label: "Timing (Dasha)", value: activeLevel ? `${topSignificator?.planet} ${activeLevel.lord} — active` : "Not in active dasha period" },
  ];

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

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
            {result.label} — Evidence Chain
          </h3>
          <span
            className="rounded-full px-3 py-1 text-xs font-bold"
            style={{
              backgroundColor: result.promise === "POSITIVE" ? "rgba(52,211,153,0.15)" : result.promise === "PARTIAL" ? "rgba(251,191,36,0.15)" : "rgba(248,113,113,0.15)",
              color: result.promise === "POSITIVE" ? "#34d399" : result.promise === "PARTIAL" ? "#fbbf24" : "#f87171",
            }}
          >
            {result.promise}
          </span>
        </div>

        <ol className="relative space-y-0 pl-6">
          {steps.map((step, i) => (
            <li key={step.label} className="relative border-l pb-4 pl-5 last:border-l-0 last:pb-0" style={{ borderColor: "var(--border-primary)" }}>
              <span
                className="absolute -left-[7px] top-0 h-3.5 w-3.5 rounded-full border-2"
                style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--accent)" }}
                aria-hidden="true"
              />
              <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{step.label}</p>
              <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{step.value}</p>
            </li>
          ))}
        </ol>

        <div className="mt-4 rounded-lg border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <p className="text-[10px] uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Verdict</p>
          <p className="mt-1 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {result.csl_verdict.detail}
          </p>
        </div>
      </div>
    </div>
  );
}
