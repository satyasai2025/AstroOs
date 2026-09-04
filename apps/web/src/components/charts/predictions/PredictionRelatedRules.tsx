"use client";

import type { RelatedRuleEntry } from "@/lib/predictions/types";

interface PredictionRelatedRulesProps {
  rules: RelatedRuleEntry[];
}

/**
 * PredictionRelatedRules — real classical citations behind this chart's
 * matched yogas (YogaResultResponse.source_text/rule_version, already
 * computed by the backend's rule engine). AstroOS's honest answer to the
 * mockup's "Classical Rule IDs" panel: real source text for yogas that
 * actually matched this chart, never invented scripture references like
 * "BPHS 34.12" for factors that don't carry one.
 */
export function PredictionRelatedRules({ rules }: PredictionRelatedRulesProps) {
  return (
    <div className="glass-card flex flex-col gap-2 p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        Related Rules
      </h3>
      {rules.length === 0 ? (
        <p className="text-xs" style={{ color: "var(--text-muted)" }}>
          No matched yogas carry a classical citation for this chart.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {rules.map((r, i) => (
            <li key={`${r.yogaName}-${i}`} className="text-xs">
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>
                {r.yogaName}
              </span>
              <p style={{ color: "var(--text-muted)" }}>
                {r.sourceText} · {r.ruleVersion}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
