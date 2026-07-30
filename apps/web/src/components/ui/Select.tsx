"use client";

import { useEffect, useRef, useState } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  label?: string;
  options?: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function Select({ label, options = [], value, onChange, placeholder = "Select…", disabled }: SelectProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const current = options.find((o) => o.value === value);

  return (
    <div ref={ref} style={{ position: "relative", fontFamily: "var(--font-body)", width: "100%" }}>
      {label && (
        <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", fontWeight: "var(--weight-medium)", marginBottom: 6 }}>
          {label}
        </div>
      )}
      <button
        type="button"
        onClick={() => !disabled && setOpen((o) => !o)}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          height: 40,
          padding: "0 12px",
          borderRadius: "var(--radius-md)",
          background: "var(--bg-surface-800)",
          border: `1px solid ${open ? "var(--border-focus)" : "var(--border-default)"}`,
          color: current ? "var(--text-primary)" : "var(--text-tertiary)",
          fontSize: "var(--text-base)",
          cursor: disabled ? "not-allowed" : "pointer",
          opacity: disabled ? 0.5 : 1,
        }}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>
          {current ? current.label : placeholder}
        </span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform var(--duration-fast)" }}
        >
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <div
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            right: 0,
            zIndex: 20,
            background: "var(--bg-surface-700)",
            border: "1px solid var(--border-default)",
            borderRadius: "var(--radius-md)",
            boxShadow: "var(--shadow-lg)",
            padding: 6,
            maxHeight: 240,
            overflowY: "auto",
            backdropFilter: "var(--blur-glass)",
          }}
        >
          {options.map((o) => (
            <div
              key={o.value}
              onClick={() => {
                onChange && onChange(o.value);
                setOpen(false);
              }}
              style={{
                padding: "8px 10px",
                borderRadius: "var(--radius-sm)",
                fontSize: "var(--text-base)",
                color: o.value === value ? "var(--cyan-300)" : "var(--text-primary)",
                background: o.value === value ? "var(--cyan-glow-soft)" : "transparent",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => {
                if (o.value !== value) e.currentTarget.style.background = "var(--surface-glass-strong)";
              }}
              onMouseLeave={(e) => {
                if (o.value !== value) e.currentTarget.style.background = "transparent";
              }}
            >
              {o.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
