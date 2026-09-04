"use client";

type ToastTone = "success" | "error" | "info" | "warning";

const TONE: Record<ToastTone, { icon: string; color: string }> = {
  success: { icon: "✓", color: "var(--success-400)" },
  error: { icon: "✕", color: "var(--danger-400)" },
  info: { icon: "i", color: "var(--cyan-400)" },
  warning: { icon: "!", color: "var(--gold-400)" },
};

interface ToastProps {
  tone?: ToastTone;
  title: string;
  description?: string;
  onClose?: () => void;
}

export function Toast({ tone = "info", title, description, onClose }: ToastProps) {
  const t = TONE[tone] || TONE.info;
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
        width: 340,
        padding: "14px 16px",
        background: "var(--bg-surface-700)",
        border: "1px solid var(--border-default)",
        borderRadius: "var(--radius-lg)",
        boxShadow: "var(--shadow-lg)",
        backdropFilter: "var(--blur-glass)",
      }}
    >
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: "50%",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: `${t.color}22`,
          color: t.color,
          fontSize: 13,
          fontWeight: 700,
        }}
      >
        {t.icon}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: "var(--text-base)", fontWeight: "var(--weight-semibold)", color: "var(--text-primary)" }}>{title}</div>
        {description && <div style={{ fontSize: "var(--text-sm)", color: "var(--text-secondary)", marginTop: 2 }}>{description}</div>}
      </div>
      <span onClick={onClose} style={{ cursor: "pointer", color: "var(--text-tertiary)", fontSize: 14 }}>
        ✕
      </span>
    </div>
  );
}
