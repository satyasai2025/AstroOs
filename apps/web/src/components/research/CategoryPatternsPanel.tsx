"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Card, FilterBar, KpiCard, Table, type TableColumn } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { PatternListItem, PatternSummary, TopFactor } from "@/lib/types";
import { EVENT_OPTIONS, pct } from "./patternConstants";
import { ResearchPatternsShell } from "./ResearchPatternsShell";
import { useResearchPatternsFilters } from "./ResearchPatternsFiltersContext";

interface CategoryPatternsPanelProps {
  tabTitle: string;
  subtitle: string;
  blurb: string;
  category?: string;
  minDimensions?: number;
  emptyMessage: string;
}

export function CategoryPatternsPanel({
  tabTitle,
  subtitle,
  blurb,
  category,
  minDimensions,
  emptyMessage,
}: CategoryPatternsPanelProps) {
  const { eventType, setEventType, confidenceBand, setConfidenceBand, dataset, gender, chartType, nodeFilter } =
    useResearchPatternsFilters();

  const [summary, setSummary] = useState<PatternSummary | null>(null);
  const [patterns, setPatterns] = useState<PatternListItem[]>([]);
  const [topFactors, setTopFactors] = useState<TopFactor[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, listData, factorsData] = await Promise.all([
        researchCasesApi.getPatternSummary(),
        researchCasesApi.listPatterns({
          category,
          min_dimensions: minDimensions,
          event_type: eventType || undefined,
          min_confidence: confidenceBand ? Number(confidenceBand) : undefined,
          dataset: dataset || undefined,
          gender: gender || undefined,
          chart: chartType || undefined,
          dimension: nodeFilter?.dimension,
          value: nodeFilter?.value,
          limit: 100,
        }),
        category ? researchCasesApi.getTopFactors(category) : Promise.resolve({ category: "", factors: [] }),
      ]);
      setSummary(summaryData);
      setPatterns(listData.patterns);
      setTopFactors(factorsData.factors);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load this tab.");
    } finally {
      setLoading(false);
    }
  }, [category, minDimensions, eventType, confidenceBand, dataset, gender, chartType, nodeFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const avgConfidence = patterns.length ? patterns.reduce((s, p) => s + p.confidence_score, 0) / patterns.length : 0;

  const columns: TableColumn<PatternListItem>[] = [
    { key: "event_type", label: "Event", render: (p) => <Badge tone="cyan">{p.event_type}</Badge> },
    { key: "description", label: "Pattern", render: (p) => <span style={{ fontSize: "var(--text-sm)" }}>{p.description}</span> },
    { key: "sample_size", label: "Support", align: "right", render: (p) => p.sample_size },
    { key: "confidence_score", label: "Confidence", align: "right", render: (p) => pct(p.confidence_score) },
    { key: "lift_score", label: "Lift", align: "right", mono: true, render: (p) => p.lift_score.toFixed(2) },
  ];

  return (
    <ResearchPatternsShell title={tabTitle} subtitle={subtitle} summary={summary} exportRows={patterns}>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", margin: 0, maxWidth: 720 }}>{blurb}</p>

        {error && (
          <Card glow="gold">
            <p style={{ color: "var(--text-primary)", margin: 0 }}>{error}</p>
          </Card>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "var(--space-3)" }}>
          <KpiCard label="Patterns Found" value={loading ? "—" : patterns.length} accent="cyan" />
          <KpiCard label="Avg Confidence" value={loading ? "—" : pct(avgConfidence)} accent="violet" />
          <KpiCard label="Top Factor" value={topFactors[0]?.value ?? "—"} accent="gold" />
        </div>

        <Card padding="var(--space-4)">
          <FilterBar
            filters={[
              { key: "eventType", label: "Event Type", options: EVENT_OPTIONS },
              {
                key: "confidence",
                label: "Min. Confidence",
                options: [
                  { value: "", label: "Any" },
                  { value: "0.5", label: "50%+" },
                  { value: "0.75", label: "75%+" },
                  { value: "0.9", label: "90%+" },
                ],
              },
            ]}
            activeValues={{ eventType, confidence: confidenceBand }}
            onChange={(key, value) => {
              if (key === "eventType") setEventType(value);
              else if (key === "confidence") setConfidenceBand(value);
            }}
            onClear={() => {
              setEventType("");
              setConfidenceBand("");
            }}
          />
        </Card>

        <Card padding="0">
          <div style={{ padding: "var(--space-4)", borderBottom: "1px solid var(--border-default)" }}>
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
              {tabTitle} Patterns ({patterns.length})
            </h2>
          </div>
          {patterns.length === 0 ? (
            <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", padding: "var(--space-4)" }}>
              {loading ? "Loading…" : emptyMessage}
            </p>
          ) : (
            <Table columns={columns} rows={patterns} />
          )}
        </Card>
      </div>
    </ResearchPatternsShell>
  );
}
