"use client";

import { useState } from "react";
import type { RuleResultResponse } from "@/lib/types";

type Filter = "all" | "matched" | "unmatched";

export function RulesPanel({
  ruleResults,
  onExplain,
}: {
  ruleResults: RuleResultResponse[];
  onExplain?: (ruleId: string) => void;
}) {
  const [filter, setFilter] = useState<Filter>("matched");

  const matched = ruleResults.filter((r) => r.matched);
  const unmatched = ruleResults.filter((r) => !r.matched);
  const visible =
    filter === "all"
      ? ruleResults
      : filter === "matched"
        ? matched
        : unmatched;

  return (
    <div className="glass-card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80">
          Rule Engine
        </h3>
        <span className="text-xs text-slate-500">
          {matched.length} matched of {ruleResults.length} evaluated
        </span>
      </div>

      {/* Filter toggle */}
      <div className="mb-4 flex gap-1">
        {(["matched", "unmatched", "all"] as Filter[]).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            className={
              f === filter
                ? "rounded-md bg-amber-500 px-2.5 py-1 text-xs font-semibold text-cosmos-950"
                : "rounded-md px-2.5 py-1 text-xs text-slate-400 hover:bg-white/5 hover:text-slate-200"
            }
          >
            {f === "all"
              ? `All (${ruleResults.length})`
              : f === "matched"
                ? `Matched (${matched.length})`
                : `Unmatched (${unmatched.length})`}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <p className="text-sm text-slate-400">No rules in this view.</p>
      ) : (
        <ul className="space-y-3">
          {visible.map((r) => (
            <li key={r.rule_id} className="border-b border-white/5 pb-3 last:border-none">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`shrink-0 text-xs font-bold ${r.matched ? "text-emerald-400" : "text-slate-600"}`}
                    >
                      {r.matched ? "✓" : "✗"}
                    </span>
                    <span className="font-medium text-slate-100">{r.rule_name}</span>
                    <span className="rounded-full border border-cosmos-600/40 bg-cosmos-800/40 px-2 py-0.5 text-xs text-slate-400">
                      {r.rule_category}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{r.explanation}</p>
                  {/* failed conditions for unmatched */}
                  {!r.matched && r.failed_conditions.length > 0 && (
                    <ul className="mt-1 flex flex-wrap gap-1">
                      {r.failed_conditions.map((c) => (
                        <li
                          key={c}
                          className="rounded-md border border-red-800/30 bg-red-900/20 px-1.5 py-0.5 text-xs text-red-400"
                        >
                          ✗ {c}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                {onExplain && (
                  <button
                    type="button"
                    onClick={() => onExplain(r.rule_id)}
                    className="ml-2 shrink-0 rounded-md border border-amber-500/30 bg-amber-900/20 px-2 py-1 text-xs text-amber-300 hover:bg-amber-900/40 transition-colors"
                  >
                    Explain
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
