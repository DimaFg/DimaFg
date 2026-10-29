from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class LeadStatus(StrEnum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    booked = "booked"
    completed = "completed"
    rejected = "rejected"
    spam = "spam"


class ContactType(StrEnum):
    telegram = "telegram"
    email = "email"
    phone = "phone"
    other = "other"


class NotificationStatus(StrEnum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    skipped = "skipped"


@dataclass(frozen=True, slots=True)
class Attribution:
    referrer: str | None = None
    landing_page: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None


@dataclass(frozen=True, slots=True)
class LeadReceipt:
    public_number: str


@dataclass(frozen=True, slots=True, kw_only=True)
class NewLead:
    id: UUID
    public_number: str
    name: str
    contact: str
    contact_normalized: str
    contact_type: ContactType
    service_id: UUID | None
    message: str
    consent_given_at: datetime
    privacy_policy_version: str
    idempotency_key: str | None
    ip_hash: str | None
    spam_reason: str | None
    attribution: Attribution

    @property
    def status(self) -> LeadStatus:
        return LeadStatus.spam if self.spam_reason else LeadStatus.new

    @property
    def notification_status(self) -> NotificationStatus:
        return NotificationStatus.skipped if self.spam_reason else NotificationStatus.pending
