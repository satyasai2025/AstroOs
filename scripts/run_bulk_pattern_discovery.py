"""
AstroOS — High-Performance Bulk Pattern Discovery Pipeline
===========================================================
Processes 66,732 clean birth records and 80,345 real-world life events
to discover statistically verified astrological rules and timing patterns.
"""

import csv
import json
import logging
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.getcwd())

from apps.api.domain.research_case import ExtractedFeature, DiscoveredPattern
from apps.api.services.pattern_discovery import PatternDiscoveryService
from apps.api.services.jaimini_shared import house_count, rashi_at, rashi_index, signs_from

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BulkDiscovery")

# Vimshottari Lord Cycle (120 years)
VIMSHOTTARI_LORDS = ["ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"]
VIMSHOTTARI_YEARS = {"ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7, "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17}
TOTAL_VIM_YEARS = 120

def parse_date_safe(date_str: str) -> datetime | None:
    """Parse various date formats robustly."""
    if not date_str:
        return None
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    return None

def approximate_lagna_moon(dob_dt: datetime, tob_str: str, lat: float, lon: float):
    """
    Fast, deterministic sidereal approximation for bulk feature discovery.
    """
    # Sidereal Day calculation
    epoch = datetime(2000, 1, 1, 12, 0)
    days_since_epoch = (dob_dt - epoch).total_seconds() / 86400.0

    # Sun approximate longitude (~1 deg/day)
    day_of_year = dob_dt.timetuple().tm_yday
    sun_approx_deg = ((day_of_year - 80) * (360.0 / 365.25)) % 360.0

    # Local Sidereal Time for Lagna
    hour, minute = 12, 0
    if tob_str and ":" in tob_str:
        try:
            h_parts = tob_str.split(":")
            hour, minute = int(h_parts[0]), int(h_parts[1])
        except Exception:
            pass

    time_offset_deg = (hour + minute / 60.0) * 15.0
    lagna_deg = (sun_approx_deg + time_offset_deg + lon) % 360.0
    lagna_rashi_idx = int(lagna_deg / 30.0) % 12
    lagna_rashi = rashi_at(lagna_rashi_idx)

    # Moon approximate motion (~13.176 deg/day from base)
    moon_deg = (sun_approx_deg + (days_since_epoch * 12.19) % 360.0) % 360.0
    moon_rashi_idx = int(moon_deg / 30.0) % 12
    moon_rashi = rashi_at(moon_rashi_idx)

    # Approximate Moon Nakshatra (27 nakshatras, 13.333 deg each)
    nak_idx = int(moon_deg / (360.0 / 27.0)) % 27
    nak_lord = VIMSHOTTARI_LORDS[nak_idx % 9]

    return lagna_rashi, moon_rashi, nak_lord

def approximate_dasha_at_event(birth_dt: datetime, event_dt: datetime, birth_nak_lord: str):
    """Compute active Vimshottari Mahadasha at the moment of the event."""
    age_years = max(0.0, (event_dt - birth_dt).total_seconds() / (365.2422 * 86400.0))
    start_lord_idx = VIMSHOTTARI_LORDS.index(birth_nak_lord)
    
    elapsed = age_years % TOTAL_VIM_YEARS
    curr_idx = start_lord_idx
    while elapsed > 0:
        lord = VIMSHOTTARI_LORDS[curr_idx % 9]
        dur = VIMSHOTTARI_YEARS[lord]
        if elapsed <= dur:
            return lord
        elapsed -= dur
        curr_idx += 1
    return VIMSHOTTARI_LORDS[curr_idx % 9]

def approximate_transits_at_event(event_dt: datetime, lagna_rashi: str):
    """Compute approximate Gochara (transit) house of Jupiter and Saturn."""
    epoch = datetime(2000, 1, 1)
    days = (event_dt - epoch).total_seconds() / 86400.0

    # Jupiter orbit ~ 11.86 years (30 deg every ~361 days)
    jup_deg = (days / (11.86 * 365.25) * 360.0) % 360.0
    jup_rashi = rashi_at(int(jup_deg / 30.0) % 12)
    jup_house = house_count(lagna_rashi, jup_rashi)

    # Saturn orbit ~ 29.46 years (30 deg every ~896 days)
    sat_deg = (days / (29.46 * 365.25) * 360.0) % 360.0
    sat_rashi = rashi_at(int(sat_deg / 30.0) % 12)
    sat_house = house_count(lagna_rashi, sat_rashi)

    return jup_house, sat_house

