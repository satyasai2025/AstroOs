"""
AstroOS — SFT Training Dataset Generator for Kundli LLM
======================================================
Generates supervised fine-tuning (SFT) dataset pairs in standard ChatML / OpenAI JSONL format.
Ensures:
  1. Strict mathematical grounding from AstroOS Ephemeris engines.
  2. Complete compliance with Vinay Jha's 10-step Shastric prediction sequence.
  3. Formatted for direct training with Unsloth, Hugging Face TRL, or Axolotl.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
import random
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.services.astrologer_fact_synthesizer import AstrologerFactSynthesizer
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.master_astrologer_engine import MasterAstrologerEngine, _MASTER_SYSTEM_PROMPT

# Representative geographic coordinates (across India and global cities)
LOCATIONS = [
    {"city": "New Delhi", "lat": 28.6139, "lon": 77.2090},
    {"city": "Varanasi", "lat": 25.3176, "lon": 82.9739},
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"city": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"city": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    {"city": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
    {"city": "Jaipur", "lat": 26.9124, "lon": 75.7873},
    {"city": "London", "lat": 51.5074, "lon": -0.1278},
    {"city": "New York", "lat": 40.7128, "lon": -74.0060},
]

NAMES = [
    "Aarav Sharma", "Ananya Verma", "Rohan Iyer", "Pooja Patel", "Vikram Malhotra",
    "Sneha Rao", "Aditya Joshi", "Kavita Nair", "Rahul Singhania", "Meera Sen",
    "Siddharth Roy", "Deepa Nambiar", "Karan Kapoor", "Ritu Agrawal", "Arjun Gupta"
]


def generate_dataset(num_samples: int = 50, output_path: str = "data/kundli_llm_sft_dataset.jsonl") -> int:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    wrapper = EphemerisWrapper("data/ephemeris")
    horoscope_engine = HoroscopeEngine(wrapper)
    synthesizer = AstrologerFactSynthesizer()
    astrologer = MasterAstrologerEngine(synthesizer)

    records = []
    start_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2015, 12, 31, tzinfo=timezone.utc)
    total_seconds = int((end_date - start_date).total_seconds())

    print(f"[+] Generating {num_samples} Shastric SFT training pairs...")

    for i in range(num_samples):
        # Pick random birth moment
        rand_sec = random.randint(0, total_seconds)
        birth_dt = start_date + timedelta(seconds=rand_sec)
        loc = random.choice(LOCATIONS)
        name = random.choice(NAMES)

        try:
            chart = horoscope_engine.generate_d1(
                birth_datetime_utc=birth_dt,
                latitude=loc["lat"],
                longitude=loc["lon"],
                ayanamsa="lahiri",
            )

            # Generate 100% plain conversational English consultation
            result = astrologer.generate_consultation(
                chart=chart,
                target_date=date(2026, 9, 5),
                subject_name=name,
                language="en",
            )

            user_query = (
                f"Please provide a personal Master Astrologer Consultation in clear, plain English for {name} ({loc['city']}).\n\n"
                f"GROUNDING FACTS:\n{result.grounding_facts.dense_grounding_text}"
            )

            pair = {
                "messages": [
                    {"role": "system", "content": _MASTER_SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": user_query.strip()},
                    {"role": "assistant", "content": result.reading_markdown.strip()},
                ]
            }
            records.append(pair)

            if (i + 1) % 10 == 0 or (i + 1) == num_samples:
                print(f"  -> Generated {i + 1}/{num_samples} pairs")

        except Exception as e:
            print(f"[-] Error generating chart for sample {i}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[OK] Successfully saved {len(records)} pairs to: {output_path}")
    return len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Kundli LLM SFT training dataset")
    parser.add_argument("--samples", type=int, default=20, help="Number of training samples to generate")
    parser.add_argument("--output", type=str, default="data/kundli_llm_sft_dataset.jsonl", help="Output JSONL path")
    args = parser.parse_args()

    generate_dataset(num_samples=args.samples, output_path=args.output)
