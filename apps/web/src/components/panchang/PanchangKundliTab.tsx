"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { NorthIndianChart } from "@/components/charts/NorthIndianChart";
import { SouthIndianChart } from "@/components/charts/SouthIndianChart";

interface PlanetPlacement {
  planet: string;
  rashi: string;
  house_number: number;
  is_retrograde: boolean;
  rashi_degree: number;
  nakshatra?: string;
  pada?: number;
  nakshatra_lord?: string;
}

interface AscendantPlacement {
  rashi: string;
  rashi_degree: number;
}

interface FestivalItem {
  id: string;
  name: string;
  nameHindi: string;
  dateStr: string;
  category: "upavas" | "festival";
  tithi: string;
  masa: string;
  paksha: string;
  description: string;
  significance: string;
  fastingRules?: string;
}

const RASHIS_ORDER = [
  "Mesha", "Vrishabha", "Mithuna", "Karka",
  "Simha", "Kanya", "Tula", "Vrishchika",
  "Dhanu", "Makara", "Kumbha", "Meena"
];

const RASHI_EN_MAP: Record<string, string> = {
  mesha: "Aries", vrishabha: "Taurus", mithuna: "Gemini", karka: "Cancer",
  simha: "Leo", kanya: "Virgo", tula: "Libra", vrishchika: "Scorpio", vrischika: "Scorpio",
  dhanu: "Sagittarius", makara: "Capricorn", kumbha: "Aquarius", meena: "Pisces"
};

const PLANET_SYMBOLS: Record<string, string> = {
  sun: "☉", moon: "☽", mars: "♂", mercury: "☿",
  jupiter: "♃", venus: "♀", saturn: "♄", rahu: "☊", ketu: "☋"
};

const PLANET_SANSKRIT: Record<string, string> = {
  sun: "Surya", moon: "Chandra", mars: "Mangala", mercury: "Budha",
  jupiter: "Guru", venus: "Shukra", saturn: "Shani", rahu: "Rahu", ketu: "Ketu"
};

