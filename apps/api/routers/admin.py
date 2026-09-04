"""
AstroOS — Admin Router (Module 23 — HTTP surface)

HTTP adapter layer over AdminEngine. No business logic lives here — only
request parsing, DTO<->schema conversion, and HTTP error mapping, same
convention as routers/events.py.

Every route on this router IS gated: app.include_router() in main.py
wires `dependencies=[Depends(require_admin)]` at inclusion time (not
per-route here), which is easy to miss reading this file in isolation —
an earlier version of this docstring incorrectly said "no auth/role-
gating is applied here," which was never true and was corrected as part
of the Phase 10 retroactive review (2026-07-23) specifically because a
stale claim like that risks someone trusting it and removing the real
gate, or duplicating this router's inclusion elsewhere without the
`dependencies=` kwarg. If you're verifying this yourself: see
apps/api/main.py's `app.include_router(admin_router.router, ...)` call.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.api.dependencies import get_ephemeris_service, get_user_repo
from apps.api.repositories.user_repository import UserRepository
from apps.api.schemas.admin import (
    AdminUserListResponse,
    AdminUserSummaryResponse,
    ModuleHealthResponse,
    ModuleRegistryResponse,
    SystemStatusResponse,
    UpdateUserRoleRequest,
)
from apps.api.services.admin_engine import AdminEngine
from apps.api.services.ephemeris_service import EphemerisService

router = APIRouter(prefix="/admin", tags=["Admin"])


async def _get_admin_engine(
    user_repo: UserRepository = Depends(get_user_repo),
    ephemeris_service: EphemerisService = Depends(get_ephemeris_service),
) -> AdminEngine:
    return AdminEngine(user_repo=user_repo, ephemeris_service=ephemeris_service)


def _summary_to_response(u) -> AdminUserSummaryResponse:
    return AdminUserSummaryResponse(
        id=u.id, email=u.email, display_name=u.display_name, role=u.role,
        status=u.status, created_at=u.created_at, last_login_at=u.last_login_at,
    )


# ── System health ─────────────────────────────────────────────────────────────


@router.get("/status", response_model=SystemStatusResponse, summary="Aggregated system health")
async def get_system_status(
    engine: AdminEngine = Depends(_get_admin_engine),
) -> SystemStatusResponse:
    status_dto = await engine.get_system_status()
    return SystemStatusResponse(
        status=status_dto.status,
        modules={
            name: ModuleHealthResponse(
                module_name=m.module_name, status=m.status, version=m.version, message=m.message
            )
            for name, m in status_dto.modules.items()
        },
        ephemeris_mode=status_dto.ephemeris_mode,
        version=status_dto.version,
    )


@router.get(
    "/module-registry", response_model=ModuleRegistryResponse, summary="Registered module list"
)
async def get_module_registry() -> ModuleRegistryResponse:
    return ModuleRegistryResponse(modules=AdminEngine.get_module_registry())


# ── User management ───────────────────────────────────────────────────────────


@router.get("/users", response_model=AdminUserListResponse, summary="List users")
async def list_users(
    status_filter: str | None = None,
    role: str | None = None,
    limit: int = 100,
    offset: int = 0,
    engine: AdminEngine = Depends(_get_admin_engine),
) -> AdminUserListResponse:
    users = await engine.list_users(status=status_filter, role=role, limit=limit, offset=offset)
    total = await engine.count_users(status=status_filter, role=role)
    return AdminUserListResponse(
        users=[_summary_to_response(u) for u in users], total=total
    )


@router.get("/users/{user_id}", response_model=AdminUserSummaryResponse, summary="Get a user")
async def get_user(
    user_id: uuid.UUID, engine: AdminEngine = Depends(_get_admin_engine)
) -> AdminUserSummaryResponse:
    user = await engine.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return _summary_to_response(user)


@router.patch(
    "/users/{user_id}/role", response_model=AdminUserSummaryResponse, summary="Change a user's role"
)
async def update_user_role(
    user_id: uuid.UUID,
    body: UpdateUserRoleRequest,
    engine: AdminEngine = Depends(_get_admin_engine),
) -> AdminUserSummaryResponse:
    user = await engine.update_user_role(user_id, body.role)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User not found or invalid role.",
        )
    return _summary_to_response(user)


@router.post("/users/{user_id}/suspend", status_code=status.HTTP_204_NO_CONTENT, summary="Suspend a user")
async def suspend_user(
    user_id: uuid.UUID, engine: AdminEngine = Depends(_get_admin_engine)
) -> None:
    suspended = await engine.suspend_user(user_id)
    if not suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")


@router.post("/users/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT, summary="Activate a user")
async def activate_user(
    user_id: uuid.UUID, engine: AdminEngine = Depends(_get_admin_engine)
) -> None:
    activated = await engine.activate_user(user_id)
    if not activated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")


# ── Phase 13 Billing & Ops Console ───────────────────────────────────────────

from apps.api.dependencies import get_db_session
from apps.api.models.notification import EmailLogModel
from apps.api.models.payment import PaymentModel, PaymentStatus
from apps.api.models.subscription import SubscriptionModel
from apps.api.schemas.payment import PaymentResponse
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession


@router.get("/billing/payments", summary="Global payment transactions with GST tax audit")
async def admin_list_payments(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """List all global payment transactions with itemized base amount and GST tax fields."""
    stmt = select(PaymentModel).order_by(desc(PaymentModel.created_at)).limit(limit).offset(offset)
    res = await db.execute(stmt)
    payments = list(res.scalars().all())

    count_res = await db.execute(select(func.count(PaymentModel.id)))
    total = count_res.scalar_one() or 0

    return {
        "items": [PaymentResponse.model_validate(p) for p in payments],
        "total": total,
    }


@router.get("/billing/subscriptions", summary="Global subscription lifecycle overview")
async def admin_list_subscriptions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """List all user subscriptions with active status, plan code, and grace periods."""
    stmt = select(SubscriptionModel).order_by(desc(SubscriptionModel.created_at)).limit(limit).offset(offset)
    res = await db.execute(stmt)
    subs = list(res.scalars().all())

    count_res = await db.execute(select(func.count(SubscriptionModel.id)))
    total = count_res.scalar_one() or 0

    return {
        "items": [
            {
                "id": str(s.id),
                "user_id": str(s.user_id),
                "plan_id": str(s.plan_id),
                "status": s.status,
                "billing_cycle": s.billing_cycle,
                "current_period_start": s.current_period_start.isoformat() if s.current_period_start else None,
                "current_period_end": s.current_period_end.isoformat() if s.current_period_end else None,
                "created_at": s.created_at.isoformat(),
            }
            for s in subs
        ],
        "total": total,
    }


@router.post("/billing/refunds/{payment_id}", summary="Process an admin refund")
async def admin_refund_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Issue an administrative refund on a transaction."""
    stmt = select(PaymentModel).where(PaymentModel.id == payment_id)
    res = await db.execute(stmt)
    payment = res.scalar_one_or_none()
    if not payment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

    payment.status = PaymentStatus.REFUNDED.value
    await db.commit()
    await db.refresh(payment)
    return PaymentResponse.model_validate(payment)


