"use client";

import type { ConfidenceInfo } from "@/lib/predictions/types";

interface PredictionScorePanelProps {
  finalLabel: string;
  finalScore: number;
  confidence: ConfidenceInfo;
}

const CONFIDENCE_COLOR: Record<ConfidenceInfo["level"], string> = {
  High: "#34d399",
  Medium: "#fbbf24",
  Low: "#f87171",
};

function scoreColor(score: number): string {
  if (score >= 66) return "#34d399";
  if (score >= 40) return "#fbbf24";
  return "#f87171";
}

/**
 * PredictionScorePanel — render-only. finalScore/confidence both come
 * straight off the PredictionGraph; confidence reflects data completeness
 * (chainEngine.ts), never the score's own magnitude.
 */
export function PredictionScorePanel({ finalLabel, finalScore, confidence }: PredictionScorePanelProps) {
  const color = scoreColor(finalScore);
  const size = 120;
  const thickness = 12;
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  const filled = (finalScore / 100) * c;

  return (
    <div className="glass-card flex flex-col items-center gap-3 p-5">
      <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
        {finalLabel}
      </span>

      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
            <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border-primary)" strokeWidth={thickness} />
            <circle
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={color}
              strokeWidth={thickness}
              strokeDasharray={`${filled} ${c - filled}`}
              strokeLinecap="round"
            />
          </g>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>
            {finalScore}
          </span>
          <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            / 100
          </span>
        </div>
      </div>

      <span
        className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
        style={{ color: CONFIDENCE_COLOR[confidence.level], border: `1px solid ${CONFIDENCE_COLOR[confidence.level]}` }}
      >
        Confidence: {confidence.level}
      </span>
      <span className="text-center text-[10px]" style={{ color: "var(--text-muted)" }}>
        {confidence.dataCompletePercent}% of expected data was available for this chart
      </span>
    </div>
  );
}
