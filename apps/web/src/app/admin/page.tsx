"use client";

import { useSystemStatus, useModuleRegistry } from "@/lib/admin";
import { ApiError } from "@/lib/api";

function StatusDot({ status }: { status: string }) {
  const color =
    status === "healthy" || status === "ok" || status === "up"
      ? "bg-emerald-400"
      : status === "degraded"
        ? "bg-amber-400"
        : "bg-red-400";
  return <span className={`inline-block h-2 w-2 rounded-full ${color}`} aria-hidden="true" />;
}

export default function AdminOverviewPage() {
  const statusQuery = useSystemStatus();
  const modulesQuery = useModuleRegistry();

  const errorMessage = (err: unknown) =>
    err instanceof ApiError ? err.detail : "Failed to load.";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">System Overview</h1>
        <p className="mt-1 text-sm text-slate-500">
          Live health of backend modules and the ephemeris engine.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
          System Status
        </h2>

        {statusQuery.isLoading && <p className="text-sm text-slate-500">Loading…</p>}
        {statusQuery.isError && (
          <p className="text-sm text-red-400" role="alert">
            {errorMessage(statusQuery.error)}
          </p>
        )}

        {statusQuery.data && (
          <div className="rounded-lg border border-slate-800 bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
              <div className="flex items-center gap-2">
                <StatusDot status={statusQuery.data.status} />
                <span className="text-sm font-medium text-slate-200">
                  {statusQuery.data.status.toUpperCase()}
                </span>
              </div>
              <div className="text-xs text-slate-500">
                v{statusQuery.data.version} · ephemeris: {statusQuery.data.ephemeris_mode}
              </div>
            </div>

            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-600">
                  <th className="px-4 py-2 font-medium">Module</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Version</th>
                  <th className="px-4 py-2 font-medium">Message</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(statusQuery.data.modules).map(([name, m]) => (
                  <tr key={name} className="border-t border-slate-800/60">
                    <td className="px-4 py-2 text-slate-300">{m.module_name || name}</td>
                    <td className="px-4 py-2">
                      <span className="inline-flex items-center gap-1.5 text-slate-300">
                        <StatusDot status={m.status} />
                        {m.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-500">{m.version}</td>
                    <td className="px-4 py-2 text-slate-500">{m.message || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
          Registered Modules
        </h2>

        {modulesQuery.isLoading && <p className="text-sm text-slate-500">Loading…</p>}
        {modulesQuery.isError && (
          <p className="text-sm text-red-400" role="alert">
            {errorMessage(modulesQuery.error)}
          </p>
        )}

        {modulesQuery.data && (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {Object.entries(modulesQuery.data.modules).map(([name, version]) => (
              <div
                key={name}
                className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2"
              >
                <p className="truncate text-sm text-slate-300">{name}</p>
                <p className="text-xs text-slate-500">{version}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