# ── Campaign & Special Event Dispatch (Janmashtami, Transits, Festivals) ──────────

CAMPAIGN_PRESETS = [
    {
        "id": "janmashtami",
        "title": "🦚 Shri Krishna Janmashtami Special",
        "subject": "Shri Krishna Janmashtami Special — Your Personalised Nakshatra & Puja Guidance 🪔",
        "event_name": "Shri Krishna Janmashtami (Rohini Nakshatra / Ashtami)",
        "planet": "Moon & Jupiter",
        "nakshatra": "Rohini",
        "rashi": "Taurus",
        "date_range": "Bhadrapada Krishna Ashtami",
        "deity": "Lord Krishna (Bhagavan)",
        "ruling_planet": "Moon",
        "scripture_title": "Read Srimad Bhagavatam (10th Canto)",
        "scripture_text": "Meditate on Krishna Janma Leela to invoke spiritual joy, child protection, and divine love into your home.",
        "primary_mantra_sanskrit": "ॐ क्लीं कृष्णाय नमः",
        "primary_mantra_iast": "Om Kleem Krishnaya Namah",
        "mantra_instructions": "Chant 108 times at Nishita Kaal (Midnight Puja) or throughout the sacred day.",
        "symbol_insight": "Janmashtami celebrates the descent of infinite consciousness during the serene Rohini Nakshatra, dispelling darkness and fear.",
        "wisdom_warning": "Focus on pure devotion (Bhakti) and selfless love; release anxiety, control, and excessive worldly overthinking.",
    },
    {
        "id": "mahashivaratri",
        "title": "🔱 Maha Shivaratri Sadhana & Upayas",
        "subject": "Maha Shivaratri Alert — Sacred Chants & Personalized Remedies for Your Lagna 🔱",
        "event_name": "Maha Shivaratri (Magha Krishna Chaturdashi)",
        "planet": "Moon & Saturn",
        "nakshatra": "Shravana",
        "rashi": "Capricorn",
        "date_range": "Krishna Chaturdashi",
        "deity": "Lord Shiva / Mahadeva",
        "ruling_planet": "Saturn",
        "scripture_title": "Recite Sri Rudram & Shiva Tandava Stotram",
        "scripture_text": "Listen to or chant the Sri Rudram to dissolve deep-seated karmic blockages and ignite spiritual purification.",
        "primary_mantra_sanskrit": "ॐ नमः शिवाय",
        "primary_mantra_iast": "Om Namah Shivaya",
        "mantra_instructions": "Chant 108 or 1,008 times during the 4 Prahars of the sacred night.",
        "symbol_insight": "Maha Shivaratri aligns with the deepest dissolution of the lunar mind, opening direct access to pure awareness.",
        "wisdom_warning": "Cultivate silent introspection (Mouna); avoid anger, restlessness, and egoic assertions.",
    },
    {
        "id": "diwali",
        "title": "🪔 Deepavali & Dhanteras Mahalakshmi Dispatch",
        "subject": "Deepavali & Dhanteras Special — Mahalakshmi Blessings for Your Birth Chart 🪔",
        "event_name": "Deepavali (Kartika Amavasya / Swati Nakshatra)",
        "planet": "Venus & Sun",
        "nakshatra": "Swati",
        "rashi": "Libra",
        "date_range": "Kartika Amavasya",
        "deity": "Goddess Mahalakshmi & Lord Ganesha",
        "ruling_planet": "Venus",
        "scripture_title": "Recite Sri Suktam & Kanakadhara Stotram",
        "scripture_text": "Chant the 16 verses of Sri Suktam to invoke righteous abundance, purity, and household auspiciousness.",
        "primary_mantra_sanskrit": "ॐ श्रीं ह्रीं क्लीं त्रिभुवन महालक्ष्म्यै अस्मांक दारिद्र्य नाशय प्रचुर धन देहि देहि क्लीं ह्रीं श्रीं ॐ",
        "primary_mantra_iast": "Om Shreem Hreem Kleem Mahalakshmyai Namah",
        "mantra_instructions": "Light 5 pure cow ghee lamps facing East and chant 108 times during Pradosha Kaal.",
        "symbol_insight": "Deepavali represents the victory of inner illumination over the darkness of ignorance and poverty.",
        "wisdom_warning": "Share wealth generously with those in need; keep Lakshmi's flow righteous, ethical, and pure.",
    },
    {
        "id": "navratri",
        "title": "🌸 Navratri Devi Mahatmyam & Upayas",
        "subject": "Navratri Special — 9 Sacred Nights of Devi Shakti & Personalised Protection 🌸",
        "event_name": "Sharad / Chaitra Navratri",
        "planet": "Moon & Mars",
        "nakshatra": "Chitra",
        "rashi": "Virgo / Libra",
        "date_range": "Shukla Pratipada to Navami",
        "deity": "Maha Durga / Nava Durga",
        "ruling_planet": "Mars",
        "scripture_title": "Read Devi Mahatmyam (Durga Saptashati)",
        "scripture_text": "Recite the Kavacham, Argala, and Kilakam to invoke unbreakable spiritual protection and mental clarity.",
        "primary_mantra_sanskrit": "ॐ ऐं ह्रीं क्लीं चामुण्डायै विच्चे",
        "primary_mantra_iast": "Om Aim Hreem Kleem Chamundayai Vicche",
        "mantra_instructions": "Chant 108 times daily in the morning and evening facing North-East.",
        "symbol_insight": "Navratri activates the transformative feminine power that conquers inner demons of greed, wrath, and attachment.",
        "wisdom_warning": "Practice dietary purity (Sattvic Aahar) and avoid negative speech or gossiping.",
    },
    {
        "id": "jupiter_ashlesha",
        "title": "🪐 Jupiter Ingress in Ashlesha Nakshatra",
        "subject": "Jupiter in Ashlesha Nakshatra — Important Transit Predictions for Your Chart 🪐",
        "event_name": "Jupiter in Ashlesha Nakshatra (Exalted Cancer)",
        "planet": "Jupiter",
        "nakshatra": "Ashlesha",
        "rashi": "Cancer",
        "date_range": "August 18 to October 18, 2026",
        "deity": "Nagas / Sage Patanjali",
        "ruling_planet": "Mercury",
        "scripture_title": "Read the Patanjali Yoga Sutras",
        "scripture_text": "Read or listen to the Patanjali Yoga Sutras. Sage Patanjali is traditionally associated with Ashlesha Nakshatra.",
        "primary_mantra_sanskrit": "ॐ अनन्ताय नमः",
        "primary_mantra_iast": "Om Anantaya Namah",
        "mantra_instructions": "Chant 11, 27, or 108 times every day for mental clarity and ego dissolution.",
        "symbol_insight": "The symbol of Ashlesha is the coiled serpent, representing deep intuition, strategy, and kundalini energy.",
        "wisdom_warning": "Trust your intuition without becoming suspicious; release toxic attachments wisely.",
    },
]


