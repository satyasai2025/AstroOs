"use client";

import { useState } from "react";
import Image from "next/image";
import { GuruResearchLayer } from "../research/GuruResearchLayer";

/* ------------------------------------------------------------------ */
/*  Types & Mock Data                                                 */
/* ------------------------------------------------------------------ */

interface MetricCard {
  label: string;
  value: number | string;
  change?: string;
  icon: string;
}

interface QuickAction {
  label: string;
  href: string;
  icon: string;
  description?: string;
}

interface DatasetRow {
  id: string;
  name: string;
  charts: number;
  lastAnalyzed: string;
  tags: string[];
  status: "ready" | "processing" | "error";
}

interface PatternShowcase {
  title: string;
  description: string;
  confidence: number;
  exampleChart: string;
}

const mockMetrics: MetricCard[] = [
  { label: "Charts Analyzed", value: "12,847", change: "+12% this week", icon: "chart" },
  { label: "Yogas Detected", value: "3,592", change: "+156 new", icon: "star" },
  { label: "Rules Fired", value: "48,201", change: "+2,340 today", icon: "target" },
  { label: "Research Datasets", value: "86", change: "3 active projects", icon: "database" },
];

const quickActions: QuickAction[] = [
  { label: "New Chart Analysis", href: "/charts?view=chart", icon: "plus", description: "Analyze a new birth chart" },
  { label: "Reverse Search", href: "/research/reverse-search", icon: "search", description: "Find charts by pattern" },
  { label: "Pattern Discovery", href: "/research/patterns", icon: "sparkle", description: "AI-powered pattern detection" },
  { label: "Knowledge Graph", href: "/knowledge-graph", icon: "network", description: "Explore astrological relationships" },
  { label: "Compare Charts", href: "/charts/compare", icon: "layers", description: "Side-by-side analysis" },
  { label: "Export Report", href: "/reports/pdf", icon: "download", description: "Generate PDF report" },
];

const mockDatasets: DatasetRow[] = [
  { id: "ds-1", name: "Celebrity Natal Charts", charts: 342, lastAnalyzed: "2 hours ago", tags: ["Natal", "Celebrity"], status: "ready" },
  { id: "ds-2", name: "Marriage Timings Study", charts: 128, lastAnalyzed: "1 day ago", tags: ["Marriage", "Timing"], status: "processing" },
  { id: "ds-3", name: "Career Yogis Analysis", charts: 256, lastAnalyzed: "3 days ago", tags: ["Career", "Yogas"], status: "ready" },
  { id: "ds-4", name: "Health & Longevity", charts: 89, lastAnalyzed: "1 week ago", tags: ["Health", "Longevity"], status: "error" },
  { id: "ds-5", name: "Transit Patterns 2024", charts: 512, lastAnalyzed: "5 hours ago", tags: ["Transit", "2024"], status: "ready" },
];

const patternShowcase: PatternShowcase[] = [
  {
    title: "Raja Yoga Detection",
    description: "Combination of planets indicating royal status, leadership, or exceptional success",
    confidence: 94,
    exampleChart: "/demo/raja-yoga.svg",
  },
  {
    title: "Sanyasa Yoga",
    description: "Indications of renunciation, spiritual inclination, and detachment",
    confidence: 87,
    exampleChart: "/demo/sanyasa.svg",
  },
  {
    title: "Dhana Yoga",
    description: "Wealth-generating combinations in the birth chart",
    confidence: 91,
    exampleChart: "/demo/dhana.svg",
  },
];

/* ------------------------------------------------------------------ */
/*  Icon Components                                                  */
/* ------------------------------------------------------------------ */

