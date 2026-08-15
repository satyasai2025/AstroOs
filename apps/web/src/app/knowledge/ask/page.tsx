"use client";

import { useState } from "react";
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
export default function AskAstroOSPage() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIResponseSchema | null>(null);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.post<AIResponseSchema>("/api/v1/ai/knowledge-qa", {
        question: question.trim(),
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to reach AstroOS. Is the server running?");
    } finally {
      setLoading(false);
    }
  }

  const noSourceFound = result?.title === "No Matching Source Found";

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>
          Ask AstroOS
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Ask a general astrology question. Answers are grounded in AstroOS's own
          classical-text knowledge base — never made up. See{" "}
          <code style={{ fontSize: "var(--text-xs)" }}>docs/rag-knowledge-search.md</code>{" "}
          for how to set up the local model this feature needs.
        </p>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleAsk();
            }}
            placeholder="e.g. What does Jupiter in the 7th house mean for marriage?"
            className="flex-1 rounded-lg px-3 py-2 text-sm"
            style={{
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border-primary)",
              color: "var(--text-primary)",
            }}
          />
          <Button onClick={handleAsk} disabled={loading || !question.trim()}>
            {loading ? "Asking…" : "Ask"}
          </Button>
        </div>
      </Card>

      {error && (
        <Card style={{ borderColor: "var(--danger-400, #ef4444)" }}>
          <p className="text-sm" style={{ color: "var(--danger-400, #ef4444)" }}>{error}</p>
        </Card>
      )}

      {result && (
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
              {result.title}
            </h2>
            <Badge tone={noSourceFound ? "neutral" : "success"}>
              {noSourceFound ? "No source" : `Confidence: ${result.confidence}`}
            </Badge>
          </div>
          <p className="whitespace-pre-line text-sm" style={{ color: "var(--text-secondary)" }}>
            {result.body}
          </p>
          {result.sources.length > 0 && (
            <div className="mt-4 pt-3" style={{ borderTop: "1px solid var(--border-primary)" }}>
              <p className="mb-1 text-xs font-semibold" style={{ color: "var(--text-muted)" }}>
                Sources used
              </p>
              <div className="flex flex-wrap gap-1.5">
                {result.sources.map((s) => (
                  <Badge key={s} tone="cyan">{s}</Badge>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
