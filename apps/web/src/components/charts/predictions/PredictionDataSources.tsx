"use client";

import { useState } from "react";
import type { DataSourceEntry } from "@/lib/predictions/types";

interface PredictionDataSourcesProps {
  sources: DataSourceEntry[];
}

function ExpandableSourceDetail({ source }: { source: DataSourceEntry }) {
  const [isExpanded, setIsExpanded] = useState(false);

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
          <span>{source.label}</span>
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
          {source.sourceLocation && (
            <div>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Source: </span>
              {source.sourceLocation}
            </div>
          )}
          {source.fieldsConsumed && source.fieldsConsumed.length > 0 && (
            <div>
              <span className="font-semibold" style={{ color: "var(--text-primary)" }}>Fields Used: </span>
              <ul className="mt-1 list-inside list-disc">
                {source.fieldsConsumed.map((field) => (
                  <li key={field}>{field}</li>
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
