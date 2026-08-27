"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { api } from "@/lib/api";
import { useCurrentUser } from "@/lib/auth";
import { Badge, Button, Card, Icon } from "@/components/ui";

interface Citation {
  source: string;
  chapter: number;
  verse: string;
  sanskrit_sloka?: string;
  translation: string;
  confidence: number;
}

interface RAGResponse {
  query: string;
  plan_tier: string;
  ai_backend_used: string;
  interpretation: string;
  provenance_citations: Citation[];
  technique_isolation_valid: boolean;
  grounding_score: number;
}

export default function GovernedAIPage() {
  const { data: user } = useCurrentUser();
  const [query, setQuery] = useState("Explain Gaja Kesari Yoga and its manifestation");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleAsk = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await api.post<RAGResponse>("/api/v1/ai/governed-rag", {
        query: query.trim(),
      });
      setResult(data);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to query Governed AI.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-8">
          {/* ── Header ── */}
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-0.5 text-xs font-semibold text-cyan-400">
              <span>🤖</span>
              <span>Governed Astrological AI Copilot &bull; Shastra Grounded</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-white mt-2">
              Governed RAG &amp; Astrological AI
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Context-aware astrological synthesis strictly anchored in classical Sanskrit shastras (BPHS, Jaimini, Phaladeepika) with explicit verse provenance.
            </p>
          </div>

          {/* ── Query Box ── */}
          <Card className="p-6 border border-slate-800 bg-slate-900/60 space-y-4">
            <label className="text-xs font-bold text-slate-300">
              Ask a Classical Astrological or Research Question:
            </label>
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. How does Jupiter aspecting 10th house impact career?"
                className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:border-cyan-400 focus:outline-none"
              />
              <button
                onClick={handleAsk}
                disabled={loading}
                className="rounded-xl bg-cyan-500 hover:bg-cyan-400 px-6 py-2.5 text-xs font-bold text-slate-950 transition shadow whitespace-nowrap"
              >
                {loading ? "Synthesizing..." : "Ask Governed AI"}
              </button>
            </div>

            {/* Quick Prompts */}
            <div className="flex flex-wrap items-center gap-2 pt-2 text-[11px] text-slate-400">
              <span>Suggested:</span>
              <button
                onClick={() => setQuery("Explain Gaja Kesari Yoga")}
                className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300 border border-slate-700"
              >
                Gaja Kesari Yoga
              </button>
              <button
                onClick={() => setQuery("Hamsa Mahapurusha yoga formation")}
                className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300 border border-slate-700"
              >
                Hamsa Yoga
              </button>
              <button
                onClick={() => setQuery("Vimshottari Dasha timing principles")}
                className="rounded-lg bg-slate-800 hover:bg-slate-750 px-2.5 py-1 text-slate-300 border border-slate-700"
              >
                Vimshottari Dasha
              </button>
            </div>
          </Card>

          {errorMessage && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs text-red-400">
              {errorMessage}
            </div>
          )}

          {/* ── AI Response Card with Strict Provenance ── */}
          {result && (
            <div className="space-y-6">
              <Card className="p-6 border border-slate-800 bg-slate-900/80 space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2.5 py-0.5 text-[10px] font-bold">
                      {result.plan_tier} Tier Engine
                    </span>
                    <span className="text-xs text-slate-400">
                      Backend: {result.ai_backend_used}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-emerald-400 font-bold">
                      Grounding: {(result.grounding_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-slate-500">&bull;</span>
                    <span className="text-purple-400 font-bold">Ephemeris Isolated</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h3 className="text-sm font-bold text-white">Astrological Synthesis</h3>
                  <div className="text-xs text-slate-200 leading-relaxed space-y-2">
                    <p>{result.interpretation}</p>
                  </div>
                </div>

                {/* Shastra Provenance Citations */}
                <div className="space-y-3 pt-3 border-t border-slate-800">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Classical Shastra Provenance Citations
                  </h4>
                  <div className="grid grid-cols-1 gap-3">
                    {result.provenance_citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-cyan-400">
                            📜 {c.source} — Chapter {c.chapter}, {c.verse}
                          </span>
                          <span className="text-[10px] text-emerald-400 font-bold">
                            {(c.confidence * 100).toFixed(0)}% Match
                          </span>
                        </div>
                        {c.sanskrit_sloka && (
                          <div className="rounded bg-slate-900/60 p-2 text-xs text-amber-300 font-mono">
                            {c.sanskrit_sloka}
                          </div>
                        )}
                        <p className="text-xs text-slate-300 italic">
                          &ldquo;{c.translation}&rdquo;
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
