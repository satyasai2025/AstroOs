"use client";

import React, { useState, useEffect, useRef } from "react";

export interface TourStep {
  targetSelector: string; // e.g. '[data-tour="step-category"]'
  title: string;
  description: string;
  actionText?: string; // e.g. "Click here to select category"
  position?: "bottom" | "top" | "left" | "right" | "center";
}

interface GuidedHelpTourProps {
  steps: TourStep[];
  isOpen: boolean;
  onClose: () => void;
  tourId: string; // e.g. "patterns" or "cases"
}

export function GuidedHelpTour({ steps, isOpen, onClose, tourId }: GuidedHelpTourProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isAnchorFound, setIsAnchorFound] = useState(true);
  const [popoverStyle, setPopoverStyle] = useState<React.CSSProperties>({});
  const cardRef = useRef<HTMLDivElement>(null);

  const currentStep = steps[currentStepIndex];
  const totalSteps = steps.length;
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === totalSteps - 1;

  const storageKey =
    tourId === "patterns" || tourId === "patterns_discovery_tour"
      ? "astroos_guided_tour_patterns_v1_done"
      : tourId === "cases" || tourId === "cases_databank_tour"
      ? "astroos_guided_tour_cases_v1_done"
      : `astroos_guided_tour_${tourId}_v1_done`;

  // Dynamically position popup box directly next to active target element
  useEffect(() => {
    if (!isOpen || !currentStep) return;

    let targetEl: Element | null = null;
    try {
      targetEl = document.querySelector(currentStep.targetSelector);
    } catch {
      targetEl = null;
    }

    const positionCard = () => {
      if (targetEl) {
        setIsAnchorFound(true);
        try {
          targetEl.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
          targetEl.classList.add("ring-4", "ring-cyan-500/80", "shadow-2xl", "transition-all", "z-50");
          
          const rect = targetEl.getBoundingClientRect();
          const cardWidth = 380;
          const cardHeight = 240;

          // Default position below target element
          let top = rect.bottom + 12;
          let left = Math.max(16, Math.min(rect.left, window.innerWidth - cardWidth - 16));

          // If element is near bottom of screen, position popover above target element
          if (top + cardHeight > window.innerHeight - 20) {
            top = Math.max(16, rect.top - cardHeight - 12);
          }

          setPopoverStyle({
            position: "fixed",
            top: `${top}px`,
            left: `${left}px`,
            width: `${cardWidth}px`,
          });
        } catch {
          setPopoverStyle({});
        }
      } else {
        setIsAnchorFound(false);
        setPopoverStyle({});
      }
    };

    positionCard();
    window.addEventListener("resize", positionCard);
    window.addEventListener("scroll", positionCard);

    return () => {
      window.removeEventListener("resize", positionCard);
      window.removeEventListener("scroll", positionCard);
      if (targetEl) {
        try {
          targetEl.classList.remove("ring-4", "ring-cyan-500/80", "shadow-2xl", "z-50");
        } catch {
          // Safe cleanup
        }
      }
    };
  }, [isOpen, currentStepIndex, currentStep]);

  if (!isOpen || !currentStep) return null;

  const handleNext = () => {
    if (isLastStep) {
      handleFinish();
    } else {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirstStep) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleFinish = () => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(storageKey, "completed");
      } catch {
        // LocalStorage fallback
      }
    }
    onClose();
    setCurrentStepIndex(0);
  };

  const isFloatingPositioned = isAnchorFound && Object.keys(popoverStyle).length > 0;

  return (
    <div className="fixed inset-0 z-50 pointer-events-auto">
      {/* Dim Backdrop */}
      <div className="fixed inset-0 bg-slate-950/50 backdrop-blur-xs transition-opacity" onClick={handleFinish} />

      {/* Floating Target-Anchored Interactive Help Box */}
      <div
        ref={cardRef}
        style={isFloatingPositioned ? popoverStyle : undefined}
        className={`${
          isFloatingPositioned
            ? "z-50 animate-in fade-in zoom-in-95 duration-200"
            : "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 max-w-md w-full animate-in fade-in duration-200"
        } rounded-2xl bg-white dark:bg-slate-900 border border-cyan-500/50 p-5 shadow-2xl space-y-4 text-slate-900 dark:text-slate-100 font-mono`}
      >
        {/* Top Pointer Arrow indicator when floating */}
        {isFloatingPositioned && (
          <div className="absolute -top-2 left-6 w-4 h-4 bg-white dark:bg-slate-900 border-t border-l border-cyan-500/50 rotate-45" />
        )}

        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2.5">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 font-bold text-xs">
              ❓
            </span>
            <span className="text-xs font-extrabold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
              Interactive Guided Tour
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            {!isAnchorFound && (
              <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[9px] font-bold border border-amber-500/20">
                General View
              </span>
            )}
            <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-400">
              Step {currentStepIndex + 1} of {totalSteps}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="space-y-2">
          <h3 className="text-base font-extrabold text-slate-900 dark:text-slate-100">
            {currentStep.title}
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-sans">
            {currentStep.description}
          </p>
          {currentStep.actionText && (
            <div className="mt-2 p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-[11px] font-bold text-cyan-600 dark:text-cyan-300 flex items-center gap-1.5">
              <span>👉</span>
              <span>{currentStep.actionText}</span>
            </div>
          )}
        </div>

        {/* Step Progress Dots */}
        <div className="flex items-center justify-center gap-1.5 py-1">
          {steps.map((_, idx) => (
            <span
              key={idx}
              className={`h-1.5 rounded-full transition-all ${
                idx === currentStepIndex
                  ? "w-6 bg-cyan-500"
                  : idx < currentStepIndex
                  ? "w-2 bg-emerald-500"
                  : "w-2 bg-slate-300 dark:bg-slate-700"
              }`}
            />
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-800">
          <button
            type="button"
            onClick={handleFinish}
            className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-300 font-bold transition cursor-pointer"
          >
            Skip Tour
          </button>

          <div className="flex items-center gap-2">
            {!isFirstStep && (
              <button
                type="button"
                onClick={handlePrev}
                className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
              >
                ← Back
              </button>
            )}
            <button
              type="button"
              onClick={handleNext}
              className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-extrabold shadow-md transition cursor-pointer flex items-center gap-1"
            >
              <span>{isLastStep ? "Submit / Finish ✨" : "Next Step →"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
