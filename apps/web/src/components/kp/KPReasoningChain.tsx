"use client";

/**
 * KP Evidence / Reasoning Chain — for a selected event, the full evidence
 * chain behind the verdict: required houses → primary cusp → CSL → CSL
 * Star Lord → CSL significations → RP intersection → timing. This is the
 * "every conclusion carries an evidence chain" layer. The complete chain
 * (steps, verdict, top significator, RP intersection, active dasha level)
 * arrives pre-computed from the backend KP engine.
 */

import { useState } from "react";
import { KP_EVENT_HOUSE_GROUPS, type KPEventKey } from "@/lib/kpSignificators";
import type { EventEvidenceResponse } from "@/lib/types";

interface Props {
  evidence: EventEvidenceResponse[];
}

export function KPReasoningChain({ evidence }: Props) {
  const [eventKey, setEventKey] = useState<KPEventKey>("career");
  const result =
    evidence.find((e) => e.eventKey === eventKey) ?? evidence[0] ?? null;

  if (!result) {
    return (
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        No evidence chain returned by the engine for this chart.
      </p>
    );
  }

  const steps = result.steps.length
    ? result.steps
    : [
        { label: "Required Houses", value: result.houses.join(", ") },
        { label: "Primary Cusp", value: `House ${result.primary_cusp}` },
        { label: "CSL (Sub Lord)", value: result.csl_verdict.csl || "—" },
        { label: "CSL Star Lord", value: result.csl_verdict.csl_star_lord || "—" },
        {
          label: "CSL Significations",
          value: result.csl_verdict.csl_signifies.length ? result.csl_verdict.csl_signifies.join(", ") : "—",
        },
        {
          label: "Required ∩ CSL",
          value: result.csl_verdict.required_houses.filter((h) => result.csl_verdict.csl_signifies.includes(h)).join(", ") || "—",
        },
        {
          label: "RP Intersection",
          value: result.fruitful_rp_intersection.length ? result.fruitful_rp_intersection.join(", ") : "—",
        },
        {
          label: "Timing (Dasha)",
          value: result.active_dasha_level ?? "Not in active dasha period",
        },
      ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {(Object.keys(KP_EVENT_HOUSE_GROUPS) as KPEventKey[]).map((key) => {
          const entry = evidence.find((e) => e.eventKey === key);
          return (
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
              {entry?.label ?? KP_EVENT_HOUSE_GROUPS[key].label}
            </button>
          );
        })}
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
          {steps.map((step) => (
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
            {result.verdict_detail}
          </p>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {result.top_significator && (
            <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: "rgba(52,211,153,0.15)", color: "#34d399" }}>
              Top significator: {result.top_significator}
            </span>
          )}
          {result.fruitful_rp_intersection.length > 0 && (
            <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: "rgba(96,165,250,0.15)", color: "#60a5fa" }}>
              RP ∩ significators: {result.fruitful_rp_intersection.join(", ")}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
