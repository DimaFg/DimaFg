from sqlalchemy.orm import Session

from app.adapter.database.notifications import SQLAlchemyNotificationRepository
from app.application.notifications.notify_lead import NotifyLead
from app.core.config import get_settings
from app.port.notifications import DeliveryProgress, Sender


def get_notify_lead(
    session: Session,
    senders: list[Sender],
    progress: DeliveryProgress,
) -> NotifyLead:
    return NotifyLead(
        SQLAlchemyNotificationRepository(session, get_settings().admin_base_url),
        senders,
        progress,
    )
