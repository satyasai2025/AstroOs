/**
 * AstroOS — Admin Stats Bar
 *
 * Top-level KPI row showing system overview metrics.
 */

"use client";

interface StatsBarProps {
  stats: {
    totalUsers: number;
    activeUsers: number;
    totalCharts: number;
    apiCallsToday: number;
    systemUptime: string;
    activePlugins: number;
  };
}

export function AdminStatsBar({ stats }: StatsBarProps) {
  const kpis = [
    {
      label: "Total Admin Users",
      value: stats.totalUsers,
      subtitle: `${stats.activeUsers} active`,
      color: "from-[rgba(139,92,246,0.2)] to-[rgba(139,92,246,0.1)]",
      border: "border-[rgba(139,92,246,0.3)]",
    },
    {
      label: "Active Sessions",
      value: stats.activeUsers,
      subtitle: "Currently online",
      color: "from-[rgba(6,207,255,0.2)] to-[rgba(6,207,255,0.1)]",
      border: "border-[rgba(6,207,255,0.3)]",
    },
    {
      label: "API Calls Today",
      value: stats.apiCallsToday,
      subtitle: "Last 24h",
      color: "from-[rgba(34,197,94,0.2)] to-[rgba(34,197,94,0.1)]",
      border: "border-[rgba(34,197,94,0.3)]",
    },
    {
      label: "System Uptime",
      value: stats.systemUptime,
      subtitle: "Operational",
      color: "from-[rgba(245,166,35,0.2)] to-[rgba(245,166,35,0.1)]",
      border: "border-[rgba(245,166,35,0.3)]",
    },
    {
      label: "Active Plugins",
      value: stats.activePlugins,
      subtitle: "Installed & running",
      color: "from-[rgba(239,68,68,0.2)] to-[rgba(239,68,68,0.1)]",
      border: "border-[rgba(239,68,68,0.3)]",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      {kpis.map((kpi) => (
        <div
          key={kpi.label}
          className={`rounded-lg border ${kpi.border} bg-gradient-to-br ${kpi.color} p-4`}
        >
          <div className="mb-2 text-sm text-[var(--text-muted)] font-medium uppercase tracking-wide">
            {kpi.label}
          </div>
          <div className="text-3xl font-bold text-[var(--text-primary)]">
            {typeof kpi.value === "number" ? kpi.value.toLocaleString() : kpi.value}
          </div>
          <div className="mt-1 text-xs text-[var(--text-secondary)]">{kpi.subtitle}</div>
        </div>
      ))}
    </div>
  );
}
