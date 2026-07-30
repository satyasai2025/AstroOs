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
          maxHeight: "86vh",
          overflowY: "auto",
          background: "linear-gradient(180deg, var(--bg-surface-800), var(--bg-surface-700))",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-xl)",
          boxShadow: "var(--shadow-xl)",
          padding: "var(--space-3)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-2)" }}>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "var(--text-xl)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>
            {title}
          </span>
          <span onClick={onClose} style={{ cursor: "pointer", color: "var(--text-tertiary)", fontSize: 18, lineHeight: 1, padding: 4 }}>
            ✕
          </span>
        </div>
        <div style={{ color: "var(--text-secondary)", fontSize: "var(--text-base)" }}>{children}</div>
        {footer && <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: "var(--space-3)" }}>{footer}</div>}
      </div>
    </div>
  );
}
