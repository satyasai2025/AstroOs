"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUnifiedSearch } from "@/lib/search";

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const pathname = usePathname();
  useEffect(() => {
    setIsFocused(false);
    setQuery("");
  }, [pathname]);

  const { data, isLoading } = useUnifiedSearch(query, 12);
  const isOpen = isFocused && query.length >= 2;
  const results = data?.results || [];

  return (
    <div ref={wrapperRef} className="relative w-full max-w-sm">
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.3-4.3"></path>
          </svg>
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          placeholder="Search charts, knowledge, projects..."
          className="field-input w-full pl-9 py-1.5 pr-9 text-sm"
          style={{ backgroundColor: "var(--bg-primary)", borderColor: "var(--border-primary)" }}
        />
        {isLoading && query.length >= 2 && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-t-transparent" style={{ borderColor: "var(--accent)" }} />
          </div>
        )}
        {!isLoading && data?.ai_enhanced && (
          <div
            className="absolute inset-y-0 right-0 flex items-center pr-2.5"
            title={`AI expanded query to: ${data.expanded_terms.join(", ")}`}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ color: "var(--section-ai)" }}>
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          </div>
        )}
      </div>

      {isOpen && (
        <div
          className="absolute left-0 right-0 top-full mt-1 max-h-96 overflow-y-auto rounded-lg border shadow-lg z-50"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border-primary)" }}
        >
          {data?.ai_enhanced && data.expanded_terms.length > 0 && (
            <div
              className="px-4 pt-2 text-[10px] uppercase tracking-wide"
              style={{ color: "var(--section-ai)" }}
            >
              ✦ AI expanded: {data.expanded_terms.join(", ")}
            </div>
          )}
          {results.length > 0 ? (
            <div className="flex flex-col py-2 text-sm">
              {results.map((result) => (
                <Link
                  key={`${result.type}-${result.id}`}
                  href={result.href}
                  className="px-4 py-2 hover:bg-black/5 transition flex flex-col gap-0.5"
                  style={{ borderBottom: "1px solid var(--border-primary)" }}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[13px]" style={{ color: "var(--text-primary)" }}>{result.title}</span>
                    <span className="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full"
                          style={{ border: "1px solid var(--border-primary)", color: "var(--text-secondary)" }}>
                      {result.type}
                    </span>
                  </div>
                  {result.type === "chart" && result.subtitle && (
                    <span className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{result.subtitle}</span>
                  )}
                  <span className="text-[11px] truncate" style={{ color: "var(--text-muted)" }}>{result.snippet}</span>
                </Link>
              ))}
            </div>
          ) : query.length >= 2 && !isLoading ? (
            <div className="p-4 text-center text-sm" style={{ color: "var(--text-muted)" }}>
              No results found for "{query}".
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}