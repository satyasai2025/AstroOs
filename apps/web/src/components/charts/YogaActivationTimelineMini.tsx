"use client";

/**
 * YogaActivationTimelineMini — a compact horizontal timeline showing when
 * a yoga activates across Dasha periods (Mahadasha/Antardasha).
 *
 * Data comes from POST /api/v1/yoga/evaluate/timeline — the YogaTimeline
 * dataclass that correlates yoga involved planets with Dasha lordship.
 */

import { useMemo } from "react";
import type { YogaActivationResponse } from "@/lib/types";

interface YogaActivationTimelineMiniProps {
  activations: YogaActivationResponse[];
  currentActivation: YogaActivationResponse | null;
  dashaSystem?: string;
  maxHeight?: number;
}

const LEVEL_LABELS: Record<number, string> = {
  1: "MD",
  2: "AD",
  3: "PD",
  4: "SD",
  5: "Prana",
};

const LEVEL_COLORS: Record<number, string> = {
  1: "#fbbf24", // amber
  2: "#a78bfa", // purple
  3: "#34d399", // green
  4: "#f87171", // red
  5: "#38bdf8", // blue
};

const LEVEL_BG: Record<number, string> = {
  1: "rgba(251, 191, 36, 0.12)",
  2: "rgba(167, 139, 250, 0.10)",
  3: "rgba(52, 211, 153, 0.08)",
  4: "rgba(248, 113, 113, 0.08)",
  5: "rgba(56, 189, 248, 0.08)",
};

function formatYear(dateStr: string): string {
  try {
    return new Date(dateStr).getFullYear().toString();
  } catch {
    return dateStr.slice(0, 4);
  }
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", { year: "numeric", month: "short" });
  } catch {
    return dateStr;
  }
}

