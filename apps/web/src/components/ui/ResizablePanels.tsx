"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

interface ResizablePanelsProps {
  /** One entry per panel; length must stay fixed for the component's lifetime. */
  children: ReactNode[];
  /** Initial width of each panel as a fraction of the row, must sum to 1. */
  defaultSizes?: number[];
  /** Minimum width fraction any single panel can be dragged down to. */
  minSize?: number;
  className?: string;
}

/**
 * Horizontal row of panels separated by draggable dividers, stacking to a
 * single column below md. Sizes are fractions (0..1) of the row width and
 * persist only for the component instance's lifetime.
 */
export function ResizablePanels({
  children,
  defaultSizes,
  minSize = 0.15,
  className,
}: ResizablePanelsProps) {
  const count = children.length;
  const [sizes, setSizes] = useState<number[]>(
    () => defaultSizes ?? Array.from({ length: count }, () => 1 / count),
  );
  const containerRef = useRef<HTMLDivElement>(null);
  const dragState = useRef<{ index: number; startX: number; startSizes: number[] } | null>(null);

  const onPointerMove = useCallback((e: PointerEvent) => {
    const drag = dragState.current;
    const container = containerRef.current;
    if (!drag || !container) return;
    const deltaFraction = (e.clientX - drag.startX) / container.getBoundingClientRect().width;
    const left = drag.index;
    const right = drag.index + 1;
    let move = deltaFraction;
    move = Math.max(move, minSize - drag.startSizes[left]);
    move = Math.min(move, drag.startSizes[right] - minSize);
    const next = [...drag.startSizes];
    next[left] = drag.startSizes[left] + move;
    next[right] = drag.startSizes[right] - move;
    setSizes(next);
  }, [minSize]);

  const endDrag = useCallback(() => {
    dragState.current = null;
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", endDrag);
  }, [onPointerMove]);

  const startDrag = (index: number) => (e: React.PointerEvent) => {
    e.preventDefault();
    dragState.current = { index, startX: e.clientX, startSizes: sizes };
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
          aria-orientation="vertical"
          className="hidden shrink-0 cursor-col-resize md:flex md:items-stretch"
          style={{ width: 9 }}
        >
          <div
            className="mx-auto h-full w-px transition-colors hover:bg-[var(--accent)] active:bg-[var(--accent)]"
            style={{ backgroundColor: "var(--border-primary)" }}
          />
        </div>,
      );
    }
    items.push(
      <div key={i} className="min-w-0 flex-1 md:flex-none" style={{ flexBasis: `${sizes[i] * 100}%` }}>
        {child}
      </div>,
    );
  });

  return (
    <div ref={containerRef} className={`flex flex-col md:flex-row ${className ?? ""}`}>
      {items}
    </div>
  );
}
