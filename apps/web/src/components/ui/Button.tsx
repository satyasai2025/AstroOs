"use client";

import Link from "next/link";
import type { AnchorHTMLAttributes, ButtonHTMLAttributes, CSSProperties, MouseEvent, ReactNode } from "react";

type ButtonVariant = "primary" | "gold" | "violet" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

const SIZE: Record<ButtonSize, { padding: string; fontSize: string; gap: number; height: number }> = {
  sm: { padding: "6px 12px", fontSize: "var(--text-sm)", gap: 6, height: 32 },
  md: { padding: "9px 16px", fontSize: "var(--text-base)", gap: 8, height: 40 },
  lg: { padding: "12px 20px", fontSize: "var(--text-md)", gap: 8, height: 48 },
};

const VARIANT: Record<ButtonVariant, CSSProperties> = {
  primary: {
    background: "var(--cyan-400)",
    color: "#020617",
    border: "1px solid transparent",
    boxShadow: "none",
  },

  gold: {
    background: "var(--gold-400)",
    color: "#1c1305",
    border: "1px solid transparent",
    boxShadow: "none",
  },
  violet: {
    background: "var(--violet-400)",
    color: "#160c2e",
    border: "1px solid transparent",
    boxShadow: "none",
  },
  secondary: {
    background: "var(--surface-glass-strong)",
    color: "var(--text-primary)",
    border: "1px solid var(--border-default)",
    boxShadow: "none",
  },
  ghost: {
    background: "transparent",
    color: "var(--text-secondary)",
    border: "1px solid transparent",
    boxShadow: "none",
  },
  danger: {
    background: "rgba(244,63,94,0.12)",
    color: "var(--danger-400)",
    border: "1px solid rgba(244,63,94,0.35)",
    boxShadow: "none",
  },
};

function buttonStyle(
  variant: ButtonVariant,
  size: ButtonSize,
  disabled: boolean | undefined,
  fullWidth: boolean | undefined,
  style: CSSProperties | undefined,
): CSSProperties {
  const v = VARIANT[variant] || VARIANT.primary;
  const s = SIZE[size] || SIZE.md;
  return {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: s.gap,
    padding: s.padding,
    height: s.height,
    fontFamily: "var(--font-body)",
    fontSize: s.fontSize,
    fontWeight: "var(--weight-semibold)",
    borderRadius: "var(--radius-md)",
    cursor: disabled ? "not-allowed" : "pointer",
    width: fullWidth ? "100%" : undefined,
    opacity: disabled ? 0.45 : 1,
    transition: "transform var(--duration-fast) var(--ease-out), filter var(--duration-fast) var(--ease-out)",
    whiteSpace: "nowrap",
    textDecoration: "none",
    ...v,
    ...style,
  };
}

function hoverHandlers(disabled: boolean | undefined) {
  return {
    onMouseEnter: (e: MouseEvent<HTMLElement>) => {
      if (!disabled) e.currentTarget.style.filter = "brightness(1.08)";
    },
    onMouseLeave: (e: MouseEvent<HTMLElement>) => {
      e.currentTarget.style.filter = "none";
    },
  };
}

interface CommonProps {
  children?: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  iconRight?: ReactNode;
  fullWidth?: boolean;
  disabled?: boolean;
}

interface ButtonAsButtonProps extends CommonProps, Omit<ButtonHTMLAttributes<HTMLButtonElement>, "size" | keyof CommonProps> {
  href?: undefined;
}

interface ButtonAsLinkProps extends CommonProps, Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "size" | keyof CommonProps> {
  href: string;
}

type ButtonProps = ButtonAsButtonProps | ButtonAsLinkProps;

export function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  iconRight,
  disabled,
  fullWidth,
  style,
  href,
  ...rest
}: ButtonProps) {
  const computedStyle = buttonStyle(variant, size, disabled, fullWidth, style);

  if (href) {
    return (
      <Link href={href} style={computedStyle} {...hoverHandlers(disabled)} {...(rest as AnchorHTMLAttributes<HTMLAnchorElement>)}>
        {icon}
        {children}
        {iconRight}
      </Link>
    );
  }

  const { onClick, ...buttonRest } = rest as ButtonHTMLAttributes<HTMLButtonElement>;
  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      style={computedStyle}
      {...hoverHandlers(disabled)}
      {...buttonRest}
    >
      {icon}
      {children}
      {iconRight}
    </button>
  );
}
