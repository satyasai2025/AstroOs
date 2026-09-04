"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";

export interface ShastricQAResponseData {
  question: string;
  domain: string;
  is_valid_query: boolean;
  guardrail_reason: string | null;
  headline_en: string;
  headline_hi: string;
  answer_en: string;
  answer_hi: string;
  probable_timing_window: string;
  peak_timing_date: string | null;
  confidence_tier: "HIGH" | "MODERATE" | "CONDITIONAL";
  shastric_rule_grounds: string[];
  planetary_triggers: string[];
  recommended_remedies: string[];
  faithfulness_score: number;
}

interface ChatMessage {
  id: string;
  sender: "user" | "oracle";
  text: string;
  data?: ShastricQAResponseData;
  timestamp: string;
}

interface ShastricChatOracleProps {
  timelineWindows?: any[];
  nativeName?: string;
  birthDateIso?: string;
  latitude?: number;
  longitude?: number;
  lang?: "en" | "hi";
  onClose?: () => void;
}

const QUICK_PROMPTS = [
  {
    icon: "💼",
    en: "When is my next major career change or promotion?",
    hi: "मेरी नौकरी में बदलाव अथवा प्रमोशन कब होगा?",
  },
  {
    icon: "✈️",
    en: "What are the yogas for foreign travel and relocation?",
    hi: "विदेश यात्रा एवं स्थान परिवर्तन के क्या योग हैं?",
  },
  {
    icon: "💍",
    en: "What is the most auspicious window for marriage?",
    hi: "विवाह एवं संबंध के शुभ योग कब हैं?",
  },
  {
    icon: "💰",
    en: "When will my wealth and financial investments peak?",
    hi: "धन लाभ एवं निवेश के लिए सबसे अनुकूल समय कब है?",
  },
];

