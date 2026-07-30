"use client";

export interface TabItem {
  key: string;
  label: string;
}

interface TabsProps {
  tabs: TabItem[];
  active?: string;
  onChange?: (key: string) => void;
}

export function Tabs({ tabs = [], active, onChange }: TabsProps) {
  return (
    <div style={{ display: "flex", gap: "var(--space-3)", borderBottom: "1px solid var(--border-subtle)" }}>
      {tabs.map((t) => {
        const isActive = t.key === active;
        return (
          <div
            key={t.key}
            onClick={() => onChange && onChange(t.key)}
            style={{
              padding: "10px 2px",
              fontSize: "var(--text-base)",
              fontWeight: isActive ? "var(--weight-semibold)" : "var(--weight-regular)",
              color: isActive ? "var(--text-primary)" : "var(--text-tertiary)",
              cursor: "pointer",
              position: "relative",
            }}
          >
            {t.label}
            {isActive && (
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  bottom: -1,
                  height: 2,
                  background: "linear-gradient(90deg, var(--cyan-400), var(--violet-400))",
                  borderRadius: 2,
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
