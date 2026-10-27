"""Импорт всех моделей, чтобы Alembic видел полную схему."""

from app.core.db import Base
from app.modules.audit.models import AuditLog
from app.modules.auth.models import Admin, AdminSession
from app.modules.leads.models import Lead, LeadStatusHistory
from app.modules.notifications.models import OutboxTask
from app.modules.portfolio.models import Photo, PhotoCategory, PhotoVariant
from app.modules.services.models import Service

__all__ = [
    "Admin",
    "AdminSession",
    "AuditLog",
    "Base",
    "Lead",
    "LeadStatusHistory",
    "OutboxTask",
    "Photo",
    "PhotoCategory",
    "PhotoVariant",
    "Service",
]
