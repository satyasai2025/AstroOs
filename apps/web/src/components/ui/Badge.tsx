import type { ReactNode } from "react";

type BadgeTone = "cyan" | "gold" | "violet" | "success" | "danger" | "neutral";

const TONE: Record<BadgeTone, { bg: string; fg: string; border: string }> = {
  cyan: { bg: "rgba(34,211,238,0.12)", fg: "var(--cyan-300)", border: "rgba(34,211,238,0.3)" },
  gold: { bg: "rgba(240,192,90,0.12)", fg: "var(--gold-300)", border: "rgba(240,192,90,0.3)" },
  violet: { bg: "rgba(139,92,246,0.12)", fg: "var(--violet-300)", border: "rgba(139,92,246,0.3)" },
  success: { bg: "rgba(52,211,153,0.12)", fg: "var(--success-400)", border: "rgba(52,211,153,0.3)" },
  danger: { bg: "rgba(244,63,94,0.12)", fg: "var(--danger-400)", border: "rgba(244,63,94,0.3)" },
  neutral: { bg: "var(--surface-glass-strong)", fg: "var(--text-secondary)", border: "var(--border-default)" },
};

interface BadgeProps {
  children?: ReactNode;
  tone?: BadgeTone;
  dot?: boolean;
  className?: string;
}

export function Badge({ children, tone = "neutral", dot, className }: BadgeProps) {
  const t = TONE[tone] || TONE.neutral;
  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "3px 10px",
        borderRadius: "var(--radius-full)",
        background: t.bg,
        color: t.fg,
        border: `1px solid ${t.border}`,
        fontSize: "var(--text-xs)",
        fontWeight: "var(--weight-semibold)",
        letterSpacing: "var(--tracking-wide)",
        textTransform: "uppercase",
      }}
    >
      {dot && <span style={{ width: 6, height: 6, borderRadius: "50%", background: t.fg }} />}
      {children}
    </span>
  );
}
