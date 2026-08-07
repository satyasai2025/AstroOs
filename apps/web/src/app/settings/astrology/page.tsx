"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";

export default function AstrologySettingsPage() {
  return (
    <SettingsLayout title="Astrology" description="Configure chart defaults and calculation preferences">
      <div className="grid gap-6 md:grid-cols-2">
        {/* Chart Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Chart
          </h3>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Zodiac
              </label>
              <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                <option>Sidereal</option>
                <option>Tropical</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Ayanamsa
              </label>
              <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                <option>Lahiri</option>
                <option>Raman</option>
                <option>KP</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                House System
              </label>
              <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                <option>Whole Sign</option>
                <option>Placidus</option>
                <option>Equal</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Chart Style
              </label>
              <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                <option>North Indian</option>
                <option>South Indian</option>
                <option>Western</option>
              </select>
            </div>
          </div>
        </div>

        {/* Calculation Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Calculation
          </h3>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Mean / True Nodes
              </label>
              <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                <option>True</option>
                <option>Mean</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Aspect Orb
              </label>
              <input
                type="text"
                defaultValue="8°"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}
              />
            </div>
          </div>
        </div>

        {/* Dasha Card */}
        <div className="rounded-2xl border p-6 md:col-span-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Dasha
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Default Dasha
              </label>
              <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                <option>Vimshottari</option>
                <option>Ashtottari</option>
                <option>Yogini</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Transit Defaults
              </label>
              <select className="w-full rounded-lg px-3 py-2 text-sm outline-none" style={{ backgroundColor: "var(--bg-input)", color: "var(--text-primary)", border: "1px solid var(--border-primary)" }}>
                <option>Gochara</option>
                <option>Jaimini</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button className="rounded-lg px-4 py-2 text-sm font-semibold" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
          Save Changes
        </button>
      </div>
    </SettingsLayout>
  );
}