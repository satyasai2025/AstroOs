"use client";

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterDef {
  key: string;
  label: string;
  options: FilterOption[];
}

interface FilterBarProps {
  filters: FilterDef[];
  activeValues?: Record<string, string>;
  onChange?: (key: string, value: string) => void;
  onClear?: () => void;
}

export function FilterBar({ filters = [], activeValues = {}, onChange, onClear }: FilterBarProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
      {filters.map((f) => (
        <div key={f.key} style={{ position: "relative" }}>
          <select
            value={activeValues[f.key] || ""}
            onChange={(e) => onChange && onChange(f.key, e.target.value)}
            style={{
              appearance: "none",
              background: "var(--surface-glass-strong)",
              border: "1px solid var(--border-default)",
              borderRadius: "var(--radius-full)",
              color: "var(--text-secondary)",
              fontSize: "var(--text-sm)",
              padding: "7px 30px 7px 14px",
              cursor: "pointer",
              fontFamily: "var(--font-body)",
            }}
          >
            <option value="">{f.label}</option>
            {f.options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      ))}
      {onClear && (
        <span onClick={onClear} style={{ fontSize: "var(--text-sm)", color: "var(--cyan-400)", cursor: "pointer" }}>
          Clear filters
        </span>
      )}
    </div>
  );
}
