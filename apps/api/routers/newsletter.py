"""
AstroOS — Newsletter & Personalized Transit Digest Router
=========================================================
Endpoints:
- POST /api/v1/newsletter/subscribe     — Subscribe email to transit digests
- GET  /api/v1/newsletter/preview       — Preview personalized transit email for user's default chart
- GET  /api/v1/newsletter/unsubscribe   — 1-click tokenized unsubscribe
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import (
    get_current_user_from_bearer,
    get_db_session,
)
from apps.api.domain.user import User
from apps.api.models.newsletter import NewsletterSubscriberModel
from apps.api.services.transit_digest_generator import TransitDigestGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/newsletter", tags=["Newsletter & Transit Digest"])


class SubscribeRequest(BaseModel):
    email: EmailStr
    frequency: str = "monthly"


class SubscribeResponse(BaseModel):
    status: str
    message: str
    email: str
    is_personalized: bool


class UnsubscribeResponse(BaseModel):
    status: str
    message: str


@router.post(
    "/subscribe",
    response_model=SubscribeResponse,
    status_code=status.HTTP_200_OK,
    summary="Subscribe to monthly astronomical transit & research dispatch",
)
async def subscribe_to_newsletter(
    req: SubscribeRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user_from_bearer),
) -> SubscribeResponse:
    """Register subscriber email and link to user profile/default chart if logged in."""
    user_id = UUID(str(current_user.id)) if current_user and current_user.id else None

    # Check if email already exists
    stmt = select(NewsletterSubscriberModel).where(NewsletterSubscriberModel.email == req.email.lower()).limit(1)
    result = await db.execute(stmt)
    subscriber = result.scalar_one_or_none()

    if subscriber:
        subscriber.is_active = True
        subscriber.frequency = req.frequency
        if user_id:
            subscriber.user_id = user_id
    else:
        subscriber = NewsletterSubscriberModel(
            email=req.email.lower(),
            user_id=user_id,
            frequency=req.frequency,
            is_active=True,
        )
        db.add(subscriber)

    await db.commit()

    return SubscribeResponse(
        status="subscribed",
        message="Successfully subscribed to Vedic Research & Transit Dispatch.",
        email=req.email.lower(),
        is_personalized=user_id is not None,
    )


@router.get(
    "/preview",
    summary="Preview personalized transit digest email for current user's default chart",
)
async def preview_transit_digest(
    planet: str = Query(default="Jupiter", description="Transiting planet"),
    nakshatra: str = Query(default="Ashlesha", description="Transiting Nakshatra"),
    rashi: str = Query(default="Cancer", description="Transiting Rashi"),
    date_range: str = Query(default="August 18 to October 18, 2026", description="Transit period"),
    db: AsyncSession = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user_from_bearer),
) -> Dict[str, Any]:
    """Generate and return a live preview of the personalized transit digest email."""
    user_id = UUID(str(current_user.id)) if current_user and current_user.id else None
    email = current_user.email if current_user else "meena.practitioner@astroos.internal"
    user_name = current_user.display_name if current_user else "Meena"

    generator = TransitDigestGeneratorService(db)
    digest = await generator.generate_personalized_digest(
        user_id=user_id,
        email=email,
        user_name=user_name,
        target_planet=planet,
        transit_nakshatra=nakshatra,
        transit_rashi=rashi,
        transit_date_range=date_range,
    )

    return digest


@router.get(
    "/unsubscribe",
    response_model=UnsubscribeResponse,
    summary="One-click unsubscribe from transit digests",
)
async def unsubscribe_newsletter(
    token: str = Query(..., description="Secret unsubscribe token"),
    db: AsyncSession = Depends(get_db_session),
) -> UnsubscribeResponse:
    """Deactivate subscription via secure unsubscribe token."""
    stmt = (
        update(NewsletterSubscriberModel)
        .where(NewsletterSubscriberModel.unsubscribe_token == token)
        .values(is_active=False)
    )
    res = await db.execute(stmt)
    await db.commit()

    if res.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired unsubscribe token.",
        )

    return UnsubscribeResponse(
        status="unsubscribed",
        message="You have successfully unsubscribed from AstroOS transit digests.",
    )
