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
  const height = size === "sm" ? 34 : size === "lg" ? 48 : 40;
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6, fontFamily: "var(--font-body)", width: "100%", ...style }}>
      {label && (
        <span style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", fontWeight: "var(--weight-medium)" }}>
          {label}
        </span>
      )}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          height,
          padding: "0 12px",
          borderRadius: "var(--radius-md)",
          background: "var(--bg-surface-800)",
          border: `1px solid ${error ? "var(--danger-500)" : "var(--border-default)"}`,
          transition: "border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out)",
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = "var(--border-focus)";
          e.currentTarget.style.boxShadow = "0 0 0 3px var(--cyan-glow-soft)";
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = error ? "var(--danger-500)" : "var(--border-default)";
          e.currentTarget.style.boxShadow = "none";
        }}
      >
        {icon && <span style={{ color: "var(--text-tertiary)", display: "flex" }}>{icon}</span>}
        <input
          type={type}
          step={step}
          name={name}
          required={required}
          placeholder={placeholder}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange && onChange(e.target.value)}
          style={{
            all: "unset",
            flex: 1,
            color: "var(--text-primary)",
            fontSize: "var(--text-base)",
            opacity: disabled ? 0.5 : 1,
          }}
        />
      </div>
      {(error || hint) && (
        <span style={{ fontSize: "var(--text-xs)", color: error ? "var(--danger-400)" : "var(--text-tertiary)" }}>
          {error || hint}
        </span>
      )}
    </label>
  );
}
