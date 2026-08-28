"use client";

import { useEffect, useState } from "react";
import { computeDasha, getDashaSystems } from "@/lib/dasha-api";
import { DASHA_SYSTEM_OPTIONS } from "@/lib/chart-alignment";
import type {
  AyanamsaCode,
  DashaSystemCode,
  DashaSystemInfo,
  DashaTreeResponse,
  HouseSystemCode,
} from "@/lib/types";

export interface DashaBirthParams {
  birth_datetime_utc: string;
  latitude: number;
  longitude: number;
  ayanamsa: AyanamsaCode;
  house_system: HouseSystemCode;
}

export interface DashaEngineMeta {
  id: string;
  name: string;
  cycle: string;
  features: string[];
  ruleSet: string;
  color: string;
  glyph: string;
  isImplemented: boolean;
}

export const DASHA_ENGINES_METADATA: DashaEngineMeta[] = [
  {
    id: "vimshottari",
    name: "Vimshottari Engine",
    cycle: "120 year cycle",
    features: ["Mahadasha", "Antardasha", "Pratyantar", "Sookshma", "Prana"],
    ruleSet: "Vimshottari Rules",
    color: "#f59e0b",
    glyph: "☉",
    isImplemented: true,
  },
  {
    id: "shoola",
    name: "Shoola Dasha Engine",
    cycle: "8/9-segment system",
    features: ["Shoola Periods", "Sub Periods", "Transitions"],
    ruleSet: "Shoola Dasha Rules",
    color: "#f97316",
    glyph: "☸",
    isImplemented: false,
  },
  {
    id: "narayana",
    name: "Narayana Dasha Engine",
    cycle: "Balanced planetary",
    features: ["Sign/House Based", "Period Sequence", "Sub Periods"],
    ruleSet: "Narayana Dasha Rules",
    color: "#10b981",
    glyph: "✵",
    isImplemented: true,
  },
  {
    id: "lagna_kala",
    name: "Lagna Kala Dasha Engine",
    cycle: "Ascendant based",
    features: ["Lagna Based Periods", "Sub Periods", "Transitions"],
    ruleSet: "Lagna Kala Rules",
    color: "#6366f1",
    glyph: "✦",
    isImplemented: false,
  },
  {
    id: "kp_vimshottari",
    name: "KP Vimshottari Engine",
    cycle: "KP specific",
    features: ["Mahadasha", "Antardasha", "Sub Lords", "KP Significators"],
    ruleSet: "KP Rules + Sub Lords",
    color: "#a855f7",
    glyph: "KP",
    isImplemented: false,
  },
  {
    id: "chara",
    name: "Chara Dasha Engine",
    cycle: "Sign based movable",
    features: ["Chara Periods", "Sub Periods", "Transitions"],
    ruleSet: "Chara Dasha Rules",
    color: "#eab308",
    glyph: "❂",
    isImplemented: true,
  },
  {
    id: "yogini",
    name: "Yogini Dasha Engine",
    cycle: "36 year cycle",
    features: ["8 Yogini Lords", "Nakshatra Cycle", "Sub Periods"],
    ruleSet: "Yogini Rules",
    color: "#06b6d4",
    glyph: "☽",
    isImplemented: true,
  },
  {
    id: "ashtottari",
    name: "Ashtottari Engine",
    cycle: "108 year cycle",
    features: ["Rahu Kendra/Trikona", "108y Sequence", "Sub Periods"],
    ruleSet: "Ashtottari Rules",
    color: "#f43f5e",
    glyph: "☊",
    isImplemented: true,
  },
  {
    id: "kalachakra",
    name: "Kalachakra Engine",
    cycle: "100 year cycle",
    features: ["Navamsha (D9) Signs", "Savya/Apasavya", "Deha/Jeeva"],
    ruleSet: "Kalachakra Rules",
    color: "#8b5cf6",
    glyph: "⏳",
    isImplemented: true,
  },
];

