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
      className="flex items-center gap-2.5 h-10 px-3 rounded-lg border bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-800 transition-colors focus-within:ring-2 focus-within:ring-sky-500 focus-within:border-sky-500 min-w-[280px]"
      style={style}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-slate-400 dark:text-slate-500 shrink-0">
        <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
        <path d="M21 21l-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <input
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="w-full bg-transparent text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none text-sm"
      />
      {shortcut && (
        <kbd
          className="font-mono text-[11px] text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 rounded px-1.5 py-0.5"
        >
          {shortcut}
        </kbd>
      )}
    </div>
  );
}
