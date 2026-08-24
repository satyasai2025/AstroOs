"use client";

import { useMemo, useState } from "react";
import { Select, type SelectOption } from "@/components/ui";
import {
  useEventCategoryTree,
  useEventTypeTree,
  type EventCategoryNode,
  type EventTypeNode,
} from "@/lib/research";

type TreeNodeShape = { id: string; name: string; children: TreeNodeShape[] };

const MAX_LEVELS = 6;

export interface TreeLevelBuilderProps {
  tree: "category" | "event";
  value: string[] | null;
  onChange: (path: string[] | null) => void;
}

/**
 * Dropdown-driven path builder for the open category/event trees, up to 6
 * levels deep. Each level's dropdown is populated with that level's real
 * children under whatever was picked one level up (cascading); typing a
 * new value not yet in the tree is also allowed (open vocabulary — the
 * backend auto-creates it on save, same as before). Replaces the old
 * single free-text search box (CategoryPathPicker) per the reference
 * screenshot's numbered-level layout.
 */
export function TreeLevelBuilder({ tree, value, onChange }: TreeLevelBuilderProps) {
  const categoryTree = useEventCategoryTree();
  const eventTree = useEventTypeTree();
  const rootNodes: TreeNodeShape[] = (tree === "category"
    ? categoryTree.data?.categories
    : eventTree.data?.event_types) as (EventCategoryNode[] | EventTypeNode[] | undefined) as TreeNodeShape[] ?? [];

  const [levels, setLevels] = useState<string[]>(value && value.length > 0 ? value : [""]);
  const [customAt, setCustomAt] = useState<Set<number>>(new Set());

  const childrenAtLevel = useMemo(() => {
    const result: TreeNodeShape[][] = [];
    let currentChildren = rootNodes;
    for (let i = 0; i < levels.length; i++) {
      result.push(currentChildren);
      const picked = currentChildren.find((n) => n.name === levels[i]);
      currentChildren = picked ? picked.children : [];
    }
    return result;
  }, [rootNodes, levels]);

  const commit = (nextLevels: string[]) => {
    const cleaned = nextLevels.map((l) => l.trim()).filter(Boolean);
    setLevels(nextLevels);
    onChange(cleaned.length > 0 ? cleaned : null);
  };

  const setLevelValue = (idx: number, val: string) => {
    const next = [...levels];
    next[idx] = val;
    // Changing an ancestor level invalidates descendant selections.
    next.length = idx + 1;
    // Auto-reveal the next level once this one is picked, so the
    // dropdown chain cascades without an extra "+ Add level" click —
    // matches the always-visible multi-level grid in the reference UI.
    if (val.trim() && next.length < MAX_LEVELS) {
      next.push("");
    }
    commit(next);
  };

  const addLevel = () => {
    if (levels.length >= MAX_LEVELS) return;
    commit([...levels, ""]);
  };

  const removeLevel = (idx: number) => {
    const next = levels.slice(0, idx);
    commit(next.length > 0 ? next : [""]);
    setCustomAt((prev) => {
      const copy = new Set(prev);
      copy.delete(idx);
      return copy;
    });
  };

  const toggleCustom = (idx: number) => {
    setCustomAt((prev) => {
      const copy = new Set(prev);
      if (copy.has(idx)) copy.delete(idx);
      else copy.add(idx);
      return copy;
    });
  };

  return (
    <div className="flex flex-col gap-2">
      {levels.map((levelValue, idx) => {
        const options: SelectOption[] = childrenAtLevel[idx]?.map((n) => ({ value: n.name, label: n.name })) ?? [];
        const isCustom = customAt.has(idx) || (options.length === 0 && idx === 0 && rootNodes.length === 0);
        return (
          <div key={idx} className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500 dark:text-slate-400 w-14 shrink-0">
              Level {idx + 1}
            </span>
            {isCustom ? (
              <input
                value={levelValue}
                onChange={(e) => setLevelValue(idx, e.target.value)}
                placeholder="Type a new value…"
                className="flex-1 h-9 px-2.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-cyan-500"
              />
            ) : (
              <div className="flex-1">
                <Select
                  options={options}
                  value={levelValue || undefined}
                  onChange={(v) => setLevelValue(idx, v)}
                  placeholder={`Select level ${idx + 1}…`}
                />
              </div>
            )}
            <button
              type="button"
              onClick={() => toggleCustom(idx)}
              className="text-[11px] text-cyan-600 dark:text-cyan-400 shrink-0"
            >
              {isCustom ? "Pick" : "+ New"}
            </button>
            {levels.length > 1 && (
              <button
                type="button"
                onClick={() => removeLevel(idx)}
                className="text-slate-400 hover:text-red-500 text-xs shrink-0"
                aria-label={`Remove level ${idx + 1}`}
              >
                ✕
              </button>
            )}
          </div>
        );
      })}

      {levels.length < MAX_LEVELS && (
        <button
          type="button"
          onClick={addLevel}
          className="self-start text-xs font-medium text-cyan-600 dark:text-cyan-400"
        >
          + Add {tree === "category" ? "Sub-category" : "Sub-event"} level
        </button>
      )}
    </div>
  );
}
