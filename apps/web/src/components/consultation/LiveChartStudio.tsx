"use client";

import React, { useState, useEffect, useRef } from "react";

export interface ChartProfile {
  id: string;
  name: string;
  dob: string;        // YYYY-MM-DD
  tob: string;        // HH:MM
  cityName: string;
  latitude: number;
  longitude: number;
  timezone?: string;
  utcOffsetHours?: number;
  tag?: string;
}

interface LiveChartStudioProps {
  onLoadIntoConsultation: (profile: ChartProfile) => void;
  lang?: "hi" | "en";
}

const DEFAULT_PROFILES: ChartProfile[] = [
  {
    id: "canonical-alpha",
    name: "Narendra Modi",
    dob: "1950-09-17",
    tob: "11:00",
    cityName: "Vadnagar, Gujarat, India",
    latitude: 23.7833,
    longitude: 72.6333,
    timezone: "Asia/Kolkata",
    tag: "Benchmark",
  },
  {
    id: "canonical-beta",
    name: "Indira Gandhi",
    dob: "1917-11-19",
    tob: "23:11",
    cityName: "Allahabad, Uttar Pradesh, India",
    latitude: 25.4500,
    longitude: 81.8500,
    timezone: "Asia/Kolkata",
    tag: "Benchmark",
  },
  {
    id: "canonical-gamma",
    name: "Donald Trump",
    dob: "1946-06-14",
    tob: "10:54",
    cityName: "New York, USA",
    latitude: 40.6900,
    longitude: -73.8000,
    timezone: "America/New_York",
    tag: "Benchmark",
  },
  {
    id: "canonical-delta",
    name: "Amitabh Bachchan",
    dob: "1942-10-11",
    tob: "16:00",
    cityName: "Allahabad, Uttar Pradesh, India",
    latitude: 25.4500,
    longitude: 81.8500,
    timezone: "Asia/Kolkata",
    tag: "Benchmark",
  },
];

const RASHIS = [
  "Aries (मेष)", "Taurus (वृषभ)", "Gemini (मिथुन)", "Cancer (कर्क)",
  "Leo (सिंह)", "Virgo (कन्या)", "Libra (तुला)", "Scorpio (वृश्चिक)",
  "Sagittarius (धनु)", "Capricorn (मकर)", "Aquarius (कुम्भ)", "Pisces (मीन)"
];

