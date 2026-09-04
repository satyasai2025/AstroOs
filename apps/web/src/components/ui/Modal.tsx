"use client";

import type { ReactNode } from "react";

interface ModalProps {
  open: boolean;
  title?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  onClose?: () => void;
  width?: number;
}

export function Modal({ open, title, children, footer, onClose, width = 520 }: ModalProps) {
  if (!open) return null;
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(15,23,42,0.65)",
        backdropFilter: "blur(8px)",
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width,
          maxWidth: "92vw",
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "var(--bg-card, #ffffff)",
          borderColor: "var(--border-primary, #e2e8f0)",
          borderWidth: "1px",
          borderStyle: "solid",
          borderRadius: "1rem",
          boxShadow: "0 20px 25px -5px rgba(0,0,0,0.2), 0 8px 10px -6px rgba(0,0,0,0.1)",
        }}
        className="text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-2xl transition-colors"
      >
        {/* Fixed header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex-shrink-0">
          <span className="text-base font-extrabold tracking-wide text-slate-900 dark:text-slate-100">
            {title}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 text-base font-bold p-1 rounded transition cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Scrollable body */}
        <div className="p-4 overflow-y-auto flex-1 text-xs text-slate-800 dark:text-slate-200 leading-relaxed custom-scrollbar">
          {children}
        </div>

        {/* Pinned footer */}
        {footer && (
          <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-200 dark:border-slate-800 flex-shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

