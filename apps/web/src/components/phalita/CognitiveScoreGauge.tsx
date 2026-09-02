'use client';

import React from "react";
import { useTheme } from "@/components/layout/ThemeProvider";

interface CognitiveScoreGaugeProps {
  score: number; // 0 to 9 Cognitive Score
  isProbable: boolean;
  domain?: string;
  size?: "sm" | "md" | "lg";
}

export const CognitiveScoreGauge: React.FC<CognitiveScoreGaugeProps> = ({
  score,
  isProbable,
  domain = "General",
  size = "md",
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const clampedScore = Math.max(0, Math.min(9, score));
  const percentage = (clampedScore / 9) * 100;

  // Determine color theme based on score (0 to 9)
  const getScoreColor = () => {
    if (clampedScore >= 6.5) return { stroke: "#10b981", text: "text-emerald-500", label: "Strong Auspicious" };
    if (clampedScore >= 5.0) return { stroke: "#06b6d4", text: "text-cyan-500", label: "Probable Support" };
    if (clampedScore >= 3.5) return { stroke: "#f59e0b", text: "text-amber-500", label: "Moderate Friction" };
    return { stroke: "#ef4444", text: "text-rose-500", label: "Obstruction / Delay" };
  };

  const { stroke, text, label } = getScoreColor();

  return (
    <div className={`p-4 rounded-xl border flex flex-col items-center justify-center ${
      isDark ? "bg-[#0c1421] border-[#1e2e42]" : "bg-white border-slate-200"
    }`}>
      <div className="relative flex items-center justify-center">
        {/* SVG Radial Gauge */}
        <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="40"
            className={isDark ? "text-slate-800" : "text-slate-100"}
            strokeWidth="8"
            stroke="currentColor"
            fill="transparent"
          />
          <circle
            cx="50"
            cy="50"
            r="40"
            stroke={stroke}
            strokeWidth="8"
            strokeDasharray={2 * Math.PI * 40}
            strokeDashoffset={2 * Math.PI * 40 * (1 - percentage / 100)}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        <div className="absolute flex flex-col items-center">
          <span className={`text-3xl font-black ${text}`}>
            {clampedScore.toFixed(1)}
          </span>
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 dark:text-slate-400">
            0 to 9 Score
          </span>
        </div>
      </div>

      <div className="mt-3 text-center">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
          isProbable
            ? isDark
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : "bg-emerald-100 text-emerald-800 border border-emerald-300"
            : isDark
              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              : "bg-amber-100 text-amber-800 border border-amber-300"
        }`}>
          {isProbable ? "✓ Event Probable" : "⏳ Pending Catalyst"}
        </span>
        <p className="mt-1 text-xs text-slate-700 dark:text-slate-300 font-medium">
          {domain.toUpperCase()} — {label}
        </p>
      </div>
    </div>
  );
};
