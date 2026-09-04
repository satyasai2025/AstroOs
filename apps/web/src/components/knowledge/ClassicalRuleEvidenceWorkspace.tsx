"use client";

import { useState, useEffect, useMemo } from "react";
import {
  fetchClassicalRules,
  evaluateChartRuleEvidence,
  type ClassicalRuleExploreItem,
  type RuleEvidenceChain,
} from "@/lib/classicalRuleEvidence";

const TRADITIONS = [
  { id: "all", label: "All Traditions" },
  { id: "Parashari", label: "Parashari (BPHS)" },
  { id: "General Classical", label: "Saravali (Kalyanavarma)" },
  { id: "Jaimini", label: "Jaimini Upadesha Sutras" },
  { id: "Varahamihira", label: "Varahamihira (Brihat Jataka)" },
  { id: "Mantreswara", label: "Mantreswara (Phaladeepika)" },
];

const CATEGORIES = [
  { id: "all", label: "All Categories" },
  { id: "Raja Yoga", label: "Raja Yogas" },
  { id: "Pancha Mahapurusha", label: "Pancha Mahapurusha" },
  { id: "Jaimini Karakamsha", label: "Jaimini Karakamsha" },
];

// Default sample research chart with prominent yogas for demonstration
const SAMPLE_RESEARCH_CHART = {
  id: "DEMO-CHART-VEDIC-01",
  subject_name: "Classical Vedic Benchmark Chart",
  planets: [
    { planet: "Jupiter", house_number: 1, rashi: "Cancer", dignity: "exalted", is_combust: false, sidereal_longitude: 104.5 },
    { planet: "Moon", house_number: 4, rashi: "Libra", dignity: "neutral", is_combust: false, sidereal_longitude: 195.2 },
    { planet: "Sun", house_number: 10, rashi: "Aries", dignity: "exalted", is_combust: false, sidereal_longitude: 15.8 },
    { planet: "Mercury", house_number: 10, rashi: "Aries", dignity: "neutral", is_combust: false, sidereal_longitude: 22.4 },
    { planet: "Mars", house_number: 10, rashi: "Capricorn", dignity: "exalted", is_combust: false, sidereal_longitude: 284.1 },
    { planet: "Venus", house_number: 11, rashi: "Taurus", dignity: "own_sign", is_combust: false, sidereal_longitude: 48.0 },
    { planet: "Saturn", house_number: 7, rashi: "Capricorn", dignity: "own_sign", is_combust: false, sidereal_longitude: 278.3 },
    { planet: "Rahu", house_number: 6, rashi: "Sagittarius", dignity: "neutral", is_combust: false, sidereal_longitude: 254.0 },
    { planet: "Ketu", house_number: 12, rashi: "Gemini", dignity: "neutral", is_combust: false, sidereal_longitude: 74.0 },
  ],
};

