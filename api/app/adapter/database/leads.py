from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapter.database.models.leads import Lead, LeadStatusHistory, lead_number_seq
from app.adapter.database.models.outbox import OutboxTask
from app.adapter.database.models.services import Service
from app.domain.leads.entities import LeadReceipt, NewLead


class SQLAlchemyLeadRepository:
    def __init__(self, session: Session):
        self.session = session

    def lock_submission(self, contact: str, ip_hash: str | None, key: str | None) -> None:
        locks = {f"lead-contact:{contact}"}
        if ip_hash:
            locks.add(f"lead-ip:{ip_hash}")
        if key:
            locks.add(f"lead-key:{key}")
        # Одинаковый порядок предотвращает взаимную блокировку запросов.
        # Блокировки автоматически освобождаются при commit/rollback.
        for value in sorted(locks):
            self.session.execute(
                select(func.pg_advisory_xact_lock(func.hashtextextended(value, 0)))
            )

    def find_by_key(self, key: str) -> LeadReceipt | None:
        number = self.session.scalar(select(Lead.public_number).where(Lead.idempotency_key == key))
        return LeadReceipt(number) if number else None

    def find_duplicate(
        self,
        contact: str,
        message: str,
        service_id: UUID | None,
        since: datetime,
        *,
        spam_reason: str | None,
    ) -> LeadReceipt | None:
        number = self.session.scalar(
            select(Lead.public_number)
            .where(
                Lead.contact_normalized == contact,
                Lead.message == message,
                Lead.service_id == service_id,
                Lead.spam_reason == spam_reason,
                Lead.created_at > since,
            )
            .order_by(Lead.created_at.desc())
            .limit(1)
        )
        return LeadReceipt(number) if number else None

    def count_by_ip(self, ip_hash: str, since: datetime) -> int:
        return (
            self.session.scalar(
                select(func.count())
                .select_from(Lead)
                .where(
                    Lead.ip_hash == ip_hash,
                    Lead.created_at > since,
                )
            )
            or 0
        )

    def count_by_contact(self, contact: str, since: datetime) -> int:
        return (
            self.session.scalar(
                select(func.count())
                .select_from(Lead)
                .where(
                    Lead.contact_normalized == contact,
                    Lead.created_at > since,
                )
            )
            or 0
        )

    def next_public_number(self, year: int) -> str:
        number = self.session.scalar(lead_number_seq.next_value())
        return f"{year}-{number:05d}"

    def add(self, lead: NewLead) -> None:
        data = asdict(lead)
        attribution = data.pop("attribution")
        data.update(attribution)
        data["source"] = data.pop("referrer")
        self.session.add(
            Lead(
                **data,
                status=lead.status,
                notification_status=lead.notification_status,
            )
        )
        self.session.flush()
        self.session.add(
            LeadStatusHistory(
                lead_id=lead.id,
                from_status=None,
                to_status=lead.status,
            )
        )


class SQLAlchemyServiceReader:
    def __init__(self, session: Session):
        self.session = session

    def find_active_id(self, slug: str) -> UUID | None:
        return self.session.scalar(
            select(Service.id).where(Service.slug == slug, Service.is_active)
        )


class SQLAlchemyOutboxWriter:
    def __init__(self, session: Session):
        self.session = session

    def enqueue(self, kind: str, payload: dict, max_attempts: int) -> None:
        self.session.add(OutboxTask(kind=kind, payload=payload, max_attempts=max_attempts))
