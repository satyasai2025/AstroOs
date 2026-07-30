"use client";

import { Fragment } from "react";

interface BreadcrumbsProps {
  items: string[];
}

export function Breadcrumbs({ items = [] }: BreadcrumbsProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "var(--text-sm)", color: "var(--text-tertiary)" }}>
      {items.map((it, i) => (
        <Fragment key={i}>
          {i > 0 && <span style={{ color: "var(--text-disabled)" }}>/</span>}
          <span
            style={{
              color: i === items.length - 1 ? "var(--text-secondary)" : "var(--text-tertiary)",
              cursor: i === items.length - 1 ? "default" : "pointer",
            }}
            onMouseEnter={(e) => {
              if (i !== items.length - 1) e.currentTarget.style.color = "var(--cyan-300)";
            }}
            onMouseLeave={(e) => {
              if (i !== items.length - 1) e.currentTarget.style.color = "var(--text-tertiary)";
            }}
          >
            {it}
          </span>
        </Fragment>
      ))}
    </div>
  );
}