export function DashaSystemSwitcher({
  current,
  birthParams,
  onChange,
  layout = "grid",
}: {
  current: string;
  birthParams?: DashaBirthParams;
  onChange: (tree: DashaTreeResponse) => void;
  layout?: "grid" | "compact";
}) {
  const [systemOptions, setSystemOptions] = useState<DashaSystemInfo[]>(
    DASHA_SYSTEM_OPTIONS.map((o) => ({ system: o.value, label: o.label, category: "nakshatra" })),
  );
  const [switching, setSwitching] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!birthParams) return;
    let cancelled = false;
    getDashaSystems()
      .then((systems) => {
        if (!cancelled && systems.length > 0) setSystemOptions(systems);
      })
      .catch(() => {
        // Fallback active
      });
    return () => {
      cancelled = true;
    };
  }, [birthParams]);

  if (!birthParams) return null;

  async function handleChange(systemId: string) {
    if (systemId === current) return;
    setSwitching(systemId);
    setError(null);
    try {
      const tree = await computeDasha(systemId as DashaSystemCode, { ...birthParams!, persist: false });
      onChange(tree);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to switch to ${systemId} dasha.`);
    } finally {
      setSwitching(null);
    }
  }

  if (layout === "compact") {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Dasha Engine:
        </label>
        <div className="flex flex-wrap gap-1.5">
          {DASHA_ENGINES_METADATA.filter((e) => e.isImplemented || systemOptions.some((s) => s.system === e.id)).map(
            (eng) => {
              const active = current === eng.id;
              const isBusy = switching === eng.id;
              return (
                <button
                  key={eng.id}
                  type="button"
                  onClick={() => handleChange(eng.id)}
                  disabled={Boolean(switching)}
                  className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                    active
                      ? "bg-amber-500/10 text-amber-300 border border-amber-500/40 shadow-xs"
                      : "bg-slate-800/80 text-slate-300 border border-slate-700 hover:bg-slate-700"
                  }`}
                >
                  <span>{eng.glyph}</span>
                  <span>{eng.name.replace(" Engine", "")}</span>
                  {isBusy && <span className="h-2 w-2 animate-spin rounded-full border border-current border-t-transparent" />}
                </button>
              );
            },
          )}
        </div>
        {error && <span className="text-xs text-rose-400">{error}</span>}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ── Section Header ─────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400">
            DASHA ENGINES
          </h3>
          <p className="text-xs text-slate-400">
            Multi-Dasha Computation Layer • Unified Abstract Interface
          </p>
        </div>
        <div className="text-xs text-slate-400">
          Active: <span className="font-semibold text-cyan-400 uppercase">{current}</span>
        </div>
      </div>

      {/* ── Engine Cards Grid ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {DASHA_ENGINES_METADATA.map((engine) => {
          const isActive = current === engine.id;
          const isBusy = switching === engine.id;
          return (
            <div
              key={engine.id}
              onClick={() => {
                if (engine.isImplemented) {
                  handleChange(engine.id);
                }
              }}
              className={`flex flex-col justify-between rounded-xl border p-4 transition-all shadow-sm ${
                isActive
                  ? "border-amber-500/50 bg-slate-900/95 ring-1 ring-amber-500/30"
                  : "border-slate-800 bg-slate-900/80 hover:border-slate-700"
              } ${engine.isImplemented ? "cursor-pointer" : "cursor-not-allowed opacity-60"}`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold bg-slate-800 border border-slate-700"
                    style={{ color: engine.color }}
                  >
                    {engine.glyph}
                  </span>
                  <div>
                    <h4 className="text-xs font-bold text-slate-100">
                      {engine.name}
                    </h4>
                    <p className="text-[11px] text-slate-400">
                      {engine.cycle}
                    </p>
                  </div>
                </div>

                {isActive ? (
                  <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-400 border border-amber-500/30">
                    Active
                  </span>
                ) : engine.isImplemented ? (
                  <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-medium text-slate-400 border border-slate-700">
                    Switch
                  </span>
                ) : (
                  <span className="rounded-full bg-slate-900 px-2 py-0.5 text-[10px] font-medium text-slate-500 border border-slate-800">
                    Plugin
                  </span>
                )}
              </div>

              {/* Feature items */}
              <ul className="my-3 space-y-1 text-xs text-slate-300">
                {engine.features.map((feat, idx) => (
                  <li key={idx} className="flex items-center gap-1.5 text-[11px]">
                    <span className="h-1 w-1 rounded-full bg-slate-500" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>

              {/* Rule Set Badge */}
              <div className="mt-auto flex items-center justify-between rounded-lg bg-slate-950/60 border border-slate-800/80 px-2.5 py-1.5 text-[10px] font-mono">
                <span className="text-slate-400">Rule Set:</span>
                <span className="font-semibold text-slate-200">{engine.ruleSet}</span>
              </div>

              {isBusy && (
                <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-slate-950/80">
                  <div className="flex items-center gap-2 text-xs font-semibold text-amber-400">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                    Calculating...
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Common Engine Abstractions ─────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-800 bg-slate-900/80 px-3.5 py-2.5 text-xs font-mono shadow-sm">
        <span className="font-semibold text-amber-400">Common Engine Abstractions:</span>
        <div className="flex flex-wrap items-center gap-2 text-slate-300 text-[11px]">
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-cyan-300">Period</span>
          <span>|</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-emerald-300">SubPeriod</span>
          <span>|</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-purple-300">PeriodHierarchy</span>
          <span>|</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-amber-300">Transition</span>
          <span>|</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-blue-300">EngineContext</span>
          <span>|</span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-rose-300">CalculationResult</span>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-950/30 p-2.5 text-xs text-rose-300">
          {error}
        </div>
      )}
    </div>
  );
}
