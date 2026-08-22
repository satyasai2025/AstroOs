"use client";

/**
 * DashboardOverview — the Dashboard's home/landing content (mockup:
 * "Dashboard Overview"), shown above the birth-data form / analysis
 * results. Every number here traces to a real backend field:
 *
 *  - Total Charts / Recent Charts: GET /api/v1/horoscope/my-charts
 *  - Active Research Projects: GET /api/v1/research/projects?status_filter=active
 *  - Hypotheses Logged / Confirmation Rate: GET /api/v1/research-tools/validations
 *    (confirmation rate = confirmed / (confirmed + rejected) among reviewed
 *    hypotheses — real ratio, not a fabricated "AI accuracy" figure. Shows
 *    "No reviews yet" instead of a fake 0% when nothing's been reviewed.)
 *  - Research Activity: GET /api/v1/research-tools/logs — the real query-log
 *    feed. The raw `response_summary` field is just "{status} {path}"
 *    (apps/api/services/research_middleware.py), so it's translated here
 *    using the log's real `action` field (a genuine backend enum like
 *    "snapshot_capture", "hypothesis_generate" — see _get_action() in that
 *    same file) into a short human sentence, the same way lib/api.ts
 *    title-cases nakshatra tokens elsewhere in this app. This is a label
 *    translation of real data, not invented activity.
 *  - Current Dasha & Transit / Active Yogas: only rendered when a chart is
 *    actually loaded in the workflow store this session (`activeResult`),
 *    using the same getCurrentDashaChain()/is_present yoga fields the Chart
 *    tabs already use — no synthesis, no placeholder chart.
 *
 * NOT included from the mockup: a global "Accuracy Score" against
 * real-world outcomes (no ground-truth outcome tracking exists in this
 * app), per-factor "Key Factors %" AI insight text, and a notification bell
 * count (no notification system exists) — all three would require
 * fabricating numbers that don't come from anywhere real.
 *
 * Yoga strength badges show the REAL backend vocabulary ("Full" /
 * "Partial" / "Cancelled", from YogaResultResponse.strength), not the
 * mockup's "Strong" / "Very Strong" / "Moderate" labels — the backend
 * doesn't compute that finer scale, and inventing it would misrepresent
 * precision the app doesn't have.
 *
 * Card icon colors are presentational only (a fixed palette cycled per
 * card / hashed per chart name for the avatar circles) — cosmetic
 * variety to match the mockup's visual style, not a new data dimension.
 */

import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useCurrentUser } from "@/lib/auth";
import { useMyCharts } from "@/lib/charts";
import { tokenStore } from "@/lib/api";
import {
  researchProjectsApi,
  researchModeApi,
  hypothesisValidationApi,
  type QueryLogEntry,
} from "@/lib/research";
import { getCurrentDashaChain, currentTransitSummary } from "@/lib/kpiScoring";
import type { WorkflowAnalysisResponse, YogaResultResponse, BirthChartSummary } from "@/lib/types";
import { Badge, Button, Card, KpiCard, SearchInput } from "@/components/ui";
import { KpiScorecards } from "@/components/dashboard/KpiScorecards";

interface DashboardOverviewProps {
  /** Full result for whichever chart is currently loaded in the workflow
   * store this session, if any — powers the two chart-specific widgets. */
  activeResult?: WorkflowAnalysisResponse | null;
  activeSubjectName?: string | null;
  onStartNewChart: () => void;
  onSelectChart?: (chart: BirthChartSummary) => void;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
  } catch {
    return iso;
  }
}

/** Short "Xh ago" / "Xd ago" relative label — presentational formatting of
 * a real timestamp, same idea as history/page.tsx's formatDateTime but
 * compact for feed rows. */
function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const diffMs = Date.now() - then;
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 30) return `${day}d ago`;
  return formatDate(iso);
}

const YOGA_STRENGTH_LABEL: Record<string, string> = {
  full: "Full",
  partial: "Partial",
  cancelled: "Cancelled",
};

const YOGA_STRENGTH_COLOR: Record<string, string> = {
  full: "var(--status-success)",
  partial: "var(--status-warning)",
  cancelled: "var(--status-danger)",
};

