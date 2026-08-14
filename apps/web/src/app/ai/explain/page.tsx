"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input, Select, type SelectOption } from "@/components/ui";
import { api } from "@/lib/api";
import { aiApi, type BirthDataInput } from "@/lib/ai";
import { ResearchPatternsShell } from "@/components/research/ResearchPatternsShell";
import type { AIResponseSchema, AyanamsaCode, ExplanationResponse, HouseSystemCode } from "@/lib/types";

const AYANAMSA_OPTIONS: SelectOption[] = [
  { value: "lahiri", label: "Lahiri (default)" },
  { value: "kp", label: "Krishnamitra (KP)" },
  { value: "raman", label: "Raman" },
  { value: "yukteshwar", label: "Yukteshwar" },
  { value: "fagan_bradley", label: "Fagan/Bradley" },
  { value: "true_chitra", label: "True Chitra" },
  { value: "true_pushya", label: "True Pushya" },
];

const HOUSE_SYSTEM_OPTIONS: SelectOption[] = [
  { value: "W", label: "W — Whole Sign" },
  { value: "P", label: "P — Placidus" },
  { value: "K", label: "K — Koch" },
  { value: "E", label: "E — Equal" },
];

const SUMMARY_STYLE_OPTIONS: SelectOption[] = [
  { value: "concise", label: "Concise" },
  { value: "detailed", label: "Detailed" },
  { value: "technical", label: "Technical" },
];

function textareaStyle(): React.CSSProperties {
  return {
    width: "100%",
    minHeight: 88,
    padding: "var(--space-3)",
    borderRadius: "var(--radius-md)",
    border: "1px solid var(--border-subtle)",
    background: "var(--surface-2)",
    color: "var(--text-primary)",
    fontSize: "var(--text-sm)",
    fontFamily: "inherit",
    resize: "vertical",
  };
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const tone =
    confidence === "high" ? "success" : confidence === "medium" ? "gold" : "danger";
  return <Badge tone={tone as any}>{confidence}</Badge>;
}

