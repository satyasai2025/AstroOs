"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input, Select, type SelectOption } from "@/components/ui";
import { api } from "@/lib/api";
import { aiApi, type BirthDataInput } from "@/lib/ai";
import { SplitWorkspaceLayout } from "@/components/layout/SplitWorkspaceLayout";
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

import { useWorkflowStore } from "@/lib/store";

const COMMON_RULES = [
  { id: "RULE-YOGA-003", name: "Gaja Kesari Yoga", category: "Yogas", description: "Jupiter in Kendra from Moon (houses 1, 4, 7, 10)" },
  { id: "RULE-YOGA-008", name: "Lakshmi Yoga", category: "Wealth", description: "2nd and 11th lord association for wealth accumulation" },
  { id: "RULE-YOGA-004", name: "Dharma-Karmadhipati Yoga", category: "Career", description: "Kendra and Trikona lord association producing high status" },
  { id: "RULE-YOGA-007", name: "Budhaditya Yoga", category: "Intellect", description: "Bhadra / Mercury Panch Mahapurusha analytical intellect" },
  { id: "RULE-HOUSE-002", name: "Netra Dosha Rule", category: "Health", description: "Afflictions to 2nd/12th houses affecting eye health" },
  { id: "RULE-TRANSIT-001", name: "Saturn-Jupiter Double Transit", category: "Transits", description: "Simultaneous Saturn & Jupiter transit activation" },
];

function ConfidenceBadge({ confidence }: { confidence?: number | string }) {
  let pct = 85;
  if (typeof confidence === "number") {
    pct = Math.round(confidence <= 1 ? confidence * 100 : confidence);
  } else if (typeof confidence === "string") {
    const parsed = parseFloat(confidence);
    if (!Number.isNaN(parsed)) {
      pct = Math.round(parsed <= 1 ? parsed * 100 : parsed);
    } else if (confidence.toLowerCase() === "high") {
      pct = 90;
    } else if (confidence.toLowerCase() === "medium") {
      pct = 70;
    } else if (confidence.toLowerCase() === "low") {
      pct = 40;
    }
  }
  const tone = pct >= 80 ? "success" : pct >= 50 ? "gold" : "danger";
  return <Badge tone={tone}>{pct}% Confidence</Badge>;
}

