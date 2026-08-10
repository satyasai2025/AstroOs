"use client";

import { useState } from "react";
import type { DataSourceEntry } from "@/lib/predictions/types";

interface PredictionDataSourcesProps {
  sources: DataSourceEntry[];
}

const FLAG_LABELS: Record<string, string> = {
  is_exalted: "exalted (very strong placement)",
  is_debilitated: "debilitated (weak placement)",
  is_in_own_sign: "in its own sign",
  is_in_kendra: "in a kendra house (angular, strong)",
  is_in_trikona: "in a trikona house (trine, favorable)",
  is_in_dusthana: "in a dusthana house (difficult house)",
  is_combust: "combust (too close to the Sun)",
  is_retrograde: "retrograde",
  is_favorable_house: "transiting a favorable house",
  is_sade_sati: "under Sade Sati (Saturn's 7.5-year transit)",
  is_ashtama_shani: "under Ashtama Shani (Saturn's 8th-house transit)",
  strength_score: "strength score",
  total_rupas: "total strength (Shadbala)",
  mahadashas: "mahadasha timeline",
  value_shashtiamsas: "directional strength (Shashtiamsas)",
  deeptadi_avastha: "Deeptadi avastha (brightness state)",
  baladi_avastha: "Baladi avastha (age state)",
};

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Turns "chart.planet_strengths[Saturn].is_exalted" into "Saturn — exalted (very strong placement)". */
function humanizeField(field: string): string {
  const planetFlagMatch = field.match(/\[([A-Za-z]+)\]\.(\w+)$/);
  if (planetFlagMatch) {
    const [, planet, flag] = planetFlagMatch;
    return `${planet} — ${FLAG_LABELS[flag] ?? flag.replace(/_/g, " ")}`;
  }
  const yogaMatch = field.match(/^yogas\.results\[([\w-]+)\]$/);
  if (yogaMatch) return `Yoga rule ${yogaMatch[1]}`;
  const aspectMatch = field.match(/^chart\.aspects\[([A-Za-z]+)→([A-Za-z]+)\]$/);
  if (aspectMatch) return `${aspectMatch[1]} aspects ${aspectMatch[2]}`;
  const bracketOnlyMatch = field.match(/\[([\w-]+)\]$/);
  if (bracketOnlyMatch) return bracketOnlyMatch[1];
  const simpleMatch = field.match(/\.(\w+)$/);
  const key = simpleMatch?.[1] ?? field;
  return FLAG_LABELS[key] ?? key.replace(/_/g, " ");
}

/** Raw API-shaped labels (e.g. "chart.planet_strengths[Saturn].is_exalted", "yogas.results[BPHS-RY-001]")
 *  get humanized for display; hand-written labels (e.g. "House & Sign Strength") pass through untouched. */
function isRawFieldPath(label: string): boolean {
  return /^[a-z][a-z_/]*[.[]/.test(label);
}

function displayLabel(source: DataSourceEntry): string {
  return isRawFieldPath(source.label) ? capitalize(humanizeField(source.label)) : source.label;
}

function ExpandableSourceDetail({ source }: { source: DataSourceEntry }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showTechnical, setShowTechnical] = useState(false);

  return (
    <li key={source.id} className="glass-card flex flex-col gap-2 p-4 text-xs">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-left text-sm font-semibold"
        style={{ color: "var(--text-primary)" }}
      >
        <div className="flex items-center gap-2">
          <span style={{ color: source.available ? "#34d399" : "var(--text-muted)" }}>
            {source.available ? "✓" : "⚠"}
          </span>
          <span>{displayLabel(source)}</span>
        </div>
        <span style={{ color: "var(--text-muted)" }}>
          {isExpanded ? "View Less <" : "View Details >"}
        </span>
      </button>
      {isExpanded && (
        <div className="mt-2 space-y-2 text-base" style={{ color: "var(--text-secondary)" }}>
          <div>
            <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Status: </span>
            {source.status}
          </div>
          {source.reason && (
            <div>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Reason: </span>
              {source.reason}
            </div>
          )}
          {source.fieldsConsumed && source.fieldsConsumed.length > 0 && (
            <div>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>What was checked: </span>
              <ul className="mt-1 list-inside list-disc">
                {source.fieldsConsumed.map((field) => (
                  <li key={field}>{capitalize(humanizeField(field))}</li>
                ))}
              </ul>
            </div>
          )}
          {source.usedBy && source.usedBy.length > 0 && (
            <div>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Used By: </span>
              <ul className="mt-1 list-inside list-disc">
                {source.usedBy.map((feature) => (
                  <li key={feature}>{feature}</li>
                ))}
              </ul>
            </div>
          )}
          {source.lastUpdated && (
            <div>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Last Updated: </span>
              {source.lastUpdated}
            </div>
          )}
          {source.impactIfUnavailable && !source.available && (
            <div>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Impact: </span>
              {source.impactIfUnavailable}
            </div>
          )}
        </div>
      )}
    </li>
  );
}

/**
 * PredictionDataSources — render-only checklist, one row per applicable
 * factor in the graph (chainEngine.ts's dataSourcesFromNodes). Missing
 * data is shown explicitly with its reason, never silently dropped.
 */
export function PredictionDataSources({ sources }: PredictionDataSourcesProps) {
  const dataQuality = sources.filter((s) => s.available).length / sources.length;
  const sourcesUsed = sources.filter((s) => s.available).length;
  const unavailableSources = sources.filter((s) => !s.available).length;

  return (
    <div className="flex flex-col gap-5">
      <div className="glass-card p-5">
        <h3 className="mb-4 text-xl font-bold" style={{ color: "var(--text-primary)" }}>
          Prediction Data Sources
        </h3>
        <div className="grid grid-cols-3 gap-4 text-center text-sm">
          <div>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>Data Quality</p>
            <p className="text-xl font-bold" style={{ color: "var(--accent)" }}>{(dataQuality * 100).toFixed(0)}%</p>
          </div>
          <div>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>Sources Used</p>
            <p className="text-xl font-bold" style={{ color: "var(--accent)" }}>{sourcesUsed}</p>
          </div>
          <div>
            <p className="font-semibold" style={{ color: "var(--text-primary)" }}>Unavailable</p>
            <p className="text-xl font-bold" style={{ color: "var(--text-muted)" }}>{unavailableSources}</p>
          </div>
        </div>
      </div>
      <ul className="flex flex-col gap-3">
        {sources.map((s) => (
          <ExpandableSourceDetail key={s.id} source={s} />
        ))}
      </ul>
    </div>
  );
}
