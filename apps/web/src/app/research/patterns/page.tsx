"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Accordion,
  Badge,
  BarChart,
  Button,
  Card,
  DonutChart,
  FilterBar,
  Icon,
  KnowledgeGraph,
  KpiCard,
  LineChart,
  Select,
  Table,
  type TableColumn,
} from "@/components/ui";
import { CHART_OPTIONS, EVENT_OPTIONS, LIFT_BUCKET_COLORS, liftBucket, pct } from "@/components/research/patternConstants";
import { ResearchPatternsShell } from "@/components/research/ResearchPatternsShell";
import { useResearchPatternsFilters } from "@/components/research/ResearchPatternsFiltersContext";
import { researchCasesApi } from "@/lib/researchCases";
import type {
  ConfidenceBucket,
  DatasetValidationReport,
  EvidenceRecalculationResult,
  FeatureExtractionResponse,
  PatternDetail,
  PatternDiscoveryResponse,
  PatternExplainAllResponse,
  PatternGraphEdge,
  PatternGraphNode,
  PatternHypothesisResponse,
  PatternListItem,
  PatternSummary,
  PatternTrendPoint,
  SnapshotRebuildResult,
  TopFactor,
} from "@/lib/types";

const FACTOR_TABS = [
  { key: "planet", label: "Planets" },
  { key: "house", label: "Houses" },
  { key: "yoga", label: "Yogas" },
  { key: "dasha", label: "Dashas" },
];

const CATEGORY_COLORS: Record<string, string> = {
  dasha: "var(--cyan-400)",
  yoga: "var(--success-400)",
  house: "var(--gold-300)",
  transit: "var(--violet-400)",
  shadbala: "var(--text-secondary)",
  varga: "var(--danger-400)",
  nakshatra: "var(--cyan-300)",
  other: "var(--text-tertiary)",
};

const EVENT_ICON: Record<string, string> = {
  Marriage: "💍",
  Divorce: "💔",
  Promotion: "📈",
  "Job Change": "💼",
  Accident: "⚠️",
  Surgery: "🏥",
  "Child Birth": "👶",
  Education: "🎓",
  Business: "🏢",
  Finance: "💰",
  "Foreign Travel": "✈️",
  Property: "🏠",
  Health: "❤️",
  Spiritual: "🕉️",
  Litigation: "⚖️",
  Awards: "🏆",
  Political: "🏛️",
  Vehicle: "🚗",
  "Death of Parent": "🕯️",
  "Death of Spouse": "🕯️",
  Hospitalization: "🏥",
  Other: "•",
};

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch {
    return "—";
  }
}

