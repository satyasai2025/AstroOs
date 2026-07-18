"use client";

import { useState, useEffect } from "react";
import type { ResearchAnswerResponse, AvailableDomainResponse } from "@/lib/types";
import { aiApi } from "@/lib/ai";

export function ResearchAssistantPanel() {
  const [question, setQuestion] = useState("");
  const [domainFilter, setDomainFilter] = useState("");
  const [domains, setDomains] = useState<AvailableDomainResponse[]>([]);
  const [result, setResult] = useState<ResearchAnswerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    aiApi.listResearchDomains().then((r) => setDomains(r.domains)).catch(() => {});
  }, []);

  async function handleAsk() {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.researchQuery({
        question: question.trim(),
        domain_filter: domainFilter || undefined,
        max_results: 10,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Research query failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80">
        Research Assistant
      </h3>
      <p className="text-xs text-slate-400">
        Ask natural language questions about the knowledge base — books, verses,
        rules, karakatvas, and doctrinal conflicts.
      </p>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder="e.g., What does BPHS say about Jupiter in the 1st house?"
          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600 focus:border-amber-500/40 focus:outline-none focus:ring-1 focus:ring-amber-500/30"
        />
        <button
          type="button"
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          className="rounded-lg bg-amber-600 px-4 py-2 text-xs font-semibold text-cosmos-950 hover:bg-amber-500 disabled:opacity-40 transition-colors"
        >
          {loading ? "Searching…" : "Ask"}
        </button>
      </div>

      {/* Domain filter */}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setDomainFilter("")}
          className={`rounded-full px-2.5 py-1 text-xs transition-colors ${
            !domainFilter
              ? "bg-amber-500/20 text-amber-300"
              : "bg-white/5 text-slate-400 hover:bg-white/10"
          }`}
        >
          All
        </button>
        {domains.map((d) => (
          <button
            key={d.id}
            type="button"
            onClick={() => setDomainFilter(d.id)}
            className={`rounded-full px-2.5 py-1 text-xs transition-colors ${
              domainFilter === d.id
                ? "bg-amber-500/20 text-amber-300"
                : "bg-white/5 text-slate-400 hover:bg-white/10"
            }`}
          >
            {d.name}
          </button>
        ))}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Results */}
      {result && (
        <div className="space-y-3 rounded-lg border border-white/10 bg-white/3 p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-200">Answer</p>
            <span
              className={`rounded-full px-2 py-0.5 text-xs ${
                result.confidence === "high"
                  ? "bg-green-900/30 text-green-300"
                  : result.confidence === "medium"
                  ? "bg-amber-900/30 text-amber-300"
                  : "bg-red-900/30 text-red-300"
              }`}
            >
              {result.confidence} confidence
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
            {result.body}
          </p>

          {/* Evidence */}
          {result.evidence.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold text-slate-400">Sources</p>
              <div className="space-y-1">
                {result.evidence.map((e, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-slate-500">
                    <span className="shrink-0 rounded bg-white/5 px-1.5 py-0.5 font-mono text-slate-400">
                      {e.source}
                    </span>
                    <span className="line-clamp-2">{e.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Related conflicts */}
          {result.related_conflicts.length > 0 && (
            <div className="rounded border border-amber-900/30 bg-amber-900/10 p-2">
              <p className="text-xs font-semibold text-amber-300">
                Related Doctrinal Conflicts: {result.related_conflicts.join(", ")}
              </p>
            </div>
          )}

          {result.unanswered_aspects.length > 0 && (
            <div className="rounded border border-slate-800 bg-slate-900/50 p-2">
              <p className="text-xs text-slate-500">
                Unanswered aspects: {result.unanswered_aspects.join("; ")}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}