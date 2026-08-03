"use client";

/**
 * AstroOS — Natural-Language Pattern Q&A (Module 27, Phase 3d)
 *
 * Ask a plain-language question ("what correlates with Marriage?") and
 * get an answer grounded in the shared, already-discovered patterns. The
 * real patterns the answer drew from are always shown alongside it, so a
 * researcher can check the generated text against the actual statistics
 * rather than taking it on trust.
 */

import { useState } from "react";
import { Badge, Button, Card, Input, Table, type TableColumn } from "@/components/ui";
import { researchCasesApi } from "@/lib/researchCases";
import type { PatternListItem, PatternQuestionResponse } from "@/lib/types";
import { pct } from "./patternConstants";
import { ResearchPatternsShell } from "./ResearchPatternsShell";

const SAMPLE_QUESTIONS = [
  "What correlates with Marriage?",
  "Which patterns predict Death of Parent?",
  "What do we know about Education events?",
  "Show me the strongest findings overall",
];

export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<PatternQuestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(q?: string) {
    const text = (q ?? question).trim();
    if (!text) return;
    setQuestion(text);
    setLoading(true);
    setError(null);
    try {
      setResult(await researchCasesApi.askAboutPatterns({ question: text }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not answer that question.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const columns: TableColumn<PatternListItem>[] = [
    { key: "event_type", label: "Event", render: (p) => <Badge tone="cyan">{p.event_type}</Badge> },
    { key: "description", label: "Pattern", render: (p) => <span style={{ fontSize: "var(--text-sm)" }}>{p.description}</span> },
    { key: "sample_size", label: "Support", align: "right", render: (p) => p.sample_size },
    { key: "confidence_score", label: "Confidence", align: "right", render: (p) => pct(p.confidence_score) },
  ];

  return (
    <ResearchPatternsShell title="Ask" subtitle="Ask questions about the discovered patterns">
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
        <Card glow="cyan">
          <p style={{ color: "var(--text-primary)", margin: 0, fontSize: "var(--text-sm)" }}>
            Ask in plain language. Answers are generated <strong>only</strong> from patterns already discovered in
            the shared dataset — the exact patterns used are listed below every answer so you can check the
            wording against the real statistics. This never runs new discovery and never changes any saved data.
          </p>
        </Card>

        {error && (
          <Card glow="gold">
            <p style={{ color: "var(--text-primary)", margin: 0 }}>{error}</p>
          </Card>
        )}

        <Card padding="var(--space-4)">
          <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "flex-end" }}>
            <Input
              label="Your question"
              placeholder="e.g. What correlates with Marriage?"
              value={question}
              onChange={setQuestion}
            />
            <Button onClick={() => ask()} disabled={loading || !question.trim()}>
              {loading ? "Thinking…" : "Ask"}
            </Button>
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: "var(--space-3)" }}>
            {SAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => ask(q)}
                disabled={loading}
                style={{
                  background: "var(--surface-glass-strong)",
                  border: "1px solid var(--border-default)",
                  borderRadius: "var(--radius-full)",
                  color: "var(--text-secondary)",
                  fontSize: "var(--text-xs)",
                  padding: "5px 12px",
                  cursor: loading ? "default" : "pointer",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </Card>

        {result && (
          <>
            <Card padding="var(--space-4)">
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "var(--space-2)" }}>
                <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>Answer</h2>
                {result.matched_event_type && <Badge tone="violet">{result.matched_event_type}</Badge>}
                <span style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", marginLeft: "auto" }}>
                  {result.execution_time_ms}ms
                </span>
              </div>
              <p style={{ color: "var(--text-primary)", margin: 0, fontSize: "var(--text-base)", lineHeight: 1.6 }}>
                {result.answer}
              </p>
            </Card>

            <Card padding="0">
              <div style={{ padding: "var(--space-4)", borderBottom: "1px solid var(--border-default)" }}>
                <h2 style={{ fontSize: "var(--text-lg)", fontWeight: "var(--weight-semibold)", margin: 0 }}>
                  Patterns this answer used ({result.patterns.length})
                </h2>
                <p style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", margin: "4px 0 0" }}>
                  Real rows from the shared dataset — the answer above can only reference these.
                </p>
              </div>
              {result.patterns.length === 0 ? (
                <p style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", padding: "var(--space-4)" }}>
                  No matching patterns were found for this question.
                </p>
              ) : (
                <Table columns={columns} rows={result.patterns} />
              )}
            </Card>
          </>
        )}
      </div>
    </ResearchPatternsShell>
  );
}
