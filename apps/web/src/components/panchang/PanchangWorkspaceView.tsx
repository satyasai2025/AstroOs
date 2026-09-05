'use client';

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useTheme } from "@/components/layout/ThemeProvider";
import { useWorkflowStore } from "@/lib/store";
import { api, ApiError } from "@/lib/api";
import {
  Clock,
  Calendar,
  Compass,
  Sparkles,
  Sun,
  Moon,
} from "@/components/phalita/Icons";
import { PanchangKundliTab } from "@/components/panchang/PanchangKundliTab";

// ── Backend API types ────────────────────────────────────────────────────────

interface HoraResponse {
  index: number;
  lord: string;
  start: string;
  end: string;
  is_day: boolean;
}

interface InauspiciousPeriodResponse {
  name: string;
  start: string;
  end: string;
}

interface AuspiciousWindowResponse {
  name: string;
  start: string;
  end: string;
  is_auspicious: boolean;
  description: string;
}

interface ChoghadiyaResponse {
  index: number;
  name: string;
  nature: string;
  start: string;
  end: string;
  is_day: boolean;
  lord: string;
}

interface TithiLimbResponse {
  number: number;
  name: string;
  paksha: string;
  completion_percent: number;
  end_time: string | null;
  lord: string;
  group: string;
}

interface VaraLimbResponse {
  number: number;
  name: string;
  lord: string;
  nature: string;
}

interface NakshatraLimbResponse {
  number: number;
  name: string;
  pada: number;
  lord: string;
  degree_in_nakshatra: number;
  completion_percent: number;
  end_time: string | null;
  quality: string;
}

interface YogaLimbResponse {
  number: number;
  name: string;
  completion_percent: number;
  end_time: string | null;
  meaning: string;
}

interface KaranaLimbResponse {
  number: number;
  name: string;
  is_fixed: boolean;
  completion_percent: number;
  end_time: string | null;
  nature: string;
}

interface SamvatsaraMasaResponse {
  shaka_year: number;
  shaka_samvatsara: string;
  vikram_year: number;
  vikram_samvatsara: string;
  amanta_masa: string;
  purnimanta_masa: string;
  is_adhika: boolean;
}

interface CelestialBodiesResponse {
  sun_sign: string;
  sun_sign_degree: number;
  sun_longitude: number;
  moon_sign: string;
  moon_sign_degree: number;
  moon_longitude: number;
  ascendant_sign: string;
  ascendant_degree: number;
  moonrise: string | null;
  moonset: string | null;
}

interface TarabalaDetailResponse {
  tara_number: number;
  tara_name: string;
  is_auspicious: boolean;
  score: number;
  description: string;
}

interface ChandrabalaDetailResponse {
  house_from_natal_moon: number;
  status: string;
  is_auspicious: boolean;
  score: number;
  description: string;
}

interface PanchakaDetailResponse {
  remainder: number;
  panchaka_name: string;
  description: string;
  has_dosha: boolean;
  score: number;
}

interface ActivitySuitabilityResponse {
  activity_id: string;
  name: string;
  score: number;
  verdict: string;
  points: string[];
}

interface MuhurtaResponse {
  sunrise: string;
  sunset: string;
  next_sunrise: string;
  horas: HoraResponse[];
  rahukalam: InauspiciousPeriodResponse;
  gulikalam: InauspiciousPeriodResponse;
  yamagandam: InauspiciousPeriodResponse;
  choghadiya: ChoghadiyaResponse[];
  tithi?: TithiLimbResponse;
  vara?: VaraLimbResponse;
  nakshatra?: NakshatraLimbResponse;
  yoga?: YogaLimbResponse;
  karana?: KaranaLimbResponse;
  calendar?: SamvatsaraMasaResponse;
  celestial?: CelestialBodiesResponse;
  abhijit_muhurta?: AuspiciousWindowResponse;
  brahma_muhurta?: AuspiciousWindowResponse;
  dur_muhurta?: InauspiciousPeriodResponse[];
  amrit_kaal?: AuspiciousWindowResponse;
  tarabala?: TarabalaDetailResponse;
  chandrabala?: ChandrabalaDetailResponse;
  panchaka?: PanchakaDetailResponse;
  activities?: ActivitySuitabilityResponse[];
}

interface PlaceResult {
  display_name: string;
  latitude: number;
  longitude: number;
  country?: string;
  state?: string;
}

const NAKSHATRA_NAMES = [
  "1. Ashwini (Ketu)", "2. Bharani (Venus)", "3. Krittika (Sun)", "4. Rohini (Moon)",
  "5. Mrigashira (Mars)", "6. Ardra (Rahu)", "7. Punarvasu (Jupiter)", "8. Pushya (Saturn)",
  "9. Ashlesha (Mercury)", "10. Magha (Ketu)", "11. Purva Phalguni (Venus)", "12. Uttara Phalguni (Sun)",
  "13. Hasta (Moon)", "14. Chitra (Mars)", "15. Swati (Rahu)", "16. Vishakha (Jupiter)",
  "17. Anuradha (Saturn)", "18. Jyeshtha (Mercury)", "19. Mula (Ketu)", "20. Purva Ashadha (Venus)",
  "21. Uttara Ashadha (Sun)", "22. Shravana (Moon)", "23. Dhanishta (Mars)", "24. Shatabhisha (Rahu)",
  "25. Purva Bhadrapada (Jupiter)", "26. Uttara Bhadrapada (Saturn)", "27. Revati (Mercury)"
];

const RASHI_NAMES = [
  "1. Mesha (Aries)", "2. Vrishabha (Taurus)", "3. Mithuna (Gemini)", "4. Karka (Cancer)",
  "5. Simha (Leo)", "6. Kanya (Virgo)", "7. Tula (Libra)", "8. Vrishchika (Scorpio)",
  "9. Dhanu (Sagittarius)", "10. Makara (Capricorn)", "11. Kumbha (Aquarius)", "12. Meena (Pisces)"
];

