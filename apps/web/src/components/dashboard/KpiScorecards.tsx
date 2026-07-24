"use client";

import { useMemo } from "react";
import {
  overallStrengthScore,
  currentDasha,
  currentTransitSummary,
  careerIndex,
  marriageIndex,
  wealthPotential,
  mentalStability,
  healthRisk,
  type HealthRiskLabel,
} from "@/lib/kpiScoring";
import type { WorkflowAnalysisResponse } from "@/lib/types";

export interface KpiScorecardsProps {
  /** Full workflow analysis response for the currently-analyzed chart. */
  result: WorkflowAnalysisResponse;
}

interface PercentCardDef {
  kind: "percent";
  label: string;
  value: number;
  caveat: string;
}

interface TextCardDef {
  kind: "text";
  label: string;
  value: string;
  caveat: string;
}

interface RiskCardDef {
  kind: "risk";
  label: string;
  value: HealthRiskLabel;
  caveat: string;
}

type CardDef = PercentCardDef | TextCardDef | RiskCardDef;

const RISK_COLORS: Record<HealthRiskLabel, string> = {
  Low: "#34d399",
  Medium: "#fbbf24",
  High: "#f87171",
  Unknown: "var(--text-muted)",
};

/** Percentage color ramp — low scores read as warning-toned, high scores as
 * accent/positive. Purely presentational, not a new scoring rule. */
function percentColor(value: number): string {
  if (value >= 66) return "#34d399";
  if (value >= 40) return "#fbbf24";
  return "#f87171";
}

function PercentCard({ label, value, caveat }: PercentCardDef) {
  const color = percentColor(value);
  return (
    <div
      className="glass-card flex flex-col justify-between p-4"
      style={{ borderColor: "var(--border-primary)" }}
    >
      <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        {label}
      </span>
      <span className="mt-2 text-2xl font-bold" style={{ color }}>
        {value}%
      </span>
      <div
        className="mt-2 h-1.5 w-full overflow-hidden rounded-full"
        style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
      >
        <div className="h-full rounded-full" style={{ width: `${value}%`, backgroundColor: color }} />
      </div>
      <p className="mt-2 text-[10px] leading-snug" style={{ color: "var(--text-muted)" }}>
        {caveat}
      </p>
    </div>
  );
}

function TextCard({ label, value, caveat }: TextCardDef) {
  return (
    <div
      className="glass-card flex flex-col justify-between p-4"
      style={{ borderColor: "var(--border-primary)" }}
    >
      <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        {label}
      </span>
      <span className="mt-2 text-sm font-semibold leading-snug" style={{ color: "var(--accent)" }}>
        {value}
      </span>
      <p className="mt-2 text-[10px] leading-snug" style={{ color: "var(--text-muted)" }}>
        {caveat}
      </p>
    </div>
  );
}

function RiskCard({ label, value, caveat }: RiskCardDef) {
  const color = RISK_COLORS[value];
  return (
    <div
      className="glass-card flex flex-col justify-between p-4"
      style={{ borderColor: "var(--border-primary)" }}
    >
      <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        {label}
      </span>
      <span
        className="mt-2 inline-flex w-fit items-center rounded-full px-2.5 py-0.5 text-sm font-bold"
        style={{ color, border: `1px solid ${color}` }}
      >
        {value}
      </span>
      <p className="mt-2 text-[10px] leading-snug" style={{ color: "var(--text-muted)" }}>
        {caveat}
      </p>
    </div>
  );
}

/**
 * KpiScorecards — Dashboard KPI scorecard row from ASTROOS_VISION_V3_ROADMAP.md
 * Phase 2: Strength Score, Mental Stability, Career Index, Marriage Index,
 * Health Risk, Wealth Potential, Current Dasha, Current Transit.
 *
 * Strength Score / Current Dasha / Current Transit are read directly off
 * existing backend fields (see lib/kpiScoring.ts doc-comments for exact
 * fields). Career / Marriage / Wealth / Mental Stability / Health Risk are
 * synthesized indices using DOCUMENTED DEFAULT HEURISTIC WEIGHTS — every
 * card's small caption states that the weighting is an adjustable default,
 * not a claim of classical astrological authority. See lib/kpiScoring.ts
 * for the full formula documentation and tunable constants.
 *
 * Usage: <KpiScorecards result={workflowAnalysisResponse} />
 */
export function KpiScorecards({ result }: KpiScorecardsProps) {
  const cards = useMemo<CardDef[]>(() => {
    return [
      {
        kind: "percent",
        label: "Strength Score",
        value: overallStrengthScore(result),
        caveat: "Average of all planet_strengths (0-10 scale) from this chart, as a percentage.",
      },
      {
        kind: "percent",
        label: "Mental Stability",
        value: mentalStability(result),
        caveat: "Moon strength + dignity, adjusted for Rahu/Ketu affliction. Default heuristic weights, tunable.",
      },
      {
        kind: "percent",
        label: "Career Index",
        value: careerIndex(result),
        caveat: "10th-lord strength + career-yoga bonus. Default heuristic weights, not classical authority.",
      },
      {
        kind: "percent",
        label: "Marriage Index",
        value: marriageIndex(result),
        caveat: "7th-lord strength + Venus/Jupiter strength. Default heuristic weights, tunable.",
      },
      {
        kind: "risk",
        label: "Health Risk",
        value: healthRisk(result),
        caveat: "6th-lord + Ascendant-lord weakness. Label, not a fabricated precise percentage.",
      },
      {
        kind: "percent",
        label: "Wealth Potential",
        value: wealthPotential(result),
        caveat: "2nd/11th-lord strength + Jupiter/Venus strength. Default heuristic weights, tunable.",
      },
      {
        kind: "text",
        label: "Current Dasha",
        value: currentDasha(result),
        caveat: "Mahadasha / Antardasha whose dates bracket today, from the dasha tree.",
      },
      {
        kind: "text",
        label: "Current Transit",
        value: currentTransitSummary(result),
        caveat: "Plain readout of transit flags — not a fabricated Strong/Weak verdict.",
      },
    ];
  }, [result]);

  return (
    <div
      className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-4 xl:grid-cols-8"
      role="region"
      aria-label="Chart KPI scorecards"
    >
      {cards.map((card) => {
        if (card.kind === "percent") return <PercentCard key={card.label} {...card} />;
        if (card.kind === "risk") return <RiskCard key={card.label} {...card} />;
        return <TextCard key={card.label} {...card} />;
      })}
    </div>
  );
}
