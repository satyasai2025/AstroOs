/**
 * AstroOS — shared icon dictionary.
 *
 * The rest of this codebase hand-duplicates a switch(name) icon renderer in
 * three separate files (AppShell.tsx, NavPanel.tsx, AdminSidebar.tsx), all
 * using the same 24x24 / stroke=currentColor / strokeWidth 1.8 recipe. This
 * is a single shared source for new UI (the Research Patterns shell) so a
 * 4th copy isn't added — existing call sites are left as-is (out of scope
 * to refactor them here).
 */

import type { CSSProperties, ReactNode } from "react";

export type IconName =
  | "dashboard"
  | "database"
  | "calendar"
  | "upload"
  | "clock"
  | "camera"
  | "sparkle"
  | "book"
  | "report"
  | "flask"
  | "gear"
  | "help"
  | "download"
  | "user"
  | "network"
  | "search"
  | "compass";

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
  style?: CSSProperties;
}

const common = {
  width: 16,
  height: 16,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const PATHS: Record<IconName, ReactNode> = {
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </>
  ),
  database: (
    <>
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v6c0 1.66 3.58 3 8 3s8-1.34 8-3V5" />
      <path d="M4 11v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" />
    </>
  ),
  calendar: (
    <>
      <rect x="3" y="4" width="18" height="17" rx="2" />
      <path d="M3 9h18M8 2v4M16 2v4" />
    </>
  ),
  upload: (
    <>
      <path d="M12 16V4M6 10l6-6 6 6" />
      <path d="M4 18v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 2" />
    </>
  ),
  camera: (
    <>
      <path d="M4 8h3l1.5-2h7L17 8h3a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2z" />
      <circle cx="12" cy="14" r="3.5" />
    </>
  ),
  sparkle: (
    <>
      <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z" />
    </>
  ),
  book: (
    <>
      <path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5A2.5 2.5 0 0 0 4 21.5v-17z" />
      <path d="M20 19H6.5A2.5 2.5 0 0 0 4 21.5" />
    </>
  ),
  report: (
    <>
      <path d="M6 2h9l5 5v15H6z" />
      <path d="M15 2v5h5M9 13h6M9 17h6M9 9h2" />
    </>
  ),
  flask: (
    <>
      <path d="M9 2h6M10 2v6l-5.5 9.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-3.5L14 8V2" />
      <path d="M7.5 15h9" />
    </>
  ),
  gear: (
    <>
      <circle cx="12" cy="12" r="3.2" />
      <path d="M12 2.5v3M12 18.5v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2.5 12h3M18.5 12h3M4.9 19.1L7 17M17 7l2.1-2.1" />
    </>
  ),
  help: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9.2a2.5 2.5 0 0 1 4.8 1c0 1.7-2.3 2-2.3 3.6" />
      <path d="M12 17.2h.01" />
    </>
  ),
  download: (
    <>
      <path d="M12 4v12M6 10l6 6 6-6" />
      <path d="M4 18v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="3.5" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </>
  ),
  network: (
    <>
      <circle cx="12" cy="4.5" r="2.2" />
      <circle cx="5" cy="18" r="2.2" />
      <circle cx="19" cy="18" r="2.2" />
      <path d="M12 6.7v6.3M12 13l-5.6 3.4M12 13l5.6 3.4" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="M20 20l-4.5-4.5" />
    </>
  ),
  compass: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M15 9l-2 6-6 2 2-6 6-2z" />
    </>
  ),
};

export function Icon({ name, size = 16, className, style }: IconProps) {
  const path = PATHS[name];
  if (!path) return null;
  return (
    <svg
      {...common}
      width={size}
      height={size}
      className={className}
      style={style}
    >
      {path}
    </svg>
  );
}
