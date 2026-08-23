"use client";

import React, { useState, useRef, useEffect } from "react";

interface ResizableSplitPaneProps {
  direction?: "horizontal" | "vertical";
  initialRatio?: number; // 0.1 to 0.9 (default 0.5)
  minRatio?: number;
  maxRatio?: number;
  storageKey?: string;
  className?: string;
  firstChild: React.ReactNode;
  secondChild: React.ReactNode;
}

export function ResizableSplitPane({
  direction = "horizontal",
  initialRatio = 0.5,
  minRatio = 0.2,
  maxRatio = 0.8,
  storageKey,
  className = "",
  firstChild,
  secondChild,
}: ResizableSplitPaneProps) {
  const [ratio, setRatio] = useState(() => {
    if (typeof window === "undefined" || !storageKey) return initialRatio;
    try {
      const stored = localStorage.getItem(`split-pane:${storageKey}`);
      const parsed = stored ? parseFloat(stored) : initialRatio;
      return isNaN(parsed) ? initialRatio : Math.max(minRatio, Math.min(maxRatio, parsed));
    } catch {
      return initialRatio;
    }
  });

  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setIsDragging(true);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    let newRatio = initialRatio;

    if (direction === "horizontal") {
      newRatio = (e.clientX - rect.left) / rect.width;
    } else {
      newRatio = (e.clientY - rect.top) / rect.height;
    }

    if (newRatio >= minRatio && newRatio <= maxRatio) {
      setRatio(newRatio);
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
        if (storageKey) {
          localStorage.setItem(`split-pane:${storageKey}`, String(ratio));
        }
      } catch (err) {}
    }
  };

  const firstPercent = `${ratio * 100}%`;
  const secondPercent = `${(1 - ratio) * 100}%`;

  return (
    <div
      ref={containerRef}
      className={`relative w-full flex ${
        direction === "horizontal" ? "flex-row items-stretch" : "flex-col"
      } ${className} select-none`}
    >
      {/* FIRST CARD (Left or Top) */}
      <div
        style={{
          [direction === "horizontal" ? "width" : "height"]: firstPercent,
        }}
        className="flex-none min-w-0 min-h-0 transition-none"
      >
        {firstChild}
      </div>

      {/* ── DRAG HANDLE DIVIDER ── */}
      <div
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onDoubleClick={() => {
          setRatio(initialRatio);
          if (storageKey) localStorage.setItem(`split-pane:${storageKey}`, String(initialRatio));
        }}
        className={`relative z-20 flex-none flex items-center justify-center transition-colors ${
          direction === "horizontal"
            ? "w-2 cursor-col-resize hover:bg-cyan-500/50"
            : "h-2 cursor-row-resize hover:bg-amber-500/50"
        } ${
          isDragging
            ? direction === "horizontal"
              ? "bg-cyan-400 shadow-[0_0_12px_#06b6d4]"
              : "bg-amber-400 shadow-[0_0_12px_#f59e0b]"
            : "bg-slate-200/50 dark:bg-slate-800/60"
        }`}
        title={`Drag to resize ${direction === "horizontal" ? "left vs right" : "top vs bottom"} panels (Double-click to reset)`}
      >
        <div
          className={`rounded-full bg-slate-400/60 ${
            direction === "horizontal" ? "w-0.5 h-6" : "h-0.5 w-6"
          }`}
        />
      </div>

      {/* SECOND CARD (Right or Bottom) */}
      <div
        style={{
          [direction === "horizontal" ? "width" : "height"]: secondPercent,
        }}
        className="flex-1 min-w-0 min-h-0 transition-none"
      >
        {secondChild}
      </div>
    </div>
  );
}