export function ClassicalRuleEvidenceWorkspace() {
  const [rules, setRules] = useState<ClassicalRuleExploreItem[]>([]);
  const [selectedTradition, setSelectedTradition] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedRuleId, setSelectedRuleId] = useState<string>("BPHS-YOGA-GAJAKESARI");

  const [evaluationMode, setEvaluationMode] = useState<"catalog" | "chart">("chart");
  const [evidenceChains, setEvidenceChains] = useState<RuleEvidenceChain[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load canonical rules and initial chart evaluation
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const [rulesRes, evalRes] = await Promise.all([
          fetchClassicalRules(),
          evaluateChartRuleEvidence(SAMPLE_RESEARCH_CHART),
        ]);
        setRules(rulesRes.rules);
        setEvidenceChains(evalRes.evidence_chains);
        if (rulesRes.rules.length > 0) {
          setSelectedRuleId(rulesRes.rules[0].rule_id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load classical rule registry.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredRules = useMemo(() => {
    return rules.filter((r) => {
      const matchTradition =
        selectedTradition === "all" || r.tradition.toLowerCase().includes(selectedTradition.toLowerCase());
      const matchCategory =
        selectedCategory === "all" || r.category.toLowerCase().includes(selectedCategory.toLowerCase());
      const matchSearch =
        !searchQuery ||
        r.rule_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.book_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.brief_description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.sanskrit_preview.toLowerCase().includes(searchQuery.toLowerCase());
      return matchTradition && matchCategory && matchSearch;
    });
  }, [rules, selectedTradition, selectedCategory, searchQuery]);

  const activeEvidenceChain = useMemo(() => {
    return evidenceChains.find((c) => c.rule_id === selectedRuleId) || null;
  }, [evidenceChains, selectedRuleId]);

  const activeRuleSummary = useMemo(() => {
    return rules.find((r) => r.rule_id === selectedRuleId) || null;
  }, [rules, selectedRuleId]);

  return (
    <div className="space-y-8" data-testid="classical-rule-evidence-workspace">
      {/* 1. Header & Authenticity Guarantee */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
              CLASSICAL EVIDENCE ENGINE
            </span>
            <span className="text-xs text-slate-400 font-medium">• BPHS • Saravali • Jaimini • Brihat Jataka</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            <span className="text-amber-700">📜</span> Classical Rule Evidence &amp; Knowledge Graph Engine
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl font-medium">
            Deterministic 5-stage classical evidence chains connecting canonical Sanskrit literature directly to computed 
            chart conditions with zero invented citations or rules.
          </p>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-xl border border-slate-200 shadow-xs">
          <button
            onClick={() => setEvaluationMode("chart")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
              evaluationMode === "chart"
                ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                : "text-slate-400 hover:text-slate-900"
            }`}
          >
            <span>🎯</span> 5-Step Chart Evidence
          </button>
          <button
            onClick={() => setEvaluationMode("catalog")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition flex items-center gap-1.5 ${
              evaluationMode === "catalog"
                ? "bg-white text-slate-900 shadow-sm border border-slate-200"
                : "text-slate-400 hover:text-slate-900"
            }`}
          >
            <span>📚</span> Classical Literature Corpus
          </button>
        </div>
      </div>

      {/* 2. Classical Citation Integrity Seal */}
      <div className="rounded-xl p-4 bg-emerald-50 border border-emerald-200 flex items-start gap-3 shadow-xs">
        <span className="text-emerald-700 text-lg leading-none mt-0.5">🔒</span>
        <div className="text-xs text-emerald-950 leading-relaxed font-medium">
          <strong className="text-emerald-950 font-bold block mb-0.5">Canonical Verification Standard</strong>
          Every rule in this knowledge graph is linked to verified Sanskrit verses, chapter numbers, and IAST transliterations 
          from foundational treatises (<em className="font-semibold text-emerald-900">Brihat Parashara Hora Shastra</em>, <em className="font-semibold text-emerald-900">Saravali</em>, <em className="font-semibold text-emerald-900">Jaimini Upadesha Sutras</em>, <em className="font-semibold text-emerald-900">Brihat Jataka</em>, and <em className="font-semibold text-emerald-900">Phaladeepika</em>).
        </div>
      </div>

      {/* 3. Search & Tradition Filter Bar */}
      <div className="rounded-xl p-4 border border-slate-200 bg-white shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          {/* Tradition Dropdown */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs font-bold text-slate-700">Tradition:</span>
            <select
              aria-label="Filter by tradition"
              value={selectedTradition}
              onChange={(e) => setSelectedTradition(e.target.value)}
              className="text-xs rounded-lg p-2.5 bg-slate-50 border border-slate-300 text-slate-800 font-medium focus:outline-none focus:border-indigo-500"
            >
              {TRADITIONS.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {/* Category Dropdown */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs font-bold text-slate-700">Category:</span>
            <select
              aria-label="Filter by category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="text-xs rounded-lg p-2.5 bg-slate-50 border border-slate-300 text-slate-800 font-medium focus:outline-none focus:border-indigo-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Search Box */}
          <div className="w-full sm:w-72">
            <input 
              type="text"
              placeholder="Search Sanskrit verses, rules, sources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search Sanskrit verses, rules, sources..."
              className="w-full text-xs rounded-lg p-2.5 bg-slate-50 border border-slate-300 text-slate-900 placeholder:text-slate-400 font-medium focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* 4. Main 2-Column Split: Rule List & 5-Step Evidence Chain */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Rule Selector List */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium mb-1">
            <span className="font-bold uppercase tracking-wider text-slate-700">Classical Rule Registry</span>
            <span className="font-semibold">{filteredRules.length} Canonical Rules</span>
          </div>

          <div tabIndex={0} role="region" aria-label="Classical Rule Registry list" className="space-y-3 max-h-[720px] overflow-y-auto pr-1">
            {filteredRules.map((r) => {
              const isSelected = r.rule_id === selectedRuleId;
              const ev = evidenceChains.find((c) => c.rule_id === r.rule_id);
              const isSatisfied = ev?.status === "SATISFIED";

              return (
                <div
                  key={r.rule_id}
                  onClick={() => setSelectedRuleId(r.rule_id)}
                  className={`bg-white rounded-lg p-4 shadow-sm transition cursor-pointer flex flex-col gap-2 ${
                    isSelected
                      ? "border-2 border-amber-500 ring-2 ring-amber-500/20 shadow-md"
                      : "border border-slate-200 hover:border-slate-300 hover:shadow"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-slate-800 text-base font-semibold flex items-center gap-1.5">
                      <span>📜</span> {r.rule_name}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {isSatisfied ? (
                        <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                          SATISFIED
                        </span>
                      ) : (
                        <span className="bg-slate-100 text-slate-700 text-xs font-medium px-2.5 py-0.5 rounded-full">
                          {r.category}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-slate-400 text-sm line-clamp-2">{r.brief_description}</div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-400">
                    <span className="font-serif italic font-medium text-slate-700">{r.book_title}</span>
                    <span>{r.chapter_info}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: 5-Stage Evidence Chain Visualizer */}
        <div className="lg:col-span-7">
          {activeEvidenceChain ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
              {/* Step 1: Rule Definition & Classification */}
              <div className="border-b pb-4 border-slate-200">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-mono font-bold text-indigo-700">STEP 1: RULE TAXONOMY</span>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                      activeEvidenceChain.status === "SATISFIED"
                        ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                        : activeEvidenceChain.status === "PARTIALLY_SATISFIED"
                        ? "bg-amber-100 text-amber-800 border border-amber-200"
                        : "bg-slate-100 text-slate-700 border border-slate-200"
                    }`}
                  >
                    {activeEvidenceChain.status.replace(/_/g, " ")}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-slate-900 mt-1">{activeEvidenceChain.rule_name}</h2>
                <p className="text-xs text-slate-400 mt-1">{activeEvidenceChain.brief_description}</p>
              </div>

              {/* Step 2: Canonical Sanskrit Citation */}
              <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-amber-900 flex items-center gap-1.5">
                    <span>📖</span> STEP 2: CANONICAL SANSKRIT CITATION
                  </span>
                  <span className="font-serif italic text-amber-900 font-semibold">
                    {activeEvidenceChain.citation.book_title} (Ch. {activeEvidenceChain.citation.chapter}, {activeEvidenceChain.citation.sloka_range})
                  </span>
                </div>

                {/* Devanagari Sanskrit Verse */}
                <div className="p-3.5 rounded-lg bg-white border border-amber-200 font-serif text-sm text-amber-950 font-semibold text-center leading-relaxed shadow-sm">
                  {activeEvidenceChain.citation.sanskrit_devanagari}
                </div>

                {/* IAST Transliteration */}
                <div className="text-[11px] text-slate-700 font-mono italic px-2">
                  &ldquo;{activeEvidenceChain.citation.sanskrit_iast}&rdquo;
                </div>

                {/* Scholarly Translation */}
                <div className="text-xs text-slate-800 border-t border-amber-200 pt-2 leading-relaxed">
                  <strong className="text-slate-900 font-bold">Scholarly Translation: </strong>
                  {activeEvidenceChain.citation.translation_english}
                </div>

                {activeEvidenceChain.citation.commentary_notes && (
                  <div className="text-[11px] text-slate-700 italic bg-amber-100/50 border border-amber-200 p-2.5 rounded-lg">
                    <strong className="text-slate-900 font-semibold">Technical Commentary: </strong>
                    {activeEvidenceChain.citation.commentary_notes}
                  </div>
                )}
              </div>

              {/* Step 3: Required Classical Conditions */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
                  STEP 3: REQUIRED ASTROLOGICAL CONDITIONS
                </span>
                <div className="space-y-2">
                  {activeEvidenceChain.required_conditions.map((req) => (
                    <div
                      key={req.condition_id}
                      className="p-3 rounded-lg bg-white border border-slate-200 shadow-sm flex items-start gap-2.5 text-xs"
                    >
                      <span className="text-indigo-700 font-mono text-[11px] mt-0.5 font-bold">
                        [{req.condition_id}]
                      </span>
                      <div className="flex-1">
                        <div className="text-slate-900 font-semibold text-sm">{req.description}</div>
                        <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                          Parameters: {JSON.stringify(req.required_parameters)}
                        </div>
                      </div>
                      {req.is_mandatory && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 uppercase font-semibold">
                          Mandatory
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Step 4: Actual Computed Chart Evidence */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
                  STEP 4: ACTUAL COMPUTED CHART EVIDENCE
                </span>
                <div className="space-y-2">
                  {activeEvidenceChain.actual_evidence.map((ev) => (
                    <div
                      key={ev.condition_id}
                      className={`p-3.5 rounded-lg border text-xs flex items-center justify-between gap-3 shadow-sm ${
                        ev.is_satisfied
                          ? "bg-emerald-50/80 border-emerald-200 text-emerald-950"
                          : "bg-red-50/80 border-red-200 text-red-950"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="text-base">{ev.is_satisfied ? "✅" : "❌"}</span>
                        <div>
                          <div className={`font-bold text-sm ${ev.is_satisfied ? "text-emerald-900" : "text-red-900"}`}>{ev.actual_chart_value}</div>
                          {ev.notes && <div className={`text-xs mt-0.5 ${ev.is_satisfied ? "text-emerald-800" : "text-red-800"}`}>{ev.notes}</div>}
                        </div>
                      </div>
                      <span className={`font-mono text-xs font-semibold px-2.5 py-1 rounded ${
                        ev.is_satisfied ? "bg-emerald-100 text-emerald-800 border border-emerald-300" : "bg-red-100 text-red-800 border border-red-300"
                      }`}>
                        {ev.is_satisfied ? "CONDITION MET" : "NOT MET"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Step 5: Final Strength Score & Verdict */}
              <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    STEP 5: TECHNICAL RESULT &amp; STRENGTH SCORE
                  </span>
                  <span className="text-2xl font-black text-slate-900 font-mono">
                    {activeEvidenceChain.strength_score}/100
                  </span>
                </div>

                {/* Score Progress Bar */}
                <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden border border-slate-300">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      activeEvidenceChain.strength_score >= 80
                        ? "bg-emerald-600"
                        : activeEvidenceChain.strength_score >= 50
                        ? "bg-amber-500"
                        : "bg-slate-500"
                    }`}
                    style={{ width: `${activeEvidenceChain.strength_score}%` }}
                  ></div>
                </div>

                <div className="text-xs text-slate-700 leading-relaxed font-semibold">
                  {activeEvidenceChain.fructification_summary}
                </div>

                {/* Cancellation Factors Alert if any active */}
                {activeEvidenceChain.cancellation_factors.some((c) => c.is_active) && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-900 space-y-1">
                    <strong className="font-bold block text-red-950">Active Cancellation Factors (Bhanga):</strong>
                    {activeEvidenceChain.cancellation_factors
                      .filter((c) => c.is_active)
                      .map((c) => (
                        <div key={c.factor_id} className="text-red-800">
                          • {c.description} ({c.classical_reference}) - Penalty: {c.impact_deduction}%
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>
          ) : activeRuleSummary ? (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
              <h2 className="text-xl font-bold text-slate-900">{activeRuleSummary.rule_name}</h2>
              <p className="text-xs text-slate-400">{activeRuleSummary.brief_description}</p>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 bg-white border border-slate-200 rounded-2xl">Select a classical rule to inspect.</div>
          )}
        </div>
      </div>
    </div>
  );
}