function FormattedShastricText({ text }: { text: string }) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let tableLines: string[] = [];
  let inTable = false;

  const flushTable = (key: string) => {
    if (tableLines.length >= 2) {
      const headerLine = tableLines[0];
      const dataLines = tableLines.slice(1).filter((l) => !l.includes("---"));
      const headers = headerLine
        .split("|")
        .map((c) => c.trim())
        .filter(Boolean);

      elements.push(
        <div key={key} className="my-3 overflow-x-auto rounded-xl border border-amber-200 dark:border-amber-900/60 shadow-sm bg-white dark:bg-slate-900">
          <table className="w-full text-[11px] text-left border-collapse">
            <thead>
              <tr className="bg-amber-100/90 dark:bg-amber-950/80 border-b border-amber-200 dark:border-amber-900/60 text-amber-950 dark:text-amber-200 font-bold">
                {headers.map((h, i) => (
                  <th key={i} className="p-2.5 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {dataLines.map((rowStr, rowIdx) => {
                const cells = rowStr
                  .split("|")
                  .map((c) => c.trim())
                  .filter(Boolean);
                const isHighlight =
                  rowStr.includes("⚡") ||
                  rowStr.includes("Permanent") ||
                  rowStr.includes("स्थायी") ||
                  rowStr.includes("80%");
                return (
                  <tr
                    key={rowIdx}
                    className={`hover:bg-amber-50/50 dark:hover:bg-slate-800/40 transition-colors ${
                      isHighlight
                        ? "bg-amber-50/70 dark:bg-amber-950/30 font-medium"
                        : rowIdx % 2 === 1
                        ? "bg-slate-50/60 dark:bg-slate-950/40"
                        : ""
                    }`}
                  >
                    {cells.map((cell, cellIdx) => {
                      const cleanCell = cell.replace(/\*\*/g, "").replace(/`/g, "");
                      const isFirst = cellIdx === 0;
                      return (
                        <td
                          key={cellIdx}
                          className={`p-2.5 ${
                            isFirst
                              ? "font-bold text-slate-900 dark:text-amber-300"
                              : "text-slate-700 dark:text-slate-300"
                          }`}
                        >
                          {cleanCell}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      );
    }
    tableLines = [];
    inTable = false;
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      inTable = true;
      tableLines.push(trimmed);
    } else {
      if (inTable) {
        flushTable(`tbl-${idx}`);
      }
      if (trimmed.startsWith("### ")) {
        elements.push(
          <h4
            key={`h-${idx}`}
            className="text-xs font-black text-amber-900 dark:text-amber-300 mt-3 mb-1.5 flex items-center gap-1.5"
          >
            {trimmed.replace("### ", "")}
          </h4>
        );
      } else if (trimmed.startsWith("• ") || trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
        elements.push(
          <div
            key={`li-${idx}`}
            className="flex items-start gap-1.5 text-[11px] text-slate-700 dark:text-slate-300 my-1 ml-1"
          >
            <span className="text-amber-500 dark:text-amber-400 font-bold">▪</span>
            <span>{trimmed.replace(/^[•*-]\s*/, "")}</span>
          </div>
        );
      } else if (trimmed.length > 0) {
        elements.push(
          <p
            key={`p-${idx}`}
            className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed my-1.5"
          >
            {trimmed}
          </p>
        );
      }
    }
  });

  if (inTable) {
    flushTable("tbl-end");
  }

  return <div className="space-y-1">{elements}</div>;
}

export function ShastricChatOracle({
  timelineWindows = [],
  nativeName = "Native",
  birthDateIso,
  latitude,
  longitude,
  lang = "en",
  onClose,
}: ShastricChatOracleProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "intro-1",
      sender: "oracle",
      text:
        lang === "hi"
          ? `नमस्ते! मैं आपका शास्त्रीय ज्योतिष सहायक (Shastric Copilot) हूँ। आपकी जन्म कुंडली, विंशोत्तरी दशा, गोचर एवं सर्वातोभद्र चक्र के आधार पर आपके प्रश्नों के सटीक, नियम-आधारित उत्तर दे सकता हूँ। नीचे दिए गए किसी विषय पर प्रश्न पूछें अथवा अपना प्रश्न टाइप करें।`
          : `Hello! I am your Shastric Astrological Copilot. Grounded strictly in your natal parameters, Vimshottari dasha, Gochara transits, and Sarvato-Bhadra Chakra vedhas, I provide deterministic answers. Select a prompt below or ask your own question.`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (textToSend?: string) => {
    const q = (textToSend || inputQuery).trim();
    if (!q) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const resp = await api.post<ShastricQAResponseData>("/api/v1/phalita/ask-oracle", {
        question: q,
        timeline_windows: timelineWindows.length > 0 ? timelineWindows : undefined,
        birth_date_iso: birthDateIso,
        latitude,
        longitude,
        native_name: nativeName,
        lang,
      });

      const oracleMsg: ChatMessage = {
        id: `ora-${Date.now()}`,
        sender: "oracle",
        text: lang === "hi" ? resp.answer_hi : resp.answer_en,
        data: resp,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, oracleMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: "oracle",
        text:
          lang === "hi"
            ? "क्षमा करें, शास्त्रीय विश्लेषण प्रक्रिया में त्रुटि उत्पन्न हुई।"
            : `Consultation analysis failed: ${err.message || "Unknown error"}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[750px] bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-3xl overflow-hidden shadow-xl text-slate-900 dark:text-slate-100">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-purple-50 via-white to-amber-50 dark:from-purple-950/60 dark:via-slate-900 dark:to-amber-950/50 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-amber-100 dark:bg-amber-500/20 border border-amber-300 dark:border-amber-500/40 flex items-center justify-center text-lg shadow-sm">
            🔮
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-black text-slate-900 dark:text-white">
                {lang === "hi" ? "शास्त्रीय प्रश्नोत्तर कॉपायलट" : "Shastric Chart Copilot"}
              </h3>
              <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40 rounded text-[9px] font-mono font-bold">
                Zero Hallucination
              </span>
            </div>
            <p className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">
              {lang === "hi"
                ? "100% गणितीय एवं शास्त्रीय नियमों पर आधारित प्रत्यक्ष उत्तर"
                : "Deterministic rule-grounded answers bound to natal dasha & transits"}
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center justify-center text-xs"
          >
            ✕
          </button>
        )}
      </div>

      {/* Messages Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/50 dark:bg-slate-950/50">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mb-1 px-1">
              <span>{msg.sender === "user" ? nativeName : "Shastric Oracle"}</span>
              <span>•</span>
              <span>{msg.timestamp}</span>
            </div>

            <div
              className={`p-4 rounded-2xl max-w-[90%] md:max-w-[85%] text-xs leading-relaxed space-y-3 ${
                msg.sender === "user"
                  ? "bg-amber-500 text-slate-950 font-bold shadow-md rounded-br-none"
                  : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 shadow-md rounded-bl-none"
              }`}
            >
              {/* Formatted Shastric Message Text */}
              {msg.sender === "user" ? (
                <div className="whitespace-pre-wrap">{msg.text}</div>
              ) : (
                <FormattedShastricText text={msg.text} />
              )}

              {/* Rich Oracle Card Details if available */}
              {msg.data && msg.data.is_valid_query && (
                <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800/80 space-y-3">
                  {/* Headline & Timing Window */}
                  <div className="p-3 bg-amber-50/80 dark:bg-slate-950/80 border border-amber-200 dark:border-amber-500/30 rounded-xl space-y-1 shadow-sm">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-amber-900 dark:text-amber-300">
                        {lang === "hi" ? msg.data.headline_hi : msg.data.headline_en}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                          msg.data.confidence_tier === "HIGH"
                            ? "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/40"
                            : "bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-500/40"
                        }`}
                      >
                        {msg.data.confidence_tier} Confidence
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-600 dark:text-slate-400 font-mono flex items-center gap-1.5">
                      <span>📅</span>
                      <span>
                        {lang === "hi" ? "संभावित समय अवधि:" : "Probable Window:"}{" "}
                        <strong className="text-slate-900 dark:text-white">{msg.data.probable_timing_window}</strong>
                      </span>
                    </div>
                  </div>

                  {/* Shastric Rule Grounds */}
                  {msg.data.shastric_rule_grounds.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-[10px] font-bold text-cyan-800 dark:text-cyan-400 uppercase tracking-wider">
                        📜 {lang === "hi" ? "शास्त्रीय गणना आधार" : "Calculated Shastric Grounds"}
                      </div>
                      <ul className="space-y-1 text-[11px] text-slate-700 dark:text-slate-300">
                        {msg.data.shastric_rule_grounds.map((g, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 bg-slate-50 dark:bg-slate-950/60 p-2 rounded-lg border border-slate-200 dark:border-slate-800/60">
                            <span className="text-cyan-700 dark:text-cyan-400">▪</span>
                            <span>{g}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Planetary Triggers */}
                  {msg.data.planetary_triggers.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-[10px] font-bold text-purple-800 dark:text-purple-300 uppercase tracking-wider">
                        🪐 {lang === "hi" ? "गोचर एवं ग्रह वेध" : "Planetary Transit Triggers"}
                      </div>
                      <ul className="space-y-1 text-[11px] text-slate-700 dark:text-slate-300">
                        {msg.data.planetary_triggers.map((trig, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 bg-slate-50 dark:bg-slate-950/60 p-2 rounded-lg border border-slate-200 dark:border-slate-800/60">
                            <span className="text-purple-700 dark:text-purple-400">▪</span>
                            <span>{trig}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recommended Remedies */}
                  {msg.data.recommended_remedies.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-[10px] font-bold text-amber-800 dark:text-amber-400 uppercase tracking-wider">
                        ✨ {lang === "hi" ? "शास्त्रीय उपाय एवं मार्गदर्शन" : "Recommended Shastric Remedies"}
                      </div>
                      <ul className="space-y-1 text-[11px] text-slate-700 dark:text-slate-300">
                        {msg.data.recommended_remedies.map((rem, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 bg-amber-50 dark:bg-amber-950/20 p-2 rounded-lg border border-amber-200 dark:border-amber-800/30">
                            <span className="text-amber-700 dark:text-amber-400">⚜️</span>
                            <span>{rem}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Guardrail Violation Banner */}
              {msg.data && !msg.data.is_valid_query && (
                <div className="mt-2 p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 rounded-xl text-[11px] flex items-start gap-2">
                  <span>🛡️</span>
                  <span>{msg.data.guardrail_reason}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400 text-xs p-3 bg-white dark:bg-slate-900/60 rounded-2xl w-max border border-slate-200 dark:border-slate-800 shadow-sm">
            <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-amber-500 border-t-transparent" />
            <span>
              {lang === "hi"
                ? "दशा एवं गोचर तालिकाओं की गणना हो रही है..."
                : "Retrieving calculated dasha and transit grounds..."}
            </span>
          </div>
        )}
      </div>

      {/* Suggested Quick Prompts */}
      <div className="p-3 bg-white dark:bg-slate-900/60 border-t border-slate-200 dark:border-slate-800/80">
        <div className="text-[10px] font-bold text-slate-600 dark:text-slate-400 mb-2 uppercase tracking-wider">
          💡 {lang === "hi" ? "त्वरित प्रश्न (Quick Questions)" : "Quick Questions"}
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 text-xs">
          {QUICK_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => handleSend(lang === "hi" ? p.hi : p.en)}
              className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-950 dark:hover:bg-slate-900 border border-slate-200 hover:border-slate-300 dark:border-slate-800 dark:hover:border-slate-700 text-slate-700 dark:text-slate-300 rounded-xl whitespace-nowrap transition flex items-center gap-1.5 flex-shrink-0 disabled:opacity-50 shadow-sm"
            >
              <span>{p.icon}</span>
              <span className="text-[11px] font-medium">{lang === "hi" ? p.hi : p.en}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <div className="p-3 bg-white dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend(inputQuery);
            }
          }}
          placeholder={
            lang === "hi"
              ? "उदा. मेरी जॉब चेंज कब होगी? या विदेश यात्रा का क्या समय है?..."
              : "Ask e.g. When will I switch my job? or Foreign travel timing?..."
          }
          className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl px-4 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-amber-500"
        />
        <button
          onClick={() => handleSend(inputQuery)}
          disabled={loading || !inputQuery.trim()}
          className="px-4 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-40 text-slate-950 font-bold rounded-2xl text-xs transition flex items-center gap-1.5 shadow-md"
        >
          <span>🚀</span>
          <span>{lang === "hi" ? "पूछें" : "Ask"}</span>
        </button>
      </div>
    </div>
  );
}