function Icon({ name, className = "" }: { name: string; className?: string }) {
  const cls = className || "h-5 w-5 flex-shrink-0";
  const common = {
    width: 20,
    height: 20,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className: cls,
    "aria-hidden": true as const,
  };

  switch (name) {
    case "chart":
      return <svg {...common}><path d="M3 3v18h18" /><path d="m19 9-5 5-4-4-3 3" /></svg>;
    case "star":
      return <svg {...common}><path d="m12 3 2.6 6.2L21 10l-5 4.3L17.4 21 12 17.5 6.6 21 8 14.3 3 10l6.4-.8L12 3Z" /></svg>;
    case "target":
      return <svg {...common}><circle cx="12" cy="12" r="3" /><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="0.6" fill="currentColor" /></svg>;
    case "database":
      return <svg {...common}><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" /></svg>;
    case "plus":
      return <svg {...common}><path d="M12 5v14M5 12h14" /></svg>;
    case "search":
      return <svg {...common}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>;
    case "sparkle":
      return <svg {...common}><path d="M12 3v4M12 17v4M3 12h4M17 12h4" /><path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" /></svg>;
    case "network":
      return <svg {...common}><circle cx="6" cy="6" r="2.3" /><circle cx="18" cy="6" r="2.3" /><circle cx="12" cy="18" r="2.3" /><path d="M8 7.2 16 7.2M7 8l4 8M17 8l-4 8" /></svg>;
    case "layers":
      return <svg {...common}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M12 8v8" /><path d="M8 12h8" /></svg>;
    case "download":
      return <svg {...common}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>;
    case "activity":
      return <svg {...common}><path d="M22 12h-2.48a4 4 0 0 0-7.52 4 4 4 0 0 0-2.14-.88" /><path d="M15 12V7a2 2 0 0 0-2-2H3a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" /><circle cx="12" cy="12" r="3" /><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" /></svg>;
    default:
      return <svg {...common}><circle cx="12" cy="12" r="3" /></svg>;
  }
}

/* ------------------------------------------------------------------ */
/*  Metric Card                                                       */
/* ------------------------------------------------------------------ */

