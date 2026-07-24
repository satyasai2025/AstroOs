/**
 * AstroOS — Literature & Yoga Rules Manager
 *
 * Unified CRUD interface for:
 * - Classical literature entries (BPHS, Saravali, etc.)
 * - Yoga rule definitions
 */

"use client";

import { useState } from "react";

interface LiteratureEntry {
  id: string;
  textSource: string;
  chapter?: string;
  verseNumber?: string;
  originalText: string;
  translation: string;
  tags: string[];
  createdAt: string;
}

interface YogaRuleEntry {
  id: string;
  name: string;
  description: string;
  ruleType: string;
  isActive: boolean;
  strengthModifier: number;
  createdAt: string;
}

const MOCK_LITERATURE: LiteratureEntry[] = [
  { id: "lit-001", textSource: "BPHS", chapter: "1", verseNumber: "1", originalText: "ṛṣyādyāḥ sūryādayaḥ sapta...", translation: "The seven sages begin with Surya...", tags: ["intro", "sages"], createdAt: "2026-01-10T00:00:00Z" },
  { id: "lit-002", textSource: "BPHS", chapter: "2", verseNumber: "5", originalText: "yatra yoge tato dṛṣṭiḥ...", translation: "Where there is yoga, look there...", tags: ["yoga", "interpretation"], createdAt: "2026-01-11T00:00:00Z" },
];

const MOCK_YOGA_RULES: YogaRuleEntry[] = [
  { id: "rule-001", name: "Sun-Moon Conjunction", description: "Sun and Moon in same house", ruleType: "planetary", isActive: true, strengthModifier: 1.5, createdAt: "2026-01-12T00:00:00Z" },
  { id: "rule-002", name: "Raja Yoga - Shasha", description: "Saturn in a kendra", ruleType: "composite", isActive: true, strengthModifier: 2.0, createdAt: "2026-01-13T00:00:00Z" },
];

export function LiteratureManager() {
  const [activeTab, setActiveTab] = useState<"literature" | "yoga">("literature");
  const [literature, setLiterature] = useState(MOCK_LITERATURE);
  const [yogaRules, setYogaRules] = useState(MOCK_YOGA_RULES);

  const toggleYogaRule = (id: string) => {
    setYogaRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, isActive: !r.isActive } : r))
    );
  };

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border-primary)] overflow-hidden">
      {/* Tab Navigation */}
      <div className="flex border-b border-[var(--border-primary)]">
        <button
          onClick={() => setActiveTab("literature")}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "literature"
              ? "text-[var(--text-primary)] border-b-2 border-[var(--accent)]"
              : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
          }`}
        >
          Classical Literature ({literature.length})
        </button>
        <button
          onClick={() => setActiveTab("yoga")}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "yoga"
              ? "text-[var(--text-primary)] border-b-2 border-[var(--accent)]"
              : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
          }`}
        >
          Yoga Rules ({yogaRules.length})
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === "literature" && (
          <div className="space-y-4">
            {literature.map((entry) => (
              <div
                key={entry.id}
                className="p-4 rounded-lg border border-[var(--border-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-[rgba(6,207,255,0.15)] text-[rgba(6,207,255,0.9)]">
                        {entry.textSource}
                      </span>
                      {entry.chapter && (
                        <span className="text-xs text-[var(--text-muted)]">
                          Ch. {entry.chapter}, V. {entry.verseNumber || "?"}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-[var(--text-secondary)] mb-2">{entry.originalText}</p>
                    <p className="text-sm text-[var(--text-primary)] italic">{entry.translation}</p>
                    <div className="flex items-center gap-2 mt-2">
                      {entry.tags.map((tag) => (
                        <span key={tag} className="px-1.5 py-0.5 text-xs bg-[var(--bg-input)] text-[var(--text-secondary)] rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {literature.length === 0 && (
              <div className="p-8 text-center text-[var(--text-muted)]">
                No literature entries yet. Add your first sloka.
              </div>
            )}
          </div>
        )}

        {activeTab === "yoga" && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border-primary)] bg-[var(--bg-card-hover)]">
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Name</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Type</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Strength</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--text-muted)] uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-primary)]">
                {yogaRules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-[var(--bg-card-hover)] transition-colors">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-[var(--text-primary)]">{rule.name}</p>
                        <p className="text-xs text-[var(--text-muted)]">{rule.description}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 text-xs bg-[var(--bg-input)] text-[var(--text-secondary)] rounded">
                        {rule.ruleType}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{rule.strengthModifier}x</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                        rule.isActive ? "bg-emerald-400/15 text-emerald-300" : "bg-slate-400/15 text-slate-300"
                      }`}>
                        {rule.isActive ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleYogaRule(rule.id)}
                        className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                          rule.isActive
                            ? "bg-slate-400/15 text-slate-300 hover:bg-slate-400/25"
                            : "bg-emerald-400/15 text-emerald-300 hover:bg-emerald-400/25"
                        }`}
                      >
                        {rule.isActive ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {yogaRules.length === 0 && (
              <div className="p-8 text-center text-[var(--text-muted)]">
                No yoga rules defined yet.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
