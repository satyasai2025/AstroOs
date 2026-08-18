"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useTarabalaReport, type PlanetTara } from "@/lib/tarabala";
import { useActiveChart } from "@/lib/charts";
import { useWorkflowStore } from "@/lib/store";
import { ActiveChartSelectorModal } from "@/components/layout/ActiveChartSelectorModal";

const NAKSHATRAS = [
  "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha",
  "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha", "anuradha",
  "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishtha", "shatabhisha",
  "purva_bhadrapada", "uttara_bhadrapada", "revati",
];

const PLANET_GLYPHS: Record<string, string> = {
  sun: "Su", moon: "Mo", mars: "Ma", mercury: "Me", jupiter: "Ju",
  venus: "Ve", saturn: "Sa", rahu: "Ra", ketu: "Ke", ascendant: "Asc",
};

const TARA_MEANINGS: Record<string, { label: string; meaning: string; is_favorable: boolean; badge: string }> = {
  janma: { label: "1. Janma", meaning: "Birth, Body, Core Vitality", is_favorable: false, badge: "Neutral / Caution" },
  sampat: { label: "2. Sampat", meaning: "Wealth, Inflow, Prosperity", is_favorable: true, badge: "Highly Favorable" },
  vipat: { label: "3. Vipat", meaning: "Danger, Sudden Losses, Hazards", is_favorable: false, badge: "Unfavorable" },
  kshema: { label: "4. Kshema", meaning: "Security, Comfort, Well-being", is_favorable: true, badge: "Favorable" },
  pratyari: { label: "5. Pratyak / Pratyari", meaning: "Obstacles, Opposition, Blockages", is_favorable: false, badge: "Unfavorable" },
  sadhaka: { label: "6. Sadhaka", meaning: "Achievement, Realization, Goals", is_favorable: true, badge: "Highly Favorable" },
  naidhana: { label: "7. Naidhana / Vadha", meaning: "Destruction, Death, High Risk", is_favorable: false, badge: "Critical Risk" },
  mitra: { label: "8. Mitra", meaning: "Friendship, Assistance, Allies", is_favorable: true, badge: "Favorable" },
  paramamitra: { label: "9. Parama Mitra", meaning: "Best Friend, Ultimate Benefactor", is_favorable: true, badge: "Highly Favorable" },
};

function normalizeNakToken(val?: string | null): string {
  if (!val) return "";
  return val.toLowerCase().trim().replace(/\s+/g, "_");
}

function findCurrentDashaChain(dasha: any): string {
  if (!dasha?.mahadashas?.length) return "";
  const now = Date.now();
  const md = dasha.mahadashas.find((m: any) => {
    const s = new Date(m.start_date).getTime();
    const e = new Date(m.end_date).getTime();
    return s <= now && now <= e;
  });
  if (!md) return "";
  const ad = md.sub_periods?.find((p: any) => {
    const s = new Date(p.start_date).getTime();
    const e = new Date(p.end_date).getTime();
    return s <= now && now <= e;
  });
  const pd = ad?.sub_periods?.find((p: any) => {
    const s = new Date(p.start_date).getTime();
    const e = new Date(p.end_date).getTime();
    return s <= now && now <= e;
  });
  return [md?.lord, ad?.lord, pd?.lord].filter(Boolean).map((s: string) => s.toLowerCase()).join(",");
}

