"use client";

import { useTheme } from "@/components/layout/ThemeProvider";
import { Icon, type IconName } from "@/components/ui";
import { useCurrentUser } from "@/lib/auth";
import type { PatternListItem, PatternSummary } from "@/lib/types";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import { ActiveDatasetBox } from "./ActiveDatasetBox";
import { useResearchPatternsFilters } from "./ResearchPatternsFiltersContext";

const TAB_ROUTES: { key: string; label: string; href: string }[] = [
  { key: "overview", label: "Overview", href: "/research/patterns/overview" },
  { key: "patterns", label: "Patterns", href: "/research/patterns" },
  { key: "combinations", label: "Combinations", href: "/research/patterns/combinations" },
  { key: "yogas", label: "Yogas", href: "/research/patterns/yogas" },
  { key: "dashas", label: "Dashas", href: "/research/patterns/dashas" },
  { key: "transits", label: "Transits", href: "/research/patterns/transits" },
  { key: "houses", label: "Houses", href: "/research/patterns/houses" },
  { key: "nakshatras", label: "Nakshatras", href: "/research/patterns/nakshatras" },
  { key: "compare", label: "Compare", href: "/research/patterns/compare" },
  { key: "explore", label: "Explore", href: "/research/patterns/explore" },
  { key: "ask", label: "Ask", href: "/research/patterns/ask" },
];

interface SidebarItem {
  key: string;
  label: string;
  icon: IconName;
  href?: string;
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  { key: "dashboard", label: "Dashboard", icon: "dashboard", href: "/dashboard" },
  { key: "research-cases", label: "Research Cases", icon: "database", href: "/research/projects" },
  { key: "life-events", label: "Life Events", icon: "calendar", href: "/research/events" },
  { key: "import-cases", label: "Import Cases", icon: "upload", href: "/research/import" },
  { key: "events-timeline", label: "Events Timeline", icon: "clock", href: "/research/events" },
  { key: "event-snapshots", label: "Event Snapshots", icon: "camera", href: "/research/projects" },
  { key: "patterns", label: "Patterns", icon: "sparkle", href: "/research/patterns" },
  { key: "knowledge-base", label: "Knowledge Base", icon: "book", href: "/knowledge" },
  { key: "reports", label: "Reports", icon: "report", href: "/reports/pdf" },
  { key: "ai-insights", label: "AI Insights", icon: "sparkle", href: "/ai/explain" },
  { key: "datasets", label: "Datasets", icon: "database", href: "/research/datasets" },
  { key: "evidence", label: "Evidence", icon: "flask", href: "/research/rules" },
  { key: "settings", label: "Settings", icon: "gear", href: "/settings/profile" },
];

const pillStyle: React.CSSProperties = {
  appearance: "none",
  background: "var(--bg-surface-700)",
  border: "1px solid var(--border-strong)",
  borderRadius: "var(--radius-full)",
  color: "var(--text-primary)",
  fontSize: "var(--text-sm)",
  padding: "7px 30px 7px 14px",
  cursor: "pointer",
  colorScheme: "dark",
};

function activeTabFromPath(pathname: string): string {
  if (pathname === "/research/patterns") return "patterns";
  const match = TAB_ROUTES.find((t) => t.href !== "/research/patterns" && pathname.startsWith(t.href));
  return match?.key ?? "patterns";
}

function toCsv(rows: PatternListItem[]): string {
  const header = ["pattern_id", "event_type", "description", "sample_size", "confidence_score", "lift_score"];
  const lines = [header.join(",")];
  for (const r of rows) {
    lines.push(
      [r.pattern_id, r.event_type, `"${r.description.replace(/"/g, '""')}"`, r.sample_size, r.confidence_score, r.lift_score].join(","),
    );
  }
  return lines.join("\n");
}

interface ResearchPatternsShellProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  summary?: PatternSummary | null;
  lastUpdated?: string | null;
  exportRows?: PatternListItem[];
}