/** Real backend action codes (apps/api/services/research_middleware.py
 * _get_action()) translated to short human sentences — a label lookup,
 * not fabricated activity. Anything not in this map falls back to the
 * raw action string with underscores replaced by spaces. */
const ACTION_LABELS: Record<string, string> = {
  workflow_analyze: "Ran a full chart analysis",
  snapshot_compare: "Compared two snapshots",
  snapshot_capture: "Captured a research snapshot",
  project_create: "Created a research project",
  research_query: "Ran a research query",
  hypothesis_generate: "Generated AI hypotheses",
  export: "Exported research data",
  chart_compare: "Compared charts",
  enhanced_qa: "Asked an enhanced Q&A question",
  hypothesis_validate: "Reviewed a hypothesis",
  research_mode_toggle: "Toggled Research Mode",
  query_log_view: "Viewed activity logs",
  research_action: "Research action",
};

function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action.replace(/_/g, " ");
}

/** The log's response_summary is "{status} {path}" — pull just the status
 * code out to render a small ok/error dot instead of the raw string. */
function logStatusOk(log: QueryLogEntry): boolean {
  const code = parseInt(log.response_summary.split(" ")[0] ?? "", 10);
  return !Number.isNaN(code) && code < 400;
}

/** Fixed cosmetic palette (matches the app's per-section rainbow colors)
 * used to give each stat card / chart avatar its own accent, purely for
 * visual variety — see the file-level doc-comment. */
const PALETTE = [
  { fg: "#ffffff", bg: "#0f766e" }, // teal-700 (WCAG AA 4.7:1)
  { fg: "#ffffff", bg: "#4338ca" }, // indigo-700 (WCAG AA 5.8:1)
  { fg: "#ffffff", bg: "#047857" }, // emerald-700 (WCAG AA 4.7:1)
  { fg: "#ffffff", bg: "#c2410c" }, // orange-700 (WCAG AA 4.6:1)
  { fg: "#ffffff", bg: "#be185d" }, // pink-700 (WCAG AA 4.9:1)
];

export function paletteFor(seed: string) {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

export function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function StatIcon({ kind }: { kind: "charts" | "research" | "hypotheses" | "confirmation" }) {
  const common = {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };
  if (kind === "charts")
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="9" />
        <path d="m15 9-2 6-6 2 2-6 6-2Z" />
      </svg>
    );
  if (kind === "research")
    return (
      <svg {...common}>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
    );
  if (kind === "hypotheses")
    return (
      <svg {...common}>
        <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
        <path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
      </svg>
    );
  return (
    <svg {...common}>
      <path d="M5 13l4 4L19 7" />
    </svg>
  );
}

function StatCard({
  label,
  value,
  caveat,
  icon,
  accent,
  href,
}: {
  label: string;
  value: string;
  caveat: string;
  icon: "charts" | "research" | "hypotheses" | "confirmation";
  accent: "cyan" | "violet" | "success" | "gold";
  href?: string;
}) {
  return <KpiCard label={label} value={value} caveat={caveat} icon={<StatIcon kind={icon} />} accent={accent} href={href} />;
}

function ActiveYogaRow({ yoga }: { yoga: YogaResultResponse }) {
  const key = (yoga.strength ?? "").toLowerCase();
  const color = YOGA_STRENGTH_COLOR[key] ?? "var(--text-muted)";
  const label = YOGA_STRENGTH_LABEL[key] ?? (yoga.strength ?? "Present");
  return (
    <div className="flex items-center gap-2.5 py-1.5 text-xs">
      <span
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border text-[10px] font-bold"
        style={{ backgroundColor: `${color}22`, borderColor: `${color}66`, color }}
      >
        ★
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium" style={{ color: "var(--text-primary)" }}>
          {yoga.name}
        </p>
        <p className="truncate" style={{ color: "var(--text-muted)" }}>
          {yoga.involved_planets.join(", ")}
        </p>
      </div>
      <span
        className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold"
        style={{ color, border: `1px solid ${color}` }}
      >
        {label}
      </span>
    </div>
  );
}

