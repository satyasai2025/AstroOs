"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";

export default function DataSettingsPage() {
  return (
    <SettingsLayout title="Data" description="Manage your charts, research data, and settings">
      <div className="space-y-6">
        {/* Export Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Export
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Download your data from AstroOS
          </p>

          <div className="space-y-3">
            <button className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--border-hover)]" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Charts</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Export all your birth charts</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </button>

            <button className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--border-hover)]" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Research</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Export research projects and datasets</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </button>

            <button className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--border-hover)]" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Settings</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Export your preferences and settings</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </button>
          </div>
        </div>

        {/* Import Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Import
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Restore data from a backup file
          </p>

          <div className="space-y-3">
            <button className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--border-hover)]" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Charts</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Import charts from JSON backup</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </button>

            <button className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--border-hover)]" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}>
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Settings</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Import settings from JSON backup</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </button>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--status-danger)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--status-danger)" }}>
            Danger Zone
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Irreversible actions that affect your data
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button className="flex-1 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors hover:border-[var(--status-danger)] hover:text-[var(--status-danger)]" style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)", backgroundColor: "var(--bg-input)" }}>
              Clear Cache
            </button>
            <button className="flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors hover:brightness-110" style={{ backgroundColor: "var(--status-danger)", color: "var(--accent-text)" }}>
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </SettingsLayout>
  );
}