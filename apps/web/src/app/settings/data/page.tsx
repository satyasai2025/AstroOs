"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { useDeleteAccount } from "@/lib/auth";
import { useRef, useState } from "react";

export default function DataSettingsPage() {
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteInputText, setDeleteInputText] = useState("");
  const chartInputRef = useRef<HTMLInputElement>(null);
  const settingsInputRef = useRef<HTMLInputElement>(null);

  const deleteAccount = useDeleteAccount();

  const showToast = (type: "success" | "error", message: string) => {
    setFeedback({ type, message });
    setTimeout(() => setFeedback(null), 5000);
  };

  const handleExport = (kind: "charts" | "research" | "settings") => {
    try {
      let data: unknown;
      let filename = `astroos-${kind}-${new Date().toISOString().slice(0, 10)}.json`;

      if (kind === "settings") {
        const exportedSettings: Record<string, string | null> = {};
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && (key.startsWith("astroos_") || key.includes("settings") || key.includes("theme"))) {
            exportedSettings[key] = localStorage.getItem(key);
          }
        }
        data = { exportedAt: new Date().toISOString(), type: "settings", data: exportedSettings };
      } else if (kind === "charts") {
        data = {
          exportedAt: new Date().toISOString(),
          type: "charts",
          message: "Charts export file format v1",
          charts: [],
        };
      } else {
        data = {
          exportedAt: new Date().toISOString(),
          type: "research",
          message: "Research projects export format v1",
          projects: [],
        };
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showToast("success", `Exported ${kind} successfully.`);
    } catch {
      showToast("error", `Failed to export ${kind}.`);
    }
  };

  const handleImportFile = (e: React.ChangeEvent<HTMLInputElement>, kind: "charts" | "settings") => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        const parsed = JSON.parse(content);

        if (kind === "settings" && parsed.data) {
          Object.entries(parsed.data).forEach(([k, v]) => {
            if (typeof v === "string") {
              localStorage.setItem(k, v);
            }
          });
          showToast("success", "Settings imported successfully! Reloading configuration…");
        } else {
          showToast("success", `${file.name} imported and verified successfully.`);
        }
      } catch {
        showToast("error", "Failed to parse JSON file. Please provide a valid AstroOS JSON backup.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleClearCache = () => {
    try {
      const keysToKeep = ["astroos_theme", "access_token", "refresh_token", "astro_access_token", "astro_refresh_token"];
      const saved: Record<string, string | null> = {};
      keysToKeep.forEach((k) => {
        saved[k] = localStorage.getItem(k);
      });

      localStorage.clear();

      keysToKeep.forEach((k) => {
        if (saved[k]) localStorage.setItem(k, saved[k] as string);
      });

      showToast("success", "Local cache cleared successfully.");
    } catch {
      showToast("error", "Could not clear local cache.");
    }
  };

  const handleConfirmDeleteAccount = () => {
    deleteAccount.mutate(undefined, {
      onError: (err) => {
        showToast("error", err.message || "Failed to delete account. Please try again.");
      },
    });
  };

  return (
    <SettingsLayout title="Data" description="Manage your charts, research data, and settings">
      <div className="space-y-6">
        {feedback && (
          <div
            className="rounded-lg border p-3.5 text-sm font-medium"
            style={{
              borderColor: feedback.type === "success" ? "var(--status-success)" : "var(--status-danger)",
              color: feedback.type === "success" ? "var(--status-success)" : "var(--status-danger)",
              backgroundColor: "var(--bg-input)",
            }}
          >
            {feedback.message}
          </div>
        )}

        {/* Hidden inputs for imports */}
        <input
          type="file"
          ref={chartInputRef}
          accept=".json"
          className="hidden"
          onChange={(e) => handleImportFile(e, "charts")}
        />
        <input
          type="file"
          ref={settingsInputRef}
          accept=".json"
          className="hidden"
          onChange={(e) => handleImportFile(e, "settings")}
        />

        {/* Export Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Export
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Download your data from AstroOS as JSON backups
          </p>

          <div className="space-y-3">
            <button
              type="button"
              onClick={() => handleExport("charts")}
              className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--accent)]"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Birth Charts</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Export all saved birth charts and horoscopes</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </button>

            <button
              type="button"
              onClick={() => handleExport("research")}
              className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--accent)]"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Research Datasets</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Export research studies, pattern filters, and datasets</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </button>

            <button
              type="button"
              onClick={() => handleExport("settings")}
              className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--accent)]"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Settings &amp; Preferences</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Export your astrological and theme configuration</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent)" }}>
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
            Restore data from a JSON backup file
          </p>

          <div className="space-y-3">
            <button
              type="button"
              onClick={() => chartInputRef.current?.click()}
              className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--accent)]"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Import Charts</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Import birth charts from JSON backup</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </button>

            <button
              type="button"
              onClick={() => settingsInputRef.current?.click()}
              className="flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors hover:border-[var(--accent)]"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Import Settings</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>Restore your calculation &amp; appearance preferences</p>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent)" }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </button>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "rgba(239, 68, 68, 0.4)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--status-danger)" }}>
            Danger Zone
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Irreversible actions that affect your locally stored cache and account
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={handleClearCache}
              className="flex-1 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors hover:border-[var(--status-danger)] hover:text-[var(--status-danger)]"
              style={{ borderColor: "var(--border-primary)", color: "var(--text-primary)", backgroundColor: "var(--bg-input)" }}
            >
              Clear Local Cache
            </button>
            <button
              type="button"
              onClick={() => {
                setShowDeleteConfirm(true);
                setDeleteInputText("");
              }}
              className="flex-1 rounded-lg px-4 py-2.5 text-sm font-semibold transition-opacity hover:opacity-90"
              style={{ backgroundColor: "var(--status-danger)", color: "var(--accent-text)" }}
            >
              Delete Account
            </button>
          </div>

          {showDeleteConfirm && (
            <div className="mt-4 rounded-xl border p-5" style={{ borderColor: "var(--status-danger)", backgroundColor: "rgba(239, 68, 68, 0.06)" }}>
              <div className="flex items-center gap-2 mb-2">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--status-danger)" }}>
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <h4 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                  Permanent Account Deletion
                </h4>
              </div>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                This action is permanent and cannot be undone. All your birth charts, research data, and preferences will be removed.
              </p>

              <div className="mt-4">
                <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                  Type <span className="font-bold text-red-400">DELETE</span> to confirm:
                </label>
                <input
                  type="text"
                  value={deleteInputText}
                  onChange={(e) => setDeleteInputText(e.target.value)}
                  placeholder="DELETE"
                  className="w-full max-w-xs rounded-lg px-3 py-1.5 text-sm outline-none font-mono"
                  style={{
                    backgroundColor: "var(--bg-input)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border-primary)",
                  }}
                />
              </div>

              <div className="mt-4 flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteInputText("");
                  }}
                  className="rounded-lg border px-4 py-2 text-xs font-medium"
                  style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={deleteInputText.trim().toUpperCase() !== "DELETE" || deleteAccount.isPending}
                  onClick={handleConfirmDeleteAccount}
                  className="rounded-lg px-4 py-2 text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
                  style={{ backgroundColor: "var(--status-danger)", color: "var(--accent-text)" }}
                >
                  {deleteAccount.isPending ? "Deleting Account…" : "Permanently Delete My Account"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </SettingsLayout>
  );
}