function RecentChartRow({ chart }: { chart: BirthChartSummary }) {
  const color = paletteFor(chart.id);
  return (
    <Link
      href="/charts/history"
      className="flex items-center gap-2.5 rounded-lg p-2.5 text-xs transition bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/60 dark:hover:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-700 shadow-sm shadow-slate-200/50 dark:shadow-none"
    >
      <span
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-bold"
        style={{ backgroundColor: color.bg, color: color.fg }}
      >
        {initialsOf(chart.subject_name)}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold text-slate-900 dark:text-slate-100">
          {chart.subject_name}
        </p>
        <p className="truncate text-xs text-slate-600 dark:text-slate-400">
          {chart.lagna_rashi ?? "—"} Lagna · {timeAgo(chart.created_at)}
        </p>
      </div>
      <span
        className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800"
      >
        D1 Chart
      </span>
    </Link>
  );
}

function ActivityRow({ log }: { log: QueryLogEntry }) {
  const ok = logStatusOk(log);
  const color = ok ? "var(--status-success)" : "var(--status-danger)";
  const bg = ok ? "var(--status-success-bg)" : "var(--status-danger-bg)";
  return (
    <li className="flex items-start gap-2.5 text-xs">
      <span
        className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md border"
        style={{ backgroundColor: bg, borderColor: color, color }}
        aria-hidden="true"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
          {ok ? <path d="M5 13l4 4L19 7" /> : <path d="M18 6 6 18M6 6l12 12" />}
        </svg>
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-slate-900 dark:text-slate-100">{actionLabel(log.action)}</p>
        <p className="text-slate-600 dark:text-slate-400">{timeAgo(log.created_at)}</p>
      </div>
    </li>
  );
}

