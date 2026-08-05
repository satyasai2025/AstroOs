"use client";

import { AppShell } from "@/components/layout/AppShell";
import { TransitWheel } from "@/components/charts/transit/TransitWheel";
import { TransitAlerts } from "@/components/charts/transit/TransitAlerts";
import { useWorkflowStore } from "@/lib/store";
import { useLiveTransit } from "@/lib/transitPatterns";
import type { AyanamsaCode, HouseSystemCode, TransitRequest, BirthChartSummary } from "@/lib/types";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

function toIsoDate(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const TABS = [
  { key: "overview", label: "Overview", icon: "✦" },
  { key: "positions", label: "Planetary Positions", icon: "🪐" },
  { key: "comparison", label: "Natal Transit", icon: "⚡" },
  { key: "houses", label: "House Activation", icon: "🏠" },
  { key: "aspects", label: "Aspects", icon: "🔗" },
  { key: "dasha", label: "Dasha Transit", icon: "☸" },
  { key: "predictions", label: "Predictions", icon: "👁" },
  { key: "remedies", label: "Remedies", icon: "✨" },
];

export default function TransitReportPage() {
  const params = useParams();
  const reportId = params.reportId as string;
  const router = useRouter();

  const result = useWorkflowStore((s) => s.result);
  const request = useWorkflowStore((s) => s.request);
  const transitChart = useWorkflowStore((s) => s.transitChart);
  const setTransitChart = useWorkflowStore((s) => s.setTransitChart);
  const openCreateModal = useWorkflowStore((s) => s.openCreateModal);

  const [transitDate, setTransitDate] = useState("2026-08-12");
  const [transitTime, setTransitTime] = useState("10:30");
  const [transitLocation, setTransitLocation] = useState("Pune, Maharashtra, India");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [showAspects, setShowAspects] = useState(true);
  const [activeStep, setActiveStep] = useState(2);

  const [availableCharts] = useState<BirthChartSummary[]>([
    { id: "raj-sharma", subject_name: "Raj Sharma", birth_datetime_utc: "1990-08-15T05:00:00.000Z", birth_latitude: 18.5204, birth_longitude: 73.8567, place_name: "Pune, Maharashtra, India", ayanamsa: "lahiri", house_system: "W", lagna_rashi: "Taurus", moon_nakshatra: "Rohini", created_at: "2026-01-01T00:00:00.000Z", is_default: true },
    { id: "priya-mehta", subject_name: "Priya Mehta", birth_datetime_utc: "1992-11-22T02:15:00.000Z", birth_latitude: 19.076, birth_longitude: 72.8777, place_name: "Mumbai, Maharashtra, India", ayanamsa: "lahiri", house_system: "W", lagna_rashi: "Cancer", moon_nakshatra: "Pushya", created_at: "2026-02-01T00:00:00.000Z", is_default: false },
    { id: "amit-shah", subject_name: "Amit Shah", birth_datetime_utc: "1988-03-03T00:45:00.000Z", birth_latitude: 28.6139, birth_longitude: 77.209, place_name: "Delhi, India", ayanamsa: "lahiri", house_system: "W", lagna_rashi: "Virgo", moon_nakshatra: "Hasta", created_at: "2026-03-01T00:00:00.000Z", is_default: false },
  ]);

  const activeSelectedChart = useMemo(() => {
    if (transitChart) return transitChart;
    if (request) return { id: "active-request", subject_name: request.subject_name || "Raj Sharma", birth_datetime_utc: request.birth_datetime_utc || "1990-08-15T05:00:00.000Z", birth_latitude: request.latitude || 18.5204, birth_longitude: request.longitude || 73.8567, place_name: "Pune, Maharashtra, India", ayanamsa: request.ayanamsa || "lahiri", house_system: request.house_system || "W", lagna_rashi: "Taurus", moon_nakshatra: "Rohini", created_at: new Date().toISOString(), is_default: true } as BirthChartSummary;
    return availableCharts[0];
  }, [transitChart, request, availableCharts]);

  const transitDatetimeUtc = useMemo(() => {
    if (!transitDate || !transitTime) return undefined;
    return new Date(`${transitDate}T${transitTime}`).toISOString();
  }, [transitDate, transitTime]);

  const transitRequest: TransitRequest | null = useMemo(() => {
    if (!transitDatetimeUtc || !activeSelectedChart) return null;
    return {
      birth_datetime_utc: activeSelectedChart.birth_datetime_utc,
      latitude: activeSelectedChart.birth_latitude,
      longitude: activeSelectedChart.birth_longitude,
      ayanamsa: (activeSelectedChart.ayanamsa || "lahiri") as AyanamsaCode,
      house_system: (activeSelectedChart.house_system || "W") as HouseSystemCode,
      transit_datetime_utc: transitDatetimeUtc,
    };
  }, [transitDatetimeUtc, activeSelectedChart]);

  const liveTransit = useLiveTransit(transitRequest!);
  const transits = liveTransit.data;

  useEffect(() => {
    if (reportId && reportId !== "current") {
      const decoded = decodeURIComponent(reportId);
      if (decoded.includes("T")) {
        const [date, time] = decoded.split("T");
        setTransitDate(date);
        if (time) setTransitTime(time.substring(0, 5));
      }
      return;
    }
  }, [reportId]);

  useEffect(() => {
    if (transitRequest) {
      liveTransit.refetch();
    }
  }, [transitRequest, liveTransit]);

  const handleSetQuickDate = (mode: "today" | "tomorrow" | "thisWeek" | "custom") => {
    const d = new Date();
    if (mode === "today") {
      setTransitDate(toIsoDate(d));
    } else if (mode === "tomorrow") {
      d.setDate(d.getDate() + 1);
      setTransitDate(toIsoDate(d));
    } else if (mode === "thisWeek") {
      d.setDate(d.getDate() + 7);
      setTransitDate(toIsoDate(d));
    }
  };

  const birthFormatted = new Date(activeSelectedChart.birth_datetime_utc).toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric", });
  const planets = (transits?.planets || []);

  return (
    <AppShell>
      <div className="mx-auto max-w-[1400px] text-zinc-100 font-sans pb-16">
        {/* Top Header Bar */}
        <div className="flex items-center justify-between mb-6 pt-2">
          <div className="flex items-center gap-4">
            <button onClick={() => router.push("/charts")} type="button" className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-950 to-slate-900 border border-indigo-500/20 text-indigo-400 hover:bg-slate-800 transition-colors shadow-lg">
              <span className="text-xl leading-none">←</span>
            </button>
            <div>
              <h1 className="text-xl font-bold tracking-wide text-white flex items-center gap-2">Create Transit Chart</h1>
              <p className="text-xs text-zinc-400 font-medium">Analyze planetary transits existing birth chart.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#0A0D18] border border-slate-800 hover:border-indigo-500 text-xs font-semibold text-indigo-300 transition-colors shadow-md">
              <span className="text-indigo-400 text-sm">▶</span> How works?
            </button>
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            <div className="rounded-2xl p-5 bg-[#0A0D18] border border-slate-800/80 shadow-xl">
              <div className="flex items-center justify-between relative">
                <div className="absolute top-[18px] left-[20%] right-[20%] h-[1px] bg-slate-800 -z-0" />
                <div onClick={() => setActiveStep(1)} className="flex flex-col items-center gap-1.5 relative z-10 cursor-pointer text-center">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-xs transition-all ${activeStep === 1 ? "bg-purple-600 border border-purple-400 text-white shadow-lg shadow-purple-600/40" : "bg-[#150F2A] text-purple-400 border border-purple-600/40"}`}>1</div>
                  <span className="text-xs font-bold text-zinc-200">Select Chart</span>
                </div>
                <div onClick={() => setActiveStep(2)} className="flex flex-col items-center gap-1.5 relative z-10 cursor-pointer text-center">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-xs transition-all ${activeStep === 2 ? "bg-purple-600 border border-purple-400 text-white shadow-lg shadow-purple-600/40" : "bg-[#131B2E] text-slate-300 border border-slate-700"}`}>2</div>
                  <span className="text-xs font-bold text-zinc-200">Transit Date</span>
                </div>
                <div onClick={() => setActiveStep(3)} className="flex flex-col items-center gap-1.5 relative z-10 cursor-pointer text-center">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-xs transition-all ${activeStep === 3 ? "bg-purple-600 border border-purple-400 text-white" : "bg-[#131B2E] text-slate-300 border border-slate-700"}`}>3</div>
                  <span className="text-xs font-bold text-zinc-200">Review</span>
                </div>
              </div>
            </div>

            {/* Select Birth Chart Card */}
            <div className="rounded-2xl p-5 bg-[#0A0D18] border border-slate-800/80 shadow-xl flex flex-col gap-4 flex-1">
              <div>
                <h2 className="text-sm font-bold text-white tracking-wide">Select Birth Chart</h2>
              </div>
              <div className="relative">
                <input type="text" placeholder="Search name..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full pl-4 pr-10 py-2.5 rounded-xl bg-[#090C15] border border-slate-800 focus:border-purple-500 focus:outline-none text-xs text-zinc-200 placeholder-zinc-400 shadow-inner" />
              </div>
              {activeSelectedChart && (
                <div className="p-3.5 rounded-xl bg-[#121026]/90 border border-purple-500 shadow-lg relative overflow-hidden flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-[#26184E]/90 flex items-center justify-center font-bold text-sm text-purple-200 shadow-md flex items-center justify-center">
                      {activeSelectedChart.subject_name.split(" ").map((w) => w[0]).join("").substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white tracking-tight">{activeSelectedChart.subject_name}</h3>
                      <p className="text-xs text-zinc-300 mt-0.5">{birthFormated}</p>
                  </div>
                </div>
              </div>
              )}
              <div className="flex flex-col gap-3">
                {availableCharts.filter((c) => c.id !== activeSelectedChart?.id && c.subject_name.toLowerCase().includes(searchQuery.toLowerCase())).map((chart, idx) => (
                <div key={chart.id} onClick={() => setTransitChart(chart)} className="p-3.5 rounded-xl bg-[#0C101E]/80 hover:bg-[#11172A] border border-slate-800/90 cursor-pointer transition-all flex items-center gap-3 shadow">
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-sm border ${idx === 0 ? "bg-[#2B1B26] text-rose-300 border-rose-500/30" : "bg-[#152B24] text-emerald-300 border-emerald-500/30"}`}>
                    {chart.subject_name.split(" ").map((w) => w[0]).join("").substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                      <h4 className="text-xs font-bold text-zinc-200">{chart.subject_name}</h4>
                      <p className="text-[11px] text-zinc-400">{new Date(chart.birth_datetime_utc).toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric" })}</p>
                    </div>
                  </div>
                ))}
              </div>
              <button type="button" onClick={openCreateModal} className="mt-auto py-3.5 rounded-xl border border-dashed border-purple-500/60 hover:border-purple-400 bg-purple-950/10 hover:bg-purple-950/30 text-xs font-bold text-purple-300 flex items-center justify-center gap-2 transition-all shadow-md">
                <span className="text-sm font-extrabold">+</span> Create New Birth Chart
              </button>
            </div>
          </div>

          {/* Right Main Area */}
          <div className="lg:col-span-8 flex flex-col gap-6">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
              <div className="md:col-span-5 rounded-2xl p-5 bg-[#0A0D18] border border-slate-800 flex flex-col gap-5 shadow-xl">
                <div>
                  <h3 className="text-sm font-bold text-white mb-3">Transit Date Time</h3>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <input type="date" value={transitDate} onChange={(e) => setTransitDate(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-[#090C15] border border-slate-800 focus:border-purple-500 text-xs text-zinc-100 font-mono" />
                    <input type="time" value={transitTime} onChange={(e) => setTransitTime(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-[#090C15] border border-slate-800 focus:border-purple-500 text-xs text-zinc-100 font-mono" />
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {(["today", "tomorrow", "thisWeek", "custom"] as const).map((btn) => (
                      <button key={btn} type="button" onClick={() => handleSetQuickDate(btn)} className={`py-1.5 px-2 rounded-lg font-bold text-[11px] capitalize transition-all ${btn === "today" ? "bg-purple-600 border border-purple-500 text-white" : "bg-[#0F1424] text-zinc-400"}`}>
                        {btn}
                      </button>
                    ))}
                  </div>
                </div>
                <button type="button" onClick={() => liveTransit.refetch()} disabled={liveTransit.isFetching} className="w-full py-3.5 rounded-xl bg-purple-600 hover:bg-purple-500 font-extrabold text-xs text-white uppercase shadow-lg shadow-indigo-600/40 flex items-center justify-center gap-2 transition-all">
                  {liveTransit.isFetching ? "Calculating..." : "Analyze Transit →"}
                </button>
              </div>

              {/* Transit Wheel */}
              <div className="md:col-span-7 rounded-2xl p-5 bg-[#0A0D18] border border-slate-800 flex flex-col items-center justify-center shadow-xl">
                {transits ? (
                  <div className="transform scale-[0.8]">
                    <TransitWheel transits={transits} houseReference="ascendant" />
                  </div>
                ) : (
                  <div className="text-zinc-500 text-xs text-center">No transit data to display.</div>
                )}
                <div className="flex items-center gap-2.5 mt-4 pt-2 border-t border-slate-800/60">
                  <span className="text-xs font-semibold text-zinc-300">Show Aspects</span>
                  <button type="button" onClick={() => setShowAspects(!showAspects)} className={`w-10 h-5 rounded-full flex items-center p-0.5 transition-colors ${showAspects ? "bg-purple-600 justify-end" : "bg-slate-800 justify-start"}`}>
                    <div className="w-4 h-4 rounded-full bg-white shadow" />
                  </button>
                </div>
              </div>
            </div>

            {/* Bottom Section: Tabs */}
            <div className="rounded-2xl p-6 bg-[#0B0F1E] border border-slate-800/90 shadow-2xl flex flex-col gap-6">
              <div className="flex items-center gap-6 border-b border-slate-800/80 pb-3.5 overflow-x-auto text-xs font-medium">
                {TABS.map((tab) => (
                  <button key={tab.key} type="button" onClick={() => setActiveTab(tab.key)} className={`pb-2 transition-all whitespace-nowrap flex items-center gap-2 border-b-2 font-bold text-xs ${activeTab === tab.key ? "border-purple-500 text-purple-300" : "border-transparent text-zinc-400 font-semibold"}`}>
                    <span>{tab.icon}</span> {tab.label}
                  </button>
                ))}
              </div>

              <div className="min-h-[140px] pt-1">
                {activeTab === "aspects" && (
                  <div className="flex flex-col gap-4">
                    {transits ? <TransitAlerts transits={transits} /> : <div className="text-zinc-500 text-xs">Waiting for transit calculation...</div>}
                  </div>
                )}
                {/* Fallback output for other tabs */}
                {activeTab !== "aspects" && <div className="text-zinc-500 text-xs text-center">Tab {activeTab} content here.</div>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}