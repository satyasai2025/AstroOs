"use client";

/**
 * AstroOS — Personal Pattern Exploration (Module 27)
 *
 * A researcher's own "what-if" lens over the shared research corpus: the
 * same dataset and the same fixed statistical formulas as the shared
 * Patterns dashboard, but with THEIR OWN significance/frequency/Wilson-z
 * thresholds. Results are computed live via POST /cases/patterns/explore
 * and are never persisted — nothing here can change what any other
 * researcher sees on the shared dashboard.
 */

import { useState } from "react";
import { Badge, Button, Card, Input, KpiCard, Select, Table, type TableColumn } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { DiscoveredPattern } from "@/lib/types";
import { EVENT_OPTIONS, pct } from "./patternConstants";
import { ResearchPatternsShell } from "./ResearchPatternsShell";

const DEFAULTS = {
  eventType: "",
  minSignificance: "0.90",
  minFrequency: "0.10",
  wilsonZ: "1.0",
  topCombos: "5",
};

export function ExplorePanel() {
  const [eventType, setEventType] = useState(DEFAULTS.eventType);
  const [minSignificance, setMinSignificance] = useState(DEFAULTS.minSignificance);
  const [minFrequency, setMinFrequency] = useState(DEFAULTS.minFrequency);
  const [wilsonZ, setWilsonZ] = useState(DEFAULTS.wilsonZ);
  const [topCombos, setTopCombos] = useState(DEFAULTS.topCombos);

  const [patterns, setPatterns] = useState<DiscoveredPattern[]>([]);
  const [executionMs, setExecutionMs] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  async function runExploration() {
    setLoading(true);
    setError(null);
    try {
      const result = await researchCasesApi.explorePatterns({
        event_type: eventType || undefined,
        min_significance: Number(minSignificance),
        min_frequency: Number(minFrequency),
        wilson_z: Number(wilsonZ),
        top_combos: Number(topCombos),
      });
      setPatterns(result.patterns);
      setExecutionMs(result.execution_time_ms);
      setHasRun(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Exploration failed.");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setEventType(DEFAULTS.eventType);
    setMinSignificance(DEFAULTS.minSignificance);
    setMinFrequency(DEFAULTS.minFrequency);
    setWilsonZ(DEFAULTS.wilsonZ);
    setTopCombos(DEFAULTS.topCombos);
  }

  const avgConfidence = patterns.length
    ? patterns.reduce((s, p) => s + p.confidence_score, 0) / patterns.length
    : 0;

  const columns: TableColumn<DiscoveredPattern>[] = [
    { key: "event_type", label: "Event", render: (p) => <Badge tone="cyan">{p.event_type}</Badge> },
    { key: "description", label: "Pattern", render: (p) => <span style={{ fontSize: "var(--text-sm)" }}>{p.description}</span> },
    { key: "sample_size", label: "Support", align: "right", render: (p) => p.sample_size },
    { key: "confidence_score", label: "Confidence", align: "right", render: (p) => pct(p.confidence_score) },
  ];

  return (
    <ResearchPatternsShell title="Explore" subtitle="Personal pattern exploration">
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        <Card glow="violet">
          <p style={{ color: "var(--text-primary)", margin: 0, fontSize: "var(--text-sm)" }}>
            This is <strong>your own view</strong> — it runs the same shared dataset through the same fixed
            statistical formulas (Wilson-shrunk significance test), but with thresholds you set yourself. Results
            are computed live and shown only to you; nothing here is saved or persisted, so it can never change
            what other researchers see on the shared Patterns dashboard.
          </p>
        </Card>

        {error && (
          <Card glow="gold">
            <p style={{ color: "var(--text-primary)", margin: 0 }}>{error}</p>
          </Card>
        )}

        <Card padding="var(--space-4)">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "var(--space-3)", alignItems: "end" }}>
            <Select label="Event Type" options={EVENT_OPTIONS} value={eventType} onChange={setEventType} />
            <Input
              label="Min. Significance (0.5–0.999)"
              type="number"
              value={minSignificance}
              onChange={setMinSignificance}
              hint="Shared dashboard default: 0.90"
            />
            <Input
              label="Min. Frequency (0.01–1.0)"
              type="number"
              value={minFrequency}
              onChange={setMinFrequency}
              hint="Shared dashboard default: 0.10"
            />
            <Input
              label="Wilson Z (0–3)"
              type="number"
              value={wilsonZ}
              onChange={setWilsonZ}
              hint="Shared dashboard default: 1.0 — higher is stricter on small samples"
            />
            <Input label="Max patterns per type" type="number" value={topCombos} onChange={setTopCombos} />
          </div>
          <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-3)" }}>
            <Button onClick={runExploration} disabled={loading}>
              {loading ? "Running…" : "Run Exploration"}
            </Button>
            <Button onClick={reset} variant="ghost">
              Reset to shared defaults
            </Button>
          </div>
        </Card>

        {hasRun && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "var(--space-3)" }}>
              <KpiCard label="Patterns Found" value={patterns.length} accent="cyan" />
              <KpiCard label="Avg Confidence" value={pct(avgConfidence)} accent="violet" />
              <KpiCard label="Execution Time" value={executionMs !== null ? `${executionMs}ms` : "—"} accent="gold" />
            </div>

            <Card padding="0">
              <div style={{ padding: "var(--space-4)", borderBottom: "1px solid var(--border-default)" }}>
                <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
                  Your Exploration ({patterns.length})
                </h2>
              </div>
              {patterns.length === 0 ? (
                <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", padding: "var(--space-4)" }}>
                  No patterns clear these thresholds. Try lowering Min. Significance or Min. Frequency.
                </p>
              ) : (
                <Table columns={columns} rows={patterns} />
              )}
            </Card>
          </>
        )}
      </div>
    </ResearchPatternsShell>
  );
}
