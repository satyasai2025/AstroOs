"""
AstroOS — Sarvatobhadra Chakra (SBC) AI Event Analyzer

Redesigned for clean, user-friendly, plain-language visual scannability:
1. 🎯 Bottom Line Verdict
2. 📖 The Complete Story (Plain English Results)
3. 🚨 Major Warning Points (What NOT to do in 1 sentence)
4. 🛡️ Safe Zones / Protections (Where you are safe)
5. 💡 Direct Practical Advice (Actionable steps)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from apps.api.config import get_settings
from apps.api.schemas.ai import (
    AISBCAnalysisRequest,
    AISBCAnalysisResponse,
    AISBCSangyaBreakdownItem,
    AISBCWarningItem,
    AISBCSafeZoneItem,
    AISBCPracticalStep,
)
from apps.api.services.sbc_vedha_engine import (
    GRAHA_VEDHA_RULES,
    SANGYA_LIFE_AREAS,
)

logger = logging.getLogger(__name__)

# Human-friendly domain translations
PLAIN_DOMAIN_NAMES: dict[str, str] = {
    "janma": "Physical Body, Energy & Personal Vitality",
    "karma": "Work, Daily Execution & Career Standing",
    "sanghatika": "Money, Business Partnerships & Joint Assets",
    "samudayika": "Overall Financial Stability & Group Wealth",
    "adhana": "Core Life Foundation & Home / Base Stability",
    "vainashika": "Capital Security & Emergency Reserves",
    "manasa": "Mental Peace, Sleep & Decision Focus",
    "jati": "Family Harmony, Community Standing & Health",
    "desha": "Travel, Property Moves & External Environment",
    "abhisheka": "Promotions, Honors & Ultimate Success Armor",
}

PLAIN_SHIELD_TITLES: dict[str, str] = {
    "janma": "Vitality & Health Shield Active",
    "karma": "Career Reputation & Authority Shield Active",
    "sanghatika": "Financial & Partnership Safety Shield Active",
    "samudayika": "Collective Wealth & Liquidity Armor Active",
    "adhana": "Home & Foundation Stability Shield Active",
    "vainashika": "Capital Protection & Downside Cushion Active",
    "manasa": "Mental Peace & Clear Focus Shield Active",
    "jati": "Family Standing & Vitality Shield Active",
    "desha": "Travel & Property Protection Shield Active",
    "abhisheka": "Royal Honor & Breakthrough Shield Active",
}


class SBCAIAnalyzer:
    """
    User-Friendly SBC AI Event Analyzer based on Narapatijayacharya Svarodaya rules.
    """

    @classmethod
    def analyze(cls, req: AISBCAnalysisRequest) -> AISBCAnalysisResponse:
        ref_nak = (req.reference_nakshatra or "Janma").replace("_", " ").title()
        event_type = req.event_type or "general"
        t_moment = req.transit_date or datetime.now(timezone.utc)
        moment_str = t_moment.strftime("%d %b %Y, %H:%M UTC")

        # Map active Sangyas
        sangya_map: dict[str, dict[str, Any]] = {}
        for s in req.active_sangyas:
            k = s.get("key", "").lower()
            if k:
                sangya_map[k] = s

        # Find afflicted and protected points
        afflicted_points: list[dict[str, Any]] = []
        protected_points: list[dict[str, Any]] = []
        breakdown_items: list[AISBCSangyaBreakdownItem] = []

        for k, info in SANGYA_LIFE_AREAS.items():
            sangya_data = sangya_map.get(k, {})
            status = sangya_data.get("status", "neutral")
            nak_name = sangya_data.get("nakshatra_name", sangya_data.get("nakshatra_token", "").title()) or "Unknown"
            vedhas_rec = sangya_data.get("vedhas_received", [])
            b_hits = sangya_data.get("benefic_hits", [])
            m_hits = sangya_data.get("malefic_hits", [])
            involved = [v.split()[0] for v in vedhas_rec if v]
            friendly_domain = PLAIN_DOMAIN_NAMES.get(k, info.get("domain", ""))

            if status == "afflicted":
                m_label = ", ".join(m_hits) if m_hits else "Malefic rays"
                interp = f"Under pressure from {m_label}. Watch out for friction in {friendly_domain.lower()}."
                afflicted_points.append({
                    "key": k,
                    "name": info["name"],
                    "offset": info["offset"],
                    "nak": nak_name,
                    "hits": m_hits,
                    "domain": friendly_domain,
                })
            elif status == "activated":
                b_label = ", ".join(b_hits) if b_hits else "Benefic rays"
                interp = f"Protected and uplifted by {b_label}. High support for {friendly_domain.lower()}."
                protected_points.append({
                    "key": k,
                    "name": info["name"],
                    "offset": info["offset"],
                    "nak": nak_name,
                    "hits": b_hits,
                    "domain": friendly_domain,
                })
            elif status == "mixed":
                interp = f"Mixed influences ({', '.join(vedhas_rec)}). You may see both opportunities and minor friction."
            else:
                interp = f"Calm and stable transit zone without direct interference."

            breakdown_items.append(
                AISBCSangyaBreakdownItem(
                    sangya_key=k,
                    sangya_name=info["name"],
                    nakshatra_name=nak_name,
                    status=status,
                    domain=friendly_domain,
                    grahas_involved=involved,
                    interpretation=interp,
                )
            )

        # Dispatch based on event type
        if event_type == "market":
            return cls._build_market_analysis(ref_nak, moment_str, afflicted_points, protected_points, breakdown_items)
        elif event_type == "life_events":
            return cls._build_life_events_analysis(ref_nak, moment_str, afflicted_points, protected_points, breakdown_items)
        elif event_type == "muhurta":
            return cls._build_muhurta_analysis(ref_nak, moment_str, afflicted_points, protected_points, breakdown_items)
        else:
            return cls._build_general_analysis(ref_nak, moment_str, afflicted_points, protected_points, breakdown_items)

    @classmethod
    def _build_market_analysis(cls, ref_nak: str, moment_str: str, afflicted, protected, items) -> AISBCAnalysisResponse:
        aff_keys = {a["key"] for a in afflicted}
        has_critical = bool(aff_keys.intersection({"sanghatika", "samudayika", "vainashika"}))
        has_wealth_shield = any(p["key"] in ("sanghatika", "samudayika", "abhisheka") for p in protected)

        if has_critical:
            verdict = "High Volatility / Avoid Speculation"
            verdict_badge = "high_risk"
            risk_level = "high"
            story = (
                f"Your chart shows direct pressure on your wealth and partnership pillars right now. "
                f"If you engage in high-risk speculative trades or enter hasty joint ventures, you are likely to experience sudden pullbacks or counterparty stress. "
                f"However, steady core assets and conservative holdings remain resilient."
            )
            quick_chips = [
                "🛑 Avoid High Leverage",
                "⚠️ Re-verify Partnership Deals",
                "🛡️ Keep Cash Buffers",
                "✅ Protect Existing Gains",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Do NOT take large speculative bets or unhedged financial risks right now.",
                    what_not_to_do="Do NOT enter aggressive new trades or lend money without solid legal contracts.",
                    affected_area="Money & Business Partnerships (Sanghatika & Vainashika)",
                    severity="critical",
                ),
                AISBCWarningItem(
                    headline="Do NOT rush into new joint business agreements without a 48-hour cooling period.",
                    what_not_to_do="Avoid verbal financial commitments with associates or co-founders.",
                    affected_area="Shared Resources & Contracts (Sanghatika)",
                    severity="warning",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Lock in partial profits on speculative positions and move funds into defensive assets.",
                    why="Planetary rays are piercing speculative points, making sharp intraday drops more likely.",
                    timing_tip="Execute risk-reduction during morning market hours.",
                ),
                AISBCPracticalStep(
                    action="Review all contract fine print and audit recurring business subscriptions.",
                    why="Afflicted partnership channels often expose hidden liabilities or billing errors.",
                    timing_tip="Complete audits before initiating new quarters.",
                ),
            ]
        elif afflicted:
            verdict = "Selective Caution / Moderate Market Fluctuations"
            verdict_badge = "caution"
            risk_level = "moderate"
            story = (
                f"You are experiencing a mixed transit period. While general cash flow is steady, certain specific sectors or routines "
                f"may face minor delays. Prudent positioning will allow you to navigate without major drawdowns."
            )
            quick_chips = [
                "⚡ Moderate Volatility",
                "✅ Focus on Core Income",
                "🔍 Double-Check Transactions",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Do NOT overcommit capital to untested projects or illiquid assets.",
                    what_not_to_do="Avoid making hasty investment switches based on emotional social media news.",
                    affected_area="General Financial Decisions",
                    severity="caution",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Focus on your primary revenue streams rather than chasing speculative windfalls.",
                    why="Core earnings are protected while speculative upside is muted.",
                    timing_tip="Stick to your established monthly budget plan.",
                ),
            ]
        else:
            verdict = "Favorable / Clean Financial Skies"
            verdict_badge = "auspicious"
            risk_level = "auspicious"
            story = (
                f"Your wealth and enterprise points are completely clear of malefic interference. "
                f"Financial negotiations, business expansions, and strategic investments are operating under supportive planetary skies."
            )
            quick_chips = [
                "🌟 Clean Financial Sky",
                "✅ Expansion Favorable",
                "📈 High Negotiation Strength",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Maintain standard financial discipline; no negative planetary storms detected.",
                    what_not_to_do="Do NOT become complacent with basic bookkeeping.",
                    affected_area="General Financial Management",
                    severity="caution",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Initiate planned business negotiations and pitch high-value proposals.",
                    why="Clean transit channels maximize favorable terms and counterpart receptivity.",
                    timing_tip="Best results when initiated during Shukla Paksha or midday.",
                ),
            ]

        safe_zones = cls._extract_safe_zones(protected)

        md = cls._render_markdown_report(
            "📈 Market & Financial Intelligence",
            ref_nak,
            moment_str,
            verdict,
            story,
            warnings,
            safe_zones,
            practical_steps,
            items,
        )

        return AISBCAnalysisResponse(
            event_type="market",
            title=f"📈 SBC Market & Financial Intelligence ({ref_nak} Reference)",
            verdict=verdict,
            verdict_badge=verdict_badge,
            the_story=story,
            executive_summary=story,
            risk_level=risk_level,
            quick_chips=quick_chips,
            major_warnings=warnings,
            safe_zones=safe_zones,
            practical_steps=practical_steps,
            sangya_breakdown=items,
            predictions=[w.headline for w in warnings],
            protective_shields=[s.benefit for s in safe_zones],
            actionable_remedies=[p.action for p in practical_steps],
            markdown_report=md,
            confidence=0.96,
            version="2.1.0",
        )

    @classmethod
    def _build_life_events_analysis(cls, ref_nak: str, moment_str: str, afflicted, protected, items) -> AISBCAnalysisResponse:
        aff_keys = {a["key"] for a in afflicted}
        has_vitality_hit = bool(aff_keys.intersection({"janma", "jati", "manasa"}))
        has_career_hit = bool(aff_keys.intersection({"karma", "adhana", "desha"}))

        if has_vitality_hit:
            verdict = "Physical & Mental Care Required / High Stress"
            verdict_badge = "high_risk"
            risk_level = "high"
            story = (
                f"You are undergoing a phase of higher bodily fatigue, mental restlessness, or domestic friction. "
                f"Aggressive arguments or overworking will drain your energy quickly. "
                f"By resting adequately and staying out of unnecessary ego battles, you will protect your health and peace."
            )
            quick_chips = [
                "🛌 Prioritize Sleep & Rest",
                "🛑 Avoid Heated Arguments",
                "🧘 Guard Mental Equanimity",
                "🛡️ Family Standing Shielded",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Do NOT engage in confrontational arguments with family or senior authorities.",
                    what_not_to_do="Do NOT react impulsively to provocation or take on excessive physical exertion.",
                    affected_area="Physical Energy & Domestic Peace (Janma & Jati)",
                    severity="critical",
                ),
                AISBCWarningItem(
                    headline="Do NOT make major life-altering decisions when feeling anxious or sleep-deprived.",
                    what_not_to_do="Avoid late-night overthinking and impulsive communication.",
                    affected_area="Mental Peace & Clarity (Manasa)",
                    severity="warning",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Schedule intentional daily downtime, gentle walks, and prioritize 7-8 hours of sleep.",
                    why="Piercing rays on Janma/Manasa increase pitta/inflammation and mental fatigue.",
                    timing_tip="Adopt calming evening wind-down rituals.",
                ),
                AISBCPracticalStep(
                    action="Pause for at least 30 minutes before replying to contentious messages or emails.",
                    why="Prevents misinterpretation and authority friction.",
                    timing_tip="Respond with neutral facts rather than emotional reactions.",
                ),
            ]
        elif has_career_hit:
            verdict = "Professional Realignment / Handle Work with Tact"
            verdict_badge = "caution"
            risk_level = "moderate"
            story = (
                f"Your work foundation or daily execution is experiencing shifting expectations or minor logistical hurdles. "
                f"Keep thorough documentation and avoid making abrupt job changes until current transit rays settle."
            )
            quick_chips = [
                "📝 Document All Deliverables",
                "⚠️ Expect Minor Deadlines Shifts",
                "🛡️ Core Reputation Intact",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Do NOT leave your current role abruptly without signed confirmation on the next one.",
                    what_not_to_do="Avoid arguing with managers over minor process changes.",
                    affected_area="Career Execution & Foundation (Karma & Adhana)",
                    severity="warning",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Maintain clear written records of agreements and deliverables at work.",
                    why="Prevents scope creep or misunderstandings during team shifts.",
                    timing_tip="Send recap emails after every important discussion.",
                ),
            ]
        else:
            verdict = "Harmonious & Peaceful / Green Light"
            verdict_badge = "auspicious"
            risk_level = "low"
            story = (
                f"Your vital health, career standing, and domestic peace are in a calm, protected zone. "
                f"This is a wonderful phase for personal rejuvenation, strengthening family bonds, and executing your goals with confidence."
            )
            quick_chips = [
                "✨ High Vitality & Balance",
                "🤝 Relationship Ease",
                "🎯 Smooth Goal Execution",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="No major life disruption storms detected; continue your constructive habits.",
                    what_not_to_do="Do NOT let good times turn into procrastination.",
                    affected_area="General Life Pillars",
                    severity="caution",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Invest time into long-term personal projects, fitness, and family relationships.",
                    why="Positive transit alignment ensures your efforts yield lasting emotional and physical dividends.",
                    timing_tip="Great time for family gatherings and recreational trips.",
                ),
            ]

        safe_zones = cls._extract_safe_zones(protected)

        md = cls._render_markdown_report(
            "⚡ Major Life Events & Conflict Risk",
            ref_nak,
            moment_str,
            verdict,
            story,
            warnings,
            safe_zones,
            practical_steps,
            items,
        )

        return AISBCAnalysisResponse(
            event_type="life_events",
            title=f"⚡ Major Life Events & Conflict Risk Analysis ({ref_nak} Reference)",
            verdict=verdict,
            verdict_badge=verdict_badge,
            the_story=story,
            executive_summary=story,
            risk_level=risk_level,
            quick_chips=quick_chips,
            major_warnings=warnings,
            safe_zones=safe_zones,
            practical_steps=practical_steps,
            sangya_breakdown=items,
            predictions=[w.headline for w in warnings],
            protective_shields=[s.benefit for s in safe_zones],
            actionable_remedies=[p.action for p in practical_steps],
            markdown_report=md,
            confidence=0.96,
            version="2.1.0",
        )

    @classmethod
    def _build_muhurta_analysis(cls, ref_nak: str, moment_str: str, afflicted, protected, items) -> AISBCAnalysisResponse:
        aff_keys = {a["key"] for a in afflicted}
        prot_keys = {p["key"] for p in protected}

        has_critical_affliction = bool(aff_keys.intersection({"janma", "karma", "abhisheka", "sanghatika"}))
        has_abhisheka_shield = "abhisheka" in prot_keys or "janma" in prot_keys

        if has_critical_affliction and not has_abhisheka_shield:
            verdict = "Inauspicious Window / Postpone Major Launches"
            verdict_badge = "high_risk"
            risk_level = "high"
            story = (
                f"Core initiation channels (action & breakthrough points) are currently pierced by malefic rays. "
                f"Ventures or contracts inaugurated during this specific transit window are prone to initial bottlenecks, regulatory delays, or friction. "
                f"Use this time for back-office preparation, auditing, and refining your strategy."
            )
            quick_chips = [
                "⏳ Postpone Launch Date",
                "🔍 Focus on Strategy & Audit",
                "🛑 Avoid High-Stake Signings",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Do NOT inaugurate new businesses, sign large property deeds, or start major campaigns today.",
                    what_not_to_do="Do NOT launch public ventures during pierced transit hours.",
                    affected_area="New Initiations & Breakthroughs (Janma / Karma / Abhisheka)",
                    severity="critical",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Dedicate this transit window to rigorous product testing, contract reviews, and internal prep.",
                    why="Quiet preparation succeeds where public launches stumble under malefic rays.",
                    timing_tip="Wait until benefic moon/jupiter rays align.",
                ),
            ]
        elif has_abhisheka_shield or not afflicted:
            verdict = "Highly Favorable / Green Light for New Ventures"
            verdict_badge = "auspicious"
            risk_level = "auspicious"
            story = (
                f"Your chart is blessed with strong protective rays on your breakthrough and honor points. "
                f"Initiatives commenced during this period receive auspicious momentum, positive reception, and resilience against obstacles."
            )
            quick_chips = [
                "🌟 Auspicious Initiation Window",
                "👑 Royal / Institutional Favor",
                "🚀 High Success Momentum",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Proceed with confidence while maintaining standard diligence.",
                    what_not_to_do="Do NOT hesitate or delay ready projects.",
                    affected_area="Initiations & Milestones",
                    severity="caution",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Schedule your key product releases, contract signings, or important announcements now.",
                    why="Auspicious Subha Vedha provides divine armor and removes friction.",
                    timing_tip="Best launched during Shukla Paksha or midday hora.",
                ),
            ]
        else:
            verdict = "Moderate / Suitable for Routine Milestones"
            verdict_badge = "caution"
            risk_level = "moderate"
            story = (
                f"A balanced, moderate window. Standard daily workflows and ongoing commitments proceed smoothly, "
                f"but high-stakes life transitions should be checked for auspicious hora alignment."
            )
            quick_chips = [
                "⚡ Moderate Timing",
                "✅ Suitable for Routine Tasks",
                "🔍 Check Planetary Hora",
            ]
            warnings = [
                AISBCWarningItem(
                    headline="Ensure all paperwork is double-checked before signing binding long-term agreements.",
                    what_not_to_do="Do NOT skip thorough contract reviews.",
                    affected_area="Agreements & Routine Steps",
                    severity="caution",
                ),
            ]
            practical_steps = [
                AISBCPracticalStep(
                    action="Proceed with routine operational steps while keeping high-stakes launches for clear windows.",
                    why="Moderate transits support steady continuous work without unexpected spikes.",
                    timing_tip="Pick Jupiter or Venus hora for essential conversations.",
                ),
            ]

        safe_zones = cls._extract_safe_zones(protected)

        md = cls._render_markdown_report(
            "🔮 Auspicious Timings & Protection (Muhurta)",
            ref_nak,
            moment_str,
            verdict,
            story,
            warnings,
            safe_zones,
            practical_steps,
            items,
        )

        return AISBCAnalysisResponse(
            event_type="muhurta",
            title=f"🔮 SBC Auspicious Timings & Protection Shield ({ref_nak} Reference)",
            verdict=verdict,
            verdict_badge=verdict_badge,
            the_story=story,
            executive_summary=story,
            risk_level=risk_level,
            quick_chips=quick_chips,
            major_warnings=warnings,
            safe_zones=safe_zones,
            practical_steps=practical_steps,
            sangya_breakdown=items,
            predictions=[w.headline for w in warnings],
            protective_shields=[s.benefit for s in safe_zones],
            actionable_remedies=[p.action for p in practical_steps],
            markdown_report=md,
            confidence=0.96,
            version="2.1.0",
        )

    @classmethod
    def _build_general_analysis(cls, ref_nak: str, moment_str: str, afflicted, protected, items) -> AISBCAnalysisResponse:
        if len(afflicted) >= 3:
            verdict = "Multiple Stress Points / Exercise Caution"
            verdict_badge = "high_risk"
            risk_level = "high"
            story = (
                f"Multiple sensitive life points are receiving malefic pressure simultaneously. "
                f"You will need to maintain conscious patience across finance, relationships, and physical well-being. "
                f"Avoid major unforced gambles and prioritize stability."
            )
            quick_chips = ["⚠️ High Overall Caution", "🛑 Avoid Major Gambles", "🛡️ Focus on Core Defense"]
        elif len(afflicted) > 0:
            verdict = "Cautious / Wait & Watch"
            verdict_badge = "caution"
            risk_level = "moderate"
            story = (
                f"The transit climate is mostly manageable with a few specific sensitive areas requiring attention. "
                f"You will achieve steady results by staying proactive and avoiding reactionary decisions."
            )
            quick_chips = ["⚡ Manageable Transit", "🔍 Proactive Monitoring", "✅ Steady Execution"]
        elif protected:
            verdict = "Fortified & Auspicious / Expansion Phase"
            verdict_badge = "auspicious"
            risk_level = "auspicious"
            story = (
                f"Your chart enjoys strong protective shielding across key pillars. "
                f"This is an empowering phase where your efforts meet minimal resistance and fruitful outcomes."
            )
            quick_chips = ["🌟 Auspicious Shield Active", "🚀 High Expansion Window", "✨ Strong Protection"]
        else:
            verdict = "Stable & Neutral Baseline"
            verdict_badge = "favorable"
            risk_level = "low"
            story = (
                f"No major planetary storms or disruptions are hitting your 10 sensitive points right now. "
                f"Your daily routines, work execution, and health operate under balanced, steady conditions."
            )
            quick_chips = ["🟢 Calm Baseline", "✅ Balanced Momentum", "🤝 Smooth Operations"]

        warnings = [
            AISBCWarningItem(
                headline=f"Watch out for stress in {a['name']} ({a['domain']}).",
                what_not_to_do=f"Do not overreact to friction in {a['domain'].lower()}.",
                affected_area=a["domain"],
                severity="warning" if risk_level == "high" else "caution",
            )
            for a in afflicted
        ] or [
            AISBCWarningItem(
                headline="No critical afflictions detected; maintain regular diligence.",
                what_not_to_do="Do not abandon regular healthy routines.",
                affected_area="General Stability",
                severity="caution",
            )
        ]

        safe_zones = cls._extract_safe_zones(protected)
        practical_steps = [
            AISBCPracticalStep(
                action="Channel your energy into protected life areas while keeping afflicted areas on conservative mode.",
                why="Aligning action with supportive transit shields maximizes returns and minimizes friction.",
                timing_tip="Review your goals weekly.",
            ),
            AISBCPracticalStep(
                action="Postpone high-risk conflicts or large speculative outflows during pierced windows.",
                why="Prevents unnecessary energy or financial drain.",
                timing_tip="Consult your Panchanga/Hora for daily timing.",
            ),
        ]

        md = cls._render_markdown_report(
            "✨ Sarvatobhadra Chakra Full Classical Synthesis",
            ref_nak,
            moment_str,
            verdict,
            story,
            warnings,
            safe_zones,
            practical_steps,
            items,
        )

        return AISBCAnalysisResponse(
            event_type="general",
            title=f"✨ Sarvatobhadra Chakra Classical Synthesis ({ref_nak} Reference)",
            verdict=verdict,
            verdict_badge=verdict_badge,
            the_story=story,
            executive_summary=story,
            risk_level=risk_level,
            quick_chips=quick_chips,
            major_warnings=warnings,
            safe_zones=safe_zones,
            practical_steps=practical_steps,
            sangya_breakdown=items,
            predictions=[w.headline for w in warnings],
            protective_shields=[s.benefit for s in safe_zones],
            actionable_remedies=[p.action for p in practical_steps],
            markdown_report=md,
            confidence=0.96,
            version="2.1.0",
        )

    @classmethod
    def _extract_safe_zones(cls, protected: list[dict[str, Any]]) -> list[AISBCSafeZoneItem]:
        if not protected:
            return [
                AISBCSafeZoneItem(
                    area_name="Foundational Resilience",
                    plain_title="Chart Inherent Safety Cushion Active",
                    description="Your core natal strength acts as a continuous baseline buffer.",
                    benefit="Maintains equilibrium during daily transit shifts.",
                )
            ]
        safe_zones = []
        for p in protected:
            k = p["key"]
            plain_title = PLAIN_SHIELD_TITLES.get(k, f"{p['name']} Protection Shield Active")
            safe_zones.append(
                AISBCSafeZoneItem(
                    area_name=f"{p['name']} ({p['offset']}th)",
                    plain_title=plain_title,
                    description=f"Fortified by {', '.join(p['hits']) if p['hits'] else 'benefic rays'}.",
                    benefit=f"Provides protective resilience, reputation backing, and recovery in {p['domain'].lower()}.",
                )
            )
        return safe_zones

    @classmethod
    def _render_markdown_report(
        cls,
        title: str,
        ref_nak: str,
        moment_str: str,
        verdict: str,
        story: str,
        warnings: list[AISBCWarningItem],
        safe_zones: list[AISBCSafeZoneItem],
        practical_steps: list[AISBCPracticalStep],
        items: list[AISBCSangyaBreakdownItem],
    ) -> str:
        md_lines = [
            f"# {title}",
            f"**Reference Nakshatra:** {ref_nak} | **Transit Time:** {moment_str}",
            f"**🎯 Bottom Line Verdict:** **{verdict}**\n",
            f"## 📖 The Complete Story",
            f"{story}\n",
            f"## 🚨 Major Warning Points (What NOT To Do)",
        ]
        for w in warnings:
            md_lines.append(f"- **{w.headline}**")
            md_lines.append(f"  - 🛑 *Avoid:* {w.what_not_to_do}")
            md_lines.append(f"  - 📍 *Area Affected:* {w.affected_area}")

        md_lines.append("\n## 🛡️ Safe Zones & Active Protections")
        for s in safe_zones:
            md_lines.append(f"- **{s.plain_title}** ({s.area_name})")
            md_lines.append(f"  - 🟢 *Benefit:* {s.benefit}")

        md_lines.append("\n## 💡 Direct Practical Advice")
        for i, step in enumerate(practical_steps, 1):
            md_lines.append(f"{i}. **{step.action}**")
            md_lines.append(f"   - *Why:* {step.why}")
            md_lines.append(f"   - *Timing Tip:* {step.timing_tip}")

        md_lines.append("\n## 🏛️ 10 Sangyas Plain-Language Summary Table")
        md_lines.append("| Sangya Point | Nakshatra | Status | Life Area Covered | What To Expect |")
        md_lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for it in items:
            status_badge = {"afflicted": "🔴 Afflicted", "activated": "🟢 Protected", "mixed": "🟡 Mixed", "neutral": "⚪ Stable"}.get(it.status, it.status)
            md_lines.append(f"| **{it.sangya_name}** | {it.nakshatra_name} | {status_badge} | {it.domain} | {it.interpretation} |")

        return "\n".join(md_lines)