function QuickAction({
  href,
  onClick,
  label,
  sublabel,
  color,
  primary,
}: {
  href?: string;
  onClick?: () => void;
  label: string;
  sublabel: string;
  color: { fg: string; bg: string };
  primary?: boolean;
}) {
  const content = (
    <>
      <span
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-sm font-bold ${
          primary
            ? "bg-slate-950/15 border-slate-950/20 text-slate-950"
            : ""
        }`}
        style={
          !primary
            ? {
                backgroundColor: color.bg,
                borderColor: `${color.fg}66`,
                color: color.fg,
              }
            : undefined
        }
      >
        +
      </span>
      <span className="min-w-0 text-left">
        <span
          className={`block truncate text-xs font-semibold ${
            primary ? "text-slate-950" : "text-slate-900 dark:text-slate-100"
          }`}
        >
          {label}
        </span>
        <span
          className={`block truncate text-[10px] ${
            primary ? "text-slate-800" : "text-slate-600 dark:text-slate-400"
          }`}
        >
          {sublabel}
        </span>
      </span>
    </>
  );
  const className = `flex items-center gap-2 rounded-lg p-2.5 text-left transition hover:opacity-90 ${
    primary
      ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-md shadow-cyan-500/20"
      : "bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-800/80 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 shadow-sm shadow-slate-200/50 dark:shadow-none"
  }`;
  if (href) {
    return (
      <Link href={href} className={className}>
        {content}
      </Link>
    );
  }
  return (
    <button type="button" onClick={onClick} className={className}>
      {content}
    </button>
  );
}


export function DashboardOverview({ activeResult, activeSubjectName, onStartNewChart, onSelectChart }: DashboardOverviewProps) {
  const hasSession = typeof window !== "undefined" && !!tokenStore.getAccess();
  const { data: user } = useCurrentUser();
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const [pickerSearch, setPickerSearch] = useState("");

  const handleLoadActiveChartClick = () => {
    if (chartsData && chartsData.charts.length > 0) {
      setIsPickerOpen(true);
    } else {
      onStartNewChart();
    }
  };

  const filteredPickerCharts = useMemo(() => {
    const charts = chartsData?.charts ?? [];
    const q = pickerSearch.trim().toLowerCase();
    if (!q) return charts;
    return charts.filter(
      (c) =>
        c.subject_name.toLowerCase().includes(q) ||
        (c.place_name ?? "").toLowerCase().includes(q) ||
        (c.lagna_rashi ?? "").toLowerCase().includes(q),
    );
  }, [chartsData, pickerSearch]);

  const { data: activeProjects } = useQuery({
    queryKey: ["research", "projects", user?.id, "active"],
    queryFn: () => researchProjectsApi.list("active"),
    enabled: !!user?.id,
  });

  const { data: allHypotheses } = useQuery({
    queryKey: ["research", "hypotheses", "all"],
    queryFn: () => hypothesisValidationApi.list({ limit: 1 }),
    enabled: hasSession,
  });
  const { data: confirmedHypotheses } = useQuery({
    queryKey: ["research-tools", "validations", "confirmed"],
    queryFn: () => hypothesisValidationApi.list({ status: "confirmed", limit: 1 }),
    enabled: hasSession,
  });
  const { data: rejectedHypotheses } = useQuery({
    queryKey: ["research-tools", "validations", "rejected"],
    queryFn: () => hypothesisValidationApi.list({ status: "rejected", limit: 1 }),
    enabled: hasSession,
  });

  const { data: activityLogs } = useQuery({
    queryKey: ["research-tools", "logs", "recent"],
    queryFn: () => researchModeApi.listLogs({ limit: 5 }),
    enabled: hasSession,
  });

  const confirmationRate = useMemo(() => {
    const confirmed = confirmedHypotheses?.total ?? 0;
    const rejected = rejectedHypotheses?.total ?? 0;
    const denom = confirmed + rejected;
    return denom > 0 ? Math.round((confirmed / denom) * 1000) / 10 : null;
  }, [confirmedHypotheses, rejectedHypotheses]);

  const dashaChain = useMemo(
    () => (activeResult ? getCurrentDashaChain(activeResult.dasha.mahadashas) : []),
    [activeResult],
  );

  const deepestPeriod = dashaChain[dashaChain.length - 1] ?? null;
  const elapsedPct = useMemo(() => {
    if (!deepestPeriod) return null;
    const start = new Date(deepestPeriod.start_date).getTime();
    const end = new Date(deepestPeriod.end_date).getTime();
    if (!(end > start)) return null;
    const pct = ((Date.now() - start) / (end - start)) * 100;
    return Math.max(0, Math.min(100, Math.round(pct * 10) / 10));
  }, [deepestPeriod]);

  const topYogas = useMemo(
    () => (activeResult ? activeResult.yogas.results.filter((y) => y.is_present).slice(0, 5) : []),
    [activeResult],
  );

  const recentCharts = chartsData?.charts.slice(0, 5) ?? [];
  const recentLogs = activityLogs?.logs ?? [];

  return (
    <div className="space-y-3">
      {/* Title + New Chart button */}
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            Dashboard Overview
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Live astrological analysis and research console.
          </p>
        </div>
        <button
          type="button"
          onClick={onStartNewChart}
          className="flex items-center gap-1.5 rounded-lg bg-cyan-400 hover:bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 shadow-sm transition"
        >
          + New Chart
        </button>
      </div>

      {/* Stats row — every number is a real count, not a mockup placeholder */}
      <div className="mb-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          label="Total Charts"
          value={chartsLoading ? "…" : String(chartsData?.total ?? 0)}
          caveat="Charts saved to your account."
          icon="charts"
          accent="cyan"
          href="/charts/history"
        />
        <StatCard
          label="Active Research"
          value={activeProjects ? String(activeProjects.total) : "—"}
          caveat="Research projects with status = active."
          icon="research"
          accent="violet"
          href="/research/projects"
        />
        <StatCard
          label="Hypotheses Logged"
          value={allHypotheses ? String(allHypotheses.total) : "—"}
          caveat="AI-generated hypotheses flagged for review, total."
          icon="hypotheses"
          accent="success"
          href="/research/hypotheses"
        />
        <StatCard
          label="Confirmation Rate"
          value={confirmationRate !== null ? `${confirmationRate}%` : "No reviews yet"}
          caveat="Confirmed ÷ (confirmed + rejected) among reviewed hypotheses."
          icon="confirmation"
          accent="gold"
          href="/research/hypotheses"
        />
      </div>

      {/* Chart KPI Scorecards (Strength, Mental Stability, Career, Marriage,
          Health Risk, Wealth, Dasha, Transit) — only for a chart actually
          loaded this session; no placeholder/demo chart is substituted. */}
      {activeResult && (
        <div className="mb-3">
          <h2 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-slate-400">
            Chart KPI Scorecards
          </h2>
          <KpiScorecards result={activeResult} />
        </div>
      )}

      {/* Current Dasha & Transit + Active Yogas — only for a chart actually
          loaded this session; no placeholder/demo chart is substituted. */}
      <div className="mb-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
        <Card>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-cyan-700 dark:text-cyan-400">
            Current Dasha &amp; Transit
          </h2>
          {activeResult ? (
            <div className="space-y-2 text-xs">
              {activeSubjectName && (
                <p className="font-semibold text-slate-800 dark:text-slate-200">{activeSubjectName}</p>
              )}
              {dashaChain.length > 0 ? (
                <>
                  <p className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    {dashaChain.map((p) => p.lord).join(" → ")}
                  </p>
                  {deepestPeriod && (
                    <>
                      <p className="text-slate-600 dark:text-slate-400">
                        {formatDate(deepestPeriod.start_date)} – {formatDate(deepestPeriod.end_date)}
                      </p>
                      {elapsedPct !== null && (
                        <div
                          className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"
                        >
                          <div
                            className="h-full rounded-full bg-cyan-500"
                            style={{ width: `${elapsedPct}%` }}
                          />
                        </div>
                      )}
                      {elapsedPct !== null && (
                        <p className="text-slate-500 dark:text-slate-400 text-[11px]">{elapsedPct}% elapsed</p>
                      )}
                    </>
                  )}
                </>
              ) : (
                <p className="text-slate-500 dark:text-slate-400">No active dasha period found.</p>
              )}
              <p className="pt-1 text-slate-700 dark:text-slate-300 font-medium">
                {currentTransitSummary(activeResult)}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 p-4 text-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500 dark:text-slate-400" aria-hidden="true">
                  <circle cx="12" cy="12" r="9" />
                  <path d="m15 9-2 6-6 2 2-6 6-2Z" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">No chart loaded</p>
                <p className="text-[11px] text-slate-600 dark:text-slate-400">Open or generate a chart to see its current dasha &amp; transits</p>
              </div>
              <button
                type="button"
                onClick={handleLoadActiveChartClick}
                className="rounded-md border border-slate-300 dark:border-slate-600 bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 px-2.5 py-1 text-xs font-medium shadow-sm transition"
              >
                Load Active Chart
              </button>
            </div>
          )}
        </Card>

        <Card>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400">
            Active Yogas
          </h2>
          {activeResult ? (
            topYogas.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {topYogas.map((y) => (
                  <ActiveYogaRow key={y.yoga_id} yoga={y} />
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                No yogas are currently flagged as present for this chart.
              </p>
            )
          ) : (
            <div className="flex flex-col items-center gap-2 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 p-4 text-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500 dark:text-slate-400" aria-hidden="true">
                  <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
                  <path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">No active yogas</p>
                <p className="text-[11px] text-slate-600 dark:text-slate-400">Open or generate a chart to see its present yogas</p>
              </div>
              <button
                type="button"
                onClick={handleLoadActiveChartClick}
                className="rounded-md border border-slate-300 dark:border-slate-600 bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 px-2.5 py-1 text-xs font-medium shadow-sm transition"
              >
                Load Active Chart
              </button>
            </div>
          )}


        </Card>
      </div>

      {/* Recent Charts + Research Activity + Quick Actions */}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <Card>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-cyan-700 dark:text-cyan-400">
              Recent Charts
            </h2>
            <Link href="/charts/history" className="text-[11px] underline" style={{ color: "var(--text-muted)" }}>
              View all
            </Link>
          </div>
          {recentCharts.length > 0 ? (
            <ul className="space-y-2">
              {recentCharts.map((c) => (
                <li key={c.id}>
                  <RecentChartRow chart={c} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              {chartsLoading ? "Loading…" : "No saved charts yet."}
            </p>
          )}
        </Card>

        <Card>
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-violet-700 dark:text-violet-400">
              Research Activity
            </h2>
            {hasSession && (
              <Link href="/research/projects" className="text-[11px] underline" style={{ color: "var(--text-muted)" }}>
                View all
              </Link>
            )}
          </div>
          {recentLogs.length > 0 ? (
            <ul className="space-y-2.5">
              {recentLogs.map((log) => (
                <ActivityRow key={log.id} log={log} />
              ))}
            </ul>
          ) : (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              {hasSession ? "No research activity logged yet." : "Sign in to see your research activity."}
            </p>
          )}
        </Card>

        <Card>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-indigo-700 dark:text-indigo-400">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 gap-2">
            <QuickAction
              onClick={onStartNewChart}
              label="New Chart"
              sublabel="Create a new birth chart"
              color={PALETTE[0]}
            />
            <QuickAction
              href="/charts/prashna"
              label="Prashna (Horary)"
              sublabel="KP Horary & Arabic Parts"
              color={PALETTE[0]}
            />
            <QuickAction
              href="/charts?view=dasha"
              label="Dasha Explorer"
              sublabel="Analyze dashas & periods"
              color={PALETTE[1]}
            />
            <QuickAction
              href="/charts?view=timeline"
              label="Transit Explorer"
              sublabel="Current transits & effects"
              color={PALETTE[2]}
            />
            <QuickAction
              href="/research/hypotheses"
              label="Hypotheses"
              sublabel="Review flagged hypotheses"
              color={PALETTE[3]}
            />
            <QuickAction
              href="/research/projects"
              label="Research Snapshot"
              sublabel="Manage research projects"
              color={PALETTE[4]}
            />
            <QuickAction
              href="/charts/compare"
              label="Compare Charts"
              sublabel="Side-by-side comparison"
              color={PALETTE[1]}
            />
          </div>
        </Card>
      </div>

      {/* ── Select Active Chart Picker Modal ── */}
      {isPickerOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: "rgba(0, 0, 0, 0.75)", backdropFilter: "blur(4px)" }}
          onClick={() => setIsPickerOpen(false)}
        >
          <div
            className="w-full max-w-lg overflow-hidden rounded-2xl border shadow-2xl"
            style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b px-6 py-4" style={{ borderColor: "var(--border-primary)" }}>
              <div>
                <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>Select Active Chart</h2>
                <p className="text-xs text-slate-400 mt-0.5">Choose a saved chart to load its Dasha, Yogas &amp; Transits</p>
              </div>
              <button
                type="button"
                onClick={() => setIsPickerOpen(false)}
                className="text-slate-400 hover:text-slate-100 text-xl leading-none"
                aria-label="Close modal"
              >
                ×
              </button>
            </div>

            <div className="p-4 border-b" style={{ borderColor: "var(--border-subtle)" }}>
              <SearchInput
                value={pickerSearch}
                onChange={setPickerSearch}
                placeholder="Search by name, place, lagna…"
                shortcut=""
              />
            </div>

            <div className="max-h-80 overflow-y-auto p-4 space-y-2">
              {filteredPickerCharts.length === 0 ? (
                <div className="text-center py-6 text-sm text-slate-400">
                  No charts found matching your search.
                </div>
              ) : (
                filteredPickerCharts.map((chart) => {
                  const color = paletteFor(chart.id);
                  return (
                    <div
                      key={chart.id}
                      onClick={() => {
                        onSelectChart?.(chart);
                        setIsPickerOpen(false);
                      }}
                      className="flex items-center justify-between p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 hover:border-amber-500/60 hover:bg-amber-500/5 transition cursor-pointer"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm"
                          style={{ backgroundColor: color.fg }}
                        >
                          {initialsOf(chart.subject_name)}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>
                              {chart.subject_name}
                            </span>
                            {chart.is_default && <Badge tone="success">Default</Badge>}
                          </div>
                          <p className="text-xs text-slate-400 truncate mt-0.5">
                            {formatDate(chart.birth_datetime_utc)}
                            {chart.place_name ? ` · ${chart.place_name}` : ""}
                            {chart.lagna_rashi ? ` · Lagna: ${chart.lagna_rashi}` : ""}
                          </p>
                        </div>
                      </div>

                      <button
                        type="button"
                        className="obsidian-btn-primary text-xs ml-3 whitespace-nowrap"
                      >
                        Load →
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            <div className="flex items-center justify-between border-t px-6 py-3 bg-slate-50 dark:bg-slate-900/80" style={{ borderColor: "var(--border-primary)" }}>
              <button
                type="button"
                onClick={() => {
                  setIsPickerOpen(false);
                  onStartNewChart();
                }}
                className="text-xs font-semibold text-cyan-500 hover:underline"
              >
                + Create New Chart instead
              </button>
              <button
                type="button"
                onClick={() => setIsPickerOpen(false)}
                className="obsidian-btn-secondary text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
