"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";

export default function SecuritySettingsPage() {
  return (
    <SettingsLayout title="Security" description="Manage your password and authentication settings">
      <div className="space-y-6">
        {/* Password Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Password
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Change your account password
          </p>

          <div className="space-y-4 max-w-md">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Current Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                New Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Confirm New Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              />
            </div>
          </div>

          <div className="mt-6">
            <button className="rounded-lg px-4 py-2 text-sm font-semibold" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
              Change Password
            </button>
          </div>
        </div>

        {/* Two Factor Authentication */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
                Two Factor Authentication
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Add an extra layer of security to your account
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium" style={{ color: "var(--status-danger)" }}>OFF</span>
              <button className="rounded-lg px-4 py-2 text-sm font-medium transition-colors" style={{ backgroundColor: "var(--obsidian-surface-elevated)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                Enable
              </button>
            </div>
          </div>
        </div>

        {/* Active Sessions */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-6 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Active Sessions
          </h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border p-4" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-primary-soft)", color: "var(--accent)" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                    <line x1="8" y1="21" x2="16" y2="21" />
                    <line x1="12" y1="17" x2="12" y2="21" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Windows</p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>Chrome • Pune</p>
                </div>
              </div>
              <button className="rounded-lg px-3 py-1.5 text-xs font-medium" style={{ backgroundColor: "var(--bg-card)", color: "var(--status-danger)", border: "1px solid var(--border-primary)" }}>
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </SettingsLayout>
  );
}