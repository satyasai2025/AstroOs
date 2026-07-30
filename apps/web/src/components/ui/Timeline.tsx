type TimelineTone = "cyan" | "gold" | "violet" | "success" | "danger";

const TONE: Record<TimelineTone, string> = {
  cyan: "var(--cyan-400)",
  gold: "var(--gold-400)",
  violet: "var(--violet-400)",
  success: "var(--success-400)",
  danger: "var(--danger-400)",
};

export interface TimelineEvent {
  title: string;
  date: string;
  description?: string;
  tone?: TimelineTone;
}

interface TimelineProps {
  events: TimelineEvent[];
}

export function Timeline({ events = [] }: TimelineProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {events.map((e, i) => (
        <div key={i} style={{ display: "flex", gap: 14 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 16 }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                flexShrink: 0,
                marginTop: 4,
                background: TONE[e.tone || "cyan"],
                boxShadow: `0 0 10px ${TONE[e.tone || "cyan"]}`,
              }}
            />
            {i < events.length - 1 && <div style={{ flex: 1, width: 2, background: "var(--border-default)", minHeight: 28 }} />}
          </div>
          <div style={{ paddingBottom: 22, flex: 1 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 2 }}>
              <span style={{ fontSize: "var(--text-base)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>{e.title}</span>
              <span style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", fontFamily: "var(--font-mono)" }}>{e.date}</span>
            </div>
            {e.description && <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>{e.description}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}
