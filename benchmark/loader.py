"""
AstroOS — Ground Truth Benchmark Loader & Split Engine
======================================================
Enforces non-negotiable benchmark governance rules:
  1. No chart without >= 1 verified event enters the set.
  2. No event without precision + provenance source enters the set.
  3. Split is strictly PER NATIVE (not per event) to prevent data leakage.
  4. Frozen seed=42 for deterministic, auditable train/test partitions.
"""

from collections import Counter
import json
from pathlib import Path
import random
from typing import Any, Dict, List, Tuple

VALID_EVENT_TYPES = {
    "death",
    "marriage",
    "divorce",
    "career.office",
    "accident",
    "health.disease",
    "family",
    "other",
}


def _read_jsonl(p: Path) -> List[Dict[str, Any]]:
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_benchmark(
    data_dir: str = "data/benchmark",
    holdout_frac: float = 0.20,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns (train, test) lists of case dicts:
    {"chart": {...}, "events": [...]}
    """
    d_path = Path(data_dir)
    charts_path = d_path / "charts.jsonl"
    events_path = d_path / "events.jsonl"

    if not charts_path.exists() or not events_path.exists():
        raise FileNotFoundError(f"Missing benchmark files in {d_path}")

    charts = {c["case_id"]: c for c in _read_jsonl(charts_path)}
    cases: Dict[str, Dict[str, Any]] = {}

    for ev in _read_jsonl(events_path):
        assert ev["event_type"] in VALID_EVENT_TYPES, f"Invalid event_type: {ev['event_type']}"
        assert ev["precision"] in {"day", "month", "year"}, f"Invalid precision: {ev['precision']}"
        assert ev.get("source"), "Event missing provenance source"
        if ev.get("verified") is not True:
            continue

        cid = ev["case_id"]
        if cid not in charts:
            continue

        cases.setdefault(cid, {"chart": charts[cid], "events": []})
        cases[cid]["events"].append(ev)

    case_list = list(cases.values())
    rng = random.Random(seed)
    # Sort first to guarantee identical shuffle across platforms
    case_list.sort(key=lambda x: x["chart"]["case_id"])
    rng.shuffle(case_list)

    n_test = max(1, int(len(case_list) * holdout_frac))
    train_set = case_list[n_test:]
    test_set = case_list[:n_test]

    return train_set, test_set


def domain_report(cases: List[Dict[str, Any]]) -> Counter:
    """Prints honest per-domain sample sizes (N) before calibration."""
    counts = Counter(ev["event_type"] for c in cases for ev in c["events"])
    print(f"Total Cohort Natives : {len(cases)}")
    print(f"Total Verified Events: {sum(counts.values())}")
    print("\nHonest Per-Domain Sample Sizes:")
    for k, v in counts.most_common():
        print(f"  {k:22s} n={v}")
    return counts


if __name__ == "__main__":
    train, test = load_benchmark()
    print("=" * 60)
    print(f"TRAIN SET (80%, N={len(train)} natives):")
    domain_report(train)
    print("-" * 60)
    print(f"TEST SET (20% Hold-out, N={len(test)} natives):")
    domain_report(test)
    print("=" * 60)
