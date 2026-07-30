"use client";

import { useState } from "react";

export interface TreeNode {
  key: string;
  label: string;
  color?: string;
  defaultOpen?: boolean;
  children?: TreeNode[];
}

interface NodeProps {
  node: TreeNode;
  depth: number;
  activeKey?: string;
  onSelect?: (key: string) => void;
}

function Node({ node, depth, activeKey, onSelect }: NodeProps) {
  const [open, setOpen] = useState(node.defaultOpen !== false && depth < 1);
  const hasChildren = Boolean(node.children && node.children.length > 0);
  const active = node.key === activeKey;
  return (
    <div>
      <div
        onClick={() => {
          hasChildren ? setOpen((o) => !o) : onSelect && onSelect(node.key);
        }}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "6px 8px",
          paddingLeft: 8 + depth * 16,
          borderRadius: "var(--radius-sm)",
          cursor: "pointer",
          fontSize: "var(--text-base)",
          color: active ? "var(--cyan-300)" : "var(--text-secondary)",
          background: active ? "var(--cyan-glow-soft)" : "transparent",
        }}
        onMouseEnter={(e) => {
          if (!active) e.currentTarget.style.background = "var(--surface-glass-strong)";
        }}
        onMouseLeave={(e) => {
          if (!active) e.currentTarget.style.background = "transparent";
        }}
      >
        {hasChildren ? (
          <svg
            width="10"
            height="10"
            viewBox="0 0 24 24"
            fill="none"
            style={{ transform: open ? "rotate(90deg)" : "none", transition: "transform var(--duration-fast)", flexShrink: 0, color: "var(--text-tertiary)" }}
          >
            <path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        ) : (
          <span style={{ width: 10, height: 10, flexShrink: 0 }} />
        )}
        <span style={{ width: 6, height: 6, borderRadius: "50%", flexShrink: 0, background: node.color || "var(--text-disabled)" }} />
        <span>{node.label}</span>
      </div>
      {hasChildren && open && node.children!.map((c) => <Node key={c.key} node={c} depth={depth + 1} activeKey={activeKey} onSelect={onSelect} />)}
    </div>
  );
}

interface TreeViewProps {
  data: TreeNode[];
  activeKey?: string;
  onSelect?: (key: string) => void;
}

export function TreeView({ data = [], activeKey, onSelect }: TreeViewProps) {
  return (
    <div style={{ fontFamily: "var(--font-body)", display: "flex", flexDirection: "column", gap: 2 }}>
      {data.map((n) => (
        <Node key={n.key} node={n} depth={0} activeKey={activeKey} onSelect={onSelect} />
      ))}
    </div>
  );
}
