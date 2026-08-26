"""
AstroOS — Seed 298 KP Astro Categories with Vedic Tags (House, Karaka, Description)
"""

import asyncio
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, os.getcwd())

from apps.api.dependencies import _async_session_factory
from apps.api.services.event_category_service import EventCategoryService

CSV_PATH = Path(r"c:\Users\rkmau\Downloads\AstroOS_Additions\kp_astro_zhakass_map.csv")

async def seed():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found")
        return

    with CSV_PATH.open(encoding="utf-8-sig") as f:
        cats = list(csv.DictReader(f))

    print(f"Reading {len(cats)} KP Astro events from Zhakass map...")
    async with _async_session_factory() as session:
        svc = EventCategoryService(session)
        updated_count = 0
        for i, r in enumerate(cats):
            path_str = r.get("astroos_category_path") or r.get("astroos_path") or ""
            parts = [p.strip() for p in path_str.split("/") if p.strip()]
            if not parts:
                continue

            node = await svc.resolve_or_create_category_path(parts, source="import")
            
            house_str = (r.get("vedic_house_no") or r.get("main_house") or "").strip()
            house_num = int(house_str) if house_str.isdigit() else None
            karaka = (r.get("vedic_karaka") or r.get("support_planets") or "").strip() or None
            desc = (r.get("description") or "").strip() or None

            await svc.update_tags(
                node.id,
                house_number=house_num,
                karaka_planet=karaka,
                description=desc,
            )
            updated_count += 1

        await session.commit()
    print(f"Successfully registered and tagged {updated_count} KP categories in database!")

if __name__ == "__main__":
    asyncio.run(seed())
