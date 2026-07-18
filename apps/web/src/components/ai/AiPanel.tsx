"use client";

import { useState, useEffect } from "react";
import type {
  WorkflowAnalysisResponse,
  ExplanationResponse,
  AIResponseSchema,
} from "@/lib/types";
import { aiApi, type BirthDataInput } from "@/lib/ai";
import { ChatInterface } from "@/components/ai/ChatInterface";
import { ExplanationPanel } from "@/components/workflow/panels/ExplanationPanel";
import { ChartComparisonPanel } from "@/components/ai/ChartComparisonPanel";
import { ResearchAssistantPanel } from "@/components/ai/ResearchAssistantPanel";
import { HypothesisPanel } from "@/components/ai/HypothesisPanel";

interface Props {
  result: WorkflowAnalysisResponse;
  birthData: BirthDataInput;
  initialRuleId?: string;
}

type AiView = "explain" | "chat" | "compare" | "research" | "hypothesis";

export function AiPanel({ result, birthData, initialRuleId }: Props) {
  const [activeExplanation, setActiveExplanation] =
    useState<ExplanationResponse | null>(null);
  const [loadingRuleId, setLoadingRuleId] = useState<string | null>(null);
  const [explainError, setExplainError] = useState<string | null>(null);
  const [view, setView] = useState<AiView>("explain");

  // Auto-explain if we arrived via the "Explain" button in RulesPanel.
  useEffect(() => {
    if (initialRuleId) {
      handleExplain(initialRuleId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialRuleId]);

  const matchedRules = result.rule_results.filter((r) => r.matched);

  async function handleExplain(ruleId: string) {
    setLoadingRuleId(ruleId);
    setExplainError(null);
    try {
      const exp = await aiApi.explainRule(ruleId, birthData);
      setActiveExplanation(exp);
    } catch (err) {
      setExplainError(err instanceof Error ? err.message : "Failed to explain rule.");
    } finally {
      setLoadingRuleId(null);
    }
  }

  async function handleAsk(question: string): Promise<AIResponseSchema> {
    return aiApi.enhancedQA({
      ...birthData,
      question,
      include_yogas: true,
      include_dashas: true,
      include_transits: true,
      include_strengths: true,
    });
  }

  const tabs: { id: AiView; label: string }[] = [
    { id: "explain", label: "Rule Explainer" },
    { id: "chat", label: "Q&A Chat" },
    { id: "compare", label: "Chart Compare" },
    { id: "research", label: "Research" },
    { id: "hypothesis", label: "Hypotheses" },
  ];

  return (
    <div className="glass-card p-5 space-y-4">
      {/* View tabs */}
      <div className="flex items-center gap-1 border-b border-white/10 pb-3 overflow-x-auto">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-300/80 mr-3 shrink-0">
          AI Workspace
        </h3>
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setView(t.id)}
            className={
              view === t.id
                ? "rounded-lg bg-amber-500 px-3 py-1 text-xs font-semibold text-cosmos-950 shrink-0"
                : "rounded-lg px-3 py-1 text-xs text-slate-400 hover:bg-white/5 hover:text-slate-200 shrink-0"
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Rule Explainer view */}
      {view === "explain" && (
        <div className="space-y-4">
          {explainError && (
            <p className="text-xs text-red-400">{explainError}</p>
          )}

          {activeExplanation && (
            <ExplanationPanel
              explanation={activeExplanation}
              onClose={() => setActiveExplanation(null)}
            />
          )}

          <div>
            <p className="mb-2 text-xs text-slate-500">
              {matchedRules.length} matched rule
              {matchedRules.length !== 1 ? "s" : ""} — click to explain:
            </p>
            {matchedRules.length === 0 ? (
              <p className="text-xs text-slate-500">No rules matched for this chart.</p>
            ) : (
              <ul className="space-y-2">
                {matchedRules.map((r) => (
                  <li
                    key={r.rule_id}
                    className="flex items-center justify-between rounded-lg border border-white/5 bg-white/3 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-200">
                        {r.rule_name}
                      </p>
                      <p className="text-xs text-slate-500">{r.rule_id} · {r.rule_category}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleExplain(r.rule_id)}
                      disabled={loadingRuleId === r.rule_id}
                      className="ml-3 shrink-0 rounded-md border border-amber-500/30 bg-amber-900/20 px-2 py-1 text-xs text-amber-300 hover:bg-amber-900/40 disabled:opacity-50 transition-colors"
                    >
                      {loadingRuleId === r.rule_id ? "Loading…" : "Explain"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Q&A Chat view */}
      {view === "chat" && (
        <div className="h-96">
          <ChatInterface onAsk={handleAsk} />
        </div>
      )}

      {/* Chart Comparison view */}
      {view === "compare" && <ChartComparisonPanel />}

      {/* Research Assistant view */}
      {view === "research" && <ResearchAssistantPanel />}

      {/* Hypothesis Generator view */}
      {view === "hypothesis" && <HypothesisPanel birthData={birthData} />}
    </div>
  );
}