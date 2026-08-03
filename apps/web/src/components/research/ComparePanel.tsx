"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Card, KpiCard, Select } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { PatternListItem } from "@/lib/types";
import { EVENT_OPTIONS, pct } from "./patternConstants";
import { ResearchPatternsShell } from "./ResearchPatternsShell";

interface SideState {
  eventType: string;
  patterns: PatternListItem[];
  topFactor: string;
  loading: boolean;
}

function useCompareSide(initialEventType: string) {
  const [state, setState] = useState<SideState>({ eventType: initialEventType, patterns: [], topFactor: "—", loading: false });

  const load = useCallback(async (eventType: string) => {
    if (!eventType) {
      setState((s) => ({ ...s, patterns: [], topFactor: "—" }));
      return;
    }
    setState((s) => ({ ...s, loading: true }));
    try {
      const [list, factors] = await Promise.all([
        researchCasesApi.listPatterns({ event_type: eventType, limit: 5, sort: "confidence_score" }),
        researchCasesApi.getTopFactors("planet"),
      ]);
      setState((s) => ({ ...s, patterns: list.patterns, topFactor: factors.factors[0]?.value ?? "—", loading: false }));
    } catch {
      setState((s) => ({ ...s, loading: false }));
    }
  }, []);

  useEffect(() => {
    void load(state.eventType);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.eventType]);

  return { state, setEventType: (v: string) => setState((s) => ({ ...s, eventType: v })) };
}

function CompareColumn({ label, eventType, onChangeEventType, side }: { label: string; eventType: string; onChangeEventType: (v: string) => void; side: SideState }) {
  const avgConfidence = side.patterns.length ? side.patterns.reduce((s, p) => s + p.confidence_score, 0) / side.patterns.length : 0;
  return (
    <Card padding="var(--space-4)">
      <div style={{ marginBottom: "var(--space-3)" }}>
        <label style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", textTransform: "uppercase" }}>{label}</label>
        <Select options={EVENT_OPTIONS.slice(1)} value={eventType} onChange={onChangeEventType} placeholder="Choose an event type" />
      </div>
      {!eventType ? (
        <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>Select an event type to compare.</p>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
            <KpiCard label="Patterns" value={side.loading ? "—" : side.patterns.length} accent="cyan" />
            <KpiCard label="Avg Conf." value={side.loading ? "—" : pct(avgConfidence)} accent="violet" />
            <KpiCard label="Top Factor" value={side.topFactor} accent="gold" />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {side.patterns.slice(0, 3).map((p) => (
              <div key={p.pattern_id} style={{ fontSize: "var(--text-xs)", color: "var(--text-secondary)" }}>
                <Badge tone="cyan">{p.event_type}</Badge> {p.description}
              </div>
            ))}
          </div>
        </>
      )}
    </Card>
  );
}

export function ComparePanel() {
  const a = useCompareSide("Marriage");
  const b = useCompareSide("Divorce");

  return (
    <ResearchPatternsShell title="Compare Event Types" subtitle="Side-by-side comparison of discovered patterns across two event types.">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-4)" }}>
        <CompareColumn label="Event Type A" eventType={a.state.eventType} onChangeEventType={a.setEventType} side={a.state} />
        <CompareColumn label="Event Type B" eventType={b.state.eventType} onChangeEventType={b.setEventType} side={b.state} />
      </div>
    </ResearchPatternsShell>
  );
}
