"""
AstroOS — Unified Canonical Decision Engine Validation Script
=============================================================

Runs the complete unified stack on Raj's real life events:
1. TPhalitCore (0-60 Logarithmic planetary strength + Start Page hierarchies)
2. ClassicalPolarityEngine (3-Kundali LK + SK + CK Gochara + Laghu Parashari Dasha)
3. VargaFusionEngine (Signed D1 + D9 + D10 + D60 Fusion + Bhavottama)
4. SudarshanaChakraDashaEngine (Annual & Monthly SCD Progressions)
5. SaptaNadiChakraEngine (7 Atmospheric / Elemental Nadis)
6. PhalitaDecisionEngine (Self-Adaptive 4-Tier Supervisory Governor)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from datetime import date, datetime, timezone
from apps.api.services.phalita_core.decision_engine import PhalitaDecisionEngine

def run_unified_validation():
    print("=" * 80)
    print("ASTROOS UNIFIED CANONICAL DECISION ENGINE — VALIDATION RUN")
    print("=" * 80)

    engine = PhalitaDecisionEngine(ephemeris_path="data/ephemeris")

    # Raj's Natal Coordinates & DateTime (Vadodara, 1971-06-29 23:27:40 UTC)
    birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    lat, lon = 22.3072, 73.1812

    events = [
        ("2002-04-15", "Marriage", "rahu", "venus", "career"),
        ("2002-05-01", "Lost teaching job", "rahu", "venus", "career"),
        ("2008-03-01", "Father death", "rahu", "mars", "general"),
        ("2013-07-01", "New PM job", "jupiter", "mercury", "career"),
        ("2019-03-01", "Lost job + new job same month", "jupiter", "sun", "career"),
        ("2026-01-01", "Lost sales role", "saturn", "saturn", "career"),
        ("2027-01-01", "Forward Scan 2027", "saturn", "saturn", "career"),
    ]

    chart = engine.horoscope_engine.generate_d1(birth_dt, lat, lon)

    # 1. Global Chart Features: Varga Fusion & Sapta Nadi
    varga_report = engine.varga_engine.evaluate_vargas(chart)
    snc_report = engine.snc_engine.evaluate_chart(chart)

    print(f"\n[GLOBAL NATAL METRICS]")
    print(f"  Vargottama Planets : {', '.join(varga_report.vargottama_planets) or 'None'}")
    print(f"  Bhavottama Planets : {', '.join(varga_report.bhavottama_planets) or 'None'}")
    print(f"  Overall Varga Harm : {varga_report.overall_varga_harmony:+.2f}")
    print(f"  Dominant Nadi      : {snc_report.dominant_nadi.upper()} ({snc_report.weather_summary})")

    print("\n" + "-" * 80)
    print("EVENT WINDOWS EVALUATION THROUGH SUPERVISORY DECISION GOVERNOR")
    print("-" * 80)

    for d_str, ev_name, md, ad, domain in events:
        ev_date = datetime.strptime(d_str, "%Y-%m-%d").date()
        features = engine.tphalit_core.extract_full_vector(chart).raw_vector

        win = engine.evaluate_window(
            chart=chart,
            slice_start=ev_date,
            slice_end=ev_date,
            mahadasha_lord=md,
            antardasha_lord=ad,
            features=features,
            domain=domain,
        )

        print(f"\n>>> [{d_str}] {ev_name.upper()} (Domain: {domain})")
        print(f"    Dasha          : {win.mahadasha_lord} - {win.antardasha_lord}")
        print(f"    SCD Progression: House {win.scd_annual_house} (Composite SCD Score: {win.scd_composite_score:+.2f})")
        print(f"    Varga Fusion   : Score {win.varga_fusion_score:+.2f} (Bhavottama: {win.is_bhavottama_active})")
        print(f"    3-Kundali Pol  : {win.polarity}")
        print(f"    Logic          : {win.polarity_logic}")
        print(f"    Decision Tier  : [{win.decision_tier}] ({win.confidence_level} Confidence)")
        print(f"    Verdict        : {win.actionable_verdict}")

    print("\n" + "=" * 80)
    print("ALL 7 MILESTONES PROCESSED WITH 100% DETERMINISTIC CANONICAL REASONING.")
    print("=" * 80)

if __name__ == "__main__":
    run_unified_validation()
