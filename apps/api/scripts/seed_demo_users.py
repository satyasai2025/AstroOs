"""
AstroOS — Demo / test account seeder (Phase 5)

Creates two throwaway accounts that exercise the premium chain end to end:

    demo@astroos.dev  → no subscription        → FREE   (5 horoscopes, 0 research)
    pro@astroos.dev   → ACTIVE PRO subscription → PRO    (50 horoscopes, 1 research)

The PRO account is provisioned through SubscriptionService, i.e. the same code
path the admin API uses — so running this also smoke-tests the lifecycle.

Idempotent: re-running updates the existing rows instead of duplicating them.

DEVELOPMENT ONLY. The script refuses to run when ENVIRONMENT=production, since
it writes accounts with a known password.

Usage:
    python -m apps.api.scripts.seed_demo_users            # create/refresh
    python -m apps.api.scripts.seed_demo_users --remove   # delete the accounts

The password defaults to a well-known dev value and can be overridden:
    DEMO_USER_PASSWORD=... python -m apps.api.scripts.seed_demo_users
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from apps.api.domain.user import UserRole, UserStatus
from apps.api.models.subscription import SubscriptionEventModel, SubscriptionModel
from apps.api.models.user import UserModel
from apps.api.security.password import hash_password
from apps.api.services.entitlement_service import EntitlementService
from apps.api.services.subscription_service import SubscriptionService

DEFAULT_PASSWORD = "DemoPass123!"

DEMO_ACCOUNTS = [
    {
        "email": "demo@astroos.dev",
        "display_name": "Demo User",
        "role": UserRole.RESEARCHER,
        "plan_code": None,  # no subscription → FREE fallback
    },
    {
        "email": "pro@astroos.dev",
        "display_name": "Pro User",
        "role": UserRole.RESEARCHER,
        "plan_code": "PRO",  # ACTIVE PRO subscription
    },
]


class _UserRef:
    """Minimal adapter exposing the ``user.id.value`` shape the services expect."""

    def __init__(self, user_id):
        self.id = type("Uid", (), {"value": user_id})()


def _require_non_production() -> None:
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    if environment == "production":
        sys.exit(
            "Refusing to seed demo accounts: ENVIRONMENT=production. "
            "These accounts use a known password."
        )


def _session_maker():
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL is not set.")
    return async_sessionmaker(create_async_engine(url), expire_on_commit=False)


async def _get_user(db, email: str) -> UserModel | None:
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


async def _drop_subscription(db, user_id) -> None:
    """Remove any subscription (and its history) so the seed stays idempotent."""
    subs = (
        await db.execute(
            select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
        )
    ).scalars().all()
    for sub in subs:
        await db.execute(
            delete(SubscriptionEventModel).where(
                SubscriptionEventModel.subscription_id == sub.id
            )
        )
        await db.execute(delete(SubscriptionModel).where(SubscriptionModel.id == sub.id))
    if subs:
        await db.commit()


async def seed(remove: bool = False) -> None:
    _require_non_production()
    password = os.getenv("DEMO_USER_PASSWORD", DEFAULT_PASSWORD)
    Session = _session_maker()

    async with Session() as db:
        for spec in DEMO_ACCOUNTS:
            user = await _get_user(db, spec["email"])

            if remove:
                if user is None:
                    print(f"{spec['email']:22} not present, nothing to remove")
                    continue
                await _drop_subscription(db, user.id)
                await db.execute(delete(UserModel).where(UserModel.id == user.id))
                await db.commit()
                print(f"{spec['email']:22} removed")
                continue

            if user is None:
                user = UserModel(
                    email=spec["email"],
                    display_name=spec["display_name"],
                    hashed_password=hash_password(password),
                    role=spec["role"],
                    status=UserStatus.ACTIVE,
                    timezone="Asia/Kolkata",
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                action = "created"
            else:
                user.display_name = spec["display_name"]
                user.hashed_password = hash_password(password)
                user.role = spec["role"]
                user.status = UserStatus.ACTIVE
                await db.commit()
                await db.refresh(user)
                action = "updated"

            # Re-provision the subscription from scratch so repeated runs are
            # deterministic regardless of the lifecycle state left behind.
            await _drop_subscription(db, user.id)
            ref = _UserRef(user.id)

            if spec["plan_code"] is not None:
                await SubscriptionService(db).create(
                    ref,
                    spec["plan_code"],
                    current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
                )

            entitlement = EntitlementService(db)
            plan = await entitlement.resolve_user_plan(ref)
            limits = await entitlement.get_plan_limits(ref)
            status, _ = await entitlement.resolve_subscription_status(ref)
            print(
                f"{spec['email']:22} {action:8} sub={str(status):10} "
                f"plan={plan.plan_code:9} "
                f"horoscopes={limits.saved_horoscopes} "
                f"research={limits.research_projects_monthly}"
            )

    if not remove:
        print(f"\nPassword for both accounts: {password}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AstroOS demo accounts.")
    parser.add_argument(
        "--remove", action="store_true", help="Delete the demo accounts instead."
    )
    args = parser.parse_args()
    asyncio.run(seed(remove=args.remove))


if __name__ == "__main__":
    main()
