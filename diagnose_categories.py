import asyncio
import os

assert os.environ.get("DATABASE_URL"), "DATABASE_URL is not set"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from apps.api.services.feature_extraction import FeatureExtractionService
from apps.api.services.pattern_discovery import PatternDiscoveryService, MIN_SIGNIFICANCE, MIN_FREQUENCY


async def main():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        features = await FeatureExtractionService(session).extract_all()

    from collections import Counter
    cat_counts = Counter(f.feature_category for f in features)
    print("Feature counts by category:", dict(cat_counts))
    print()

    engine_svc = PatternDiscoveryService()
    base_rates, by_type = engine_svc._build_stats(features)

    for category in ("dasha", "house", "nakshatra", "yoga", "transit"):
        print(f"=== Top 8 by significance for category={category} (any event type, incl. below threshold) ===")
        rows = []
        for etype, stats in by_type.items():
            for dv in stats.dim_values:
                if dv.dimension.startswith(category) or (category == "yoga" and dv.dimension.startswith("active yoga")) or (category == "nakshatra" and dv.dimension.startswith("nakshatra")):
                    rows.append((etype, dv.dimension, dv.value, dv.frequency, dv.expected_by_chance, dv.significance, dv.count))
        rows.sort(key=lambda r: -r[5])
        for etype, dim, val, freq, base, sig, count in rows[:8]:
            flag = "CLEARS" if (sig >= MIN_SIGNIFICANCE and freq >= MIN_FREQUENCY) else "below"
            print(f"  [{flag}] {etype}: {dim}={val}  freq={freq:.3f} base={base:.3f} sig={sig:.3f} n={count}")
        if not rows:
            print("  (no dimension-values of this category exist in the extracted feature set at all)")
        print()


asyncio.run(main())