// Curated In-Memory Cities for Instant Zero-Latency Search
const CLIENT_CITIES: PlaceResult[] = [
  { display_name: "New Delhi, Delhi, India", latitude: 28.6139, longitude: 77.2090, state: "Delhi", country: "India" },
  { display_name: "Pune, Maharashtra, India", latitude: 18.5204, longitude: 73.8567, state: "Maharashtra", country: "India" },
  { display_name: "Mumbai, Maharashtra, India", latitude: 19.0760, longitude: 72.8777, state: "Maharashtra", country: "India" },
  { display_name: "Varanasi, Uttar Pradesh, India", latitude: 25.3176, longitude: 82.9739, state: "Uttar Pradesh", country: "India" },
  { display_name: "Ujjain, Madhya Pradesh, India", latitude: 23.1765, longitude: 75.7885, state: "Madhya Pradesh", country: "India" },
  { display_name: "Ayodhya, Uttar Pradesh, India", latitude: 26.7922, longitude: 82.1998, state: "Uttar Pradesh", country: "India" },
  { display_name: "Mathura, Uttar Pradesh, India", latitude: 27.4924, longitude: 77.6737, state: "Uttar Pradesh", country: "India" },
  { display_name: "Haridwar, Uttarakhand, India", latitude: 29.9457, longitude: 78.1642, state: "Uttarakhand", country: "India" },
  { display_name: "Rishikesh, Uttarakhand, India", latitude: 30.0869, longitude: 78.2676, state: "Uttarakhand", country: "India" },
  { display_name: "Prayagraj, Uttar Pradesh, India", latitude: 25.4358, longitude: 81.8463, state: "Uttar Pradesh", country: "India" },
  { display_name: "Puri, Odisha, India", latitude: 19.8135, longitude: 85.8312, state: "Odisha", country: "India" },
  { display_name: "Dwarka, Gujarat, India", latitude: 22.2394, longitude: 68.9678, state: "Gujarat", country: "India" },
  { display_name: "Rameswaram, Tamil Nadu, India", latitude: 9.2876, longitude: 79.3129, state: "Tamil Nadu", country: "India" },
  { display_name: "Tirupati, Andhra Pradesh, India", latitude: 13.6288, longitude: 79.4192, state: "Andhra Pradesh", country: "India" },
  { display_name: "Madurai, Tamil Nadu, India", latitude: 9.9252, longitude: 78.1198, state: "Tamil Nadu", country: "India" },
  { display_name: "Kanchipuram, Tamil Nadu, India", latitude: 12.8342, longitude: 79.7036, state: "Tamil Nadu", country: "India" },
  { display_name: "Gaya, Bihar, India", latitude: 24.7914, longitude: 85.0002, state: "Bihar", country: "India" },
  { display_name: "Nashik, Maharashtra, India", latitude: 19.9975, longitude: 73.7898, state: "Maharashtra", country: "India" },
  { display_name: "Shirdi, Maharashtra, India", latitude: 19.7667, longitude: 74.4762, state: "Maharashtra", country: "India" },
  { display_name: "Kedarnath, Uttarakhand, India", latitude: 30.7346, longitude: 79.0669, state: "Uttarakhand", country: "India" },
  { display_name: "Badrinath, Uttarakhand, India", latitude: 30.7433, longitude: 79.4938, state: "Uttarakhand", country: "India" },
  { display_name: "Bengaluru, Karnataka, India", latitude: 12.9716, longitude: 77.5946, state: "Karnataka", country: "India" },
  { display_name: "Hyderabad, Telangana, India", latitude: 17.3850, longitude: 78.4867, state: "Telangana", country: "India" },
  { display_name: "Chennai, Tamil Nadu, India", latitude: 13.0827, longitude: 80.2707, state: "Tamil Nadu", country: "India" },
  { display_name: "Kolkata, West Bengal, India", latitude: 22.5726, longitude: 88.3639, state: "West Bengal", country: "India" },
  { display_name: "Ahmedabad, Gujarat, India", latitude: 23.0225, longitude: 72.5714, state: "Gujarat", country: "India" },
  { display_name: "Surat, Gujarat, India", latitude: 21.1702, longitude: 72.8311, state: "Gujarat", country: "India" },
  { display_name: "Jaipur, Rajasthan, India", latitude: 26.9124, longitude: 75.7873, state: "Rajasthan", country: "India" },
  { display_name: "Lucknow, Uttar Pradesh, India", latitude: 26.8467, longitude: 80.9462, state: "Uttar Pradesh", country: "India" },
  { display_name: "Kanpur, Uttar Pradesh, India", latitude: 26.4499, longitude: 80.3319, state: "Uttar Pradesh", country: "India" },
  { display_name: "Patna, Bihar, India", latitude: 25.5941, longitude: 85.1376, state: "Bihar", country: "India" },
  { display_name: "Bhopal, Madhya Pradesh, India", latitude: 23.2599, longitude: 77.4126, state: "Madhya Pradesh", country: "India" },
  { display_name: "Indore, Madhya Pradesh, India", latitude: 22.7196, longitude: 75.8577, state: "Madhya Pradesh", country: "India" },
  { display_name: "Chandigarh, Punjab, India", latitude: 30.7333, longitude: 76.7794, state: "Punjab", country: "India" },
  { display_name: "London, England, United Kingdom", latitude: 51.5074, longitude: -0.1278, state: "England", country: "United Kingdom" },
  { display_name: "New York, New York, United States", latitude: 40.7128, longitude: -74.0060, state: "New York", country: "United States" },
  { display_name: "San Francisco, California, United States", latitude: 37.7749, longitude: -122.4194, state: "California", country: "United States" },
  { display_name: "Dallas, Texas, United States", latitude: 32.7767, longitude: -96.7970, state: "Texas", country: "United States" },
  { display_name: "Toronto, Ontario, Canada", latitude: 43.6532, longitude: -79.3832, state: "Ontario", country: "Canada" },
  { display_name: "Dubai, Dubai, United Arab Emirates", latitude: 25.2048, longitude: 55.2708, state: "Dubai", country: "United Arab Emirates" },
  { display_name: "Singapore, Central, Singapore", latitude: 1.3521, longitude: 103.8198, state: "Central", country: "Singapore" },
  { display_name: "Tokyo, Tokyo, Japan", latitude: 35.6762, longitude: 139.6503, state: "Tokyo", country: "Japan" },
  { display_name: "Sydney, New South Wales, Australia", latitude: -33.8688, longitude: 151.2093, state: "New South Wales", country: "Australia" },
];

function searchClientCities(q: string, limit = 8): PlaceResult[] {
  const norm = q.trim().toLowerCase();
  if (!norm || norm.length < 2) return [];
  return CLIENT_CITIES.filter(c => 
    c.display_name.toLowerCase().includes(norm) ||
    (c.country && c.country.toLowerCase().includes(norm)) ||
    (c.state && c.state.toLowerCase().includes(norm))
  ).slice(0, limit);
}

// ── Authenticated API fetch functions ────────────────────────────────────────

async function fetchMuhurta(
  date: string,
  timeStr: string,
  lat: number,
  lon: number,
  utcOffsetMinutes: number,
  ayanamsa: string,
  natalNakshatra?: number,
  natalMoonSign?: number
): Promise<MuhurtaResponse> {
  const validLat = isNaN(Number(lat)) ? 28.6139 : Number(lat);
  const validLon = isNaN(Number(lon)) ? 77.2090 : Number(lon);
  const validOffset = isNaN(Number(utcOffsetMinutes)) ? 330 : Math.round(Number(utcOffsetMinutes));
  const ayanamsaSlug = ayanamsa === "krishnamurti" ? "kp" : ayanamsa;

  const params = new URLSearchParams({
    local_date: date || new Date().toISOString().split("T")[0],
    local_time: timeStr || "12:00",
    latitude: validLat.toString(),
    longitude: validLon.toString(),
    utc_offset_minutes: validOffset.toString(),
    ayanamsa: ayanamsaSlug,
  });
  if (natalNakshatra) params.set("natal_nakshatra", natalNakshatra.toString());
  if (natalMoonSign) params.set("natal_moon_sign", natalMoonSign.toString());

  return api.get<MuhurtaResponse>(`/api/v1/muhurta?${params}`);
}

async function searchPlacesAPI(query: string): Promise<PlaceResult[]> {
  if (!query || query.trim().length < 2) return [];
  try {
    const data = await api.get<{ results: PlaceResult[] }>(
      `/api/v1/geocode/search?query=${encodeURIComponent(query)}&limit=10`
    );
    return data?.results || [];
  } catch (err) {
    console.error("Place search API failed:", err);
    return [];
  }
}

async function resolveTimezoneAPI(lat: number, lon: number, dateStr: string): Promise<number> {
  try {
    const data = await api.get<{ utc_offset_minutes: number }>(
      `/api/v1/geocode/timezone?latitude=${lat}&longitude=${lon}&local_date=${dateStr}`
    );
    return data.utc_offset_minutes;
  } catch (err) {
    console.error("Timezone resolution failed", err);
    if (lat >= 8 && lat <= 37 && lon >= 68 && lon <= 97) return 330;
    return -new Date().getTimezoneOffset();
  }
}

// ── Utility: format datetime ────────────────────────────────────────────────

function fmtTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
}

function fmtRange(start: string, end: string): string {
  return `${fmtTime(start)} – ${fmtTime(end)}`;
}


// ── Panchanga Next-Limb Lookup Tables ────────────────────────────────────────

const TITHI_NAMES_EN = [
  "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami",
  "Navami","Dashami","Ekadashi","Dwadashi","Trayodashi","Chaturdashi","Purnima",
  "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami",
  "Navami","Dashami","Ekadashi","Dwadashi","Trayodashi","Chaturdashi","Amavasya",
];
const NAK_NAMES_EN = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];

/** Returns "Until 7:42 AM · then Panchami" for Tithi */
function tithiDetail(num: number | undefined, end_time: string | null | undefined): string {
  if (!num || !end_time) return "";
  const next = TITHI_NAMES_EN[(num % 30)]; // index = num % 30 gives next
  return `Until ${fmtTime(end_time)} · then ${next}`;
}

