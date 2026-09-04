"use client";

import { useAdminCurrentUser } from "@/lib/adminAuth";
import { Card } from "@/components/ui";

export default function AdminProfilePage() {
  const { data: adminUser } = useAdminCurrentUser();

  return (
    <div className="space-y-6 max-w-3xl">
      {/* ── Header ── */}
      <div>
        <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-0.5 text-xs font-semibold text-indigo-400">
          <span>👤</span>
          <span>Administrator Profile</span>
        </div>
        <h1 className="text-2xl font-extrabold text-white mt-2">
          Admin Profile &amp; Credentials
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Active system administrator account details and privilege levels.
        </p>
      </div>

      <Card className="p-6 border border-slate-800 bg-slate-900/60 space-y-4">
        <div className="flex items-center gap-4 border-b border-slate-800 pb-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600 font-bold text-white text-xl shadow">
            AD
          </div>
          <div>
            <h2 className="text-base font-bold text-white">
              {adminUser?.display_name || "System Administrator"}
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              {adminUser?.email || "admin@astroos.dev"}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-1">
            <span className="text-slate-500 font-semibold">Assigned Role</span>
            <div className="font-bold text-indigo-400 uppercase">
              {adminUser?.role || "SUPER_ADMIN"}
            </div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-1">
            <span className="text-slate-500 font-semibold">Status</span>
            <div className="font-bold text-emerald-400">Active &amp; Verified</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
