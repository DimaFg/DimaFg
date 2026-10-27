import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.logging import log_event
from app.modules.leads.contact import classify_contact
from app.modules.leads.models import (
    Lead,
    LeadStatus,
    LeadStatusHistory,
    NotificationStatus,
    lead_number_seq,
)
from app.modules.leads.schemas import LeadCreate
from app.modules.notifications.models import OutboxTask
from app.modules.services.models import Service

log = logging.getLogger("app.leads")

NOTIFY_TASK = "lead.notify"


@dataclass
class LeadResult:
    lead: Lead
    created: bool


def _now() -> datetime:
    return datetime.now(UTC)


def _find_by_idempotency_key(db: Session, key: str) -> Lead | None:
    return db.scalars(select(Lead).where(Lead.idempotency_key == key)).first()


def _resolve_service(db: Session, slug: str | None) -> Service | None:
    if slug is None or slug == "other":
        return None
    service = db.scalars(select(Service).where(Service.slug == slug, Service.is_active)).first()
    if service is None:
        raise ApiError(
            422,
            "validation_error",
            "Проверьте правильность заполнения полей.",
            {"service": "Выберите услугу из списка."},
        )
    return service


def _spam_reason(data: LeadCreate) -> str | None:
    if data.website:
        return "honeypot"
    min_ms = get_settings().lead_min_fill_seconds * 1000
    if data.elapsed_ms is not None and data.elapsed_ms < min_ms:
        return "too_fast"
    return None


def _check_rate_limits(db: Session, ip_hash: str | None, contact_normalized: str) -> None:
    settings = get_settings()
    now = _now()
    if ip_hash:
        per_ip = db.scalar(
            select(func.count())
            .select_from(Lead)
            .where(Lead.ip_hash == ip_hash, Lead.created_at > now - timedelta(hours=1))
        )
        if per_ip >= settings.lead_rate_limit_per_ip_hour:
            raise ApiError(
                429,
                "rate_limited",
                "Слишком много заявок за короткое время. Попробуйте позже или напишите в Telegram.",
                headers={"Retry-After": "3600"},
            )
    per_contact = db.scalar(
        select(func.count())
        .select_from(Lead)
        .where(
            Lead.contact_normalized == contact_normalized,
            Lead.created_at > now - timedelta(days=1),
        )
    )
    if per_contact >= settings.lead_rate_limit_per_contact_day:
        raise ApiError(
            429,
            "rate_limited",
            "Мы уже получили ваши заявки и скоро ответим.",
            headers={"Retry-After": "86400"},
        )


def _find_recent_duplicate(db: Session, contact_normalized: str, data: LeadCreate) -> Lead | None:
    window = timedelta(minutes=get_settings().lead_dedup_window_minutes)
    return db.scalars(
        select(Lead)
        .where(
            Lead.contact_normalized == contact_normalized,
            Lead.message == data.message,
            Lead.created_at > _now() - window,
        )
        .order_by(Lead.created_at.desc())
    ).first()


def _next_public_number(db: Session) -> str:
    n = db.scalar(lead_number_seq.next_value())
    return f"{_now().year}-{n:05d}"


def create_lead(
    db: Session, data: LeadCreate, *, ip_hash: str | None, idempotency_key: str | None
) -> LeadResult:
    settings = get_settings()

    if idempotency_key and (existing := _find_by_idempotency_key(db, idempotency_key)):
        return LeadResult(existing, created=False)

    contact_type, contact_normalized = classify_contact(data.contact)
    _check_rate_limits(db, ip_hash, contact_normalized)

    if duplicate := _find_recent_duplicate(db, contact_normalized, data):
        return LeadResult(duplicate, created=False)

    service = _resolve_service(db, data.service)
    spam_reason = _spam_reason(data)
    status = LeadStatus.spam if spam_reason else LeadStatus.new
    attribution = data.attribution
    now = _now()

    lead = Lead(
        public_number=_next_public_number(db),
        name=data.name,
        contact=data.contact,
        contact_normalized=contact_normalized,
        contact_type=contact_type,
        service_id=service.id if service else None,
        message=data.message,
        status=status,
        source=attribution.referrer if attribution else None,
        landing_page=attribution.landing_page if attribution else None,
        utm_source=attribution.utm_source if attribution else None,
        utm_medium=attribution.utm_medium if attribution else None,
        utm_campaign=attribution.utm_campaign if attribution else None,
        utm_term=attribution.utm_term if attribution else None,
        utm_content=attribution.utm_content if attribution else None,
        consent_given_at=now,
        privacy_policy_version=data.privacy_policy_version or settings.privacy_policy_version,
        notification_status=(
            NotificationStatus.skipped if spam_reason else NotificationStatus.pending
        ),
        idempotency_key=idempotency_key,
        ip_hash=ip_hash,
        spam_reason=spam_reason,
    )
    db.add(lead)
    db.flush()
    db.add(LeadStatusHistory(lead_id=lead.id, from_status=None, to_status=status))
    if not spam_reason:
        db.add(
            OutboxTask(
                kind=NOTIFY_TASK,
                payload={"lead_id": str(lead.id)},
                max_attempts=settings.outbox_max_attempts,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        # Параллельный запрос с тем же Idempotency-Key успел раньше.
        db.rollback()
        if idempotency_key and (existing := _find_by_idempotency_key(db, idempotency_key)):
            return LeadResult(existing, created=False)
        raise

    log_event(
        log,
        "lead created",
        lead_id=str(lead.id),
        public_number=lead.public_number,
        contact_type=contact_type.value,
        spam_reason=spam_reason,
    )
    return LeadResult(lead, created=True)
