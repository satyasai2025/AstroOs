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

  const [name, setName] = useState(initialData?.name ?? "Kunal");
  const [gender, setGender] = useState<"Male" | "Female" | "Unknown">(initialData?.gender ?? "Male");
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
  const [place, setPlace] = useState(initialData?.place ?? "Pune, Maharashtra, India");
  const [latitude, setLatitude] = useState(initialData?.latitude ?? 18.5204);
  const [longitude, setLongitude] = useState(initialData?.longitude ?? 73.8567);
  const [gmt, setGmt] = useState(initialData?.gmt ?? 5.5);
  const [dst, setDst] = useState(initialData?.dst ?? 0);
  const [question, setQuestion] = useState(
    initialData?.question ?? "kunal ka selection aaj job ke liye hoga ki nahi"
  );

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="flex w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-slate-700/80 bg-slate-900 shadow-2xl text-slate-100 animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <h2 className="text-lg font-semibold tracking-wide text-slate-100">
            Horary/Time Chart Data Entry
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition"
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
          <div className="w-full md:w-44 border-b md:border-b-0 md:border-r border-slate-800 bg-slate-950/50 p-3 space-y-1">
            {[
              { id: "birth", label: "Birth Details" },
              { id: "lineage", label: "Lineage" },
              { id: "settings", label: "Settings" },
              { id: "notes", label: "Notes" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                className={`w-full rounded-xl px-4 py-2.5 text-left text-sm font-medium transition ${
                  activeTab === tab.id
                    ? "bg-sky-500/15 text-sky-400 border border-sky-500/30"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Right Tab Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {activeTab === "birth" && (
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Name */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-3">
                  <label className="text-sm font-medium text-slate-300 md:text-right">
                    <span className="text-rose-400 mr-1">*</span>Name:
                  </label>
                  <div className="md:col-span-3">
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Enter native / querent name"
                      className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    />
                  </div>
                </div>

                {/* Gender */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-3">
                  <label className="text-sm font-medium text-slate-300 md:text-right">
                    <span className="text-rose-400 mr-1">*</span>Gender:
                  </label>
                  <div className="md:col-span-3 flex items-center space-x-6 text-sm text-slate-300">
                    {(["Male", "Female", "Unknown"] as const).map((g) => (
                      <label key={g} className="inline-flex items-center cursor-pointer space-x-2">
                        <input
                          type="radio"
                          name="gender"
                          value={g}
                          checked={gender === g}
                          onChange={() => setGender(g)}
                          className="h-4 w-4 text-sky-500 focus:ring-sky-500 bg-slate-800 border-slate-600"
                        />
                        <span>{g}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Horary Seed & Buttons */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-3">
                  <label className="text-sm font-medium text-slate-300 md:text-right">Horary:</label>
                  <div className="md:col-span-3 flex flex-wrap items-center gap-2">
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
                      className="w-24 rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={handleRandom}
                      className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 transition"
                    >
                      Random
                    </button>
                    <button
                      type="button"
                      onClick={handleSelect249}
                      className={`rounded-xl border px-3 py-1.5 text-xs font-medium transition ${
                        !isTimeChart && horarySystem === "kp_249"
                          ? "border-sky-500 bg-sky-500/20 text-sky-300"
                          : "border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
                      }`}
                    >
                      1-249
                    </button>
                    <button
                      type="button"
                      onClick={handleSelect2193}
                      className={`rounded-xl border px-3 py-1.5 text-xs font-medium transition ${
                        !isTimeChart && horarySystem === "kp_2193"
                          ? "border-sky-500 bg-sky-500/20 text-sky-300"
                          : "border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
                      }`}
                    >
                      1-2193
                    </button>
                    <button
                      type="button"
                      onClick={handleTimeChart}
                      className={`rounded-xl border px-3.5 py-1.5 text-xs font-semibold transition ${
                        isTimeChart
                          ? "border-sky-400 bg-sky-500 text-white shadow-md shadow-sky-500/25"
                          : "border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
                      }`}
                    >
                      Time Chart
                    </button>
                  </div>
                </div>

                {/* Date & Time */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-3">
                  <label className="text-sm font-medium text-slate-300 md:text-right">
                    <span className="text-rose-400 mr-1">*</span>Date:
                  </label>
                  <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <input
                      type="date"
                      required
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
                    />
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-slate-300">
                        <span className="text-rose-400 mr-1">*</span>Time:
                      </span>
                      <input
                        type="time"
                        step="1"
                        required
                        value={time}
                        onChange={(e) => setTime(e.target.value)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Place */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-3">
                  <label className="text-sm font-medium text-slate-300 md:text-right">
                    <span className="text-rose-400 mr-1">*</span>Place:
                  </label>
                  <div className="md:col-span-3">
                    <input
                      type="text"
                      required
                      value={place}
                      onChange={(e) => setPlace(e.target.value)}
                      placeholder="City, State, Country"
                      className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none"
                    />
                  </div>
                </div>

                {/* Coordinates & TZ */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-center gap-3">
                  <label className="text-sm font-medium text-slate-300 md:text-right">Lat / Lng:</label>
                  <div className="md:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <input
                      type="number"
                      step="any"
                      value={latitude}
                      onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                      placeholder="Lat (e.g. 18.52)"
                      className="rounded-xl border border-slate-700 bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-100 focus:border-sky-500 focus:outline-none"
                    />
                    <input
                      type="number"
                      step="any"
                      value={longitude}
                      onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                      placeholder="Lng (e.g. 73.85)"
                      className="rounded-xl border border-slate-700 bg-slate-800/80 px-2.5 py-1.5 text-xs text-slate-100 focus:border-sky-500 focus:outline-none"
                    />
                    <div className="flex items-center space-x-1">
                      <span className="text-[11px] text-slate-400">GMT:</span>
                      <input
                        type="number"
                        step="any"
                        value={gmt}
                        onChange={(e) => setGmt(parseFloat(e.target.value) || 5.5)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-2 py-1.5 text-xs text-slate-100 focus:border-sky-500 focus:outline-none"
                      />
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className="text-[11px] text-slate-400">DST:</span>
                      <input
                        type="number"
                        step="any"
                        value={dst}
                        onChange={(e) => setDst(parseFloat(e.target.value) || 0)}
                        className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-2 py-1.5 text-xs text-slate-100 focus:border-sky-500 focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Questions */}
                <div className="grid grid-cols-1 md:grid-cols-4 items-start gap-3">
                  <label className="text-sm font-medium text-slate-300 md:text-right pt-2">Questions:</label>
                  <div className="md:col-span-3">
                    <textarea
                      rows={2}
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Enter horary question (e.g. kunal ka selection aaj job ke liye hoga ki nahi)"
                      className="w-full rounded-xl border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    />
                  </div>
                </div>
              </form>
            )}

            {activeTab === "lineage" && (
              <div className="space-y-4 text-sm text-slate-300">
                <p className="text-slate-400">Optional Lineage and Astrological Family Details.</p>
                <div className="space-y-2">
                  <label className="block text-xs text-slate-400">Querent Gotra / Lineage:</label>
                  <input
                    type="text"
                    placeholder="Enter gotra or spiritual lineage"
                    className="w-full rounded-xl border border-slate-700 bg-slate-800 px-3.5 py-2 text-sm text-slate-100"
                  />
                </div>
              </div>
            )}

            {activeTab === "settings" && (
              <div className="space-y-4 text-sm text-slate-300">
                <p className="text-slate-400">Calculation Engine Settings</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                    <span className="text-xs font-semibold text-sky-400">Ayanamsa</span>
                    <p className="mt-1 text-xs text-slate-300">KP New / Krishnamurti Straight Line</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                    <span className="text-xs font-semibold text-emerald-400">House System</span>
                    <p className="mt-1 text-xs text-slate-300">Placidus (KP Standard Cusps)</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "notes" && (
              <div className="space-y-3">
                <label className="block text-sm font-medium text-slate-300">Consultation Notes:</label>
                <textarea
                  rows={6}
                  placeholder="Record consult notes, context, or feedback here..."
                  className="w-full rounded-xl border border-slate-700 bg-slate-800 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
                />
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end space-x-3 border-t border-slate-800 bg-slate-950/40 px-6 py-3.5">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700 transition"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => handleSubmit()}
            className="rounded-xl bg-sky-600 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-600/30 hover:bg-sky-500 transition"
          >
            Create
          </button>
          <button
            type="button"
            onClick={() => handleSubmit()}
            className="rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-500/25 hover:opacity-95 transition"
          >
            Create & Save
          </button>
        </div>
      </div>
    </div>
  );
}
