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

export function Modal({ open, title, children, footer, onClose, width = 480 }: ModalProps) {
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
        background: "rgba(5,7,13,0.65)",
        backdropFilter: "blur(6px)",
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
          background: "linear-gradient(180deg, var(--bg-surface-800), var(--bg-surface-700))",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-xl)",
          boxShadow: "var(--shadow-xl)",
        }}
      >
        {/* Fixed header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "var(--space-3)", borderBottom: "1px solid var(--border-subtle)", flexShrink: 0 }}>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "var(--text-xl)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
            {title}
          </span>
          <span onClick={onClose} style={{ cursor: "pointer", color: "var(--text-tertiary)", fontSize: 18, lineHeight: 1, padding: 4, flexShrink: 0 }}>
            ✕
          </span>
        </div>

        {/* Scrollable body */}
        <div style={{ color: "var(--text-secondary)", fontSize: "var(--text-base)", padding: "var(--space-3)", overflowY: "auto", flex: 1 }}>
          {children}
        </div>

        {/* Pinned footer */}
        {footer && (
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, padding: "var(--space-3)", borderTop: "1px solid var(--border-subtle)", flexShrink: 0 }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