/** Returns "Until 3:23 AM · then Ashwini" for Nakshatra */
function nakDetail(num: number | undefined, end_time: string | null | undefined): string {
  if (!num || !end_time) return "";
  const next = NAK_NAMES_EN[num % 27]; // index = num % 27 gives next
  return `Until ${fmtTime(end_time)} · then ${next}`;
}


export function PanchangWorkspaceView() {
  // Panchang is strictly dark mode only — no light, no system theme
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    }
  }, []);

  const isDark = true;

  const activeChart = useWorkflowStore((s) => s.result?.chart);
  const activeRequest = useWorkflowStore((s) => s.request);

  const [calculationMode, setCalculationMode] = useState<"lahiri" | "raman" | "krishnamurti">("lahiri");
  const [selectedDate, setSelectedDate] = useState<string>(() => new Date().toISOString().split("T")[0]);
  const [selectedTime, setSelectedTime] = useState<string>(() => {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  });

  const [locationName, setLocationName] = useState<string>("New Delhi, India");
  const [latitude, setLatitude] = useState<number>(28.6139);
  const [longitude, setLongitude] = useState<number>(77.2090);
  const [utcOffsetMinutes, setUtcOffsetMinutes] = useState<number>(330);

  const [showLocationModal, setShowLocationModal] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<PlaceResult[]>([]);
  const [searching, setSearching] = useState<boolean>(false);
  const [searchFeedback, setSearchFeedback] = useState<string | null>(null);
  const [gpsLoading, setGpsLoading] = useState<boolean>(false);
  const [manualCoordsOpen, setManualCoordsOpen] = useState<boolean>(false);

  const [natalNakshatra, setNatalNakshatra] = useState<number>(1);
  const [natalMoonSign, setNatalMoonSign] = useState<number>(1);

  const [activeTab, setActiveTab] = useState<"panchanga" | "windows" | "tarabala" | "activities" | "kundli">("panchanga");
  const [showHelpGuide, setShowHelpGuide] = useState<boolean>(false);

  // Check URL hash or query params for #kundli
  useEffect(() => {
    if (typeof window !== "undefined") {
      if (window.location.hash === "#kundli" || window.location.search.includes("tab=kundli")) {
        setActiveTab("kundli");
      }
      const handleHashChange = () => {
        if (window.location.hash === "#kundli") {
          setActiveTab("kundli");
        }
      };
      window.addEventListener("hashchange", handleHashChange);
      return () => window.removeEventListener("hashchange", handleHashChange);
    }
  }, []);

  const [muhurtaData, setMuhurtaData] = useState<MuhurtaResponse | null>(null);
  const [muhurtaError, setMuhurtaError] = useState<string | null>(null);
  const [muhurtaLoading, setMuhurtaLoading] = useState<boolean>(false);

  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const loadMuhurta = useCallback(async () => {
    setMuhurtaLoading(true);
    setMuhurtaError(null);
    try {
      const data = await fetchMuhurta(
        selectedDate,
        selectedTime,
        latitude,
        longitude,
        utcOffsetMinutes,
        calculationMode,
        natalNakshatra,
        natalMoonSign
      );
      setMuhurtaData(data);
    } catch (err) {
      setMuhurtaError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Failed to compute Panchanga");
    } finally {
      setMuhurtaLoading(false);
    }
  }, [selectedDate, selectedTime, latitude, longitude, utcOffsetMinutes, calculationMode, natalNakshatra, natalMoonSign]);

  useEffect(() => {
    void loadMuhurta();
  }, [loadMuhurta]);

  useEffect(() => {
    if (activeRequest && activeChart) {
      if (activeRequest.place_name) {
        setLocationName(activeRequest.place_name);
        setLatitude(activeRequest.latitude);
        setLongitude(activeRequest.longitude);
      }
      const moon = (activeChart.planets || []).find(p => (p?.planet || "").toLowerCase() === "moon");
      if (moon && moon.pada) {
        const nakIdx = NAKSHATRA_NAMES.findIndex(n => n.toLowerCase().includes((moon.nakshatra || "").toLowerCase()));
        if (nakIdx !== -1) setNatalNakshatra(nakIdx + 1);
        const rashiIdx = RASHI_NAMES.findIndex(r => r.toLowerCase().includes((moon.rashi || "").toLowerCase()));
        if (rashiIdx !== -1) setNatalMoonSign(rashiIdx + 1);
      }
    }
  }, [activeRequest, activeChart]);

  // Combined Instant + Asynchronous Search Handler
  const executeSearch = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (trimmed.length < 2) {
      setSearchResults([]);
      setSearchFeedback(null);
      setSearching(false);
      return;
    }

    // Step 1: Immediate local match (0ms latency)
    const localMatches = searchClientCities(trimmed, 8);
    setSearchResults(localMatches);
    setSearchFeedback(null);

    // Step 2: Query backend geocoding service in background
    setSearching(true);
    try {
      const remoteResults = await searchPlacesAPI(trimmed);
      if (remoteResults && remoteResults.length > 0) {
        const seen = new Set<string>();
        const merged: PlaceResult[] = [];
        for (const item of [...remoteResults, ...localMatches]) {
          const key = `${item.display_name.toLowerCase()}_${item.latitude.toFixed(2)}_${item.longitude.toFixed(2)}`;
          if (!seen.has(key)) {
            seen.add(key);
            merged.push(item);
          }
        }
        setSearchResults(merged.slice(0, 10));
      } else if (localMatches.length === 0) {
        setSearchFeedback(`No locations found for "${trimmed}". Try another city name or use current location.`);
      }
    } catch (err) {
      if (localMatches.length === 0) {
        setSearchFeedback(`Could not fetch online locations. You can use GPS or manual coords.`);
      }
    } finally {
      setSearching(false);
    }
  }, []);

  const handleSearchChange = (q: string) => {
    setSearchQuery(q);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    
    if (q.trim().length >= 2) {
      const instant = searchClientCities(q.trim(), 6);
      if (instant.length > 0) {
        setSearchResults(instant);
      }
    } else {
      setSearchResults([]);
      setSearchFeedback(null);
    }

    searchTimeoutRef.current = setTimeout(() => {
      void executeSearch(q);
    }, 200);
  };

  // Instant apply city selection & close modal immediately without blocking
  const handleSelectCity = (name: string, lat: number, lon: number, offset?: number) => {
    const cleanLat = parseFloat(Number(lat).toFixed(4));
    const cleanLon = parseFloat(Number(lon).toFixed(4));
    
    setLocationName(name);
    setLatitude(cleanLat);
    setLongitude(cleanLon);

    let initialOffset = offset;
    if (initialOffset === undefined) {
      if (cleanLat >= 8 && cleanLat <= 37 && cleanLon >= 68 && cleanLon <= 97) {
        initialOffset = 330;
      } else {
        initialOffset = -new Date().getTimezoneOffset();
      }
    }
    setUtcOffsetMinutes(initialOffset);

    // Immediately close modal and reset search state
    setShowLocationModal(false);
    setSearchQuery("");
    setSearchResults([]);
    setSearchFeedback(null);

    // Asynchronously refine timezone in background
    if (offset === undefined) {
      void resolveTimezoneAPI(cleanLat, cleanLon, selectedDate).then((resolved) => {
        setUtcOffsetMinutes(resolved);
      });
    }
  };

  // Robust GPS + IP Fallback Location Detection
  const handleUseCurrentLocation = async () => {
    setGpsLoading(true);
    setSearchFeedback(null);

    // Strategy 1: Browser Geolocation
    if (typeof window !== "undefined" && navigator.geolocation) {
      try {
        const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: false,
            timeout: 3500,
            maximumAge: 300000,
          });
        });

        const lat = parseFloat(pos.coords.latitude.toFixed(4));
        const lon = parseFloat(pos.coords.longitude.toFixed(4));
        handleSelectCity(`Current Location (${lat}°, ${lon}°)`, lat, lon);
        setGpsLoading(false);
        return;
      } catch (geoErr) {
        console.warn("Browser GPS failed or blocked, trying IP fallback...", geoErr);
      }
    }

    // Strategy 2: Fast IP Geolocation Fallback
    try {
      const ipLoc = await api.get<PlaceResult>("/api/v1/geocode/ip");
      if (ipLoc && ipLoc.latitude && ipLoc.longitude) {
        handleSelectCity(ipLoc.display_name, ipLoc.latitude, ipLoc.longitude);
        setGpsLoading(false);
        return;
      }
    } catch (ipErr) {
      console.warn("IP Geolocation fallback failed:", ipErr);
    }

    setGpsLoading(false);
    setSearchFeedback("Could not detect location automatically. Please search city name above.");
  };

  const setToCurrentTime = () => {
    const now = new Date();
    setSelectedDate(now.toISOString().split("T")[0]);
    setSelectedTime(`${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`);
  };

  const dayChoghadiya = muhurtaData?.choghadiya.filter((c) => c.is_day) ?? [];
  const nightChoghadiya = muhurtaData?.choghadiya.filter((c) => !c.is_day) ?? [];

  return (
    <div className="min-h-screen p-4 sm:p-6 lg:p-8 space-y-6 transition-colors bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* 🌟 Top Header Banner */}
      <div className="border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm transition-all relative overflow-hidden bg-white dark:bg-slate-900/90">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-mono text-xs font-bold tracking-wider uppercase">
              <Clock className="w-4 h-4 text-cyan-500" />
              <span>CLASSICAL MUHURTA &amp; PANCHANGA EVALUATOR</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold font-sans tracking-tight">
              Auspicious Timing &amp; Shastric Panchanga Suite
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl font-sans">
              Precision Swiss Ephemeris electional engine implementing real-time <strong>5 Panchanga Limbs</strong>, <strong>Tarabala</strong>, <strong>Chandrabala</strong>, <strong>Panchaka Dosha</strong>, <strong>Choghadiya</strong>, and <strong>Activity Suitability Playbook</strong>.
            </p>
          </div>

          <div className="flex flex-col items-start md:items-end gap-2.5">
            <button
              type="button"
              onClick={() => setShowHelpGuide(true)}
              className="px-3.5 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-cyan-600/30 transition-all cursor-pointer"
            >
              <span>📖</span>
              <span>View Shastric Help Guide</span>
            </button>

            <div className="flex flex-col items-start md:items-end gap-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
                AYANAMSA SYSTEM
              </span>
              <div className="flex items-center p-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 font-mono text-xs">
                <button
                  type="button"
                  onClick={() => setCalculationMode("lahiri")}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                    calculationMode === "lahiri"
                      ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  🪐 Lahiri (Chitra Paksha)
                </button>
                <button
                  type="button"
                  onClick={() => setCalculationMode("krishnamurti")}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                    calculationMode === "krishnamurti"
                      ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  📐 KP (Krishnamurti)
                </button>
                <button
                  type="button"
                  onClick={() => setCalculationMode("raman")}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                    calculationMode === "raman"
                      ? "bg-amber-600 text-white shadow-md shadow-amber-600/30"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  📜 Raman
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 🌟 Interactive Parameter Controls Bar */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-4 font-mono text-xs bg-white dark:bg-slate-900/90">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-slate-500 dark:text-slate-400 font-bold">📅 DATE:</span>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-2.5 py-1 rounded-lg border font-bold focus:outline-none bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-cyan-300"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500 dark:text-slate-400 font-bold">⏰ TIME:</span>
            <input
              type="time"
              value={selectedTime}
              onChange={(e) => setSelectedTime(e.target.value)}
              className="px-2.5 py-1 rounded-lg border font-bold focus:outline-none bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-cyan-300"
            />
            <button
              onClick={setToCurrentTime}
              className="px-3 py-1 rounded-lg text-xs font-bold transition-colors cursor-pointer bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              NOW
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500 dark:text-slate-400 font-bold">📍 LOCATION:</span>
            <button
              type="button"
              onClick={() => setShowLocationModal(true)}
              className="px-3 py-1.5 rounded-lg border border-cyan-600/40 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 font-bold flex items-center gap-2 transition cursor-pointer"
            >
              <span>{locationName}</span>
              <span className="text-[10px] text-slate-400">({latitude.toFixed(2)}°, {longitude.toFixed(2)}°)</span>
              <span className="text-xs">✏️</span>
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {muhurtaLoading ? (
            <span className="text-cyan-500 dark:text-cyan-400 animate-pulse font-bold flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              Computing Ephemeris...
            </span>
          ) : muhurtaError ? (
            <span className="text-rose-600 dark:text-rose-400 font-bold">⚠️ {muhurtaError}</span>
          ) : (
            <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500" />
              Real-time Ephemeris Active
            </span>
          )}
        </div>
      </div>

      {/* 🌟 Tab Navigation */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 border-b pb-4 border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("panchanga")}
          className={`px-3 py-2.5 rounded-xl text-xs font-bold font-mono transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === "panchanga"
              ? "bg-cyan-600 text-white shadow-lg shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>01 PANCHANGA</span>
        </button>

        <button
          onClick={() => setActiveTab("windows")}
          className={`px-3 py-2.5 rounded-xl text-xs font-bold font-mono transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === "windows"
              ? "bg-cyan-600 text-white shadow-lg shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>02 WINDOWS</span>
        </button>

        <button
          onClick={() => setActiveTab("tarabala")}
          className={`px-3 py-2.5 rounded-xl text-xs font-bold font-mono transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === "tarabala"
              ? "bg-cyan-600 text-white shadow-lg shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          <Compass className="w-4 h-4" />
          <span>03 TARABALA</span>
        </button>

        <button
          onClick={() => setActiveTab("activities")}
          className={`px-3 py-2.5 rounded-xl text-xs font-bold font-mono transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
            activeTab === "activities"
              ? "bg-cyan-600 text-white shadow-lg shadow-cyan-600/30"
              : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>04 ACTIVITIES</span>
        </button>

        <button
          id="kundli"
          onClick={() => setActiveTab("kundli")}
          className={`col-span-2 sm:col-span-1 px-3 py-2.5 rounded-xl text-xs font-bold font-mono transition-all flex items-center justify-center gap-1.5 cursor-pointer border ${
            activeTab === "kundli"
              ? "bg-gradient-to-r from-cyan-600 to-sky-600 text-white shadow-lg shadow-cyan-600/30 border-cyan-400/40"
              : "bg-white dark:bg-slate-900 border-cyan-500/30 text-cyan-600 dark:text-cyan-300 hover:text-slate-900 dark:hover:text-white"
          }`}
        >
          <span>🪐</span>
          <span>05 KUNDLI &amp; FESTIVALS</span>
        </button>
      </div>

      {/* 🌟 Tab 1: Panchanga 5 Limbs */}
      {activeTab === "panchanga" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

            {/* ── 1. TITHI ── */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm bg-white dark:bg-slate-900/90">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                  1. TITHI (LUNAR DAY)
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 font-bold">
                  {(muhurtaData?.tithi?.paksha ?? "").toUpperCase()} PAKSHA
                </span>
              </div>
              <div className="text-lg font-extrabold text-slate-900 dark:text-white font-sans leading-tight">
                {muhurtaData?.tithi?.name || "Computing..."}{" "}
                <span className="text-xs font-normal text-slate-400">#{muhurtaData?.tithi?.number || "—"}</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-500 h-full rounded-full transition-all"
                  style={{ width: `${muhurtaData?.tithi?.completion_percent || 0}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 font-mono">
                <span>Ruler: {muhurtaData?.tithi?.lord || "Surya"}</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">{muhurtaData?.tithi?.group}</span>
              </div>
              {/* Detail: upto time + next tithi */}
              {tithiDetail(muhurtaData?.tithi?.number, muhurtaData?.tithi?.end_time) && (
                <p className="text-[11px] text-cyan-700 dark:text-cyan-300 font-mono leading-snug">
                  ⏱ {tithiDetail(muhurtaData?.tithi?.number, muhurtaData?.tithi?.end_time)}
                </p>
              )}
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                {muhurtaData?.tithi?.completion_percent}% elapsed
              </p>
            </div>

            {/* ── 2. VARA ── */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm bg-white dark:bg-slate-900/90">
              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                2. VARA (SOLAR WEEKDAY)
              </span>
              <div className="text-lg font-extrabold text-slate-900 dark:text-white font-sans">
                {muhurtaData?.vara?.name || "Computing..."}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Ruling Graha: <strong className="text-slate-700 dark:text-slate-300">{muhurtaData?.vara?.lord}</strong>
              </div>
              <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-bold font-mono">
                {muhurtaData?.vara?.nature || "Vedic Sunrise Day"}
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                Sunrise: <strong className="text-amber-600 dark:text-amber-400">{fmtTime(muhurtaData?.sunrise)}</strong>
                {" · "}
                Sunset: <strong className="text-amber-600 dark:text-amber-400">{fmtTime(muhurtaData?.sunset)}</strong>
              </p>
            </div>

            {/* ── 3. NAKSHATRA ── */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm bg-white dark:bg-slate-900/90">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                  3. NAKSHATRA (LUNAR MANSION)
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold">
                  Pada {muhurtaData?.nakshatra?.pada || 1}
                </span>
              </div>
              <div className="text-lg font-extrabold text-slate-900 dark:text-white font-sans leading-tight">
                {muhurtaData?.nakshatra?.name || "Computing..."}{" "}
                <span className="text-xs font-normal text-slate-400">#{muhurtaData?.nakshatra?.number || "—"}</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all"
                  style={{ width: `${muhurtaData?.nakshatra?.completion_percent || 0}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 font-mono">
                <span>Lord: {muhurtaData?.nakshatra?.lord}</span>
                <span className="text-cyan-600 dark:text-cyan-400">{muhurtaData?.nakshatra?.degree_in_nakshatra?.toFixed(2)}° in star</span>
              </div>
              {/* Detail: upto time + next nakshatra */}
              {nakDetail(muhurtaData?.nakshatra?.number, muhurtaData?.nakshatra?.end_time) && (
                <p className="text-[11px] text-cyan-700 dark:text-cyan-300 font-mono leading-snug">
                  ⏱ {nakDetail(muhurtaData?.nakshatra?.number, muhurtaData?.nakshatra?.end_time)}
                </p>
              )}
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                {muhurtaData?.nakshatra?.quality}
              </p>
            </div>

            {/* ── 4. YOGA ── */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm bg-white dark:bg-slate-900/90">
              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                4. YOGA (LUNI-SOLAR ANGLE)
              </span>
              <div className="text-lg font-extrabold text-slate-900 dark:text-white font-sans">
                {muhurtaData?.yoga?.name || "Computing..."}{" "}
                <span className="text-xs font-normal text-slate-400">#{muhurtaData?.yoga?.number || "—"}</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all"
                  style={{ width: `${muhurtaData?.yoga?.completion_percent || 0}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Meaning: <strong className="text-slate-700 dark:text-slate-200">{muhurtaData?.yoga?.meaning}</strong>
              </p>
              <p className="text-[11px] text-cyan-700 dark:text-cyan-300 font-mono">
                ⏱ Until {fmtTime(muhurtaData?.yoga?.end_time)}
              </p>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                {muhurtaData?.yoga?.completion_percent}% elapsed
              </p>
            </div>

            {/* ── 5. KARANA ── */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm bg-white dark:bg-slate-900/90">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                  5. KARANA (HALF-TITHI)
                </span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  muhurtaData?.karana?.name === "Vishti" ? "bg-rose-500/20 text-rose-500 dark:text-rose-400" : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                }`}>
                  {muhurtaData?.karana?.is_fixed ? "Fixed" : "Movable"}
                </span>
              </div>
              <div className="text-lg font-extrabold text-slate-900 dark:text-white font-sans">
                {muhurtaData?.karana?.name || "Computing..."}{" "}
                <span className="text-xs font-normal text-slate-400">#{muhurtaData?.karana?.number || "—"}</span>
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                Nature: <strong className={muhurtaData?.karana?.name === "Vishti" ? "text-rose-600 dark:text-rose-400" : "text-emerald-600 dark:text-emerald-400"}>{muhurtaData?.karana?.nature}</strong>
              </div>
              <p className="text-[11px] text-cyan-700 dark:text-cyan-300 font-mono">
                ⏱ Until {fmtTime(muhurtaData?.karana?.end_time)}
              </p>
            </div>

            {/* ── SAMVATSARA & MASA ── */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm bg-white dark:bg-slate-900/90">
              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                SAMVATSARA &amp; MASA (YEAR &amp; MONTH)
              </span>
              <div className="text-base font-extrabold text-amber-600 dark:text-amber-400 font-sans">
                {muhurtaData?.calendar?.vikram_samvatsara || "—"} ({muhurtaData?.calendar?.vikram_year} VS)
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono space-y-0.5">
                <div>Shaka Year: <strong className="text-slate-700 dark:text-slate-200">{muhurtaData?.calendar?.shaka_year} ({muhurtaData?.calendar?.shaka_samvatsara})</strong></div>
                <div>Amanta Masa: <strong className="text-cyan-700 dark:text-cyan-300">{muhurtaData?.calendar?.amanta_masa}</strong></div>
                <div>Purnimanta Masa: <strong className="text-cyan-700 dark:text-cyan-300">{muhurtaData?.calendar?.purnimanta_masa}</strong></div>
              </div>
            </div>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm bg-white dark:bg-slate-900/90">
            <div className="border-b pb-3 mb-4 flex justify-between items-center border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono flex items-center gap-2">
                <Sun className="w-4 h-4 text-amber-400" />
                <span>SOLAR, LUNAR &amp; ASCENDANT EPHEMERIS COORDINATES</span>
              </span>
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                Ayanamsa: {calculationMode.toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="text-amber-600 dark:text-amber-500 font-bold flex items-center gap-1">☀️ Sun Position</span>
                <div className="text-sm font-bold text-slate-900 dark:text-white">
                  {muhurtaData?.celestial?.sun_sign} {muhurtaData?.celestial?.sun_sign_degree.toFixed(2)}°
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">Total: {muhurtaData?.celestial?.sun_longitude.toFixed(2)}°</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="text-cyan-600 dark:text-cyan-400 font-bold flex items-center gap-1">🌙 Moon Position</span>
                <div className="text-sm font-bold text-slate-900 dark:text-white">
                  {muhurtaData?.celestial?.moon_sign} {muhurtaData?.celestial?.moon_sign_degree.toFixed(2)}°
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">Total: {muhurtaData?.celestial?.moon_longitude.toFixed(2)}°</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">🌅 Ascendant (Lagna)</span>
                <div className="text-sm font-bold text-slate-900 dark:text-white">
                  {muhurtaData?.celestial?.ascendant_sign} {muhurtaData?.celestial?.ascendant_degree.toFixed(2)}°
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">Momentary Ascendant</div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/60 space-y-1">
                <span className="text-purple-600 dark:text-purple-400 font-bold flex items-center gap-1">🌌 Lunar Rise &amp; Set</span>
                <div className="text-[11px] text-slate-600 dark:text-slate-300">Rise: <strong className="text-slate-900 dark:text-white">{fmtTime(muhurtaData?.celestial?.moonrise)}</strong></div>
                <div className="text-[11px] text-slate-600 dark:text-slate-300">Set: <strong className="text-slate-900 dark:text-white">{fmtTime(muhurtaData?.celestial?.moonset)}</strong></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 2: Windows & Choghadiya */}
      {activeTab === "windows" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div className={`p-4 rounded-xl border space-y-2 ${
              muhurtaData?.abhijit_muhurta?.is_auspicious
                ? "bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/40 text-emerald-900 dark:text-emerald-300"
                : "bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-800/40 text-rose-900 dark:text-rose-300"
            }`}>
              <div className="font-bold text-sm flex items-center justify-between">
                <span>🌟 Abhijit Muhurta</span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                  muhurtaData?.abhijit_muhurta?.is_auspicious ? "bg-emerald-500/20 text-emerald-700 dark:text-emerald-400" : "bg-rose-500/20 text-rose-700 dark:text-rose-400"
                }`}>
                  {muhurtaData?.abhijit_muhurta?.is_auspicious ? "Auspicious" : "Afflicted"}
                </span>
              </div>
              <div className="text-lg font-extrabold">
                {muhurtaData?.abhijit_muhurta ? fmtRange(muhurtaData.abhijit_muhurta.start, muhurtaData.abhijit_muhurta.end) : "—"}
              </div>
              <p className="text-xs font-sans">
                {muhurtaData?.abhijit_muhurta?.description || "Supreme midday window wiping out minor doshas."}
              </p>
            </div>

            <div className="p-4 rounded-xl border space-y-2 bg-cyan-50 dark:bg-cyan-950/20 border-cyan-200 dark:border-cyan-800/40 text-cyan-900 dark:text-cyan-300">
              <div className="font-bold text-sm flex items-center justify-between">
                <span>🧘 Brahma Muhurta</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-700 dark:text-cyan-400 font-bold">Spiritual</span>
              </div>
              <div className="text-lg font-extrabold">
                {muhurtaData?.brahma_muhurta ? fmtRange(muhurtaData.brahma_muhurta.start, muhurtaData.brahma_muhurta.end) : "—"}
              </div>
              <p className="text-xs font-sans">
                {muhurtaData?.brahma_muhurta?.description || "Optimal window before sunrise for intellect and meditation."}
              </p>
            </div>

            <div className="p-4 rounded-xl border space-y-2 bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-800/40 text-rose-900 dark:text-rose-300">
              <div className="font-bold text-sm flex items-center justify-between">
                <span>⚠️ Rahu Kalam</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-700 dark:text-rose-400 font-bold">Strict Avoid</span>
              </div>
              <div className="text-lg font-extrabold">
                {muhurtaData?.rahukalam ? fmtRange(muhurtaData.rahukalam.start, muhurtaData.rahukalam.end) : "—"}
              </div>
              <p className="text-xs font-sans">
                Do not initiate new travels, signing contracts, or monetary disbursements during Rahu Kalam.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
            <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90">
              <div className="font-bold text-amber-500 dark:text-amber-400 mb-1">⏳ Gulika Kalam</div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{muhurtaData?.gulikalam ? fmtRange(muhurtaData.gulikalam.start, muhurtaData.gulikalam.end) : "—"}</div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-sans mt-1">Actions started here tend to repeat repeatedly.</p>
            </div>

            <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90">
              <div className="font-bold text-rose-500 dark:text-rose-400 mb-1">⚠️ Yamagandam</div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{muhurtaData?.yamagandam ? fmtRange(muhurtaData.yamagandam.start, muhurtaData.yamagandam.end) : "—"}</div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-sans mt-1">Inauspicious window governed by Yama; avoid travel.</p>
            </div>

            <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90">
              <div className="font-bold text-emerald-600 dark:text-emerald-400 mb-1">🍯 Amrit Kaal</div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200">{muhurtaData?.amrit_kaal ? fmtRange(muhurtaData.amrit_kaal.start, muhurtaData.amrit_kaal.end) : "—"}</div>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-sans mt-1">Nectar-like window for healing and life celebrations.</p>
            </div>

            <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90">
              <div className="font-bold text-rose-500 dark:text-rose-400 mb-1">🛑 Dur Muhurta(s)</div>
              <div className="text-[11px] font-bold text-slate-800 dark:text-slate-200">
                {muhurtaData?.dur_muhurta?.map((d, i) => (
                  <div key={i}>{fmtRange(d.start, d.end)}</div>
                )) || "None"}
              </div>
            </div>
          </div>

          <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors bg-white dark:bg-slate-900/90">
            <div className="border-b pb-3 mb-4 flex justify-between items-center border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                DAY CHOGHADIYA CYCLES (SUNRISE TO SUNSET)
              </span>
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">8 Exact Divisions for {locationName.split(",")[0]}</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
              {dayChoghadiya.map((c, idx) => (
                <div key={idx} className={`p-3 rounded-lg border flex flex-col justify-between space-y-1 ${
                  c.nature === "auspicious"
                    ? "bg-emerald-50 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-800/40 text-emerald-800 dark:text-emerald-300"
                    : "bg-rose-50 dark:bg-rose-950/10 border-rose-200 dark:border-rose-800/40 text-rose-800 dark:text-rose-300"
                }`}>
                  <div className="flex justify-between items-center">
                    <span className="font-extrabold text-sm">{c.name}</span>
                    <span className={`text-[10px] font-bold uppercase ${c.nature === "auspicious" ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                      {c.nature}
                    </span>
                  </div>
                  <div className="text-[11px] font-bold">{fmtRange(c.start, c.end)}</div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400">Ruler: {c.lord || "—"}</div>
                </div>
              ))}
            </div>

            <div className="border-b pb-3 my-4 mt-6 flex justify-between items-center border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400 font-mono">
                NIGHT CHOGHADIYA CYCLES (SUNSET TO NEXT SUNRISE)
              </span>
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">8 Exact Divisions</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
              {nightChoghadiya.map((c, idx) => (
                <div key={idx} className={`p-3 rounded-lg border flex flex-col justify-between space-y-1 ${
                  c.nature === "auspicious"
                    ? "bg-emerald-50 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-800/40 text-emerald-800 dark:text-emerald-300"
                    : "bg-rose-50 dark:bg-rose-950/10 border-rose-200 dark:border-rose-800/40 text-rose-800 dark:text-rose-300"
                }`}>
                  <div className="flex justify-between items-center">
                    <span className="font-extrabold text-sm">{c.name}</span>
                    <span className={`text-[10px] font-bold uppercase ${c.nature === "auspicious" ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                      {c.nature}
                    </span>
                  </div>
                  <div className="text-[11px] font-bold">{fmtRange(c.start, c.end)}</div>
                  <div className="text-[10px] text-slate-500 dark:text-slate-400">Ruler: {c.lord || "—"}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 24 Planetary Horas Table */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition-colors bg-white dark:bg-slate-900/90">
            <div className="border-b pb-3 mb-4 flex justify-between items-center border-slate-200 dark:border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400 font-mono">
                24 PLANETARY HORAS TIMELINE (CHALDEAN SEQUENCE)
              </span>
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">Day 12 + Night 12</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5 font-mono text-xs max-h-80 overflow-y-auto pr-1">
              {muhurtaData?.horas.map((h, i) => (
                <div key={i} className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-700/60 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50">
                  <div>
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold mr-1.5">#{h.index} {h.is_day ? "☀️" : "🌙"}</span>
                    <span className="font-bold text-cyan-700 dark:text-cyan-300 capitalize">{h.lord}</span>
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">{fmtRange(h.start, h.end)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 3: Tarabala, Chandrabala & Panchaka */}
      {activeTab === "tarabala" && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-wrap items-center justify-between gap-4 font-mono text-xs bg-white dark:bg-slate-900/90">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-cyan-600 dark:text-cyan-400 font-bold">✨ JANMA NAKSHATRA:</span>
                <select
                  value={natalNakshatra}
                  onChange={(e) => setNatalNakshatra(parseInt(e.target.value))}
                  className="px-2.5 py-1 rounded-lg border font-bold focus:outline-none bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-cyan-300"
                >
                  {NAKSHATRA_NAMES.map((name, i) => (
                    <option key={i} value={i + 1}>{name}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-cyan-600 dark:text-cyan-400 font-bold">🌙 JANMA RASHI (MOON SIGN):</span>
                <select
                  value={natalMoonSign}
                  onChange={(e) => setNatalMoonSign(parseInt(e.target.value))}
                  className="px-2.5 py-1 rounded-lg border font-bold focus:outline-none bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-800 dark:text-cyan-300"
                >
                  {RASHI_NAMES.map((name, i) => (
                    <option key={i} value={i + 1}>{name}</option>
                  ))}
                </select>
              </div>
            </div>

            {activeChart && (
              <button
                type="button"
                onClick={() => {
                  const moon = (activeChart.planets || []).find(p => (p?.planet || "").toLowerCase() === "moon");
                  if (moon) {
                    const nakIdx = NAKSHATRA_NAMES.findIndex(n => n.toLowerCase().includes((moon.nakshatra || "").toLowerCase()));
                    if (nakIdx !== -1) setNatalNakshatra(nakIdx + 1);
                    const rashiIdx = RASHI_NAMES.findIndex(r => r.toLowerCase().includes((moon.rashi || "").toLowerCase()));
                    if (rashiIdx !== -1) setNatalMoonSign(rashiIdx + 1);
                  }
                }}
                className="px-3 py-1 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-700 dark:text-cyan-300 font-bold border border-cyan-500/30 transition cursor-pointer"
              >
                🔄 Sync from Active Chart ({activeChart.ascendant.rashi})
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 bg-white dark:bg-slate-900/90">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
                  TARABALA (9 STELLAR FORCES)
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  muhurtaData?.tarabala?.is_auspicious ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400" : "bg-rose-500/20 text-rose-600 dark:text-rose-400"
                }`}>
                  {muhurtaData?.tarabala?.is_auspicious ? "FAVORABLE" : "INAUSPICIOUS"}
                </span>
              </div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                {muhurtaData?.tarabala?.tara_name || "Computing..."}
              </div>
              <div className="text-sm font-bold text-cyan-600 dark:text-cyan-400">
                Score: {muhurtaData?.tarabala?.score || 0}%
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                {muhurtaData?.tarabala?.description || "Measures the cyclic relationship from your Janma Nakshatra."}
              </p>
            </div>

            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 bg-white dark:bg-slate-900/90">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
                  CHANDRABALA (LUNAR STRENGTH)
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  muhurtaData?.chandrabala?.is_auspicious ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400" : "bg-rose-500/20 text-rose-600 dark:text-rose-400"
                }`}>
                  {muhurtaData?.chandrabala?.is_auspicious ? "SUPPORTIVE" : "AFFLICTED"}
                </span>
              </div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                House {muhurtaData?.chandrabala?.house_from_natal_moon || 1} from Natal Moon
              </div>
              <div className="text-sm font-bold text-cyan-600 dark:text-cyan-400">
                Status: {muhurtaData?.chandrabala?.status || "—"}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                {muhurtaData?.chandrabala?.description || "Transit Moon relative to natal Moon sign."}
              </p>
            </div>

            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 bg-white dark:bg-slate-900/90">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
                  PANCHAKA DOSHA EVALUATOR
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  !muhurtaData?.panchaka?.has_dosha ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400" : "bg-rose-500/20 text-rose-600 dark:text-rose-400"
                }`}>
                  {!muhurtaData?.panchaka?.has_dosha ? "DOSHA FREE" : "DOSHA AFFLICTED"}
                </span>
              </div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">
                {muhurtaData?.panchaka?.panchaka_name || "Computing..."}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                (Tithi + Vara + Nakshatra + Lagna) mod 9 = <strong className="text-cyan-700 dark:text-cyan-300">{muhurtaData?.panchaka?.remainder}</strong>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 font-sans leading-relaxed">
                {muhurtaData?.panchaka?.description || "Panchaka calculation ensures freedom from Mrityu, Agni, Raja, Chora, and Roga doshas."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 🌟 Tab 4: Activities Playbook */}
      {activeTab === "activities" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {muhurtaData?.activities && muhurtaData.activities.length > 0 ? (
            muhurtaData.activities.map((act) => (
              <div key={act.activity_id} className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3 transition-colors bg-white dark:bg-slate-900/90">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-sm text-slate-900 dark:text-white font-sans">{act.name}</span>
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-bold font-mono border ${
                    act.score >= 75
                      ? "bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800"
                      : act.score >= 50
                      ? "bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800"
                      : "bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-800"
                  }`}>
                    {act.score}% Score
                  </span>
                </div>
                <div className="text-xs font-bold text-emerald-700 dark:text-emerald-400 font-mono">
                  {act.verdict}
                </div>
                <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300 font-sans list-disc list-inside">
                  {act.points.map((pt, i) => (
                    <li key={i}>{pt}</li>
                  ))}
                </ul>
              </div>
            ))
          ) : (
            <div className="col-span-4 p-8 text-center text-slate-500 dark:text-slate-400 font-mono text-xs">
              Calculating activity suitability scores from live ephemeris...
            </div>
          )}
        </div>
      )}

      {/* 🌟 Tab 5: Gochar Kundli & Upavas/Festivals (Full-screen capable, JeevanCode-style) */}
      {activeTab === "kundli" && (
        <PanchangKundliTab
          selectedDate={selectedDate}
          selectedTime={selectedTime}
          latitude={latitude}
          longitude={longitude}
          locationName={locationName}
          utcOffsetMinutes={utcOffsetMinutes}
          calculationMode={calculationMode}
          muhurtaData={muhurtaData}
        />
      )}

      {/* 🌟 Streamlined Location Modal (Zero Scroll Required) */}
      {showLocationModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-lg rounded-2xl border border-cyan-500/40 shadow-2xl p-5 sm:p-6 space-y-4 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <span className="text-xl">📍</span>
                <div>
                  <h3 className="text-base font-bold font-sans text-cyan-600 dark:text-cyan-400">
                    Select Location
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    Search city name or auto-detect with GPS / IP.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowLocationModal(false)}
                className="w-7 h-7 rounded-full border border-slate-300 dark:border-slate-700 flex items-center justify-center text-xs font-bold hover:bg-rose-500 hover:text-white hover:border-rose-500 transition-colors cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Quick Action One-Click Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => void handleUseCurrentLocation()}
                disabled={gpsLoading}
                className="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 transition cursor-pointer shadow-md"
              >
                <span>{gpsLoading ? "⏳ Detecting Location..." : "📡 Use Current Location"}</span>
              </button>

              {activeRequest ? (
                <button
                  type="button"
                  onClick={() => handleSelectCity(activeRequest.place_name || "Active Chart Location", activeRequest.latitude, activeRequest.longitude)}
                  className="px-3 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs flex items-center justify-center gap-2 transition cursor-pointer shadow-md"
                >
                  <span>🔄 Sync Active Chart</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setManualCoordsOpen(!manualCoordsOpen)}
                  className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-mono font-bold text-xs flex items-center justify-center gap-2 transition cursor-pointer border border-slate-300 dark:border-slate-700"
                >
                  <span>⚙️ {manualCoordsOpen ? "Hide Manual" : "Enter Coordinates"}</span>
                </button>
              )}
            </div>

            {/* Live Search Input Box */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-xs font-bold uppercase text-cyan-600 dark:text-cyan-400 font-mono">
                <span>🔍 Search City</span>
                {searching && <span className="text-cyan-600 dark:text-cyan-300 font-normal animate-pulse text-[10px]">Searching...</span>}
              </div>

              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  void executeSearch(searchQuery);
                }}
                className="flex items-center gap-2"
              >
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Type city (e.g. Pune, Varanasi, London, Dallas)..."
                    value={searchQuery}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    autoFocus
                    className="w-full px-3.5 py-2 rounded-xl border text-xs font-bold focus:outline-none focus:ring-2 focus:ring-cyan-500 transition bg-slate-50 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500"
                  />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={() => {
                        setSearchQuery("");
                        setSearchResults([]);
                        setSearchFeedback(null);
                      }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 text-xs font-bold cursor-pointer"
                    >
                      ✕
                    </button>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={searching || searchQuery.trim().length < 2}
                  className="px-3 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-mono font-bold text-xs flex items-center gap-1 transition cursor-pointer shrink-0 shadow-md"
                >
                  <span>🔍</span>
                  <span>Search</span>
                </button>
              </form>

              {searchFeedback && (
                <p className="text-[10px] text-amber-600 dark:text-amber-400 font-mono">{searchFeedback}</p>
              )}

              {/* Instant Search Results Dropdown - One Click to Apply and Auto-Close */}
              {searchResults.length > 0 && (
                <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-1.5 space-y-0.5 max-h-48 overflow-y-auto mt-1 bg-slate-50 dark:bg-slate-800">
                  <div className="px-2 py-0.5 text-[9px] uppercase font-mono font-bold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700 flex justify-between">
                    <span>Results ({searchResults.length})</span>
                    <span className="text-cyan-600 dark:text-cyan-400">Click to Select</span>
                  </div>
                  {searchResults.map((res, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSelectCity(res.display_name, res.latitude, res.longitude)}
                      className="w-full text-left p-2 rounded-lg hover:bg-cyan-500/20 text-xs font-mono flex items-center justify-between transition cursor-pointer group"
                    >
                      <span className="truncate max-w-[280px] font-bold text-slate-800 dark:text-slate-200 group-hover:text-cyan-600 dark:group-hover:text-cyan-300">
                        {res.display_name}
                      </span>
                      <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-semibold shrink-0 ml-2">
                        {res.latitude.toFixed(2)}°, {res.longitude.toFixed(2)}°
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Manual Lat/Lon Override */}
            {manualCoordsOpen && (
              <div className="grid grid-cols-3 gap-2 font-mono text-xs p-3 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <div>
                  <label className="text-[9px] text-slate-500 dark:text-slate-400 block mb-0.5">Lat (°N)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={latitude}
                    onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                    className="w-full px-2 py-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-cyan-700 dark:text-cyan-300 font-bold text-xs"
                  />
                </div>
                <div>
                  <label className="text-[9px] text-slate-500 dark:text-slate-400 block mb-0.5">Lon (°E)</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={longitude}
                    onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                    className="w-full px-2 py-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-cyan-700 dark:text-cyan-300 font-bold text-xs"
                  />
                </div>
                <div>
                  <label className="text-[9px] text-slate-500 dark:text-slate-400 block mb-0.5">UTC (Min)</label>
                  <input
                    type="number"
                    value={utcOffsetMinutes}
                    onChange={(e) => setUtcOffsetMinutes(parseInt(e.target.value) || 0)}
                    className="w-full px-2 py-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-cyan-700 dark:text-cyan-300 font-bold text-xs"
                  />
                </div>
                <div className="col-span-3 pt-1 flex justify-end">
                  <button
                    type="button"
                    onClick={() => handleSelectCity(locationName, latitude, longitude, utcOffsetMinutes)}
                    className="px-3 py-1 bg-cyan-600 text-white rounded font-bold text-[10px]"
                  >
                    Apply Coordinates
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 🌟 Shastric Help Guide Modal */}
      {showHelpGuide && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="relative w-full max-w-3xl max-h-[85vh] overflow-y-auto rounded-2xl border border-cyan-500/40 shadow-2xl p-6 sm:p-8 space-y-6 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100">
            <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2.5">
                <span className="text-2xl">📖</span>
                <div>
                  <h3 className="text-lg font-bold font-sans text-cyan-600 dark:text-cyan-400">
                    Shastric Muhurta &amp; Panchanga Complete Guide
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                    Classical Electional Astrology Standard (Muhurta Chintamani &amp; Surya Siddhanta)
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowHelpGuide(false)}
                className="w-8 h-8 rounded-full border border-slate-300 dark:border-slate-700 flex items-center justify-center text-sm font-bold hover:bg-rose-500 hover:text-white hover:border-rose-500 transition-colors cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-5 text-xs leading-relaxed font-sans">
              <div className="space-y-1.5">
                <h4 className="font-bold text-sm text-cyan-600 dark:text-cyan-300 font-mono">
                  1. Panchanga (The 5 Cosmic Limbs of Time)
                </h4>
                <p>
                  Panchanga represents the cosmic energy of any moment. Checking all 5 limbs ensures that physical, mental, and environmental factors support your action:
                </p>
                <ul className="list-disc list-inside space-y-1 pl-1 text-slate-600 dark:text-slate-300">
                  <li><strong>Tithi (Water Element):</strong> Governs emotional harmony, wealth (*Lakshmi*), and mental composure.</li>
                  <li><strong>Vara (Fire Element):</strong> Governs physical vitality, longevity, and stamina.</li>
                  <li><strong>Nakshatra (Air Element):</strong> Governs subconscious karma, focus, and outcome fruition.</li>
                  <li><strong>Yoga (Ether Element):</strong> Governs spiritual protection, purity of action, and health (*Amrita*).</li>
                  <li><strong>Karana (Earth Element):</strong> Governs tangible material success, career execution, and trade.</li>
                </ul>
              </div>

              <div className="space-y-1.5">
                <h4 className="font-bold text-sm text-cyan-600 dark:text-cyan-300 font-mono">
                  2. Understanding Auspicious &amp; Inauspicious Windows
                </h4>
                <ul className="list-disc list-inside space-y-1 pl-1 text-slate-600 dark:text-slate-300">
                  <li><strong>🌟 Abhijit Muhurta:</strong> The 8th Muhurta of the day (midday window). Lord Shiva blessed Abhijit to dissolve almost all planetary doshas (except on Wednesdays).</li>
                  <li><strong>🧘 Brahma Muhurta:</strong> 1 hour 36 minutes before sunrise. Sattva Guna is at its peak; optimal for meditation, study, writing, and strategic planning.</li>
                  <li><strong>⚠️ Rahu Kalam:</strong> 1.5-hour period each day governed by Rahu. Strictly avoid starting new journeys, major purchases, or signing long-term contracts.</li>
                </ul>
              </div>

              <div className="space-y-1.5">
                <h4 className="font-bold text-sm text-cyan-600 dark:text-cyan-300 font-mono">
                  3. Tarabala &amp; Chandrabala
                </h4>
                <p>
                  <strong>Tarabala:</strong> Measures the 9-fold cyclic relationship from your Janma Nakshatra to the day's Nakshatra. Taras 2 (*Sampat*), 4 (*Kshema*), 6 (*Sadhana*), 8 (*Mitra*), and 9 (*Parama Mitra*) guarantee success.
                </p>
                <p>
                  <strong>Chandrabala:</strong> The Moon must sit in favorable houses (1, 3, 6, 7, 10, 11) from your natal Moon sign. If the Moon sits in your 8th house (*Ashtama Chandra*), mental stress is high and major worldly inaugurations should be postponed.
                </p>
              </div>

              <div className="space-y-1.5">
                <h4 className="font-bold text-sm text-cyan-600 dark:text-cyan-300 font-mono">
                  4. Panchaka Dosha Guidelines
                </h4>
                <p>
                  Calculated by taking $(Tithi + Vara + Nakshatra + Lagna) \pmod 9$:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] pt-1">
                  <span className="p-2 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-mono">• Remainder 1 (Mrityu): Avoid vital surgeries</span>
                  <span className="p-2 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-mono">• Remainder 2 (Agni): Avoid kitchen / furnaces</span>
                  <span className="p-2 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-mono">• Remainder 4 (Raja): Avoid government petitions</span>
                  <span className="p-2 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-mono">• Remainder 6 (Chora): Avoid travel &amp; loans</span>
                  <span className="p-2 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-mono">• Remainder 8 (Roga): Avoid medical cures</span>
                  <span className="p-2 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-mono">• Remainder 0/3/5/7: Shubh / Nirbana (Clear)</span>
                </div>
              </div>
            </div>

            <div className="border-t border-slate-200 dark:border-slate-800 pt-4 flex justify-end">
              <button
                type="button"
                onClick={() => setShowHelpGuide(false)}
                className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs shadow-md transition-all cursor-pointer"
              >
                Close Help Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