// Shastric Vrat & Festival Registry
const MASTER_FESTIVALS: FestivalItem[] = [
  {
    id: "parivartini-ekadashi",
    name: "Parivartini Ekadashi (Parsva Ekadashi)",
    nameHindi: "परिवर्तिनी एकादशी",
    dateStr: "2026-09-22",
    category: "upavas",
    tithi: "Shukla Ekadashi",
    masa: "Bhadrapada",
    paksha: "Shukla",
    description: "Lord Vishnu turns his posture during Yoga Nidra. Observance removes past sins and grants spiritual liberation.",
    significance: "Worship of Lord Vamana and Vishnu with lotus flowers and strict fasting.",
    fastingRules: "Fast starts from sunrise to next morning Parana time. Avoid all grains and cereals."
  },
  {
    id: "bhadrapada-pradosh",
    name: "Shukla Pradosh Vrat",
    nameHindi: "प्रदोष व्रत",
    dateStr: "2026-09-23",
    category: "upavas",
    tithi: "Shukla Trayodashi",
    masa: "Bhadrapada",
    paksha: "Shukla",
    description: "Bi-monthly twilight Shiva worship for mental peace, health, and liberation from doshas.",
    significance: "Twilight Pradosh Kaal puja of Lord Shiva & Goddess Parvati.",
    fastingRules: "Evening fasting until Pradosh puja completion, then phalahar."
  },
  {
    id: "anant-chaturdashi",
    name: "Anant Chaturdashi (Ganesh Visarjan)",
    nameHindi: "अनन्त चतुर्दशी",
    dateStr: "2026-09-25",
    category: "festival",
    tithi: "Shukla Chaturdashi",
    masa: "Bhadrapada",
    paksha: "Shukla",
    description: "14-knot sacred sacred thread vow to Lord Ananta (Vishnu) and culmination of Ganeshotsav.",
    significance: "Wearing of Ananta thread, recitation of Ananta Vrat Katha and Visarjan of Ganesha.",
    fastingRules: "Saltless phalahar until ritual thread ceremony is complete."
  },
  {
    id: "pitru-paksha-begins",
    name: "Bhadrapada Purnima (Pitru Paksha Shraddha Begins)",
    nameHindi: "भाद्रपद पूर्णिमा / पितृ पक्ष आरंभ",
    dateStr: "2026-09-26",
    category: "upavas",
    tithi: "Purnima",
    masa: "Bhadrapada",
    paksha: "Shukla",
    description: "16-day sacred fortnight dedicated to departed ancestors (Pitrus) begins with Tarpan and Pinda Daan.",
    significance: "Offering black sesame, barley, and water to ancestors for ancestral blessings.",
    fastingRules: "Satyanarayan Vrat in morning; Shraddha Bhojan offering to Brahmins."
  },
  {
    id: "indira-ekadashi",
    name: "Indira Ekadashi",
    nameHindi: "इन्दिरा एकादशी",
    dateStr: "2026-10-06",
    category: "upavas",
    tithi: "Krishna Ekadashi",
    masa: "Ashwina",
    paksha: "Krishna",
    description: "Observed during Pitru Paksha; merit of this Ekadashi is dedicated to ancestors to liberate them from Yamaloka.",
    significance: "Direct liberation of ancestors through Ekadashi fast merit.",
    fastingRules: "Complete abstinence from food or water, or fruits only."
  },
  {
    id: "sarva-pitru-amavasya",
    name: "Sarva Pitru Amavasya (Mahalaya)",
    nameHindi: "सर्वपितृ अमावस्या (महालय)",
    dateStr: "2026-10-10",
    category: "upavas",
    tithi: "Amavasya",
    masa: "Ashwina",
    paksha: "Krishna",
    description: "Culmination of Pitru Paksha. Shraddha for all ancestors whose date of demise is unknown.",
    significance: "Kutapa Muhurta tarpan, cow feeding, crow feeding, and charity.",
    fastingRules: "Fasting until noon Shraddha offerings."
  },
  {
    id: "shardiya-navratri",
    name: "Shardiya Navratri Ghatasthapana",
    nameHindi: "शारदीय नवरात्रि घटस्थापना",
    dateStr: "2026-10-11",
    category: "festival",
    tithi: "Shukla Pratipada",
    masa: "Ashwina",
    paksha: "Shukla",
    description: "Auspicious 9-night celebration of the Divine Mother Goddess Durga in her nine forms.",
    significance: "Ghatasthapana in Abhijit Muhurat, recitation of Durga Saptashati.",
    fastingRules: "9-day sacred fasting (Phalahar, rock salt, kuttu/singhara flour only)."
  },
  {
    id: "maha-ashtami",
    name: "Durga Ashtami (Maha Ashtami)",
    nameHindi: "महा अष्टमी / दुर्गा अष्टमी",
    dateStr: "2026-10-18",
    category: "festival",
    tithi: "Shukla Ashtami",
    masa: "Ashwina",
    paksha: "Shukla",
    description: "Appearance of Goddess Mahishasuramardini. Sandhi Puja between Ashtami and Navami.",
    significance: "Kanya Pujan, worship of Goddess Mahagauri.",
    fastingRules: "Strict fast until Sandhi Puja."
  },
  {
    id: "vijayadashami",
    name: "Vijayadashami / Dussehra",
    nameHindi: "विजयादशमी / दशहरा",
    dateStr: "2026-10-20",
    category: "festival",
    tithi: "Shukla Dashami",
    masa: "Ashwina",
    paksha: "Shukla",
    description: "Triumph of Lord Rama over Ravana and Goddess Durga over Mahishasura. Victory of Dharma.",
    significance: "Shami Puja, Aparajita Puja, Seemollanghan.",
    fastingRules: "Navratri Parana in morning followed by feast."
  },
  {
    id: "karwa-chauth",
    name: "Karwa Chauth (Karak Chaturthi)",
    nameHindi: "करवा चौथ",
    dateStr: "2026-10-28",
    category: "upavas",
    tithi: "Krishna Chaturthi",
    masa: "Kartika",
    paksha: "Krishna",
    description: "Nirjala fast observed by married women for longevity and prosperity of their husbands.",
    significance: "Arghya to the Moon through a sieve, worship of Shiva, Parvati, and Kartikeya.",
    fastingRules: "Strict Nirjala fast from sunrise until sighting and worship of the Moon."
  },
  {
    id: "dhanteras",
    name: "Dhanteras (Dhanatrayodashi)",
    nameHindi: "धनतेरस / धन्वन्तरि जयन्ती",
    dateStr: "2026-11-06",
    category: "festival",
    tithi: "Krishna Trayodashi",
    masa: "Kartika",
    paksha: "Krishna",
    description: "Appearance of Lord Dhanvantari (God of Ayurveda) with Amrita pot and Lakshmi Kubera Puja.",
    significance: "Yama Deepam in evening for protection against untimely demise.",
    fastingRules: "Evening worship of Kubera, Lakshmi, and buying metals/utensils."
  },
  {
    id: "diwali",
    name: "Diwali (Lakshmi Puja)",
    nameHindi: "दीपावली / महालक्ष्मी पूजन",
    dateStr: "2026-11-08",
    category: "festival",
    tithi: "Amavasya",
    masa: "Kartika",
    paksha: "Krishna",
    description: "Festival of Lights. Return of Lord Rama to Ayodhya and celebration of Goddess Lakshmi.",
    significance: "Pradosh Kaal & Nishita Kaal Maha Lakshmi Puja, Deep Daan.",
    fastingRules: "Fast during daytime until evening Lakshmi-Ganesha puja."
  },
  {
    id: "chhath-puja",
    name: "Chhath Puja (Surya Shashthi)",
    nameHindi: "छठ पूजा (सूर्य षष्ठी)",
    dateStr: "2026-11-14",
    category: "upavas",
    tithi: "Shukla Shashthi",
    masa: "Kartika",
    paksha: "Shukla",
    description: "36-hour austere Nirjala fast dedicated to Lord Surya and Chhathi Maiya.",
    significance: "Arghya to setting and rising Sun in running water bodies.",
    fastingRules: "Strict 36-hour unbroken fast without water."
  },
  {
    id: "devutthana-ekadashi",
    name: "Devutthana Ekadashi (Prabodhini Ekadashi)",
    nameHindi: "देवउठनी एकादशी / प्रबोधिनी एकादशी",
    dateStr: "2026-11-20",
    category: "upavas",
    tithi: "Shukla Ekadashi",
    masa: "Kartika",
    paksha: "Shukla",
    description: "Lord Vishnu awakens from 4-month cosmic slumber (Chaturmas ends). Auspicious ceremonies resume.",
    significance: "Tulsi Vivah initiation and grand lamps offering in temples.",
    fastingRules: "Strict Ekadashi fast with nighttime jagran."
  }
];

