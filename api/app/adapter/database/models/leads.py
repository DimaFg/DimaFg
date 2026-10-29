import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Sequence,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapter.database.base import Base, TimestampMixin
from app.domain.leads.entities import ContactType, LeadStatus, NotificationStatus

lead_number_seq = Sequence("lead_public_number_seq", start=1, metadata=Base.metadata)


class Lead(TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_status_created_at", "status", "created_at"),
        Index("ix_leads_ip_hash_created_at", "ip_hash", "created_at"),
        Index("ix_leads_contact_normalized_created_at", "contact_normalized", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    public_number: Mapped[str] = mapped_column(String(20), unique=True)

    name: Mapped[str] = mapped_column(String(100))
    contact: Mapped[str] = mapped_column(String(200))
    contact_normalized: Mapped[str] = mapped_column(String(200))
    contact_type: Mapped[ContactType] = mapped_column(Enum(ContactType, name="lead_contact_type"))
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"), index=True
    )
    message: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status"), default=LeadStatus.new
    )
    internal_note: Mapped[str] = mapped_column(Text, default="")

    # Атрибуция
    source: Mapped[str | None] = mapped_column(String(500))  # referrer
    landing_page: Mapped[str | None] = mapped_column(String(500))
    utm_source: Mapped[str | None] = mapped_column(String(200))
    utm_medium: Mapped[str | None] = mapped_column(String(200))
    utm_campaign: Mapped[str | None] = mapped_column(String(200))
    utm_term: Mapped[str | None] = mapped_column(String(200))
    utm_content: Mapped[str | None] = mapped_column(String(200))

    consent_given_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    privacy_policy_version: Mapped[str] = mapped_column(String(40))

    notification_status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="lead_notification_status"),
        default=NotificationStatus.pending,
    )

    # Антиспам и защита от повторной отправки
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    # HMAC от IP. Обнуляется задачей очистки через IP_HASH_RETENTION_DAYS.
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    spam_reason: Mapped[str | None] = mapped_column(String(80))

    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    history: Mapped[list["LeadStatusHistory"]] = relationship(
        back_populates="lead", order_by="LeadStatusHistory.created_at", lazy="selectin"
    )


class LeadStatusHistory(Base):
    __tablename__ = "lead_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[LeadStatus | None] = mapped_column(
        Enum(LeadStatus, name="lead_status", create_type=False)
    )
    to_status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status", create_type=False)
    )
    admin_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped[Lead] = relationship(back_populates="history")
