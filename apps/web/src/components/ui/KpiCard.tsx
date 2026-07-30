import type { ReactNode } from "react";

type KpiAccent = "cyan" | "gold" | "violet" | "success";

const ACCENTS: Record<KpiAccent, { text: string; glow: string }> = {
  cyan: { text: "var(--cyan-400)", glow: "var(--cyan-glow-soft)" },
  gold: { text: "var(--gold-400)", glow: "var(--gold-glow-soft)" },
  violet: { text: "var(--violet-400)", glow: "var(--violet-glow-soft)" },
  success: { text: "var(--success-400)", glow: "rgba(16,185,129,0.1)" },
};

interface KpiCardProps {
  label: string;
  value: ReactNode;
  delta?: ReactNode;
  deltaDirection?: "up" | "down";
  accent?: KpiAccent;
  icon?: ReactNode;
  /** Small caption below the value — e.g. a data-provenance note. Not part
   * of the original kit component, added for cases where the number's
   * source needs a one-line explanation (real backend field vs synthesized
   * heuristic, etc). */
  caveat?: ReactNode;
}

export function KpiCard({ label, value, delta, deltaDirection = "up", accent = "cyan", icon, caveat }: KpiCardProps) {
  const a = ACCENTS[accent] || ACCENTS.cyan;
  const up = deltaDirection === "up";
  // Long text values (e.g. "No reviews yet") wrap ugly at the default
  // display size — mirrors the kit mockup's own length-based downshift.
  const valueFontSize = typeof value === "string" && value.length > 4 ? "var(--text-xl)" : "var(--text-3xl)";
  return (
    <div
      style={{
        background: "linear-gradient(180deg, var(--bg-surface-800), var(--bg-surface-700))",
        border: "1px solid var(--border-default)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--space-2_5)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-1_5)",
        boxShadow: "var(--shadow-md)",
        position: "relative",
        overflow: "hidden",
        minWidth: 180,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -30,
          right: -30,
          width: 100,
          height: 100,
          borderRadius: "50%",
          background: a.glow,
          filter: "blur(10px)",
        }}
      />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", fontWeight: "var(--weight-medium)" }}>
          {label}
        </span>
        {icon && <span style={{ color: a.text }}>{icon}</span>}
      </div>
      <div
        style={{
          fontFamily: "var(--font-display)",
          fontSize: valueFontSize,
          fontWeight: "var(--weight-bold)",
          color: "var(--text-primary)",
          letterSpacing: "var(--tracking-tight)",
        }}
      >
        {value}
      </div>
      {delta && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontSize: "var(--text-xs)",
            color: up ? "var(--success-400)" : "var(--danger-400)",
            fontWeight: "var(--weight-semibold)",
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" style={{ transform: up ? "none" : "rotate(180deg)" }}>
            <path d="M12 19V5M5 12l7-7 7 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {delta}
        </div>
      )}
      {caveat && (
        <div style={{ fontSize: "var(--text-xs)", color: "var(--text-tertiary)", lineHeight: "var(--leading-snug)" }}>{caveat}</div>
      )}
    </div>
  );
}
