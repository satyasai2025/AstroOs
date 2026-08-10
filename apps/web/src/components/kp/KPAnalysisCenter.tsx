"use client";

/**
 * KP Analysis Center — the main /charts?view=kp workspace. Sub-tabs map
 * to the mockup's KP Portfolio: Overview, Cusps, Planets, Significators,
 * Ruling Planets, Events, Timing, Special Factors, Evidence.
 */

import { useState } from "react";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import { KPHeader } from "@/components/kp/KPHeader";
import { KPOverview } from "@/components/kp/KPOverview";
import { KPCuspMatrix } from "@/components/kp/KPCuspMatrix";
import { KPPlanetPortfolio } from "@/components/kp/KPPlanetPortfolio";
import { KPSignificatorMatrix } from "@/components/kp/KPSignificatorMatrix";
import { KPRulingPlanets } from "@/components/kp/KPRulingPlanets";
import { KPEventExplorer } from "@/components/kp/KPEventExplorer";
import { KPTimingEngine } from "@/components/kp/KPTimingEngine";
import { KPSpecialFactors } from "@/components/kp/KPSpecialFactors";
import { KPReasoningChain } from "@/components/kp/KPReasoningChain";
import { KPSnapshot } from "@/components/kp/KPSnapshot";

interface Props {
  result: WorkflowAnalysisResponse;
}

type KPSection =
  | "snapshot"
  | "overview"
  | "cusps"
  | "planets"
  | "significators"
  | "ruling"
  | "events"
  | "timing"
  | "factors"
  | "evidence";

const SECTIONS: { key: KPSection; label: string }[] = [
  { key: "snapshot", label: "Snapshot" },
  { key: "overview", label: "Overview" },
  { key: "cusps", label: "Cusp Matrix" },
  { key: "planets", label: "Planet Portfolio" },
  { key: "significators", label: "Significators" },
  { key: "ruling", label: "Ruling Planets" },
  { key: "events", label: "Event Explorer" },
  { key: "timing", label: "Timing Engine" },
  { key: "factors", label: "Special Factors" },
  { key: "evidence", label: "Evidence / Reasoning" },
];

export function KPAnalysisCenter({ result }: Props) {
  const [section, setSection] = useState<KPSection>("snapshot");
  const { chart, dasha } = result;

  return (
    <div className="w-full space-y-5">
      <KPHeader />

      <div className="flex flex-wrap gap-1 border-b pb-2" style={{ borderColor: "var(--border-primary)" }} role="tablist" aria-label="KP Analysis sections">
        {SECTIONS.map((s) => (
          <button
            key={s.key}
            type="button"
            role="tab"
            aria-selected={section === s.key}
            aria-controls={`kp-panel-${s.key}`}
            onClick={() => setSection(s.key)}
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition"
            style={{
              backgroundColor: section === s.key ? "var(--accent)" : "transparent",
              color: section === s.key ? "var(--accent-text)" : "var(--text-secondary)",
            }}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div id={`kp-panel-${section}`} role="tabpanel" className="space-y-4">
        {section === "snapshot" && <KPSnapshot chart={chart} dasha={dasha} />}
        {section === "overview" && <KPOverview />}
        {section === "cusps" && <KPCuspMatrix chart={chart} />}
        {section === "planets" && <KPPlanetPortfolio chart={chart} />}
        {section === "significators" && <KPSignificatorMatrix chart={chart} />}
        {section === "ruling" && <KPRulingPlanets chart={chart} />}
        {section === "events" && <KPEventExplorer chart={chart} />}
        {section === "timing" && <KPTimingEngine chart={chart} dasha={dasha} />}
        {section === "factors" && <KPSpecialFactors chart={chart} />}
        {section === "evidence" && <KPReasoningChain chart={chart} dasha={dasha} />}
      </div>
    </div>
  );
}
