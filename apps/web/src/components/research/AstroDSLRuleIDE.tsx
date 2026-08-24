"use client";

import React, { useState, useEffect } from "react";

export interface CustomRule {
  rule_id: string;
  name: string;
  description: string;
  dsl_source: string;
  category: string;
  tags: string[];
  author: string;
  version: string;
  created_at: string;
}

export interface TraceStep {
  node_type: string;
  expression: string;
  result: any;
}

export interface EvaluationResult {
  is_satisfied: boolean;
  evaluated_value: any;
  execution_time_ms: number;
  trace: TraceStep[];
  error_message?: string;
}

const SAMPLE_TEMPLATES = [
  {
    title: "Gajakesari Yoga (Jupiter Kendra from Moon)",
    dsl: 'PLANET("Jupiter").house IN KENDRA_HOUSES AND PLANET("Jupiter").is_combust == FALSE',
  },
  {
    title: "Ruchaka Yoga (Mars Kendra in Own/Exalted)",
    dsl: 'PLANET("Mars").house IN KENDRA_HOUSES AND PLANET("Mars").rashi IN ["Aries", "Scorpio", "Capricorn"]',
  },
  {
    title: "Sun Directional Strength (Digbala in 10th)",
    dsl: 'PLANET("Sun").house == 10 AND PLANET("Sun").is_combust == FALSE',
  },
  {
    title: "Benefic Venus in Trikona or 11th",
    dsl: 'PLANET("Venus").house IN [1, 5, 9, 11]',
  },
];

const DEFAULT_SAMPLE_CHART = {
  planets: [
    { planet: "JUPITER", house_number: 4, rashi: "Cancer", is_combust: false, is_retrograde: false },
    { planet: "MOON", house_number: 1, rashi: "Aries", is_combust: false, is_retrograde: false },
    { planet: "SUN", house_number: 10, rashi: "Capricorn", is_combust: false, is_retrograde: false },
    { planet: "MARS", house_number: 10, rashi: "Capricorn", is_combust: false, is_retrograde: false },
    { planet: "VENUS", house_number: 9, rashi: "Sagittarius", is_combust: false, is_retrograde: false },
    { planet: "SATURN", house_number: 11, rashi: "Aquarius", is_combust: false, is_retrograde: false },
  ],
  planet_strengths: [],
};

