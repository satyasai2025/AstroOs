import type { CSSProperties, ReactNode } from "react";

type Glow = "cyan" | "gold" | "violet" | "success";

interface CardProps {
  children?: ReactNode;
  glow?: Glow;
  padding?: string;
  style?: CSSProperties;
  className?: string;
}

export function Card({ children, glow, padding = "var(--space-3)", style, className }: CardProps) {
  return (
    <div
      className={className}
      style={{
        background: "linear-gradient(180deg, var(--bg-surface-800), var(--bg-surface-700))",
        border: "1px solid var(--border-default)",
        borderRadius: "var(--radius-lg)",
        padding,
        boxShadow: glow ? `var(--shadow-md), var(--glow-${glow})` : "var(--shadow-md), var(--shadow-inset)",
        backdropFilter: "var(--blur-glass)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
