"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";

export default function AppearanceSettingsPage() {
  return (
    <SettingsLayout title="Appearance" description="Customize the look and feel of AstroOS">
      <div className="space-y-6">
        {/* Theme Selection */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Theme
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Choose your preferred color scheme
          </p>

          <div className="grid gap-4 sm:grid-cols-3">
            <label className="cursor-pointer">
              <input type="radio" name="theme" className="sr-only peer" />
              <div
                className="rounded-xl border-2 p-4 text-center transition-all peer-checked:border-[var(--accent)] peer-checked:bg-[var(--accent)]/5"
                style={{ borderColor: "var(--border-primary)" }}
              >
                <div className="mb-3 text-2xl">☀️</div>
                <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Light</div>
              </div>
            </label>

            <label className="cursor-pointer">
              <input type="radio" name="theme" defaultChecked className="sr-only peer" />
              <div
                className="rounded-xl border-2 p-4 text-center transition-all peer-checked:border-[var(--accent)] peer-checked:bg-[var(--accent)]/5"
                style={{ borderColor: "var(--border-primary)" }}
              >
                <div className="mb-3 text-2xl">🌙</div>
                <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Dark</div>
              </div>
            </label>

            <label className="cursor-pointer">
              <input type="radio" name="theme" className="sr-only peer" />
              <div
                className="rounded-xl border-2 p-4 text-center transition-all peer-checked:border-[var(--accent)] peer-checked:bg-[var(--accent)]/5"
                style={{ borderColor: "var(--border-primary)" }}
              >
                <div className="mb-3 text-2xl">💻</div>
                <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>System</div>
              </div>
            </label>
          </div>
        </div>

        {/* Accent Color */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Accent Color
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Select your preferred accent color
          </p>

          <div className="flex gap-4">
            {[
              { name: "Blue", color: "#06CFFF" },
              { name: "Purple", color: "#8B5CF6" },
              { name: "Emerald", color: "#10B981" },
            ].map((accent) => (
              <label key={accent.name} className="cursor-pointer">
                <input type="radio" name="accent" defaultChecked={accent.name === "Blue"} className="sr-only peer" />
                <div
                  className="flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all peer-checked:scale-110 peer-checked:ring-2 peer-checked:ring-offset-2"
                  style={{
                    backgroundColor: accent.color,
                    borderColor: "var(--border-primary)",
                    ringColor: accent.color,
                  }}
                />
              </label>
            ))}
          </div>
        </div>

        {/* Density */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-1 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Density
          </h3>
          <p className="mb-6 text-xs" style={{ color: "var(--text-muted)" }}>
            Adjust the spacing and density of the interface
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="cursor-pointer">
              <input type="radio" name="density" defaultChecked className="sr-only peer" />
              <div
                className="rounded-xl border-2 p-4 transition-all peer-checked:border-[var(--accent)] peer-checked:bg-[var(--accent)]/5"
                style={{ borderColor: "var(--border-primary)" }}
              >
                <div className="text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>Comfortable</div>
                <div className="space-y-2">
                  <div className="h-2 rounded w-full" style={{ backgroundColor: "var(--border-primary)" }} />
                  <div className="h-2 rounded w-5/6" style={{ backgroundColor: "var(--border-primary)" }} />
                </div>
              </div>
            </label>

            <label className="cursor-pointer">
              <input type="radio" name="density" className="sr-only peer" />
              <div
                className="rounded-xl border-2 p-4 transition-all peer-checked:border-[var(--accent)] peer-checked:bg-[var(--accent)]/5"
                style={{ borderColor: "var(--border-primary)" }}
              >
                <div className="text-sm font-medium mb-2" style={{ color: "var(--text-primary)" }}>Compact</div>
                <div className="space-y-1">
                  <div className="h-1.5 rounded w-full" style={{ backgroundColor: "var(--border-primary)" }} />
                  <div className="h-1.5 rounded w-5/6" style={{ backgroundColor: "var(--border-primary)" }} />
                </div>
              </div>
            </label>
          </div>
        </div>

        <div className="flex justify-end">
          <button
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