"use client";

import { useState, useEffect } from "react";
import type { HypothesisTemplateResponse, GeneratedHypothesisResponse } from "@/lib/types";
import { aiApi, type BirthDataInput } from "@/lib/ai";

interface Props {
  birthData: BirthDataInput;
}

export function HypothesisPanel({ birthData }: Props) {
  const [templates, setTemplates] = useState<HypothesisTemplateResponse[]>([]);
  const [hypotheses, setHypotheses] = useState<GeneratedHypothesisResponse[]>([]);
  const [domainFilter, setDomainFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    aiApi.listHypothesisTemplates()
      .then((r) => setTemplates(r.templates))
      .catch(() => {});
  }, []);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.generateHypotheses({
        ...birthData,
        domain_filter: domainFilter || undefined,
        max_hypotheses: 8,
      });
      setHypotheses(res.hypotheses);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hypothesis generation failed.");
    } finally {
      setLoading(false);
    }
  }

  const domains = [...new Set(templates.map((t) => t.domain))];

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80">
        Hypothesis Generator
      </h3>
      <p className="text-xs text-slate-400">
        Generate testable astrological hypotheses from this chart. Each hypothesis
        includes chart-specific evidence and a falsifiable prediction.
      </p>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setDomainFilter("")}
          className={`rounded-full px-2.5 py-1 text-xs transition-colors ${
            !domainFilter
              ? "bg-amber-500/20 text-amber-300"
              : "bg-white/5 text-slate-400 hover:bg-white/10"
          }`}
        >
          All Domains
        </button>
        {domains.map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => setDomainFilter(d)}
            className={`rounded-full px-2.5 py-1 text-xs transition-colors ${
              domainFilter === d
                ? "bg-amber-500/20 text-amber-300"
                : "bg-white/5 text-slate-400 hover:bg-white/10"
            }`}
          >
            {d.charAt(0).toUpperCase() + d.slice(1)}
          </button>
        ))}
        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="ml-auto rounded-lg bg-amber-600 px-4 py-1.5 text-xs font-semibold text-cosmos-950 hover:bg-amber-500 disabled:opacity-40 transition-colors"
        >
          {loading ? "Generating…" : "Generate Hypotheses"}
        </button>
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      {/* Results */}
      {hypotheses.length > 0 && (
        <div className="space-y-3">
          {hypotheses.map((h) => (
            <div
              key={h.hypothesis_id}
              className="rounded-lg border border-white/10 bg-white/3 p-3 space-y-2"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-200">{h.title}</p>
                  <p className="text-xs text-slate-500">
                    {h.hypothesis_id} · {h.domain} · Priority {h.priority}/10
                  </p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    h.confidence === "high"
                      ? "bg-green-900/30 text-green-300"
                      : "bg-amber-900/30 text-amber-300"
                  }`}
                >
                  {h.confidence}
                </span>
              </div>

              <p className="text-xs text-slate-300">{h.description}</p>

              {/* Supporting evidence */}
              {h.supporting_evidence.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-semibold text-green-400/80">Supporting Evidence</p>
                  <ul className="space-y-0.5">
                    {h.supporting_evidence.map((ev, i) => (
                      <li key={i} className="text-xs text-slate-400">• {ev}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Testable prediction */}
              <div className="rounded border border-amber-900/30 bg-amber-900/10 p-2">
                <p className="text-xs font-semibold text-amber-300">Testable Prediction</p>
                <p className="text-xs text-slate-300">{h.testable_prediction}</p>
              </div>

              <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                <span className="rounded bg-white/5 px-1.5 py-0.5">
                  Dataset: {h.suggested_dataset}
                </span>
                {h.related_rules.length > 0 && (
                  <span className="rounded bg-white/5 px-1.5 py-0.5">
                    Rules: {h.related_rules.join(", ")}
                  </span>
                )}
                {h.related_yogas.length > 0 && (
                  <span className="rounded bg-white/5 px-1.5 py-0.5">
                    Yogas: {h.related_yogas.join(", ")}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Templates reference */}
      {templates.length > 0 && !hypotheses.length && (
        <details className="group">
          <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-300">
            Available hypothesis templates ({templates.length})
          </summary>
          <div className="mt-2 space-y-2">
            {templates.map((t) => (
              <div key={t.hypothesis_id} className="rounded border border-white/5 bg-white/3 p-2">
                <p className="text-xs font-medium text-slate-300">
                  {t.hypothesis_id}: {t.title}
                </p>
                <p className="text-xs text-slate-500">{t.description}</p>
                <div className="mt-1 flex gap-2 text-xs text-slate-600">
                  <span>Domain: {t.domain}</span>
                  <span>Priority: {t.priority}/10</span>
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}