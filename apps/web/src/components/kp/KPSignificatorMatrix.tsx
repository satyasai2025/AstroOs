"use client";

/**
 * KP Significator Matrix — the full 12-house significator table from the
 * shared A/B/C/D grading engine, presented as a ranked matrix with the
 * strongest significators first.
 */

import { useMemo } from "react";
import { getHouseSignificators } from "@/lib/kpAnalysis";
import { GRADE_LABELS, type SignificatorGrade } from "@/lib/kpSignificators";
import type { D1ChartResponse } from "@/lib/types";

interface Props {
  chart: D1ChartResponse;
}

const GRADE_RANK: Record<SignificatorGrade, number> = { A: 4, B: 3, C: 2, D: 1 };
const GRADE_COLOR: Record<SignificatorGrade, string> = {
  A: "#34d399",
  B: "#60a5fa",
  C: "#fbbf24",
  D: "#f87171",
};

function GradeBadge({ grade }: { grade: SignificatorGrade }) {
  return (
    <span
      className="inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold"
      style={{ backgroundColor: `${GRADE_COLOR[grade]}26`, color: GRADE_COLOR[grade] }}
      title={GRADE_LABELS[grade]}
    >
      {grade}
    </span>
  );
}

export function KPSignificatorMatrix({ chart }: Props) {
  const houses = useMemo(() => getHouseSignificators(chart), [chart]);

  return (
    <div className="space-y-4">
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        Every house&apos;s significators, ranked strongest grade first, per the classical KP grading
        (A — in the Star of a house occupant, B — occupies the house, C — in the Star of the Sign
        Lord, D — is the Sign Lord). Click a badge title for its exact definition.
      </p>
      {houses.map((hs) => {
        const sorted = hs.significators.slice().sort((a, b) => {
          const bestA = Math.max(...a.grades.map((g) => GRADE_RANK[g]));
          const bestB = Math.max(...b.grades.map((g) => GRADE_RANK[g]));
          return bestB - bestA;
        });
        return (
          <div key={hs.houseNumber} className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
            <p className="mb-1 text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
              House {hs.houseNumber} ({hs.rashi ?? "—"}) — Lord: {hs.lord ?? "—"}
              {hs.occupants.length > 0 && (
                <span style={{ color: "var(--text-muted)" }}> · Occupants: {hs.occupants.join(", ")}</span>
              )}
            </p>
            <div className="flex flex-wrap gap-2">
              {sorted.length === 0 && (
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>No significators found.</span>
              )}
              {sorted.map((sig) => (
                <span
                  key={sig.planet}
                  className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
                  style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}
                >
                  {sig.planet}
                  {sig.grades.map((g) => (
                    <GradeBadge key={g} grade={g} />
                  ))}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
