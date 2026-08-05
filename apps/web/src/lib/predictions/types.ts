/**
 * AstroOS — Prediction Chain Explorer: shared types
 *
 * The Prediction Chain is a computation GRAPH, not a flat list: one
 * `PredictionGraph` is the single source of truth (produced by
 * chainEngine.ts from scoring.ts's PREDICTION_FACTORS), and every UI
 * component under components/charts/predictions/ only ever renders that
 * object — no scoring math lives in a component.
 *
 * Every PredictionNode carries full provenance (source field paths, raw
 * values, formula id/version, delta, availability) so any displayed
 * number traces back to a real WorkflowAnalysisResponse field. Missing
 * inputs are represented as an explicit `unavailable` node, never
 * silently dropped or defaulted to 0.
 */

import type { WorkflowAnalysisResponse } from "@/lib/types";
import type { AvasthaListResponse } from "@/lib/avastha";
import type { AllShadbalaResponse } from "@/lib/shadbala";

export type LifeArea = "career" | "marriage" | "wealth" | "health";

/** Everything a factor's compute()/isAvailable() can read from — the real
 * per-chart data for the life area currently being explored. */
export interface ChainContext {
  area: LifeArea;
  result: WorkflowAnalysisResponse;
  /** The house number this life area is rooted in (10th for career, etc). */
  houseNumber: number;
  /** That house's ruling lord, resolved via rashiLordFromApiName — null if
   * the house/lord couldn't be resolved (e.g. missing house data). */
  lord: string | null;
  /** Best-effort extra data, fetched separately from the main workflow
   * response. Absent/undefined means "not fetched yet or failed" — factors
   * that depend on these must check availability, never assume presence. */
  avastha?: AvasthaListResponse;
  shadbalaAll?: AllShadbalaResponse;
}

export interface PredictionFactor {
  id: string;
  label: string;
  category: string;
  /** Bumped whenever this factor's weights/logic change, so a displayed
   * node can be traced to the exact formula version that produced it. */
  formulaVersion: string;
  appliesTo(area: LifeArea): boolean;
  isAvailable(ctx: ChainContext): boolean;
  compute(ctx: ChainContext): {
    delta: number;
    inputs: Record<string, unknown>;
    raw: Record<string, unknown>;
    source: string[];
    /** Human-readable computation-detail lines shown in the step detail
     * panel, e.g. "Saturn is in its own sign — Score: +6". */
    detail: string[];
  };
}

export interface PredictionNode {
  id: string;
  label: string;
  category: string;
  formulaId: string;
  formulaVersion: string;
  delta: number;
  inputs: Record<string, unknown>;
  raw: Record<string, unknown>;
  source: string[];
  detail: string[];
  /** The house/lord this node is about — a simple grouping/breadcrumb
   * reference, not a generic multi-parent graph edge (nothing in this UI
   * needs to traverse arbitrary DAG edges yet). */
  parentId: string;
  /** True when a required real input was missing (fetch failed, still
   * loading, or the field doesn't exist for this chart) — delta is
   * forced to 0 and the UI must show "Unavailable", not a fabricated
   * score. */
  unavailable: boolean;
  unavailableReason?: string;
}

export interface CategoryTotal {
  category: string;
  delta: number;
  nodeCount: number;
}

export interface ConfidenceInfo {
  level: "High" | "Medium" | "Low";
  /** Percentage of applicable factors that were actually available for
   * this chart — confidence is data completeness, never score magnitude. */
  dataCompletePercent: number;
  missing: string[];
}

export interface DataSourceEntry {
  id: string;
  label: string;
  available: boolean;
  reason?: string;
}

export interface DashaTimelineEntry {
  lord: string;
  level: number;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
}

export interface PredictionGraph {
  area: LifeArea;
  areaLabel: string;
  houseNumber: number;
  lord: string | null;
  baseline: number;
  finalScore: number;
  finalLabel: string;
  nodes: PredictionNode[];
  categories: CategoryTotal[];
  confidence: ConfidenceInfo;
  dataSources: DataSourceEntry[];
  dashaTimeline: DashaTimelineEntry[];
}
