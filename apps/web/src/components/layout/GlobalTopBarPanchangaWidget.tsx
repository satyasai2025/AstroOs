"use client";

import React, { useState, useEffect } from "react";
import { useWorkflowStore } from "@/lib/store";

export function GlobalTopBarPanchangaWidget() {
  const [timeStr, setTimeStr] = useState<string>("");
  const request = useWorkflowStore((s) => s.request);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      };
      setTimeStr(`${now.toLocaleDateString("en-IN", options)} IST`);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const locationName = request?.place_name ? request.place_name.split(",")[0] : "New Delhi";

  return (
    <div className="hidden 2xl:flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-900/80 border border-slate-800 text-[11px] font-mono whitespace-nowrap">
      <span className="text-amber-400 font-bold">⏰ {timeStr || "18 May, 14:35 IST"}</span>
      <span className="text-slate-600">·</span>
      <span className="text-slate-300 truncate max-w-[100px]">📍 {locationName}</span>
    </div>
  );
}
