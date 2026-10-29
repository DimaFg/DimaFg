"""Импорт всех моделей, чтобы Alembic видел полную схему."""

from app.adapter.database.base import Base
from app.adapter.database.models.audit import AuditLog
from app.adapter.database.models.auth import Admin, AdminSession
from app.adapter.database.models.leads import Lead, LeadStatusHistory
from app.adapter.database.models.outbox import OutboxTask
from app.adapter.database.models.portfolio import Photo, PhotoCategory, PhotoVariant
from app.adapter.database.models.services import Service

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
