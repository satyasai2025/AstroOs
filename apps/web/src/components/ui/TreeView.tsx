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

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onSelect) {
      onSelect(node.key);
    }
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      setOpen((o) => !o);
    }
  };

  return (
    <div>
      <div
        onClick={handleClick}
        className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium transition cursor-pointer ${
          active
            ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/40"
            : "text-slate-300 hover:bg-slate-800/80 hover:text-slate-100"
        }`}
        style={{ paddingLeft: 8 + depth * 16 }}
      >
        {hasChildren ? (
          <button
            type="button"
            onClick={handleToggle}
            className="flex h-4 w-4 items-center justify-center rounded text-slate-400 hover:text-slate-200"
          >
            <svg
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              className={`transform transition-transform ${open ? "rotate-90" : "rotate-0"}`}
            >
              <path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        ) : (
          <span className="w-4 h-4 flex-shrink-0" />
        )}
        <span
          className="h-2 w-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: node.color || "#94a3b8" }}
        />
        <span className="truncate">{node.label}</span>
      </div>
      {hasChildren && open && (
        <div className="space-y-0.5 mt-0.5">
          {node.children!.map((c) => (
            <Node key={c.key} node={c} depth={depth + 1} activeKey={activeKey} onSelect={onSelect} />
          ))}
        </div>
      )}
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
    <div className="flex flex-col gap-0.5 font-sans">
      {data.map((n) => (
        <Node key={n.key} node={n} depth={0} activeKey={activeKey} onSelect={onSelect} />
      ))}
    </div>
  );
}
