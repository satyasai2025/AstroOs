"use client";

import React, { useState } from "react";

export function BTRMethodologyGuide() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"workflow" | "methods" | "events" | "faq">("workflow");

  return (
    <div style={{ margin: "16px 0" }}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "8px 16px",
          background: "linear-gradient(135deg, #1e3a8a, #2563eb)",
          color: "#ffffff",
          border: "1px solid #3b82f6",
          borderRadius: "8px",
          fontSize: "13px",
          fontWeight: 600,
          cursor: "pointer",
          boxShadow: "0 2px 8px rgba(37, 99, 235, 0.25)",
          transition: "all 0.2s ease",
        }}
      >
        <span style={{ fontSize: "16px" }}>📘</span>
        <span>{isOpen ? "Hide BTR Guide & Methodology" : "How to Use: BTR Guide & Methodology"}</span>
      </button>

      {/* Expandable Guide Card */}
      {isOpen && (
        <div
          style={{
            marginTop: "12px",
            background: "#0f172a",
            border: "1.5px solid #1e293b",
            borderRadius: "12px",
            padding: "20px",
            color: "#e2e8f0",
            boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
          }}
        >
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #1e293b", paddingBottom: "12px", marginBottom: "16px" }}>
            <div>
              <h3 style={{ margin: 0, fontSize: "18px", color: "#f8fafc", fontWeight: 700 }}>
                🧭 Birth Time Rectification (BTR) — Practical Guide & Rules
              </h3>
              <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                Scientific Krishnamurti Paddhati (KP) and Bayesian Event reverse-engineering methods.
              </p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                fontSize: "18px",
                cursor: "pointer",
                padding: "4px 8px",
              }}
            >
              ✕
            </button>
          </div>

          {/* Navigation Tabs */}
          <div style={{ display: "flex", gap: "8px", marginBottom: "16px", flexWrap: "wrap" }}>
            {[
              { id: "workflow", label: "🚀 3-Step Quickstart" },
              { id: "methods", label: "🔬 4 Core KP Methods" },
              { id: "events", label: "📊 Life Events & House Matrix" },
              { id: "faq", label: "❓ Expert Tips & FAQ" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 600,
                  border: activeTab === tab.id ? "1px solid #3b82f6" : "1px solid #1e293b",
                  background: activeTab === tab.id ? "rgba(59, 130, 246, 0.2)" : "#1e293b",
                  color: activeTab === tab.id ? "#60a5fa" : "#cbd5e1",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab 1: Workflow */}
          {activeTab === "workflow" && (
            <div style={{ lineHeight: 1.6, fontSize: "13px" }}>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                  gap: "12px",
                  marginBottom: "16px",
                }}
              >
                <div style={{ background: "#1e293b", padding: "14px", borderRadius: "8px", borderLeft: "4px solid #3b82f6" }}>
                  <div style={{ fontWeight: 700, color: "#60a5fa", marginBottom: "4px" }}>Step 1: Set Base Time & Window</div>
                  <p style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                    Enter the reported birth date, time, and coordinates. Set a search window (e.g. ±15 mins for hospital records, ±1 hr for approximate times).
                  </p>
                </div>

                <div style={{ background: "#1e293b", padding: "14px", borderRadius: "8px", borderLeft: "4px solid #f59e0b" }}>
                  <div style={{ fontWeight: 700, color: "#fbbf24", marginBottom: "4px" }}>Step 2: Add 2-3 Verified Past Events</div>
                  <p style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                    Add key landmark dates: <strong>Marriage</strong>, <strong>First Job / Major Promotion</strong>, <strong>Child Birth</strong>, or <strong>Relocation</strong>.
                  </p>
                </div>

                <div style={{ background: "#1e293b", padding: "14px", borderRadius: "8px", borderLeft: "4px solid #10b981" }}>
                  <div style={{ fontWeight: 700, color: "#34d399", marginBottom: "4px" }}>Step 3: Review High-Score Candidates</div>
                  <p style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                    The engine scans every 60 seconds, tests Dasha lords and Cuspal Sub-Lords, and highlights the candidate with the highest posterior probability.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: 4 Core KP Methods */}
          {activeTab === "methods" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "13px", lineHeight: 1.6 }}>
              <div style={{ background: "#1e293b", padding: "12px 14px", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 4px 0", color: "#38bdf8" }}>1. 👦/👧 Gender & Sub-Lord Polarity Verification</h4>
                <p style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                  In KP, the 1st Cusp (Lagna) Sub-Sub-Lord (SSL) reflects the native’s biological gender through sign and planetary polarity. If a female native’s reported time yields a purely male Lagna SSL, the birth time is shifted by ±1 to 3 minutes to the nearest feminine sub-lord.
                </p>
              </div>

              <div style={{ background: "#1e293b", padding: "12px 14px", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 4px 0", color: "#38bdf8" }}>2. 🪐 Ruling Planets (RP) Alignment</h4>
                <p style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                  The Ruling Planets at the moment of birth (or at the moment of divine inquiry) are: <strong>Day Lord</strong>, <strong>Moon Sign Lord</strong>, <strong>Moon Star Lord</strong>, <strong>Lagna Sign Lord</strong>, and <strong>Lagna Star Lord</strong>. The true birth ascendant’s star/sub-lord must be strongly connected with these Ruling Planets.
                </p>
              </div>

              <div style={{ background: "#1e293b", padding: "12px 14px", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 4px 0", color: "#38bdf8" }}>3. ☀️/🌙 Rule of Origin (Fruitful Cusps from 9th House)</h4>
                <p style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                  Sun (Father) and Moon (Mother) are fruitful indicators (FIPs). Counting 2, 5, 11 (fruitful houses) from the 9th cusp yields the <strong>10th, 1st, and 7th cusps</strong> of the native. Sun and Moon must connect with the Star Lord, Sub Lord, or Sub-Sub Lord of cusps 1, 7, or 10. Sub-sub lords change every 2m 40s to 8m 48s, allowing micro-second rectification.
                </p>
              </div>

              <div style={{ background: "#1e293b", padding: "12px 14px", borderRadius: "8px" }}>
                <h4 style={{ margin: "0 0 4px 0", color: "#38bdf8" }}>4. 🎯 Event-Based Dasha & Transit Reverse-Matching</h4>
                <p style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                  The gold standard of rectification: Each past milestone event is cross-referenced against the candidate’s operating Vimshottari Mahadasha, Bhukti, Antara, and relevant Cuspal Sub-Lords. The candidate time where all events align with strong signification receives the highest confidence score.
                </p>
              </div>
            </div>
          )}

          {/* Tab 3: Event & House Matrix */}
          {activeTab === "events" && (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                <thead>
                  <tr style={{ background: "#1e293b", color: "#94a3b8", borderBottom: "1px solid #334155" }}>
                    <th style={{ padding: "8px 10px" }}>Life Event</th>
                    <th style={{ padding: "8px 10px" }}>Primary Cusp</th>
                    <th style={{ padding: "8px 10px" }}>KP Favorable Houses</th>
                    <th style={{ padding: "8px 10px" }}>Detrimental Houses</th>
                    <th style={{ padding: "8px 10px" }}>Typical Significance</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { event: "💍 Marriage / Relationship", cusp: "7th Cusp", fav: "2, 7, 11", det: "1, 6, 10, 12", weight: "High (1.5x)" },
                    { event: "💼 Career Rise / First Job", cusp: "10th / 6th Cusp", fav: "2, 6, 10, 11", det: "5, 8, 12", weight: "High (1.2x)" },
                    { event: "👶 Child Birth / Progeny", cusp: "5th Cusp", fav: "2, 5, 11", det: "1, 4, 10", weight: "High (1.3x)" },
                    { event: "🏠 Property / Vehicle Purchase", cusp: "4th Cusp", fav: "4, 11, 12", det: "3, 6, 8", weight: "Medium (1.0x)" },
                    { event: "✈️ Foreign Travel / Relocation", cusp: "12th / 9th Cusp", fav: "3, 9, 12", det: "4, 11", weight: "Medium (1.0x)" },
                    { event: "🩺 Surgery / Acute Illness", cusp: "6th / 8th Cusp", fav: "6, 8, 12", det: "1, 5, 11", weight: "High (1.2x)" },
                  ].map((row, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #1e293b" }}>
                      <td style={{ padding: "8px 10px", fontWeight: 600, color: "#f1f5f9" }}>{row.event}</td>
                      <td style={{ padding: "8px 10px", color: "#38bdf8" }}>{row.cusp}</td>
                      <td style={{ padding: "8px 10px", color: "#4ade80", fontWeight: 600 }}>{row.fav}</td>
                      <td style={{ padding: "8px 10px", color: "#f87171" }}>{row.det}</td>
                      <td style={{ padding: "8px 10px", color: "#e2e8f0" }}>{row.weight}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: FAQ */}
          {activeTab === "faq" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px", lineHeight: 1.5 }}>
              <div>
                <strong style={{ color: "#fbbf24" }}>Q: What if hospital records say 10:30 AM but don't specify seconds?</strong>
                <p style={{ margin: "2px 0 0 0", color: "#cbd5e1" }}>
                  A: Set the base time to 10:30:00 UTC and a search window of ±15 minutes with 60-second steps. The engine will evaluate all 30 candidate charts.
                </p>
              </div>
              <div>
                <strong style={{ color: "#fbbf24" }}>Q: How many past events should I provide?</strong>
                <p style={{ margin: "2px 0 0 0", color: "#cbd5e1" }}>
                  A: At least 2 events from different domains (e.g. Marriage + Career milestone) give high statistical confidence (&gt;90% posterior probability).
                </p>
              </div>
              <div>
                <strong style={{ color: "#fbbf24" }}>Q: Why did the Lagna Sub-Lord change by moving only 40 seconds?</strong>
                <p style={{ margin: "2px 0 0 0", color: "#cbd5e1" }}>
                  A: KP Sub-lords span between 40 arcminutes to 2 degrees. Near the boundary of a sub-arc, a shift of just 30-60 seconds can alter the Sub-Lord or Sub-Sub-Lord.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
