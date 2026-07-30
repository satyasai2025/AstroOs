"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Badge, Button, Card, KpiCard } from "@/components/ui";
import { useCurrentUser } from "@/lib/auth";
import { researchProjectsApi, type ResearchProject } from "@/lib/research";

/**
 * Illustrative counts matching the "Researcher Dashboard" mockup — this app
 * has no dataset/query-result backend yet (see app/research/query-builder,
 * app/research/datasets), so these are explicit placeholders, not live
 * figures. "Recent Research Projects" below is real data from the existing
 * /api/v1/research/projects endpoint (same source as /research/projects).
 */
const PLACEHOLDER_KPIS = [
  { label: "Active Datasets", value: "6", accent: "cyan" as const },
  { label: "Total Charts Indexed", value: "52,431", accent: "gold" as const },
  { label: "Queries Run (30d)", value: "184", accent: "violet" as const },
  { label: "Rules Pending Review", value: "23", accent: "success" as const },
];

const TOP_COMBINATIONS = [
  { name: "Jupiter in Kendra from Moon", matches: 1243, tone: "success" as const },
  { name: "10th Lord in 11th House", matches: 998, tone: "cyan" as const },
  { name: "Saturn Sade Sati (natal Moon)", matches: 1102, tone: "gold" as const },
];

export default function ResearcherDashboardPage() {
  const { data: user } = useCurrentUser();
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    researchProjectsApi
      .list(user.id)
      .then((data) => setProjects(data.projects.slice(0, 5)))
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, [user]);

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
        {PLACEHOLDER_KPIS.map((k) => (
          <KpiCard key={k.label} label={k.label} value={k.value} accent={k.accent} />
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
            {loading ? (
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
