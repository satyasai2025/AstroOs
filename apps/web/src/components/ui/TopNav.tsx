"use client";

import type { ReactNode } from "react";

interface TopNavProps {
  title?: string;
  breadcrumb?: ReactNode;
  children?: ReactNode;
  avatarInitial?: string;
}

export function TopNav({ title, breadcrumb, children, avatarInitial = "A" }: TopNavProps) {
  return (
    <div
      style={{
        height: "var(--topbar-height)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 var(--space-3)",
        borderBottom: "1px solid var(--border-subtle)",
        background: "rgba(10,15,30,0.6)",
        backdropFilter: "var(--blur-glass)",
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {breadcrumb}
        {title && (
          <span style={{ fontFamily: "var(--font-display)", fontSize: "var(--text-xl)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
            {title}
          </span>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
        {children}
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "linear-gradient(135deg, var(--violet-400), var(--cyan-500))",
            color: "#0a0f1e",
            fontWeight: "var(--weight-bold)",
            fontSize: "var(--text-sm)",
            flexShrink: 0,
          }}
        >
          {avatarInitial}
        </div>
      </div>
    </div>
  );
}
