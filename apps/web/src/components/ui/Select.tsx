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
    <div ref={ref} className="relative w-full">
      {label && (
        <div className="text-slate-700 dark:text-slate-300 font-medium text-xs mb-1.5">
          {label}
        </div>
      )}
      <button
        type="button"
        aria-label={label || placeholder || "Select option"}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => !disabled && setOpen((o) => !o)}
        className={`flex items-center justify-between w-full h-10 px-3 rounded-lg bg-white dark:bg-slate-900 border transition shadow-sm text-sm ${
          open
            ? "border-indigo-500 ring-2 ring-indigo-500"
            : "border-slate-300 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700"
        } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
      >
        <span className={`overflow-hidden text-ellipsis whitespace-nowrap min-w-0 ${
          current ? "text-slate-900 dark:text-slate-100 font-medium" : "text-slate-400 dark:text-slate-500"
        }`}>
          {current ? current.label : placeholder}
        </span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          className={`shrink-0 ml-1 text-slate-500 dark:text-slate-400 transition-transform duration-150 ${
            open ? "rotate-180" : ""
          }`}
        >
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <div className="absolute top-[calc(100%+6px)] left-0 right-0 z-50 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl p-1.5 max-h-44 overflow-y-auto">
          {options.map((o) => (
            <div
              key={o.value}
              onClick={() => {
                onChange && onChange(o.value);
                setOpen(false);
              }}
              className={`px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition ${
                o.value === value
                  ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-semibold"
                  : "text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80"
              }`}
            >
              {o.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
