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

import { useMemo } from "react";
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
import { Button, Card, KpiCard } from "@/components/ui";
import { KpiScorecards } from "@/components/dashboard/KpiScorecards";

interface DashboardOverviewProps {
  /** Full result for whichever chart is currently loaded in the workflow
   * store this session, if any — powers the two chart-specific widgets. */
  activeResult?: WorkflowAnalysisResponse | null;
  activeSubjectName?: string | null;
  onStartNewChart: () => void;
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
  { fg: "#14b8a6", bg: "rgba(20, 184, 166, 0.15)" }, // teal
  { fg: "#6366f1", bg: "rgba(99, 102, 241, 0.15)" }, // indigo (spec: Accent Primary)
  { fg: "#10b981", bg: "rgba(16, 185, 129, 0.15)" }, // green (spec: Success/Strong)
  { fg: "#f97316", bg: "rgba(249, 115, 22, 0.15)" }, // orange
  { fg: "#ec4899", bg: "rgba(236, 72, 153, 0.15)" }, // pink
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


export function DashboardOverview({ activeResult, activeSubjectName, onStartNewChart }: DashboardOverviewProps) {
  const hasSession = typeof window !== "undefined" && !!tokenStore.getAccess();
  const { data: user } = useCurrentUser();
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();

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
    <div className="space-y-6">
      {/* Greeting */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Welcome back{user?.display_name ? `, ${user.display_name}` : ""} 👋
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Here&apos;s what&apos;s happening with your research.
          </p>
        </div>
        <button
          type="button"
          onClick={onStartNewChart}
          className="flex items-center gap-1.5 rounded-lg bg-cyan-400 hover:bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950 shadow-md shadow-cyan-400/20 transition"
        >
          + New Chart
        </button>
      </div>

      {/* Stats row — every number is a real count, not a mockup placeholder */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
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
        <div className="mb-6">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
            Chart KPI Scorecards
          </h3>
          <KpiScorecards result={activeResult} />
        </div>
      )}

      {/* Current Dasha & Transit + Active Yogas — only for a chart actually
          loaded this session; no placeholder/demo chart is substituted. */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--section-charts)" }}>
            Current Dasha &amp; Transit
          </h3>
          {activeResult ? (
            <div className="space-y-2 text-xs">
              {activeSubjectName && (
                <p style={{ color: "var(--text-muted)" }}>{activeSubjectName}</p>
              )}
              {dashaChain.length > 0 ? (
                <>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {dashaChain.map((p) => p.lord).join(" → ")}
                  </p>
                  {deepestPeriod && (
                    <>
                      <p style={{ color: "var(--text-muted)" }}>
                        {formatDate(deepestPeriod.start_date)} – {formatDate(deepestPeriod.end_date)}
                      </p>
                      {elapsedPct !== null && (
                        <div
                          className="h-1.5 w-full overflow-hidden rounded-full"
                          style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
                        >
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${elapsedPct}%`, backgroundColor: "var(--section-charts)" }}
                          />
                        </div>
                      )}
                      {elapsedPct !== null && (
                        <p style={{ color: "var(--text-muted)" }}>{elapsedPct}% elapsed</p>
                      )}
                    </>
                  )}
                </>
              ) : (
                <p style={{ color: "var(--text-muted)" }}>No active dasha period found.</p>
              )}
              <p className="pt-1" style={{ color: "var(--text-secondary)" }}>
                {currentTransitSummary(activeResult)}
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 p-6 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500 dark:text-slate-400" aria-hidden="true">
                  <circle cx="12" cy="12" r="9" />
                  <path d="m15 9-2 6-6 2 2-6 6-2Z" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">No chart loaded</p>
                <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">Open or generate a chart to see its current dasha &amp; transits</p>
              </div>
              <button
                type="button"
                onClick={onStartNewChart}
                className="rounded-md border border-slate-300 dark:border-slate-600 bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 px-3 py-1.5 text-xs font-medium shadow-sm transition"
              >
                Load Active Chart
              </button>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--success-400)" }}>
            Active Yogas
          </h3>
          {activeResult ? (
            topYogas.length > 0 ? (
              <div className="divide-y" style={{ borderColor: "var(--border-primary)" }}>
                {topYogas.map((y) => (
                  <ActiveYogaRow key={y.yoga_id} yoga={y} />
                ))}
              </div>
            ) : (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                No yogas are currently flagged as present for this chart.
              </p>
            )
          ) : (
            <div className="flex flex-col items-center gap-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 p-6 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500 dark:text-slate-400" aria-hidden="true">
                  <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
                  <path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-900 dark:text-slate-200">No active yogas</p>
                <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">Open or generate a chart to see its present yogas</p>
              </div>
              <button
                type="button"
                onClick={onStartNewChart}
                className="rounded-md border border-slate-300 dark:border-slate-600 bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 px-3 py-1.5 text-xs font-medium shadow-sm transition"
              >
                Load Active Chart
              </button>
            </div>
          )}


        </Card>
      </div>

      {/* Recent Charts + Research Activity + Quick Actions */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--section-charts)" }}>
              Recent Charts
            </h3>
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
            <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--section-research)" }}>
              Research Activity
            </h3>
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
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--section-ai)" }}>
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 gap-2">
            <QuickAction
              onClick={onStartNewChart}
              label="New Chart"
              sublabel="Create a new birth chart"
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
    </div>
  );
}
