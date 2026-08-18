"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, KpiCard } from "@/components/ui";
import { useCurrentUser } from "@/lib/auth";
import { useMyCharts } from "@/lib/charts";
import {
  useResearchProjects,
  useQueryLogs,
  useHypotheses,
  type ResearchProject,
} from "@/lib/research";

const TOP_COMBINATIONS = [
  { name: "Jupiter in Kendra from Moon (Gajakesari)", matches: 1243, tone: "success" as const },
  { name: "10th Lord in 11th House (Dhana)", matches: 998, tone: "cyan" as const },
  { name: "Saturn Sade Sati (natal Moon)", matches: 1102, tone: "gold" as const },
];

export default function ResearcherDashboardPage() {
  const { data: user } = useCurrentUser();
  const { data: projectsData, isLoading: projectsLoading } = useResearchProjects(user?.id);
  const { data: chartsData, isLoading: chartsLoading } = useMyCharts();
  const { data: queryLogs, isLoading: logsLoading } = useQueryLogs(10);
  const { data: hypothesesData, isLoading: hypothesesLoading } = useHypotheses();

  const projects = projectsData?.projects ?? [];
  const activeProjectsCount = projects.filter((p) => p.status === "active").length;
  const totalCharts = chartsData?.total ?? 0;
  const totalLogs = queryLogs?.total ?? 0;
  const totalHypotheses = hypothesesData?.total ?? 0;

  const realKpis = [
    {
      label: "Active Projects",
      value: projectsLoading ? "…" : String(activeProjectsCount),
      accent: "cyan" as const,
      href: "/research/projects",
    },
    {
      label: "Total Charts Saved",
      value: chartsLoading ? "…" : String(totalCharts),
      accent: "gold" as const,
      href: "/charts/history",
    },
    {
      label: "Research Queries Logged",
      value: logsLoading ? "…" : String(totalLogs),
      accent: "violet" as const,
      href: "/research/projects",
    },
    {
      label: "Hypotheses for Review",
      value: hypothesesLoading ? "…" : String(totalHypotheses),
      accent: "success" as const,
      href: "/research/hypotheses",
    },
  ];

  return (
    <AppShell sectionColor="--section-research">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Researcher Dashboard
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Vedic Astrology Research Platform — cross-chart pattern queries and dataset management.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button href="/research/query-builder" variant="primary">
            Research Query Builder
          </Button>
          <Button href="/research/projects" variant="secondary">
            New Research Project
          </Button>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {realKpis.map((k) => (
          <KpiCard key={k.label} label={k.label} value={k.value} accent={k.accent} href={k.href} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card padding="0" style={{ gridColumn: "span 2" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "14px 18px",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
              Recent Research Projects
            </span>
            <a href="/research/projects" style={{ fontSize: "var(--text-xs)", color: "var(--cyan-400)" }}>
              View All
            </a>
          </div>
          <div>
            {projectsLoading ? (
              <p className="p-4 text-sm" style={{ color: "var(--text-muted)" }}>
                Loading projects…
              </p>
            ) : projects.length === 0 ? (
              <p className="p-4 text-sm" style={{ color: "var(--text-muted)" }}>
                No research projects yet. Create one to get started.
              </p>
            ) : (
              projects.map((p) => (
                <div
                  key={p.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 18px",
                    borderBottom: "1px solid var(--border-subtle)",
                  }}
                >
                  <div>
                    <p style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", color: "var(--text-primary)" }}>{p.title}</p>
                    <p style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>{p.description ?? "No description"}</p>
                  </div>
                  <Badge tone={p.status === "active" ? "success" : "neutral"}>{p.status}</Badge>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card padding="0">
          <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "var(--text-sm)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
              Top Combinations Found
            </span>
          </div>
          <div style={{ padding: "6px 18px" }}>
            {TOP_COMBINATIONS.map((c) => (
              <div
                key={c.name}
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, padding: "10px 0", borderBottom: "1px solid var(--border-subtle)" }}
              >
                <p style={{ fontSize: "var(--text-sm)", color: "var(--text-primary)" }}>{c.name}</p>
                <Badge tone={c.tone}>{c.matches.toLocaleString()}</Badge>
              </div>
            ))}
            <p className="pt-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
              Illustrative — cross-chart pattern matching isn't wired to a real query engine yet.
            </p>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