function MetricCard({ metric }: { metric: MetricCard }) {
  return (
    <div
      className="obsidian-card flex items-center gap-4 p-4"
      style={{ backgroundColor: "var(--obsidian-surface)" }}
    >
      <div
        className="obsidian-icon-bg flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl"
        style={{ backgroundColor: "var(--obsidian-status-success-bg)", color: "var(--obsidian-accent-success)" }}
      >
        <Icon name={metric.icon} className="h-6 w-6" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs uppercase tracking-wider" style={{ color: "var(--obsidian-text-muted)" }}>
          {metric.label}
        </p>
        <p className="text-2xl font-bold leading-none mt-1" style={{ color: "var(--obsidian-text-primary)" }}>
          {metric.value}
        </p>
        {metric.change && (
          <p className="mt-1 text-xs" style={{ color: "var(--obsidian-status-success)" }}>
            {metric.change}
          </p>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Quick Actions Bar                                                 */
/* ------------------------------------------------------------------ */

function QuickActions() {
  return (
    <div className="obsidian-card" style={{ backgroundColor: "var(--obsidian-surface)" }}>
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: "var(--obsidian-border)" }}>
        <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--obsidian-text-primary)" }}>
          Quick Actions
        </h3>
        <button
          className="text-xs font-medium transition-colors"
          style={{ color: "var(--obsidian-accent-primary)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--obsidian-accent-hover)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--obsidian-accent-primary)")}
        >
          Customize
        </button>
      </div>
      <div className="grid grid-cols-2 gap-2 p-4 sm:grid-cols-3 lg:grid-cols-6">
        {quickActions.map((action) => (
          <a
            key={action.label}
            href={action.href}
            className="group flex flex-col items-center gap-2 rounded-lg p-3 text-center transition-all"
            style={{
              border: "1px solid var(--obsidian-border)",
              backgroundColor: "var(--obsidian-surface)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--obsidian-accent-primary)";
              e.currentTarget.style.backgroundColor = "var(--obsidian-border)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--obsidian-border)";
              e.currentTarget.style.backgroundColor = "var(--obsidian-surface)";
            }}
          >
            <div
              className="obsidian-icon-bg flex h-10 w-10 items-center justify-center rounded-lg"
              style={{ color: "var(--obsidian-accent-primary)" }}
            >
              <Icon name={action.icon} className="h-5 w-5" />
            </div>
            <span className="text-xs font-medium leading-tight" style={{ color: "var(--obsidian-text-primary)" }}>
              {action.label}
            </span>
            {action.description && (
              <span className="text-[10px]" style={{ color: "var(--obsidian-text-muted)" }}>
                {action.description}
              </span>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Recent Datasets Table                                             */
/* ------------------------------------------------------------------ */

function RecentDatasets() {
  const getStatusStyle = (status: DatasetRow["status"]) => {
    switch (status) {
      case "ready":
        return { bg: "var(--obsidian-status-success-bg)", text: "var(--obsidian-accent-success)", label: "Ready" };
      case "processing":
        return { bg: "rgba(245, 158, 11, 0.2)", text: "#f59e0b", label: "Processing" };
      case "error":
        return { bg: "var(--obsidian-status-danger-bg)", text: "#f87171", label: "Error" };
    }
  };

  return (
    <div className="obsidian-card overflow-hidden" style={{ backgroundColor: "var(--obsidian-surface)" }}>
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: "var(--obsidian-border)" }}>
        <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: "var(--obsidian-text-primary)" }}>
          Recent Datasets
        </h3>
        <button
          className="text-xs font-medium transition-colors"
          style={{ color: "var(--obsidian-accent-primary)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--obsidian-accent-hover)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--obsidian-accent-primary)")}
        >
          View All
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: "1px solid var(--obsidian-border)" }}>
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--obsidian-text-muted)" }}>
                Dataset Name
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--obsidian-text-muted)" }}>
                Charts
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--obsidian-text-muted)" }}>
                Last Analyzed
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--obsidian-text-muted)" }}>
                Tags
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--obsidian-text-muted)" }}>
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {mockDatasets.map((dataset, idx) => {
              const statusStyle = getStatusStyle(dataset.status);
              return (
                <tr
                  key={dataset.id}
                  className="group transition-colors"
                  style={{ borderBottom: idx < mockDatasets.length - 1 ? "1px solid var(--obsidian-border)" : "none" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--obsidian-border)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  <td className="px-4 py-3">
                    <a
                      href={`/research/projects/${dataset.id}`}
                      className="text-sm font-medium transition-colors"
                      style={{ color: "var(--obsidian-text-primary)" }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--obsidian-accent-primary)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--obsidian-text-primary)")}
                    >
                      {dataset.name}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-sm" style={{ color: "var(--obsidian-text-secondary)" }}>
                    {dataset.charts.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm" style={{ color: "var(--obsidian-text-muted)" }}>
                    {dataset.lastAnalyzed}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {dataset.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded px-1.5 py-0.5 text-[10px] font-medium"
                          style={{ border: "1px solid var(--obsidian-border)", color: "var(--obsidian-text-muted)" }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-flex items-center rounded-full px-2 py-1 text-[11px] font-medium"
                      style={{ backgroundColor: statusStyle.bg, color: statusStyle.text }}
                    >
                      {statusStyle.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Pattern Showcase                                                  */
/* ------------------------------------------------------------------ */

function PatternShowcaseCard({ pattern }: { pattern: PatternShowcase }) {
  const [imageError, setImageError] = useState(false);

  return (
    <div className="obsidian-card" style={{ backgroundColor: "var(--obsidian-surface)" }}>
      {/* Placeholder chart visualization */}
      <div className="relative h-32 w-full overflow-hidden rounded-t-lg border-b" style={{ borderColor: "var(--obsidian-border)", backgroundColor: "var(--obsidian-canvas)" }}>
        {/* Simulated chart with CSS */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative h-24 w-24">
            {/* Concentric circles for zodiac */}
            <div className="absolute inset-0 rounded-full border" style={{ borderColor: "var(--obsidian-border)", borderStyle: "dashed" }} />
            <div className="absolute inset-2 rounded-full border" style={{ borderColor: "var(--obsidian-border)", borderStyle: "dotted", opacity: 0.6 }} />
            <div className="absolute inset-4 rounded-full border" style={{ borderColor: "var(--obsidian-border)", borderStyle: "dotted", opacity: 0.4 }} />
            {/* 12 houses */}
            {Array.from({ length: 12 }).map((_, i) => (
              <div
                key={i}
                className="absolute left-1/2 top-1/2 h-1/2 w-0.5 origin-bottom"
                style={{
                  backgroundColor: "var(--obsidian-accent-primary)",
                  transform: `rotate(${i * 30}deg)`,
                  opacity: 0.5,
                }}
              />
            ))}
            {/* Central pattern indicator */}
            <div
              className="absolute left-1/2 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full animate-pulse"
              style={{ backgroundColor: "var(--obsidian-accent-success)" }}
            />
          </div>
        </div>
        {/* Confidence badge */}
        <div
          className="absolute right-2 top-2 rounded px-2 py-1 text-[10px] font-bold uppercase"
          style={{ backgroundColor: "var(--obsidian-status-success-bg)", color: "var(--obsidian-accent-success)" }}
        >
          {pattern.confidence}% Match
        </div>
      </div>

      {/* Content */}
      <div className="p-3">
        <h4
          className="text-sm font-bold leading-tight mb-1"
          style={{ color: "var(--obsidian-text-primary)" }}
        >
          {pattern.title}
        </h4>
        <p className="text-xs leading-relaxed mb-3 line-clamp-2" style={{ color: "var(--obsidian-text-secondary)" }}>
          {pattern.description}
        </p>
        <button
          className="w-full rounded py-1.5 text-xs font-medium transition-all"
          style={{
            border: "1px solid var(--obsidian-accent-primary)",
            color: "var(--obsidian-accent-primary)",
            backgroundColor: "transparent",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--obsidian-accent-primary)";
            e.currentTarget.style.color = "var(--obsidian-accent-text)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.color = "var(--obsidian-accent-primary)";
          }}
        >
          Analyze Pattern
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Dashboard                                                    */
/* ------------------------------------------------------------------ */

export default function ResearchDashboard() {
  return (
    <div className="flex h-full flex-col gap-4 p-4 overflow-y-auto">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1
            className="text-2xl font-bold tracking-tight"
            style={{ color: "var(--obsidian-text-primary)" }}
          >
            Research Dashboard
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--obsidian-text-secondary)" }}>
            Overview of your Vedic astrology research activities and findings
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            className="obsidian-btn-primary"
            style={{ backgroundColor: "var(--obsidian-accent-primary)" }}
          >
            <Icon name="plus" className="h-4 w-4" />
            New Analysis
          </button>
          <button
            className="obsidian-btn-ghost"
            style={{ borderColor: "var(--obsidian-border)" }}
          >
            <Icon name="download" className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* ── Metrics Grid ── */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {mockMetrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </div>

      {/* ── Quick Actions ── */}
      <QuickActions />

      {/* ── Guru Research Layer (Teacher Research Slices) ── */}
      <GuruResearchLayer />

      {/* ── Main Content Grid (Datasets + Showcase) ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* ── Recent Datasets (2/3 width) ── */}
        <div className="lg:col-span-2" style={{ minWidth: 0 }}>
          <RecentDatasets />
        </div>

        {/* ── Pattern Showcase (1/3 width) ── */}
        <div className="flex flex-col gap-3" style={{ minWidth: 0 }}>
          <h3
            className="text-sm font-bold uppercase tracking-wider px-1"
            style={{ color: "var(--obsidian-text-primary)" }}
          >
            Live Pattern Detection
          </h3>
          {patternShowcase.map((pattern) => (
            <PatternShowcaseCard key={pattern.title} pattern={pattern} />
          ))}
        </div>
      </div>

      {/* ── Footer ── */}
      <div className="mt-2 pt-2 text-center" style={{ borderTop: "1px solid var(--obsidian-border)" }}>
        <p className="text-xs" style={{ color: "var(--obsidian-text-muted)" }}>
          AstroOS v2.3 · Lakshmi Release · All systems operational
        </p>
      </div>
    </div>
  );
}
