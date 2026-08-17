"use client";

import { useState } from "react";

export interface ShareButtonProps {
  title?: string;
  text?: string;
  url?: string;
  className?: string;
  compact?: boolean;
}

export function ShareButton({
  title = "AstroOS Vedic Research Platform",
  text = "Check out this astrological analysis on AstroOS",
  url,
  className = "",
  compact = false,
}: ShareButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleShare = async (e: React.MouseEvent) => {
    e.preventDefault();
    const shareUrl = url || (typeof window !== "undefined" ? window.location.href : "");

    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({
          title,
          text,
          url: shareUrl,
        });
        return;
      } catch (err: any) {
        if (err.name === "AbortError") return;
        // Fall back to clipboard copy if share fails
      }
    }

    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(shareUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2500);
      } else {
        throw new Error("Clipboard API not available");
      }
    } catch {
      // Fallback manual input copy
      const input = document.createElement("input");
      input.value = shareUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onClick={handleShare}
        className={`inline-flex items-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 text-slate-700 dark:text-slate-200 hover:border-amber-500/60 hover:text-amber-600 dark:hover:text-amber-400 px-2.5 py-1.5 text-xs font-medium transition shadow-sm ${className}`}
        title="Share or copy link"
        aria-label="Share or copy link"
      >
        {copied ? (
          <>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500">
              <path d="M20 6L9 17l-5-5" />
            </svg>
            {!compact && <span className="text-emerald-500 font-semibold">Copied!</span>}
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
              <polyline points="16 6 12 2 8 6" />
              <line x1="12" y1="2" x2="12" y2="15" />
            </svg>
            {!compact && <span>Share</span>}
          </>
        )}
      </button>

      {copied && (
        <div
          role="status"
          className="absolute right-0 top-full z-50 mt-1 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] font-medium text-slate-100 shadow-lg dark:bg-slate-100 dark:text-slate-900 animate-fade-in"
        >
          Link copied to clipboard!
        </div>
      )}
    </div>
  );
}
