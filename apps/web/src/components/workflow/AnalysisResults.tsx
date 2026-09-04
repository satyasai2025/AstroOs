"use client";

import { useState } from "react";
import type { WorkflowAnalysisResponse, WorkflowAnalysisRequest } from "@/lib/types";
import { ChartPanel } from "./panels/ChartPanel";
import { VargaPanel } from "./panels/VargaPanel";
import { DashaPanel } from "./panels/DashaPanel";
import { YogaPanel } from "./panels/YogaPanel";
import { StrengthPanel } from "./panels/StrengthPanel";
import { TransitPanel } from "./panels/TransitPanel";
import { RulesPanel } from "./panels/RulesPanel";
import { KnowledgePanel } from "./panels/KnowledgePanel";
import { VerificationPanel } from "./panels/VerificationPanel";
import { ReportPanel } from "./panels/ReportPanel";
import { AiPanel } from "@/components/ai/AiPanel";

const TABS = [
  "Chart",
  "Vargas",
  "Dasha",
  "Yogas",
  "Strength",
  "Transits",
  "Rules",
  "Knowledge",
  "Verification",
  "Report",
  "AI",
] as const;

type Tab = (typeof TABS)[number];

export function AnalysisResults({
  result,
  request,
  onReset,
}: {
  result: WorkflowAnalysisResponse;
  request: WorkflowAnalysisRequest;
  onReset: () => void;
}) {
  const [tab, setTab] = useState<Tab>("Chart");
  const [explainRuleId, setExplainRuleId] = useState<string | null>(null);

  // Birth data needed by AI endpoints.
  const birthData = {
    birth_datetime_utc: request.birth_datetime_utc,
    latitude: request.latitude,
    longitude: request.longitude,
    ayanamsa: request.ayanamsa,
    house_system: request.house_system,
  };

  function handleExplainRule(ruleId: string) {
    setExplainRuleId(ruleId);
    setTab("AI");
  }

  return (
    <div className="animate-fade-in space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          Analysis complete for{" "}
          <span className="font-semibold text-slate-200">{request.subject_name}</span>
          {" "}
          <span className="font-mono text-[10px] text-slate-500">({result.chart_id})</span>
        </p>
        <button type="button" onClick={onReset} className="btn-ghost text-xs px-3 py-1.5">
          New Analysis
        </button>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-white/10 pb-2">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={
              t === tab
                ? "rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-semibold text-cosmos-950"
                : "rounded-lg px-3 py-1.5 text-xs text-slate-400 hover:bg-white/5 hover:text-slate-200"
            }
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Chart" && <ChartPanel chart={result.chart} />}
      {tab === "Vargas" && <VargaPanel vargas={result.vargas} />}
      {tab === "Dasha" && <DashaPanel dasha={result.dasha} birthParams={birthData} />}
      {tab === "Yogas" && <YogaPanel yogas={result.yogas} />}
      {tab === "Strength" && (
        <StrengthPanel shadbala={result.shadbala} ashtakavarga={result.ashtakavarga} />
      )}
      {tab === "Transits" && <TransitPanel transits={result.transits} />}
      {tab === "Rules" && (
        <RulesPanel
          ruleResults={result.rule_results}
          onExplain={handleExplainRule}
        />
      )}
      {tab === "Knowledge" && <KnowledgePanel citations={result.knowledge_citations} />}
      {tab === "Verification" && (
        <VerificationPanel verification={result.verification} />
      )}
      {tab === "Report" && (
        <ReportPanel report={result.report} benchmark={result.benchmark} />
      )}
      {tab === "AI" && (
        <AiPanel
          result={result}
          birthData={birthData}
          initialRuleId={explainRuleId ?? undefined}
        />
      )}
    </div>
  );
}
