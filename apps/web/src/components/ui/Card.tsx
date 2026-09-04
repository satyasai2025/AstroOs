import type { CSSProperties, ReactNode } from "react";

type Glow = "cyan" | "gold" | "violet" | "success";

interface CardProps {
  id?: string;
  children?: ReactNode;
  glow?: Glow;
  padding?: string;
  style?: CSSProperties;
  className?: string;
}

export function Card({ id, children, glow, padding = "var(--space-3)", style, className }: CardProps) {
  return (
    <div
      id={id}
      className={`bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-sm shadow-slate-200/50 dark:shadow-none transition-all ${className ?? ""}`}
      style={{
        borderRadius: "var(--radius-lg, 0.75rem)",
        padding,
        boxShadow: glow ? `var(--shadow-md), var(--glow-${glow})` : undefined,
        ...style,
      }}
    >
      {children}
    </div>
  );
}