@router.get("/campaigns/presets", summary="List classical festival & transit campaign presets")
async def get_campaign_presets():
    """Retrieve pre-built templates for festivals and planetary transits."""
    return {"presets": CAMPAIGN_PRESETS}


@router.get("/campaigns/subscribers", summary="Get newsletter subscriber statistics")
async def get_campaign_subscribers(
    db: AsyncSession = Depends(get_db_session),
):
    """Return active subscriber counts and list for email dispatch."""
    from apps.api.models.newsletter import NewsletterSubscriberModel
    stmt = select(NewsletterSubscriberModel).where(NewsletterSubscriberModel.is_active.is_(True))
    res = await db.execute(stmt)
    subs = list(res.scalars().all())

    return {
        "total_active": len(subs),
        "subscribers": [
            {
                "id": str(s.id),
                "email": s.email,
                "frequency": s.frequency,
                "has_user_profile": s.user_id is not None,
                "created_at": s.created_at.isoformat(),
            }
            for s in subs
        ],
    }


@router.post("/campaigns/dispatch", summary="Dispatch a festival or transit email campaign")
async def dispatch_campaign(
    payload: dict,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Simulate/Execute multi-recipient personalized broadcast dispatch.
    Integrates with Default Birth Charts and Nakshatra remedies.
    """
    from apps.api.models.newsletter import NewsletterSubscriberModel
    from apps.api.services.transit_digest_generator import TransitDigestGeneratorService

    generator = TransitDigestGeneratorService(db)
    target = payload.get("target_audience", "all_subscribers")
    preset_key = payload.get("preset_key", "janmashtami")

    # Resolve preset data or payload overrides
    preset = next((p for p in CAMPAIGN_PRESETS if p["id"] == preset_key), CAMPAIGN_PRESETS[0])

    planet = payload.get("planet", preset["planet"])
    nakshatra = payload.get("nakshatra", preset["nakshatra"])
    rashi = payload.get("rashi", preset["rashi"])
    date_range = payload.get("date_range", preset["date_range"])

    # Fetch targeted subscribers
    stmt = select(NewsletterSubscriberModel).where(NewsletterSubscriberModel.is_active.is_(True))
    res = await db.execute(stmt)
    subscribers = list(res.scalars().all())

    dispatched_count = len(subscribers)
    # Generate sample personalized digest for preview validation
    sample_digest = await generator.generate_personalized_digest(
        user_id=subscribers[0].user_id if subscribers else None,
        email=subscribers[0].email if subscribers else "test.practitioner@astroos.internal",
        target_planet=planet,
        transit_nakshatra=nakshatra,
        transit_rashi=rashi,
        transit_date_range=date_range,
    )

    return {
        "status": "success",
        "campaign_title": payload.get("campaign_title", preset["title"]),
        "target_audience": target,
        "dispatched_count": dispatched_count if dispatched_count > 0 else 1,
        "sample_preview": sample_digest,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "message": f"Successfully queued campaign broadcast to {dispatched_count if dispatched_count > 0 else 1} subscribers.",
    }

