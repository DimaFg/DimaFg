from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.leads.entities import LeadReceipt, NewLead


class LeadRepository(Protocol):
    def lock_submission(self, contact: str, ip_hash: str | None, key: str | None) -> None: ...

    def find_by_key(self, key: str) -> LeadReceipt | None: ...

    def find_duplicate(
        self,
        contact: str,
        message: str,
        service_id: UUID | None,
        since: datetime,
        *,
        spam_reason: str | None,
    ) -> LeadReceipt | None: ...

    def count_by_ip(self, ip_hash: str, since: datetime) -> int: ...

    def count_by_contact(self, contact: str, since: datetime) -> int: ...

    def next_public_number(self, year: int) -> str: ...

    def add(self, lead: NewLead) -> None: ...


class ServiceReader(Protocol):
    def find_active_id(self, slug: str) -> UUID | None: ...


class OutboxWriter(Protocol):
    def enqueue(self, kind: str, payload: dict, max_attempts: int) -> None: ...
