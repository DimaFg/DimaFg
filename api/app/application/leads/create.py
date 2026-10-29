import logging
from dataclasses import dataclass, field
from datetime import timedelta
from uuid import uuid4

from app.core.logging import log_event
from app.domain.leads.contact import classify_contact
from app.domain.leads.entities import Attribution, LeadReceipt, NewLead
from app.port.clock import Clock
from app.port.leads import LeadRepository, OutboxWriter, ServiceReader
from app.port.unit_of_work import UnitOfWork

log = logging.getLogger("app.leads")
NOTIFY_TASK = "lead.notify"


class UnknownServiceError(Exception):
    pass


class RateLimitError(Exception):
    def __init__(self, *, per_contact: bool):
        self.per_contact = per_contact


@dataclass(frozen=True, slots=True)
class LeadPolicy:
    min_fill_seconds: float
    rate_limit_per_ip_hour: int
    rate_limit_per_contact_day: int
    dedup_window_minutes: int
    privacy_policy_version: str
    outbox_max_attempts: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateLeadCommand:
    name: str
    contact: str
    message: str = ""
    service: str | None = None
    privacy_policy_version: str | None = None
    website: str = ""
    elapsed_ms: int | None = None
    attribution: Attribution = field(default_factory=Attribution)
    ip_hash: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class LeadResult:
    lead: LeadReceipt
    created: bool


class CreateLead:
    def __init__(
        self,
        *,
        leads: LeadRepository,
        services: ServiceReader,
        outbox: OutboxWriter,
        uow: UnitOfWork,
        clock: Clock,
        policy: LeadPolicy,
    ):
        self.leads = leads
        self.services = services
        self.outbox = outbox
        self.uow = uow
        self.clock = clock
        self.policy = policy

    def __call__(self, command: CreateLeadCommand) -> LeadResult:
        try:
            return self._execute(command)
        except Exception:
            self.uow.rollback()
            raise

    def _execute(self, command: CreateLeadCommand) -> LeadResult:
        contact_type, normalized = classify_contact(command.contact)
        # Сериализация повторов и подсчёта лимитов между процессами API.
        self.leads.lock_submission(normalized, command.ip_hash, command.idempotency_key)
        if command.idempotency_key:
            existing = self.leads.find_by_key(command.idempotency_key)
            if existing:
                self.uow.commit()
                return LeadResult(existing, created=False)

        service_id = None
        if command.service not in (None, "other"):
            service_id = self.services.find_active_id(command.service)
            if service_id is None:
                raise UnknownServiceError

        now = self.clock.now()
        spam_reason = None
        if command.website:
            spam_reason = "honeypot"
        elif (
            command.elapsed_ms is not None
            and command.elapsed_ms < self.policy.min_fill_seconds * 1000
        ):
            spam_reason = "too_fast"
        duplicate = self.leads.find_duplicate(
            normalized,
            command.message,
            service_id,
            now - timedelta(minutes=self.policy.dedup_window_minutes),
            spam_reason=spam_reason,
        )
        if duplicate:
            self.uow.commit()
            return LeadResult(duplicate, created=False)

        if (
            command.ip_hash
            and self.leads.count_by_ip(command.ip_hash, now - timedelta(hours=1))
            >= self.policy.rate_limit_per_ip_hour
        ):
            raise RateLimitError(per_contact=False)
        if (
            self.leads.count_by_contact(normalized, now - timedelta(days=1))
            >= self.policy.rate_limit_per_contact_day
        ):
            raise RateLimitError(per_contact=True)

        lead = NewLead(
            id=uuid4(),
            public_number=self.leads.next_public_number(now.year),
            name=command.name,
            contact=command.contact,
            contact_normalized=normalized,
            contact_type=contact_type,
            service_id=service_id,
            message=command.message,
            consent_given_at=now,
            privacy_policy_version=command.privacy_policy_version
            or self.policy.privacy_policy_version,
            idempotency_key=command.idempotency_key,
            ip_hash=command.ip_hash,
            spam_reason=spam_reason,
            attribution=command.attribution,
        )
        self.leads.add(lead)
        if not spam_reason:
            self.outbox.enqueue(
                NOTIFY_TASK, {"lead_id": str(lead.id)}, self.policy.outbox_max_attempts
            )
        self.uow.commit()
        log_event(
            log,
            "lead created",
            lead_id=str(lead.id),
            public_number=lead.public_number,
            contact_type=contact_type.value,
            spam_reason=spam_reason,
        )
        return LeadResult(LeadReceipt(lead.public_number), created=True)
