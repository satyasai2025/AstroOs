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
    <div style={{ marginBottom: "var(--space-3)" }}>
      <div
        style={{
          fontSize: "var(--text-xs)",
          fontWeight: "var(--weight-semibold)",
          color: "var(--text-tertiary)",
          textTransform: "uppercase",
          letterSpacing: "var(--tracking-wide)",
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      {children}
    </div>
  );
}

function EventDetailBody({ event }: { event: LifeEventDetail }) {
  const s = event.snapshot;
  const activeTransits = s ? Object.entries(s.transit_features).filter(([, active]) => active) : [];
  const houseEntries = s ? Object.entries(s.house_lord_statuses).sort((a, b) => Number(a[0]) - Number(b[0])) : [];

  return (
    <div>
      <SnapshotSection label="Date">
        <div style={{ color: "var(--text-primary)", fontSize: "var(--text-base)" }}>
          {formatDate(event.event_date)}
          {event.event_time && <span style={{ color: "var(--text-tertiary)" }}> · {event.event_time}</span>}
          {event.event_place && <span style={{ color: "var(--text-tertiary)" }}> · {event.event_place}</span>}
        </div>
      </SnapshotSection>

      <SnapshotSection label="Description">
        <div style={{ color: "var(--text-secondary)" }}>
          {event.description || <span style={{ color: "var(--text-tertiary)" }}>No description recorded.</span>}
        </div>
      </SnapshotSection>

      <SnapshotSection label="Chart / Astrological Positions">
        {!s ? (
          <div style={{ color: "var(--text-tertiary)", fontSize: "var(--text-sm)" }}>
            No astrological snapshot has been computed for this event yet.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {s.mahadasha && <Badge tone="cyan">Mahadasha: {titleCaseToken(s.mahadasha)}</Badge>}
              {s.antardasha && <Badge tone="violet">Antardasha: {titleCaseToken(s.antardasha)}</Badge>}
              {s.pratyantar && <Badge tone="gold">Pratyantar: {titleCaseToken(s.pratyantar)}</Badge>}
            </div>

            {s.active_yogas.length > 0 && (
              <div>
                <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", marginBottom: 4 }}>Active Yogas</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {s.active_yogas.map((y) => (
                    <Badge key={y} tone="success">{y}</Badge>
                  ))}
                </div>
              </div>
            )}

            {activeTransits.length > 0 && (
              <div>
                <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", marginBottom: 4 }}>Transits</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {activeTransits.map(([key]) => (
                    <Badge key={key} tone="neutral">{titleCaseToken(key)}</Badge>
                  ))}
                </div>
              </div>
            )}

            {houseEntries.length > 0 && (
              <div>
                <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", marginBottom: 4 }}>House Lord Dignity</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", gap: 6 }}>
                  {houseEntries.map(([house, status]) => (
                    <div
                      key={house}
                      style={{
                        fontSize: "var(--text-xs)",
                        color: "var(--text-secondary)",
                        background: "var(--surface-glass-strong)",
                        border: "1px solid var(--border-default)",
                        borderRadius: "var(--radius-md)",
                        padding: "4px 8px",
                      }}
                    >
                      House {house}: {titleCaseToken(status)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {s.nakshatra_activations.length > 0 && (
              <div>
                <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", marginBottom: 4 }}>Nakshatra Placements</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
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
        <div style={{ color: "var(--text-secondary)" }}>
          {event.notes || <span style={{ color: "var(--text-tertiary)" }}>No notes recorded.</span>}
        </div>
      </SnapshotSection>
    </div>
  );
}

interface EventTimelineChartProps {
  events: LifeEventDetail[];
}

export function EventTimelineChart({ events }: EventTimelineChartProps) {
  const [selected, setSelected] = useState<LifeEventDetail | null>(null);
  const positioned = useMemo(() => layoutEvents(events), [events]);

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
                  onClick={() => setSelected(event)}
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
                  <span style={{ fontSize: "var(--text-xs)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
                    {event.event_type}
                  </span>
                  <span style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>
                    {formatDate(event.event_date)}
                  </span>
                </button>
              )}

              <button
                onClick={() => setSelected(event)}
                aria-label={`View details for ${event.event_type} on ${formatDate(event.event_date)}`}
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  background: TONE_HEX[tone],
                  boxShadow: `0 0 10px ${TONE_HEX[tone]}`,
                  border: "2px solid var(--bg-surface-800, #0D1528)",
                  cursor: "pointer",
                  padding: 0,
                  transition: "transform 0.15s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.3)")}
                onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
              ></button>

              {!isTop && (
                <button
                  onClick={() => setSelected(event)}
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
                  aria-label={`${event.event_type} on ${formatDate(event.event_date)}`}
                >
                  <span style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>
                    {formatDate(event.event_date)}
                  </span>
                  <span style={{ fontSize: "var(--text-xs)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
                    {event.event_type}
                  </span>
                </button>
              )}
            </div>
          );
        })}
      </div>

      <Modal
        open={selected !== null}
        onClose={() => setSelected(null)}
        title={selected ? `${selected.event_type}` : ""}
        width={560}
      >
        {selected && <EventDetailBody event={selected} />}
      </Modal>
    </div>
  );
}
