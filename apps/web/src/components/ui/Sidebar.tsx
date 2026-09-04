"use client";

export interface SidebarItem {
  key: string;
  label: string;
  group: string;
  disabled?: boolean;
  badge?: string;
}

interface SidebarGroup {
  name: string;
  items: SidebarItem[];
}

function groupBy(items: SidebarItem[]): SidebarGroup[] {
  const out: SidebarGroup[] = [];
  for (const it of items) {
    let g = out.find((g) => g.name === it.group);
    if (!g) {
      g = { name: it.group, items: [] };
      out.push(g);
    }
    g.items.push(it);
  }
  return out;
}

interface SidebarProps {
  items: SidebarItem[];
  activeKey?: string;
  onSelect?: (key: string) => void;
  collapsed?: boolean;
  brand?: string;
}

export function Sidebar({ items, activeKey, onSelect, collapsed, brand = "AstroOS" }: SidebarProps) {
  const groups = groupBy(items);
  return (
    <div
      style={{
        width: collapsed ? "var(--sidebar-width-collapsed)" : "var(--sidebar-width)",
        background: "var(--bg-charcoal-900)",
        borderRight: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        padding: "var(--space-2) var(--space-1_5)",
        transition: "width var(--duration-base) var(--ease-standard)",
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "0 8px", height: 40, marginBottom: "var(--space-3)" }}>
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 8,
            flexShrink: 0,
            background: "conic-gradient(from 180deg, var(--cyan-400), var(--violet-400), var(--gold-400), var(--cyan-400))",
            boxShadow: "var(--glow-cyan)",
          }}
        />
        {!collapsed && (
          <span style={{ fontFamily: "var(--font-display)", fontWeight: "var(--weight-bold)", fontSize: "var(--text-lg)", color: "var(--text-primary)" }}>
            {brand}
          </span>
        )}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2_5)", overflowY: "auto" }}>
        {groups.map((g) => (
          <div key={g.name}>
            {!collapsed && (
              <div
                style={{
                  fontSize: "var(--text-xs)",
                  color: "var(--text-tertiary)",
                  textTransform: "uppercase",
                  letterSpacing: "var(--tracking-widest)",
                  padding: "0 10px",
                  marginBottom: 6,
                }}
              >
                {g.name}
              </div>
            )}
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {g.items.map((it) => {
                const active = it.key === activeKey;
                return (
                  <div
                    key={it.key}
                    onClick={() => !it.disabled && onSelect && onSelect(it.key)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      padding: "9px 10px",
                      borderRadius: "var(--radius-sm)",
                      cursor: it.disabled ? "default" : "pointer",
                      fontSize: "var(--text-base)",
                      fontWeight: active ? "var(--weight-semibold)" : "var(--weight-regular)",
                      color: it.disabled ? "var(--text-disabled)" : active ? "var(--cyan-300)" : "var(--text-secondary)",
                      background: active ? "var(--cyan-glow-soft)" : "transparent",
                      borderLeft: active ? "2px solid var(--cyan-400)" : "2px solid transparent",
                      opacity: it.disabled ? 0.6 : 1,
                    }}
                    onMouseEnter={(e) => {
                      if (!active && !it.disabled) e.currentTarget.style.background = "var(--surface-glass-strong)";
                    }}
                    onMouseLeave={(e) => {
                      if (!active) e.currentTarget.style.background = "transparent";
                    }}
                  >
                    <span
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        background: active ? "var(--cyan-400)" : "var(--text-disabled)",
                        flexShrink: 0,
                      }}
                    />
                    {!collapsed && it.label}
                    {!collapsed && it.badge && (
                      <span
                        style={{
                          marginLeft: "auto",
                          fontSize: "var(--text-xs)",
                          color: "var(--text-tertiary)",
                          textTransform: "uppercase",
                          letterSpacing: "var(--tracking-wide)",
                        }}
                      >
                        {it.badge}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
