"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { useCurrentUser, useUpdateProfile } from "@/lib/auth";
import { useEffect, useMemo, useState } from "react";

const POPULAR_TIMEZONES = [
  { value: "Asia/Kolkata", label: "🇮🇳 India Standard Time (IST) — Asia/Kolkata (UTC+05:30)" },
  { value: "Asia/Calcutta", label: "🇮🇳 India Standard Time (IST) — Asia/Calcutta (UTC+05:30)" },
  { value: "UTC", label: "🌐 UTC — Coordinated Universal Time (UTC+00:00)" },
  { value: "Asia/Dubai", label: "🇦🇪 Gulf Standard Time (GST) — Asia/Dubai (UTC+04:00)" },
  { value: "Asia/Singapore", label: "🇸🇬 Singapore Time (SGT) — Asia/Singapore (UTC+08:00)" },
  { value: "America/New_York", label: "🇺🇸 Eastern Time — America/New_York (UTC-05:00)" },
  { value: "America/Chicago", label: "🇺🇸 Central Time — America/Chicago (UTC-06:00)" },
  { value: "America/Los_Angeles", label: "🇺🇸 Pacific Time — America/Los_Angeles (UTC-08:00)" },
  { value: "Europe/London", label: "🇬🇧 UK Time — Europe/London (UTC+00:00)" },
  { value: "Europe/Berlin", label: "🇩🇪 Central European Time — Europe/Berlin (UTC+01:00)" },
  { value: "Asia/Tokyo", label: "🇯🇵 Japan Standard Time (JST) — Asia/Tokyo (UTC+09:00)" },
  { value: "Australia/Sydney", label: "🇦🇺 Australian Eastern Time — Australia/Sydney (UTC+10:00)" },
];

/** Real IANA timezone list from the browser's own tzdata (all modern
 * browsers/Node support this) — falls back to a short curated list only
 * if the runtime somehow lacks Intl.supportedValuesOf (very old browsers). */
function getTimezoneOptions(): string[] {
  try {
    return Intl.supportedValuesOf("timeZone");
  } catch {
    return [
      "Asia/Kolkata",
      "UTC",
      "America/New_York",
      "America/Los_Angeles",
      "Europe/London",
      "Europe/Berlin",
      "Asia/Tokyo",
      "Australia/Sydney",
    ];
  }
}

export default function ProfileSettingsPage() {
  const { data: user, isLoading } = useCurrentUser();
  const updateProfile = useUpdateProfile();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [saveState, setSaveState] = useState<"idle" | "saved" | "error">("idle");

  const timezoneOptions = useMemo(() => getTimezoneOptions(), []);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || "");
      setEmail(user.email || "");
      setPhoneNumber(user.phone_number || "");
      setTimezone(user.timezone || "Asia/Kolkata");
    }
  }, [user]);

  const handleSave = () => {
    setSaveState("idle");
    const payload: { display_name?: string; email?: string; timezone?: string; phone_number?: string } = {};
    if (displayName !== user?.display_name) payload.display_name = displayName;
    if (email !== user?.email) payload.email = email;
    if (phoneNumber !== (user?.phone_number || "")) payload.phone_number = phoneNumber;
    if (timezone !== user?.timezone) payload.timezone = timezone;
    if (Object.keys(payload).length === 0) return;

    updateProfile.mutate(payload, {
      onSuccess: () => setSaveState("saved"),
      onError: () => setSaveState("error"),
    });
  };

  const initials = (displayName || "?")
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  if (isLoading) {
    return (
      <SettingsLayout title="Profile" description="Manage your personal information">
        <div className="flex h-64 items-center justify-center" style={{ color: "var(--text-muted)" }}>
          Loading…
        </div>
      </SettingsLayout>
    );
  }

  return (
    <SettingsLayout title="Profile" description="Manage your personal information">
      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Information Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Personal Information
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Update your personal details
          </p>

          {/* Avatar */}
          <div className="mb-6 flex items-center gap-4">
            <div className="relative">
              <div
                className="flex h-16 w-16 items-center justify-center rounded-2xl text-xl font-bold"
                style={{
                  background: "linear-gradient(135deg, var(--accent), var(--violet-400))",
                  color: "var(--accent-text)",
                }}
              >
                {initials}
              </div>
              <button
                className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full"
                style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-primary)" }}
                title="Change avatar"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
              </button>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Phone Number
              </label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+1 (555) 000-0000"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Timezone
              </label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none font-medium"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              >
                <optgroup label="Popular & India Timezones">
                  {POPULAR_TIMEZONES.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </optgroup>
                <optgroup label="All Global Timezones (A-Z)">
                  {timezoneOptions
                    .filter((tz) => !POPULAR_TIMEZONES.some((p) => p.value === tz))
                    .map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                </optgroup>
              </select>
              <p className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
                Used to interpret date/time fields you enter without an explicit offset — e.g. Transit
                Analysis&rsquo;s &ldquo;Jump to Date &amp; Time&rdquo; picker.
              </p>
            </div>
          </div>
        </div>

        {/* Account Overview Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Account
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Your account details and activity
          </p>

          <div className="space-y-5">
            {/* Email with Envelope Mail Icon */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-primary-soft)", color: "var(--accent)" }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect width="20" height="16" x="2" y="4" rx="2" />
                    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>Email</p>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{user?.email || email || "—"}</p>
                </div>
              </div>
            </div>

            {/* Phone with Telephone Handset Icon */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "rgba(6, 182, 212, 0.15)", color: "#06b6d4" }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>Phone Number</p>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{user?.phone_number || phoneNumber || "—"}</p>
                </div>
              </div>
            </div>

            {/* Created */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-secondary-soft)", color: "var(--obsidian-accent-secondary)" }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                    <line x1="16" y1="2" x2="16" y2="6" />
                    <line x1="8" y1="2" x2="8" y2="6" />
                    <line x1="3" y1="10" x2="21" y2="10" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>Created</p>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—"}
                  </p>
                </div>
              </div>
            </div>

            {/* Last Login */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: "rgba(16, 185, 129, 0.1)", color: "var(--status-success)" }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>Last Login</p>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {user?.last_login_at ? new Date(user.last_login_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "—"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 flex items-center justify-end gap-3">
        {saveState === "saved" && (
          <span className="text-xs" style={{ color: "var(--status-success)" }}>
            Saved.
          </span>
        )}
        {saveState === "error" && (
          <span className="text-xs" style={{ color: "var(--status-danger)" }}>
            {updateProfile.error?.message || "Could not save changes."}
          </span>
        )}
        <button
          onClick={handleSave}
          disabled={updateProfile.isPending}
          className="rounded-lg px-4 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
          style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          {updateProfile.isPending ? "Saving…" : "Save Changes"}
        </button>
      </div>
    </SettingsLayout>
  );
}