"use client";

/**
 * AstroOS — Interactive Life Event Timeline Chart
 *
 * Plots a research case's life events (Marriage, Job Change, Relocation,
 * ...) along a horizontal timeline, positioned proportionally by date.
 * Clicking a node opens a modal with the event's full detail: date,
 * description, notes, and the astrological positions captured for it
 * (dasha, active yogas, transits, house-lord dignity, nakshatra
 * placements) via LifeEventDetail.snapshot.
 */

import { useMemo, useState } from "react";
import { Badge, Modal } from "@/components/ui";
import { titleCaseToken } from "@/lib/api";
import { formatEventTitle } from "@/lib/astro";
import type { LifeEventDetail } from "@/lib/types";

type Tone = "cyan" | "gold" | "violet" | "success" | "danger";
const TONE_ORDER: Tone[] = ["cyan", "gold", "violet", "success", "danger"];
const TONE_HEX: Record<Tone, string> = {
  cyan: "var(--cyan-400)",
  gold: "var(--gold-400)",
  violet: "var(--violet-400)",
  success: "var(--success-400)",
  danger: "var(--danger-400)",
};

function toneForEventType(eventType: string): Tone {
  let hash = 0;
  for (let i = 0; i < eventType.length; i++) {
    hash = (hash * 31 + eventType.charCodeAt(i)) >>> 0;
  }
  return TONE_ORDER[hash % TONE_ORDER.length];
}

function formatDate(iso: string): string {
  const d = new Date(iso + "T00:00:00Z");
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
}

interface PositionedEvent {
  event: LifeEventDetail;
  pct: number; // 0-100 position along the timeline
  lane: "top" | "bottom"; // alternate to reduce label overlap
}

function layoutEvents(events: LifeEventDetail[]): PositionedEvent[] {
  if (events.length === 0) return [];
  const sorted = [...events].sort((a, b) => a.event_date.localeCompare(b.event_date));
  if (sorted.length === 1) {
    return [{ event: sorted[0], pct: 50, lane: "top" }];
  }
  const times = sorted.map((e) => new Date(e.event_date + "T00:00:00Z").getTime());
  const min = Math.min(...times);
  const max = Math.max(...times);
  const span = max - min;
  return sorted.map((event, i) => {
    const t = new Date(event.event_date + "T00:00:00Z").getTime();
    // Spread evenly when every event falls on the same date (span === 0);
    // otherwise position proportionally, clamped away from the very edge
    // so nodes/labels never get clipped by the container.
    const pct = span === 0 ? (i / (sorted.length - 1)) * 100 : ((t - min) / span) * 96 + 2;
    return { event, pct, lane: i % 2 === 0 ? "top" : "bottom" };
  });
}

