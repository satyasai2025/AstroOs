"use client";

import { Card } from "@/components/ui";
import type { TransitPatternsResponse, TransitResponse } from "@/lib/types";

interface Alert {
  key: string;
  title: string;
  description: string;
  range?: string;
  tone: "danger" | "warn";
}

function formatRange(start: string | null, end: string | null): string | undefined {
  if (!start || !end) return undefined;
  return `${start} – ${end}`;
}

function phaseLabel(phase: string | null): string {
  switch (phase) {
    case "first_year":
      return "Phase 1 (12th from Moon)";
    case "peak":
      return "Peak Phase (over natal Moon)";
    case "third_year":
      return "Phase 3 (2nd from Moon)";
    default:
      return "Active";
  }
}

export function TransitAlerts({
  transits,
  patterns,
}: {
  transits: TransitResponse;
  patterns?: TransitPatternsResponse;
}) {
  const alerts: Alert[] = [];

  if (patterns?.sade_sati.is_active) {
    alerts.push({
      key: "sade-sati",
      title: `Sade Sati — ${phaseLabel(patterns.sade_sati.phase)}`,
      description: "Saturn transiting within the 12th–1st–2nd houses from natal Moon.",
      range: formatRange(patterns.sade_sati.start_date, patterns.sade_sati.end_date),
      tone: "warn",
    });
  }
  if (patterns?.ashtama_shani.is_active) {
    alerts.push({
      key: "ashtama-shani",
      title: "Ashtama Shani",
      description: "Saturn transiting the 8th house from natal Moon.",
      range: formatRange(patterns.ashtama_shani.start_date, patterns.ashtama_shani.end_date),
      tone: "warn",
    });
  }
  for (const p of transits.planets) {
    if (p.has_vedha) {
      alerts.push({
        key: `${p.planet}-vedha`,
        title: `${p.planet} — Vedha`,
        description: `Favorable-house effect currently obstructed by ${p.vedha_planet ?? "another planet"}.`,
        tone: "danger",
      });
    }
    if (p.has_nakshatra_vedha) {
      alerts.push({
        key: `${p.planet}-nakshatra-vedha`,
        title: `${p.planet} — Nakshatra Vedha`,
        description: `${p.nakshatra_vedha_planet ?? "Another planet"} occupies ${p.planet}'s Vedha target nakshatra (${p.nakshatra_vedha_target ?? "—"}).`,
        tone: "danger",
      });
    }
  }

  return (
    <Card padding="0">
      <div className="px-4 py-3.5 border-b border-slate-200 dark:border-slate-800">
        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Transit Alerts
        </span>
      </div>
      <div className="flex flex-col gap-2.5 p-4">
        {alerts.length === 0 ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            No active Sade Sati, Ashtama Shani, or Vedha obstructions right now.
          </p>
        ) : (
          alerts.map((a) => {
            const isDanger = a.tone === "danger";
            return (
              <div
                key={a.key}
                className={`rounded-xl border p-3.5 transition ${
                  isDanger
                    ? "bg-rose-50/80 dark:bg-rose-950/30 border-rose-200 dark:border-rose-800/60"
                    : "bg-amber-50/80 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800/60"
                }`}
              >
                <span className={`text-sm font-semibold block ${isDanger ? "text-rose-900 dark:text-rose-200" : "text-amber-900 dark:text-amber-200"}`}>
                  {a.title}
                </span>
                {a.range && (
                  <div className="mt-0.5 font-mono text-[10px] text-slate-600 dark:text-slate-400">
                    {a.range}
                  </div>
                )}
                <div className="mt-1 text-xs text-slate-700 dark:text-slate-300">
                  {a.description}
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
