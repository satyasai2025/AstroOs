"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";
import { useEffect, useState } from "react";

const STORAGE_KEY = "astroos_astrology_settings";

interface AstrologySettingsState {
  zodiac: string;
  ayanamsa: string;
  houseSystem: string;
  chartStyle: string;
  nodeType: string;
  aspectOrb: string;
  defaultDasha: string;
  transitDefaults: string;
}

const DEFAULT_SETTINGS: AstrologySettingsState = {
  zodiac: "Sidereal",
  ayanamsa: "Lahiri",
  houseSystem: "Whole Sign",
  chartStyle: "North Indian",
  nodeType: "True",
  aspectOrb: "8°",
  defaultDasha: "Vimshottari",
  transitDefaults: "Gochara",
};

export default function AstrologySettingsPage() {
  const [settings, setSettings] = useState<AstrologySettingsState>(DEFAULT_SETTINGS);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(stored) });
      }
    } catch {
      // Ignore storage error
    }
  }, []);

  const handleChange = (field: keyof AstrologySettingsState, value: string) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
    setSavedMessage(null);
  };

  const handleSave = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      setSavedMessage("Astrology preferences saved successfully.");
      setTimeout(() => setSavedMessage(null), 4000);
    } catch {
      setSavedMessage("Failed to save preferences.");
    }
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_SETTINGS));
      setSavedMessage("Preferences reset to defaults.");
      setTimeout(() => setSavedMessage(null), 4000);
    } catch {
      // Ignore
    }
  };

  const inputStyle = {
    backgroundColor: "var(--bg-input)",
    color: "var(--text-primary)",
    border: "1px solid var(--border-primary)",
  };

  return (
    <SettingsLayout title="Astrology" description="Configure chart defaults and calculation preferences">
      <div className="grid gap-6 md:grid-cols-2">
        {/* Chart Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Chart Defaults
          </h3>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Zodiac System
              </label>
              <select
                value={settings.zodiac}
                onChange={(e) => handleChange("zodiac", e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              >
                <option value="Sidereal">Sidereal (Nirayana)</option>
                <option value="Tropical">Tropical (Sayana)</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Ayanamsa
              </label>
              <select
                value={settings.ayanamsa}
                onChange={(e) => handleChange("ayanamsa", e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              >
                <option value="Lahiri">Lahiri / Chitra Paksha</option>
                <option value="Raman">B.V. Raman</option>
                <option value="KP">Krishnamurti (KP)</option>
                <option value="Yukteshwar">Sri Yukteshwar</option>
                <option value="FaganBradley">Fagan-Bradley</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                House System
              </label>
              <select
                value={settings.houseSystem}
                onChange={(e) => handleChange("houseSystem", e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              >
                <option value="Whole Sign">Whole Sign (Rashi = Bhava)</option>
                <option value="Placidus">Placidus</option>
                <option value="Equal">Equal House</option>
                <option value="Sripati">Sripati / Porphyry</option>
                <option value="Koch">Koch</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Default Chart Style
              </label>
              <select
                value={settings.chartStyle}
                onChange={(e) => handleChange("chartStyle", e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              >
                <option value="North Indian">North Indian (Diamond)</option>
                <option value="South Indian">South Indian (Box)</option>
                <option value="East Indian">East Indian (Sun Chart)</option>
                <option value="Western">Western (Circular Wheel)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Calculation Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Calculation Rules
          </h3>
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Lunar Nodes (Rahu / Ketu)
              </label>
              <select
                value={settings.nodeType}
                onChange={(e) => handleChange("nodeType", e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              >
                <option value="True">True Nodes (Astronomical)</option>
                <option value="Mean">Mean Nodes (Averaged)</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Aspect Orb Tolerance
              </label>
              <input
                type="text"
                value={settings.aspectOrb}
                onChange={(e) => handleChange("aspectOrb", e.target.value)}
                placeholder="e.g. 8°"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              />
            </div>
          </div>
        </div>

        {/* Dasha Card */}
        <div className="rounded-2xl border p-6 md:col-span-2" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-4 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Dasha & Transits
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Default Dasha System
              </label>
              <select
                value={settings.defaultDasha}
                onChange={(e) => handleChange("defaultDasha", e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              >
                <option value="Vimshottari">Vimshottari (120 Years)</option>
                <option value="Ashtottari">Ashtottari (108 Years)</option>
                <option value="Yogini">Yogini (36 Years)</option>
                <option value="Chara">Jaimini Chara Dasha</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Transit Calculation Framework
              </label>
              <select
                value={settings.transitDefaults}
                onChange={(e) => handleChange("transitDefaults", e.target.value)}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                style={inputStyle}
              >
                <option value="Gochara">Gochara (Moon-based transit)</option>
                <option value="Jaimini">Jaimini Sign Transits</option>
                <option value="Ashtakavarga">Ashtakavarga Kakshya Transits</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {savedMessage && (
        <div
          className="mt-6 rounded-lg border p-3 text-sm"
          style={{
            borderColor: "var(--status-success)",
            color: "var(--status-success)",
            backgroundColor: "var(--bg-input)",
          }}
        >
          {savedMessage}
        </div>
      )}

      <div className="mt-8 flex items-center justify-end gap-3">
        <button
          type="button"
          onClick={handleReset}
          className="rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          style={{
            backgroundColor: "var(--obsidian-surface-elevated)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-primary)",
          }}
        >
          Reset to Defaults
        </button>
        <button
          type="button"
          onClick={handleSave}
          className="rounded-lg px-4 py-2 text-sm font-semibold"
          style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          Save Changes
        </button>
      </div>
    </SettingsLayout>
  );
}