"""
AstroOS — Famous Case Studies Verification Runner (Supervisory Decision Layer)
==============================================================================

Verifies the PhalitaDecisionEngine on celebrated historical natal charts:
1. Narendra Modi (2014 & 2019 Election Victories)
2. Indira Gandhi (1966 PM elevation, 1971 War victory, 1980 Comeback)
3. Donald Trump (2016 US Presidential Election Victory)
4. Amitabh Bachchan (1973 Stardom Breakthrough, 1982 Coolie crisis)

Generates scholar-level visual event timelines and tier classifications.
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from apps.api.services.phalita_core.dataset_pipeline import DatasetBundle, PhalitaDatasetPipeline
from apps.api.services.phalita_core.decision_engine import (
    PhalitaConsultationTimeline,
    PhalitaDecisionEngine,
)
from apps.api.services.phalita_models.phalita_moe import PhalitaMoETrainer


def run_case_studies():
    csv_file = r"C:\Users\rkmau\Downloads\astro_data_combined (1).csv"
    print("=" * 95)
    print("        ASTROOS: FAMOUS CASE STUDIES VERIFICATION (SUPERVISORY DECISION LAYER)        ")
    print("=" * 95)

    # 1. Train or load calibrated Neural MoE
    print("Training / Initializing Authoritative Phalita MoE on full historical corpus...")
    pipeline = PhalitaDatasetPipeline(matching_tolerance_days=45)
    bundle = pipeline.parse_adb_csv(csv_file, limit=300, domain="career")
    trainer = PhalitaMoETrainer(epochs=30, batch_size=32)
    model, _ = trainer.train_moe(bundle)
    model.eval()

    decision_engine = PhalitaDecisionEngine(ephemeris_path="data/ephemeris", moe_model=model)

    # 2. Case study definitions
    cases = [
        {
            "name": "Narendra Modi",
            "birth_dt": datetime(1950, 9, 17, 5, 30, tzinfo=timezone.utc),  # 11:00 AM IST
            "lat": 23.7833,
            "lon": 72.6333,
            "start_yr": 2010,
            "end_yr": 2025,
            "domain": "career",
            "ground_truth_events": [
                ("2014-05-16", "2014-05-26", "16th Lok Sabha Landslide Win & Prime Minister Swearing-In"),
                ("2019-05-23", "2019-05-30", "17th Lok Sabha Landslide Re-election Victory"),
            ],
        },
        {
            "name": "Indira Gandhi",
            "birth_dt": datetime(1917, 11, 19, 17, 41, tzinfo=timezone.utc), # 23:11 IST
            "lat": 25.45,
            "lon": 81.85,
            "start_yr": 1965,
            "end_yr": 1985,
            "domain": "career",
            "ground_truth_events": [
                ("1966-01-24", "1966-01-24", "First Swearing-In as Prime Minister of India"),
                ("1971-12-16", "1971-12-16", "Indo-Pak War Victory & Liberation of Bangladesh"),
                ("1977-03-24", "1977-03-24", "Post-Emergency General Election Defeat"),
                ("1980-01-14", "1980-01-14", "Landslide Electoral Comeback as Prime Minister"),
            ],
        },
        {
            "name": "Donald Trump",
            "birth_dt": datetime(1946, 6, 14, 14, 54, tzinfo=timezone.utc), # 10:54 AM EDT
            "lat": 40.69,
            "lon": -73.80,
            "start_yr": 2010,
            "end_yr": 2025,
            "domain": "career",
            "ground_truth_events": [
                ("2016-11-08", "2017-01-20", "45th US Presidential Election Victory & Inauguration"),
            ],
        },
        {
            "name": "Amitabh Bachchan",
            "birth_dt": datetime(1942, 10, 11, 10, 30, tzinfo=timezone.utc), # 16:00 IST
            "lat": 25.45,
            "lon": 81.85,
            "start_yr": 1970,
            "end_yr": 1990,
            "domain": "career",
            "ground_truth_events": [
                ("1973-05-11", "1973-05-11", "Zanjeer Release (Superstardom / Angry Young Man Breakthrough)"),
                ("1982-07-26", "1982-09-24", "Coolie Movie Set Life-Threatening Accident & National Recovery"),
            ],
        },
    ]

    report_md = "# ASTROOS FAMOUS CASE STUDIES VERIFICATION REPORT\n\n"
    report_md += "**Architecture Layer:** Layer 3 Supervisory Adaptive Decision Governor\n"
    report_md += "**Synthesized Components:** Neural Mixture of Experts (Focal Loss) + Classical Ashtakavarga & Gochara Transits\n\n---\n"

    for case in cases:
        print(f"\nScanning Life Timeline for: {case['name']} ({case['start_yr']}–{case['end_yr']})...")
        timeline = decision_engine.scan_life_timeline(
            birth_datetime=case["birth_dt"],
            latitude=case["lat"],
            longitude=case["lon"],
            native_name=case["name"],
            scan_start_year=case["start_yr"],
            scan_end_year=case["end_yr"],
            domain=case["domain"],
        )

        print(f"Total Dasha Windows Scanned : {timeline.total_windows_scanned}")
        print(f"Tier 1 (Pratyaksha Phala)   : {timeline.pratyaksha_events_count}")
        print(f"Tier 2 (Sushupta Beeja)     : {timeline.latent_potential_count}")
        print(f"Tier 3 (Alpa Phala)         : {timeline.transient_triggers_count}")

        report_md += f"## Case Study: {case['name']}\n\n"
        report_md += f"- **Birth Datetime (UTC):** `{case['birth_dt']}` | **Coordinates:** `{case['lat']}, {case['lon']}`\n"
        report_md += f"- **Evaluation Horizon:** `{case['start_yr']} to {case['end_yr']}`\n"
        report_md += f"- **Summary:** `{timeline.pratyaksha_events_count} Pratyaksha Events`, `{timeline.latent_potential_count} Latent Potential Windows`, `{timeline.transient_triggers_count} Minor Triggers`\n\n"

        # Ground truth matching
        report_md += "### Ground-Truth Event Alignments:\n\n"
        report_md += "| Landmark Event Date | Event Description | Matched Dasha Window | Decision Tier | MoE Prob | 10H SAV | Transit Sanction | Scholar Assessment |\n"
        report_md += "|---|---|---|---|---|---|---|---|\n"

        for ev_start_str, ev_end_str, ev_desc in case["ground_truth_events"]:
            ev_start = date.fromisoformat(ev_start_str)
            matched_win = None
            for w in timeline.windows:
                if w.window_start <= ev_start <= w.window_end:
                    matched_win = w
                    break

            if matched_win:
                tr_str = "YES (Double Transit)" if matched_win.double_transit else ("YES (Jupiter Aspect)" if matched_win.jupiter_aspect else "Partial")
                tier_badge = f"**{matched_win.decision_tier}**"
                scholar_note = matched_win.actionable_verdict
                report_md += f"| `{ev_start_str}` | {ev_desc} | `{matched_win.window_start} to {matched_win.window_end}` ({matched_win.mahadasha_lord}-{matched_win.antardasha_lord}) | {tier_badge} | `{matched_win.raw_probability:.1%}` | `{matched_win.sav_10th_bindus}` | {tr_str} | {scholar_note} |\n"
            else:
                report_md += f"| `{ev_start_str}` | {ev_desc} | `Outside Scan Window` | — | — | — | — | — |\n"

        report_md += "\n### Full Antardasha Decision Timeline Table:\n\n"
        report_md += "| # | Period Window | Dasha (MD-AD) | MoE Prob | Tier Category | 10H SAV | Transits (J/S) | Hindi Explanation |\n"
        report_md += "|---|---|---|---|---|---|---|---|\n"

        for idx, w in enumerate(timeline.windows):
            tr_short = f"{'Y' if w.jupiter_aspect else 'N'}/{'Y' if w.saturn_aspect else 'N'}"
            report_md += f"| {idx+1} | {w.window_start} to {w.window_end} | `{w.mahadasha_lord}-{w.antardasha_lord}` | `{w.raw_probability:.1%}` | `{w.decision_tier}` | `{w.sav_10th_bindus}` | {tr_short} | {w.explanation_hi} |\n"

        report_md += "\n---\n"

    out_file = Path("PHALITA_FAMOUS_CASE_STUDIES_AUDIT.md")
    out_file.write_text(report_md, encoding="utf-8")
    print(f"\n[OK] Case Studies Audit complete! Full report written to {out_file.resolve()}")


if __name__ == "__main__":
    run_case_studies()
