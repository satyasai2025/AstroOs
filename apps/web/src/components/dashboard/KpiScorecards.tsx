"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  overallStrengthScore,
  currentDasha,
  currentTransitSummary,
  careerIndex,
  marriageIndex,
  wealthPotential,
  mentalStability,
  healthRisk,
  educationIndex,
  childrenIndex,
  foreignIndex,
  spiritualityIndex,
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
  /** Links into the Prediction Chain Explorer for this KPI, pre-selected
   * to the matching life area — only set on Career/Marriage/Wealth, which
   * have a real chain. Strength Score/Mental Stability have no chain. */
  href?: string;
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
  href?: string;
}

type CardDef = PercentCardDef | TextCardDef | RiskCardDef;

const RISK_BADGES: Record<HealthRiskLabel, { text: string; bg: string; border: string }> = {
  Low: {
    text: "text-emerald-700 dark:text-emerald-300",
    bg: "bg-emerald-50 dark:bg-emerald-950/50",
    border: "border-emerald-300 dark:border-emerald-700",
  },
  Medium: {
    text: "text-amber-700 dark:text-amber-300",
    bg: "bg-amber-50 dark:bg-amber-950/50",
    border: "border-amber-300 dark:border-amber-700",
  },
  High: {
    text: "text-rose-700 dark:text-rose-300",
    bg: "bg-rose-50 dark:bg-rose-950/50",
    border: "border-rose-300 dark:border-rose-700",
  },
  Unknown: {
    text: "text-slate-600 dark:text-slate-400",
    bg: "bg-slate-100 dark:bg-slate-800",
    border: "border-slate-300 dark:border-slate-700",
  },
};

function percentColorClasses(value: number): { text: string; bg: string } {
  if (value >= 66) return { text: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500" };
  if (value >= 40) return { text: "text-amber-600 dark:text-amber-400", bg: "bg-amber-500" };
  return { text: "text-rose-600 dark:text-rose-400", bg: "bg-rose-500" };
}

function PercentCard({ label, value, caveat, href }: PercentCardDef) {
  const { text: colorClass, bg: barColorClass } = percentColorClasses(value);
  const content = (
    <>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
          {label}
        </span>
        <span className={`text-lg font-extrabold ${colorClass}`}>
          {value}%
        </span>
      </div>
      <div className="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <div className={`h-full rounded-full transition-all ${barColorClass}`} style={{ width: `${value}%` }} />
      </div>
      <p className="mt-2.5 text-[11px] font-medium leading-relaxed text-slate-600 dark:text-slate-400">
        {caveat}
      </p>
    </>
  );
  const cardClass = "flex flex-col justify-between rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm shadow-slate-200/50 dark:shadow-none transition hover:border-cyan-500/50";
  if (href) {
    return (
      <Link href={href} className={cardClass}>
        {content}
      </Link>
    );
  }
  return <div className={cardClass}>{content}</div>;
}

function TextCard({ label, value, caveat }: TextCardDef) {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm shadow-slate-200/50 dark:shadow-none">
      <div>
        <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
          {label}
        </span>
        <p className="mt-1.5 text-sm font-bold leading-snug text-cyan-600 dark:text-cyan-400">
          {value}
        </p>
      </div>
      <p className="mt-2.5 text-[11px] font-medium leading-relaxed text-slate-600 dark:text-slate-400">
        {caveat}
      </p>
    </div>
  );
}

function RiskCard({ label, value, caveat, href }: RiskCardDef) {
  const badge = RISK_BADGES[value] ?? RISK_BADGES.Unknown;
  const content = (
    <>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
          {label}
        </span>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold border ${badge.text} ${badge.bg} ${badge.border}`}
        >
          {value}
        </span>
      </div>
      <p className="mt-2.5 text-[11px] font-medium leading-relaxed text-slate-600 dark:text-slate-400">
        {caveat}
      </p>
    </>
  );
  const cardClass = "flex flex-col justify-between rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm shadow-slate-200/50 dark:shadow-none transition hover:border-cyan-500/50";
  if (href) {
    return (
      <Link href={href} className={cardClass}>
        {content}
      </Link>
    );
  }
  return <div className={cardClass}>{content}</div>;
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
        caveat: "Moon strength/dignity, Rahu/Ketu/Saturn affliction (Vish Yoga), Paksha Bala. Default weights, tunable.",
      },
      {
        kind: "percent",
        label: "Career Index",
        value: careerIndex(result),
        caveat: "10th-lord + Saturn/Sun strength, dignity, Raja Yoga, career yogas. Default weights, tunable.",
        href: "/predictions?kpi=career",
      },
      {
        kind: "percent",
        label: "Marriage Index",
        value: marriageIndex(result),
        caveat: "7th-lord + Venus/Jupiter strength, Manglik Dosha, 7th-house occupancy. Default weights, tunable.",
        href: "/predictions?kpi=marriage",
      },
      {
        kind: "risk",
        label: "Health Risk",
        value: healthRisk(result),
        caveat: "6th/1st/8th-lord weakness (weighted). Label, not a fabricated precise percentage.",
        href: "/predictions?kpi=health",
      },
      {
        kind: "percent",
        label: "Wealth Potential",
        value: wealthPotential(result),
        caveat: "2nd/11th-lord + Jupiter/Venus strength, Dhana Yoga bonus. Default weights, tunable.",
        href: "/predictions?kpi=wealth",
      },
      {
        kind: "percent",
        label: "Education",
        value: educationIndex(result),
        caveat: "5th-lord + Jupiter/Mercury strength. Default weights, tunable.",
        href: "/predictions?kpi=education",
      },
      {
        kind: "percent",
        label: "Children",
        value: childrenIndex(result),
        caveat: "5th-lord + Jupiter/Venus strength. Default weights, tunable.",
        href: "/predictions?kpi=children",
      },
      {
        kind: "percent",
        label: "Foreign Settlement",
        value: foreignIndex(result),
        caveat: "12th-lord + Rahu/Saturn strength. Default weights, tunable.",
        href: "/predictions?kpi=foreign",
      },
      {
        kind: "percent",
        label: "Spirituality",
        value: spiritualityIndex(result),
        caveat: "9th-lord + Jupiter/Ketu strength. Default weights, tunable.",
        href: "/predictions?kpi=spirituality",
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
      className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
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

