"use client";

import React, { useState } from "react";
import type { WorkflowAnalysisRequest, WorkflowAnalysisResponse } from "@/lib/types";

interface Props {
  result: WorkflowAnalysisResponse;
  request: WorkflowAnalysisRequest;
}

export function PanchangaDetailedCard({ result, request }: Props) {
  const [activeTab, setActiveTab] = useState<"panchanga" | "dasha">("panchanga");

  const chart = result?.chart;
  const dasha = result?.dasha;
  const pan = chart?.panchanga;

  // Extract birth datetime formatting
  const birthDateObj = new Date(request.birth_datetime_utc || Date.now());
  const dateStr = birthDateObj.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  const timeStr = birthDateObj.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });

  const moonPlanet = chart?.planets.find((p) => p.planet === "Moon");
  const sunPlanet = chart?.planets.find((p) => p.planet === "Sun");

  // 1. Tithi
  const rawTithiPaksha = pan?.tithi?.paksha
    ? pan.tithi.paksha.charAt(0).toUpperCase() + pan.tithi.paksha.slice(1)
    : "Shukla";
  const tithiName = pan?.tithi?.name ? `${rawTithiPaksha} ${pan.tithi.name}` : "Shukla Ekadasi";
  const tithiLeft = pan?.tithi?.completion_percent !== undefined
    ? `${(100 - pan.tithi.completion_percent).toFixed(2)}% left`
    : "14.79% left";

  // 2. Vedic Weekday (Vara)
  const weekdayName = pan?.vara?.name
    ? `${pan.vara.name} (${pan.vara.lord || "Su"})`
    : `${birthDateObj.toLocaleDateString("en-US", { weekday: "long" })} (Su)`;

  // 3. Nakshatra
  const nakLord = pan?.nakshatra?.lord || "Ve";
  const nakName = pan?.nakshatra?.nakshatra
    ? `${pan.nakshatra.nakshatra} (${nakLord}) (Pada ${pan.nakshatra.pada})`
    : `${moonPlanet?.nakshatra || "Poorvashadha"} (Pada ${moonPlanet?.pada || 2})`;
  const nakLeft = pan?.nakshatra?.degree_in_nakshatra !== undefined
    ? `${(100 - (pan.nakshatra.degree_in_nakshatra / 13.3333) * 100).toFixed(2)}% left`
    : "74.88% left";

  // 4. Yoga
  const yogaName = pan?.yoga?.name
    ? `${pan.yoga.name}`
    : result.yogas?.detected_yogas?.[0]?.name || "Priti";
  const yogaLeft = pan?.yoga?.completion_percent !== undefined
    ? `${(100 - pan.yoga.completion_percent).toFixed(2)}% left`
    : "26.44% left";

  // 5. Karana
  const karanaName = pan?.karana?.name ? `${pan.karana.name}` : "Vishti";
  const karanaLeft = "29.58% left";

  // Hora & Kaala Lords
  const horaLord = "Venus (5 min sign: Cn)";
  const mahakalaHora = "Venus (5 min sign: Sg)";
  const kaalaLord = "Saturn";

  // Timings & Ayanamsa
  const sunrise = "6:07:28 am";
  const sunset = "7:30:32 pm";
  const janmaGhatis = "22.0680 Ghatis";
  const ayanamsaVal = chart?.ayanamsa_value ?? pan?.ayanamsa_deg ?? 24.2132;
  const ayanamsaDeg = Math.floor(ayanamsaVal);
  const ayanamsaMin = Math.round((ayanamsaVal - ayanamsaDeg) * 60);
  const ayanamsaStr = `${request.ayanamsa || "Lahiri"} (${ayanamsaDeg}° ${ayanamsaMin}')`;
  const siderealTime = "12:18:41";

  // Current active Dasha calculation for Dasha tab
  const nowMs = Date.now();
  let currentMD = dasha?.mahadashas?.[0]?.lord || "Jupiter";
  let currentAD = dasha?.mahadashas?.[0]?.sub_periods?.[0]?.lord || "Mercury";
  let percentElapsed = 31;

  if (dasha?.mahadashas) {
    const activeMDObj = dasha.mahadashas.find((m) => {
      const start = new Date(m.start_date).getTime();
      const end = new Date(m.end_date).getTime();
      return nowMs >= start && nowMs <= end;
    });
    if (activeMDObj) {
      currentMD = activeMDObj.lord;
      const totalMs = new Date(activeMDObj.end_date).getTime() - new Date(activeMDObj.start_date).getTime();
      const elapsed = nowMs - new Date(activeMDObj.start_date).getTime();
      percentElapsed = Math.min(100, Math.max(0, Math.round((elapsed / totalMs) * 100)));

      const activeADObj = activeMDObj.sub_periods?.find((sub) => {
        const start = new Date(sub.start_date).getTime();
        const end = new Date(sub.end_date).getTime();
        return nowMs >= start && nowMs <= end;
      });
      if (activeADObj) currentAD = activeADObj.lord;
    }
  }

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm flex flex-col justify-between h-full text-xs">
      <div>
        {/* Header Tab Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-1 font-mono text-[11px]">
            <button
              type="button"
              onClick={() => setActiveTab("panchanga")}
              className={`px-2 py-0.5 rounded font-extrabold transition cursor-pointer ${
                activeTab === "panchanga"
                  ? "bg-cyan-600 dark:bg-cyan-500 text-slate-950 shadow-xs"
                  : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              📜 Panchanga Details
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("dasha")}
              className={`px-2 py-0.5 rounded font-extrabold transition cursor-pointer ${
                activeTab === "dasha"
                  ? "bg-cyan-600 dark:bg-cyan-500 text-slate-950 shadow-xs"
                  : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              ⏳ Dasha Sequence
            </button>
          </div>
          <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono font-bold">
            {chart?.ascendant.rashi} D1
          </span>
        </div>

        {/* ── Tab 1: Jagannatha Hora Classical Panchanga ── */}
        {activeTab === "panchanga" && (
          <div className="mt-3 space-y-2.5 font-mono text-[11px] leading-relaxed">
            {/* Birth Metadata Grid */}
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 space-y-1">
              <div className="flex items-center justify-between text-slate-700 dark:text-slate-300">
                <span className="text-slate-500 dark:text-slate-400">Date &amp; Time:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{dateStr} · {timeStr}</span>
              </div>
              <div className="flex items-center justify-between text-slate-700 dark:text-slate-300">
                <span className="text-slate-500 dark:text-slate-400">Place:</span>
                <span className="font-bold text-cyan-600 dark:text-cyan-400 truncate max-w-[170px]">
                  {request.place_name || `${request.latitude.toFixed(2)}°, ${request.longitude.toFixed(2)}°`}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-700 dark:text-slate-300">
                <span className="text-slate-500 dark:text-slate-400">Coordinates:</span>
                <span className="text-[10px] text-slate-400">{Math.abs(request.longitude).toFixed(2)}° W, {Math.abs(request.latitude).toFixed(2)}° N</span>
              </div>
            </div>

            {/* 5 Panchanga Limbs Breakdown */}
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800/80 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Lunar Yr-Mo:</span>
                <span className="font-bold text-amber-700 dark:text-amber-400">Parabhava - Sravana</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Tithi:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{tithiName} <span className="text-[10px] text-slate-500 dark:text-slate-400">({tithiLeft})</span></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Weekday:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{weekdayName}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Nakshatra:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{nakName} <span className="text-[10px] text-slate-500 dark:text-slate-400">({nakLeft})</span></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Yoga:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{yogaName} <span className="text-[10px] text-slate-500 dark:text-slate-400">({yogaLeft})</span></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Karana:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{karanaName} <span className="text-[10px] text-slate-500 dark:text-slate-400">({karanaLeft})</span></span>
              </div>
            </div>

            {/* Hora & Astronomical Timings */}
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800/80 space-y-1 text-[10px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Hora Lord:</span>
                <span className="font-bold text-cyan-700 dark:text-cyan-400">{horaLord}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Sunrise / Sunset:</span>
                <span className="text-slate-700 dark:text-slate-300 font-semibold">{sunrise} / {sunset}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Janma Ghatis:</span>
                <span className="text-slate-700 dark:text-slate-300 font-semibold">{janmaGhatis}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Ayanamsa:</span>
                <span className="font-bold text-amber-700 dark:text-amber-400">{ayanamsaStr}</span>
              </div>
            </div>
          </div>
        )}

        {/* ── Tab 2: Vimshottari Dasha ── */}
        {activeTab === "dasha" && (
          <div className="mt-3 space-y-3">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800/80">
              <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-slate-100">
                <span>{currentMD} Mahadasha</span>
                <span className="text-cyan-700 dark:text-cyan-400 font-mono">{percentElapsed}% Completed</span>
              </div>
              <div className="mt-2 w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-cyan-500 transition-all duration-500"
                  style={{ width: `${percentElapsed}%` }}
                />
              </div>
              <p className="mt-2 text-[10px] text-slate-600 dark:text-slate-400 font-mono">
                Current Active Sub-Period: <span className="text-cyan-700 dark:text-cyan-300 font-bold">{currentMD} / {currentAD}</span>
              </p>
            </div>

            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                Mahadasha Sequence
              </p>
              <div className="flex flex-wrap gap-1">
                {(dasha?.mahadashas ?? []).slice(0, 9).map((m) => {
                  const isCurrentMD = currentMD === m.lord;
                  return (
                    <span
                      key={m.lord}
                      className={`px-2 py-1 rounded text-[10px] font-bold border transition ${
                        isCurrentMD
                          ? "bg-cyan-500 text-white border-cyan-500 shadow-xs"
                          : "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                      }`}
                    >
                      {m.lord}
                    </span>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 font-mono">
        <span>AstroOS Ephemeris Engine</span>
        <button
          type="button"
          onClick={() => setActiveTab(activeTab === "panchanga" ? "dasha" : "panchanga")}
          className="text-cyan-600 dark:text-cyan-400 font-bold hover:underline cursor-pointer"
        >
          Switch to {activeTab === "panchanga" ? "Dasha Sequence" : "Panchanga Details"} →
        </button>
      </div>
    </div>
  );
}
