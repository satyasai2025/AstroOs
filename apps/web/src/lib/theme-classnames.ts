"use client";

export function getDarkClass(isDark: boolean, light: string, dark: string) {
  return isDark ? dark : light;
}

// Pre‑computed Tailwind class mappings that use the design‑token system.
// These map the Phalita dashboard's former hard‑coded hexes to the canonical
// CSS‑variable tokens defined in globals.css.

/**
 * Card / surface background
 *  - Light:  var(--bg-surface)  → bg‑white / bg‑gray‑50 equivalents
 *  - Dark:   var(--bg-card)    → bg‑navy‑950 / bg‑charcoal‑900 equivalents
 */
export const cardClass = (isDark: boolean) =>
  isDark
    ? "bg-[var(--bg-card)] border-[var(--border-default)]"
    : "bg-[var(--bg-surface)] border-[var(--border-default)]";

/**
 * Panel / overview banner background
 *  - Light:  bg‑white
 *  - Dark:   bg‑navy‑950 (more readable than raw #0b1424)
 */
export const panelClass = (isDark: boolean) =>
  isDark ? "bg-[var(--bg-card)]" : "bg-white";

/**
 * Text on dark card – use the primary text token for maximum contrast.
 *  - Light:  var(--text-primary)
 *  - Dark:   var(--text-primary) (also high‑contrast)
 */
export const darkCardTextClass = (isDark: boolean) =>
  isDark ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)]";

/**
 * Border color used on cards/panels
 */
export const borderClass = (isDark: boolean) =>
  isDark ? "border-[var(--border-default)]" : "border-slate-200";

/**
 * Button backgrounds – use token‑based backgrounds.
 */
export const buttonBackground = (
  isDark: boolean,
  darkBg: string,
  lightBg: string
) => `bg-${isDark ? darkBg : lightBg}`;

/**
 * Ink / hover state for buttons
 */
export const buttonHover = (isDark: boolean, hoverDark: string, hoverLight: string) =>
  `hover:bg-${isDark ? hoverDark : hoverLight}`;