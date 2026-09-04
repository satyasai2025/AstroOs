"use client";

import React, { useState, useEffect } from "react";
import { BirthPlaceSearch } from "@/components/workflow/BirthPlaceSearch";
import type { PlaceResultResponse } from "@/lib/types";

export interface ChartFormData {
  name: string;
  dob: string;
  tob: string;
  citySearchText: string;
  lat: number;
  lon: number;
  saveToVault: boolean;
}

interface ChartInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ChartFormData) => void;
  initialData: {
    name: string;
    dob: string;
    tob: string;
    citySearchText: string;
    lat: number;
    lon: number;
  };
  theme?: "dark" | "light";
  title?: string;
}

export function ChartInputModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  theme = "light",
  title = "Create New Chart Profile",
}: ChartInputModalProps) {
  const [name, setName] = useState(initialData.name);
  const [dob, setDob] = useState(initialData.dob);
  const [tob, setTob] = useState(initialData.tob);
  const [citySearchText, setCitySearchText] = useState(initialData.citySearchText);
  const [lat, setLat] = useState(initialData.lat);
  const [lon, setLon] = useState(initialData.lon);
  const [saveToVault, setSaveToVault] = useState(false);
  const [showAdvancedCoords, setShowAdvancedCoords] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setName(initialData.name || "");
      setDob(initialData.dob || "");
      setTob(initialData.tob || "12:00");
      setCitySearchText(initialData.citySearchText || "");
      setLat(initialData.lat || 0);
      setLon(initialData.lon || 0);
      setSaveToVault(false);
      setShowAdvancedCoords(false);
      setValidationError(null);
    }
  }, [isOpen, initialData]);

  if (!isOpen) return null;

  const handlePlaceSelect = (place: PlaceResultResponse) => {
    setCitySearchText(place.display_name);
    setLat(place.latitude);
    setLon(place.longitude);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setValidationError("Please enter a name for the chart.");
      return;
    }
    if (!dob) {
      setValidationError("Please select the date of birth.");
      return;
    }
    if (lat < -90 || lat > 90) {
      setValidationError("Latitude must be between -90 and +90 degrees.");
      return;
    }
    if (lon < -180 || lon > 180) {
      setValidationError("Longitude must be between -180 and +180 degrees.");
      return;
    }

    setValidationError(null);
    onSubmit({
      name: name.trim(),
      dob,
      tob: tob || "12:00",
      citySearchText: citySearchText || "Custom Location",
      lat: Number(lat),
      lon: Number(lon),
      saveToVault,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div
        className={`w-full max-w-lg rounded-2xl shadow-2xl border p-6 transition-all ${
          theme === "light"
            ? "bg-white border-slate-200 text-slate-900"
            : "bg-slate-900 border-slate-800 text-slate-100"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center font-bold text-base">
              ✨
            </div>
            <div>
              <h2 className="text-base font-bold">{title}</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Enter birth parameters to load into the active consultation engine
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1.5 rounded-lg text-lg leading-none"
          >
            ✕
          </button>
        </div>

        {validationError && (
          <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 rounded-xl text-xs flex items-center gap-2">
            <span>⚠️</span>
            <span>{validationError}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Full Name */}
          <div>
            <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
              Full Name / Native Name <span className="text-amber-500">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Native Full Name / Client ID"
              className={`w-full border rounded-xl px-3 py-2 text-sm focus:border-amber-500 focus:outline-none transition ${
                theme === "light"
                  ? "bg-slate-50 border-slate-300 text-slate-900"
                  : "bg-slate-950 border-slate-800 text-white"
              }`}
            />
          </div>

          {/* DOB & TOB */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                Date of Birth <span className="text-amber-500">*</span>
              </label>
              <input
                type="date"
                required
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className={`w-full border rounded-xl px-3 py-2 text-sm focus:border-amber-500 focus:outline-none transition ${
                  theme === "light"
                    ? "bg-slate-50 border-slate-300 text-slate-900"
                    : "bg-slate-950 border-slate-800 text-white"
                }`}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                Time of Birth (Local)
              </label>
              <input
                type="time"
                value={tob}
                onChange={(e) => setTob(e.target.value)}
                className={`w-full border rounded-xl px-3 py-2 text-sm focus:border-amber-500 focus:outline-none transition ${
                  theme === "light"
                    ? "bg-slate-50 border-slate-300 text-slate-900"
                    : "bg-slate-950 border-slate-800 text-white"
                }`}
              />
            </div>
          </div>

          {/* Birth Place Search */}
          <div>
            <label className="block text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
              Birth Place (Global City Autocomplete)
            </label>
            <BirthPlaceSearch
              value={citySearchText}
              onChange={setCitySearchText}
              onSelect={handlePlaceSelect}
            />
            <div className="flex items-center justify-between mt-1.5 text-[11px] font-mono text-slate-500 dark:text-slate-400">
              <span>
                Lat: {isNaN(lat) ? "0.0000" : Number(lat).toFixed(4)}°, Lon:{" "}
                {isNaN(lon) ? "0.0000" : Number(lon).toFixed(4)}°
              </span>
              <button
                type="button"
                onClick={() => setShowAdvancedCoords(!showAdvancedCoords)}
                className="text-amber-500 hover:underline font-semibold"
              >
                {showAdvancedCoords ? "Hide Manual Coords" : "Edit Coords"}
              </button>
            </div>
          </div>

          {/* Manual Coords Drawer */}
          {showAdvancedCoords && (
            <div
              className={`grid grid-cols-2 gap-3 p-3 border rounded-xl animate-fadeIn ${
                theme === "light" ? "bg-slate-50 border-slate-200" : "bg-slate-950 border-slate-800"
              }`}
            >
              <div>
                <label className="block text-[10px] font-semibold mb-1 text-slate-600 dark:text-slate-400">
                  Manual Latitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={isNaN(lat) ? "" : lat}
                  onChange={(e) => {
                    const v = e.target.value;
                    setLat(v === "" ? 0 : parseFloat(v) || 0);
                  }}
                  className={`w-full border rounded-lg px-2.5 py-1 text-xs focus:border-amber-500 focus:outline-none ${
                    theme === "light"
                      ? "bg-white border-slate-300 text-slate-900"
                      : "bg-slate-900 border-slate-700 text-white"
                  }`}
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold mb-1 text-slate-600 dark:text-slate-400">
                  Manual Longitude
                </label>
                <input
                  type="number"
                  step="0.0001"
                  value={isNaN(lon) ? "" : lon}
                  onChange={(e) => {
                    const v = e.target.value;
                    setLon(v === "" ? 0 : parseFloat(v) || 0);
                  }}
                  className={`w-full border rounded-lg px-2.5 py-1 text-xs focus:border-amber-500 focus:outline-none ${
                    theme === "light"
                      ? "bg-white border-slate-300 text-slate-900"
                      : "bg-slate-900 border-slate-700 text-white"
                  }`}
                />
              </div>
            </div>
          )}

          {/* Save to Vault Checkbox */}
          <div
            className={`p-3 rounded-xl border flex items-center gap-3 cursor-pointer select-none transition ${
              saveToVault
                ? theme === "light"
                  ? "bg-amber-50 border-amber-300"
                  : "bg-amber-500/10 border-amber-500/40"
                : theme === "light"
                ? "bg-slate-50 border-slate-200"
                : "bg-slate-950/60 border-slate-800"
            }`}
            onClick={() => setSaveToVault(!saveToVault)}
          >
            <input
              type="checkbox"
              id="saveToVaultCheckbox"
              checked={saveToVault}
              onChange={(e) => setSaveToVault(e.target.checked)}
              className="w-4 h-4 text-amber-500 rounded border-slate-300 focus:ring-amber-400 cursor-pointer"
            />
            <label
              htmlFor="saveToVaultCheckbox"
              className="text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer"
            >
              <strong>Save chart to permanent vault</strong>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                If unchecked, data remains active in this session only and resets on refresh/logout.
              </p>
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className={`px-4 py-2 text-xs font-semibold rounded-xl border transition ${
                theme === "light"
                  ? "bg-white border-slate-300 text-slate-700 hover:bg-slate-50"
                  : "bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 text-xs font-bold bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-slate-950 rounded-xl shadow-lg transition transform hover:scale-[1.02]"
            >
              Apply Chart to Consultation
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
