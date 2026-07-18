"use client";

import { useState, useRef, useEffect } from "react";
import type { AIResponseSchema } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  text: string;
  citations?: AIResponseSchema["citations"];
}

const QUICK_QUESTIONS = [
  "What are the strongest planets in this chart?",
  "What yogas are active and what do they mean?",
  "Which house lord placements are most significant?",
  "What does the current dasha period indicate?",
];

export function ChatInterface({
  onAsk,
  placeholder = "Ask anything about this chart…",
}: {
  onAsk: (question: string) => Promise<AIResponseSchema>;
  placeholder?: string;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const resp = await onAsk(q);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: resp.body || resp.summary,
          citations: resp.citations,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-3">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-slate-500">Quick questions:</p>
            <div className="flex flex-wrap gap-2">
              {QUICK_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => send(q)}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 hover:bg-white/10 hover:text-slate-100 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                m.role === "user"
                  ? "bg-amber-600/20 text-amber-100"
                  : "bg-white/5 text-slate-200"
              }`}
            >
              <p>{m.text}</p>
              {m.citations && m.citations.length > 0 && (
                <div className="mt-2 border-t border-white/10 pt-2 space-y-1">
                  {m.citations.map((c, ci) => (
                    <p key={ci} className="text-slate-500">
                      <span className="font-medium text-slate-400">
                        {c.source}
                      </span>{" "}
                      — {c.reference}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-xl bg-white/5 px-3 py-2 text-xs text-slate-500">
              Thinking…
            </div>
          </div>
        )}
        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600 focus:border-amber-500/40 focus:outline-none focus:ring-1 focus:ring-amber-500/30 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="rounded-lg bg-amber-600 px-3 py-2 text-xs font-semibold text-cosmos-950 hover:bg-amber-500 disabled:opacity-40 transition-colors"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
