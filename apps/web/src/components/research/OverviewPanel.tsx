"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Card, DonutChart, KpiCard } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { PatternListItem, PatternSummary } from "@/lib/types";
import { pct } from "./patternConstants";
import { ResearchPatternsShell } from "./ResearchPatternsShell";
import { useResearchPatternsFilters } from "./ResearchPatternsFiltersContext";

const PALETTE = ["var(--cyan-400)", "var(--violet-400)", "var(--gold-300)", "var(--success-400)", "var(--danger-400)"];

export function OverviewPanel() {
  const { eventType, confidenceBand, dataset, gender, chartType, nodeFilter } = useResearchPatternsFilters();
  const [summary, setSummary] = useState<PatternSummary | null>(null);
  const [topPatterns, setTopPatterns] = useState<PatternListItem[]>([]);
  const [allPatterns, setAllPatterns] = useState<PatternListItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const filters = {
        event_type: eventType || undefined,
        min_confidence: confidenceBand ? Number(confidenceBand) : undefined,
        dataset: dataset || undefined,
        gender: gender || undefined,
        chart: chartType || undefined,
        dimension: nodeFilter?.dimension,
        value: nodeFilter?.value,
      };
      const [summaryData, top5, all] = await Promise.all([
        researchCasesApi.getPatternSummary(),
        researchCasesApi.listPatterns({ ...filters, limit: 5 }),
        researchCasesApi.listPatterns({ ...filters, limit: 200 }),
      ]);
      setSummary(summaryData);
      setTopPatterns(top5.patterns);
      setAllPatterns(all.patterns);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load overview.");
    }
  }, [eventType, confidenceBand, dataset, gender, chartType, nodeFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const eventTypeDistribution = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of allPatterns) counts.set(p.event_type, (counts.get(p.event_type) ?? 0) + 1);
    return Array.from(counts.entries()).map(([event_type, count], i) => ({
      event_type,
      count,
      color: PALETTE[i % PALETTE.length],
    }));
  }, [allPatterns]);

  return (
    <ResearchPatternsShell title="Research Overview" subtitle="A condensed snapshot across every discovered pattern." summary={summary}>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {error && (
          <Card glow="gold">
            <p style={{ color: "var(--text-primary)", margin: 0 }}>{error}</p>
          </Card>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "var(--space-3)" }}>
          <KpiCard label="Total Cases" value={summary?.total_cases ?? "—"} accent="cyan" />
          <KpiCard label="Total Events" value={summary?.total_events ?? "—"} accent="violet" />
          <KpiCard label="Patterns Discovered" value={summary?.patterns_found ?? "—"} accent="gold" />
          <KpiCard label="High Confidence" value={summary?.high_confidence_patterns ?? "—"} accent="success" />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-4)" }}>
          <Card padding="0">
            <div style={{ padding: "var(--space-4)", borderBottom: "1px solid var(--border-default)" }}>
              <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>Top 5 Patterns Overall</h2>
            </div>
            {topPatterns.length === 0 ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", padding: "var(--space-4)" }}>No patterns yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column" }}>
                {topPatterns.map((p) => (
                  <div key={p.pattern_id} style={{ display: "flex", alignItems: "center", gap: "var(--space-3)", padding: "var(--space-3) var(--space-4)", borderBottom: "1px solid var(--border-subtle)" }}>
                    <Badge tone="cyan">{p.event_type}</Badge>
                    <span style={{ flex: 1, fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>{p.description}</span>
                    <span style={{ fontSize: "var(--text-sm)", color: "var(--text-primary)", fontWeight: "var(--weight-semibold)" }}>
                      {pct(p.confidence_score)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>Event Type Distribution</h2>
            {eventTypeDistribution.length === 0 ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>No data yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--space-3)" }}>
                <DonutChart segments={eventTypeDistribution.map((e) => ({ value: e.count, color: e.color }))} />
                <div style={{ display: "flex", flexDirection: "column", gap: 4, width: "100%" }}>
                  {eventTypeDistribution.map((e) => (
                    <div key={e.event_type} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "var(--text-xs)" }}>
                      <span style={{ width: 8, height: 8, borderRadius: "50%", background: e.color }} />
                      <span style={{ color: "var(--text-secondary)", flex: 1 }}>{e.event_type}</span>
                      <span style={{ color: "var(--text-tertiary)" }}>{e.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </ResearchPatternsShell>
  );
}
