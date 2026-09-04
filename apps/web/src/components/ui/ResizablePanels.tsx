"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

interface ResizablePanelsProps {
  /** One entry per panel; length must stay fixed for the component's lifetime. */
  children: ReactNode[];
  /** Initial width/height fraction of each panel as a fraction (0..1), must sum to 1. */
  defaultSizes?: number[];
  /** Minimum width/height fraction any single panel can be dragged down to. */
  minSize?: number;
  /** Layout direction: 'horizontal' (columns) or 'vertical' (rows). Default: 'horizontal'. */
  direction?: "horizontal" | "vertical";
  className?: string;
}

/**
 * Row or column of panels separated by draggable dividers (split panes).
 * Sizes are fractions (0..1) of container dimension and persist for component instance lifetime.
 */
export function ResizablePanels({
  children,
  defaultSizes,
  minSize = 0.12,
  direction = "horizontal",
  className,
}: ResizablePanelsProps) {
  const count = children.length;
  const [sizes, setSizes] = useState<number[]>(
    () => defaultSizes ?? Array.from({ length: count }, () => 1 / count),
  );
  const containerRef = useRef<HTMLDivElement>(null);
  const dragState = useRef<{ index: number; startPos: number; startSizes: number[] } | null>(null);

  const isHorizontal = direction === "horizontal";

  const onPointerMove = useCallback((e: PointerEvent) => {
    const drag = dragState.current;
    const container = containerRef.current;
    if (!drag || !container) return;
    const rect = container.getBoundingClientRect();
    const totalDim = isHorizontal ? rect.width : rect.height;
    const currentPos = isHorizontal ? e.clientX : e.clientY;
    const deltaFraction = (currentPos - drag.startPos) / totalDim;

    const left = drag.index;
    const right = drag.index + 1;
    let move = deltaFraction;
    move = Math.max(move, minSize - drag.startSizes[left]);
    move = Math.min(move, drag.startSizes[right] - minSize);
    const next = [...drag.startSizes];
    next[left] = drag.startSizes[left] + move;
    next[right] = drag.startSizes[right] - move;
    setSizes(next);
  }, [isHorizontal, minSize]);

  const endDrag = useCallback(() => {
    dragState.current = null;
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", endDrag);
  }, [onPointerMove]);

  const startDrag = (index: number) => (e: React.PointerEvent) => {
    e.preventDefault();
    const pos = isHorizontal ? e.clientX : e.clientY;
    dragState.current = { index, startPos: pos, startSizes: sizes };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", endDrag);
  };

  useEffect(() => () => endDrag(), [endDrag]);

  const items: ReactNode[] = [];
  children.forEach((child, i) => {
    if (i > 0) {
      items.push(
        <div
          key={`divider-${i}`}
          onPointerDown={startDrag(i - 1)}
          role="separator"
          aria-orientation={isHorizontal ? "vertical" : "horizontal"}
          className={`shrink-0 select-none group flex items-center justify-center transition-colors ${
            isHorizontal
              ? "hidden md:flex w-2.5 cursor-col-resize hover:bg-cyan-500/20 active:bg-cyan-500/40"
              : "w-full h-2.5 cursor-row-resize hover:bg-cyan-500/20 active:bg-cyan-500/40"
          }`}
          title="Drag to resize panel split"
        >
          <div
            className={`rounded-full transition-all ${
              isHorizontal
                ? "w-1 h-8 bg-slate-300 dark:bg-slate-700 group-hover:bg-cyan-400 group-active:bg-cyan-400"
                : "h-1 w-12 bg-slate-300 dark:bg-slate-700 group-hover:bg-cyan-400 group-active:bg-cyan-400"
            }`}
          />
        </div>,
      );
    }
    items.push(
      <div
        key={i}
        className="min-w-0 flex-1 md:flex-none"
        style={{ flexBasis: `${sizes[i] * 100}%` }}
      >
        {child}
      </div>,
    );
  });

  return (
    <div
      ref={containerRef}
      className={`flex ${isHorizontal ? "flex-col md:flex-row" : "flex-col"} gap-2 md:gap-0 ${className ?? ""}`}
    >
      {items}
    </div>
  );
}
