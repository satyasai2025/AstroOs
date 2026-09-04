"use client";

import { useState, type ReactNode } from "react";

export interface AccordionItem {
  key: string;
  title: string;
  content: ReactNode;
}

interface AccordionProps {
  items: AccordionItem[];
  defaultOpenKey?: string;
}

export function Accordion({ items = [], defaultOpenKey }: AccordionProps) {
  const [openKey, setOpenKey] = useState(defaultOpenKey);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {items.map((it) => {
        const open = it.key === openKey;
        return (
          <div key={it.key} style={{ border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)", background: "var(--bg-surface-800)", overflow: "hidden" }}>
            <div
              onClick={() => setOpenKey(open ? undefined : it.key)}
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "13px 16px", cursor: "pointer" }}
            >
              <span style={{ fontSize: "var(--text-base)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>{it.title}</span>
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                style={{ color: "var(--text-tertiary)", transform: open ? "rotate(180deg)" : "none", transition: "transform var(--duration-fast)" }}
              >
                <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            {open && <div style={{ padding: "0 16px 16px", fontSize: "var(--text-sm)", color: "var(--text-secondary)" }}>{it.content}</div>}
          </div>
        );
      })}
    </div>
  );
}
