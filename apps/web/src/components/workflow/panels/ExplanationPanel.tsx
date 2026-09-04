"use client";

import type { ExplanationResponse, ConditionExplanationResponse } from "@/lib/types";

function ConditionRow({ c }: { c: ConditionExplanationResponse }) {
  return (
    <li className="flex items-start gap-2 py-1 text-xs">
      <span
        className={
          c.satisfied
            ? "mt-0.5 shrink-0 text-emerald-400"
            : "mt-0.5 shrink-0 text-red-400"
        }
      >
        {c.satisfied ? "✓" : "✗"}
      </span>
      <div className="min-w-0">
        <span className="font-medium text-slate-200">{c.condition_text}</span>
        <span className="ml-1 text-slate-500">
          ({c.fact_key}: got&nbsp;{c.actual_value}, expected&nbsp;
          {c.operator}&nbsp;{c.expected_value})
        </span>
      </div>
    </li>
  );
}

export function ExplanationPanel({
  explanation,
  onClose,
}: {
  explanation: ExplanationResponse;
  onClose?: () => void;
}) {
  const confidenceColor =
    explanation.confidence === "high"
      ? "text-emerald-400"
      : explanation.confidence === "medium"
        ? "text-amber-400"
        : "text-slate-400";

  return (
    <div className="glass-card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">
            {explanation.rule_name}
          </h3>
          <span className="text-xs text-slate-500">{explanation.rule_id}</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full border border-white/10 px-2 py-0.5 text-xs ${confidenceColor}`}
          >
            confidence: {explanation.confidence}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              explanation.matched
                ? "bg-emerald-900/40 text-emerald-300"
                : "bg-red-900/40 text-red-300"
            }`}
          >
            {explanation.matched ? "matched" : "no match"}
          </span>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="ml-2 text-slate-500 hover:text-slate-200 text-xs"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      <p className="text-xs text-slate-400">{explanation.summary}</p>

      {/* Conditions */}
      {explanation.conditions.length > 0 && (
        <div>
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-300/70">
            Conditions
          </h4>
          <ul className="divide-y divide-white/5">
            {explanation.conditions.map((c, i) => (
              <ConditionRow key={i} c={c} />
            ))}
          </ul>
        </div>
      )}

      {/* Derived facts */}
      {Object.keys(explanation.derived_facts).length > 0 && (
        <div>
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-300/70">
            Derived Facts
          </h4>
          <ul className="space-y-0.5">
            {Object.entries(explanation.derived_facts).map(([k, v]) => (
              <li key={k} className="flex items-baseline gap-2 text-xs">
                <span className="font-mono text-slate-400">{k}</span>
                <span className="text-slate-200">{String(v)}</span>
                {explanation.derived_fact_sources[k] && (
                  <span className="text-slate-600">
                    via {explanation.derived_fact_sources[k]}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Locked facts */}
      {explanation.locked_facts.length > 0 && (
        <div>
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-300/70">
            Locked (priority conflict)
          </h4>
          <ul className="flex flex-wrap gap-1">
            {explanation.locked_facts.map((f) => (
              <li
                key={f}
                className="rounded-md border border-amber-600/30 bg-amber-900/20 px-2 py-0.5 font-mono text-xs text-amber-400"
              >
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Explanation text */}
      {explanation.explanation_text && (
        <p className="rounded-md border border-white/5 bg-white/5 px-3 py-2 text-xs text-slate-300">
          {explanation.explanation_text}
        </p>
      )}
    </div>
  );
}