export function YogaActivationTimelineMini({
  activations,
  currentActivation,
  dashaSystem = "Vimshottari",
  maxHeight = 140,
}: YogaActivationTimelineMiniProps) {
  // Compute the full date range across all activations
  const dateRange = useMemo(() => {
    if (activations.length === 0) return null;
    const dates = activations.flatMap((a) => [new Date(a.start_date), new Date(a.end_date)]);
    return {
      start: new Date(Math.min(...dates.map((d) => d.getTime()))),
      end: new Date(Math.max(...dates.map((d) => d.getTime()))),
    };
  }, [activations]);

  if (activations.length === 0) {
    return (
      <div
        className="text-center py-4"
        style={{ color: "var(--text-muted)" }}
        aria-label="No activation periods found for this yoga"
      >
        <p className="text-xs">No Dasha periods activate this yoga's involved planets.</p>
      </div>
    );
  }

  if (!dateRange) {
    return null;
  }

  const totalSpanMs = dateRange.end.getTime() - dateRange.start.getTime();
  const padding = 30;

  return (
    <div className="space-y-2" role="img" aria-label={`Activation timeline for ${activations.length} periods across ${dashaSystem} dasha`}>
      {/* Header */}
      <div className="flex items-center justify-between text-xs">
        <span style={{ color: "var(--text-secondary)" }}>
          {dashaSystem} Dasha Activation
        </span>
        <span style={{ color: "var(--text-secondary)" }}>
          {activations.length} activation{activations.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-[10px]" style={{ color: "var(--text-secondary)" }}>
        {Object.entries(LEVEL_LABELS).slice(0, 3).map(([level, label]) => (
          <span key={level} className="flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-sm"
              style={{ backgroundColor: LEVEL_COLORS[Number(level)] }}
            />
            {label} = {label === "MD" ? "Mahadasha" : label === "AD" ? "Antardasha" : "Pratyantar"}
          </span>
        ))}
        {currentActivation && (
          <span className="flex items-center gap-1 font-medium" style={{ color: "var(--status-success)" }}>
            <span className="inline-block h-2 w-2 rounded-sm animate-pulse" style={{ backgroundColor: "var(--status-success)" }} />
            Now Active
          </span>
        )}
      </div>

      {/* Timeline */}
      <div
        className="relative"
        style={{ height: maxHeight }}
        role="img"
        aria-label="Dasha activation timeline"
      >
        <svg
          width="100%"
          height={maxHeight}
          viewBox={`0 0 ${800} ${maxHeight}`}
          preserveAspectRatio="none"
          className="w-full"
          style={{ overflow: "visible" }}
        >
          {activations.map((act, i) => {
            const xStart = ((new Date(act.start_date).getTime() - dateRange!.start.getTime()) / totalSpanMs) * (800 - padding * 2) + padding;
            const xEnd = ((new Date(act.end_date).getTime() - dateRange!.start.getTime()) / totalSpanMs) * (800 - padding * 2) + padding;
            const barWidth = Math.max(2, xEnd - xStart);
            const yBase = 20 + (act.period_level - 1) * 22;
            const barHeight = 16;
            const color = LEVEL_COLORS[act.period_level] ?? "#6b7280";
            const bgColor = LEVEL_COLORS[act.period_level] ? LEVEL_BG[act.period_level] : "rgba(107, 115, 128, 0.10)";
            const isCurrent = !!currentActivation && act.start_date === currentActivation.start_date && act.end_date === currentActivation.end_date;

            return (
              <g key={`${act.yoga_id}-${act.period_name}-${i}`}>
                {/* Background band */}
                <rect
                  x={xStart}
                  y={yBase}
                  width={barWidth}
                  height={barHeight}
                  rx={3}
                  fill={bgColor}
                  stroke={color}
                  strokeWidth={isCurrent ? 2 : 1}
                  style={{ opacity: isCurrent ? 1 : 0.7 }}
                />
                {/* Planet label */}
                <text
                  x={xStart + 2}
                  y={yBase + barHeight / 2 + 1}
                  fontSize={9}
                  fill={color}
                  fontWeight={isCurrent ? "bold" : "normal"}
                >
                  {act.planet ? act.planet.slice(0, 1).toUpperCase() : "?"}
                </text>
                {/* Period name label (if space permits) */}
                {barWidth > 50 && (
                  <text
                    x={xStart + barWidth / 2}
                    y={yBase + barHeight + 10}
                    fontSize={7}
                    fill="var(--text-muted)"
                    textAnchor="middle"
                  >
                    {LEVEL_LABELS[act.period_level] ?? act.period_level}
                  </text>
                )}
                {/* Date label at the end */}
                {barWidth > 40 && (
                  <text
                    x={xEnd - 2}
                    y={yBase + barHeight / 2 + 1}
                    fontSize={7}
                    fill="var(--text-secondary)"
                    textAnchor="end"
                  >
                    {formatYear(act.end_date)}
                  </text>
                )}
                {/* "NOW" indicator line */}
                {isCurrent && (
                  <line
                    x1={xStart - 2}
                    y1={yBase + barHeight + 14}
                    x2={xEnd + 2}
                    y2={yBase + barHeight + 14}
                    stroke="var(--status-success)"
                    strokeWidth={1.5}
                    strokeDasharray="3,2"
                  />
                )}
              </g>
            );
          })}

          {/* Year axis */}
          {Array.from({ length: Math.min(8, 6) }).map((_, i) => {
            const yearDate = new Date(dateRange!.start.getTime() + (totalSpanMs * i) / (7));
            const x = (i / 7) * (800 - padding * 2) + padding;
            return (
              <g key={i}>
                <line x1={x} y1={maxHeight - 8} x2={x} y2={maxHeight - 2} stroke="var(--border-primary)" strokeWidth={0.5} />
                <text x={x} y={maxHeight - 1} fontSize={7} fill="var(--text-muted)" textAnchor="middle">
                  {yearDate.getFullYear()}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Current activation highlight */}
        {currentActivation && (
          <div
            className="mt-2 rounded-lg border p-2 text-xs"
            style={{
              borderColor: "var(--status-success)",
              backgroundColor: "var(--status-success-bg)",
            }}
          >
            <span style={{ color: "var(--status-success)", fontWeight: "bold" }}>▶ Currently Active</span>
            {" — "}
            {currentActivation.period_name} ({formatDate(currentActivation.start_date)} — {formatDate(currentActivation.end_date)})
          </div>
        )}
      </div>

      {/* Activation list (compact) */}
      <div className="space-y-1">
        {activations.slice(0, 5).map((act, i) => (
          <div
            key={`${act.yoga_id}-${act.period_name}-${i}-list`}
            className="flex items-center justify-between text-[10px] rounded px-2 py-1"
            style={{
              backgroundColor: act.is_current
                ? "var(--status-success-bg)"
                : "var(--bg-secondary)",
              border: `1px solid ${act.is_current ? "var(--status-success)" : "var(--border-primary)"}`,
            }}
          >
            <span style={{ color: LEVEL_COLORS[act.period_level] ?? "var(--text-secondary)" }}>
              {LEVEL_LABELS[act.period_level] ?? `L${act.period_level}`}
            </span>
            <span style={{ color: "var(--text-secondary)" }}>{act.planet}</span>
            <span style={{ color: "var(--text-muted)" }}>{formatDate(act.start_date)} — {formatDate(act.end_date)}</span>
            {act.is_current && (
              <span style={{ color: "var(--status-success)", fontWeight: "bold" }}>● NOW</span>
            )}
          </div>
        ))}
        {activations.length > 5 && (
          <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            +{activations.length - 5} more activations
          </p>
        )}
      </div>
    </div>
  );
}