export function ResearchPatternsShell({
  title,
  subtitle,
  children,
  summary = null,
  lastUpdated = null,
  exportRows = [],
}: ResearchPatternsShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const activeTab = useMemo(() => activeTabFromPath(pathname ?? ""), [pathname]);
  const { data: user } = useCurrentUser();
  const { dataset, setDataset, dateFrom, setDateFrom, dateTo, setDateTo } = useResearchPatternsFilters();

  const handleExport = () => {
    const csv = toCsv(exportRows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "research-patterns-export.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-primary, #0b0f16)" }}>
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside
        style={{
          width: 240,
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          borderRight: "1px solid var(--border-default)",
          padding: "var(--space-4) var(--space-3)",
          gap: "var(--space-4)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "0 var(--space-2)" }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              background: "linear-gradient(135deg, var(--cyan-400), var(--violet-400))",
            }}
          />
          <div>
            <div style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)" }}>
              AstroOS
            </div>
            <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>Research Engine v2.0</div>
          </div>
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: 2, flex: 1, overflowY: "auto" }}>
          {SIDEBAR_ITEMS.map((item) => {
            const isActive = item.key === "patterns";
            const disabled = !item.href;
            const content = (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 10px",
                  borderRadius: "var(--radius-md)",
                  fontSize: "var(--text-sm)",
                  color: isActive ? "var(--text-primary)" : disabled ? "var(--text-tertiary)" : "var(--text-secondary)",
                  background: isActive ? "var(--surface-glass-strong)" : "transparent",
                  opacity: disabled ? 0.5 : 1,
                  cursor: disabled ? "default" : "pointer",
                }}
              >
                <Icon name={item.icon} size={16} />
                <span>{item.label}</span>
              </div>
            );
            return item.href ? (
              <Link key={item.key} href={item.href} style={{ textDecoration: "none" }}>
                {content}
              </Link>
            ) : (
              <div key={item.key} title="Coming soon">
                {content}
              </div>
            );
          })}
        </nav>

        <ActiveDatasetBox summary={summary} lastUpdated={lastUpdated} />

        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "var(--text-xs)", color: "var(--text-tertiary)", padding: "0 var(--space-2)" }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--success-400)" }} />
          AstroOS v2.0 · Online
        </div>
      </aside>

      {/* ── Main column ─────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <header
          style={{
            position: "sticky",
            top: 0,
            zIndex: 10,
            background: "var(--bg-primary, #0b0f16)",
            borderBottom: "1px solid var(--border-default)",
            padding: "var(--space-3) var(--space-4)",
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--space-3)" }}>
            <div>
              <h1 style={{ fontSize: "var(--text-xl)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)", margin: 0 }}>
                {title}
              </h1>
              <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", margin: "2px 0 0" }}>{subtitle}</p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexShrink: 0 }}>
              <select style={pillStyle} value={dataset} onChange={(e) => setDataset(e.target.value)} aria-label="Dataset">
                <option value="">All Cases</option>
              </select>
              <select
                style={pillStyle}
                value={dateFrom ? "custom" : "all"}
                onChange={(e) => {
                  if (e.target.value === "all") {
                    setDateFrom("");
                    setDateTo("");
                  }
                }}
                aria-label="Date Range"
              >
                <option value="all">All Time</option>
                <option value="custom">Custom (set below)</option>
              </select>
              <button
                onClick={handleExport}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  background: "var(--surface-glass-strong)",
                  border: "1px solid var(--border-default)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--text-primary)",
                  fontSize: "var(--text-sm)",
                  padding: "8px 14px",
                  cursor: "pointer",
                }}
              >
                <Icon name="download" size={14} />
                Export
              </button>
              <div
                title="Help"
                style={{
                  width: 34,
                  height: 34,
                  borderRadius: "50%",
                  border: "1px solid var(--border-default)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-tertiary)",
                  cursor: "default",
                }}
              >
                <Icon name="help" size={16} />
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: "50%",
                    background: "linear-gradient(135deg, var(--gold-300), var(--violet-400))",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#1c1305",
                    fontWeight: "var(--weight-bold)",
                    fontSize: "var(--text-sm)",
                  }}
                >
                  {(user?.display_name ?? "R").charAt(0).toUpperCase()}
                </div>
                <div>
                  <div style={{ fontSize: "var(--text-sm)", color: "var(--text-primary)", fontWeight: "var(--weight-semibold)" }}>
                    {user?.display_name ?? "Researcher"}
                  </div>
                  <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>Researcher</div>
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "var(--space-4)", overflowX: "auto", marginTop: "var(--space-3)", borderBottom: "1px solid var(--border-subtle)" }}>
            {TAB_ROUTES.map((tab) => {
              const isActive = tab.key === activeTab;
              return (
                <button
                  key={tab.key}
                  onClick={() => router.push(tab.href)}
                  style={{
                    background: "none",
                    border: "none",
                    padding: "10px 2px",
                    fontSize: "var(--text-sm)",
                    fontWeight: isActive ? "var(--weight-semibold)" : "var(--weight-regular)",
                    color: isActive ? "var(--text-primary)" : "var(--text-tertiary)",
                    cursor: "pointer",
                    position: "relative",
                    whiteSpace: "nowrap",
                  }}
                >
                  {tab.label}
                  {isActive && (
                    <div
                      style={{
                        position: "absolute",
                        left: 0,
                        right: 0,
                        bottom: -1,
                        height: 2,
                        background: "linear-gradient(90deg, var(--cyan-400), var(--violet-400))",
                        borderRadius: 2,
                      }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        </header>

        <main style={{ flex: 1, padding: "var(--space-4)", minWidth: 0 }}>{children}</main>
      </div>
    </div>
  );
}