function AIResponseCard({ result }: { result: AIResponseSchema }) {
  const [copied, setCopied] = useState(false);
  const [noteSaved, setNoteSaved] = useState(false);

  const handleCopy = async () => {
    const textToCopy = `${result.title}\n\n${result.body}`;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const handleSaveNote = () => {
    try {
      const stored = localStorage.getItem("astroos_ai_saved_notes");
      const list = stored ? JSON.parse(stored) : [];
      list.push({ title: result.title, text: result.body, date: new Date().toISOString() });
      localStorage.setItem("astroos_ai_saved_notes", JSON.stringify(list));
      setNoteSaved(true);
      setTimeout(() => setNoteSaved(false), 2500);
    } catch {
      setNoteSaved(true);
      setTimeout(() => setNoteSaved(false), 2500);
    }
  };

  // Prevent duplicate rendering if body already starts with or equals summary
  const shouldRenderSummary =
    result.summary &&
    !result.body.includes(result.summary.slice(0, 40)) &&
    result.summary !== result.body;

  return (
    <Card padding="var(--space-4)">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-3)", flexWrap: "wrap" }}>
        <div>
          <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0, color: "var(--text-primary)" }}>
            {result.title}
          </h3>
          {shouldRenderSummary && (
            <p style={{ color: "var(--text-secondary)", fontSize: "var(--text-sm)", marginTop: 4 }}>
              {result.summary}
            </p>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <ConfidenceBadge confidence={result.confidence} />
          <button
            type="button"
            onClick={handleCopy}
            className="obsidian-btn-secondary text-xs px-2 py-1"
            title="Copy answer"
          >
            {copied ? "✓ Copied" : "Copy"}
          </button>
          <button
            type="button"
            onClick={handleSaveNote}
            className="obsidian-btn-secondary text-xs px-2 py-1"
            title="Save as research note"
          >
            {noteSaved ? "✓ Saved" : "Save Note"}
          </button>
        </div>
      </div>

      <div
        style={{
          marginTop: "var(--space-3)",
          color: "var(--text-primary)",
          whiteSpace: "pre-wrap",
          lineHeight: 1.6,
          fontSize: "var(--text-sm)",
          background: "var(--surface-2)",
          padding: "var(--space-3)",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border-subtle)",
        }}
      >
        {result.body}
      </div>

      {result.recommendations.length > 0 && (
        <div style={{ marginTop: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Recommendations
          </h4>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>
            {result.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {result.citations.length > 0 && (
        <div style={{ marginTop: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Classical Citations
          </h4>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: "var(--text-xs)", color: "var(--text-secondary)" }}>
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
          Grounding Sources: {result.sources.join(", ")}
        </p>
      )}
    </Card>
  );
}

function RuleExplanationCard({ result }: { result: ExplanationResponse }) {
  return (
    <Card padding="var(--space-4)">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "var(--space-3)" }}>
        <div>
          <h3 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
            {result.rule_name} <span style={{ color: "var(--text-tertiary)", fontWeight: "var(--weight-regular)" }}>({result.rule_id})</span>
          </h3>
          <p style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", textTransform: "uppercase", margin: "2px 0 0 0" }}>
            Category: {result.rule_category}
          </p>
        </div>
        <Badge tone={result.matched ? "success" : "danger"}>{result.matched ? "✓ Rule Fired" : "✗ Not Matched"}</Badge>
      </div>

      <div style={{ marginTop: "var(--space-3)", color: "var(--text-primary)", whiteSpace: "pre-wrap", fontSize: "var(--text-sm)" }}>
        {result.explanation_text}
      </div>

      {result.conditions.length > 0 && (
        <div style={{ marginTop: "var(--space-3)" }}>
          <h4 style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Rule Conditions &amp; Evaluation
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", marginTop: 4 }}>
            {result.conditions.map((c, i) => (
              <div
                key={i}
                style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "var(--space-2) var(--space-3)", borderRadius: "var(--radius-sm)",
                  background: "var(--surface-2)", fontSize: "var(--text-xs)",
                }}
              >
                <span>
                  <strong>{c.condition_text}</strong>{" "}
                  <span style={{ color: "var(--text-muted)" }}>({c.fact_key} {c.operator} {c.expected_value}, actual: {c.actual_value})</span>
                </span>
                <Badge tone={c.satisfied ? "success" : "danger"}>{c.satisfied ? "✓ Matched" : "✗ Unmet"}</Badge>
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

const PROMPT_CHIPS = [
  "Analyze Monetary Gains",
  "Explain Current Transits",
  "Career Impact in Active Dasha",
  "Health & Vitality Overview",
];

export default function AiExplainPage() {
  const storeRequest = useWorkflowStore((s) => s.request);
  const setRequest = useWorkflowStore((s) => s.setRequest);

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
  const [ruleId, setRuleId] = useState("RULE-YOGA-003");
  const [ruleResult, setRuleResult] = useState<ExplanationResponse | null>(null);
  const [ruleLoading, setRuleLoading] = useState(false);
  const [ruleError, setRuleError] = useState<string | null>(null);
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);

  const populateFromChart = useCallback((chart: any) => {
    const birthDt = new Date(chart.birth_datetime_utc);
    setBirthDate(birthDt.toISOString().split("T")[0]);
    setBirthTime(birthDt.toISOString().split("T")[1]?.slice(0, 5) || "12:00");
    setLatitude(chart.birth_latitude?.toString() || "");
    setLongitude(chart.birth_longitude?.toString() || "");
    setAyanamsa((chart.ayanamsa as AyanamsaCode) || "lahiri");
    setHouseSystem((chart.house_system as HouseSystemCode) || "W");

    const workflowReq = {
      subject_name: chart.subject_name || "Active Chart",
      birth_datetime_utc: chart.birth_datetime_utc,
      latitude: typeof chart.birth_latitude === "number" ? chart.birth_latitude : parseFloat(chart.birth_latitude || "0"),
      longitude: typeof chart.birth_longitude === "number" ? chart.birth_longitude : parseFloat(chart.birth_longitude || "0"),
      place_name: chart.place_name || undefined,
      gender: (chart.gender as any) || "other",
      ayanamsa: (chart.ayanamsa as any) || "lahiri",
      house_system: (chart.house_system as any) || "W",
    };
    setRequest(workflowReq as any);
    if (typeof window !== "undefined") {
      localStorage.setItem("astroos_active_chart_request", JSON.stringify(workflowReq));
    }
  }, [setRequest]);

  useEffect(() => {
    if (storeRequest) {
      const birthDt = new Date(storeRequest.birth_datetime_utc);
      setBirthDate(birthDt.toISOString().split("T")[0]);
      setBirthTime(birthDt.toISOString().split("T")[1]?.slice(0, 5) || "12:00");
      setLatitude(storeRequest.latitude?.toString() || "");
      setLongitude(storeRequest.longitude?.toString() || "");
      setAyanamsa((storeRequest.ayanamsa as AyanamsaCode) || "lahiri");
      setHouseSystem((storeRequest.house_system as HouseSystemCode) || "W");
    }
  }, [storeRequest]);

  const loadSavedCharts = useCallback(async () => {
    try {
      setLoadingCharts(true);
      const data = await api.get<{ charts: any[]; total: number }>("/api/v1/horoscope/my-charts?limit=50&offset=0");
      setSavedCharts(data.charts || []);

      const storedActiveId = typeof window !== "undefined"
        ? localStorage.getItem("astroos_active_chart_id") || localStorage.getItem("astroos_last_viewed_chart_id")
        : null;

      if (!storeRequest && data.charts && data.charts.length > 0) {
        const found = storedActiveId ? data.charts.find((c) => c.id === storedActiveId) : null;
        const targetChart = found || data.charts[0];
        setSelectedChartId(targetChart.id);
        populateFromChart(targetChart);
      }
    } catch {
      setSavedCharts([]);
    } finally {
      setLoadingCharts(false);
    }
  }, [storeRequest, populateFromChart]);

  useEffect(() => {
    void loadSavedCharts();
  }, [loadSavedCharts]);

  const handleChartSelect = useCallback((chartId: string) => {
    setSelectedChartId(chartId);
    if (typeof window !== "undefined") {
      localStorage.setItem("astroos_active_chart_id", chartId);
      localStorage.setItem("astroos_last_viewed_chart_id", chartId);
    }
    const chart = savedCharts.find((c) => c.id === chartId);
    if (chart) populateFromChart(chart);
  }, [savedCharts, populateFromChart]);

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
      setSummaryError("⚠️ Active chart data is required. Please select a saved chart from above or fill in the birth details before evaluating.");
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
  }, [birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem, summaryStyle]);

  const handleAskQuestion = useCallback(async (promptText?: string) => {
    setQuestionError(null);
    const query = promptText || question;
    if (!query.trim()) {
      setQuestionError("Please enter a question.");
      return;
    }
    const birthData = buildBirthData();
    if (!birthData) {
      setQuestionError("⚠️ Active chart data is required. Please select a saved chart from above or fill in the birth details before evaluating.");
      return;
    }
    setQuestionLoading(true);
    try {
      const result = await aiApi.answerQuestion(query, birthData);
      setQuestionResult(result);
    } catch (err) {
      setQuestionError(err instanceof Error ? err.message : "Failed to answer question.");
    } finally {
      setQuestionLoading(false);
    }
  }, [question, birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem]);

  const handleExplainRule = useCallback(async (targetRuleId?: string) => {
    setRuleError(null);
    const rId = targetRuleId || ruleId;
    if (!rId.trim()) {
      setRuleError("Please enter a rule ID (e.g. RULE-YOGA-003 or GAJA-001).");
      return;
    }
    const birthData = buildBirthData();
    if (!birthData) {
      setRuleError("⚠️ Active chart data is required. Please select a saved chart from above or fill in the birth details before evaluating.");
      return;
    }
    setRuleLoading(true);
    try {
      const result = await aiApi.explainRule(rId.trim(), birthData);
      setRuleResult(result);
    } catch (err) {
      setRuleError(err instanceof Error ? err.message : "Failed to explain rule.");
    } finally {
      setRuleLoading(false);
    }
  }, [ruleId, birthDate, birthTime, latitude, longitude, ayanamsa, houseSystem]);

  return (
    <SplitWorkspaceLayout
      title="AI Explain"
      subtitle="Ask questions, summarize a chart, or explain why a specific rule fired — grounded in the chart's own computed facts, never free-floating claims."
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        {/* ── Birth data form ────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
              Birth Data
            </h2>
            {storeRequest && (
              <Badge tone="success">Active Session Chart</Badge>
            )}
          </div>
          <div style={{ marginBottom: "var(--space-4)" }}>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Load from Saved Chart
            </label>
            {loadingCharts ? (
              <span className="text-xs text-slate-500 dark:text-slate-400">Loading saved charts…</span>
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
              <span className="text-xs text-slate-500 dark:text-slate-400">
                No saved charts found. Enter birth details manually below.
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
            Chart Summary &amp; Synthesis
          </h2>
          <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "flex-end", flexWrap: "wrap" }}>
            <div style={{ width: 200 }}>
              <Select label="Style" options={SUMMARY_STYLE_OPTIONS} value={summaryStyle} onChange={(v) => setSummaryStyle(v as any)} />
            </div>
            <Button variant="gold" disabled={summaryLoading} onClick={handleChartSummary}>
              {summaryLoading ? "Summarizing…" : "Summarize Chart"}
            </Button>
          </div>
          {summaryError && (
            <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-300 flex items-center justify-between">
              <span>{summaryError}</span>
              {savedCharts.length > 0 && !selectedChartId && (
                <button
                  type="button"
                  onClick={() => handleChartSelect(savedCharts[0].id)}
                  className="ml-3 shrink-0 rounded bg-amber-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-amber-500 transition shadow-sm"
                >
                  Load {savedCharts[0].subject_name || "Active Chart"}
                </button>
              )}
            </div>
          )}
        </Card>
        {summaryResult && <AIResponseCard result={summaryResult} />}

        {/* ── Ask a question ─────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", marginTop: 0 }}>
            Ask Astro
          </h2>

          {/* Quick Prompt Chips */}
          <div style={{ marginBottom: "var(--space-3)" }}>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Suggested Queries:
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {PROMPT_CHIPS.map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => {
                    setQuestion(chip);
                    void handleAskQuestion(chip);
                  }}
                  className="rounded-full border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/80 px-2.5 py-1 text-xs text-slate-700 dark:text-slate-300 hover:border-amber-500 hover:text-amber-500 transition"
                >
                  ⚡ {chip}
                </button>
              ))}
            </div>
          </div>

          <textarea
            className="w-full bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-300 dark:border-slate-800 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 rounded-lg p-3 text-sm min-h-[90px] resize-y placeholder:text-slate-400 dark:placeholder:text-slate-500 transition shadow-sm outline-none"
            placeholder="e.g. What does my 10th house indicate for career gains during current transits?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <div style={{ marginTop: "var(--space-3)" }}>
            <Button variant="gold" disabled={questionLoading} onClick={() => void handleAskQuestion()}>
              {questionLoading ? "Thinking…" : "Ask Astro"}
            </Button>
          </div>
          {questionError && (
            <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-300 flex items-center justify-between">
              <span>{questionError}</span>
              {savedCharts.length > 0 && !selectedChartId && (
                <button
                  type="button"
                  onClick={() => handleChartSelect(savedCharts[0].id)}
                  className="ml-3 shrink-0 rounded bg-amber-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-amber-500 transition shadow-sm"
                >
                  Load {savedCharts[0].subject_name || "Active Chart"}
                </button>
              )}
            </div>
          )}
        </Card>
        {questionResult && <AIResponseCard result={questionResult} />}

        {/* ── Explain a rule ─────────────────────────────────────────────── */}
        <Card padding="var(--space-4)">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
              Explain a Rule
            </h2>
            <Button variant="ghost" size="sm" onClick={() => setIsRuleModalOpen(true)}>
              Browse All Rules
            </Button>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Test whether a classical rule or yoga fired for this chart and evaluate matched conditions.
          </p>

          {/* Quick rule chips */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, margin: "8px 0 12px 0" }}>
            {COMMON_RULES.map((r) => (
              <button
                key={r.id}
                type="button"
                onClick={() => {
                  setRuleId(r.id);
                  void handleExplainRule(r.id);
                }}
                className={`rounded px-2.5 py-1 text-xs font-medium border transition ${
                  ruleId === r.id
                    ? "border-amber-500 bg-amber-500/10 text-amber-600 dark:text-amber-400 font-semibold"
                    : "border-slate-300 dark:border-slate-800 bg-slate-100/70 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 hover:border-amber-500 hover:text-amber-500"
                }`}
              >
                {r.id}: {r.name}
              </button>
            ))}
          </div>

          <div style={{ display: "flex", gap: "var(--space-3)", alignItems: "flex-end", flexWrap: "wrap" }}>
            <div style={{ width: 240 }}>
              <Input label="Rule ID" placeholder="e.g. RULE-YOGA-003" value={ruleId} onChange={setRuleId} />
            </div>
            <Button variant="gold" disabled={ruleLoading} onClick={() => void handleExplainRule()}>
              {ruleLoading ? "Explaining…" : "Explain Rule"}
            </Button>
          </div>
          {ruleError && (
            <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-300 flex items-center justify-between">
              <span>{ruleError}</span>
              {savedCharts.length > 0 && !selectedChartId && (
                <button
                  type="button"
                  onClick={() => handleChartSelect(savedCharts[0].id)}
                  className="ml-3 shrink-0 rounded bg-amber-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-amber-500 transition shadow-sm"
                >
                  Load {savedCharts[0].subject_name || "Active Chart"}
                </button>
              )}
            </div>
          )}
        </Card>
        {ruleResult && <RuleExplanationCard result={ruleResult} />}

        {/* ── Browse Rules Reference Modal ── */}
        {isRuleModalOpen && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 100,
              backgroundColor: "rgba(0, 0, 0, 0.7)",
              backdropFilter: "blur(4px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "var(--space-4)",
            }}
          >
            <div
              style={{
                width: "100%",
                maxWidth: 600,
                maxHeight: "80vh",
                overflowY: "auto",
                backgroundColor: "var(--bg-card)",
                borderRadius: "var(--radius-lg)",
                border: "1px solid var(--border-primary)",
                padding: "var(--space-4)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-3)" }}>
                <h3 style={{ fontSize: "var(--text-md)", fontWeight: "var(--weight-bold)", margin: 0, color: "var(--text-primary)" }}>
                  Classical Rules &amp; Yogas Catalog
                </h3>
                <button
                  type="button"
                  onClick={() => setIsRuleModalOpen(false)}
                  className="text-slate-400 hover:text-slate-100 text-lg leading-none"
                >
                  ×
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
                {COMMON_RULES.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => {
                      setRuleId(r.id);
                      setIsRuleModalOpen(false);
                      void handleExplainRule(r.id);
                    }}
                    style={{
                      padding: "var(--space-3)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--border-subtle)",
                      background: "var(--surface-2)",
                      cursor: "pointer",
                    }}
                    className="hover:border-amber-500 transition"
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "var(--text-xs)", fontWeight: "bold", color: "var(--accent)" }}>
                        {r.id} · {r.name}
                      </span>
                      <Badge tone="violet">{r.category}</Badge>
                    </div>
                    <p style={{ fontSize: "var(--text-xs)", color: "var(--text-secondary)", marginTop: 4, margin: 0 }}>
                      {r.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </SplitWorkspaceLayout>
  );
}
