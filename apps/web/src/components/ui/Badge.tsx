import type { ReactNode } from "react";

type BadgeTone = "cyan" | "gold" | "violet" | "success" | "danger" | "neutral";

const TONE: Record<BadgeTone, { bg: string; fg: string; border: string }> = {
  cyan: { bg: "var(--badge-cyan-bg)", fg: "var(--badge-cyan-fg)", border: "var(--badge-cyan-border)" },
  gold: { bg: "var(--badge-gold-bg)", fg: "var(--badge-gold-fg)", border: "var(--badge-gold-border)" },
  violet: { bg: "var(--badge-violet-bg)", fg: "var(--badge-violet-fg)", border: "var(--badge-violet-border)" },
  success: { bg: "var(--badge-success-bg)", fg: "var(--badge-success-fg)", border: "var(--badge-success-border)" },
  danger: { bg: "var(--badge-danger-bg)", fg: "var(--badge-danger-fg)", border: "var(--badge-danger-border)" },
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
