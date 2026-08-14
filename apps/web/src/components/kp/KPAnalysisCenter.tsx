"use client";

/**
 * KP Analysis Center — the main /charts?view=kp workspace. Sub-tabs map
 * to the mockup's KP Portfolio: Overview, Cusps, Planets, Significators,
 * Ruling Planets, Events, Timing, Special Factors, Evidence.
 *
 * Every panel now consumes the backend KP Analysis + Evidence engine
 * (POST /api/v1/kp/analyze): the center builds the request from the
 * chart's own birth data and renders the pre-computed slices.
 */

import { useMemo, useState } from "react";
import type {
  KPAnalysisRequest,
  WorkflowAnalysisRequest,
  WorkflowAnalysisResponse,
} from "@/lib/types";
import { useKPAnalysis } from "@/lib/workflow";
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
  /** The workflow-sourced birth data — the KP endpoint reuses its core fields. */
  request: WorkflowAnalysisRequest | null;
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

export function KPAnalysisCenter({ request, result }: Props) {
  const [section, setSection] = useState<KPSection>("snapshot");

  // The KP endpoint is stateless and mirrors the workflow request's core
  // fields; we reuse them as-is and pin the transit moment to the one the
  // workflow already computed, so the timing layer matches the chart page.
  const kpRequest = useMemo<KPAnalysisRequest | null>(() => {
    if (!request) return null;
    return {
      birth_datetime_utc: request.birth_datetime_utc,
      latitude: request.latitude,
      longitude: request.longitude,
      ayanamsa: request.ayanamsa,
      house_system: request.house_system,
      transit_datetime_utc: result.transits?.transit_datetime_utc ?? null,
    };
  }, [request, result]);

  const kp = useKPAnalysis(kpRequest);

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

      {kp.isPending ? (
        <div className="glass-card p-6 text-center" role="status">
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Computing KP analysis…</p>
        </div>
      ) : kp.isError ? (
        <div className="glass-card p-6 text-center" role="alert">
          <p className="text-sm font-medium" style={{ color: "#f87171" }}>Could not load the KP analysis.</p>
          <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>{kp.error?.message ?? "Please try again."}</p>
        </div>
      ) : kp.data ? (
        <div id={`kp-panel-${section}`} role="tabpanel" className="space-y-4">
          {section === "snapshot" && (
            <KPSnapshot
              cusps={kp.data.cusps}
              profiles={kp.data.planet_profiles}
              rulingPlanets={kp.data.ruling_planets}
              eventPromises={kp.data.event_promises}
              timing={kp.data.timing}
            />
          )}
          {section === "overview" && <KPOverview />}
          {section === "cusps" && <KPCuspMatrix cusps={kp.data.cusps} />}
          {section === "planets" && <KPPlanetPortfolio profiles={kp.data.planet_profiles} />}
          {section === "significators" && <KPSignificatorMatrix houses={kp.data.house_significators} />}
          {section === "ruling" && (
            <KPRulingPlanets rulingPlanets={kp.data.ruling_planets} houseSignificators={kp.data.house_significators} />
          )}
          {section === "events" && <KPEventExplorer eventPromises={kp.data.event_promises} />}
          {section === "timing" && <KPTimingEngine timing={kp.data.timing} />}
          {section === "factors" && <KPSpecialFactors factors={kp.data.special_factors} />}
          {section === "evidence" && <KPReasoningChain evidence={kp.data.evidence} />}
        </div>
      ) : null}
    </div>
  );
}
