"use client";

import type { CSSProperties } from "react";

interface SearchInputProps {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  shortcut?: string;
  style?: CSSProperties;
}

export function SearchInput({
  value,
  onChange,
  placeholder = "Search charts, natives, transits…",
  shortcut = "⌘K",
  style,
}: SearchInputProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        height: 40,
        padding: "0 12px",
        borderRadius: "var(--radius-md)",
        background: "var(--surface-glass)",
        border: "1px solid var(--border-subtle)",
        minWidth: 280,
        ...style,
      }}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ color: "var(--text-tertiary)", flexShrink: 0 }}>
        <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
        <path d="M21 21l-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <input
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        placeholder={placeholder}
        style={{ all: "unset", flex: 1, color: "var(--text-primary)", fontSize: "var(--text-base)" }}
      />
      {shortcut && (
        <kbd
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-xs)",
            color: "var(--text-tertiary)",
            border: "1px solid var(--border-default)",
            borderRadius: "var(--radius-xs)",
            padding: "2px 6px",
          }}
        >
          {shortcut}
        </kbd>
      )}
    </div>
  );
}