export function AstroDSLRuleIDE() {
  const [dslSource, setDslSource] = useState<string>(SAMPLE_TEMPLATES[0].dsl);
  const [ruleName, setRuleName] = useState<string>("Custom Gajakesari Rule");
  const [ruleDesc, setRuleDesc] = useState<string>("User authored AstroDSL yoga rule");

  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [syntaxError, setSyntaxError] = useState<string>("");
  const [astView, setAstView] = useState<string>("");

  const [testResult, setTestResult] = useState<EvaluationResult | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);

  const [rulesList, setRulesList] = useState<CustomRule[]>([]);
  const [activeTab, setActiveTab] = useState<"ide" | "registry">("ide");

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const res = await fetch("/api/v1/techniques/custom/");
      if (res.ok) {
        const data = await res.json();
        setRulesList(data);
      }
    } catch {
      // offline fallback
    }
  };

  const handleValidate = async () => {
    setSyntaxError("");
    try {
      const res = await fetch("/api/v1/techniques/custom/dsl/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dsl_source: dslSource }),
      });
      const data = await res.json();
      setIsValid(data.is_valid);
      if (!data.is_valid) {
        setSyntaxError(data.error_message || "Invalid AstroDSL syntax");
      } else {
        setAstView(data.ast_representation || "");
      }
    } catch (err: any) {
      setIsValid(false);
      setSyntaxError(err.message || "Validation failed");
    }
  };

  const handleTestEvaluate = async () => {
    setIsEvaluating(true);
    setTestResult(null);
    try {
      const res = await fetch("/api/v1/techniques/custom/dsl/test-evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dsl_source: dslSource,
          chart_context: DEFAULT_SAMPLE_CHART,
        }),
      });
      const data = await res.json();
      setTestResult(data);
    } catch (err: any) {
      setTestResult({
        is_satisfied: false,
        evaluated_value: null,
        execution_time_ms: 0,
        trace: [],
        error_message: err.message,
      });
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleSaveRule = async () => {
    if (!ruleName.trim()) return;
    try {
      const res = await fetch("/api/v1/techniques/custom/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: ruleName,
          description: ruleDesc,
          dsl_source: dslSource,
          category: "custom_yoga",
          tags: ["astro_dsl"],
        }),
      });
      if (res.ok) {
        fetchRules();
        alert("Rule saved successfully!");
      } else {
        const err = await res.json();
        alert(`Error saving rule: ${err.detail || "Failed"}`);
      }
    } catch (err: any) {
      alert(`Save error: ${err.message}`);
    }
  };

  const handleExportBundle = async () => {
    try {
      const res = await fetch("/api/v1/techniques/custom/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      const blob = new Blob([data.bundle_json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AstroDSL_Rule_Bundle_${new Date().toISOString().slice(0, 10)}.astro.json`;
      a.click();
    } catch (err: any) {
      alert(`Export error: ${err.message}`);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 bg-slate-900 text-slate-100 rounded-xl shadow-2xl border border-slate-800 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Priority 9 Engine
            </span>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              AstroDSL Rule IDE & Sandbox Engine
            </h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Author, validate, and evaluate sandboxed custom astrological rules and yoga predicates in real-time.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab("ide")}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "ide"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            AstroDSL Editor & Sandbox
          </button>
          <button
            onClick={() => setActiveTab("registry")}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === "registry"
                ? "bg-indigo-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Custom Rule Registry ({rulesList.length})
          </button>
        </div>
      </div>

      {activeTab === "ide" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Code Editor Panel */}
          <div className="lg:col-span-7 space-y-4">
            {/* Quick Templates */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Quick Preset Templates
              </label>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_TEMPLATES.map((tmpl, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setDslSource(tmpl.dsl);
                      setRuleName(tmpl.title);
                      setIsValid(null);
                      setSyntaxError("");
                    }}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-500/20 px-3 py-1.5 rounded-md transition-colors"
                  >
                    {tmpl.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Rule Name & Desc */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1 font-medium">Rule Name</label>
                <input
                  type="text"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1 font-medium">Description</label>
                <input
                  type="text"
                  value={ruleDesc}
                  onChange={(e) => setRuleDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* AstroDSL Code Area */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  AstroDSL Source Code
                </label>
                {isValid !== null && (
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-mono ${
                      isValid ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"
                    }`}
                  >
                    {isValid ? "✓ Valid Syntax" : "✕ Syntax Error"}
                  </span>
                )}
              </div>
              <textarea
                rows={6}
                value={dslSource}
                onChange={(e) => {
                  setDslSource(e.target.value);
                  setIsValid(null);
                }}
                className="w-full font-mono text-sm bg-slate-950 border border-slate-800 rounded-lg p-3 text-emerald-300 focus:outline-none focus:border-indigo-500 leading-relaxed shadow-inner"
                placeholder="Enter AstroDSL expression e.g. PLANET('Jupiter').house IN KENDRA_HOUSES..."
              />
              {syntaxError && (
                <div className="mt-2 text-xs text-rose-400 bg-rose-950/40 border border-rose-800/40 p-2.5 rounded font-mono">
                  {syntaxError}
                </div>
              )}
            </div>

            {/* Action Bar */}
            <div className="flex items-center space-x-3 pt-2">
              <button
                onClick={handleValidate}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 text-sm font-medium rounded-lg border border-slate-700 transition-colors"
              >
                Validate Syntax
              </button>
              <button
                onClick={handleTestEvaluate}
                disabled={isEvaluating}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2 text-sm font-medium rounded-lg shadow-lg shadow-indigo-600/20 transition-colors disabled:opacity-50"
              >
                {isEvaluating ? "Evaluating..." : "Test on Chart"}
              </button>
              <button
                onClick={handleSaveRule}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 text-sm font-medium rounded-lg shadow-lg shadow-emerald-600/20 transition-colors"
              >
                Save to Registry
              </button>
            </div>
          </div>

          {/* Sandbox Testing & Trace Inspector */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-4 shadow-xl">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2">
                Sandbox Evaluation Inspector
              </h2>

              {testResult ? (
                <div className="space-y-4">
                  {/* Result Status Badge */}
                  <div
                    className={`p-4 rounded-xl border flex items-center justify-between ${
                      testResult.is_satisfied
                        ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-300"
                        : "bg-rose-950/30 border-rose-500/30 text-rose-300"
                    }`}
                  >
                    <div>
                      <div className="text-xs uppercase tracking-wider font-semibold opacity-80">
                        Verdict
                      </div>
                      <div className="text-lg font-bold">
                        {testResult.is_satisfied ? "TRUE (Satisfied)" : "FALSE (Not Triggered)"}
                      </div>
                    </div>
                    <div className="text-right font-mono text-xs opacity-75">
                      <div>Execution Time</div>
                      <div className="text-base font-semibold">{testResult.execution_time_ms} ms</div>
                    </div>
                  </div>

                  {/* Evaluation Trace */}
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                      AST Tree-Walker Trace ({testResult.trace.length} steps)
                    </label>
                    <div className="max-h-56 overflow-y-auto space-y-1.5 pr-1 font-mono text-xs">
                      {testResult.trace.map((step, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-900 border border-slate-800/80 p-2 rounded flex items-center justify-between text-slate-300"
                        >
                          <span className="text-indigo-400 font-semibold">{step.node_type}</span>
                          <span className="text-slate-400 truncate max-w-[140px]">{step.expression}</span>
                          <span className="text-emerald-400 font-bold">{String(step.result)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500 text-sm">
                  Click <strong className="text-indigo-400 font-medium">"Test on Chart"</strong> to run the sandboxed AST evaluator against natal chart context.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Registry & Import/Export View */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Registered Custom AstroDSL Techniques</h2>
            <button
              onClick={handleExportBundle}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 text-sm font-medium rounded-lg border border-slate-700 transition-colors"
            >
              Export Bundle (.astro.json)
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rulesList.map((rule) => (
              <div
                key={rule.rule_id}
                className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h2 className="font-semibold text-indigo-300 text-base">{rule.name}</h2>
                  <span className="text-xs bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded font-mono border border-indigo-500/20">
                    {rule.rule_id}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{rule.description}</p>
                <div className="font-mono text-xs bg-slate-900 p-2 rounded text-emerald-400 border border-slate-800">
                  {rule.dsl_source}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