function SnapshotSection({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1 font-mono">
        {label}
      </div>
      {children}
    </div>
  );
}
export function EventDetailBody({ event }: { event: LifeEventDetail }) {
  const s = event.snapshot;
  const activeTransits = s ? Object.entries(s.transit_features).filter(([, active]) => active) : [];
  const houseEntries = s ? Object.entries(s.house_lord_statuses).sort((a, b) => Number(a[0]) - Number(b[0])) : [];

  return (
    <div className="space-y-4">
      <SnapshotSection label="Date">
        <div className="text-sm font-extrabold text-slate-900 dark:text-slate-100">
          {formatDate(event.event_date)}
          {event.event_time && <span className="text-slate-500 dark:text-slate-400 font-mono font-normal"> · {event.event_time}</span>}
          {event.event_place && <span className="text-slate-500 dark:text-slate-400 font-mono font-normal"> · {event.event_place}</span>}
        </div>
      </SnapshotSection>

      <SnapshotSection label="Description">
        <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">
          {event.description || event.event_type ? (
            formatEventTitle(event.description || event.event_type)
          ) : (
            <span className="text-slate-400 italic">No description recorded.</span>
          )}
        </div>
      </SnapshotSection>

      <SnapshotSection label="Chart / Astrological Positions">
        {!s ? (
          <div className="text-xs text-slate-500 dark:text-slate-400 italic font-mono">
            No astrological snapshot has been computed for this event yet.
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-1.5">
              {s.mahadasha && <Badge tone="cyan">Mahadasha: {titleCaseToken(s.mahadasha)}</Badge>}
              {s.antardasha && <Badge tone="violet">Antardasha: {titleCaseToken(s.antardasha)}</Badge>}
              {s.pratyantar && <Badge tone="gold">Pratyantar: {titleCaseToken(s.pratyantar)}</Badge>}
            </div>

            {s.active_yogas.length > 0 && (
              <div>
                <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1 font-mono">Active Yogas</div>
                <div className="flex flex-wrap gap-1.5">
                  {s.active_yogas.map((y) => (
                    <Badge key={y} tone="success">{y}</Badge>
                  ))}
                </div>
              </div>
            )}

            {activeTransits.length > 0 && (
              <div>
                <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1 font-mono">Transits</div>
                <div className="flex flex-wrap gap-1.5">
                  {activeTransits.map(([key]) => (
                    <Badge key={key} tone="neutral">{titleCaseToken(key)}</Badge>
                  ))}
                </div>
              </div>
            )}

            {houseEntries.length > 0 && (
              <div>
                <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1 font-mono">House Lord Dignity</div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 font-mono text-[11px]">
                  {houseEntries.map(([house, status]) => (
                    <div
                      key={house}
                      className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/80 text-slate-800 dark:text-slate-200 font-bold"
                    >
                      House {house}: <span className="text-cyan-600 dark:text-cyan-400">{titleCaseToken(status)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {s.nakshatra_activations.length > 0 && (
              <div>
                <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-1 font-mono">Nakshatra Placements</div>
                <div className="flex flex-wrap gap-1.5">
                  {s.nakshatra_activations.map((n) => (
                    <Badge key={n} tone="violet">{titleCaseToken(n)}</Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </SnapshotSection>

      <SnapshotSection label="Notes">
        <div className="text-xs text-slate-700 dark:text-slate-300">
          {event.notes || <span className="text-slate-400 italic">No notes recorded.</span>}
        </div>
      </SnapshotSection>
    </div>
  );
}

interface EventTimelineChartProps {
  events: LifeEventDetail[];
  onSelectEvent?: (event: LifeEventDetail) => void;
  selectedEventId?: string;
}

export function EventTimelineChart({ events, onSelectEvent, selectedEventId }: EventTimelineChartProps) {
  const [selectedModal, setSelectedModal] = useState<LifeEventDetail | null>(null);

  const positioned = useMemo(() => layoutEvents(events), [events]);

  const handleEventClick = (event: LifeEventDetail) => {
    if (onSelectEvent) {
      onSelectEvent(event);
    } else {
      setSelectedModal(event);
    }
  };

  if (events.length === 0) {
    return (
      <div style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)", padding: "var(--space-4)", textAlign: "center" }}>
        No life events recorded for this case.
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          position: "relative",
          minHeight: 160,
          padding: "56px var(--space-4) 0",
          overflowX: "auto",
        }}
      >
        {/* Baseline */}
        <div
          style={{
            position: "absolute",
            left: "var(--space-4)",
            right: "var(--space-4)",
            top: 88,
            height: 2,
            background: "var(--border-default)",
          }}
        />

        {positioned.map(({ event, pct, lane }) => {
          const tone = toneForEventType(event.event_type);
          const isTop = lane === "top";
          const isSelected = selectedEventId === event.id;
          return (
            <div
              key={event.id}
              style={{
                position: "absolute",
                left: `calc(${pct}% )`,
                top: 88,
                transform: "translateX(-50%)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
              }}
            >
              {isTop && (
                <button
                  type="button"
                  onClick={() => handleEventClick(event)}
                  style={{
                    position: "absolute",
                    bottom: 14,
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: 0,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 2,
                    width: 120,
                  }}
                  aria-label={`${event.event_type} on ${formatDate(event.event_date)}`}
                >
                  <span className={`text-xs font-semibold truncate max-w-[110px] ${isSelected ? "text-cyan-500 dark:text-cyan-400 font-extrabold" : "text-slate-800 dark:text-slate-200"}`}>
                    {formatEventTitle(event.event_type || event.description)}
                  </span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    {formatDate(event.event_date)}
                  </span>
                </button>
              )}

              <button
                type="button"
                onClick={() => handleEventClick(event)}
                aria-label={`View details for ${formatEventTitle(event.event_type || event.description)} on ${formatDate(event.event_date)}`}
                style={{
                  width: 26,
                  height: 26,
                  borderRadius: "50%",
                  background: TONE_HEX[tone],
                  boxShadow: isSelected ? `0 0 16px 4px ${TONE_HEX[tone]}` : `0 0 10px ${TONE_HEX[tone]}`,
                  border: isSelected ? "3px solid #06b6d4" : "2px solid var(--bg-surface-800, #0D1528)",
                  cursor: "pointer",
                  padding: 0,
                  transition: "transform 0.15s ease",
                  transform: isSelected ? "scale(1.25)" : "scale(1)",
                }}
              ></button>

              {!isTop && (
                <button
                  type="button"
                  onClick={() => handleEventClick(event)}
                  style={{
                    position: "absolute",
                    top: 14,
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: 0,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 2,
                    width: 120,
                  }}
                  aria-label={`${formatEventTitle(event.event_type || event.description)} on ${formatDate(event.event_date)}`}
                >
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    {formatDate(event.event_date)}
                  </span>
                  <span className={`text-xs font-semibold truncate max-w-[110px] ${isSelected ? "text-cyan-500 dark:text-cyan-400 font-extrabold" : "text-slate-800 dark:text-slate-200"}`}>
                    {formatEventTitle(event.event_type || event.description)}
                  </span>
                </button>
              )}
            </div>
          );
        })}
      </div>

      {!onSelectEvent && (
        <Modal
          open={selectedModal !== null}
          onClose={() => setSelectedModal(null)}
          title={selectedModal ? `${selectedModal.event_type}` : ""}
          width={560}
        >
          {selectedModal && <EventDetailBody event={selectedModal} />}
        </Modal>
      )}
    </div>
  );
}
