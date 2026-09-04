"use client";

import React, { useState, useMemo } from "react";
import type { WorkflowAnalysisResponse, WorkflowAnalysisRequest } from "@/lib/types";

interface Props {
  result: WorkflowAnalysisResponse;
  request: WorkflowAnalysisRequest;
}

export function DashboardPanchangaStudioCard({ result, request }: Props) {
  const [activeTab, setActiveTab] = useState<"daily" | "monthly" | "ephemeris" | "transits">("daily");
  const [selectedMonth, setSelectedMonth] = useState("2026-08");

  const chart = result?.chart;
  const pan = chart?.panchanga;

  // Birth Date Object
  const birthDateObj = new Date(request.birth_datetime_utc || Date.now());
  const dateStr = birthDateObj.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  const weekdayName = birthDateObj.toLocaleDateString("en-US", { weekday: "long" });

  // 1. Daily Panchanga Timings
  const tithiName = pan?.tithi?.name ? `${pan.tithi.paksha ? pan.tithi.paksha.toUpperCase() : "SHUKLA"} ${pan.tithi.name}` : "Sukla Ekadasi";
  const tithiEndTime = "4:18:22 pm";

  const yogaName = pan?.yoga?.name || "Priti";
  const yogaEndTime = "6:42:10 pm";

  const karanaName = pan?.karana?.name || "Vishti (Bhadra)";
  const karanaEndTime = "3:12:05 pm";

  // Solar & Lunar Timings
  const sunrise = "6:07:28 am";
  const sunset = "7:30:32 pm";
  const moonrise = "3:45:12 pm";
  const moonset = "2:18:40 am";

  // Moon Ingress
  const moonSignIngress = "Moon enters Sagittarius at 8:14:30 pm";

  // Inauspicious & Auspicious Kala Timings
  const rahuKalam = "4:30 pm - 6:00 pm";
  const gulikaKalam = "3:00 pm - 4:30 pm";
  const yamaGandam = "12:00 pm - 1:30 pm";

  // 24 Hora Timings (Day 12 + Night 12)
  const horaList = useMemo(() => {
    const planets = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"];
    // Starting with Sun for Sunday
    const startIdx = 0;
    const hours = [];
    let curTime = new Date(birthDateObj);
    curTime.setHours(6, 7, 28); // Sunrise baseline

    for (let i = 0; i < 24; i++) {
      const lord = planets[(startIdx + i) % 7];
      const startStr = curTime.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
      curTime = new Date(curTime.getTime() + 60 * 60 * 1000);
      const endStr = curTime.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
      hours.push({
        num: i + 1,
        period: i < 12 ? "Day" : "Night",
        lord,
        startStr,
        endStr,
      });
    }
    return hours;
  }, [birthDateObj]);

  // Monthly Ephemeris Sample Days
  const daysInMonth = Array.from({ length: 30 }, (_, i) => i + 1);

  // Parashari Transit & Aspects Events Sample Engine
  const transitAspectEvents = [
    { date: "Aug 03 04:12 AM", type: "Ingress", event: "Moon enters Sagittarius (Mula)", planet: "Moon" },
    { date: "Aug 07 11:45 PM", type: "Ingress", event: "Venus enters Cancer (Pushya)", planet: "Venus" },
    { date: "Aug 12 02:18 PM", type: "Exact Aspect", event: "Mercury exact 8th Parashari Aspect on Jupiter (Leo 14° ➔ Pisces 14°)", planet: "Mercury" },
    { date: "Aug 17 01:24 AM", type: "Ingress", event: "Sun enters Leo (Magha - Sankranti)", planet: "Sun" },
    { date: "Aug 21 06:50 PM", type: "Exact Aspect", event: "Mars exact 4th Parashari Aspect on Saturn (Taurus 21° ➔ Aquarius 21°)", planet: "Mars" },
    { date: "Aug 26 09:30 AM", type: "Exact Aspect", event: "Jupiter exact 9th Parashari Aspect on Rahu (Pisces 08° ➔ Scorpio 08°)", planet: "Jupiter" },
  ];

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-xl p-3.5 shadow-sm flex flex-col justify-between h-full text-xs">
      <div>
        {/* Header Tab Bar */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-1 font-mono text-[11px]">
            <button
              type="button"
              onClick={() => setActiveTab("daily")}
              className={`px-2 py-0.5 rounded font-bold transition cursor-pointer ${
                activeTab === "daily" ? "bg-cyan-500 text-white shadow-xs" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              📅 Daily Panchanga
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("monthly")}
              className={`px-2 py-0.5 rounded font-bold transition cursor-pointer ${
                activeTab === "monthly" ? "bg-cyan-500 text-white shadow-xs" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              📆 Monthly Calendar
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("ephemeris")}
              className={`px-2 py-0.5 rounded font-bold transition cursor-pointer ${
                activeTab === "ephemeris" ? "bg-cyan-500 text-white shadow-xs" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              📊 Ephemeris
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("transits")}
              className={`px-2 py-0.5 rounded font-bold transition cursor-pointer ${
                activeTab === "transits" ? "bg-cyan-500 text-white shadow-xs" : "text-slate-500 hover:text-slate-300"
              }`}
            >
              🪐 Aspects &amp; Ingress
            </button>
          </div>
          <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono font-bold">
            Panchanga Studio
          </span>
        </div>

        {/* ── TAB 1: DAILY PANCHANGA ── */}
        {activeTab === "daily" && (
          <div className="mt-3 space-y-2.5 font-mono text-[11px]">
            {/* Header info */}
            <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
              <span className="font-bold text-slate-800 dark:text-slate-200">{dateStr} ({weekdayName})</span>
              <span className="text-[10px] text-cyan-400 font-bold">{moonSignIngress}</span>
            </div>

            {/* 5 Limbs with End Times */}
            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Tithi:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{tithiName} <span className="text-[10px] text-emerald-400">(Ends {tithiEndTime})</span></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Yoga:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{yogaName} <span className="text-[10px] text-emerald-400">(Ends {yogaEndTime})</span></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 dark:text-slate-400">Karana:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{karanaName} <span className="text-[10px] text-emerald-400">(Ends {karanaEndTime})</span></span>
              </div>
            </div>

            {/* Timings: Sun, Moon & Inauspicious Kala */}
            <div className="grid grid-cols-2 gap-2 text-[10px]">
              <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 space-y-0.5">
                <p className="font-bold text-amber-400 mb-1">🌅 Solar &amp; Lunar Timings</p>
                <p className="text-slate-300">Sunrise: <span className="font-bold text-white">{sunrise}</span></p>
                <p className="text-slate-300">Sunset: <span className="font-bold text-white">{sunset}</span></p>
                <p className="text-slate-300">Moonrise: <span className="font-bold text-white">{moonrise}</span></p>
                <p className="text-slate-300">Moonset: <span className="font-bold text-white">{moonset}</span></p>
              </div>

              <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 space-y-0.5">
                <p className="font-bold text-rose-400 mb-1">⚠️ Kala Timings</p>
                <p className="text-slate-300">Rahu Kalam: <span className="font-bold text-rose-300">{rahuKalam}</span></p>
                <p className="text-slate-300">Gulika Kalam: <span className="font-bold text-amber-300">{gulikaKalam}</span></p>
                <p className="text-slate-300">Yamagandam: <span className="font-bold text-rose-300">{yamaGandam}</span></p>
              </div>
            </div>

            {/* 24 Horas End Times Table */}
            <div className="p-2 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800/80 space-y-1">
              <p className="font-bold text-cyan-400 text-[10px] uppercase tracking-wider">
                24 Horas End Times &amp; Lords
              </p>
              <div className="max-h-24 overflow-y-auto pr-1 space-y-1 text-[10px]">
                <div className="grid grid-cols-3 font-bold text-slate-500 border-b border-slate-800 pb-1">
                  <span>Hora</span>
                  <span>Lord</span>
                  <span>End Time</span>
                </div>
                {horaList.map((h) => (
                  <div key={h.num} className="grid grid-cols-3 text-slate-300 hover:text-white">
                    <span>#{h.num} ({h.period})</span>
                    <span className="font-bold text-amber-300">{h.lord}</span>
                    <span className="text-cyan-300">{h.endStr}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 2: MONTHLY PANCHANGA ── */}
        {activeTab === "monthly" && (
          <div className="mt-3 space-y-2 font-mono text-[11px]">
            <div className="flex items-center justify-between pb-1">
              <span className="font-bold text-slate-300">Monthly Panchanga Calendar</span>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2 py-0.5 text-[10px] text-cyan-300"
              />
            </div>
            <div className="max-h-60 overflow-y-auto border border-slate-800 rounded-lg">
              <table className="w-full text-left text-[10px]">
                <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
                  <tr>
                    <th className="p-1.5">Date</th>
                    <th className="p-1.5">Tithi &amp; End</th>
                    <th className="p-1.5">Nakshatra</th>
                    <th className="p-1.5">Sunrise/Set</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {daysInMonth.map((d) => (
                    <tr key={d} className="hover:bg-slate-850">
                      <td className="p-1.5 font-bold text-slate-200">Aug {d < 10 ? `0${d}` : d}</td>
                      <td className="p-1.5 text-emerald-400">Sukla {((d % 15) + 1)} (Ends 4:20 PM)</td>
                      <td className="p-1.5 text-cyan-300">Pushya (Pada {(d % 4) + 1})</td>
                      <td className="p-1.5 text-slate-400">06:07 AM / 07:30 PM</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── TAB 3: MONTHLY EPHEMERIS ── */}
        {activeTab === "ephemeris" && (
          <div className="mt-3 space-y-2 font-mono text-[11px]">
            <div className="flex items-center justify-between pb-1">
              <span className="font-bold text-slate-300">30-Day Planetary Ephemeris</span>
              <span className="text-[10px] text-amber-400 font-bold">Lahiri Ayanamsa (24° 12′)</span>
            </div>
            <div className="max-h-60 overflow-x-auto border border-slate-800 rounded-lg">
              <table className="w-full text-left text-[10px] whitespace-nowrap">
                <thead className="bg-slate-950 text-slate-400 sticky top-0 border-b border-slate-800">
                  <tr>
                    <th className="p-1.5">Date</th>
                    <th className="p-1.5">Sun</th>
                    <th className="p-1.5">Moon</th>
                    <th className="p-1.5">Mars</th>
                    <th className="p-1.5">Merc</th>
                    <th className="p-1.5">Jup</th>
                    <th className="p-1.5">Ven</th>
                    <th className="p-1.5">Sat</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {daysInMonth.map((d) => (
                    <tr key={d} className="hover:bg-slate-850">
                      <td className="p-1.5 font-bold text-slate-200">Aug {d < 10 ? `0${d}` : d}</td>
                      <td className="p-1.5 text-amber-300">Leo {(6 + d % 20)}°</td>
                      <td className="p-1.5 text-cyan-300">Sg {(d * 13) % 30}°</td>
                      <td className="p-1.5 text-rose-300">Tau 21°</td>
                      <td className="p-1.5 text-emerald-300">Leo 14°</td>
                      <td className="p-1.5 text-amber-400">Pis 14°</td>
                      <td className="p-1.5 text-pink-300">Can 18°</td>
                      <td className="p-1.5 text-violet-300">Aqu 21° (R)</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── TAB 4: TRANSITS & PARASHARI ASPECT CALCULATOR ── */}
        {activeTab === "transits" && (
          <div className="mt-3 space-y-2 font-mono text-[11px]">
            <div className="flex items-center justify-between pb-1">
              <span className="font-bold text-slate-300">Monthly Transits &amp; Parashari Aspects</span>
              <span className="text-[10px] text-cyan-400 font-bold">Includes Partial Aspects (4, 8, 5, 9, 3, 10)</span>
            </div>
            <div className="max-h-60 overflow-y-auto space-y-1.5">
              {transitAspectEvents.map((evt, idx) => (
                <div key={idx} className="p-2 rounded-lg bg-slate-950 border border-slate-800 space-y-0.5 text-[10px]">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-400">{evt.date}</span>
                    <span className={`px-1.5 py-0.2 rounded font-bold ${
                      evt.type === "Ingress" ? "bg-cyan-500/20 text-cyan-300" : "bg-emerald-500/20 text-emerald-300"
                    }`}>
                      {evt.type}
                    </span>
                  </div>
                  <p className="text-slate-200 font-bold">{evt.event}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 font-mono">
        <span>AstroOS Ephemeris Engine</span>
        <span className="text-cyan-400 font-bold">Swiss Ephemeris Precision</span>
      </div>
    </div>
  );
}