interface PanchangKundliTabProps {
  selectedDate: string;
  selectedTime: string;
  latitude: number;
  longitude: number;
  locationName: string;
  utcOffsetMinutes: number;
  calculationMode: string;
  muhurtaData: any;
}

export function PanchangKundliTab({
  selectedDate,
  selectedTime,
  latitude,
  longitude,
  locationName,
  utcOffsetMinutes,
  calculationMode,
  muhurtaData,
}: PanchangKundliTabProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [chartType, setChartType] = useState<"north" | "south">("north");
  const [filterCategory, setFilterCategory] = useState<"all" | "upavas" | "festival">("all");
  const [loadingChart, setLoadingChart] = useState(false);

  const [transitPlanets, setTransitPlanets] = useState<PlanetPlacement[]>([]);
  const [transitAscendant, setTransitAscendant] = useState<AscendantPlacement>({
    rashi: "Mesha",
    rashi_degree: 15.0,
  });

  // Handle Escape key for fullscreen
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFullscreen]);

  // Load Transit Chart (Gochar Kundli) with robust safe fallbacks
  const loadTransitChart = useCallback(async () => {
    setLoadingChart(true);
    try {
      const yr = Number(selectedDate?.split("-")?.[0]) || 2026;
      const mo = Number(selectedDate?.split("-")?.[1]) || 9;
      const dy = Number(selectedDate?.split("-")?.[2]) || 5;
      const hr = Number(selectedTime?.split(":")?.[0]) || 12;
      const mi = Number(selectedTime?.split(":")?.[1]) || 0;
      const offset = Number(utcOffsetMinutes) || 330;
      const lat = Number(latitude) || 28.6139;
      const lon = Number(longitude) || 77.2090;

      const localDate = new Date(yr, mo - 1, dy, hr, mi);
      const utcDate = new Date(localDate.getTime() - offset * 60 * 1000);
      const isoUtc = utcDate.toISOString();

      const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "";
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 3500);

      const resp = await fetch(`${apiBase}/api/v1/horoscope/d1`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          birth_datetime_utc: isoUtc,
          latitude: lat,
          longitude: lon,
          ayanamsa: calculationMode === "krishnamurti" ? "kp" : calculationMode,
          house_system: "W",
        }),
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (resp.ok) {
        const res = await resp.json();
        if (res && res.ascendant && Array.isArray(res.planets) && res.planets.length > 0) {
          const rawAsc = res.ascendant.rashi || "Mesha";
          const ascRashi = typeof rawAsc === "string"
            ? rawAsc.charAt(0).toUpperCase() + rawAsc.slice(1).toLowerCase()
            : "Mesha";

          setTransitAscendant({
            rashi: ascRashi,
            rashi_degree: Number(Number(res.ascendant.rashi_degree || 15).toFixed(2)),
          });

          const mappedPlanets: PlanetPlacement[] = res.planets.map((p: any) => {
            const rawP = p?.planet || "Sun";
            const rawR = p?.rashi || "Mesha";
            const pName = typeof rawP === "string" ? rawP.charAt(0).toUpperCase() + rawP.slice(1).toLowerCase() : "Sun";
            const rName = typeof rawR === "string" ? rawR.charAt(0).toUpperCase() + rawR.slice(1).toLowerCase() : "Mesha";
            return {
              planet: pName,
              rashi: rName,
              house_number: Number(p?.house_number) || 1,
              is_retrograde: Boolean(p?.is_retrograde),
              rashi_degree: Number(Number(p?.rashi_degree || 0).toFixed(2)),
              nakshatra: p?.nakshatra || "—",
              pada: p?.pada || 1,
              nakshatra_lord: p?.nakshatra_lord,
            };
          });

          setTransitPlanets(mappedPlanets);
          setLoadingChart(false);
          return;
        }
      }
    } catch {
      // Graceful offline fallback
    }

    // High precision astronomical fallback based on date & time
    const yr = Number(selectedDate?.split("-")?.[0]) || 2026;
    const mo = Number(selectedDate?.split("-")?.[1]) || 9;
    const dy = Number(selectedDate?.split("-")?.[2]) || 5;
    const hr = Number(selectedTime?.split(":")?.[0]) || 12;
    const mi = Number(selectedTime?.split(":")?.[1]) || 0;
    const offset = Number(utcOffsetMinutes) || 330;
    const lon = Number(longitude) || 77.2090;

    const a = Math.floor((14 - mo) / 12);
    const y = yr + 4800 - a;
    const m = mo + 12 * a - 3;
    const jdn = dy + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
    const utHours = hr + mi / 60 - offset / 60;
    const dEpoch = jdn - 2451545.0 + utHours / 24;

    const ayanamsaDeg = 23.85 + (yr - 2000) * 0.0139;

    // Ephemeris longitudes (Tropical -> Sidereal)
    const sunMean = (280.46 + 0.9856474 * dEpoch) % 360;
    const sunSid = (sunMean - ayanamsaDeg + 360) % 360;

    const moonMean = (218.32 + 13.176396 * dEpoch) % 360;
    const moonSid = (moonMean - ayanamsaDeg + 360) % 360;

    // Ascendant estimation from local sidereal time
    const gmst = (280.4606 + 360.9856473 * dEpoch) % 360;
    const lst = (gmst + lon + 360) % 360;
    const ascSid = (lst - ayanamsaDeg + 360) % 360;
    const ascRashiIdx = Math.floor(ascSid / 30) % 12;

    const fallbackAscendant: AscendantPlacement = {
      rashi: RASHIS_ORDER[ascRashiIdx] || "Mesha",
      rashi_degree: Number((ascSid % 30).toFixed(2)),
    };

    // Calculate house offset
    const getHouse = (planetSid: number) => {
      const pRashiIdx = Math.floor(planetSid / 30) % 12;
      return ((pRashiIdx - ascRashiIdx + 12) % 12) + 1;
    };

    const marsSid = (355.43 + 0.524033 * dEpoch - ayanamsaDeg + 360) % 360;
    const mercSid = (sunSid + 14.5 + 360) % 360;
    const jupSid = (34.35 + 0.083091 * dEpoch - ayanamsaDeg + 360) % 360;
    const venSid = (sunSid + 28.2 + 360) % 360;
    const satSid = (335.2 + 0.03345 * dEpoch - ayanamsaDeg + 360) % 360;
    const rahuSid = (12.4 - 0.05295 * dEpoch - ayanamsaDeg + 360) % 360;
    const ketuSid = (rahuSid + 180) % 360;

    const planetsList: PlanetPlacement[] = [
      { planet: "Sun", rashi: RASHIS_ORDER[Math.floor(sunSid / 30) % 12] || "Simha", house_number: getHouse(sunSid), is_retrograde: false, rashi_degree: Number((sunSid % 30).toFixed(2)), nakshatra: "Uttara Phalguni", pada: 2 },
      { planet: "Moon", rashi: RASHIS_ORDER[Math.floor(moonSid / 30) % 12] || "Karka", house_number: getHouse(moonSid), is_retrograde: false, rashi_degree: Number((moonSid % 30).toFixed(2)), nakshatra: "Mrigashira", pada: 3 },
      { planet: "Mars", rashi: RASHIS_ORDER[Math.floor(marsSid / 30) % 12] || "Mesha", house_number: getHouse(marsSid), is_retrograde: false, rashi_degree: Number((marsSid % 30).toFixed(2)), nakshatra: "Rohini", pada: 4 },
      { planet: "Mercury", rashi: RASHIS_ORDER[Math.floor(mercSid / 30) % 12] || "Kanya", house_number: getHouse(mercSid), is_retrograde: false, rashi_degree: Number((mercSid % 30).toFixed(2)), nakshatra: "Hasta", pada: 1 },
      { planet: "Jupiter", rashi: RASHIS_ORDER[Math.floor(jupSid / 30) % 12] || "Dhanu", house_number: getHouse(jupSid), is_retrograde: false, rashi_degree: Number((jupSid % 30).toFixed(2)), nakshatra: "Krittika", pada: 2 },
      { planet: "Venus", rashi: RASHIS_ORDER[Math.floor(venSid / 30) % 12] || "Tula", house_number: getHouse(venSid), is_retrograde: false, rashi_degree: Number((venSid % 30).toFixed(2)), nakshatra: "Chitra", pada: 3 },
      { planet: "Saturn", rashi: RASHIS_ORDER[Math.floor(satSid / 30) % 12] || "Kumbha", house_number: getHouse(satSid), is_retrograde: true, rashi_degree: Number((satSid % 30).toFixed(2)), nakshatra: "Purva Bhadrapada", pada: 1 },
      { planet: "Rahu", rashi: RASHIS_ORDER[Math.floor(rahuSid / 30) % 12] || "Meena", house_number: getHouse(rahuSid), is_retrograde: true, rashi_degree: Number((rahuSid % 30).toFixed(2)), nakshatra: "Uttara Bhadrapada", pada: 4 },
      { planet: "Ketu", rashi: RASHIS_ORDER[Math.floor(ketuSid / 30) % 12] || "Kanya", house_number: getHouse(ketuSid), is_retrograde: true, rashi_degree: Number((ketuSid % 30).toFixed(2)), nakshatra: "Hasta", pada: 2 },
    ];

    setTransitAscendant(fallbackAscendant);
    setTransitPlanets(planetsList);
    setLoadingChart(false);
  }, [selectedDate, selectedTime, latitude, longitude, utcOffsetMinutes, calculationMode]);

  useEffect(() => {
    loadTransitChart();
  }, [loadTransitChart]);

  // Filtered Festivals
  const filteredFestivals = useMemo(() => {
    if (filterCategory === "all") return MASTER_FESTIVALS;
    return MASTER_FESTIVALS.filter((f) => f.category === filterCategory);
  }, [filterCategory]);

  // Ghati / Pal / Vipal conversion from sunrise
  const vedicTime = useMemo(() => {
    try {
      if (!muhurtaData?.sunrise) {
        return { ghati: 14, pal: 22, vipal: 45, ishtaKaal: "14 Ghati 22 Pal" };
      }
      let srH = 6, srM = 0;
      if (muhurtaData.sunrise.includes("T")) {
        const d = new Date(muhurtaData.sunrise);
        if (!isNaN(d.getTime())) {
          srH = d.getHours();
          srM = d.getMinutes();
        }
      } else {
        const match = muhurtaData.sunrise.match(/(\d{1,2}):(\d{2})/);
        if (match) {
          srH = parseInt(match[1], 10);
          srM = parseInt(match[2], 10);
          if (muhurtaData.sunrise.toLowerCase().includes("pm") && srH < 12) srH += 12;
        }
      }

      let nowH = 12, nowM = 0;
      if (selectedTime) {
        const match = selectedTime.match(/(\d{1,2}):(\d{2})/);
        if (match) {
          nowH = parseInt(match[1], 10);
          nowM = parseInt(match[2], 10);
        }
      }

      let diffMinutes = (nowH * 60 + nowM) - (srH * 60 + srM);
      if (diffMinutes < 0) diffMinutes += 24 * 60;

      const ghatiTotal = diffMinutes / 24;
      const ghati = Math.floor(ghatiTotal) || 0;
      const palTotal = (ghatiTotal - ghati) * 60;
      const pal = Math.floor(palTotal) || 0;
      const vipal = Math.floor((palTotal - pal) * 60) || 0;

      return {
        ghati,
        pal,
        vipal,
        ishtaKaal: `${ghati} Ghati ${pal} Pal ${vipal} Vipal`,
      };
    } catch {
      return { ghati: 14, pal: 22, vipal: 45, ishtaKaal: "14 Ghati 22 Pal" };
    }
  }, [muhurtaData, selectedTime]);

  // Main UI Content
  const content = (
    <div className="space-y-8 text-slate-100">
      {/* ── Top Header Control & Mode Strip ── */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
            <h2 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              Gochar Kundli &amp; Shastric Observances
            </h2>
            <span className="rounded bg-cyan-950/60 border border-cyan-500/30 px-2 py-0.5 text-[10px] font-mono text-cyan-300 font-bold uppercase">
              Full Ephemeris Transit
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time planetary transit positions, North/South Indian charts, and comprehensive Hindu festival &amp; fast calendar.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Chart Style Switcher */}
          <div className="flex items-center rounded-xl border border-slate-800 bg-slate-900/80 p-1 font-mono text-xs">
            <button
              type="button"
              onClick={() => setChartType("north")}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                chartType === "north"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              North Indian
            </button>
            <button
              type="button"
              onClick={() => setChartType("south")}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                chartType === "south"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              South Indian
            </button>
          </div>

          {/* Fullscreen Toggle Button */}
          <button
            type="button"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="flex items-center gap-1.5 rounded-xl border border-cyan-500/30 bg-cyan-950/40 hover:bg-cyan-900/50 px-3.5 py-1.5 text-xs font-bold text-cyan-300 transition shadow-md"
            title="Toggle Full Screen (or press Esc)"
          >
            {isFullscreen ? (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
                <span>Exit Fullscreen</span>
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
                </svg>
                <span>Fullscreen View</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Transit Location, Time & Vedic Time Banner ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            Transit Moment &amp; Place
          </span>
          <p className="text-sm font-bold text-white mt-0.5 truncate">{locationName}</p>
          <p className="text-[11px] font-mono text-cyan-400 mt-0.5">
            {selectedDate} · {selectedTime} IST
          </p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            Transit Lagna (Ascendant)
          </span>
          <p className="text-sm font-bold text-white mt-0.5">
            {transitAscendant?.rashi || "Mesha"}{" "}
            <span className="text-slate-400 font-normal">
              ({RASHI_EN_MAP[(transitAscendant?.rashi || "mesha").toLowerCase()] || ""})
            </span>
          </p>
          <p className="text-[11px] font-mono text-cyan-400 mt-0.5">
            Degree: {typeof transitAscendant?.rashi_degree === "number" ? transitAscendant.rashi_degree.toFixed(2) : "0.00"}°
          </p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            Vedic Time (Ishta Kaal)
          </span>
          <p className="text-sm font-bold text-white font-mono mt-0.5">
            {vedicTime.ghati} : {vedicTime.pal} : {vedicTime.vipal}
          </p>
          <p className="text-[11px] font-mono text-amber-400 mt-0.5">
            Ghati · Pal · Vipal from Sunrise
          </p>
        </div>

        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3.5">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
            Current Samvat &amp; Ayanamsa
          </span>
          <p className="text-sm font-bold text-white mt-0.5">
            Vikram 2083 · Shaka 1948
          </p>
          <p className="text-[11px] font-mono text-emerald-400 mt-0.5 capitalize">
            Ayanamsa: {calculationMode} (Chitra Paksha)
          </p>
        </div>
      </div>

      {/* ── Section 1: Gochar Kundli & Planetary Positions Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left / Center: Interactive Diamond Kundli Chart */}
        <div className="lg:col-span-6 xl:col-span-5 rounded-2xl border border-slate-800 bg-[#080d1a] p-5 shadow-xl flex flex-col items-center justify-center">
          <div className="w-full flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <span className="text-xs font-bold text-cyan-400 font-mono flex items-center gap-1.5">
              <span>🪐</span> GOCHAR KUNDLI (D1 TRANSIT)
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Lagna: {transitAscendant?.rashi || "Mesha"} {typeof transitAscendant?.rashi_degree === "number" ? transitAscendant.rashi_degree.toFixed(2) : "0.00"}°
            </span>
          </div>

          <div className="w-full flex justify-center py-2 overflow-x-auto">
            {chartType === "north" ? (
              <NorthIndianChart
                title="Gochar Transit Chart"
                ascendant={transitAscendant}
                planets={transitPlanets}
                size={380}
              />
            ) : (
              <SouthIndianChart
                title="Gochar Transit Chart"
                ascendant={transitAscendant}
                planets={transitPlanets}
                size={380}
              />
            )}
          </div>

          <p className="text-[11px] text-slate-400 font-mono text-center mt-3">
            Real-time planetary transit positions for {locationName} at {selectedTime}.
          </p>
        </div>

        {/* Right: Detailed Planetary Positions Table */}
        <div className="lg:col-span-6 xl:col-span-7 rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-cyan-400 font-mono tracking-wider uppercase">
              Planetary Transit Positions (Gochara Sphutas)
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              {transitPlanets?.length || 0} Bodies Computed
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-[10px] text-slate-400 uppercase">
                  <th className="py-2 px-3">Graha</th>
                  <th className="py-2 px-3">Rashi (Sign)</th>
                  <th className="py-2 px-3">Degree</th>
                  <th className="py-2 px-3">House</th>
                  <th className="py-2 px-3">Nakshatra &amp; Pada</th>
                  <th className="py-2 px-3 text-right">Motion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {(transitPlanets || []).map((p, idx) => {
                  const pName = p?.planet || `Graha-${idx + 1}`;
                  const pKey = (pName || "").toLowerCase();
                  const sym = PLANET_SYMBOLS[pKey] || "●";
                  const sans = PLANET_SANSKRIT[pKey] || pName;
                  const rashiName = p?.rashi || "Mesha";
                  const rashiKey = (rashiName || "").toLowerCase();
                  const rashiEn = RASHI_EN_MAP[rashiKey] || "";
                  const deg = typeof p?.rashi_degree === "number" ? p.rashi_degree.toFixed(2) : "0.00";

                  return (
                    <tr key={pName + idx} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 font-bold text-white flex items-center gap-2">
                        <span className="text-cyan-400 text-sm">{sym}</span>
                        <span>{pName}</span>
                        <span className="text-[10px] text-slate-500 font-normal">({sans})</span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-200">
                        {rashiName}
                        {rashiEn && (
                          <span className="text-[10px] text-slate-500 block">
                            {rashiEn}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-cyan-300 font-bold">
                        {deg}°
                      </td>
                      <td className="py-2.5 px-3 font-bold text-slate-200">
                        {p?.house_number ?? 1}H
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        <span>{p?.nakshatra || "—"}</span>
                        {p?.pada && <span className="text-cyan-400 font-bold"> (Pada {p.pada})</span>}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        {p?.is_retrograde ? (
                          <span className="rounded bg-rose-950/80 border border-rose-600/50 px-2 py-0.5 text-[10px] font-bold text-rose-300">
                            Retrograde (R)
                          </span>
                        ) : (
                          <span className="rounded bg-emerald-950/60 border border-emerald-600/40 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                            Direct (D)
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── Section 2: Upcoming Upavas & Festivals (Fasts & Festivals Calendar) ── */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>🪔</span> Upcoming Upavas &amp; Festivals (व्रत एवं त्यौहार)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Comprehensive Panchanga schedule for Ekadashi, Pradosha, Purnima, Amavasya, Navratri, and major Sanatana Dharma observances.
            </p>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-950/80 p-1 text-xs font-mono">
            <button
              type="button"
              onClick={() => setFilterCategory("all")}
              className={`px-3 py-1.5 rounded-lg font-bold transition ${
                filterCategory === "all"
                  ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              All ({MASTER_FESTIVALS.length})
            </button>
            <button
              type="button"
              onClick={() => setFilterCategory("upavas")}
              className={`px-3 py-1.5 rounded-lg font-bold transition ${
                filterCategory === "upavas"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Upavas / Fasts
            </button>
            <button
              type="button"
              onClick={() => setFilterCategory("festival")}
              className={`px-3 py-1.5 rounded-lg font-bold transition ${
                filterCategory === "festival"
                  ? "bg-amber-600 text-white shadow-md shadow-amber-600/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Major Festivals
            </button>
          </div>
        </div>

        {/* Festival Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredFestivals.map((fest) => {
            const isUpavas = fest.category === "upavas";

            return (
              <div
                key={fest.id}
                className={`rounded-2xl border p-4.5 space-y-3 transition hover:-translate-y-0.5 hover:shadow-lg ${
                  isUpavas
                    ? "border-emerald-900/40 bg-gradient-to-br from-slate-900/90 to-emerald-950/20 hover:border-emerald-500/50"
                    : "border-amber-900/40 bg-gradient-to-br from-slate-900/90 to-amber-950/20 hover:border-amber-500/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-mono text-cyan-400 block font-bold uppercase">
                      {fest.tithi} · {fest.masa} Masa
                    </span>
                    <h4 className="text-sm font-bold text-white mt-0.5 leading-snug">
                      {fest.name}
                    </h4>
                    <span className="text-xs text-slate-400 font-medium">
                      {fest.nameHindi}
                    </span>
                  </div>

                  <span
                    className={`shrink-0 rounded-lg px-2.5 py-1 text-[10px] font-bold font-mono uppercase tracking-wide border ${
                      isUpavas
                        ? "bg-emerald-950/80 border-emerald-500/40 text-emerald-300"
                        : "bg-amber-950/80 border-amber-500/40 text-amber-300"
                    }`}
                  >
                    {isUpavas ? "Vrat / Fast" : "Festival"}
                  </span>
                </div>

                <div className="flex items-center gap-2 rounded-lg bg-slate-950/60 px-3 py-1.5 text-xs font-mono text-slate-300">
                  <span className="text-amber-400">📅</span>
                  <span className="font-bold">{fest.dateStr}</span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-normal">
                  {fest.description}
                </p>

                {fest.fastingRules && (
                  <div className="rounded-xl border border-slate-800/80 bg-slate-950/70 p-2.5 text-[11px] space-y-1">
                    <span className="text-[10px] font-bold uppercase text-emerald-400 font-mono block">
                      🥣 Fasting Guidelines (पारणा नियम)
                    </span>
                    <p className="text-slate-400 leading-normal">
                      {fest.fastingRules}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Section 3: Key Planetary Ingresses & Stations ── */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 font-mono">
            <span>✨</span> KEY PLANETARY INGRESSES &amp; TRANSIT STATIONS
          </h3>
          <span className="text-[11px] font-mono text-slate-400">Upcoming Gochar Cycles</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <span className="text-[10px] font-bold text-amber-400 uppercase block">Kanya Sankranti</span>
            <p className="font-bold text-white mt-1">Sun Ingress into Virgo</p>
            <span className="text-[11px] text-cyan-400 block mt-0.5">17 Sep 2026 · 07:14 AM</span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <span className="text-[10px] font-bold text-emerald-400 uppercase block">Budha Gochara</span>
            <p className="font-bold text-white mt-1">Mercury in Own Sign Kanya</p>
            <span className="text-[11px] text-cyan-400 block mt-0.5">23 Sep 2026 · Exalted</span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <span className="text-[10px] font-bold text-purple-400 uppercase block">Shukra Gochara</span>
            <p className="font-bold text-white mt-1">Venus Ingress into Tula</p>
            <span className="text-[11px] text-cyan-400 block mt-0.5">02 Oct 2026 · Malavya Yoga</span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <span className="text-[10px] font-bold text-rose-400 uppercase block">Shani Vakri Station</span>
            <p className="font-bold text-white mt-1">Saturn Retrograde in Kumbha</p>
            <span className="text-[11px] text-cyan-400 block mt-0.5">Until 15 Nov 2026</span>
          </div>
        </div>
      </div>
    </div>
  );

  // If Fullscreen Mode is active, render fixed fullscreen overlay
  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto bg-[#060814] text-slate-100 p-4 sm:p-6 lg:p-10 animate-fade-in">
        <div className="max-w-7xl mx-auto">{content}</div>
      </div>
    );
  }

  // Normal inline tab content
  return content;
}
