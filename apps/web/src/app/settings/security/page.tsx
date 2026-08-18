"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { useState } from "react";

export default function SecuritySettingsPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [twoFactorMsg, setTwoFactorMsg] = useState<string | null>(null);
  const [sessions, setSessions] = useState([
    { id: "1", device: "Current Session (Windows / Chrome)", location: "Active Now", isCurrent: true },
  ]);

  const handlePasswordChange = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);

    if (!currentPassword) {
      setPasswordMsg({ type: "error", text: "Please enter your current password." });
      return;
    }
    if (!newPassword || newPassword.length < 8) {
      setPasswordMsg({ type: "error", text: "New password must be at least 8 characters long." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: "error", text: "New passwords do not match." });
      return;
    }

    // Success feedback
    setPasswordMsg({ type: "success", text: "Password changed successfully." });
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setTimeout(() => setPasswordMsg(null), 5000);
  };

  const handleToggle2FA = () => {
    const nextState = !twoFactorEnabled;
    setTwoFactorEnabled(nextState);
    setTwoFactorMsg(nextState ? "Two-Factor Authentication has been enabled." : "Two-Factor Authentication disabled.");
    setTimeout(() => setTwoFactorMsg(null), 4000);
  };

  const handleLogoutOtherSessions = () => {
    setSessions([{ id: "1", device: "Current Session (Windows / Chrome)", location: "Active Now", isCurrent: true }]);
    setPasswordMsg({ type: "success", text: "All other sessions have been logged out." });
    setTimeout(() => setPasswordMsg(null), 4000);
  };

  const inputStyle = {
    backgroundColor: "var(--bg-input)",
    color: "var(--text-primary)",
    border: "1px solid var(--border-primary)",
  };

  return (
    <SettingsLayout title="Security" description="Manage your password and authentication settings">
      <div className="space-y-6">
        {/* Password Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Change Password
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Update your account password
          </p>

          <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Current Password
              </label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Confirm New Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              />
            </div>

            {passwordMsg && (
              <div
                className="rounded-lg border p-3 text-xs"
                style={{
                  borderColor: passwordMsg.type === "success" ? "var(--status-success)" : "var(--status-danger)",
                  color: passwordMsg.type === "success" ? "var(--status-success)" : "var(--status-danger)",
                  backgroundColor: "var(--bg-input)",
                }}
              >
                {passwordMsg.text}
              </div>
            )}

            <div className="pt-2">
              <button
                type="submit"
                className="rounded-lg px-4 py-2 text-sm font-semibold transition-opacity hover:opacity-90"
                style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
              >
                Update Password
              </button>
            </div>
          </form>
        </div>

        {/* Two Factor Authentication */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
                Two-Factor Authentication (2FA)
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Add an extra layer of security to your account with authenticator codes
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span
                className="text-xs font-semibold px-2.5 py-1 rounded-full"
                style={{
                  backgroundColor: twoFactorEnabled ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                  color: twoFactorEnabled ? "var(--status-success)" : "var(--status-danger)",
                }}
              >
                {twoFactorEnabled ? "ENABLED" : "DISABLED"}
              </span>
              <button
                type="button"
                onClick={handleToggle2FA}
                className="rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                style={{
                  backgroundColor: twoFactorEnabled ? "var(--obsidian-surface-elevated)" : "var(--accent)",
                  color: twoFactorEnabled ? "var(--text-primary)" : "var(--accent-text)",
                  border: "1px solid var(--border-primary)",
                }}
              >
                {twoFactorEnabled ? "Disable" : "Enable"}
              </button>
            </div>
          </div>
          {twoFactorMsg && (
            <div
              className="mt-4 rounded-lg border p-3 text-xs"
              style={{
                borderColor: "var(--status-success)",
                color: "var(--status-success)",
                backgroundColor: "var(--bg-input)",
              }}
            >
              {twoFactorMsg}
            </div>
          )}
        </div>

        {/* Active Sessions */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
                Active Sessions
              </h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Devices and browsers currently logged into your account
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogoutOtherSessions}
              className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
              style={{
                backgroundColor: "var(--bg-input)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border-primary)",
              }}
            >
              Revoke Others
            </button>
          </div>

          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between rounded-lg border p-4"
                style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-primary-soft)", color: "var(--accent)" }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                      <line x1="8" y1="21" x2="16" y2="21" />
                      <line x1="12" y1="17" x2="12" y2="21" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{session.device}</p>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>{session.location}</p>
                  </div>
                </div>
                <span
                  className="rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                  style={{ backgroundColor: "rgba(16, 185, 129, 0.15)", color: "var(--status-success)" }}
                >
                  Active
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </SettingsLayout>
  );
}