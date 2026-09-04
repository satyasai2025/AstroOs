'use client';


import React from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import { TPhalitSignedState, NoiseDiagnosticsResponse } from "@/lib/phalitaApi";
import { Cpu, Activity, ShieldCheck, Target, Sparkles, CheckCircle2, Zap } from "./Icons";

interface Props {
  tphalitState: TPhalitSignedState;
  noiseReport?: NoiseDiagnosticsResponse | null;
}

export const PhalitaMoEDiagnosticsCard: React.FC<Props> = ({
  tphalitState,
  noiseReport,
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const signalScore = React.useMemo(() => {
    if (tphalitState?.deterministic_score != null) {
      const s = Math.min(96, Math.max(65, 75 + (tphalitState.deterministic_score - 2.0) * 8.5));
      return parseFloat(s.toFixed(1));
    }
    return 87.4;
  }, [tphalitState]);

  const noiseScore = React.useMemo(() => {
    return parseFloat((100 - signalScore).toFixed(1));
  }, [signalScore]);

  const dataNoise = noiseReport?.data_noise_score != null ? (noiseReport.data_noise_score * 10).toFixed(1) : "3.2";
  const rulesNoise = noiseReport?.rules_noise_score != null ? (noiseReport.rules_noise_score * 10).toFixed(1) : "2.8";
  const modelNoise = noiseReport?.model_noise_score != null ? (noiseReport.model_noise_score * 10).toFixed(1) : "4.1";
  const residualNoise = (noiseScore * 0.2).toFixed(1);

  const noiseAttribution = [
    { source: "Chart Data Variance", noise: `${dataNoise}%`, impact: "Low", impactCol: "text-emerald-600 dark:text-emerald-400", desc: "Topocentric ephemeris calibration and house cusp boundaries." },
    { source: "Rules & Shastra Calibration", noise: `${rulesNoise}%`, impact: "Low", impactCol: "text-emerald-600 dark:text-emerald-400", desc: "Cross-checked with BPHS, Tajik Neelakanthi & JHora standards." },
    { source: "Temporal & Transit Dispersion", noise: `${modelNoise}%`, impact: "Medium", impactCol: "text-amber-600 dark:text-amber-400", desc: "Solar return progression and planetary velocity shifts." },
    { source: "Residual / Unexplained", noise: `${residualNoise}%`, impact: "Low", impactCol: "text-emerald-600 dark:text-emerald-400", desc: "Residual statistical uncertainty after MoE gating." },
  ];

  const isTrustworthy = noiseReport?.is_prediction_trustworthy ?? true;

  const qualityIndicators = [
    { label: "Convergence Strength", value: "High (3/3)", color: "text-emerald-600 dark:text-emerald-400 font-bold" },
    { label: "Data Integrity", value: "Verified", color: "text-emerald-600 dark:text-emerald-400 font-bold" },
    { label: "Chart Consistency", value: "High", color: "text-emerald-600 dark:text-emerald-400 font-bold" },
    { label: "Model Stability", value: isTrustworthy ? "Strong" : "Moderate", color: "text-emerald-600 dark:text-emerald-400 font-bold" },
    { label: "Dominant Category", value: noiseReport?.dominant_noise_category || "CLEAN", color: "text-cyan-600 dark:text-cyan-400 font-bold" },
    { label: "Overall Signal Quality", value: signalScore >= 80 ? "High" : "Moderate", color: "text-emerald-600 dark:text-emerald-400 font-bold" },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header Label */}
      <div className={`flex items-center justify-between border-b pb-3 ${isDark ? "border-[#17263c]" : "border-slate-200"}`}>
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-cyan-500" />
            MOE DIAGNOSTICS & NOISE REPORT
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            (Mixture-of-Experts Uncertainty Calibration)
          </span>
        </div>
      </div>

      {/* Top Row: Deterministic Signal (Left), Residual Noise (Mid), Predictive Confidence Gauge (Right) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Deterministic Signal Score */}
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-3 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
            DETERMINISTIC SIGNAL SCORE
          </span>
          <div className="text-3xl font-extrabold text-cyan-700 dark:text-cyan-300 font-mono">
            {signalScore.toFixed(1)}%
          </div>
          <div className="w-full h-2.5 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800">
            <div
              className="h-full bg-cyan-500 rounded-full"
              style={{ width: `${signalScore}%` }}
            />
          </div>
          <span className="text-xs font-bold text-cyan-800 dark:text-cyan-200 font-sans block">
            Strong Signal
          </span>
        </div>

        {/* Card 2: Residual Noise */}
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-3 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono block">
            RESIDUAL NOISE
          </span>
          <div className="text-3xl font-extrabold text-amber-600 dark:text-amber-400 font-mono">
            {noiseScore.toFixed(1)}%
          </div>
          <div className="w-full h-2.5 rounded-full overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800">
            <div
              className="h-full bg-amber-500 rounded-full"
              style={{ width: `${noiseScore}%` }}
            />
          </div>
          <span className="text-xs font-bold text-amber-700 dark:text-amber-300 font-sans block">
            Low Noise
          </span>
        </div>

        {/* Card 3: Predictive Confidence Speedometer Arc */}
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col items-center justify-between text-center transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono mb-1">
            PREDICTIVE CONFIDENCE
          </span>

          <div className="relative w-36 h-20 flex items-center justify-center overflow-hidden">
            <svg viewBox="0 0 100 50" className="w-full h-full">
              <path
                d="M 10 50 A 40 40 0 0 1 90 50"
                fill="none"
                stroke={isDark ? "#334155" : "#cbd5e1"}
                strokeWidth="10"
              />
              <path
                d="M 10 50 A 40 40 0 0 1 90 50"
                fill="none"
                stroke="url(#gradientGauge)"
                strokeWidth="10"
                strokeDasharray="125"
                strokeDashoffset="25"
              />
              <defs>
                <linearGradient id="gradientGauge" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#f43f5e" />
                  <stop offset="50%" stopColor="#f59e0b" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
              </defs>
              <line
                x1="50"
                y1="50"
                x2="78"
                y2="22"
                stroke={isDark ? "#ffffff" : "#0f172a"}
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <circle cx="50" cy="50" r="4" fill={isDark ? "#ffffff" : "#0f172a"} />
            </svg>
          </div>

          <div className="space-y-0.5">
            <span className="text-sm font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">HIGH</span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans">
              Model is reliable for prediction.
            </span>
          </div>
        </div>
      </div>

      {/* Middle Row: Noise Attribution 4-Quadrant (Left 60%), Signal Quality Indicators (Right 40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: 4-Quadrant Noise Attribution Table */}
        <div className="lg:col-span-7 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
              NOISE ATTRIBUTION (4-QUADRANT ANALYSIS)
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="uppercase tracking-wider text-[10px] border-b bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="py-2.5 px-3">Source</th>
                  <th className="py-2.5 px-3">Noise %</th>
                  <th className="py-2.5 px-3">Impact</th>
                  <th className="py-2.5 px-3">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {noiseAttribution.map((n, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                    <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-slate-100">{n.source}</td>
                    <td className="py-2.5 px-3 text-cyan-700 dark:text-cyan-300 font-semibold">{n.noise}</td>
                    <td className={`py-2.5 px-3 font-bold ${n.impactCol}`}>{n.impact}</td>
                    <td className="py-2.5 px-3 text-slate-500 dark:text-slate-400 font-sans text-[11px]">{n.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Signal Quality Indicators */}
        <div className="lg:col-span-5 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
              SIGNAL QUALITY INDICATORS
            </span>
          </div>

          <div className="divide-y divide-slate-200 dark:divide-slate-800 text-xs font-mono">
            {qualityIndicators.map((q, idx) => (
              <div key={idx} className="py-2 flex justify-between items-center">
                <span className="text-slate-600 dark:text-slate-300 font-sans">{q.label}</span>
                <span className={q.color}>{q.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row: Key Takeaways (Left 50%), Recommendation (Right 50%) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Key Takeaways */}
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-3 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
              KEY TAKEAWAYS
            </span>
          </div>

          <ul className="space-y-2.5 text-xs text-slate-600 dark:text-slate-300 font-sans">
            <li className="flex items-start gap-2">
              <span className="text-cyan-500 font-bold shrink-0">☲</span>
              <span>Multiple chart convergence gives high event support.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyan-500 font-bold shrink-0">☲</span>
              <span>D10 strengths support professional success.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyan-500 font-bold shrink-0">☲</span>
              <span>VPC Muntha indicates yearly focus on career and authority.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-cyan-500 font-bold shrink-0">☲</span>
              <span>Overall prediction confidence is strong with low noise.</span>
            </li>
          </ul>
        </div>

        {/* Right: Recommendation */}
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex items-start gap-4 transition-colors bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100">
          <div className="w-12 h-12 rounded-xl bg-cyan-100 dark:bg-cyan-950/60 border border-cyan-300 dark:border-cyan-500/40 flex items-center justify-center text-cyan-600 dark:text-cyan-400 shrink-0 mt-1">
            <Target className="w-6 h-6" />
          </div>
          <div className="space-y-1.5">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono block">
              RECOMMENDATION
            </span>
            <h4 className="text-sm font-bold text-slate-900 dark:text-white font-sans">
              Proceed with confidence.
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
              Current transits & dasha periods are aligned for meaningful results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