export function LiveChartStudio({ onLoadIntoConsultation, lang = "en" }: LiveChartStudioProps) {
  // Form State
  const [name, setName] = useState("Narendra Modi");
  const [dob, setDob] = useState("1950-09-17");
  const [tob, setTob] = useState("11:00");
  const [cityName, setCityName] = useState("Vadnagar, Gujarat, India");
  const [latitude, setLatitude] = useState(23.7833);
  const [longitude, setLongitude] = useState(72.6333);
  const [timezoneStr, setTimezoneStr] = useState("Asia/Kolkata");

  // Geocoding Autocomplete State
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Chart Style State
  const [chartStyle, setChartStyle] = useState<"north" | "south">("north");

  // Saved Profiles in LocalStorage
  const [savedProfiles, setSavedProfiles] = useState<ChartProfile[]>(DEFAULT_PROFILES);
  const [isSavedToast, setIsSavedToast] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("astroos_saved_charts");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setSavedProfiles(parsed);
        }
      }
    } catch {
      // ignore
    }
  }, []);

  const saveCurrentToVault = () => {
    const newProfile: ChartProfile = {
      id: "chart-" + Date.now(),
      name: name.trim() || "Native Profile",
      dob,
      tob,
      cityName,
      latitude: Number(latitude) || 0,
      longitude: Number(longitude) || 0,
      timezone: timezoneStr,
      tag: "Custom",
    };
    const updated = [newProfile, ...savedProfiles.filter((p) => p.name !== newProfile.name)];
    setSavedProfiles(updated);
    try {
      localStorage.setItem("astroos_saved_charts", JSON.stringify(updated));
      setIsSavedToast(true);
      setTimeout(() => setIsSavedToast(false), 2500);
    } catch {
      // ignore
    }
  };

  const deleteProfile = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = savedProfiles.filter((p) => p.id !== id);
    setSavedProfiles(updated);
    try {
      localStorage.setItem("astroos_saved_charts", JSON.stringify(updated));
    } catch {
      // ignore
    }
  };

  const selectProfile = (p: ChartProfile) => {
    setName(p.name);
    setDob(p.dob);
    setTob(p.tob);
    setCityName(p.cityName);
    setLatitude(p.latitude);
    setLongitude(p.longitude);
    if (p.timezone) setTimezoneStr(p.timezone);
  };

  // Debounced City Search
  const handleCitySearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);

    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);

    if (val.trim().length < 2) {
      setSearchResults([]);
      setIsDropdownOpen(false);
      return;
    }

    setIsSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/geocode/search?query=${encodeURIComponent(val.trim())}`);
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data.results || []);
          setIsDropdownOpen(true);
        }
      } catch {
        // ignore
      } finally {
        setIsSearching(false);
      }
    }, 350);
  };

  const handleSelectLocation = async (item: any) => {
    setCityName(item.display_name);
    setLatitude(item.latitude);
    setLongitude(item.longitude);
    setSearchQuery(item.display_name);
    setIsDropdownOpen(false);

    // Resolve timezone
    try {
      const tzRes = await fetch(
        `/api/v1/geocode/timezone?latitude=${item.latitude}&longitude=${item.longitude}&local_date=${dob}`
      );
      if (tzRes.ok) {
        const tzData = await tzRes.json();
        if (tzData.timezone) setTimezoneStr(tzData.timezone);
      }
    } catch {
      // fallback
    }
  };

  const handleLoadClick = () => {
    onLoadIntoConsultation({
      id: "active-" + Date.now(),
      name: name.trim() || "Native Profile",
      dob,
      tob,
      cityName,
      latitude,
      longitude,
      timezone: timezoneStr,
    });
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 md:p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🌌</span>
            <h3 className="text-base md:text-lg font-bold bg-gradient-to-r from-amber-200 via-amber-400 to-cyan-300 bg-clip-text text-transparent">
              Live Chart Studio & Geocoding Autocomplete
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Search global cities, auto-resolve timezones, and load instantly into Shastric Consultation
          </p>
        </div>

        {/* Action Button: Load into Consultation */}
        <button
          onClick={handleLoadClick}
          className="px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-slate-950 font-black rounded-xl text-xs shadow-lg flex items-center justify-center gap-2 transition"
        >
          <span>⚡</span>
          <span>Load into Consultation Engine</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form & City Search */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              1. Birth Parameters
            </h4>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Alexander The Great"
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:border-amber-500 focus:outline-none text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs focus:border-amber-500 focus:outline-none text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Time of Birth</label>
                <input
                  type="time"
                  value={tob}
                  onChange={(e) => setTob(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>

            {/* City Autocomplete Search */}
            <div className="relative">
              <label className="block text-xs text-slate-400 mb-1">
                Birth Place (Auto-complete)
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Type city name (e.g. Varanasi, London, New York)..."
                  value={searchQuery ? searchQuery : cityName || ""}
                  onChange={handleCitySearchChange}
                  onFocus={() => searchQuery.length >= 2 && setIsDropdownOpen(true)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-3 pr-8 py-2 text-xs text-white focus:outline-none focus:border-amber-500"
                />
                {isSearching && (
                  <div className="absolute right-2.5 top-2.5 w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                )}
              </div>

              {/* Autocomplete Dropdown */}
              {isDropdownOpen && searchResults.length > 0 && (
                <div className="absolute z-20 mt-1 w-full bg-slate-900 border border-slate-700 rounded-xl shadow-2xl max-h-48 overflow-y-auto">
                  {searchResults.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleSelectLocation(item)}
                      className="px-3 py-2 text-xs text-slate-200 hover:bg-amber-500/20 hover:text-amber-300 cursor-pointer border-b border-slate-800/60 last:border-0"
                    >
                      <div className="font-semibold">{item.display_name}</div>
                      <div className="text-[10px] text-slate-500">
                        Lat: {Number(item.latitude || 0).toFixed(4)}, Lon: {Number(item.longitude || 0).toFixed(4)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Resolved Coordinates & Timezone Card */}
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800/80 grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                <div className="text-[10px] text-slate-500">Latitude</div>
                <div className="font-bold text-white text-xs">{Number(latitude || 0).toFixed(4)}°</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500">Longitude</div>
                <div className="font-bold text-white text-xs">{Number(longitude || 0).toFixed(4)}°</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500">Timezone</div>
                <div className="font-bold text-cyan-400 text-[11px] truncate">{timezoneStr || "UTC"}</div>
              </div>
            </div>

            {/* Save to Vault Button */}
            <button
              onClick={saveCurrentToVault}
              className={`w-full py-2 rounded-lg text-xs font-semibold transition flex items-center justify-center gap-1.5 ${
                isSavedToast
                  ? "bg-emerald-500 text-slate-950 font-bold shadow-md"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white"
              }`}
            >
              <span>{isSavedToast ? "✅" : "💾"}</span>
              <span>
                {isSavedToast
                  ? lang === "hi" ? "वॉल्ट में सुरक्षित हो गया!" : "Saved to Vault!"
                  : lang === "hi" ? "चार्ट वॉल्ट (My Charts) में सुरक्षित करें" : "Save to Chart Vault"}
              </span>
            </button>
          </div>
        </div>

        {/* Right Column: Chart Vault & Presets */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
                {lang === "hi" ? "2. चार्ट वॉल्ट (Saved Profiles)" : "2. Saved Chart Profiles"}
              </h4>
              <span className="text-[10px] text-slate-500">{savedProfiles.length} profiles</span>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {savedProfiles.map((p) => {
                const isSelected = p.dob === dob && p.tob === tob && p.latitude === latitude;
                return (
                  <div
                    key={p.id}
                    onClick={() => selectProfile(p)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition flex items-center justify-between ${
                      isSelected
                        ? "bg-amber-500/10 border-amber-500/50 text-amber-200 shadow-sm"
                        : "bg-slate-900/70 border-slate-800 text-slate-300 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{p.name}</span>
                        {p.tag && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-medium">
                            {p.tag}
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        📅 {p.dob} at {p.tob} • 📍 {p.cityName}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {p.tag === "Custom" && (
                        <button
                          onClick={(e) => deleteProfile(p.id, e)}
                          className="text-slate-600 hover:text-rose-400 p-1 text-xs"
                          title="Delete"
                        >
                          ✕
                        </button>
                      )}
                      <span className="text-[11px] font-bold text-amber-400">
                        {isSelected ? "✓ Active" : "Select →"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
