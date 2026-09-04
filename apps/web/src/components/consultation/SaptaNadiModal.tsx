"use client";

import React from "react";

export interface SaptaNadiDetails {
  name: string;
  hindiName: string;
  element: string;
  elementHi: string;
  ruler: string;
  icon: string;
  tagline: string;
  taglineHi: string;
  personalImpact: {
    health: string;
    healthHi: string;
    psychology: string;
    psychologyHi: string;
    career: string;
    careerHi: string;
  };
  actionableGuidance: {
    dos: string[];
    dosHi: string[];
    donts: string[];
    dontsHi: string[];
  };
}

export const SAPTA_NADI_KNOWLEDGE: Record<string, SaptaNadiDetails> = {
  vata: {
    name: "Vata (Pavana) Nadi — Air / Wind Element",
    hindiName: "वात / पवन नाड़ी (वायु तत्व)",
    element: "Air / Dynamic Wind (Vata)",
    elementHi: "वायु / पवन तत्व",
    ruler: "Mercury / Moon / Rahu (Budha / Chandra / Rahu)",
    icon: "🌪️",
    tagline: "High cognitive dynamism, nervous system sensitivity, and rapid idea generation",
    taglineHi: "तीव्र गतिशीलता, तंत्रिका संवेदनशीलता और विचार-प्रवाह का काल",
    personalImpact: {
      health: "Pronounced Vata dosha tendencies. Nervous system is heightened. Increased susceptibility to restless sleep, joint dryness, digestive irregularity, and mental fatigue if overworked.",
      healthHi: "शरीर में वात दोष की प्रधानता। तंत्रिका तंत्र अति-सक्रिय रहता है। अनिद्रा, जोड़ों में खिंचाव, त्वचा में रूखापन और पाचन में अनियमितता की संभावना रहती है।",
      psychology: "Mind is extraordinarily agile, creative, and full of multidirectional thoughts. High multitasking ability, but prone to overthinking, scattered focus, and restlessness.",
      psychologyHi: "मन अत्यंत तीव्र, चंचल और नए विचारों से भरा रहता है। एक साथ कई योजनाओं पर काम करने की इच्छा, लेकिन बेचैनी और ओवरथिंकिंग से ऊर्जा बिखर सकती है।",
      career: "Exceptional speed in communications, quantitative analysis, technology architectures, media, and travel-oriented strategic initiatives.",
      careerHi: "संचार, टेक्नोलॉजी, मीडिया और यात्रा से जुड़े कार्यों में त्वरित अवसर मिलते हैं।",
    },
    actionableGuidance: {
      dos: [
        "Consume warm, freshly prepared, grounding foods (ghee/healthy oils) and maintain fixed sleep cycles.",
        "Deliberate on critical contracts or major life commitments for 24 hours before executing.",
        "Practice daily grounding exercises: Pranayama (Anulom-Vilom), walking in nature, and meditation.",
      ],
      dosHi: [
        "गर्म, ताजा, स्निग्ध (घी/तिल तेल) आहार लें और नियमित समय पर सोएँ।",
        "महत्वपूर्ण अनुबंध या बड़े फैसले 24 घंटे शांत मन से सोचकर लें।",
        "प्राणायाम (अनुलोम-विलोम), ध्यान और प्रकृति में नियमित सैर करें।",
      ],
      donts: [
        "Avoid stale, overly dry, cold, or fast-processed foods.",
        "Avoid reactive, hurried decisions under transient emotional pressure.",
        "Avoid late-night screen marathons and irregular waking hours.",
      ],
      dontsHi: [
        "बासी, सूखा या अत्यधिक ठंडा भोजन करने से बचें।",
        "हड़बड़ी या घबराहट में तुरंत प्रतिक्रिया देने से बचें।",
        "लगातार देर रात तक जागकर स्क्रीन देखने से बचें।",
      ],
    },
  },
  chanda: {
    name: "Chanda Nadi — Solar / Intense Fire Element",
    hindiName: "चण्ड नाड़ी (प्रचंड अग्नि तत्व)",
    element: "Solar Fire (Pitta / Tejas)",
    elementHi: "तीव्र सौर अग्नि तत्व",
    ruler: "Sun (Surya)",
    icon: "☀️",
    tagline: "Radiant executive vitality, authoritative leadership, and intense transformation",
    taglineHi: "प्रखर ऊर्जा, नेतृत्व, आत्म-विश्वास और ताप का संचार",
    personalImpact: {
      health: "Elevated Pitta constitution, sensitivity to heat, eye strain, or blood pressure. Physical drive and stamina are peaked.",
      healthHi: "पित्त और रक्तचाप की संवेदनशीलता, सिरदर्द या आँखों में तनाव। शारीरिक ऊर्जा चरम पर रहती है।",
      psychology: "Unstoppable ambition, commanding presence, and clear executive vision. Guard against ego friction or impatience.",
      psychologyHi: "अदम्य साहस, महत्वाकांक्षा और नेतृत्व क्षमता। अहंकार या क्रोध पर नियंत्रण रखना आवश्यक होता है।",
      career: "Government administrative approvals, corporate leadership, high-stakes negotiations, and public authority.",
      careerHi: "सरकारी कार्य, प्रशासनिक निर्णय, प्रबंधन और उच्च पदों पर प्रभावशाली प्रगति।",
    },
    actionableGuidance: {
      dos: [
        "Stay properly hydrated, consume cooling foods (coconut water, fresh fruits), and practice measured leadership.",
        "Channel energy into structured physical discipline and organizational governance.",
      ],
      dosHi: ["शीतल पेय, पर्याप्त जल और सकारात्मक नेतृत्व अपनाएँ।", "सूर्य नमस्कार और अनुशासन का पालन करें।"],
      donts: ["Avoid spicy, excessively salty foods and confrontational arguments over pride."],
      dontsHi: ["अत्यधिक तीखा/मसालेदार भोजन और बेवजह के विवादों से बचें।"],
    },
  },
  dahana: {
    name: "Dahana Nadi — Burning Fire / Friction Element",
    hindiName: "दहन नाड़ी (दाहक अग्नि तत्व)",
    element: "Combustion / Friction (Agni)",
    elementHi: "दाहक अग्नि तत्व",
    ruler: "Mars / Ketu (Mangala / Ketu)",
    icon: "🔥",
    tagline: "Decisive courage, surgical precision, and strategic breakthrough energy",
    taglineHi: "साहस, निर्णायक संघर्ष और रूपांतरण का काल",
    personalImpact: {
      health: "Sensitivity to inflammation, acidity, cuts, sports injuries, or surgical interventions. Discipline in movement is vital.",
      healthHi: "रक्त विकार, जलन, चोट या सर्जरी की संवेदनशीलता। सतर्कता और संयम जरूरी है।",
      psychology: "High risk appetite and fearless determination, but susceptible to impulsiveness and irritation.",
      psychologyHi: "तीव्र इच्छाशक्ति और जोखिम लेने की क्षमता, लेकिन अधीरता से बचना चाहिए।",
      career: "Engineering breakthroughs, surgical operations, defense, real estate, and rapid technical problem-solving.",
      careerHi: "इंजीनियरिंग, सर्जरी, रक्षा, रियल एस्टेट और तकनीकी क्षेत्रों में निर्णायक लाभ।",
    },
    actionableGuidance: {
      dos: ["Channel adrenaline into intense workouts, technical mastery, and defensive driving."],
      dosHi: ["नियमित व्यायाम, संयम और सावधानीपूर्वक वाहन चालन करें।"],
      donts: ["Avoid rash maneuvers, road rage, or making impulsive financial gambles."],
      dontsHi: ["उतावलेपन में जोखिम भरे कदम न उठाएँ।"],
    },
  },
  saumya: {
    name: "Saumya Nadi — Gentle / Harmonious Earth-Water Element",
    hindiName: "सौम्य नाड़ी (सौम्य जल व पृथ्वी तत्व)",
    element: "Gentle Harmony (Saumya)",
    elementHi: "सौम्य जल व पृथ्वी तत्व",
    ruler: "Venus / Mercury (Shukra / Budha)",
    icon: "🌸",
    tagline: "Diplomatic harmony, creative synthesis, intellectual clarity, and social grace",
    taglineHi: "सौहार्द, कला, संतुलन, सुख और बौद्धिक विकास",
    personalImpact: {
      health: "Well-balanced biological constitution, resilient immune function, and natural hormonal equilibrium.",
      healthHi: "स्वास्थ्य में संतुलन और रोग-प्रतिरोधक क्षमता (Immunity) मजबूत रहती है।",
      psychology: "Poised, cheerful, diplomatic, and perceptive mindset. Enhanced relationship warmth and collaboration.",
      psychologyHi: "शांत, प्रसन्न और कूटनीतिक सोच। रिश्तों और साझेदारी में मधुरता।",
      career: "Creative industries, design, law, corporate alliances, wealth management, and public relations.",
      careerHi: "कला, रचनात्मकता, डिजाइनिंग, वित्त, कानून और जन-संपर्क में शानदार प्रगति।",
    },
    actionableGuidance: {
      dos: ["Launch partnership negotiations, aesthetic/product redesigns, and strategic alliances."],
      dosHi: ["नये रचनात्मक प्रोजेक्ट शुरू करें और संबंध मजबूत करें।"],
      donts: ["Avoid complacency or delaying execution due to comfortable conditions."],
      dontsHi: ["अत्यधिक विलासिता या आराम में समय व्यर्थ न करें।"],
    },
  },
  neera: {
    name: "Neera Nadi — Fertile Rain / Abundance Element",
    hindiName: "नीर नाड़ी (उर्वर जल तत्व)",
    element: "Fertile Rain (Neera / Varuna)",
    elementHi: "उर्वर वर्षा जल तत्व",
    ruler: "Jupiter (Guru / Brihaspati)",
    icon: "🌧️",
    tagline: "Wisdom expansion, bodily vitality, intellectual nourishment, and ethical growth",
    taglineHi: "ज्ञान, प्रचुरता और जीवन में उर्वरता का संचार",
    personalImpact: {
      health: "Nourished Kapha balance, robust vitality, and strong regenerative potential across all bodily tissues.",
      healthHi: "शरीर में कफ व जल का संतुलन। उत्तम स्वास्थ्य और नई जीवन-शक्ति।",
      psychology: "Philosophical depth, generous perspective, optimism, and grounded moral clarity.",
      psychologyHi: "गंभीर, दार्शनिक, संतोषी और परोपकारी मनोवृत्ति।",
      career: "Academic appointments, wealth advisories, judicial decisions, institutional funding, and spiritual progress.",
      careerHi: "शिक्षा, परामर्श, बैंकिंग और आध्यात्मिक उन्नति के द्वार खुलते हैं।",
    },
    actionableGuidance: {
      dos: ["Execute long-term investments, mentorship initiatives, and advanced studies."],
      dosHi: ["अध्ययन, निवेश और मार्गदर्शन के कार्य करें।"],
      donts: ["Avoid complacency or unexamined over-optimism."],
      dontsHi: ["आलस्य या अति-आत्मविश्वास से बचें।"],
    },
  },
  jala: {
    name: "Jala Nadi — Deep Oceanic / Emotional Water Element",
    hindiName: "जल नाड़ी (गहन जल तत्व)",
    element: "Deep Water (Jala / Soma)",
    elementHi: "गहन जल तत्व",
    ruler: "Moon / Venus (Chandra / Shukra)",
    icon: "🌊",
    tagline: "Intuitive perception, emotional depth, fluid adaptation, and somatic rhythm",
    taglineHi: "भावुकता, अंतर्ज्ञान, जल-प्रवाह और प्राकृतिक संतुलन",
    personalImpact: {
      health: "Fluctuations in lymphatic and fluid balance. Pay careful attention to hydration and hormonal cycles.",
      healthHi: "कफ और हार्मोन्स में उतार-चढ़ाव। जल-संतुलन और तरल आहार का ध्यान रखें।",
      psychology: "Heightened intuitive cognition, deep empathy, artistic sensitivity, and subconscious awareness.",
      psychologyHi: "अत्यधिक संवेदनशील, सहज ज्ञान (Intuition) और गहरी अनुभूति।",
      career: "Psychology, healthcare, chemistry, arts, creative storytelling, and counseling.",
      careerHi: "परामर्श, चिकित्सा, कला और रचनात्मक क्षेत्रों में सफलता।",
    },
    actionableGuidance: {
      dos: ["Harness emotional intelligence into creative work, team mentoring, and reflective journaling."],
      dosHi: ["भावनाओं को रचनात्मक दिशा दें और पर्याप्त विश्राम करें।"],
      donts: ["Avoid taking critical life decisions during emotional lows or fatigue."],
      dontsHi: ["अति-संवेदनशीलता में आकर नकारात्मक विचार न लाएँ।"],
    },
  },
  amrita: {
    name: "Amrita Nadi — Nectar / Sovereign Healing Element",
    hindiName: "अमृत नाड़ी (परम कल्याणकारी अमृत तत्व)",
    element: "Divine Nectar (Amrita / Ojas)",
    elementHi: "परम कल्याणकारी अमृत तत्व",
    ruler: "Sovereign Benefics / Jupiter / Venus",
    icon: "✨",
    tagline: "Total biological rejuvenation, institutional acclaim, and sovereign harmony",
    taglineHi: "समग्र स्वास्थ्य, आरोग्य, सर्व-सिद्धि और आंतरिक शांति",
    personalImpact: {
      health: "Deep cellular healing, reversal of chronic exhaustion, and peak radiance (Ojas).",
      healthHi: "पुराने रोगों से मुक्ति (Deep healing), ओज और तेज में असाधारण वृद्धि।",
      psychology: "Unshakable mental clarity, profound equanimity, fearlessness, and deep contentment.",
      psychologyHi: "शांति, स्पष्टता, निर्भयता और आंतरिक तृप्ति।",
      career: "Lifetime landmark achievements, public honors, and lasting professional milestones.",
      careerHi: "सम्मान, सफलता और दीर्घकालिक प्रतिष्ठा।",
    },
    actionableGuidance: {
      dos: ["Initiate high-impact long-range visions, health transformations, and major life commitments."],
      dosHi: ["नए संकल्प और दीर्घकालिक लक्ष्यों की शुरुआत करें।"],
      donts: ["Do not let this rare auspicious window pass without undertaking decisive positive actions."],
      dontsHi: ["इस शुभ काल का लाभ उठाए बिना निष्क्रिय न बैठें।"],
    },
  },
};