export default function PatternDiscoveryPage() {
  const [error, setError] = useState<string | null>(null);

  const {
    dataset,
    eventType,
    setEventType,
    chartType,
    setChartType,
    confidenceBand,
    setConfidenceBand,
    supportBand,
    setSupportBand,
    gender,
    setGender,
    nodeFilter,
    setNodeFilter,
    clearNodeFilter,
  } = useResearchPatternsFilters();

  // ── Dashboard data ───────────────────────────────────────────────────────
  const [summary, setSummary] = useState<PatternSummary | null>(null);
  const [patterns, setPatterns] = useState<PatternListItem[]>([]);
  const [trends, setTrends] = useState<Record<string, PatternTrendPoint[]>>({});
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  // ── Top factors ──────────────────────────────────────────────────────────
  const [factorCategory, setFactorCategory] = useState("planet");
  const [topFactors, setTopFactors] = useState<TopFactor[]>([]);

  // ── Confidence distribution / graph ─────────────────────────────────────
  const [confidenceBuckets, setConfidenceBuckets] = useState<ConfidenceBucket[]>([]);
  const [graph, setGraph] = useState<{ nodes: PatternGraphNode[]; edges: PatternGraphEdge[] }>({ nodes: [], edges: [] });

  // ── Pattern detail ───────────────────────────────────────────────────────
  const [selectedPatternId, setSelectedPatternId] = useState<string | null>(null);
  const [detail, setDetail] = useState<PatternDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [explainError, setExplainError] = useState<string | null>(null);

  const openPatternDetail = useCallback(async (patternId: string) => {
    setSelectedPatternId(patternId);
    setDetail(null);
    setExplainError(null);
    setDetailLoading(true);
    try {
      const data = await researchCasesApi.getPatternDetail(patternId);
      setDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pattern detail.");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const loadDashboard = useCallback(async () => {
    setLoadingDashboard(true);
    setError(null);
    try {
      const [summaryData, listData, factorsData, distData, graphData] = await Promise.all([
        researchCasesApi.getPatternSummary(),
        researchCasesApi.listPatterns({
          event_type: eventType || undefined,
          gender: gender || undefined,
          dataset: dataset || undefined,
          chart: chartType || undefined,
          min_confidence: confidenceBand ? Number(confidenceBand) : undefined,
          min_support: supportBand ? Number(supportBand) : undefined,
          dimension: nodeFilter?.dimension,
          value: nodeFilter?.value,
          limit: 20,
        }),
        researchCasesApi.getTopFactors(factorCategory),
        researchCasesApi.getConfidenceDistribution(),
        researchCasesApi.getPatternGraph(),
      ]);
      setSummary(summaryData);
      setPatterns(listData.patterns);
      setTopFactors(factorsData.factors);
      setConfidenceBuckets(distData.buckets);
      setGraph(graphData);

      if (listData.patterns.length > 0 && !selectedPatternId) {
        void openPatternDetail(listData.patterns[0].pattern_id);
      }

      const trendEntries = await Promise.all(
        listData.patterns.map((p) =>
          researchCasesApi
            .getPatternTrend(p.pattern_id)
            .then((t) => [p.pattern_id, t.points] as const)
            .catch(() => [p.pattern_id, []] as const),
        ),
      );
      setTrends(Object.fromEntries(trendEntries));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load the pattern dashboard.");
    } finally {
      setLoadingDashboard(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventType, gender, dataset, chartType, confidenceBand, supportBand, nodeFilter, factorCategory]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const handleExplain = useCallback(async () => {
    if (!selectedPatternId) return;
    setExplaining(true);
    setExplainError(null);
    try {
      const result = await researchCasesApi.explainPattern(selectedPatternId);
      setDetail((prev) =>
        prev
          ? { ...prev, explanation: result.explanation, explanation_generated_at: result.explanation_generated_at }
          : prev,
      );
    } catch (err) {
      setExplainError(err instanceof Error ? err.message : "Failed to generate explanation.");
    } finally {
      setExplaining(false);
    }
  }, [selectedPatternId]);

  const handleSelectGraphNode = useCallback(
    (nodeId: string) => {
      // node id format: "${category}:${dimension}=${value}" (see pattern_graph.py)
      const afterColon = nodeId.slice(nodeId.indexOf(":") + 1);
      const eqIndex = afterColon.indexOf("=");
      if (eqIndex === -1) return;
      const dimension = afterColon.slice(0, eqIndex);
      const value = afterColon.slice(eqIndex + 1);
      setNodeFilter({ dimension, value });
    },
    [setNodeFilter],
  );

  // ── Derived (client-side, no extra endpoint) ─────────────────────────────
  const eventTypeDistribution = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of patterns) counts.set(p.event_type, (counts.get(p.event_type) ?? 0) + 1);
    const palette = ["var(--cyan-400)", "var(--violet-400)", "var(--gold-300)", "var(--success-400)", "var(--danger-400)"];
    return Array.from(counts.entries()).map(([event_type, count], i) => ({
      event_type,
      count,
      color: palette[i % palette.length],
    }));
  }, [patterns]);

  const liftBuckets = useMemo(() => {
    const counts: Record<string, number> = { "Very High": 0, High: 0, Medium: 0, Low: 0 };
    for (const p of patterns) counts[liftBucket(p.lift_score)] += 1;
    return counts;
  }, [patterns]);

  const strongestPattern = useMemo(
    () => [...patterns].sort((a, b) => b.confidence_score - a.confidence_score)[0] ?? null,
    [patterns],
  );
  const avgConfidence = useMemo(
    () => (patterns.length ? patterns.reduce((s, p) => s + p.confidence_score, 0) / patterns.length : 0),
    [patterns],
  );

  const recentPatterns = useMemo(
    () =>
      [...patterns]
        .sort((a, b) => (b.discovered_at ?? "").localeCompare(a.discovered_at ?? ""))
        .slice(0, 4),
    [patterns],
  );

  const insights = useMemo(() => {
    const lines: string[] = [];
    if (topFactors[0]) {
      lines.push(
        `${topFactors[0].value}${topFactors[1] ? ` & ${topFactors[1].value}` : ""} ${topFactors[1] ? "are" : "is"} the most influential ${factorCategory}${topFactors[1] ? "s" : ""} across discovered patterns.`,
      );
    }
    if (strongestPattern) {
      lines.push(`Strongest pattern: ${strongestPattern.description}`);
    }
    if (summary) {
      lines.push(
        `${summary.high_confidence_patterns} of ${summary.patterns_found} patterns clear the 75% confidence bar.`,
      );
    }
    return lines;
  }, [topFactors, factorCategory, strongestPattern, summary]);

  // ── Advanced Research state (unchanged) ──────────────────────────────────
  const [extraction, setExtraction] = useState<FeatureExtractionResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [discoverEventType, setDiscoverEventType] = useState("");
  const [topCombos, setTopCombos] = useState("5");
  const [discoverDateFrom, setDiscoverDateFrom] = useState("");
  const [discoverDateTo, setDiscoverDateTo] = useState("");
  const [discoveryResult, setDiscoveryResult] = useState<PatternDiscoveryResponse | null>(null);
  const [conditionsRaw, setConditionsRaw] = useState("");
  const [hypothesisType, setHypothesisType] = useState("Marriage");
  const [hypothesisResult, setHypothesisResult] = useState<PatternHypothesisResponse | null>(null);
  const [validationReport, setValidationReport] = useState<DatasetValidationReport | null>(null);
  const [rebuildResult, setRebuildResult] = useState<SnapshotRebuildResult | null>(null);
  const [evidenceResult, setEvidenceResult] = useState<EvidenceRecalculationResult | null>(null);
  const [explainAllResult, setExplainAllResult] = useState<PatternExplainAllResponse | null>(null);

  const handleExtract = useCallback(async () => {
    setBusy("extract");
    setError(null);
    try {
      setExtraction(await researchCasesApi.extractFeatures());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to extract features.");
    } finally {
      setBusy(null);
    }
  }, []);

  const handleDiscover = useCallback(async () => {
    setBusy("discover");
    setError(null);
    try {
      const data = await researchCasesApi.discoverPatterns({
        event_type: discoverEventType || undefined,
        top_combos: Number(topCombos),
        date_from: discoverDateFrom || undefined,
        date_to: discoverDateTo || undefined,
      });
      setDiscoveryResult(data);
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pattern discovery failed.");
    } finally {
      setBusy(null);
    }
  }, [discoverEventType, topCombos, discoverDateFrom, discoverDateTo, loadDashboard]);

  const handleHypothesis = useCallback(async () => {
    setError(null);
    const conditions: Record<string, string> = {};
    for (const line of conditionsRaw.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const [k, v] = trimmed.split("=");
      if (k && v) conditions[k.trim()] = v.trim();
    }
    if (!Object.keys(conditions).length) {
      setError("Enter at least one condition as dimension=value.");
      return;
    }
    setBusy("hypothesis");
    try {
      setHypothesisResult(await researchCasesApi.testHypothesis({ event_type: hypothesisType, conditions }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hypothesis test failed.");
    } finally {
      setBusy(null);
    }
  }, [conditionsRaw, hypothesisType]);

  const handleValidateDataset = useCallback(async () => {
    setBusy("validate");
    setError(null);
    try {
      setValidationReport(await researchCasesApi.validateDataset());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dataset validation failed.");
    } finally {
      setBusy(null);
    }
  }, []);

  const handleRebuildSnapshots = useCallback(async () => {
    setBusy("rebuild");
    setError(null);
    try {
      setRebuildResult(await researchCasesApi.rebuildSnapshots());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Snapshot rebuild failed.");
    } finally {
      setBusy(null);
    }
  }, []);

  const handleRecalculateEvidence = useCallback(async () => {
    setBusy("evidence");
    setError(null);
    try {
      setEvidenceResult(await researchCasesApi.recalculateEvidence());
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evidence recalculation failed.");
    } finally {
      setBusy(null);
    }
  }, [loadDashboard]);

  const handleRegenerateAllExplanations = useCallback(async () => {
    setBusy("explain-all");
    setError(null);
    try {
      setExplainAllResult(await researchCasesApi.regenerateAllExplanations());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk explanation regeneration failed.");
    } finally {
      setBusy(null);
    }
  }, []);

  const patternColumns: TableColumn<PatternListItem>[] = [
    {
      key: "rank",
      label: "Rank",
      render: (p) => {
        const idx = patterns.findIndex((x) => x.pattern_id === p.pattern_id);
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 22,
              height: 22,
              borderRadius: "50%",
              background: "var(--surface-glass-strong)",
              color: "var(--text-primary)",
              fontSize: "var(--text-xs)",
              fontWeight: "var(--weight-semibold)",
            }}
          >
            {idx + 1}
          </span>
        );
      },
    },
    {
      key: "event_type",
      label: "Event",
      render: (p) => (
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <Badge tone="cyan">{p.event_type}</Badge>
          <div style={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
            {p.categories.map((c) => (
              <span
                key={c}
                style={{
                  fontSize: "10px",
                  padding: "1px 6px",
                  borderRadius: "var(--radius-full)",
                  border: `1px solid ${CATEGORY_COLORS[c] ?? CATEGORY_COLORS.other}`,
                  color: CATEGORY_COLORS[c] ?? CATEGORY_COLORS.other,
                  textTransform: "uppercase",
                }}
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      ),
    },
    { key: "description", label: "Pattern", render: (p) => <span style={{ fontSize: "var(--text-sm)" }}>{p.description}</span> },
    { key: "sample_size", label: "Support", align: "right", render: (p) => p.sample_size },
    {
      key: "confidence_score",
      label: "Confidence",
      align: "right",
      render: (p) => (
        <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
          <div style={{ width: 46, height: 5, borderRadius: "var(--radius-full)", background: "var(--bg-surface-700)", overflow: "hidden" }}>
            <div style={{ width: `${p.confidence_score * 100}%`, height: "100%", background: "var(--cyan-400)" }} />
          </div>
          <span>{pct(p.confidence_score)}</span>
        </div>
      ),
    },
    {
      key: "lift_score",
      label: "Lift",
      align: "right",
      render: (p) => (
        <span style={{ color: LIFT_BUCKET_COLORS[liftBucket(p.lift_score)] }}>
          {p.lift_score.toFixed(2)} · {liftBucket(p.lift_score)}
        </span>
      ),
    },
    {
      key: "trend",
      label: "Trend",
      render: (p) => {
        const points = trends[p.pattern_id];
        if (!points || points.length === 0) return <span style={{ color: "var(--text-tertiary)" }}>—</span>;
        return <LineChart data={points.map((pt) => pt.confidence_score * 100)} height={28} color="var(--violet-400)" />;
      },
    },
  ];

  return (
    <ResearchPatternsShell
      title="Research Patterns"
      subtitle="Discover recurring astrological patterns across verified life events"
      summary={summary}
      lastUpdated={strongestPattern?.discovered_at}
      exportRows={patterns}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {error && (
          <Card glow="gold">
            <p style={{ color: "var(--text-primary)", margin: 0 }}>{error}</p>
          </Card>
        )}

        {/* ── KPIs ─────────────────────────────────────────────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "var(--space-3)" }}>
          <KpiCard label="Total Events Analyzed" value={summary?.total_events ?? "—"} accent="cyan" />
          <KpiCard label="Patterns Discovered" value={summary?.patterns_found ?? "—"} accent="violet" />
          <KpiCard label="High Confidence Patterns" value={summary?.high_confidence_patterns ?? "—"} accent="success" />
          <KpiCard
            label="Strongest Pattern"
            value={strongestPattern?.event_type ?? "—"}
            caveat={strongestPattern ? `${pct(strongestPattern.confidence_score)} confidence` : undefined}
            accent="gold"
          />
          <KpiCard label="Avg Confidence Score" value={patterns.length ? pct(avgConfidence) : "—"} />
        </div>

        {summary && summary.patterns_found === 0 && !loadingDashboard && (
          <Card glow="cyan">
            <p style={{ margin: 0, color: "var(--text-primary)" }}>
              No patterns discovered yet. Open <strong>Advanced Research Tools</strong> below and run
              Feature Extraction then Discover Patterns to populate this dashboard.
            </p>
          </Card>
        )}

        {/* ── Filters ──────────────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <FilterBar
            filters={[
              { key: "eventType", label: "Event Type", options: EVENT_OPTIONS },
              { key: "chart", label: "Chart Type", options: CHART_OPTIONS },
              {
                key: "gender",
                label: "Gender",
                options: [
                  { value: "", label: "Any" },
                  { value: "male", label: "Male" },
                  { value: "female", label: "Female" },
                  { value: "other", label: "Other" },
                ],
              },
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
              {
                key: "support",
                label: "Min. Support (cases)",
                options: [
                  { value: "", label: "Any" },
                  { value: "5", label: "5+" },
                  { value: "20", label: "20+" },
                  { value: "50", label: "50+" },
                ],
              },
            ]}
            activeValues={{ eventType, chart: chartType, gender, confidence: confidenceBand, support: supportBand }}
            onChange={(key, value) => {
              if (key === "eventType") setEventType(value);
              else if (key === "chart") setChartType(value);
              else if (key === "gender") setGender(value);
              else if (key === "confidence") setConfidenceBand(value);
              else if (key === "support") setSupportBand(value);
            }}
            onClear={() => {
              setEventType("");
              setChartType("");
              setGender("");
              setConfidenceBand("");
              setSupportBand("");
            }}
          />
        </Card>

        {/* ── Top Contributing Factors + Event Type Distribution ──────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-4)" }}>
          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Top Contributing Factors
            </h2>
            <div style={{ display: "flex", gap: "var(--space-3)", borderBottom: "1px solid var(--border-subtle)", marginBottom: "var(--space-3)" }}>
              {FACTOR_TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setFactorCategory(t.key)}
                  style={{
                    background: "none",
                    border: "none",
                    padding: "8px 2px",
                    fontSize: "var(--text-sm)",
                    fontWeight: t.key === factorCategory ? "var(--weight-semibold)" : "var(--weight-regular)",
                    color: t.key === factorCategory ? "var(--text-primary)" : "var(--text-tertiary)",
                    cursor: "pointer",
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>
            {topFactors.length === 0 ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>No data yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {(() => {
                  const max = Math.max(...topFactors.map((f) => f.count), 1);
                  return topFactors.map((f) => (
                    <div key={f.value} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ width: 70, fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>{f.value}</span>
                      <div style={{ flex: 1, height: 8, borderRadius: "var(--radius-full)", background: "var(--bg-surface-700)", overflow: "hidden" }}>
                        <div style={{ width: `${(f.count / max) * 100}%`, height: "100%", background: "var(--cyan-400)" }} />
                      </div>
                      <span style={{ width: 90, textAlign: "right", fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>
                        {Math.round((f.count / max) * 100)}% ({f.count.toLocaleString()})
                      </span>
                    </div>
                  ));
                })()}
              </div>
            )}
          </Card>

          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Event Type Distribution
            </h2>
            {eventTypeDistribution.length === 0 ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>No patterns yet.</p>
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

        {nodeFilter && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "8px 14px",
              borderRadius: "var(--radius-full)",
              background: "var(--surface-glass-strong)",
              border: "1px solid var(--cyan-400)",
              width: "fit-content",
              fontSize: "var(--text-sm)",
              color: "var(--text-primary)",
            }}
          >
            Filtered by: {nodeFilter.dimension} = {nodeFilter.value}
            <button
              onClick={clearNodeFilter}
              style={{ background: "none", border: "none", color: "var(--text-tertiary)", cursor: "pointer", fontSize: "var(--text-sm)" }}
              aria-label="Clear network graph filter"
            >
              ✕
            </button>
          </div>
        )}

        {/* ── Top Patterns + Detail panel (sticky) ─────────────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-4)", alignItems: "start" }}>
          <Card padding="0">
            <div style={{ padding: "var(--space-4)", borderBottom: "1px solid var(--border-default)" }}>
              <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
                Top Patterns ({patterns.length})
              </h2>
            </div>
            {patterns.length === 0 ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", padding: "var(--space-4)" }}>
                No patterns match the current filters.
              </p>
            ) : (
              <Table columns={patternColumns} rows={patterns} onRowClick={(p) => void openPatternDetail(p.pattern_id)} />
            )}
          </Card>

          <Card
            padding="var(--space-4)"
            style={{ position: "sticky", top: 170, maxHeight: "calc(100vh - 190px)", overflowY: "auto" }}
          >
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Pattern Detail
            </h2>
            {!selectedPatternId ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
                Select a pattern from the table to inspect its evidence.
              </p>
            ) : detailLoading ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>Loading…</p>
            ) : detail ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
                <div>
                  <Badge tone="cyan">{detail.event_type}</Badge>
                  <p style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", margin: "var(--space-2) 0 0" }}>
                    {detail.description}
                  </p>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {detail.dimensions.map((d) => (
                    <div key={`${d.dimension}-${d.value}`} style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>
                      <span style={{ color: "var(--gold-300)", fontFamily: "var(--font-mono)" }}>
                        {d.dimension}={d.value}
                      </span>{" "}
                      — {pct(d.frequency)} vs {pct(d.expected_by_chance)} base, sig. {d.significance.toFixed(2)}
                    </div>
                  ))}
                </div>

                <div style={{ display: "flex", gap: "var(--space-3)", fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>
                  <span>{detail.supporting_case_ids.length} supporting</span>
                  <span>{detail.contradicting_case_ids.length} contradicting</span>
                </div>

                <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>
                  Computed with algorithm v{detail.algorithm_version}, feature v{detail.feature_version}
                  {detail.snapshot_versions.length > 0 && `, snapshot v${detail.snapshot_versions.join(", v")}`}
                </div>

                <div style={{ borderTop: "1px solid var(--border-default)", paddingTop: "var(--space-3)" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <strong style={{ fontSize: "var(--text-sm)" }}>AI Explanation</strong>
                    <Button variant="secondary" size="sm" disabled={explaining} onClick={handleExplain}>
                      {explaining ? "Generating…" : detail.explanation ? "Regenerate" : "Generate"}
                    </Button>
                  </div>
                  {explainError && (
                    <p style={{ color: "var(--danger-400)", fontSize: "var(--text-xs)", marginTop: 6 }}>{explainError}</p>
                  )}
                  {detail.explanation && (
                    <p style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginTop: 6 }}>
                      {detail.explanation}
                    </p>
                  )}
                </div>

                {detail.classical_references.length > 0 && (
                  <div>
                    <strong style={{ fontSize: "var(--text-sm)" }}>Classical References</strong>
                    <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: "var(--text-xs)", color: "var(--text-tertiary)" }}>
                      {detail.classical_references.map((ref) => (
                        <li key={ref}>{ref}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : null}
          </Card>
        </div>

        {/* ── Confidence Distribution + Pattern Strength ───────────────────── */}
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-4)" }}>
          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Confidence Score Distribution
            </h2>
            {confidenceBuckets.length === 0 ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>No data yet.</p>
            ) : (
              <BarChart
                data={confidenceBuckets.map((b) => ({ value: b.count, label: b.bucket }))}
                color="var(--violet-400)"
              />
            )}
          </Card>

          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Pattern Strength (Lift Score)
            </h2>
            {patterns.length === 0 ? (
              <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>No data yet.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "var(--space-3)" }}>
                <div style={{ position: "relative", width: 140, height: 140 }}>
                  <DonutChart
                    size={140}
                    segments={(["Very High", "High", "Medium", "Low"] as const)
                      .filter((b) => liftBuckets[b] > 0)
                      .map((b) => ({ value: liftBuckets[b], color: LIFT_BUCKET_COLORS[b] }))}
                  />
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <div style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-bold)", color: "var(--text-primary)" }}>
                      {patterns.length}
                    </div>
                    <div style={{ fontSize: "10px", color: "var(--text-tertiary)" }}>Total</div>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4, width: "100%" }}>
                  {(["Very High", "High", "Medium", "Low"] as const).map((b) => (
                    <div key={b} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "var(--text-xs)" }}>
                      <span style={{ width: 8, height: 8, borderRadius: "50%", background: LIFT_BUCKET_COLORS[b] }} />
                      <span style={{ color: "var(--text-secondary)", flex: 1 }}>{b}</span>
                      <span style={{ color: "var(--text-tertiary)" }}>
                        {liftBuckets[b]} ({patterns.length ? Math.round((liftBuckets[b] / patterns.length) * 100) : 0}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* ── Recent Significant Patterns ────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Recent Significant Patterns
          </h2>
          {recentPatterns.length === 0 ? (
            <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>None yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
              {recentPatterns.map((p) => (
                <div key={p.pattern_id} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: "var(--text-sm)" }}>
                  <span style={{ fontSize: "var(--text-md)" }}>{EVENT_ICON[p.event_type] ?? "•"}</span>
                  <Badge tone="cyan">{p.event_type}</Badge>
                  <span style={{ flex: 1, color: "var(--text-secondary)" }}>{p.description}</span>
                  <span style={{ color: "var(--text-tertiary)", fontSize: "var(--text-xs)" }}>{formatDate(p.discovered_at)}</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* ── Network Graph ─────────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Pattern Network
          </h2>
          <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", marginTop: 0 }}>
            Dimension-values that co-occur across discovered patterns, grouped into rings by category
            (dasha, yoga, house, transit, shadbala, varga, nakshatra). Click a node to filter the table
            and detail panel to that factor.
          </p>
          {graph.nodes.length === 0 ? (
            <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>No graph data yet.</p>
          ) : (
            <div style={{ display: "flex", justifyContent: "center" }}>
              <KnowledgeGraph
                nodes={graph.nodes.map((n) => ({
                  id: n.id,
                  x: n.x,
                  y: n.y,
                  label: n.label,
                  size: n.size,
                  color: CATEGORY_COLORS[n.category] ?? CATEGORY_COLORS.other,
                }))}
                edges={graph.edges}
                width={520}
                height={520}
                onSelectNode={handleSelectGraphNode}
              />
            </div>
          )}
        </Card>

        {/* ── Pattern Insights ──────────────────────────────────────────────── */}
        {insights.length > 0 && (
          <Card padding="var(--space-4)">
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
              Pattern Insights
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "var(--space-3)" }}>
              {insights.map((line, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 10,
                    padding: "var(--space-3)",
                    borderRadius: "var(--radius-md)",
                    background: "var(--bg-surface-800)",
                    border: "1px solid var(--border-default)",
                  }}
                >
                  <span
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: "50%",
                      background: "var(--surface-glass-strong)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    <Icon name="sparkle" size={14} />
                  </span>
                  <p style={{ margin: 0, fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>{line}</p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* ── Advanced Research (collapsed by default) ─────────────────────── */}
        <Accordion
          items={[
            {
              key: "advanced",
              title: "⚙ Advanced Research Tools",
              content: (
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
                  {/* Feature Extraction */}
                  <div>
                    <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>Feature Extraction</h3>
                    <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
                      Normalise every imported EventSnapshot into flat research features.
                    </p>
                    <Button variant="secondary" size="md" disabled={busy === "extract"} onClick={handleExtract}>
                      {busy === "extract" ? "Extracting…" : "Extract Features"}
                    </Button>
                    {extraction && (
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                          gap: "var(--space-2)",
                          marginTop: "var(--space-3)",
                        }}
                      >
                        <StatTile label="Total" value={String(extraction.total_features)} />
                        {Object.entries(extraction.features_by_category).map(([cat, count]) => (
                          <StatTile key={cat} label={cat} value={String(count)} />
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Discover Patterns */}
                  <div>
                    <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>Discover Patterns</h3>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-3)", alignItems: "flex-end" }}>
                      <div style={{ width: 200 }}>
                        <Select label="Event type" options={EVENT_OPTIONS} value={discoverEventType} onChange={setDiscoverEventType} />
                      </div>
                      <div style={{ width: 100 }}>
                        <Select
                          label="Top combos"
                          options={[
                            { value: "3", label: "3" },
                            { value: "5", label: "5" },
                            { value: "10", label: "10" },
                          ]}
                          value={topCombos}
                          onChange={setTopCombos}
                        />
                      </div>
                      <label style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
                        From{" "}
                        <input
                          type="date"
                          value={discoverDateFrom}
                          onChange={(e) => setDiscoverDateFrom(e.target.value)}
                          style={{ marginLeft: 4 }}
                        />
                      </label>
                      <label style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
                        To <input type="date" value={discoverDateTo} onChange={(e) => setDiscoverDateTo(e.target.value)} style={{ marginLeft: 4 }} />
                      </label>
                      <Button variant="secondary" size="md" disabled={!extraction || busy === "discover"} onClick={handleDiscover}>
                        {busy === "discover" ? "Discovering…" : "Discover Patterns"}
                      </Button>
                    </div>
                    {discoveryResult && (
                      <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", marginTop: "var(--space-2)" }}>
                        Found {discoveryResult.patterns.length} pattern(s) across {discoveryResult.total_cases} cases in{" "}
                        {discoveryResult.execution_time_ms}ms. Dashboard refreshed above.
                      </p>
                    )}
                  </div>

                  {/* Hypothesis Tester */}
                  <div>
                    <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>Hypothesis Tester</h3>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-3)", alignItems: "flex-start" }}>
                      <div style={{ width: 200 }}>
                        <Select label="Event type" options={EVENT_OPTIONS.slice(1)} value={hypothesisType} onChange={setHypothesisType} />
                      </div>
                      <textarea
                        value={conditionsRaw}
                        onChange={(e) => setConditionsRaw(e.target.value)}
                        placeholder={"dasha_mahadasha=Ju\ntransit_Sa_7th_house=True"}
                        rows={3}
                        style={{
                          flex: 1,
                          minWidth: 240,
                          borderRadius: "var(--radius-md)",
                          border: "1px solid var(--border-default)",
                          background: "var(--bg-surface-800)",
                          padding: "var(--space-2)",
                          color: "var(--text-primary)",
                          fontSize: "var(--text-sm)",
                        }}
                      />
                      <Button variant="primary" size="md" disabled={busy === "hypothesis"} onClick={handleHypothesis}>
                        {busy === "hypothesis" ? "Testing…" : "Test Hypothesis"}
                      </Button>
                    </div>
                    {hypothesisResult && (
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                          gap: "var(--space-2)",
                          marginTop: "var(--space-3)",
                        }}
                      >
                        <StatTile label="Matching" value={String(hypothesisResult.matching_cases)} />
                        <StatTile label="Total" value={String(hypothesisResult.total_cases)} />
                        <StatTile label="Proportion" value={pct(hypothesisResult.proportion)} />
                        <StatTile label="Confidence" value={pct(hypothesisResult.confidence_score)} />
                      </div>
                    )}
                  </div>

                  {/* Dataset Validation */}
                  <div>
                    <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>Dataset Validation</h3>
                    <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
                      Integrity report over already-imported cases: missing snapshots, duplicates, stale versions.
                    </p>
                    <Button variant="secondary" size="md" disabled={busy === "validate"} onClick={handleValidateDataset}>
                      {busy === "validate" ? "Validating…" : "Validate Dataset"}
                    </Button>
                    {validationReport && (
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                          gap: "var(--space-2)",
                          marginTop: "var(--space-3)",
                        }}
                      >
                        <StatTile label="Total cases" value={String(validationReport.total_cases)} />
                        <StatTile label="Missing snapshots" value={String(validationReport.cases_without_snapshots.length)} />
                        <StatTile label="Stale snapshot version" value={String(validationReport.stale_snapshot_case_ids.length)} />
                        <StatTile label="Duplicates" value={String(validationReport.duplicate_case_ids.length)} />
                      </div>
                    )}
                  </div>

                  {/* Snapshot Rebuild */}
                  <div>
                    <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>Snapshot Rebuild</h3>
                    <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
                      Recompute snapshots for every imported case under the current engine version. Old
                      snapshots are kept, not overwritten.
                    </p>
                    <Button variant="secondary" size="md" disabled={busy === "rebuild"} onClick={handleRebuildSnapshots}>
                      {busy === "rebuild" ? "Rebuilding…" : "Rebuild Snapshots"}
                    </Button>
                    {rebuildResult && (
                      <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", marginTop: "var(--space-2)" }}>
                        {rebuildResult.cases_processed} case(s) processed, {rebuildResult.snapshots_created} new
                        snapshot(s) under v{rebuildResult.snapshot_version}.
                        {rebuildResult.errors.length > 0 && ` ${rebuildResult.errors.length} error(s).`}
                      </p>
                    )}
                  </div>

                  {/* Evidence Recalculation */}
                  <div>
                    <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>Evidence Recalculation</h3>
                    <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
                      Refresh supporting/contradicting cases and lift for existing patterns — no new
                      discovery. Run this after a Snapshot Rebuild.
                    </p>
                    <Button variant="secondary" size="md" disabled={busy === "evidence"} onClick={handleRecalculateEvidence}>
                      {busy === "evidence" ? "Recalculating…" : "Recalculate Evidence"}
                    </Button>
                    {evidenceResult && (
                      <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", marginTop: "var(--space-2)" }}>
                        {evidenceResult.patterns_refreshed} pattern(s) refreshed.
                      </p>
                    )}
                  </div>

                  {/* AI Explanation Regeneration */}
                  <div>
                    <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>AI Explanation Regeneration</h3>
                    <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
                      Bulk-refresh every persisted pattern&apos;s AI explanation. Calls a real external
                      API sequentially per pattern.
                    </p>
                    <Button variant="secondary" size="md" disabled={busy === "explain-all"} onClick={handleRegenerateAllExplanations}>
                      {busy === "explain-all" ? "Regenerating…" : "Regenerate All Explanations"}
                    </Button>
                    {explainAllResult && (
                      <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", marginTop: "var(--space-2)" }}>
                        {explainAllResult.succeeded}/{explainAllResult.total_patterns} succeeded.
                        {explainAllResult.errors.length > 0 && ` ${explainAllResult.errors.length} error(s).`}
                      </p>
                    )}
                  </div>
                </div>
              ),
            },
          ]}
        />
      </div>
    </ResearchPatternsShell>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: "var(--bg-surface-800)",
        border: "1px solid var(--border-default)",
        borderRadius: "var(--radius-md)",
        padding: "var(--space-2)",
      }}
    >
      <div style={{ color: "var(--text-tertiary)", fontSize: "var(--text-xs)", textTransform: "uppercase" }}>{label}</div>
      <div style={{ color: "var(--text-primary)", fontSize: "var(--text-md)", fontWeight: "var(--weight-semibold)" }}>
        {value}
      </div>
    </div>
  );
}
