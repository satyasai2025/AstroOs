"""
AstroOS — KP Cuspal Sub-Lord Decision Tree Engine (Module 19, Phase 4)

Pure mathematical implementation of:
1. 4-Tier Significator Matrix (Tiers A, B, C, D)
2. Cuspal Sub-Lord (CSL) Decision Tree with 12th-from-bhava negation/veto logic
3. Event-Specific Analysis (Career, Marriage, Finance, Health)
4. Deterministic step-by-step audit trace with zero opaque numbers.
"""

from __future__ import annotations

from typing import Any, Optional

from packages.shared.enums import Rashi

_RASHI_ORDER = [r.value.capitalize() for r in Rashi]
from apps.api.domain.kp_decision_tree import (
    KPDecisionVerdict,
    KPEventDomain,
    KPEventDecisionTreeResult,
    KPCuspalSubLordDecisionNode,
    KPTierSignificators,
)
from apps.api.services.ephemeris_wrapper import (
    longitude_to_sub_lord,
    longitude_to_sub_sub_lord,
)

# Standard Vimshottari / KP Lordship mapping
RASHI_SIGN_LORDS = {
    "Aries": "Mars", "Mesha": "Mars",
    "Taurus": "Venus", "Vrishabha": "Venus",
    "Gemini": "Mercury", "Mithuna": "Mercury",
    "Cancer": "Moon", "Karka": "Moon", "Karkataka": "Moon",
    "Leo": "Sun", "Simha": "Sun",
    "Virgo": "Mercury", "Kanya": "Mercury",
    "Libra": "Venus", "Tula": "Venus",
    "Scorpio": "Mars", "Vrischika": "Mars", "Vrishchika": "Mars",
    "Sagittarius": "Jupiter", "Dhanu": "Jupiter", "Dhanus": "Jupiter",
    "Capricorn": "Saturn", "Makara": "Saturn",
    "Aquarius": "Saturn", "Kumbha": "Saturn",
    "Pisces": "Jupiter", "Meena": "Jupiter",
}

# 27 Nakshatras and their Vimshottari / KP Star Lords
NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Event domain rules (Primary, Supporting, Negating houses)
EVENT_RULES = {
    KPEventDomain.CAREER: {
        "primary_cusp": 10,
        "supporting_cusps": [2, 6, 11],
        "negating_cusps": [9, 5, 1],  # 12th from 10, 6, 2
        "label": "Career / Professional Elevation",
    },
    KPEventDomain.MARRIAGE: {
        "primary_cusp": 7,
        "supporting_cusps": [2, 11],
        "negating_cusps": [6, 1, 10, 12],  # 6th (12th from 7), 1st (12th from 2), 10th (12th from 11)
        "label": "Marriage / Partnership Realization",
    },
    KPEventDomain.FINANCE: {
        "primary_cusp": 2,
        "supporting_cusps": [6, 10, 11],
        "negating_cusps": [12, 1, 5, 8],  # 12th (12th from 1), 1st (12th from 2), 5th (12th from 6)
        "label": "Financial Inflow & Asset Accumulation",
    },
    KPEventDomain.HEALTH: {
        "primary_cusp": 6,
        "supporting_cusps": [8, 12],
        "negating_cusps": [1, 5, 11],  # 1, 5, 11 represent cure and vitality recovery
        "label": "Health Vulnerability vs Recovery",
    },
}


