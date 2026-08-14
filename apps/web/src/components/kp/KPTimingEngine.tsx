"use client";

/**
 * KP Timing Engine — the complete KP fructification system. For each
 * event it shows the three real timing layers together:
 *
 *   1. Dasha Link — the running Vimshottari period chain and whether any
 *      level's lord is an event significator (computed on the backend).
 *   2. Transit Triggers — which transit planets are passing through the
 *      star/sub of an event significator, plus Guru's transit over the
 *      event's primary-cusp sign.
 *   3. Ruling Planet Triggers — the RPs at the transit moment (transit
 *      Moon sign/star/sub lords + transit weekday lord) that coincide
 *      with an event significator.
 *
 * The fructification verdict (OPEN / PARTIAL / CLOSED) combines all three
 * and arrives pre-computed from the backend KP engine.
 */

import type { EventTimingAnalysisResponse } from "@/lib/types";

interface Props {
  timing: EventTimingAnalysisResponse[];
}

const PROMISE_COLORS: Record<string, { fg: string; bg: string }> = {
  POSITIVE: { fg: "#34d399", bg: "rgba(52,211,153,0.15)" },
  PARTIAL: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
  WEAK: { fg: "#f87171", bg: "rgba(248,113,113,0.15)" },
};

const FRUCTIFICATION_COLORS: Record<EventTimingAnalysisResponse["fructification"], { fg: string; bg: string; label: string }> = {
  OPEN: { fg: "#34d399", bg: "rgba(52,211,153,0.15)", label: "Window Open" },
  PARTIAL: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)", label: "Partial" },
  CLOSED: { fg: "#f87171", bg: "rgba(248,113,113,0.15)", label: "Closed" },
};

const TRIGGER_TYPE_COLORS: Record<string, { fg: string; bg: string }> = {
  STAR: { fg: "#60a5fa", bg: "rgba(96,165,250,0.15)" },
  SUB: { fg: "#a78bfa", bg: "rgba(167,139,250,0.15)" },
  GURU: { fg: "#fbbf24", bg: "rgba(251,191,36,0.15)" },
  CUSP: { fg: "#f472b6", bg: "rgba(244,114,182,0.15)" },
};

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function KPTimingEngine({ timing }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        KP timing reads three real layers together — the running Vimshottari Dasha chain, the current
        transit positions (star/sub lords computed with the backend&apos;s own algorithm), and the Ruling
        Planets at the transit moment. A window is <strong style={{ color: "#34d399" }}>OPEN</strong> when an
        event significator&apos;s period is running AND a transit or RP trigger is active.
      </p>

      {timing.map((a) => {
        const fc = FRUCTIFICATION_COLORS[a.fructification];
        const pc = PROMISE_COLORS[a.promise];
        return (
          <div key={a.eventKey} className="glass-card p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{a.label}</span>
                <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ backgroundColor: pc.bg, color: pc.fg }}>
                  Promise {a.promise}
                </span>
              </div>
              <span className="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide" style={{ backgroundColor: fc.bg, color: fc.fg }}>
                {fc.label}
              </span>
            </div>

            <p className="mb-3 text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>{a.summary}</p>

            <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
              {/* Dasha Link */}
              <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
                  Dasha Link
                </p>
                <div className="mb-1.5 flex flex-wrap gap-1">
                  {a.dasha_link.chain.map((c) => (
                    <span key={c.level} className="rounded-full px-2 py-0.5 text-[10px]" style={{ backgroundColor: "rgba(148,163,184,0.12)", color: "var(--text-secondary)" }}>
                      {c.lord} · {c.level}
                    </span>
                  ))}
                </div>
                {a.dasha_link.significator_level ? (
                  <p className="text-[11px]" style={{ color: "#34d399" }}>
                    Significator running: <strong>{a.dasha_link.significator_level.lord}</strong> ({a.dasha_link.significator_level.level},{" "}
                    {formatDate(a.dasha_link.significator_level.start)} → {formatDate(a.dasha_link.significator_level.end)})
                  </p>
                ) : (
                  <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>No significator running in the active chain.</p>
                )}
                {a.dasha_link.next_significator_period && (
                  <p className="mt-1 text-[10px]" style={{ color: "var(--text-muted)" }}>
                    Next: {a.dasha_link.next_significator_period.lord} · {a.dasha_link.next_significator_period.level} (
                    {formatDate(a.dasha_link.next_significator_period.start)} → {formatDate(a.dasha_link.next_significator_period.end)})
                  </p>
                )}
              </div>

              {/* Transit Triggers */}
              <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
                  Transit Triggers ({a.transit_triggers.length})
                </p>
                {a.transit_triggers.length === 0 ? (
                  <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>No active transit trigger.</p>
                ) : (
                  <ul className="space-y-1.5">
                    {a.transit_triggers.map((tr, i) => {
                      const tc = TRIGGER_TYPE_COLORS[tr.type];
                      return (
                        <li key={i} className="flex items-start gap-2 text-[11px]" style={{ color: "var(--text-secondary)" }}>
                          <span className="mt-0.5 shrink-0 rounded px-1 py-0.5 text-[9px] font-bold" style={{ backgroundColor: tc.bg, color: tc.fg }}>
                            {tr.type}
                          </span>
                          <span>
                            <strong style={{ color: "var(--text-primary)" }}>{tr.transit_planet}</strong> in {tr.transit_rashi} · star{" "}
                            <strong style={{ color: "var(--accent)" }}>{tr.transit_star_lord}</strong> · sub{" "}
                            <strong style={{ color: "var(--accent)" }}>{tr.transit_sub_lord}</strong>
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              {/* RP Triggers */}
              <div className="rounded-lg border p-3" style={{ borderColor: "var(--border-primary)" }}>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>
                  Ruling Planet Triggers ({a.rp_triggers.length})
                </p>
                {a.rp_triggers.length === 0 ? (
                  <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>No transit-moment RP coincides with a significator.</p>
                ) : (
                  <ul className="space-y-1.5">
                    {a.rp_triggers.map((rp, i) => (
                      <li key={i} className="text-[11px]" style={{ color: "var(--text-secondary)" }}>
                        <strong style={{ color: "#60a5fa" }}>{rp.rp}</strong> — {rp.rpSource}
                        <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                          matched significator: {rp.matched_significator} — {rp.note}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
                <p className="mt-2 text-[10px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
                  Significators: {a.significators.join(", ")}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
