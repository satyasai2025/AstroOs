"use client";

import React, { useState } from "react";

interface ExplainabilityHelpGuideProps {
  lang?: "hi" | "en";
}

export function ExplainabilityHelpGuide({ lang: defaultLang = "hi" }: ExplainabilityHelpGuideProps) {
  const [lang, setLang] = useState<"hi" | "en">(defaultLang);
  const [activeTopic, setActiveTopic] = useState<string>("purpose");

  const topics = [
    {
      id: "purpose",
      icon: "🎯",
      titleHi: "स्टूडियो का उद्देश्य (Zero Black-Box)",
      titleEn: "Studio Purpose & Zero Black-Box",
    },
    {
      id: "factor_attribution",
      icon: "📊",
      titleHi: "फैक्टर वाटरफॉल (Attribution %)",
      titleEn: "Factor Attribution Waterfall",
    },
    {
      id: "classical_provenance",
      icon: "📜",
      titleHi: "शास्त्रीय श्लोक प्रमाण (Canonical Shlokas)",
      titleEn: "Canonical Shloka Provenance",
    },
    {
      id: "counterfactuals",
      icon: "🧪",
      titleHi: "काउंटरफैक्टुअल सिमुलेशन (Engine Rerun)",
      titleEn: "Counterfactual Recalculation",
    },
    {
      id: "epistemic_grades",
      icon: "🏷️",
      titleHi: "प्रमाणिकता स्तर (Epistemic Grades)",
      titleEn: "Epistemic Grading System",
    },
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-700/80 rounded-2xl p-5 md:p-6 shadow-2xl space-y-5 text-slate-100">
      {/* Header with Language Toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">🧠</span>
          <div>
            <h3 className="text-lg md:text-xl font-bold bg-gradient-to-r from-purple-300 via-pink-300 to-cyan-300 bg-clip-text text-transparent">
              {lang === "hi"
                ? "रिसर्च व प्रेडिक्शन व्याख्या मार्गदर्शिका (Explainability User Guide)"
                : "Research & Prediction Explainability Guide"}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {lang === "hi"
                ? "जानें कि AstroOS किसी भविष्यवाणी को 100% गणितीय और शास्त्रीय रूप से कैसे सिद्ध करता है"
                : "Learn how AstroOS transparently decomposes predictions into mathematical weights and canonical shlokas"}
            </p>
          </div>
        </div>

        {/* Language Switcher */}
        <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-lg border border-slate-700 text-xs font-semibold">
          <button
            onClick={() => setLang("hi")}
            className={`px-2.5 py-1 rounded transition ${
              lang === "hi" ? "bg-purple-600 text-white shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            हिंदी
          </button>
          <button
            onClick={() => setLang("en")}
            className={`px-2.5 py-1 rounded transition ${
              lang === "en" ? "bg-purple-600 text-white shadow" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            English
          </button>
        </div>
      </div>

      {/* Topic Selection Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {topics.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTopic(t.id)}
            className={`px-3 py-2 rounded-xl font-semibold flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTopic === t.id
                ? "bg-purple-600 text-white shadow-lg shadow-purple-600/30 font-bold border border-purple-400/40"
                : "bg-slate-950/70 border border-slate-800 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <span>{t.icon}</span>
            <span>{lang === "hi" ? t.titleHi : t.titleEn}</span>
          </button>
        ))}
      </div>

      {/* Topic Content Body */}
      <div className="bg-slate-950/80 p-5 md:p-6 rounded-xl border border-slate-800 text-xs md:text-sm leading-relaxed space-y-4">
        {/* 1. Purpose */}
        {activeTopic === "purpose" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-purple-300 flex items-center gap-2">
              <span>🎯</span>
              <span>
                {lang === "hi"
                  ? "यह एक्सप्लेनएबिलिटी (व्याख्या) स्टूडियो क्या है और क्यों आवश्यक है?"
                  : "What is this Explainability Studio and Why is it Essential?"}
              </span>
            </h4>
            <p className="text-slate-300">
              {lang === "hi"
                ? "साधारण ज्योतिषीय ऐप्स या जेनेरिक AI सिस्टम केवल एक अंतिम भविष्यवाणी दे देते हैं (जैसे: '2026 में विवाह होगा'), लेकिन यह नहीं बताते कि यह परिणाम कहाँ से आया। AstroOS में हम 'ब्लैक-बॉक्स' (Black-Box AI) का पूरी तरह विरोध करते हैं।"
                : "Standard astrology platforms or LLMs output opaque assertions (e.g. 'Marriage in 2026') without exposing the underlying chain of logic. AstroOS strictly rejects black-box opacity."}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              <div className="p-3 bg-purple-950/30 border border-purple-800/40 rounded-lg space-y-1">
                <div className="font-bold text-purple-300 text-xs">1. गणितीय विभाजन (Math Decomposition)</div>
                <p className="text-[11px] text-slate-400">
                  {lang === "hi"
                    ? "प्रत्येक ग्रह, भाव और गोचर का प्रतिशत योगदान देखें।"
                    : "Inspect the exact percentage contribution of each astrological factor."}
                </p>
              </div>
              <div className="p-3 bg-cyan-950/30 border border-cyan-800/40 rounded-lg space-y-1">
                <div className="font-bold text-cyan-300 text-xs">2. प्रामाणिक श्लोक (Shloka Citations)</div>
                <p className="text-[11px] text-slate-400">
                  {lang === "hi"
                    ? "BPHS एवं सारावली के सत्यापित श्लोक संदर्भ देखें।"
                    : "Trace every single rule back to canonical classical verses."}
                </p>
              </div>
              <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-lg space-y-1">
                <div className="font-bold text-amber-300 text-xs">3. संवेदनशीलता परीक्षण (Counterfactuals)</div>
                <p className="text-[11px] text-slate-400">
                  {lang === "hi"
                    ? "जन्म समय बदलने पर परिणाम पर क्या असर पड़ेगा, लाइव टेस्ट करें।"
                    : "Live simulate how minor birth-time shifts alter prediction certainty."}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 2. Factor Attribution */}
        {activeTopic === "factor_attribution" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-emerald-300 flex items-center gap-2">
              <span>📊</span>
              <span>
                {lang === "hi"
                  ? "फैक्टर वाटरफॉल (Mathematical Factor Decomposition) को कैसे समझें?"
                  : "How to Read the Factor Attribution Waterfall?"}
              </span>
            </h4>
            <p className="text-slate-300">
              {lang === "hi"
                ? "जब कोई इवेंट प्रेडिक्ट होता है, तो सिस्टम सभी शामिल कारकों को 100% के स्केल पर विभाजित (Normalized Weightage) करता है:"
                : "Every prediction is broken down into normalized atomic weights summing to 100%:"}
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-300">
              <li>
                <strong>Raw Score:</strong>{" "}
                {lang === "hi"
                  ? "ग्रह का मूल गणितीय बल (Main Strength, BAV Rekhas, या गोचर बल)।"
                  : "The intrinsic mathematical strength of the planet or house."}
              </li>
              <li>
                <strong>Calibrated Weight:</strong>{" "}
                {lang === "hi"
                  ? "पाराशरी पदानुक्रम में उस कारक का महत्व (जैसे महादशा स्वामी का भार गोचर से अधिक होता है)।"
                  : "Hierarchical importance in classical Parashari priority."}
              </li>
              <li>
                <strong>Contribution %:</strong>{" "}
                {lang === "hi"
                  ? "अंतिम निर्णय में उस कारक की वास्तविक हिस्सेदारी (जैसे 7th Lord Antardasha = 28.5% Contribution)।"
                  : "The exact share of confidence contributed to the overall event prediction."}
              </li>
            </ul>
          </div>
        )}

        {/* 3. Classical Provenance */}
        {activeTopic === "classical_provenance" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-cyan-300 flex items-center gap-2">
              <span>📜</span>
              <span>
                {lang === "hi"
                  ? "शास्त्रीय श्लोक एवं प्रामाणिकता (Canonical Citations)"
                  : "Canonical Shloka Lineage & Verification"}
              </span>
            </h4>
            <p className="text-slate-300">
              {lang === "hi"
                ? "AstroOS का प्रत्येक नियम सीधे महर्षि पराशर के *बृहत्पाराशर होराशास्त्र (BPHS)*, कल्याणवर्मा की *सारावली*, या वराहमिहिर की *बृहत्संहिता* से सत्यापित है:"
                : "Every rule in AstroOS is strictly tethered to canonical Jyotisha classics:"}
            </p>
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-2 text-xs">
              <div className="flex items-center justify-between font-mono">
                <span className="text-cyan-400 font-semibold">BPHS Ch. 46 / Shloka 15-18</span>
                <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded text-[10px] font-bold">
                  VERIFIED CANONICAL
                </span>
              </div>
              <p className="text-slate-400">
                {lang === "hi"
                  ? "सत्यापित टैग का अर्थ है कि इस नियम को हमारे कॉर्पस डेटाबेस और क्लासिकल टेक्स्ट से हूबहू मिलाया गया है।"
                  : "A 'Verified Canonical' tag confirms that the rule matches genuine classical treatises verbatim."}
              </p>
            </div>
          </div>
        )}

        {/* 4. Counterfactuals */}
        {activeTopic === "counterfactuals" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-amber-300 flex items-center gap-2">
              <span>🧪</span>
              <span>
                {lang === "hi"
                  ? "काउंटरफैक्टुअल संवेदनशीलता सिमुलेशन (Engine Rerun) क्या है?"
                  : "What is Counterfactual Sensitivity Simulation?"}
              </span>
            </h4>
            <p className="text-slate-300">
              {lang === "hi"
                ? "यह एस्ट्रो-रिसर्च का सबसे शक्तिशाली टूल है। मान लीजिए किसी जातक का जन्म समय 3 मिनट आगे या पीछे हो जाए, तो:"
                : "Counterfactual analysis is the gold standard of scientific astrology. It allows you to test: 'What if birth time shifted by 3 minutes?'"}
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-300">
              <li>{lang === "hi" ? "क्या नवांश (D9) लग्न बदल जाएगा?" : "Does the D9 Navamsha Lagna cross a boundary?"}</li>
              <li>{lang === "hi" ? "क्या सत्य-तिथि दशा की तारीखें शिफ्ट हो जाएंगी?" : "Do True-Tithi Dasha entry timestamps shift?"}</li>
              <li>{lang === "hi" ? "क्या प्रेडिक्शन का कॉन्फिडेंस स्कोर 85% से गिरकर 42% हो जाएगा?" : "Does the composite confidence score drop significantly?"}</li>
            </ul>
            <p className="text-slate-400 text-xs">
              {lang === "hi"
                ? "यह सिमुलेशन कोई अंदाज़ा नहीं लगाता, बल्कि सीधे हमारे बैकएंड इंजन को नए इनपुट पर रिरन (Recalculate) करके वास्तविक डेल्टा (Score Delta %) दिखाता है।"
                : "This simulation does not guess — it executes a live backend recalculation of our ephemeris and varga engines."}
            </p>
          </div>
        )}

        {/* 5. Epistemic Grades */}
        {activeTopic === "epistemic_grades" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-purple-300 flex items-center gap-2">
              <span>🏷️</span>
              <span>
                {lang === "hi"
                  ? "प्रमाणिकता स्तर (Epistemic Grading System)"
                  : "Epistemic Grading System"}
              </span>
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-lg space-y-1">
                <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded text-[10px] font-bold">
                  GRADE A
                </span>
                <div className="font-semibold text-white text-xs mt-1">
                  {lang === "hi" ? "ऋषि पाराशर सिद्धांत" : "Core Canonical Shastra"}
                </div>
                <p className="text-[11px] text-slate-400">
                  {lang === "hi"
                    ? "BPHS, सारावली, जातक पारिजात जैसे मूल ग्रंथों का सीधा नियम।"
                    : "Direct rules from BPHS, Saravali, and foundational treatises."}
                </p>
              </div>

              <div className="p-3 bg-cyan-950/30 border border-cyan-800/40 rounded-lg space-y-1">
                <span className="bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded text-[10px] font-bold">
                  GRADE B
                </span>
                <div className="font-semibold text-white text-xs mt-1">
                  {lang === "hi" ? "व्याख्याता व टीकाकार" : "Classical Commentators"}
                </div>
                <p className="text-[11px] text-slate-400">
                  {lang === "hi"
                    ? "भट्टोत्पल, वराहमिहिर या नीलकंठ की शास्त्रीय व्याख्याएं।"
                    : "Revered classical commentary and multi-century traditional applications."}
                </p>
              </div>

              <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-lg space-y-1">
                <span className="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded text-[10px] font-bold">
                  GRADE C
                </span>
                <div className="font-semibold text-white text-xs mt-1">
                  {lang === "hi" ? "अनुभवजन्य शोध (Empirical)" : "Empirical Calibration"}
                </div>
                <p className="text-[11px] text-slate-400">
                  {lang === "hi"
                    ? "हजारों जन्मकुंडलियों के डेटाबेस पर सत्यापित सांख्यिकीय निष्कर्ष।"
                    : "Statistically verified patterns across large-scale historical cohorts."}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