function AIResponseCard({ result }: { result: AIResponseSchema }) {
  return (
    <Card padding="var(--space-4)">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-3)" }}>
        <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>{result.title}</h3>
        <ConfidenceBadge confidence={result.confidence} />
      </div>
      <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)" }}>{result.summary}</p>
      <p style={{ color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>{result.body}</p>

      {result.recommendations.length > 0 && (
        <div style={{ marginTop: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Recommendations
          </h4>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: "var(--text-sm)" }}>
            {result.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {result.citations.length > 0 && (
        <div style={{ marginTop: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Citations
          </h4>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
            {result.citations.map((c, i) => (
              <li key={i}>
                <strong>{c.source}</strong> — {c.reference}: {c.text}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.sources.length > 0 && (
        <p style={{ marginTop: "var(--space-3)", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
          Sources: {result.sources.join(", ")}
        </p>
      )}
    </Card>
  );
}

function RuleExplanationCard({ result }: { result: ExplanationResponse }) {
  return (
    <Card padding="var(--space-4)">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-3)" }}>
        <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
          {result.rule_name} <span style={{ color: "var(--text-tertiary)", fontWeight: "var(--weight-regular)" }}>({result.rule_id})</span>
        </h3>
        <Badge tone={result.matched ? "success" : "danger"}>{result.matched ? "Matched" : "Not Matched"}</Badge>
      </div>
      <p style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", textTransform: "uppercase" }}>{result.rule_category}</p>
      <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)" }}>{result.summary}</p>
      <p style={{ color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>{result.explanation_text}</p>

      {result.conditions.length > 0 && (
        <div style={{ marginTop: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Conditions
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
            {result.conditions.map((c, i) => (
              <div
                key={i}
                style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)",
                  background: "var(--surface-2)", fontSize: "var(--text-sm)",
                }}
              >
                <span>{c.condition_text} <span style={{ color: "var(--text-muted)" }}>({c.fact_key} {c.operator} {c.expected_value}, actual: {c.actual_value})</span></span>
                <Badge tone={c.satisfied ? "success" : "danger"}>{c.satisfied ? "✓" : "✗"}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: "var(--space-3)", display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
        <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>Confidence:</span>
        <ConfidenceBadge confidence={result.confidence} />
      </div>
    </Card>
  );
}

export default function AiExplainPage() {
  // ── Birth data form ──────────────────────────────────────────────────────
  const [selectedChartId, setSelectedChartId] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [ayanamsa, setAyanamsa] = useState<AyanamsaCode>("lahiri");
  const [houseSystem, setHouseSystem] = useState<HouseSystemCode>("W");

  const [savedCharts, setSavedCharts] = useState<any[]>([]);
  const [loadingCharts, setLoadingCharts] = useState(true);

  // ── Chart Summary ────────────────────────────────────────────────────────
  const [summaryStyle, setSummaryStyle] = useState<"concise" | "detailed" | "technical">("concise");
  const [summaryResult, setSummaryResult] = useState<AIResponseSchema | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // ── Ask a question ───────────────────────────────────────────────────────
  const [question, setQuestion] = useState("");
  const [questionResult, setQuestionResult] = useState<AIResponseSchema | null>(null);
  const [questionLoading, setQuestionLoading] = useState(false);
  const [questionError, setQuestionError] = useState<string | null>(null);

  // ── Explain a rule ───────────────────────────────────────────────────────
  const [ruleId, setRuleId] = useState("");
  const [ruleResult, setRuleResult] = useState<ExplanationResponse | null>(null);
  const [ruleLoading, setRuleLoading] = useState(false);
  const [ruleError, setRuleError] = useState<string | null>(null);

  const populateFromChart = (chart: any) => {
    const birthDt = new Date(chart.birth_datetime_utc);
    setBirthDate(birthDt.toISOString().split("T")[0]);
    setBirthTime(birthDt.toISOString().split("T")[1].slice(0, 5));
    setLatitude(chart.birth_latitude?.toString() || "");
    setLongitude(chart.birth_longitude?.toString() || "");
    setAyanamsa((chart.ayanamsa as AyanamsaCode) || "lahiri");
    setHouseSystem((chart.house_system as HouseSystemCode) || "W");
  };

  const loadSavedCharts = useCallback(async () => {
    try {
      setLoadingCharts(true);
      const data = await api.get<{ charts: any[]; total: number }>("/api/v1/horoscope/my-charts?limit=50&offset=0");
      setSavedCharts(data.charts || []);
      if (data.charts && data.charts.length > 0) {
        setSelectedChartId(data.charts[0].id);
        populateFromChart(data.charts[0]);
      }
    } catch {
      setSavedCharts([]);
    } finally {
      setLoadingCharts(false);
    }
  }, []);

  useEffect(() => {
    void loadSavedCharts();
  }, [loadSavedCharts]);

  const handleChartSelect = useCallback((chartId: string) => {
    setSelectedChartId(chartId);
    const chart = savedCharts.find((c) => c.id === chartId);
    if (chart) populateFromChart(chart);
  }, [savedCharts]);

  function buildBirthData(): BirthDataInput | null {
    if (!birthDate || !birthTime) return null;
    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
    return {
      birth_datetime_utc: `${birthDate}T${birthTime}Z`,
      latitude: lat,
      longitude: lng,
      ayanamsa,
      house_system: houseSystem,
    };
  }

  const handleChartSummary = useCallback(async () => {
    setSummaryError(null);
    const birthData = buildBirthData();
    if (!birthData) {
      setSummaryError("Please provide a valid birth date, time, latitude, and longitude.");
      return;
    }
    setSummaryLoading(true);
    try {
      const result = await aiApi.chartSummary(birthData, summaryStyle);
      setSummaryResult(result);
    } catch (err) {
      setSummaryError(err instanceof Error ? err.message : "Failed to generate chart summary.");
    } finally {
      setSummaryLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem, summaryStyle]);

  const handleAskQuestion = useCallback(async () => {
    setQuestionError(null);
    if (!question.trim()) {
      setQuestionError("Please enter a question.");
      return;
    }
    const birthData = buildBirthData();
    if (!birthData) {
      setQuestionError("Please provide a valid birth date, time, latitude, and longitude.");
      return;
    }
    setQuestionLoading(true);
    try {
      const result = await aiApi.answerQuestion(question, birthData);
      setQuestionResult(result);
    } catch (err) {
      setQuestionError(err instanceof Error ? err.message : "Failed to answer question.");
    } finally {
      setQuestionLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question, birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem]);

  const handleExplainRule = useCallback(async () => {
    setRuleError(null);
    if (!ruleId.trim()) {
      setRuleError("Please enter a rule ID (e.g. EYE-001).");
      return;
    }
    const birthData = buildBirthData();
    if (!birthData) {
      setRuleError("Please provide a valid birth date, time, latitude, and longitude.");
      return;
    }
    setRuleLoading(true);
    try {
      const result = await aiApi.explainRule(ruleId.trim(), birthData);
      setRuleResult(result);
    } catch (err) {
      setRuleError(err instanceof Error ? err.message : "Failed to explain rule.");
    } finally {
      setRuleLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ruleId, birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem]);

  return (
    <ResearchPatternsShell
      title="AI Explain"
      subtitle="Ask questions, summarize a chart, or explain why a specific rule fired — grounded in the chart's own computed facts, never free-floating claims."
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {/* ── Birth data form ────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Birth Data
          </h2>
          <div style={{ marginBottom: "var(--space-4)" }}>
            <label style={{ display: "block", fontSize: "var(--text-sm)", fontWeight: "var(--weight-medium)", marginBottom: "var(--space-2)", color: "var(--text-secondary)" }}>
              Load from Saved Chart
            </label>
            {loadingCharts ? (
              <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>Loading saved charts…</span>
            ) : savedCharts.length > 0 ? (
              <Select
                value={selectedChartId}
                onChange={handleChartSelect}
                options={savedCharts.map((c) => ({
                  value: c.id,
                  label: `${c.subject_name} · ${new Date(c.birth_datetime_utc).toLocaleDateString()} · ${c.place_name || "Unknown place"}`,
                }))}
                placeholder="Select a saved chart…"
              />
            ) : (
              <span style={{ fontSize: "var(--text-sm)", color: "var(--text-muted)" }}>
                No saved charts found. Enter birth details manually below or save a chart first from the Dashboard.
              </span>
            )}
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "var(--space-3)",
            }}
          >
            <Input label="Birth Date" type="date" value={birthDate} onChange={setBirthDate} required />
            <Input label="Birth Time (UTC)" type="time" value={birthTime} onChange={setBirthTime} required />
            <Input label="Latitude" type="number" placeholder="e.g. 28.6139" value={latitude} onChange={setLatitude} hint="Between -90 and 90" />
            <Input label="Longitude" type="number" placeholder="e.g. 77.2090" value={longitude} onChange={setLongitude} hint="Between -180 and 180" />
            <div style={{ width: "100%" }}>
              <Select label="Ayanamsa" options={AYANAMSA_OPTIONS} value={ayanamsa} onChange={(v) => setAyanamsa(v as AyanamsaCode)} />
            </div>
            <div style={{ width: "100%" }}>
              <Select label="House System" options={HOUSE_SYSTEM_OPTIONS} value={houseSystem} onChange={(v) => setHouseSystem(v as HouseSystemCode)} />
            </div>
          </div>
        </Card>

        {/* ── Chart Summary ──────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Chart Summary
          </h2>
          <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "flex-end", flexWrap: "wrap" }}>
            <div style={{ width: 200 }}>
              <Select label="Style" options={SUMMARY_STYLE_OPTIONS} value={summaryStyle} onChange={(v) => setSummaryStyle(v as any)} />
            </div>
            <Button variant="gold" disabled={summaryLoading} onClick={handleChartSummary}>
              {summaryLoading ? "Summarizing…" : "Summarize Chart"}
            </Button>
          </div>
          {summaryError && <p style={{ color: "var(--danger-400)", fontSize: "var(--text-sm)" }}>{summaryError}</p>}
        </Card>
        {summaryResult && <AIResponseCard result={summaryResult} />}

        {/* ── Ask a question ─────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Ask a Question
          </h2>
          <textarea
            style={textareaStyle()}
            placeholder="e.g. What does my 7th house lord's placement suggest about relationships?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <div style={{ marginTop: "var(--space-3)" }}>
            <Button variant="gold" disabled={questionLoading} onClick={handleAskQuestion}>
              {questionLoading ? "Thinking…" : "Ask Astro"}
            </Button>
          </div>
          {questionError && <p style={{ color: "var(--danger-400)", fontSize: "var(--text-sm)" }}>{questionError}</p>}
        </Card>
        {questionResult && <AIResponseCard result={questionResult} />}

        {/* ── Explain a rule ─────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Explain a Rule
          </h2>
          <p style={{ fontSize: "var(--text-sm)", color: "var(--text-tertiary)", marginTop: 0 }}>
            Enter a classical rule ID (e.g. EYE-001, TRN-SJ-001) to see whether it fired for this chart, and exactly which conditions matched.
          </p>
          <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "flex-end", flexWrap: "wrap" }}>
            <div style={{ width: 240 }}>
              <Input label="Rule ID" placeholder="e.g. EYE-001" value={ruleId} onChange={setRuleId} />
            </div>
            <Button variant="gold" disabled={ruleLoading} onClick={handleExplainRule}>
              {ruleLoading ? "Explaining…" : "Explain"}
            </Button>
          </div>
          {ruleError && <p style={{ color: "var(--danger-400)", fontSize: "var(--text-sm)" }}>{ruleError}</p>}
        </Card>
        {ruleResult && <RuleExplanationCard result={ruleResult} />}
      </div>
    </ResearchPatternsShell>
  );
}