export function TarabalaPanel() {
  const { result, request, activeSummary, myCharts, selectChart, isLoading: isChartLoading } = useActiveChart();
  const { openCreateModal } = useWorkflowStore();
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [showManualOverride, setShowManualOverride] = useState(false);

  // Derive auto values from active chart
  const autoValues = useMemo(() => {
    if (!result?.chart) {
      return {
        janmaNakshatra: "ashwini",
        lagnaNakshatra: "",
        birthDate: "",
        birthTime: "00:00",
        dashaChain: "",
      };
    }
    const moon = result.chart.planets?.find((p) => p.planet.toLowerCase() === "moon");
    const asc = result.chart.ascendant;
    const jNak = normalizeNakToken(moon?.nakshatra) || "ashwini";
    const lNak = normalizeNakToken(asc?.nakshatra) || "";
    const bDt = request?.birth_datetime_utc || activeSummary?.birth_datetime_utc || "";
    let bDate = "";
    let bTime = "00:00";
    if (bDt) {
      const parts = bDt.split("T");
      bDate = parts[0] || "";
      if (parts[1]) bTime = parts[1].slice(0, 5);
    }
    const dChain = findCurrentDashaChain(result.dasha);
    return {
      janmaNakshatra: jNak,
      lagnaNakshatra: lNak,
      birthDate: bDate,
      birthTime: bTime,
      dashaChain: dChain,
    };
  }, [result, request, activeSummary]);


  // Form states (controlled by autoValues by default)
  const [janmaNakshatra, setJanmaNakshatra] = useState(autoValues.janmaNakshatra);
  const [lagnaNakshatra, setLagnaNakshatra] = useState(autoValues.lagnaNakshatra);
  const [birthDate, setBirthDate] = useState(autoValues.birthDate);
  const [birthTime, setBirthTime] = useState(autoValues.birthTime);
  const [dashaChain, setDashaChain] = useState(autoValues.dashaChain);

  // Sync state when active chart changes unless user is in manual override mode
  useEffect(() => {
    if (!showManualOverride && autoValues.birthDate) {
      setJanmaNakshatra(autoValues.janmaNakshatra);
      setLagnaNakshatra(autoValues.lagnaNakshatra);
      setBirthDate(autoValues.birthDate);
      setBirthTime(autoValues.birthTime);
      setDashaChain(autoValues.dashaChain);
    }
  }, [autoValues, showManualOverride]);

  // Auto-select default/first saved chart if none is loaded in workflow
  useEffect(() => {
    if (!result && myCharts.length > 0 && !isChartLoading) {
      const target = myCharts.find((c) => c.is_default) || myCharts[0];
      if (target) {
        selectChart(target);
      }
    }
  }, [result, myCharts, isChartLoading, selectChart]);

  const activeBirthDatetimeUtc = birthDate ? `${birthDate}T${birthTime}:00Z` : null;

  const { data, isLoading, error } = useTarabalaReport(
    activeBirthDatetimeUtc
      ? {
          janma_nakshatra: janmaNakshatra,
          birth_datetime_utc: activeBirthDatetimeUtc,
          lagna_nakshatra: lagnaNakshatra || null,
          dasha_chain: dashaChain
            ? dashaChain.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean)
            : null,
        }
      : null
  );

  const jIndex = NAKSHATRAS.indexOf(janmaNakshatra);

  // Generate 9-Tara Matrix Cards with 3 Paryayas (9 * 3 = 27 Nakshatras)
  const taraMatrix = useMemo(() => {
    if (jIndex === -1) return [];
    return Object.entries(TARA_MEANINGS).map(([key, info], offset) => {
      const p1 = NAKSHATRAS[(jIndex + offset) % 27];
      const p2 = NAKSHATRAS[(jIndex + offset + 9) % 27];
      const p3 = NAKSHATRAS[(jIndex + offset + 18) % 27];
      const nakshatras = [p1, p2, p3];

      // Find planets in these nakshatras
      const natalPlanets = data?.natal_tarabala?.filter((p) => p.position === offset) || [];
      const transitPlanets = data?.transit_tarabala?.filter((p) => p.position === offset) || [];

      return {
        key,
        position: offset + 1,
        ...info,
        nakshatras,
        natalPlanets,
        transitPlanets,
      };
    });
  }, [jIndex, data]);

  return (
    <div className="space-y-6">
      {/* ── Active Chart Selector Modal ────────────────────────────────────── */}
      <ActiveChartSelectorModal
        isOpen={selectorOpen}
        onClose={() => setSelectorOpen(false)}
      />

      {/* ── 1. Selected Profile Card ──────────────────────────────────────── */}
      <div
        className="rounded-2xl border p-5 sm:p-6 shadow-sm transition-all"
        style={{
          borderColor: "var(--border-primary)",
          background: "var(--bg-card, var(--bg-secondary))",
        }}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4" style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 text-white font-bold text-xl shadow-md">
              ⭐
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-foreground">
                  {request?.subject_name || activeSummary?.subject_name || "Guest Chart Profile"}
                </h2>
                {activeSummary?.is_default && (
                  <span className="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                    Default
                  </span>
                )}
                <span className="rounded-full bg-cyan-500/15 border border-cyan-500/30 px-2 py-0.5 text-[10px] font-bold text-cyan-400 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  Live Sync
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {activeBirthDatetimeUtc ? new Date(activeBirthDatetimeUtc).toUTCString() : "No birth time loaded"}
                {request?.place_name ? ` · ${request.place_name}` : ""}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSelectorOpen(true)}
              className="flex items-center gap-1.5 rounded-xl border px-3.5 py-2 text-xs font-semibold text-foreground hover:bg-muted transition cursor-pointer shadow-xs"
              style={{ borderColor: "var(--border-primary)" }}
            >
              <span>🔄</span>
              <span>Switch Profile</span>
            </button>
            <button
              type="button"
              onClick={() => setShowManualOverride((v) => !v)}
              className={`flex items-center gap-1.5 rounded-xl border px-3.5 py-2 text-xs font-semibold transition cursor-pointer ${
                showManualOverride
                  ? "bg-indigo-600 text-white border-indigo-600 shadow-xs"
                  : "text-muted-foreground hover:text-foreground border-border hover:bg-muted"
              }`}
            >
              <span>⚙️</span>
              <span>{showManualOverride ? "Hide Manual Form" : "Manual Override"}</span>
            </button>
          </div>
        </div>

        {/* Anchors & Dasha Summary Chips */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
          <div className="rounded-xl border p-3 bg-background/50 border-border">
            <span className="text-[10px] font-bold uppercase text-muted-foreground">🌙 Janma Nakshatra (Moon)</span>
            <p className="text-sm font-bold text-foreground mt-0.5 capitalize">{janmaNakshatra.replace("_", " ")}</p>
          </div>
          <div className="rounded-xl border p-3 bg-background/50 border-border">
            <span className="text-[10px] font-bold uppercase text-muted-foreground">☀️ Lagna Nakshatra (Asc)</span>
            <p className="text-sm font-bold text-foreground mt-0.5 capitalize">{lagnaNakshatra ? lagnaNakshatra.replace("_", " ") : "— (Optional)"}</p>
          </div>
          <div className="rounded-xl border p-3 bg-background/50 border-border">
            <span className="text-[10px] font-bold uppercase text-muted-foreground">⏳ Active Dasha Chain</span>
            <p className="text-sm font-bold text-foreground mt-0.5 capitalize">{dashaChain || "—"}</p>
          </div>
          <div className="rounded-xl border p-3 bg-background/50 border-border">
            <span className="text-[10px] font-bold uppercase text-muted-foreground">🎂 Running Yearly Tara</span>
            <p className="text-sm font-bold text-cyan-400 mt-0.5">
              {data?.yearly_name ? `Age ${data.yearly_age} → ${data.yearly_name}` : "—"}
            </p>
          </div>
        </div>
      </div>

      {/* ── Manual Override Collapsible Form ──────────────────────────────── */}
      {showManualOverride && (
        <div
          className="rounded-2xl border p-5 bg-background/40 border-dashed space-y-4 animate-in fade-in duration-200"
          style={{ borderColor: "var(--border-primary)" }}
        >
          <div className="flex items-center justify-between border-b pb-2" style={{ borderColor: "var(--border-primary)" }}>
            <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
              Manual Override / Custom Research Inputs
            </h4>
            <button
              type="button"
              onClick={() => {
                setJanmaNakshatra(autoValues.janmaNakshatra);
                setLagnaNakshatra(autoValues.lagnaNakshatra);
                setBirthDate(autoValues.birthDate);
                setBirthTime(autoValues.birthTime);
                setDashaChain(autoValues.dashaChain);
              }}
              className="text-xs text-indigo-400 hover:underline font-semibold cursor-pointer"
            >
              Reset to Active Chart Values
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <label className="text-xs text-muted-foreground">
              Janma Nakshatra
              <select
                value={janmaNakshatra}
                onChange={(e) => setJanmaNakshatra(e.target.value)}
                className="mt-1 block w-full rounded-xl border px-3 py-1.5 text-xs bg-background text-foreground"
                style={{ borderColor: "var(--border-primary)" }}
              >
                {NAKSHATRAS.map((n) => (
                  <option key={n} value={n}>{n.replace("_", " ")}</option>
                ))}
              </select>
            </label>
            <label className="text-xs text-muted-foreground">
              Lagna Nakshatra (optional)
              <select
                value={lagnaNakshatra}
                onChange={(e) => setLagnaNakshatra(e.target.value)}
                className="mt-1 block w-full rounded-xl border px-3 py-1.5 text-xs bg-background text-foreground"
                style={{ borderColor: "var(--border-primary)" }}
              >
                <option value="">— None —</option>
                {NAKSHATRAS.map((n) => (
                  <option key={n} value={n}>{n.replace("_", " ")}</option>
                ))}
              </select>
            </label>
            <label className="text-xs text-muted-foreground">
              Birth date (UTC)
              <input
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                className="mt-1 block w-full rounded-xl border px-3 py-1.5 text-xs bg-background text-foreground"
                style={{ borderColor: "var(--border-primary)" }}
              >
              </input>
            </label>
            <label className="text-xs text-muted-foreground">
              Birth time (UTC)
              <input
                type="time"
                value={birthTime}
                onChange={(e) => setBirthTime(e.target.value)}
                className="mt-1 block w-full rounded-xl border px-3 py-1.5 text-xs bg-background text-foreground"
                style={{ borderColor: "var(--border-primary)" }}
              >
              </input>
            </label>
          </div>

          <label className="block text-xs text-muted-foreground">
            Active Dasha Chain (e.g. jupiter,saturn,mercury)
            <input
              type="text"
              value={dashaChain}
              onChange={(e) => setDashaChain(e.target.value)}
              placeholder="jupiter,saturn,mercury"
              className="mt-1 block w-full rounded-xl border px-3 py-1.5 text-xs bg-background text-foreground"
              style={{ borderColor: "var(--border-primary)" }}
            />
          </label>
        </div>
      )}

      {/* ── Status Banners ────────────────────────────────────────────────── */}
      {isLoading && (
        <div className="rounded-xl border p-4 text-xs text-muted-foreground flex items-center gap-2 bg-background/50" style={{ borderColor: "var(--border-primary)" }}>
          <svg className="animate-spin h-4 w-4 text-cyan-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          <span>Computing auto-generated Navatara & Tarabala Matrix...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 p-4 text-xs text-rose-400">
          Could not compute Tarabala. Please check active chart birth date and connection.
        </div>
      )}

      {/* ── 2. Auto-Generated Navatara Matrix ─────────────────────────────── */}
      {data && (
        <div className="space-y-6">
          {/* Dual Best Stars Banner (Moon ∩ Lagna) */}
          {data.best_stars && data.best_stars.length > 0 && (
            <div className="rounded-2xl border p-4 bg-emerald-500/10 border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="text-xl">🌟</span>
                <div>
                  <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                    Best Stars Intersection (Moon ∩ Lagna)
                  </h4>
                  <p className="text-xs text-slate-700 dark:text-slate-300 mt-0.5">
                    These Nakshatras are simultaneously auspicious from both your Moon and Ascendant.
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {data.best_stars.map((star) => (
                  <span
                    key={star}
                    className="rounded-lg bg-emerald-500/20 border border-emerald-500/40 px-2.5 py-1 text-xs font-bold text-emerald-300 capitalize"
                  >
                    {star.replace("_", " ")}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Dasha Hierarchy Convergence Alert */}
          {data.total_active_levels > 0 && (
            <div className="rounded-2xl border p-4 sm:p-5 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-indigo-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">⏳</span>
                  <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
                    Dasha-Hierarchy Lordship Convergence
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-indigo-400">
                    {data.favorable_level_count} / {data.total_active_levels} Levels Favorable
                  </span>
                  {data.all_levels_favorable && (
                    <span className="rounded-full bg-emerald-500/20 border border-emerald-500/40 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                      All Favorable ✓
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {data.lordship_tarabala.map((l) => (
                  <div
                    key={l.dasha_level}
                    className={`rounded-xl p-3 border text-xs flex items-center justify-between ${
                      l.is_favorable
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                        : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-bold">
                        Level {l.dasha_level} ({PLANET_GLYPHS[l.lord] ?? l.lord})
                      </span>
                      <span className="text-[11px] text-muted-foreground capitalize">
                        → {l.position_name}
                      </span>
                    </div>
                    <span className="font-bold text-xs">
                      {l.is_favorable ? "✓ Favorable" : "✗ Unfavorable"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 9-Tara Navatara Visual Matrix Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
                Classical 9-Tara Navatara Matrix (3 Cycles)
              </h3>
              <span className="text-xs text-muted-foreground">
                Counted from Janma Nakshatra ({janmaNakshatra})
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {taraMatrix.map((tara) => {
                const hasTransit = tara.transitPlanets.length > 0;
                const hasNatal = tara.natalPlanets.length > 0;
                return (
                  <div
                    key={tara.key}
                    className={`rounded-2xl border p-4 space-y-3 transition-all ${
                      tara.is_favorable
                        ? "bg-emerald-500/5 border-emerald-500/25 hover:border-emerald-500/40"
                        : tara.key === "janma"
                        ? "bg-sky-500/5 border-sky-500/25 hover:border-sky-500/40"
                        : "bg-rose-500/5 border-rose-500/25 hover:border-rose-500/40"
                    }`}
                  >
                    {/* Tara Header */}
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-foreground">
                        {tara.label}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase border ${
                          tara.is_favorable
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                            : tara.key === "janma"
                            ? "bg-sky-500/20 text-sky-400 border-sky-500/30"
                            : "bg-rose-500/20 text-rose-400 border-rose-500/30"
                        }`}
                      >
                        {tara.badge}
                      </span>
                    </div>

                    <p className="text-[11px] text-muted-foreground font-medium">
                      {tara.meaning}
                    </p>

                    {/* 3 Cycle Stars */}
                    <div className="rounded-xl bg-background/60 border border-border/60 p-2.5 space-y-1">
                      <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-wide">
                        3 Paryaya Stars
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {tara.nakshatras.map((nak, i) => (
                          <span
                            key={nak}
                            className="rounded-md bg-muted/60 px-1.5 py-0.5 text-[10px] font-medium text-foreground capitalize"
                          >
                            {i + 1}st: {nak.replace("_", " ")}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Active Occupants */}
                    {(hasTransit || hasNatal) && (
                      <div className="space-y-1 pt-1 border-t border-border/50 text-[10px]">
                        {hasTransit && (
                          <div className="flex items-center gap-1.5 text-cyan-400 font-medium">
                            <span>🛰️ Transit:</span>
                            <span>
                              {tara.transitPlanets.map((p) => `${PLANET_GLYPHS[p.planet] ?? p.planet} (${p.nakshatra})`).join(", ")}
                            </span>
                          </div>
                        )}
                        {hasNatal && (
                          <div className="flex items-center gap-1.5 text-muted-foreground">
                            <span>🪐 Natal:</span>
                            <span>
                              {tara.natalPlanets.map((p) => `${PLANET_GLYPHS[p.planet] ?? p.planet}`).join(", ")}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Natal & Transit Side-by-Side Tables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Natal Tarabala */}
            <div className="rounded-2xl border p-4 space-y-3 bg-background/40" style={{ borderColor: "var(--border-primary)" }}>
              <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
                Natal Grahas Tarabala
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b text-[10px] uppercase tracking-wide text-muted-foreground" style={{ borderColor: "var(--border-primary)" }}>
                      <th className="py-1.5 pr-2">Graha</th>
                      <th className="py-1.5 pr-2">Birth Nakshatra</th>
                      <th className="py-1.5 pr-2">Tara</th>
                      <th className="py-1.5">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.natal_tarabala.map((p) => (
                      <tr key={p.planet} className="border-b border-border/40">
                        <td className="py-1.5 pr-2 font-bold text-foreground">
                          {PLANET_GLYPHS[p.planet] ?? p.planet}
                        </td>
                        <td className="py-1.5 pr-2 text-muted-foreground capitalize">
                          {p.nakshatra.replace("_", " ")}
                        </td>
                        <td className="py-1.5 pr-2 font-medium capitalize text-foreground">
                          {p.name}
                        </td>
                        <td className="py-1.5">
                          <span
                            className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${
                              p.is_favorable
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-rose-500/20 text-rose-400"
                            }`}
                          >
                            {p.is_favorable ? "Favorable" : "Unfavorable"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Transit Tarabala */}
            <div className="rounded-2xl border p-4 space-y-3 bg-background/40" style={{ borderColor: "var(--border-primary)" }}>
              <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
                Current Transit Grahas Tarabala
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b text-[10px] uppercase tracking-wide text-muted-foreground" style={{ borderColor: "var(--border-primary)" }}>
                      <th className="py-1.5 pr-2">Graha</th>
                      <th className="py-1.5 pr-2">Current Nakshatra</th>
                      <th className="py-1.5 pr-2">Tara</th>
                      <th className="py-1.5">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.transit_tarabala.map((p) => (
                      <tr key={p.planet} className="border-b border-border/40">
                        <td className="py-1.5 pr-2 font-bold text-foreground">
                          {PLANET_GLYPHS[p.planet] ?? p.planet}
                        </td>
                        <td className="py-1.5 pr-2 text-muted-foreground capitalize">
                          {p.nakshatra.replace("_", " ")}
                        </td>
                        <td className="py-1.5 pr-2 font-medium capitalize text-foreground">
                          {p.name}
                        </td>
                        <td className="py-1.5">
                          <span
                            className={`rounded-full px-2 py-0.5 text-[9px] font-bold uppercase ${
                              p.is_favorable
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-rose-500/20 text-rose-400"
                            }`}
                          >
                            {p.is_favorable ? "Favorable" : "Unfavorable"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Special Points (28-Scheme Abhijit-inclusive) */}
          <div className="rounded-2xl border p-4 space-y-3 bg-background/40" style={{ borderColor: "var(--border-primary)" }}>
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
                Special Points (28-Nakshatra Abhijit Scheme)
              </h4>
              <span className="text-[10px] text-muted-foreground">
                Canonical sensitive points derived from Moon & Lagna
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b text-[10px] uppercase tracking-wide text-muted-foreground" style={{ borderColor: "var(--border-primary)" }}>
                    <th className="py-1.5 pr-3">Sensitive Point Name</th>
                    <th className="py-1.5 pr-3">From Moon Anchor</th>
                    <th className="py-1.5">From Lagna Anchor</th>
                  </tr>
                </thead>
                <tbody>
                  {data.special_points.map((sp) => (
                    <tr key={sp.name} className="border-b border-border/40">
                      <td className="py-1.5 pr-3 font-bold capitalize text-foreground">{sp.name}</td>
                      <td className="py-1.5 pr-3 text-muted-foreground capitalize">{sp.from_moon.replace("_", " ")}</td>
                      <td className="py-1.5 text-muted-foreground capitalize">{sp.from_lagna ? sp.from_lagna.replace("_", " ") : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
