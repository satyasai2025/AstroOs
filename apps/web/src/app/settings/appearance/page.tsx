"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { useTheme } from "@/components/layout/ThemeProvider";
import { useEffect, useState } from "react";

const ACCENT_OPTIONS = [
  { name: "Cyan", color: "#06CFFF" },
  { name: "Purple", color: "#8B5CF6" },
  { name: "Emerald", color: "#10B981" },
  { name: "Gold", color: "#F59E0B" },
];

export default function AppearanceSettingsPage() {
  const { theme, setTheme } = useTheme();
  const [selectedTheme, setSelectedTheme] = useState<"light" | "dark" | "system">("dark");
  const [selectedAccent, setSelectedAccent] = useState("#06CFFF");
  const [density, setDensity] = useState<"comfortable" | "compact">("comfortable");
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    try {
      const storedTheme = localStorage.getItem("astroos_theme_mode") || (theme as "light" | "dark");
      setSelectedTheme(storedTheme as "light" | "dark" | "system");

      const storedAccent = localStorage.getItem("astroos_accent_color");
      if (storedAccent) setSelectedAccent(storedAccent);

      const storedDensity = localStorage.getItem("astroos_density");
      if (storedDensity === "comfortable" || storedDensity === "compact") {
        setDensity(storedDensity);
      }
    } catch {
      // Ignore
    }
  }, [theme]);

  const handleThemeChange = (mode: "light" | "dark" | "system") => {
    setSelectedTheme(mode);
    setSavedMessage(null);
    try {
      localStorage.setItem("astroos_theme_mode", mode);
    } catch {
      // Ignore
    }

    if (mode === "system") {
      const isLight = window.matchMedia("(prefers-color-scheme: light)").matches;
      setTheme(isLight ? "light" : "dark");
    } else {
      setTheme(mode);
    }
  };

  const handleAccentChange = (color: string) => {
    setSelectedAccent(color);
    setSavedMessage(null);
    try {
      localStorage.setItem("astroos_accent_color", color);
      document.documentElement.style.setProperty("--accent", color);
    } catch {
      // Ignore
    }
  };

  const handleDensityChange = (d: "comfortable" | "compact") => {
    setDensity(d);
    setSavedMessage(null);
    try {
      localStorage.setItem("astroos_density", d);
    } catch {
      // Ignore
    }
  };

  const handleSave = () => {
    setSavedMessage("Appearance preferences saved successfully.");
    setTimeout(() => setSavedMessage(null), 4000);
  };

  return (
    <SettingsLayout title="Appearance" description="Customize the look and feel of AstroOS">
      <div className="space-y-6">
        {/* Theme Selection */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Theme Mode
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Choose your preferred color scheme
          </p>

          <div className="grid gap-4 sm:grid-cols-3">
            <button
              type="button"
              onClick={() => handleThemeChange("light")}
              className="rounded-xl border-2 p-4 text-center transition-all focus:outline-none"
              style={{
                borderColor: selectedTheme === "light" ? "var(--accent)" : "var(--border-primary)",
                backgroundColor: selectedTheme === "light" ? "var(--obsidian-accent-primary-soft)" : "transparent",
              }}
            >
              <div className="mb-3 text-2xl">☀️</div>
              <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Light</div>
            </button>

            <button
              type="button"
              onClick={() => handleThemeChange("dark")}
              className="rounded-xl border-2 p-4 text-center transition-all focus:outline-none"
              style={{
                borderColor: selectedTheme === "dark" ? "var(--accent)" : "var(--border-primary)",
                backgroundColor: selectedTheme === "dark" ? "var(--obsidian-accent-primary-soft)" : "transparent",
              }}
            >
              <div className="mb-3 text-2xl">🌙</div>
              <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Dark</div>
            </button>

            <button
              type="button"
              onClick={() => handleThemeChange("system")}
              className="rounded-xl border-2 p-4 text-center transition-all focus:outline-none"
              style={{
                borderColor: selectedTheme === "system" ? "var(--accent)" : "var(--border-primary)",
                backgroundColor: selectedTheme === "system" ? "var(--obsidian-accent-primary-soft)" : "transparent",
              }}
            >
              <div className="mb-3 text-2xl">💻</div>
              <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>System</div>
            </button>
          </div>
        </div>

        {/* Accent Color */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Accent Color
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Select your primary interface highlight
          </p>

          <div className="flex flex-wrap gap-4">
            {ACCENT_OPTIONS.map((accent) => (
              <button
                key={accent.name}
                type="button"
                onClick={() => handleAccentChange(accent.color)}
                className="flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all hover:scale-105 focus:outline-none"
                style={{
                  backgroundColor: accent.color,
                  borderColor: selectedAccent === accent.color ? "var(--text-primary)" : "var(--border-primary)",
                  boxShadow: selectedAccent === accent.color ? `0 0 0 3px ${accent.color}88` : "none",
                }}
                title={accent.name}
              ></button>
            ))}
          </div>
        </div>

        {/* Density */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Interface Density
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Adjust the spacing and density of lists and tables
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => handleDensityChange("comfortable")}
              className="rounded-xl border-2 p-4 text-left transition-all focus:outline-none"
              style={{
                borderColor: density === "comfortable" ? "var(--accent)" : "var(--border-primary)",
                backgroundColor: density === "comfortable" ? "var(--obsidian-accent-primary-soft)" : "transparent",
              }}
            >
              <div className="text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>Comfortable</div>
              <div className="space-y-2">
                <div className="h-2 rounded w-full" style={{ backgroundColor: "var(--border-primary)" }} />
                <div className="h-2 rounded w-5/6" style={{ backgroundColor: "var(--border-primary)" }} />
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleDensityChange("compact")}
              className="rounded-xl border-2 p-4 text-left transition-all focus:outline-none"
              style={{
                borderColor: density === "compact" ? "var(--accent)" : "var(--border-primary)",
                backgroundColor: density === "compact" ? "var(--obsidian-accent-primary-soft)" : "transparent",
              }}
            >
              <div className="text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>Compact</div>
              <div className="space-y-1">
                <div className="h-1.5 rounded w-full" style={{ backgroundColor: "var(--border-primary)" }} />
                <div className="h-1.5 rounded w-5/6" style={{ backgroundColor: "var(--border-primary)" }} />
              </div>
            </button>
          </div>
        </div>

        {savedMessage && (
          <div
            className="rounded-lg border p-3 text-sm"
            style={{
              borderColor: "var(--status-success)",
              color: "var(--status-success)",
              backgroundColor: "var(--bg-input)",
            }}
          >
            {savedMessage}
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            className="rounded-lg px-4 py-2 text-sm font-semibold"
            style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
          >
            Save Changes
          </button>
        </div>
      </div>
    </SettingsLayout>
  );
}