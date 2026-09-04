"use client";

import type { CSSProperties, ReactNode } from "react";

interface InputProps {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  type?: string;
  icon?: ReactNode;
  error?: string;
  hint?: string;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
  style?: CSSProperties;
  name?: string;
  required?: boolean;
  /** Passed straight to the input. For type="time", step={1} shows seconds. */
  step?: number | string;
}

export function Input({
  label,
  placeholder,
  value,
  onChange,
  type = "text",
  icon,
  error,
  hint,
  disabled,
  size = "md",
  style,
  name,
  required,
  step,
}: InputProps) {
  const heightClass = size === "sm" ? "h-8.5" : size === "lg" ? "h-12" : "h-10";
  return (
    <label style={style} className="flex flex-col gap-1.5 w-full">
      {label && (
        <span className="text-slate-700 dark:text-slate-300 font-medium text-xs">
          {label}
          {required && <span className="text-rose-500 ml-0.5">*</span>}
        </span>
      )}
      <div
        className={`flex items-center gap-2 px-3 rounded-lg transition shadow-sm ${heightClass} ${
          error
            ? "border border-rose-500 focus-within:ring-2 focus-within:ring-rose-500 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
            : "bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 text-slate-900 dark:text-slate-100 focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-indigo-500"
        } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        {icon && <span className="text-slate-400 dark:text-slate-500 flex shrink-0">{icon}</span>}
        <input
          type={type}
          step={step}
          name={name}
          required={required}
          placeholder={placeholder}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange && onChange(e.target.value)}
          className="w-full bg-transparent text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 outline-none text-sm"
        />
      </div>
      {(error || hint) && (
        <span className={`text-xs ${error ? "text-rose-500 font-medium" : "text-slate-500 dark:text-slate-400"}`}>
          {error || hint}
        </span>
      )}
    </label>
  );
}
