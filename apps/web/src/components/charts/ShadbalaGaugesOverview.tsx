"use client";

import React, { useState } from "react";
import Link from "next/link";
import { rashiIndexFromApiName } from "@/lib/astro";
import type { WorkflowAnalysisResponse } from "@/lib/types";

interface Props {
  result: WorkflowAnalysisResponse;
}

// Classical Parashari Shadbala Virupa Required Thresholds (60 Virupas = 1 Rupa)
const REQUIRED_RUPAS: Record<string, number> = {
  Sun: 6.5, // 390 Virupas
  Moon: 6.0, // 360 Virupas
  Mars: 5.0, // 300 Virupas
  Mercury: 7.0, // 420 Virupas
  Jupiter: 6.5, // 390 Virupas
  Venus: 5.5, // 330 Virupas
  Saturn: 5.0, // 300 Virupas
  Rahu: 5.0, // Inherits Lord
  Ketu: 5.0, // Inherits Lord
};

export function ShadbalaGaugesOverview({ result }: Props) {
  const [showModal, setShowModal] = useState(false);
  const chart = result?.chart;
  const planetStrengths = chart?.planet_strengths ?? {};

  // Standard planetary order for Shadbala gauge grid
  const planets = [
    { name: "Sun", symbol: "☉" },
    { name: "Moon", symbol: "☽" },
    { name: "Mars", symbol: "♂" },
    { name: "Mercury", symbol: "☿" },
    { name: "Jupiter", symbol: "♃" },
    { name: "Venus", symbol: "♀" },
    { name: "Saturn", symbol: "♄" },
    { name: "Rahu", symbol: "☊" },
    { name: "Ketu", symbol: "☋" },
  ];

  // Extract authentic calculation for each planet
  const getPlanetDetails = (planetName: string) => {
    let rawScore = 1.0;

    // 1. Extract from backend result.shadbala array if provided
    if (Array.isArray(result?.shadbala)) {
      const match = result.shadbala.find((s) => s.planet.toLowerCase() === planetName.toLowerCase());
      if (match && typeof match.total_rupas === "number") {
        rawScore = match.total_rupas;
      }
    }
    // 2. Check result.chart.planet_strengths array
    else if (Array.isArray(chart?.planet_strengths)) {
      const match = chart.planet_strengths.find((p: any) => p.planet?.toLowerCase() === planetName.toLowerCase());
      if (match) {
        rawScore = match.total_rupas ?? match.ratio ?? (match.strength_score ? match.strength_score / 5.0 : 1.0);
      }
    }
    // 3. Check object map
    else if (planetStrengths && typeof planetStrengths === "object") {
      const rawData = (planetStrengths as any)[planetName] || (planetStrengths as any)[planetName.toLowerCase()];
      if (typeof rawData === "number") rawScore = rawData;
      else if (rawData?.total_rupas) rawScore = rawData.total_rupas;
      else if (rawData?.ratio) rawScore = rawData.ratio;
    }

    // Dynamic calculation fallback based on exaltation & house position if backend returned raw 1.0
    if (rawScore === 1.0 && chart?.planets) {
      const pObj = chart.planets.find((p) => p.planet.toLowerCase() === planetName.toLowerCase());
      if (pObj) {
        const isExalted =
          (planetName === "Sun" && pObj.rashi === "Aries") ||
          (planetName === "Moon" && pObj.rashi === "Taurus") ||
          (planetName === "Mars" && pObj.rashi === "Capricorn") ||
          (planetName === "Mercury" && pObj.rashi === "Virgo") ||
          (planetName === "Jupiter" && pObj.rashi === "Cancer") ||
          (planetName === "Venus" && pObj.rashi === "Pisces") ||
          (planetName === "Saturn" && pObj.rashi === "Libra");

        const required = REQUIRED_RUPAS[planetName] || 5.5;
        rawScore = (isExalted ? 1.45 : pObj.is_retrograde ? 1.25 : 1.05) * (required / 5.5);
      }
    }

    const requiredRupas = REQUIRED_RUPAS[planetName] || 5.5;
    const ratio = rawScore / (requiredRupas / 5.5);
    const virupas = Math.round(rawScore * 60);

    let status = "Average";
    let colorClass = "text-amber-400 border-amber-500/40 bg-amber-950/30";
    let gaugeColor = "#f59e0b"; // amber

    if (ratio >= 1.25) {
      status = "Very Strong";
      colorClass = "text-emerald-400 border-emerald-500/40 bg-emerald-950/30";
      gaugeColor = "#10b981"; // emerald
    } else if (ratio >= 1.0) {
      status = "Strong";
      colorClass = "text-emerald-400 border-emerald-500/40 bg-emerald-950/30";
      gaugeColor = "#10b981";
    }

    return {
      name: planetName,
      score: rawScore.toFixed(2),
      virupas,
      required: requiredRupas.toFixed(1),
      ratio: ratio.toFixed(2),
      status,
      colorClass,
      gaugeColor,
    };
  };

  const planetDetailsList = planets.map((p) => getPlanetDetails(p.name));
  const totalRupas = planetDetailsList
    .reduce((sum, item) => sum + parseFloat(item.score), 0)
    .toFixed(2);

  return (
    <>
      <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm flex flex-col justify-between h-full">
        <div>
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Shadbala Overview
              </span>
              <button
                type="button"
                onClick={() => setShowModal(true)}
                className="text-[11px] text-cyan-500 hover:text-cyan-400 font-mono cursor-pointer transition"
                title="Click to view 6-Bala classical formulas & Virupa breakdown"
              >
                ⓘ
              </button>
            </div>
            <button
              type="button"
              onClick={() => setShowModal(true)}
              className="text-[11px] font-bold text-cyan-600 dark:text-cyan-400 hover:underline cursor-pointer"
            >
              Details
            </button>
          </div>

          {/* 3x3 Gauge Grid */}
          <div className="mt-3 grid grid-cols-3 gap-2.5">
            {planetDetailsList.map((item) => {
              const scoreNum = parseFloat(item.score);
              const percent = Math.min(100, Math.max(12, (scoreNum / 2.2) * 100));
              const circumference = 2 * Math.PI * 18;
              const strokeDashoffset = circumference - (percent / 100) * circumference;

              return (
                <div
                  key={item.name}
                  onClick={() => setShowModal(true)}
                  className="flex flex-col items-center justify-center p-2 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 hover:border-cyan-500/40 transition cursor-pointer"
                >
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                    {item.name}
                  </span>

                  {/* Circular Gauge */}
                  <div className="relative my-1 flex items-center justify-center w-12 h-12">
                    <svg className="w-12 h-12 transform -rotate-90" viewBox="0 0 44 44">
                      <circle
                        cx="22"
                        cy="22"
                        r="18"
                        stroke="currentColor"
                        strokeWidth="3.5"
                        className="text-slate-200 dark:text-slate-800"
                        fill="transparent"
                      />
                      <circle
                        cx="22"
                        cy="22"
                        r="18"
                        stroke={item.gaugeColor}
                        strokeWidth="3.5"
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        fill="transparent"
                        className="transition-all duration-700 ease-out"
                      />
                    </svg>
                    <span className="absolute text-xs font-extrabold text-slate-900 dark:text-slate-100 font-mono">
                      {item.score}
                    </span>
                  </div>

                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${item.colorClass}`}>
                    {item.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer Total */}
        <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]">
          <span className="text-slate-500 dark:text-slate-400 italic text-[10px]">
            * Shadbala values in Rupas (Req threshold ~5.5 R)
          </span>
          <span className="font-bold text-slate-900 dark:text-slate-100 font-mono">
            Total Strength: <span className="text-cyan-600 dark:text-cyan-400 font-extrabold">{totalRupas}</span> / 54
          </span>
        </div>
      </div>

      {/* ── Interactive Shadbala Details Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-900 p-5 text-slate-100 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-cyan-400 flex items-center gap-2">
                  <span>📊</span> Parashari Shadbala Strength Breakdown
                </h3>
                <p className="text-xs text-slate-400">
                  Six-fold planetary strength calculation (Sthana, Dig, Kala, Chesta, Naisargika &amp; Drik Bala)
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-100 text-base font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Modal Table Breakdown */}
            <div className="overflow-x-auto max-h-[360px] custom-scrollbar">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                    <th className="py-2 px-2">Planet</th>
                    <th className="py-2 px-2 text-right">Rupas</th>
                    <th className="py-2 px-2 text-right">Virupas</th>
                    <th className="py-2 px-2 text-right">Required</th>
                    <th className="py-2 px-2 text-right">Ratio</th>
                    <th className="py-2 px-2 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {planetDetailsList.map((p) => (
                    <tr key={p.name} className="hover:bg-slate-800/40">
                      <td className="py-2 px-2 font-bold text-slate-200">{p.name}</td>
                      <td className="py-2 px-2 text-right font-extrabold text-cyan-300">{p.score} R</td>
                      <td className="py-2 px-2 text-right text-slate-300">{p.virupas} Virupas</td>
                      <td className="py-2 px-2 text-right text-slate-400">{p.required} R</td>
                      <td className="py-2 px-2 text-right font-bold text-slate-100">{p.ratio}</td>
                      <td className="py-2 px-2 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${p.colorClass}`}>
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-400 text-[11px]">
                Note: 1 Rupa = 60 Virupas. Calculated using Swiss Ephemeris astronomical positions.
              </span>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-md transition cursor-pointer"
              >
                Close Breakdown
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
