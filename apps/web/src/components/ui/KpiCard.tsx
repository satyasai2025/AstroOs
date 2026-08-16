import Link from "next/link";
import type { CSSProperties, ReactNode } from "react";

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
  /** When set, the whole card becomes a link to this route (e.g. a "Total
   * Charts" KPI linking to /charts/history) — cards without it stay plain,
   * non-interactive summary tiles (e.g. research/dashboard's placeholder
   * KPIs, which have nowhere real to link to yet). */
  href?: string;
}

export function KpiCard({ label, value, delta, deltaDirection = "up", accent = "cyan", icon, caveat, href }: KpiCardProps) {
  const a = ACCENTS[accent] || ACCENTS.cyan;
  const up = deltaDirection === "up";
  // Long text values (e.g. "No reviews yet") wrap ugly at the default
  // display size — mirrors the kit mockup's own length-based downshift.
  const valueFontSize = typeof value === "string" && value.length > 4 ? "var(--text-xl)" : "var(--text-3xl)";

  const cardStyle: CSSProperties = {
    borderRadius: "var(--radius-lg)",
    padding: "var(--space-2_5)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-1_5)",
    position: "relative",
    overflow: "hidden",
    minWidth: 180,
  };

  const content = (
    <div
      style={
        href
          ? { ...cardStyle, cursor: "pointer", transition: "border-color var(--duration-fast, 150ms), transform var(--duration-fast, 150ms)" }
          : cardStyle
      }
      className={`bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800 shadow-sm shadow-slate-200/50 dark:shadow-none ${
        href ? "group hover:-translate-y-0.5 hover:border-cyan-500/60 dark:hover:border-cyan-500/40" : ""
      }`}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span className="text-xs font-semibold tracking-wider text-slate-500 dark:text-slate-400 uppercase">
          {label}
        </span>
        {icon && <span style={{ color: a.text }}>{icon}</span>}
      </div>
      <div
        className={`${typeof value === "string" && value.length > 4 ? "text-xl" : "text-3xl"} font-bold text-slate-900 dark:text-slate-100`}
        style={{
          fontFamily: "var(--font-display)",
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
        <div className="text-xs leading-snug text-slate-600 dark:text-slate-400">{caveat}</div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block no-underline">
        {content}
      </Link>
    );
  }

  return content;
}
