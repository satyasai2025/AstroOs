"""
AstroOS — Seed All 408 KP Master Events into database (event_categories + event_types)
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.getcwd())

from apps.api.dependencies import _async_session_factory
from apps.api.services.event_category_service import EventCategoryService
from apps.api.services.event_type_service import EventTypeService

JSON_PATH = "apps/api/data/kp_events.json"

async def seed_all_408_events():
    if not os.path.exists(JSON_PATH):
        print(f"ERROR: {JSON_PATH} not found")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        events = json.load(f)

    print(f"Seeding all {len(events)} KP Master Events into Database...")
    async with _async_session_factory() as session:
        cat_svc = EventCategoryService(session)
        type_svc = EventTypeService(session)

        for e in events:
            category = e.get("category", "General")
            name = e.get("name", "")
            if not name:
                continue

            # 1. Seed into event_categories tree: Category / Name
            cat_path = [category, name]
            cat_node = await cat_svc.resolve_or_create_category_path(cat_path, source="kp_master")

            # Attach Vedic metadata (Primary Cusp, Karaka Planets, Required Houses)
            house = e.get("primary_cusp")
            karakas = ", ".join(e.get("supporting_planets", [])) or None
            req_houses = ", ".join(str(h) for h in e.get("required_houses", []))
            desc = f"Primary cusp: {house}. Required houses: [{req_houses}]. Polarity: {e.get('polarity', 'NEUTRAL')}"

            await cat_svc.update_tags(
                cat_node.id,
                house_number=house,
                karaka_planet=karakas,
                description=desc,
            )

            # 2. Seed into event_types tree
            type_path = [category, name]
            await type_svc.resolve_or_create_event_type_path(type_path, source="kp_master")

        await session.commit()
    print(f"Successfully seeded all {len(events)} KP Master Events into database!")

if __name__ == "__main__":
    asyncio.run(seed_all_408_events())
