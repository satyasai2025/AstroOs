"use client";

import React, { useState } from "react";

interface ShastricHelpGuideProps {
  lang?: "hi" | "en";
}

export function ShastricHelpGuide({ lang = "en" }: ShastricHelpGuideProps) {
  const [activeTopic, setActiveTopic] = useState<string>("timeline");

  const topics = [
    {
      id: "timeline",
      icon: "⚖️",
      titleHi: "4-स्तरीय निर्णय टाइमलाइन (Roadmap)",
      titleEn: "4-Tier Decision Timeline",
    },
    {
      id: "triple_dasha",
      icon: "🌟",
      titleHi: "त्रि-दशा संगम (100% अचूक नियम)",
      titleEn: "Triple-Dasha Confluence",
    },
    {
      id: "double_transit",
      icon: "✨",
      titleHi: "द्वि-गोचर (Double Transit)",
      titleEn: "Double Transit Rule",
    },
    {
      id: "bhavottama",
      icon: "⭐",
      titleHi: "भावोत्तम सुपर-शक्ति (Bhāvottama)",
      titleEn: "Bhāvottama Amplification",
    },
    {
      id: "sav_points",
      icon: "📊",
      titleHi: "10H SAV बिंदु (Karma Strength)",
      titleEn: "10th House SAV Bindus",
    },
    {
      id: "sudarshana",
      icon: "☸️",
      titleHi: "सुदर्शन चक्र (Tri-Lagna Analysis)",
      titleEn: "Sudarshana Chakra (3-Lagnas)",
    },
    {
      id: "bhrigu_sbc",
      icon: "⚡",
      titleHi: "भृगु बिन्दु व SBC गोचर वेध",
      titleEn: "Bhrigu Bindu & SBC Shield",
    },
  ];

  return (
    <div className="bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 md:p-6 shadow-xl space-y-6 text-slate-900 dark:text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📖</span>
          <h3 className="text-lg md:text-xl font-bold text-slate-900 dark:bg-gradient-to-r dark:from-amber-200 dark:via-amber-400 dark:to-cyan-300 dark:bg-clip-text dark:text-transparent">
            {lang === "hi" ? "AstroOS सरल शास्त्रीय मार्गदर्शिका (User Help Guide)" : "AstroOS Plain Shastric User Guide"}
          </h3>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
          {lang === "hi"
            ? "कठिन ज्योतिषीय शब्दों और गणनाओं का सरल भाषा में अर्थ और उपयोग"
            : "Simple, practical explanations for all classical astrological terms and metrics"}
        </p>
      </div>

      {/* Topic Selection Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 text-xs">
        {topics.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTopic(t.id)}
            className={`px-3.5 py-2 rounded-xl font-bold flex items-center gap-1.5 transition whitespace-nowrap ${
              activeTopic === t.id
                ? "bg-amber-500 text-slate-950 shadow-md font-black"
                : "bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:border-slate-700"
            }`}
          >
            <span>{t.icon}</span>
            <span>{lang === "hi" ? t.titleHi : t.titleEn}</span>
          </button>
        ))}
      </div>

      {/* Topic Content */}
      <div className="bg-slate-50 dark:bg-slate-950 p-5 md:p-6 rounded-xl border border-slate-200 dark:border-slate-800/80 text-slate-800 dark:text-slate-200 text-xs md:text-sm leading-relaxed space-y-4 shadow-sm">
        {/* 1. Timeline */}
        {activeTopic === "timeline" && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-amber-800 dark:text-amber-400 flex items-center gap-2">
              <span>⚖️</span>
              <span>
                {lang === "hi"
                  ? "4-स्तरीय निर्णय टाइमलाइन को कैसे पढ़ें?"
                  : "How to Interpret the 4-Tier Decision Timeline?"}
              </span>
            </h4>
            <p className="text-slate-700 dark:text-slate-300">
              {lang === "hi"
                ? "यह टाइमलाइन आपके जीवन के आने वाले 10-15 वर्षों को 4 स्पष्ट श्रेणियों में विभाजित करती है, ताकि आप जान सकें कि कब बड़ा कदम उठाना है और कब धैर्य रखना है:"
                : "This timeline segments life periods into 4 distinct supervisory tiers to guide strategic action:"}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
              <div className="p-3.5 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/50 rounded-xl space-y-1 shadow-sm">
                <div className="font-bold text-emerald-800 dark:text-emerald-400 text-sm flex items-center gap-1.5">
                  <span>🟢</span>
                  <span>{lang === "hi" ? "प्रत्यक्ष फल (Pratyaksha Phala)" : "Pratyaksha Phala (Landmark Event)"}</span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300">
                  {lang === "hi"
                    ? "यह जीवन का सबसे बड़ा मील का पत्थर है! इस समय पदोन्नति, नया बिज़नेस, विवाह, विदेश यात्रा या बड़ी उपलब्धि का 100% योग बनता है।"
                    : "Major breakthrough window. Dasha, Gochara, and double-transits align for peak career, financial, or personal success."}
                </p>
              </div>

              <div className="p-3.5 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800/50 rounded-xl space-y-1 shadow-sm">
                <div className="font-bold text-blue-800 dark:text-blue-400 text-sm flex items-center gap-1.5">
                  <span>🔵</span>
                  <span>{lang === "hi" ? "सुषुप्त बीज (Sushupta Beeja)" : "Sushupta Beeja (Preparation Phase)"}</span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300">
                  {lang === "hi"
                    ? "यह 'बीज' बोने का समय है। इस समय की गई पढ़ाई, कौशल विकास और योजना का फल अगले प्रत्यक्ष फल के समय भरपूर मिलता है।"
                    : "Latent fertile period. Focus on skill building, preparation, and foundational planning."}
                </p>
              </div>

              <div className="p-3.5 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-xl space-y-1 shadow-sm">
                <div className="font-bold text-amber-800 dark:text-amber-400 text-sm flex items-center gap-1.5">
                  <span>🟡</span>
                  <span>{lang === "hi" ? "अल्प फल (Alpa Phala)" : "Alpa Phala (Minor Transient Trigger)"}</span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300">
                  {lang === "hi"
                    ? "अल्पकालीन लाभ या छोटे बदलाव। इसमें कोई बड़ा जोखिम न लें, लेकिन छोटे अवसरों का लाभ उठाएं।"
                    : "Short-lived temporary opportunities or minor adjustments."}
                </p>
              </div>

              <div className="p-3.5 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1 shadow-sm">
                <div className="font-bold text-slate-700 dark:text-slate-400 text-sm flex items-center gap-1.5">
                  <span>⚪</span>
                  <span>{lang === "hi" ? "सामान्य काल (Samanya Kal)" : "Samanya Kal (Routine Period)"}</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {lang === "hi"
                    ? "सामान्य और स्थिर समय। जीवन सामान्य गति से चलता है, कोई बड़ा संकट या भारी उछाल नहीं होता।"
                    : "Steady baseline routine without major upheavals."}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 2. Double Transit */}
        {activeTopic === "double_transit" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-cyan-800 dark:text-cyan-400 flex items-center gap-2">
              <span>✨</span>
              <span>
                {lang === "hi"
                  ? "द्वि-गोचर (Double Transit) क्या है और यह क्यों सबसे शक्तिशाली है?"
                  : "What is the Double Transit Rule?"}
              </span>
            </h4>
            <p className="text-slate-700 dark:text-slate-300">
              {lang === "hi"
                ? "प्राचीन महर्षियों के अनुसार, जब तक ब्रह्मांड के दो सबसे बड़े ग्रह — देवगुरु बृहस्पति (आशीर्वाद व विस्तार) और कर्मफलदाता शनि (कर्म व स्थायित्व) — दोनों मिलकर किसी भाव पर अपनी दृष्टि या गोचर नहीं डालते, तब तक कोई भी बड़ी घटना वास्तविक रूप में घटित नहीं होती।"
                : "According to classical Shastras, no landmark event materializes in physical reality unless both Jupiter (expansion/grace) and Saturn (karma/manifestation) simultaneously influence the target house."}
            </p>
            <div className="p-3 bg-amber-100/70 dark:bg-amber-500/10 border border-amber-300 dark:border-amber-500/30 rounded-xl text-amber-900 dark:text-amber-200 text-xs shadow-sm">
              💡 {lang === "hi" ? "जहाँ भी टाइमलाइन में '✓ Double Transit' दिखे, समझें कि वह समय परिणाम देने के लिए 100% परिपक्व है।" : "Whenever '✓ Double Transit' is present, event manifestation confidence is at its peak."}
            </div>
          </div>
        )}

        {/* 3. Bhavottama */}
        {activeTopic === "bhavottama" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-amber-800 dark:text-amber-400 flex items-center gap-2">
              <span>⭐</span>
              <span>
                {lang === "hi"
                  ? "भावोत्तम (Bhāvottama 1.5x - 2.0x) सुपर-एम्प्लीफिकेशन क्या है?"
                  : "What is Bhāvottama Super-Amplification?"}
              </span>
            </h4>
            <p className="text-slate-700 dark:text-slate-300">
              {lang === "hi"
                ? "जब कोई ग्रह लग्न कुंडली (D1) और नवांश कुंडली (D9) दोनों में बिल्कुल एक ही भाव (House) में बैठता है, तो उसे 'भावोत्तम' कहा जाता है। ऐसे ग्रह की फल देने की क्षमता साधारण ग्रह की तुलना में 1.5 गुना से 2 गुना तक बढ़ जाती है।"
                : "When a planet occupies the exact same house in both D1 (Lagna) and D9 (Navamsha), it gains Bhāvottama dignity, amplifying its positive event delivery by 1.5x to 2.0x."}
            </p>
          </div>
        )}

        {/* 4. SAV Points */}
        {activeTopic === "sav_points" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-cyan-800 dark:text-cyan-400 flex items-center gap-2">
              <span>📊</span>
              <span>
                {lang === "hi"
                  ? "10H SAV (सर्व्राष्टकवर्ग बिंदु) का क्या अर्थ है?"
                  : "What are 10th House SAV Bindus?"}
              </span>
            </h4>
            <p className="text-slate-700 dark:text-slate-300">
              {lang === "hi"
                ? "अष्टकवर्ग में 10वें भाव (करियर, मान-सम्मान व कर्म) के कुल शुभ बिंदुओं (Points) को 10H SAV कहा जाता है। औसत मान 28 बिंदु होता है। यदि 29 या उससे अधिक बिंदु हैं, तो व्यक्ति का करियर तूफानों के बीच भी अडिग और मजबूत बना रहता है।"
                : "The 10th House Sarvashtakavarga score measures professional resilience. The benchmark average is 28. Scores of 29 or higher indicate robust career stability."}
            </p>
          </div>
        )}

        {/* 5. Sudarshana */}
        {activeTopic === "sudarshana" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-amber-800 dark:text-amber-400 flex items-center gap-2">
              <span>☸️</span>
              <span>
                {lang === "hi"
                  ? "सुदर्शन चक्र (Sudarshana Chakra) के 3 छल्ले क्या बताते हैं?"
                  : "What do the 3 Rings of Sudarshana Chakra Reveal?"}
              </span>
            </h4>
            <p className="text-slate-700 dark:text-slate-300">
              {lang === "hi"
                ? "सुदर्शन चक्र जीवन को तीन अलग-अलग दृष्टिकोणों से देखता है:"
                : "Sudarshana Chakra examines life through three concentric planes:"}
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
              <li><strong>{lang === "hi" ? "बाहरी छल्ला (लग्न कुंडली - LK)" : "Outer Ring (Lagna LK)"}</strong>: {lang === "hi" ? "शारीरिक स्वास्थ्य और प्रत्यक्ष कर्म।" : "Physical health and external action."}</li>
              <li><strong>{lang === "hi" ? "मध्य छल्ला (चन्द्र कुंडली - CK)" : "Middle Ring (Chandra CK)"}</strong>: {lang === "hi" ? "मानसिक शांति, भावनाएं और पारिवारिक सुख।" : "Mind, emotions, and personal happiness."}</li>
              <li><strong>{lang === "hi" ? "आंतरिक छल्ला (सूर्य कुंडली - SK)" : "Inner Ring (Surya SK)"}</strong>: {lang === "hi" ? "आत्मा, तेज, शक्ति और आत्म-सम्मान।" : "Soul, vitality, authority, and destiny drive."}</li>
            </ul>
          </div>
        )}

        {/* 1.5. Triple Dasha Confluence */}
        {activeTopic === "triple_dasha" && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-amber-800 dark:text-amber-400 flex items-center gap-2">
              <span>🌟</span>
              <span>
                {lang === "hi"
                  ? "त्रि-दशा संगम (Triveni Sangam) क्या है और यह 100% अचूक क्यों है?"
                  : "What is Triple-Dasha Confluence (Triveni Sangam)?"}
              </span>
            </h4>
            <p className="text-slate-700 dark:text-slate-300">
              {lang === "hi"
                ? "प्राचीन महर्षियों का नियम है कि किसी एक दशा पर निर्भर रहने से 70-75% तक ही सटीकता मिलती है। परंतु जब 3 स्वतंत्र प्रणालियां एक साथ एक ही भाव को सक्रिय करती हैं, तो परिणाम 100% निश्चित (Infallible) हो जाता है:"
                : "Classical Jyotish dictates that a single dasha system provides ~70-75% timing fidelity. When 3 independent classical timing systems simultaneously converge, manifestation certainty reaches 100%:"}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
              <div className="p-3 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800/60 rounded-xl space-y-1 shadow-sm">
                <div className="font-bold text-purple-900 dark:text-purple-300 text-xs">1. विंशोत्तरी दशा (Vimshottari)</div>
                <p className="text-[11px] text-slate-700 dark:text-slate-300">
                  {lang === "hi" ? "चन्द्र-नक्षत्र आधारित — जातक की मानसिक तैयारी व आंतरिक इच्छा।" : "Moon-Nakshatra based — mental receptivity and internal readiness."}
                </p>
              </div>
              <div className="p-3 bg-cyan-50 dark:bg-cyan-950/40 border border-cyan-200 dark:border-cyan-800/60 rounded-xl space-y-1 shadow-sm">
                <div className="font-bold text-cyan-900 dark:text-cyan-300 text-xs">2. सुदर्शन चक्र दशा (SCD)</div>
                <p className="text-[11px] text-slate-700 dark:text-slate-300">
                  {lang === "hi" ? "3-लग्न प्रोग्रेशन — उस वर्ष का सक्रिय भाव और अधिकार।" : "3-Lagna annual progression — active house authority for the year."}
                </p>
              </div>
              <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-xl space-y-1 shadow-sm">
                <div className="font-bold text-amber-900 dark:text-amber-300 text-xs">3. जैमिनी चर दशा (Chara Dasha)</div>
                <p className="text-[11px] text-slate-700 dark:text-slate-300">
                  {lang === "hi" ? "राशि आधारित — भौतिक संसार, पद, प्रतिष्ठा व वास्तविक परिणाम।" : "Rashi based — material manifestation, status, and external environment."}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 6. Bhrigu & SBC */}
        {activeTopic === "bhrigu_sbc" && (
          <div className="space-y-3">
            <h4 className="text-base font-bold text-cyan-800 dark:text-cyan-400 flex items-center gap-2">
              <span>⚡</span>
              <span>
                {lang === "hi"
                  ? "भृगु बिन्दु और सर्वतोभद्र चक्र (SBC) का क्या कार्य है?"
                  : "What are Bhrigu Bindu and SBC Transit Shield?"}
              </span>
            </h4>
            <p className="text-slate-700 dark:text-slate-300">
              {lang === "hi"
                ? "भृगु बिन्दु चन्द्रमा और राहु के बीच का गणितीय भाग्य-बिन्दु (Destiny Trigger) है। जब कोई शुभ ग्रह इस बिन्दु पर गोचर करता है, तो जीवन में अचानक नया मोड़ या बड़ा अवसर मिलता है। सर्वतोभद्र चक्र (28-नक्षत्र) यह देखता है कि वर्तमान में आपके जन्म नक्षत्र पर कोई दुष्प्रभाव या वेध तो नहीं लग रहा।"
                : "Bhrigu Bindu marks destiny trigger events. The 28-Nakshatra Sarvato-Bhadra Chakra evaluates real-time planetary vedhas (afflictions or protections) on natal key nakshatras."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