class KPDecisionTreeEngine:
    """
    Stateless evaluator for KP 4-Tier Significators and Cuspal Sub-Lord Decision Trees.
    """

    def compute_four_tier_matrix(self, chart_data: dict[str, Any]) -> list[KPTierSignificators]:
        """
        Computes the complete 4-tier significator matrix for all 12 houses.
        """
        planets = chart_data.get("planets", [])
        houses = chart_data.get("houses", [])
        
        # Build lookup maps
        # 1. House occupants (planet.house_number)
        house_occupants: dict[int, list[str]] = {h: [] for h in range(1, 13)}
        planet_star_lords: dict[str, str] = {}
        planet_houses: dict[str, int] = {}
        
        for p in planets:
            p_name = p.get("planet", "")
            h_num = int(p.get("house_number", 1))
            st_lord = p.get("nakshatra_lord") or p.get("star_lord", "")
            if not st_lord:
                st_lord = self._guess_star_lord(p.get("sidereal_longitude", 0.0))
            planet_star_lords[p_name] = st_lord
            planet_houses[p_name] = h_num
            if 1 <= h_num <= 12:
                house_occupants[h_num].append(p_name)

        # 2. House Sign Lords
        lagna_h = next((h for h in houses if int(h.get("house_number", 0)) == 1), None)
        lagna_rashi = lagna_h.get("rashi") if lagna_h else None
        lagna_rashi_idx = _RASHI_ORDER.index(lagna_rashi) if lagna_rashi in _RASHI_ORDER else None

        house_sign_lords: dict[int, str] = {}
        for h_idx in range(1, 13):
            # Check if explicit in houses list
            matched_h = next((h for h in houses if int(h.get("house_number", 0)) == h_idx), None)
            if matched_h and matched_h.get("sign_lord"):
                house_sign_lords[h_idx] = matched_h["sign_lord"]
            elif matched_h and matched_h.get("rashi"):
                house_sign_lords[h_idx] = RASHI_SIGN_LORDS.get(matched_h["rashi"], "Mars")
            elif lagna_rashi_idx is not None:
                # Whole-sign house rashi, counted forward from the real Lagna rashi
                rashi = _RASHI_ORDER[(lagna_rashi_idx + h_idx - 1) % 12]
                house_sign_lords[h_idx] = RASHI_SIGN_LORDS.get(rashi, "Mars")
            else:
                # No Lagna data available either — cannot derive a real sign
                # lord. Previously this silently defaulted to "Jupiter" for
                # every unmatched house, fabricating a plausible-looking
                # verdict; None makes the gap visible to callers instead.
                house_sign_lords[h_idx] = None

        matrix: list[KPTierSignificators] = []

        for h_num in range(1, 13):
            occupants = house_occupants.get(h_num, [])
            sign_lord = house_sign_lords.get(h_num, "Jupiter")

            # Tier A: Planets in the Star of a Planet Occupying the House (Strongest)
            tier_a: list[str] = []
            for p_name, st_lord in planet_star_lords.items():
                if st_lord in occupants:
                    tier_a.append(p_name)

            # Tier B: Planet Occupying the House
            tier_b = list(occupants)

            # Tier C: Planets in the Star of the House Sign Lord
            tier_c: list[str] = []
            for p_name, st_lord in planet_star_lords.items():
                if st_lord == sign_lord and p_name not in tier_a and p_name not in tier_b:
                    tier_c.append(p_name)

            # Tier D: House Sign Lord
            tier_d = [sign_lord] if sign_lord else []

            matrix.append(
                KPTierSignificators(
                    house_number=h_num,
                    tier_a_planets=sorted(list(set(tier_a))),
                    tier_b_planets=sorted(list(set(tier_b))),
                    tier_c_planets=sorted(list(set(tier_c))),
                    tier_d_planets=sorted(list(set(tier_d))),
                )
            )

        return matrix

    def compute_cuspal_decision_nodes(
        self,
        chart_data: dict[str, Any],
        house_numbers: Optional[list[int]] = None,
    ) -> list[KPCuspalSubLordDecisionNode]:
        """
        Evaluates Cuspal Sub-Lord decision nodes for selected (or all 12) cusps.
        """
        four_tier = self.compute_four_tier_matrix(chart_data)
        four_tier_map = {item.house_number: item for item in four_tier}
        houses = chart_data.get("houses", [])
        planets = chart_data.get("planets", [])
        planet_star_lords = {
            p.get("planet", ""): (p.get("nakshatra_lord") or p.get("star_lord") or self._guess_star_lord(p.get("sidereal_longitude", 0.0)))
            for p in planets
        }

        target_houses = house_numbers if house_numbers else list(range(1, 13))
        nodes: list[KPCuspalSubLordDecisionNode] = []

        for h_num in target_houses:
            matched_h = next((h for h in houses if int(h.get("house_number", 0)) == h_num), None) or {}
            cusp_deg = float(matched_h.get("longitude", (h_num - 1) * 30.0 + 15.0))
            cusp_rashi = matched_h.get("rashi", "Aries")
            sign_lord = matched_h.get("sign_lord") or RASHI_SIGN_LORDS.get(cusp_rashi, "Mars")
            star_lord = matched_h.get("star_lord") or self._guess_star_lord(cusp_deg)
            # Real 249-division KP Sub-Lord / Sub-Sub-Lord, computed from the
            # cusp's own sidereal longitude rather than a hardcoded fallback
            # planet — the verdict below hinges entirely on sub_lord, so a
            # fabricated value here would silently fabricate the verdict too.
            sub_lord = matched_h.get("sub_lord") or longitude_to_sub_lord(cusp_deg).capitalize()
            sub_sub_lord = matched_h.get("sub_sub_lord") or longitude_to_sub_sub_lord(cusp_deg).capitalize()
            sub_star = planet_star_lords.get(sub_lord, "Mercury")

            # Calculate houses signified by the Sub-Lord
            signified_houses = self._get_houses_signified_by_planet(sub_lord, four_tier)
            sub_star_signified = self._get_houses_signified_by_planet(sub_star, four_tier)
            combined_signified = sorted(list(set(signified_houses + sub_star_signified)))

            # Check for primary, supporting, and negating houses
            negating_h = ((h_num - 2) % 12) + 1  # 12th from this house
            is_veto = negating_h in combined_signified

            primary_list = [h_num] if h_num in combined_signified else []
            supporting_list = [h for h in combined_signified if h != h_num and h != negating_h]
            negating_list = [negating_h] if is_veto else []

            # Verdict derivation
            audit: list[str] = [
                f"Cusp {h_num} Longitude: {cusp_deg:.2f}° in {cusp_rashi}.",
                f"Sign Lord: {sign_lord} | Star Lord: {star_lord} | Sub-Lord: {sub_lord} (Star: {sub_star}).",
                f"Sub-Lord {sub_lord} and Star {sub_star} signify Houses: {combined_signified}.",
            ]

            if h_num in combined_signified and not is_veto:
                verdict = KPDecisionVerdict.PROMISED_FRUCTIFY
                explanation = f"Cuspal Sub-Lord {sub_lord} strongly supports House {h_num} through its Star Lord {sub_star} without 12th-house negation."
                audit.append(f"Verdict: {verdict.value} -> Positive fructification promised.")
            elif is_veto:
                verdict = KPDecisionVerdict.VETOED_NEGATED
                explanation = f"Cuspal Sub-Lord {sub_lord} connects to House {negating_h} (12th from {h_num}), creating an active negation veto."
                audit.append(f"Verdict: {verdict.value} -> Negation veto active via House {negating_h}.")
            elif len(supporting_list) >= 2:
                verdict = KPDecisionVerdict.DELAYED_MODERATE
                explanation = f"Cuspal Sub-Lord {sub_lord} signifies supporting houses {supporting_list} but lacks direct primary anchor {h_num}."
                audit.append(f"Verdict: {verdict.value} -> Moderate manifestation with delay.")
            else:
                verdict = KPDecisionVerdict.DENIED
                explanation = f"Cuspal Sub-Lord {sub_lord} does not signify House {h_num} or its supportive harmonic groupings."
                audit.append(f"Verdict: {verdict.value} -> Matter denied by Cuspal Sub-Lord.")

            nodes.append(
                KPCuspalSubLordDecisionNode(
                    house_number=h_num,
                    cusp_degree=cusp_deg,
                    cusp_rashi=cusp_rashi,
                    sign_lord=sign_lord,
                    star_lord=star_lord,
                    sub_lord=sub_lord,
                    sub_sub_lord=sub_sub_lord,
                    sub_lord_star_lord=sub_star,
                    primary_houses_signified=primary_list,
                    supporting_houses_signified=supporting_list,
                    negating_houses_signified=negating_list,
                    is_veto_active=is_veto,
                    verdict=verdict,
                    verdict_explanation=explanation,
                    audit_chain=audit,
                )
            )

        return nodes

    def compute_event_decision_trees(
        self,
        chart_data: dict[str, Any],
        event_domain: Optional[str] = None,
    ) -> list[KPEventDecisionTreeResult]:
        """
        Computes event-specific KP decision trees for Career, Marriage, Finance, and Health.
        """
        nodes = self.compute_cuspal_decision_nodes(chart_data)
        node_map = {n.house_number: n for n in nodes}
        four_tier = self.compute_four_tier_matrix(chart_data)

        target_domains = [KPEventDomain(event_domain)] if (event_domain and event_domain.lower() != "all" and event_domain in [d.value for d in KPEventDomain]) else [
            KPEventDomain.CAREER,
            KPEventDomain.MARRIAGE,
            KPEventDomain.FINANCE,
            KPEventDomain.HEALTH,
        ]

        results: list[KPEventDecisionTreeResult] = []

        for domain in target_domains:
            rule = EVENT_RULES[domain]
            primary_c = rule["primary_cusp"]
            supporting_cs = rule["supporting_cusps"]
            negating_cs = rule["negating_cusps"]

            cusp_node = node_map.get(primary_c)
            if not cusp_node:
                continue

            # Gather strong supporting significators
            supp_significators: list[str] = []
            for h in supporting_cs:
                tier_item = next((t for t in four_tier if t.house_number == h), None)
                if tier_item:
                    supp_significators.extend(tier_item.tier_a_planets + tier_item.tier_b_planets)
            supp_significators = sorted(list(set(supp_significators)))

            # Ruling planets agreement: real Ascendant sign/star lord + Moon
            # sign/star lord, derived from this chart's own data. Day Lord
            # is classically the 5th RP but is omitted here — chart_data
            # passed into this engine carries no datetime/weekday field to
            # derive it from, so it is left out rather than guessed.
            ruling_planets = self._compute_ruling_planets(chart_data, node_map)

            calc_steps: list[str] = [
                f"Step 1 (Root Cusp): Inspected Cusp {primary_c} ({rule['label']}).",
                f"Step 2 (CSL & Star-Lord): Sub-Lord is {cusp_node.sub_lord}, whose Star-Lord is {cusp_node.sub_lord_star_lord}.",
                f"Step 3 (House Grouping Signification): Evaluated Primary ({primary_c}), Supporting ({supporting_cs}), and Negating ({negating_cs}) houses.",
            ]

            if cusp_node.is_veto_active:
                fruct_verdict = KPDecisionVerdict.VETOED_NEGATED
                summary = f"{domain.value} matter experiences active veto/negation via Cuspal Sub-Lord {cusp_node.sub_lord}."
                calc_steps.append(f"Step 4 (Veto Check): VETO TRIGGERED -> Negating houses {cusp_node.negating_houses_signified} active.")
            elif cusp_node.verdict == KPDecisionVerdict.PROMISED_FRUCTIFY:
                fruct_verdict = KPDecisionVerdict.PROMISED_FRUCTIFY
                summary = f"{domain.value} matter is firmly promised by Cuspal Sub-Lord {cusp_node.sub_lord}."
                calc_steps.append("Step 4 (Promise Check): Event is firmly promised by primary & supporting significations.")
            elif len(supp_significators) >= 2:
                fruct_verdict = KPDecisionVerdict.DELAYED_MODERATE
                summary = f"{domain.value} matter has supportive significations but requires Dasha/Transit trigger synchronization."
                calc_steps.append("Step 4 (Support Check): Supporting houses active; moderate manifestation expected.")
            else:
                fruct_verdict = KPDecisionVerdict.DENIED
                summary = f"{domain.value} matter is not supported by Cuspal Sub-Lord alignment."
                calc_steps.append("Step 4 (Denial Check): Insufficient harmonic significator support.")

            calc_steps.append(f"Step 5 (Final KP Verdict): {fruct_verdict.value} -> {summary}")

            results.append(
                KPEventDecisionTreeResult(
                    event_domain=domain,
                    primary_cusp=primary_c,
                    supporting_cusps=supporting_cs,
                    negating_cusps=negating_cs,
                    cusp_node=cusp_node,
                    supporting_significators=supp_significators,
                    ruling_planets_agreement=ruling_planets,
                    fructification_verdict=fruct_verdict,
                    summary_verdict=summary,
                    technical_calculation_steps=calc_steps,
                )
            )

        return results

    def _get_houses_signified_by_planet(
        self,
        planet_name: str,
        four_tier_matrix: list[KPTierSignificators],
    ) -> list[int]:
        signified: list[int] = []
        for item in four_tier_matrix:
            if (
                planet_name in item.tier_a_planets
                or planet_name in item.tier_b_planets
                or planet_name in item.tier_c_planets
                or planet_name in item.tier_d_planets
            ):
                signified.append(item.house_number)
        return sorted(list(set(signified)))

    def _compute_ruling_planets(
        self,
        chart_data: dict[str, Any],
        node_map: dict[int, KPCuspalSubLordDecisionNode],
    ) -> list[str]:
        """Real Ascendant sign/star lord + Moon sign/star lord, deduplicated. See caller's comment on Day Lord's omission."""
        ruling: list[str] = []

        lagna_node = node_map.get(1)
        if lagna_node:
            ruling.append(lagna_node.sign_lord)
            ruling.append(lagna_node.star_lord)

        moon = next(
            (p for p in chart_data.get("planets", []) if p.get("planet", "").lower() == "moon"),
            None,
        )
        if moon:
            moon_lon = float(moon.get("sidereal_longitude", 0.0))
            moon_rashi = moon.get("rashi") or _RASHI_ORDER[int((moon_lon % 360.0) // 30.0)]
            ruling.append(RASHI_SIGN_LORDS.get(moon_rashi, "Mars"))
            moon_star_lord = moon.get("nakshatra_lord") or moon.get("star_lord") or self._guess_star_lord(moon_lon)
            ruling.append(moon_star_lord)

        return sorted({r for r in ruling if r})

    def _guess_star_lord(self, longitude_deg: float) -> str:
        # 360 / 27 = 13.3333 degrees per nakshatra
        idx = int((longitude_deg % 360.0) / (360.0 / 27.0))
        return NAKSHATRA_LORDS[idx % 27]