def run_pipeline(csv_path: str, max_cases: int = 50000):
    logger.info("Starting Bulk Pattern Discovery Pipeline on: %s", csv_path)
    start_time = time.perf_counter()

    if not os.path.exists(csv_path):
        logger.error("File %s not found.", csv_path)
        return

    extracted_features: list[ExtractedFeature] = []
    case_counter = 0
    event_counter = 0
    category_counts = Counter()

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_counter += 1
            if case_counter > max_cases:
                break

            name = row.get("name", f"Case_{case_counter}")
            dob_str = row.get("dob")
            tob_str = row.get("tob")
            try:
                lat = float(row.get("latitude", 0.0))
                lon = float(row.get("longitude", 0.0))
            except ValueError:
                continue

            birth_dt = parse_date_safe(dob_str)
            if not birth_dt:
                continue

            lagna_rashi, moon_rashi, nak_lord = approximate_lagna_moon(birth_dt, tob_str, lat, lon)

            # Process up to 3 events per case
            for i in range(1, 4):
                e_type = row.get(f"event_{i}_type")
                e_date_str = row.get(f"event_{i}_date")
                if not e_type or not e_date_str or e_type.strip() == "Other":
                    continue

                event_dt = parse_date_safe(e_date_str)
                if not event_dt or event_dt < birth_dt:
                    continue

                event_counter += 1
                category_counts[e_type] += 1
                case_id = f"case_{case_counter}"

                # 1. Dasha Feature
                md_lord = approximate_dasha_at_event(birth_dt, event_dt, nak_lord)
                extracted_features.append(
                    ExtractedFeature(
                        research_case_id=case_id,
                        event_type=e_type,
                        event_date=event_dt.date(),
                        feature_category="dasha",
                        feature_name="mahadasha_lord",
                        feature_value=md_lord.capitalize(),
                    )
                )

                # 2. Transit Features (Jupiter & Saturn Houses)
                jup_h, sat_h = approximate_transits_at_event(event_dt, lagna_rashi)
                extracted_features.append(
                    ExtractedFeature(
                        research_case_id=case_id,
                        event_type=e_type,
                        event_date=event_dt.date(),
                        feature_category="transit",
                        feature_name="jupiter_house",
                        feature_value=f"Ju_H{jup_h}",
                    )
                )
                extracted_features.append(
                    ExtractedFeature(
                        research_case_id=case_id,
                        event_type=e_type,
                        event_date=event_dt.date(),
                        feature_category="transit",
                        feature_name="saturn_house",
                        feature_value=f"Sa_H{sat_h}",
                    )
                )

                # 3. Natal Lagna and Moon Sign
                extracted_features.append(
                    ExtractedFeature(
                        research_case_id=case_id,
                        event_type=e_type,
                        event_date=event_dt.date(),
                        feature_category="house",
                        feature_name="lagna_rashi",
                        feature_value=lagna_rashi.capitalize(),
                    )
                )
                extracted_features.append(
                    ExtractedFeature(
                        research_case_id=case_id,
                        event_type=e_type,
                        event_date=event_dt.date(),
                        feature_category="house",
                        feature_name="moon_rashi",
                        feature_value=moon_rashi.capitalize(),
                    )
                )

    logger.info("Extracted %d astrological feature observations across %d cases.", len(extracted_features), case_counter)
    logger.info("Event Categories Sample: %s", dict(category_counts.most_common(8)))

    # Run Pattern Discovery Engine
    logger.info("Running Statistical Pattern Discovery Engine (Wilson shrinkage + Base rate lift)...")
    discovery_service = PatternDiscoveryService()
    discovered_patterns: list[DiscoveredPattern] = discovery_service.discover(extracted_features)

    elapsed = time.perf_counter() - start_time
    logger.info("Discovery complete! Discovered %d statistically significant patterns in %.2f seconds.", len(discovered_patterns), elapsed)

    # Save Output
    output_path = os.path.join("data", "discovered_patterns_report.json")
    serializable = [
        {
            "event_type": p.event_type,
            "pattern_id": p.pattern_id,
            "description": p.description,
            "sample_size": p.sample_size,
            "confidence_score": round(p.confidence_score, 4),
            "lift_score": round(p.lift_score, 4),
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "value": d.value,
                    "count": d.count,
                    "frequency": round(d.frequency, 4),
                    "expected_by_chance": round(d.expected_by_chance, 4),
                    "significance": round(d.significance, 4),
                    "lift_score": round(d.lift_score, 4),
                }
                for d in p.dimensions
            ],
        }
        for p in discovered_patterns
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_cases_analyzed": case_counter,
                "total_events_analyzed": event_counter,
                "total_features_extracted": len(extracted_features),
                "total_patterns_discovered": len(discovered_patterns),
                "patterns": serializable,
            },
            f,
            indent=2,
        )

    print("\n" + "=" * 75)
    print("  ASTROOS BULK STATISTICAL PATTERN DISCOVERY REPORT")
    print("=" * 75)
    print(f"  Total Cases Processed:      {case_counter:,}")
    print(f"  Total Events Analyzed:      {event_counter:,}")
    print(f"  Total Features Extracted:   {len(extracted_features):,}")
    print(f"  Significant Rules Found:    {len(discovered_patterns):,}")
    print(f"  Report Saved To:            {output_path}")
    print("=" * 75)
    print("\n* Top Statistically Discovered Astrological Rules:\n")
    for idx, p in enumerate(discovered_patterns[:20], 1):
        print(f"  {idx:2d}. [{p.event_type.upper()}] {p.description}")
        print(f"      Support: {p.sample_size:,} cases | Confidence Score: {p.confidence_score*100:.1f}% | Lift vs Chance: {p.lift_score:.2f}x")
        for dim in p.dimensions:
            print(f"        -> {dim.dimension}: {dim.value} (Freq: {dim.frequency*100:.1f}%, Expected: {dim.expected_by_chance*100:.1f}%, Significance: {dim.significance:.3f})")
        print()

if __name__ == "__main__":
    csv_file = os.path.join("data", "kundalee", "kundalee_clean.csv")
    run_pipeline(csv_file, max_cases=66732)
