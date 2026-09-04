"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Badge, Button, Card } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import type { AIResponseSchema } from "@/lib/types";

/**
 * AstroOS — Ask AstroOS (RAG-grounded knowledge Q&A, Phase IV IV.3.1)
 *
 * Frontend for POST /api/v1/ai/knowledge-qa. Requires AI_BACKEND=local_llm
 * and an embedded knowledge base to return a real grounded answer (see
 * docs/rag-knowledge-search.md) — with neither set up, the backend still
 * responds normally, just with an honest "No Matching Source Found"
 * result rather than an error, which this page renders as-is so it's
 * obvious what state the feature is in.
 */
function AskAstroOSContent() {
  const searchParams = useSearchParams();
  const initialQ = searchParams?.get("q") || "";
  const [question, setQuestion] = useState(initialQ);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIResponseSchema | null>(null);

  useEffect(() => {
    if (initialQ && !question) {
      setQuestion(initialQ);
    }
  }, [initialQ]);

  async function handleAsk(queryToAsk?: string) {
    const textToQuery = (queryToAsk ?? question).trim();
    if (!textToQuery) return;
    if (queryToAsk) setQuestion(queryToAsk);
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.post<AIResponseSchema>("/api/v1/ai/knowledge-qa", {
        question: textToQuery,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to reach AstroOS. Is the server running?");
    } finally {
      setLoading(false);
    }
  }

  const noSourceFound = result?.sources.length === 0;

  const EXAMPLE_QUESTIONS = [
    "What is the effect of Jupiter in the 7th house for marriage?",
    "Explain Gaja Kesari Yoga and its planetary conditions",
    "What are the classical significations (Karakatvas) of the Sun?",
    "What results are given by Mars in the 10th house?",
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
            Ask AstroOS
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Ask a Vedic astrology question. Answers are strictly grounded in classical texts (BPHS, Saravali) and cited with reference sources.
          </p>
        </div>
        <Button href="/knowledge" variant="secondary">
          ← Back to Knowledge
        </Button>
      </div>

      <Card>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleAsk();
            }}
            placeholder="e.g. What is the effect of Saturn in the 7th house?"
            className="flex-1 rounded-lg px-3.5 py-2.5 text-sm outline-none"
            style={{
              backgroundColor: "var(--bg-surface, var(--bg-card))",
              border: "1px solid var(--border-primary)",
              color: "var(--text-primary)",
            }}
          />
          <Button onClick={() => handleAsk()} disabled={loading || !question.trim()} variant="primary">
            {loading ? "Searching classical texts…" : "Ask AstroOS"}
          </Button>
        </div>

        {/* Quick Question Chips */}
        <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800">
          <p className="mb-2 text-xs font-medium text-slate-400">
            Suggested questions to try:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => handleAsk(q)}
                className="text-left text-xs px-2.5 py-1 rounded-md transition-colors hover:border-cyan-500 hover:text-cyan-400"
                style={{
                  backgroundColor: "var(--bg-subtle, rgba(255, 255, 255, 0.03))",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-secondary)",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {error && (
        <Card style={{ borderColor: "var(--danger-400, #ef4444)" }}>
          <p className="text-sm" style={{ color: "var(--danger-400, #ef4444)" }}>{error}</p>
        </Card>
      )}

      {result && (
        <Card style={{ borderLeft: noSourceFound ? "3px solid var(--gold-400)" : "3px solid var(--success-400)" }}>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
              {result.title}
            </h2>
            <Badge tone={noSourceFound ? "neutral" : "success"}>
              {noSourceFound ? "No direct citation" : `Confidence: ${result.confidence}`}
            </Badge>
          </div>
          <p className="whitespace-pre-line text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {result.body}
          </p>
          {result.sources.length > 0 && (
            <div className="mt-4 pt-3" style={{ borderTop: "1px solid var(--border-primary)" }}>
              <p className="mb-1.5 text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
                Verified Classical Sources
              </p>
              <div className="flex flex-wrap gap-1.5">
                {result.sources.map((s) => (
                  <Badge key={s} tone="cyan">{s}</Badge>
                ))}
              </div>
            </div>
          )}

          {noSourceFound && (
            <div className="mt-4 pt-3 flex flex-wrap items-center gap-2" style={{ borderTop: "1px solid var(--border-subtle)" }}>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                Need more information?
              </span>
              <Button href="/knowledge/browse?type=karakatvas" variant="secondary">
                Browse 5,000+ Karakatvas
              </Button>
              <Button href="/help" variant="secondary">
                View Help Guide
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

export default function AskAstroOSPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-400">Loading Ask AstroOS…</div>}>
      <AskAstroOSContent />
    </Suspense>
  );
}