interface SaptaNadiModalProps {
  isOpen: boolean;
  onClose: () => void;
  dominantNadi: string;
  lang?: "en" | "hi";
}

export const SaptaNadiModal: React.FC<SaptaNadiModalProps> = ({
  isOpen,
  onClose,
  dominantNadi,
  lang = "en",
}) => {
  if (!isOpen) return null;

  const isHi = lang === "hi";
  const key = dominantNadi?.toLowerCase().trim() || "vata";
  const details = SAPTA_NADI_KNOWLEDGE[key] || SAPTA_NADI_KNOWLEDGE["vata"];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl overflow-y-auto max-h-[90vh] text-slate-900 dark:text-slate-100">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
          <div className="flex items-center gap-3.5">
            <span className="text-4xl p-2.5 rounded-2xl bg-cyan-50 dark:bg-cyan-950/50 border border-cyan-200 dark:border-cyan-800/60 shadow-inner">
              {details.icon}
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-black uppercase tracking-wider text-cyan-600 dark:text-cyan-400 bg-cyan-100 dark:bg-cyan-950/80 px-2 py-0.5 rounded-md">
                  {isHi ? "सप्त-नाड़ी चक्र (Sapta Nadi)" : "Sapta-Nadi Channel"}
                </span>
                <span className="text-xs font-bold text-slate-500">
                  {isHi ? `स्वामी: ${details.ruler}` : `Ruler: ${details.ruler}`}
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black mt-1 text-slate-900 dark:text-white">
                {isHi ? details.hindiName : details.name}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Tagline */}
        <div className="mt-4 p-3.5 bg-cyan-50/60 dark:bg-cyan-950/30 border border-cyan-100 dark:border-cyan-900/50 rounded-2xl text-xs font-semibold text-cyan-900 dark:text-cyan-200 flex items-center gap-2">
          <span>💡</span>
          <span>{isHi ? details.taglineHi : details.tagline}</span>
        </div>

        {/* Content Sections */}
        <div className="mt-5 space-y-4 text-xs">
          {/* Section 1: Personal & Health Impact */}
          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
            <h3 className="font-bold text-sm text-slate-900 dark:text-amber-400 flex items-center gap-2 mb-2.5">
              <span>👤</span>
              <span>{isHi ? "व्यक्तिगत व स्वास्थ्य प्रभाव (Personal Health & Mindset)" : "Personal Health, Physiology & Cognition"}</span>
            </h3>
            <div className="space-y-2.5 text-slate-700 dark:text-slate-300 leading-relaxed">
              <p>
                <strong className="text-slate-900 dark:text-white font-semibold">
                  {isHi ? "शारीरिक संवेदनशीलता:" : "Biological & Dosha Tendency:"}
                </strong>{" "}
                {isHi ? details.personalImpact.healthHi : details.personalImpact.health}
              </p>
              <p>
                <strong className="text-slate-900 dark:text-white font-semibold">
                  {isHi ? "मनोस्थिति व विचार:" : "Cognition & Thought Dynamics:"}
                </strong>{" "}
                {isHi ? details.personalImpact.psychologyHi : details.personalImpact.psychology}
              </p>
              <p>
                <strong className="text-slate-900 dark:text-white font-semibold">
                  {isHi ? "कार्य व आजीविका शैली:" : "Action & Strategic Style:"}
                </strong>{" "}
                {isHi ? details.personalImpact.careerHi : details.personalImpact.career}
              </p>
            </div>
          </div>

          {/* Section 2: Actionable Do's & Don'ts */}
          <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
            <h3 className="font-bold text-sm text-slate-900 dark:text-emerald-400 flex items-center gap-2 mb-2.5">
              <span>🌿</span>
              <span>{isHi ? "व्यावहारिक सुझाव व संतुलन (Actionable Guidance)" : "Actionable Balance & Grounding Guidance"}</span>
            </h3>
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="p-3 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 rounded-xl">
                <span className="font-bold text-emerald-800 dark:text-emerald-300 block mb-1.5 flex items-center gap-1.5">
                  <span>✅</span>
                  <span>{isHi ? "क्या करें (Do's):" : "Recommended Actions (Do's):"}</span>
                </span>
                <ul className="space-y-1.5 text-slate-700 dark:text-slate-300">
                  {(isHi ? details.actionableGuidance.dosHi : details.actionableGuidance.dos).map((item, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-3 bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/40 rounded-xl">
                <span className="font-bold text-rose-800 dark:text-rose-300 block mb-1.5 flex items-center gap-1.5">
                  <span>⚠️</span>
                  <span>{isHi ? "किससे बचें (Don'ts):" : "Cautions & Pitfalls (Don'ts):"}</span>
                </span>
                <ul className="space-y-1.5 text-slate-700 dark:text-slate-300">
                  {(isHi ? details.actionableGuidance.dontsHi : details.actionableGuidance.donts).map((item, idx) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <span className="text-rose-500 font-bold">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-950 font-bold rounded-xl text-xs hover:opacity-90 transition shadow-md cursor-pointer"
          >
            {isHi ? "समझ गया (Close)" : "Understood (Close)"}
          </button>
        </div>
      </div>
    </div>
  );
};
