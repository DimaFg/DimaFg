from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapter.clock import SystemClock
from app.adapter.database.base import get_db
from app.adapter.database.leads import (
    SQLAlchemyLeadRepository,
    SQLAlchemyOutboxWriter,
    SQLAlchemyServiceReader,
)
from app.adapter.database.unit_of_work import SQLAlchemyUnitOfWork
from app.application.leads.create import CreateLead, LeadPolicy
from app.core.config import get_settings


def get_create_lead(db: Session = Depends(get_db)) -> CreateLead:
    settings = get_settings()
    return CreateLead(
        leads=SQLAlchemyLeadRepository(db),
        services=SQLAlchemyServiceReader(db),
        outbox=SQLAlchemyOutboxWriter(db),
        uow=SQLAlchemyUnitOfWork(db),
        clock=SystemClock(),
        policy=LeadPolicy(
            min_fill_seconds=settings.lead_min_fill_seconds,
            rate_limit_per_ip_hour=settings.lead_rate_limit_per_ip_hour,
            rate_limit_per_contact_day=settings.lead_rate_limit_per_contact_day,
            dedup_window_minutes=settings.lead_dedup_window_minutes,
            privacy_policy_version=settings.privacy_policy_version,
            outbox_max_attempts=settings.outbox_max_attempts,
        ),
    )
