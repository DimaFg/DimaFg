from uuid import UUID

from sqlalchemy.orm import Session

from app.adapter.database.models.leads import Lead
from app.adapter.database.models.outbox import OutboxTask
from app.adapter.database.models.services import Service
from app.domain.leads.entities import NotificationStatus
from app.domain.notifications import LeadMessage


class SQLAlchemyDeliveryProgress:
    def __init__(self, session: Session, task: OutboxTask):
        self.session = session
        self.task = task

    def mark_done(self, channel: str) -> None:
        done = list(self.task.payload.get("done", []))
        if channel not in done:
            done.append(channel)
        self.task.payload = {**self.task.payload, "done": done}
        self.session.commit()


class SQLAlchemyNotificationRepository:
    def __init__(self, session: Session, admin_base_url: str):
        self.session = session
        self.admin_base_url = admin_base_url.rstrip("/")

    def get_message(self, lead_id: UUID) -> LeadMessage | None:
        lead = self.session.get(Lead, lead_id)
        if lead is None:
            return None
        service = self.session.get(Service, lead.service_id) if lead.service_id else None
        return LeadMessage(
            public_number=lead.public_number,
            name=lead.name,
            contact=lead.contact,
            service=service.title if service else None,
            message=lead.message,
            admin_url=f"{self.admin_base_url}/leads/{lead.id}",
        )

    def mark_sent(self, lead_id: UUID) -> None:
        lead = self.session.get(Lead, lead_id)
        if lead is not None:
            lead.notification_status = NotificationStatus.sent
