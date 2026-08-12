"use client";

import { Timeline, type TimelineEvent } from "@/components/ui/Timeline";
import type { WorkflowAnalysisResponse } from "@/lib/types";
import type { PlanetContext } from "./context";

function ymd(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toISOString().slice(0, 10);
}

interface Props {
  ctx: PlanetContext;
  result: WorkflowAnalysisResponse;
}

/**
 * Factual NATAL → DASHA → TRANSIT → ACTIVATION chain, showing only currently
 * active periods. Analytical, not decorative.
 */
export function TimelineTab({ ctx }: Props) {
  const events: TimelineEvent[] = [];

  // NATAL
  if (ctx.position) {
    events.push({
      title: `Natal ${ctx.planet}`,
      date: `natal · ${ctx.position.rashi}`,
      description: `${ctx.position.rashi_degree.toFixed(2)}° · ${ctx.position.nakshatra} pada ${ctx.position.pada} · House ${ctx.position.house_number}`,
      tone: "violet",
    });
  }

  // DASHA — current chain
  ctx.dashaChain.forEach((p, i) => {
    events.push({
      title: `${p.lord} dasha${p.lord === ctx.planet ? " (this planet)" : ""}`,
      date: `${ymd(p.start_date)} → ${ymd(p.end_date)}`,
      description: i === 0 ? "Current dasha period" : "Sub-period of the above",
      tone: p.lord === ctx.planet ? "gold" : "cyan",
    });
  });

  // TRANSIT
  if (ctx.transit) {
    events.push({
      title: `Transit ${ctx.transit.planet} through ${ctx.transit.transit_rashi}`,
      date: "current transit",
      description: [
        ctx.transit.is_sade_sati && "Sade Sati",
        ctx.transit.is_ashtama_shani && "Ashtama Shani",
        ctx.transit.is_favorable_house === true && "favorable house",
        ctx.transit.has_nakshatra_vedha && "Nakshatra Vedha",
      ]
        .filter(Boolean)
        .join(" · ") || "transit read",
      tone: "danger",
    });
  }

  // ACTIVATION — yogas + dasha/transit hits
  for (const y of ctx.yogasInvolving) {
    events.push({
      title: `Yoga active: ${y.name}`,
      date: y.strength ? y.strength : "yoga",
      description: `${y.involved_planets.join(" + ")}`,
      tone: "success",
    });
  }
  const dashaActive = ctx.dashaChain.some((p) => p.lord === ctx.planet);
  if (dashaActive) {
    events.push({
      title: `${ctx.planet} structurally activated`,
      date: "dasha window",
      description: "Relevant during the current dasha chain",
      tone: "gold",
    });
  }

  if (events.length === 0) {
    return <p className="text-sm" style={{ color: "var(--text-muted)" }}>No timeline events resolved for {ctx.planet}.</p>;
  }

  return (
    <div className="rounded-2xl border p-5" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
      <h3 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
        Activation Timeline
      </h3>
      <Timeline events={events} />
    </div>
  );
}