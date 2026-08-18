"use client";

import { SettingsLayout } from "@/components/settings/SettingsLayout";

export default function AboutSettingsPage() {
  return (
    <SettingsLayout title="About" description="AstroOS version and licensing information">
      <div className="space-y-6">
        {/* App Info Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <div className="flex items-center gap-4 mb-6">
            <div
              className="flex h-16 w-16 items-center justify-center rounded-2xl text-2xl font-bold"
              style={{
                background: "linear-gradient(135deg, var(--accent), var(--violet-400))",
                color: "var(--accent-text)",
              }}
            >
              ॐ
            </div>
            <div>
              <h3 className="text-xl font-bold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
                AstroOS
              </h3>
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                Vedic Research Platform
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b" style={{ borderColor: "var(--border-primary)" }}>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>Version</span>
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>2.0</span>
            </div>
            <div className="flex items-center justify-between py-3 border-b" style={{ borderColor: "var(--border-primary)" }}>
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>Swiss Ephemeris</span>
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Included</span>
            </div>
          </div>
        </div>

        {/* Resources Card */}
        <div className="rounded-2xl border p-6" style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-card)" }}>
          <h3 className="mb-6 text-lg font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-outfit)" }}>
            Resources
          </h3>

          <div className="space-y-3">
            <a
              href="/knowledge"
              className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:border-[var(--accent)]"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-primary-soft)", color: "var(--accent)" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Documentation &amp; Knowledge Base</p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>Explore classical references, texts, and user guides</p>
                </div>
              </div>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
                <path d="M7 17l9.2-9.2M17 17V7H7" />
              </svg>
            </a>

            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between rounded-lg border p-4 transition-colors hover:border-[var(--accent)]"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-primary-soft)", color: "var(--accent)" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>GitHub Repository</p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>View open source code and contribution guidelines</p>
                </div>
              </div>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
                <path d="M7 17l9.2-9.2M17 17V7H7" />
              </svg>
            </a>

            <div
              className="flex items-center justify-between rounded-lg border p-4"
              style={{ borderColor: "var(--border-primary)", backgroundColor: "var(--bg-input)" }}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: "var(--obsidian-accent-primary-soft)", color: "var(--accent)" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Software License</p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>MIT License • All rights reserved</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SettingsLayout>
  );
}