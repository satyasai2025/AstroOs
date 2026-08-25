"use client";

import React, { useState } from "react";

export interface HoraryFormData {
  name: string;
  gender: "Male" | "Female" | "Unknown";
  horaryNumber: number | null;
  horarySystem: "kp_249" | "kp_2193";
  isTimeChart: boolean;
  date: string;
  time: string;
  place: string;
  latitude: number;
  longitude: number;
  gmt: number;
  dst: number;
  question: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: HoraryFormData) => void;
  initialData?: Partial<HoraryFormData>;
}

export function HoraryDataEntryModal({ isOpen, onClose, onSubmit, initialData }: Props) {
  const [activeTab, setActiveTab] = useState<"birth" | "lineage" | "settings" | "notes">("birth");

  const [name, setName] = useState(initialData?.name ?? "");
  const [gender, setGender] = useState<"Male" | "Female" | "Unknown">(initialData?.gender ?? "Unknown");
  const [horaryInput, setHoraryInput] = useState<string>(
    initialData?.horaryNumber ? String(initialData.horaryNumber) : ""
  );
  const [horarySystem, setHorarySystem] = useState<"kp_249" | "kp_2193">(initialData?.horarySystem ?? "kp_249");
  const [isTimeChart, setIsTimeChart] = useState(initialData?.isTimeChart ?? true);

  const now = new Date();
  const defaultDate = now.toISOString().split("T")[0];
  const defaultTime = now.toTimeString().split(" ")[0];

  const [date, setDate] = useState(initialData?.date ?? defaultDate);
  const [time, setTime] = useState(initialData?.time ?? defaultTime);
  const [place, setPlace] = useState(initialData?.place ?? "New Delhi, Delhi, India");
  const [latitude, setLatitude] = useState(initialData?.latitude ?? 28.6139);
  const [longitude, setLongitude] = useState(initialData?.longitude ?? 77.2090);
  const [gmt, setGmt] = useState(initialData?.gmt ?? 5.5);
  const [dst, setDst] = useState(initialData?.dst ?? 0);
  const [question, setQuestion] = useState(initialData?.question ?? "");

  if (!isOpen) return null;

  const handleRandom = () => {
    const max = horarySystem === "kp_2193" ? 2193 : 249;
    const rnd = Math.floor(Math.random() * max) + 1;
    setHoraryInput(String(rnd));
    setIsTimeChart(false);
  };

  const handleSelect249 = () => {
    setHorarySystem("kp_249");
    const num = parseInt(horaryInput, 10);
    if (!num || num > 249) {
      setHoraryInput("1");
    }
    setIsTimeChart(false);
  };

  const handleSelect2193 = () => {
    setHorarySystem("kp_2193");
    const num = parseInt(horaryInput, 10);
    if (!num || num > 2193) {
      setHoraryInput("1");
    }
    setIsTimeChart(false);
  };

  const handleTimeChart = () => {
    setIsTimeChart(true);
    setHoraryInput("");
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const hNum = !isTimeChart && horaryInput.trim() ? parseInt(horaryInput.trim(), 10) : null;
    onSubmit({
      name,
      gender,
      horaryNumber: hNum && !isNaN(hNum) ? hNum : null,
      horarySystem,
      isTimeChart,
      date,
      time,
      place,
      latitude,
      longitude,
      gmt,
      dst,
      question,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
      <div
        className="obsidian-card relative flex w-full max-w-3xl flex-col overflow-hidden rounded-2xl border shadow-2xl animate-in fade-in zoom-in-95 duration-200"
        style={{ backgroundColor: "var(--obsidian-surface-elevated, #0f172a)", borderColor: "var(--border-primary)" }}
      >
        {/* Modal Header */}
        <div
          className="flex items-center justify-between border-b px-6 py-4"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <div className="flex items-center gap-2.5">
            <span className="text-xl">🔮</span>
            <h2 className="text-base font-bold" style={{ color: "var(--text-primary)" }}>
              Custom Horary (Prashna) Query Entry
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 transition hover:opacity-70"
            style={{ color: "var(--text-muted)" }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex flex-col md:flex-row min-h-[460px]">
          {/* Left Vertical Tabs */}
          <div
            className="w-full md:w-44 border-b md:border-b-0 md:border-r p-3 space-y-1"
            style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}
          >
            {[
              { id: "birth", label: "Query Details" },
              { id: "lineage", label: "Lineage / Context" },
              { id: "settings", label: "Settings" },
              { id: "notes", label: "Notes" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className="w-full rounded-xl px-4 py-2.5 text-left text-xs font-semibold transition"
                style={{
                  backgroundColor: activeTab === tab.id ? "rgba(6,182,212,0.15)" : "transparent",
                  color: activeTab === tab.id ? "#06b6d4" : "var(--text-muted)",
                  border: activeTab === tab.id ? "1px solid rgba(6,182,212,0.3)" : "1px solid transparent",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Right Tab Content */}
          <div className="flex-1 p-6 overflow-y-auto" style={{ backgroundColor: "var(--bg-card)" }}>
            {activeTab === "birth" && (
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Question */}
                <div className="space-y-1">
                  <label className="block text-xs font-bold uppercase tracking-wider" style={{ color: "var(--text-primary)" }}>
                    <span className="text-cyan-400 mr-1">*</span>Prashna Question:
                  </label>
                  <textarea
                    rows={2}
                    required
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Enter your specific question (e.g. Will I get the promotion this month?)"
                    className="obsidian-input w-full text-xs"
                  />
                </div>

                {/* Name & Gender */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      Querent Name (Optional):
                    </label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Querent name"
                      className="obsidian-input w-full text-xs"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      Gender:
                    </label>
                    <div className="flex items-center gap-4 pt-1.5">
                      {(["Male", "Female", "Unknown"] as const).map((g) => (
                        <label key={g} className="inline-flex items-center cursor-pointer gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                          <input
                            type="radio"
                            name="gender"
                            value={g}
                            checked={gender === g}
                            onChange={() => setGender(g)}
                            className="accent-cyan-400"
                          />
                          <span>{g}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Horary Seed & Buttons */}
                <div className="space-y-2 pt-2 border-t" style={{ borderColor: "var(--border-primary)" }}>
                  <label className="block text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                    Horary Seed Selection:
                  </label>
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="number"
                      min={1}
                      max={horarySystem === "kp_2193" ? 2193 : 249}
                      value={horaryInput}
                      onChange={(e) => {
                        setHoraryInput(e.target.value);
                        setIsTimeChart(false);
                      }}
                      placeholder={horarySystem === "kp_2193" ? "1-2193" : "1-249"}
                      className="obsidian-input w-24 text-xs font-mono font-bold text-cyan-400"
                    />
                    <button
                      type="button"
                      onClick={handleRandom}
                      className="rounded-lg border px-3 py-1.5 text-xs font-bold transition hover:bg-cyan-500/10"
                      style={{ borderColor: "var(--border-primary)", color: "var(--text-secondary)" }}
                    >
                      🎲 Random
                    </button>
                    <button
                      type="button"
                      onClick={handleSelect249}
                      className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition ${
                        !isTimeChart && horarySystem === "kp_249"
                          ? "border-cyan-500 bg-cyan-500/20 text-cyan-300"
                          : "border-white/10 text-slate-400 hover:bg-white/5"
                      }`}
                    >
                      1–249
                    </button>
                    <button
                      type="button"
                      onClick={handleSelect2193}
                      className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition ${
                        !isTimeChart && horarySystem === "kp_2193"
                          ? "border-cyan-500 bg-cyan-500/20 text-cyan-300"
                          : "border-white/10 text-slate-400 hover:bg-white/5"
                      }`}
                    >
                      1–2193
                    </button>
                    <button
                      type="button"
                      onClick={handleTimeChart}
                      className={`rounded-lg border px-3.5 py-1.5 text-xs font-bold transition ${
                        isTimeChart
                          ? "border-cyan-400 bg-cyan-500/20 text-cyan-300"
                          : "border-white/10 text-slate-400 hover:bg-white/5"
                      }`}
                    >
                      ⏱️ Time Chart (Now)
                    </button>
                  </div>
                </div>

                {/* Date & Time */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      Query Date:
                    </label>
                    <input
                      type="date"
                      required
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      className="obsidian-input w-full text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                      Query Time:
                    </label>
                    <input
                      type="time"
                      step="1"
                      required
                      value={time}
                      onChange={(e) => setTime(e.target.value)}
                      className="obsidian-input w-full text-xs"
                    />
                  </div>
                </div>

                {/* Place */}
                <div className="space-y-1">
                  <label className="block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                    Query Location (City, Country):
                  </label>
                  <input
                    type="text"
                    required
                    value={place}
                    onChange={(e) => setPlace(e.target.value)}
                    placeholder="City, State, Country"
                    className="obsidian-input w-full text-xs"
                  />
                </div>

                {/* Coordinates & TZ */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>Latitude</span>
                    <input
                      type="number"
                      step="any"
                      value={latitude}
                      onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                      className="obsidian-input text-xs w-full"
                    />
                  </div>
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>Longitude</span>
                    <input
                      type="number"
                      step="any"
                      value={longitude}
                      onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                      className="obsidian-input text-xs w-full"
                    />
                  </div>
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>GMT Offset</span>
                    <input
                      type="number"
                      step="any"
                      value={gmt}
                      onChange={(e) => setGmt(parseFloat(e.target.value) || 5.5)}
                      className="obsidian-input text-xs w-full"
                    />
                  </div>
                  <div>
                    <span className="block text-[10px]" style={{ color: "var(--text-muted)" }}>DST</span>
                    <input
                      type="number"
                      step="any"
                      value={dst}
                      onChange={(e) => setDst(parseFloat(e.target.value) || 0)}
                      className="obsidian-input text-xs w-full"
                    />
                  </div>
                </div>
              </form>
            )}

            {activeTab === "lineage" && (
              <div className="space-y-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                <p style={{ color: "var(--text-muted)" }}>Optional Lineage and Astrological Context.</p>
                <div className="space-y-2">
                  <label className="block text-xs" style={{ color: "var(--text-muted)" }}>Querent Gotra / Spiritual Lineage:</label>
                  <input
                    type="text"
                    placeholder="Enter gotra or spiritual lineage"
                    className="obsidian-input w-full text-xs"
                  />
                </div>
              </div>
            )}

            {activeTab === "settings" && (
              <div className="space-y-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                <p style={{ color: "var(--text-muted)" }}>Calculation Engine Settings</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
                    <span className="text-xs font-bold text-cyan-400">Ayanamsa</span>
                    <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>KP New / Krishnamurti Straight Line (Lahiri)</p>
                  </div>
                  <div className="rounded-xl border p-3" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-primary)" }}>
                    <span className="text-xs font-bold text-emerald-400">House System</span>
                    <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>Placidus (KP Standard Cusps)</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "notes" && (
              <div className="space-y-3">
                <label className="block text-xs font-bold" style={{ color: "var(--text-primary)" }}>Consultation Notes:</label>
                <textarea
                  rows={6}
                  placeholder="Record consult notes, context, or feedback here..."
                  className="obsidian-input w-full text-xs"
                />
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div
          className="flex items-center justify-between border-t px-6 py-3.5"
          style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}
        >
          <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
            ⚡ KP Placidus Cusps &amp; Ruling Planets
          </span>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="obsidian-btn-secondary text-xs px-4 py-2"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => handleSubmit()}
              className="obsidian-btn-primary text-xs px-5 py-2 font-bold"
              style={{ backgroundColor: "var(--obsidian-accent-secondary, #06b6d4)", color: "#000" }}
            >
              Cast Prashna Chart →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
