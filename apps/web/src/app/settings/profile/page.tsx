"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { useCurrentUser, useUpdateProfile } from "@/lib/auth";
import { Card, Icon, type IconName } from "@/components/ui";

const STORAGE_PROFILE_EXTRA = "astroos_practitioner_profile";

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

const SPECIALIZATIONS_LIST = [
  "Parashari Jyotish",
  "KP System (Krishnamurti)",
  "Jaimini Astrology",
  "Nadi Jyotish",
  "Sarvatobhadra & SBC",
  "Medical Astrology",
  "Muhurta & Electional",
  "Vastu & Astro-Geography",
  "Mundane & Financial",
  "Empirical Research",
];

const AVATAR_PRESETS = [
  { id: "om", icon: "ॐ", bg: "from-cyan-500 to-blue-600", name: "Sacred Om" },
  { id: "sun", icon: "☉", bg: "from-amber-400 to-orange-500", name: "Surya (Sun)" },
  { id: "moon", icon: "☽", bg: "from-slate-300 to-indigo-400", name: "Chandra (Moon)" },
  { id: "jupiter", icon: "♃", bg: "from-yellow-400 to-amber-600", name: "Guru (Jupiter)" },
  { id: "mercury", icon: "☿", bg: "from-emerald-400 to-teal-600", name: "Budha (Mercury)" },
  { id: "venus", icon: "♀", bg: "from-pink-400 to-rose-600", name: "Shukra (Venus)" },
  { id: "mars", icon: "♂", bg: "from-red-500 to-rose-700", name: "Mangal (Mars)" },
  { id: "saturn", icon: "♄", bg: "from-indigo-600 to-purple-800", name: "Shani (Saturn)" },
];

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

  // Core profile fields
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [timezone, setTimezone] = useState("Asia/Kolkata");

  // Practitioner & extended fields
  const [practitionerLevel, setPractitionerLevel] = useState("Practicing Astrologer");
  const [organization, setOrganization] = useState("");
  const [selectedSpecializations, setSelectedSpecializations] = useState<string[]>([
    "Parashari Jyotish",
    "Vimshottari Timing",
  ]);
  const [bio, setBio] = useState("");
  const [defaultCity, setDefaultCity] = useState("New Delhi, India");
  const [avatarStyle, setAvatarStyle] = useState<string>("om");
  const [customAvatarEmoji, setCustomAvatarEmoji] = useState<string>("");
  const [showAvatarPicker, setShowAvatarPicker] = useState(false);

  // UI status states
  const [copiedUid, setCopiedUid] = useState(false);
  const [saveState, setSaveState] = useState<"idle" | "saved" | "error">("idle");
  const [hasChanges, setHasChanges] = useState(false);

  const timezoneOptions = useMemo(() => getTimezoneOptions(), []);

  // Initialize from user data and localStorage
  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || "");
      setEmail(user.email || "");
      setPhoneNumber(user.phone_number || "");
      setTimezone(user.timezone || "Asia/Kolkata");
    }

    try {
      const storedExtra = localStorage.getItem(STORAGE_PROFILE_EXTRA);
      if (storedExtra) {
        const parsed = JSON.parse(storedExtra);
        if (parsed.practitionerLevel) setPractitionerLevel(parsed.practitionerLevel);
        if (parsed.organization) setOrganization(parsed.organization);
        if (parsed.selectedSpecializations) setSelectedSpecializations(parsed.selectedSpecializations);
        if (parsed.bio) setBio(parsed.bio);
        if (parsed.defaultCity) setDefaultCity(parsed.defaultCity);
        if (parsed.avatarStyle) setAvatarStyle(parsed.avatarStyle);
        if (parsed.customAvatarEmoji) setCustomAvatarEmoji(parsed.customAvatarEmoji);
      }
    } catch {
      // Ignore local storage error
    }
  }, [user]);

  // Track if changes exist
  useEffect(() => {
    if (!user) return;
    const isCoreChanged =
      displayName !== (user.display_name || "") ||
      email !== (user.email || "") ||
      phoneNumber !== (user.phone_number || "") ||
      timezone !== (user.timezone || "Asia/Kolkata");

    setHasChanges(isCoreChanged);
  }, [displayName, email, phoneNumber, timezone, user]);

  const initials = (displayName || user?.display_name || "?")
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const handleCopyUid = () => {
    if (!user?.id) return;
    navigator.clipboard.writeText(user.id);
    setCopiedUid(true);
    setTimeout(() => setCopiedUid(false), 2500);
  };

  const handleDetectTimezone = () => {
    try {
      const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (detected) {
        setTimezone(detected);
        setHasChanges(true);
      }
    } catch {
      // Fallback
    }
  };

  const toggleSpecialization = (spec: string) => {
    setSelectedSpecializations((prev) =>
      prev.includes(spec) ? prev.filter((s) => s !== spec) : [...prev, spec]
    );
    setHasChanges(true);
  };

  const handleSave = () => {
    setSaveState("idle");

    // Save extended practitioner preferences to local cache
    try {
      const extraData = {
        practitionerLevel,
        organization,
        selectedSpecializations,
        bio,
        defaultCity,
        avatarStyle,
        customAvatarEmoji,
      };
      localStorage.setItem(STORAGE_PROFILE_EXTRA, JSON.stringify(extraData));
    } catch {
      // Ignore local storage error
    }

    const payload: { display_name?: string; email?: string; timezone?: string } = {};
    if (displayName !== user?.display_name) payload.display_name = displayName;
    if (email !== user?.email) payload.email = email;
    if (timezone !== user?.timezone) payload.timezone = timezone;

    if (Object.keys(payload).length === 0) {
      setSaveState("saved");
      setHasChanges(false);
      setTimeout(() => setSaveState("idle"), 3500);
      return;
    }

    updateProfile.mutate(payload, {
      onSuccess: () => {
        setSaveState("saved");
        setHasChanges(false);
        setTimeout(() => setSaveState("idle"), 3500);
      },
      onError: () => {
        setSaveState("error");
      },
    });
  };

  const handleExportData = () => {
    const dataToExport = {
      profile: {
        id: user?.id,
        display_name: displayName,
        email,
        phone_number: phoneNumber,
        timezone,
        role: user?.role,
        status: user?.status,
        created_at: user?.created_at,
        last_login_at: user?.last_login_at,
      },
      practitioner_preferences: {
        practitionerLevel,
        organization,
        specializations: selectedSpecializations,
        bio,
        defaultCity,
      },
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `AstroOS_Profile_${(displayName || "User").replace(/\s+/g, "_")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Calculate profile completion percentage
  const completionScore = useMemo(() => {
    let score = 0;
    if (displayName) score += 20;
    if (email) score += 20;
    if (phoneNumber) score += 15;
    if (timezone) score += 15;
    if (bio) score += 15;
    if (selectedSpecializations.length > 0) score += 15;
    return Math.min(score, 100);
  }, [displayName, email, phoneNumber, timezone, bio, selectedSpecializations]);

  const activeAvatar = AVATAR_PRESETS.find((p) => p.id === avatarStyle) || AVATAR_PRESETS[0];

  if (isLoading) {
    return (
      <SettingsLayout title="Profile & Account" description="Manage personal details and practitioner profile">
        <div className="flex h-64 items-center justify-center text-slate-400">
          <div className="flex items-center gap-3">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
            <span className="text-sm font-medium">Loading profile data…</span>
          </div>
        </div>
      </SettingsLayout>
    );
  }

  return (
    <SettingsLayout
      title="Profile &amp; Practitioner Settings"
      description="Manage your personal identity, contact information, astrological credentials, and research defaults."
    >
      <div className="space-y-6">
        {/* ── 1. Hero Identity Banner ── */}
        <div className="relative overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-slate-900 via-slate-850 to-slate-950 p-6 text-white shadow-xl">
          <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
              {/* Avatar with click to customize */}
              <div className="relative group cursor-pointer" onClick={() => setShowAvatarPicker(true)}>
                <div
                  className={`flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br ${activeAvatar.bg} text-2xl font-bold shadow-lg shadow-cyan-500/10 border-2 border-white/20 transition-transform group-hover:scale-105`}
                >
                  {customAvatarEmoji || activeAvatar.icon || initials}
                </div>
                <div
                  className="absolute -bottom-1.5 -right-1.5 flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 text-cyan-400 border border-slate-700 shadow-md group-hover:bg-cyan-500 group-hover:text-slate-950 transition"
                  title="Customize Avatar"
                >
                  <Icon name="palette" style={{ width: 14, height: 14 }} />
                </div>
              </div>

              {/* User info */}
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
                    {displayName || user?.display_name || "Vedic Practitioner"}
                  </h2>
                  <span className="rounded-full bg-cyan-500/20 border border-cyan-400/40 px-2.5 py-0.5 text-xs font-semibold text-cyan-300">
                    {practitionerLevel}
                  </span>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    {user?.status || "Active"}
                  </span>
                </div>

                <p className="text-xs text-slate-300 flex items-center gap-2">
                  <span>{email || user?.email}</span>
                  <span>•</span>
                  <span>{timezone}</span>
                  {organization && (
                    <>
                      <span>•</span>
                      <span className="text-cyan-300">{organization}</span>
                    </>
                  )}
                </p>

                {/* User ID copy row */}
                <div className="flex items-center gap-2 pt-1">
                  <span className="text-[11px] text-slate-400 font-mono">UID: {user?.id || "—"}</span>
                  <button
                    type="button"
                    onClick={handleCopyUid}
                    className="inline-flex items-center gap-1 text-[10px] font-medium text-cyan-400 hover:text-cyan-300 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700"
                  >
                    {copiedUid ? "✓ Copied!" : "Copy UID"}
                  </button>
                </div>
              </div>
            </div>

            {/* Profile completion gauge */}
            <div className="rounded-xl border border-slate-700/60 bg-slate-800/60 p-3.5 sm:w-56 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium">Profile Strength</span>
                <span className="text-cyan-400 font-bold">{completionScore}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-700">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400 transition-all duration-500"
                  style={{ width: `${completionScore}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-400">
                {completionScore === 100
                  ? "✓ Complete profile configuration"
                  : "Add phone, bio & specializations to reach 100%"}
              </p>
            </div>
          </div>
        </div>

        {/* ── Avatar Picker Modal ── */}
        {showAvatarPicker && (
          <div className="rounded-2xl border border-cyan-500/40 bg-white dark:bg-slate-900 p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Icon name="palette" style={{ width: 18, height: 18, color: "var(--accent)" }} />
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Select Astrological Avatar Emblem
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAvatarPicker(false)}
                className="text-xs text-slate-400 hover:text-slate-200"
              >
                ✕ Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {AVATAR_PRESETS.map((preset) => {
                const isSelected = avatarStyle === preset.id;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => {
                      setAvatarStyle(preset.id);
                      setCustomAvatarEmoji("");
                      setHasChanges(true);
                    }}
                    className={`flex items-center gap-3 rounded-xl border p-2.5 text-left transition ${
                      isSelected
                        ? "border-cyan-500 bg-cyan-500/10 shadow-sm shadow-cyan-500/20"
                        : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-850"
                    }`}
                  >
                    <div
                      className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br ${preset.bg} text-lg font-bold text-white shadow`}
                    >
                      {preset.icon}
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                        {preset.name}
                      </p>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400">Emblem</p>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Custom Initial / Emoji Option */}
            <div className="flex items-center gap-3 pt-2 border-t border-slate-200 dark:border-slate-800 text-xs">
              <span className="text-slate-600 dark:text-slate-400 font-medium">Or type custom symbol/emoji:</span>
              <input
                type="text"
                maxLength={2}
                value={customAvatarEmoji}
                onChange={(e) => {
                  setCustomAvatarEmoji(e.target.value);
                  setHasChanges(true);
                }}
                placeholder="e.g. 🔱, ✡, ⚡"
                className="w-28 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-2.5 py-1 text-center text-sm"
              />
              <button
                type="button"
                onClick={() => setShowAvatarPicker(false)}
                className="ml-auto rounded-lg bg-cyan-500 px-3 py-1 text-xs font-bold text-slate-950"
              >
                Apply
              </button>
            </div>
          </div>
        )}

        {/* ── 2. Grid: Personal Info & Practitioner Profile ── */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Card 1: Personal & Contact Information */}
          <Card className="p-6 space-y-4">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Icon name="user" style={{ width: 18, height: 18, color: "var(--accent)" }} />
                <span>Personal &amp; Contact Details</span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Primary credentials used for account verification and client correspondence.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Full Name / Display Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => {
                    setDisplayName(e.target.value);
                    setHasChanges(true);
                  }}
                  placeholder="Your Name (e.g. Dr. Aryan Sharma)"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-850 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Email Address <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setHasChanges(true);
                    }}
                    placeholder="practitioner@example.com"
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-850 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition"
                  />
                  <span className="absolute right-3 top-2.5 rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    Primary
                  </span>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Phone Number (for Client Consultations)
                </label>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => {
                    setPhoneNumber(e.target.value);
                    setHasChanges(true);
                  }}
                  placeholder="+91 98765 43210"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-850 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 transition"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Default Timezone <span className="text-rose-500">*</span>
                  </label>
                  <button
                    type="button"
                    onClick={handleDetectTimezone}
                    className="text-[11px] font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
                  >
                    📍 Auto-Detect Local
                  </button>
                </div>
                <select
                  value={timezone}
                  onChange={(e) => {
                    setTimezone(e.target.value);
                    setHasChanges(true);
                  }}
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-850 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 font-medium"
                >
                  <optgroup label="Popular & India Timezones">
                    {POPULAR_TIMEZONES.map((tz) => (
                      <option key={tz.value} value={tz.value}>
                        {tz.label}
                      </option>
                    ))}
                  </optgroup>
                  <optgroup label="All Global IANA Timezones (A-Z)">
                    {timezoneOptions
                      .filter((tz) => !POPULAR_TIMEZONES.some((p) => p.value === tz))
                      .map((tz) => (
                        <option key={tz} value={tz}>
                          {tz}
                        </option>
                      ))}
                  </optgroup>
                </select>
                <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                  Used for interpreting real-time transits, Prashna charts, and planetary ephemeris calculations.
                </p>
              </div>
            </div>
          </Card>

          {/* Card 2: Astrological Credentials & Specializations */}
          <Card className="p-6 space-y-4">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Icon name="star" style={{ width: 18, height: 18, color: "var(--accent)" }} />
                <span>Astrological Credentials &amp; Focus</span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Customize your research domains and public report headers.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Practitioner / Experience Level
                </label>
                <select
                  value={practitionerLevel}
                  onChange={(e) => {
                    setPractitionerLevel(e.target.value);
                    setHasChanges(true);
                  }}
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-850 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 font-medium"
                >
                  <option value="Student &amp; Enthusiast">🎓 Student &amp; Astrology Enthusiast</option>
                  <option value="Practicing Astrologer">⭐ Practicing Vedic Astrologer</option>
                  <option value="Professional Consultant">👑 Professional Astrological Consultant</option>
                  <option value="Academic Researcher / Scholar">🏛️ Academic Researcher / Scholar</option>
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Consultation Practice / Organization
                </label>
                <input
                  type="text"
                  value={organization}
                  onChange={(e) => {
                    setOrganization(e.target.value);
                    setHasChanges(true);
                  }}
                  placeholder="e.g. Center for Vedic Studies / Private Practice"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-850 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 transition"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Primary Specializations (Select all that apply)
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {SPECIALIZATIONS_LIST.map((spec) => {
                    const isSelected = selectedSpecializations.includes(spec);
                    return (
                      <button
                        key={spec}
                        type="button"
                        onClick={() => toggleSpecialization(spec)}
                        className={`rounded-lg px-2.5 py-1 text-xs font-medium transition ${
                          isSelected
                            ? "bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border border-cyan-400/40 font-bold"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-transparent hover:border-slate-300 dark:hover:border-slate-700"
                        }`}
                      >
                        {isSelected ? "✓ " : "+ "}
                        {spec}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Practitioner Bio / Research Summary
                </label>
                <textarea
                  rows={3}
                  value={bio}
                  onChange={(e) => {
                    setBio(e.target.value);
                    setHasChanges(true);
                  }}
                  placeholder="Share your astrological background, favorite classical texts (BPHS, Saravali), or research focus..."
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-850 p-3 text-sm text-slate-900 dark:text-slate-100 outline-none focus:border-cyan-500 transition resize-none"
                />
              </div>
            </div>
          </Card>
        </div>

        {/* ── 3. Account Activity & Security Overview ── */}
        <Card className="p-6 space-y-4">
          <div className="border-b border-slate-200 dark:border-slate-800 pb-3">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Icon name="shield" style={{ width: 18, height: 18, color: "var(--accent)" }} />
              <span>Account Information &amp; Data Control</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Review your system privileges, activity timestamps, and data export options.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl bg-slate-50 dark:bg-slate-850 p-3.5 border border-slate-200 dark:border-slate-800">
              <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                System Role
              </p>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1 capitalize">
                {user?.role || "Researcher"}
              </p>
              <p className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-0.5">
                Full platform access
              </p>
            </div>

            <div className="rounded-xl bg-slate-50 dark:bg-slate-850 p-3.5 border border-slate-200 dark:border-slate-800">
              <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Member Since
              </p>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })
                  : "Recent"}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">Verified registration</p>
            </div>

            <div className="rounded-xl bg-slate-50 dark:bg-slate-850 p-3.5 border border-slate-200 dark:border-slate-800">
              <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Last Active Login
              </p>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-1">
                {user?.last_login_at
                  ? new Date(user.last_login_at).toLocaleString("en-US", {
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })
                  : "Active Now"}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">Secure JWT Session</p>
            </div>

            <div className="rounded-xl bg-slate-50 dark:bg-slate-850 p-3.5 border border-slate-200 dark:border-slate-800">
              <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Security Shortcuts
              </p>
              <div className="mt-1 flex items-center gap-2">
                <Link
                  href="/settings/security"
                  className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline"
                >
                  Change Password &rarr;
                </Link>
              </div>
              <p className="text-[10px] text-slate-400 mt-0.5">2FA &amp; session locks</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
              <Icon name="database" style={{ width: 16, height: 16 }} />
              <span>Download a portable copy of your account profile &amp; preferences.</span>
            </div>
            <button
              type="button"
              onClick={handleExportData}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:border-cyan-500 transition"
            >
              <Icon name="download" style={{ width: 14, height: 14 }} />
              <span>Export Profile JSON</span>
            </button>
          </div>
        </Card>

        {/* ── 4. Sticky Action & Save Bar ── */}
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-md">
          <div className="flex items-center gap-2">
            {saveState === "saved" && (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                <span>✓</span> Profile changes saved successfully.
              </span>
            )}
            {saveState === "error" && (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400">
                <span>✕</span> {updateProfile.error?.message || "Could not save profile changes."}
              </span>
            )}
            {saveState === "idle" && hasChanges && (
              <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                ● You have unsaved changes.
              </span>
            )}
            {saveState === "idle" && !hasChanges && (
              <span className="text-xs text-slate-500 dark:text-slate-400">
                All profile settings are up to date.
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                if (user) {
                  setDisplayName(user.display_name || "");
                  setEmail(user.email || "");
                  setPhoneNumber(user.phone_number || "");
                  setTimezone(user.timezone || "Asia/Kolkata");
                }
                setHasChanges(false);
                setSaveState("idle");
              }}
              disabled={!hasChanges}
              className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Discard Changes
            </button>

            <button
              type="button"
              onClick={handleSave}
              disabled={updateProfile.isPending}
              className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 px-5 py-2.5 text-xs font-bold text-slate-950 shadow-md shadow-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-50 transition cursor-pointer"
            >
              {updateProfile.isPending ? (
                <>
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
                  <span>Saving…</span>
                </>
              ) : (
                <span>Save Profile Changes</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </SettingsLayout>
  );
}