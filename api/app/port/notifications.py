from typing import Protocol
from uuid import UUID

from app.domain.notifications import LeadMessage


class Sender(Protocol):
    channel: str

    def send(self, lead: LeadMessage) -> None: ...


class DeliveryProgress(Protocol):
    def mark_done(self, channel: str) -> None:
        """Надёжно сохранить успех канала до перехода к следующему."""
        ...


class NotificationRepository(Protocol):
    def get_message(self, lead_id: UUID) -> LeadMessage | None: ...

    def mark_sent(self, lead_id: UUID) -> None: ...
