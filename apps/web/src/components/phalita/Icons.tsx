'use client';


import React from "react";

export const Icon: React.FC<{ path: string; className?: string; viewBox?: string }> = ({
  path,
  className = "w-4 h-4",
  viewBox = "0 0 24 24",
}) => (
  <svg
    className={className}
    viewBox={viewBox}
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d={path} />
  </svg>
);

export const Compass: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m16.2 7.8-2 6.3-6.4 2 2-6.3z M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z" className={className} />
);

export const Sparkles: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z" className={className} />
);

export const Sun: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 2v2 M12 20v2 M4.93 4.93l1.41 1.41 M17.66 17.66l1.41 1.41 M2 12h2 M20 12h2 M6.34 17.66l-1.41 1.41 M19.07 4.93l-1.41 1.41 M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10z" className={className} />
);

export const Moon: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" className={className} />
);

export const Layers: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.9a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z M2 12l10 4.5 10-4.5 M2 17l10 4.5 10-4.5" className={className} />
);

export const Calendar: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M8 2v4 M16 2v4 M3 10h18 M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" className={className} />
);

export const Clock: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 6v6l4 2 M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z" className={className} />
);

export const Milestone: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M18 6H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h13l4-3.5L18 6Z M12 13v8 M12 3v3" className={className} />
);

export const Cpu: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M4 4h16v16H4z M9 9h6v6H9z M9 1v3 M15 1v3 M9 20v3 M15 20v3 M20 9h3 M20 15h3 M1 9h3 M1 15h3" className={className} />
);

export const Zap: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M13 2 3 14h9l-1 8 10-12h-9l1-8z" className={className} />
);

export const Activity: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M22 12h-4l-3 9L9 3l-3 9H2" className={className} />
);

export const AlertTriangle: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z M12 9v4 M12 17h.01" className={className} />
);

export const AlertCircle: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 8v4 M12 16h.01" className={className} />
);

export const CheckCircle: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M22 11.08V12a10 10 0 1 1-5.93-9.14 M22 4 12 14.01l-3-3" className={className} />
);

export const CheckCircle2: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M9 12l2 2 4-4" className={className} />
);

export const ShieldCheck: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z M9 12l2 2 4-4" className={className} />
);

export const RefreshCw: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8 M21 3v5h-5 M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16 M3 21v-5h5" className={className} />
);

export const MapPin: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z M12 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" className={className} />
);

export const ChevronDown: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m6 9 6 6 6-6" className={className} />
);

export const ChevronUp: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m18 15-6-6-6 6" className={className} />
);

export const User: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2 M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z" className={className} />
);

export const Target: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 16a6 6 0 1 1 6-6 6 6 0 0 1-6 6zm0-8a2 2 0 1 0 2 2 2 2 0 0 0-2-2z" className={className} />
);

export const Globe: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8zm-7-8h14M12 4a14 14 0 0 1 0 16 14 14 0 0 1 0-16z" className={className} />
);

export const Briefcase: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M20 7h-4V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v3H4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zM10 4h4v3h-4V4z" className={className} />
);

export const Award: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 15a7 7 0 1 0 0-14 7 7 0 0 0 0 14zm-4 3 4-2 4 2v4l-4-2-4 2v-4z" className={className} />
);

export const Wallet: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zm-2 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4z M16 7V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3" className={className} />
);

export const Heart: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" className={className} />
);

export const Users: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75" className={className} />
);

export const BarChart3: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M3 3v18h18 M18 17V9 M13 17V5 M8 17v-3" className={className} />
);

export const TrendingUp: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m22 7-8.5 8.5-5-5L1 18 M16 7h6v6" className={className} />
);

export const ChevronRight: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="m9 18 6-6-6-6" className={className} />
);

export const BookOpen: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" className={className} />
);

export const Shield: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" className={className} />
);

export const Lock: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M7 11V7a5 5 0 0 1 10 0v4 M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z" className={className} />
);

export const Database: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M21 5c0 1.66-4 3-9 3s-9-1.34-9-3 4-3 9-3 9 1.34 9 3z M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5 M3 12c0 1.66 4 3 9 3s9-1.34 9-3" className={className} />
);

export const FileText: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8" className={className} />
);

export const Download: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3" className={className} />
);

export const FileSpreadsheet: React.FC<{ className?: string }> = ({ className }) => (
  <Icon path="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M8 13h2 M14 13h2 M8 17h2 M14 17h2" className={className} />
);


