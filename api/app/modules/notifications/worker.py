"""Обработчик outbox-заданий. Запускается отдельным процессом: `python -m app.cli worker`.

Несколько экземпляров worker'а безопасны: задания захватываются через FOR UPDATE SKIP LOCKED.
"""

import logging
import signal
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.heartbeat import heartbeat_path, write_heartbeat
from app.core.logging import log_event
from app.modules.leads.models import Lead, NotificationStatus
from app.modules.notifications.models import OutboxStatus, OutboxTask
from app.modules.notifications.senders import (
    LeadMessage,
    Sender,
    TemporaryError,
    configured_senders,
)
from app.modules.services.models import Service

log = logging.getLogger("app.worker")


class PermanentError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def backoff(attempts: int) -> timedelta:
    s = get_settings()
    delay = s.outbox_retry_base_seconds * 2 ** max(0, attempts - 1)
    return timedelta(seconds=min(delay, s.outbox_retry_max_seconds))


def claim_task(db: Session) -> OutboxTask | None:
    now = _now()
    stale_lock = timedelta(seconds=get_settings().outbox_lock_timeout_seconds)
    candidate = (
        select(OutboxTask.id)
        .where(
            or_(
                (OutboxTask.status == OutboxStatus.pending) & (OutboxTask.run_after <= now),
                (OutboxTask.status == OutboxStatus.processing)
                & (OutboxTask.locked_at < now - stale_lock),
            )
        )
        .order_by(OutboxTask.run_after, OutboxTask.id)
        .limit(1)
        .with_for_update(skip_locked=True)
        .scalar_subquery()
    )
    task = db.scalars(
        update(OutboxTask)
        .where(OutboxTask.id == candidate)
        .values(
            status=OutboxStatus.processing,
            locked_at=now,
            attempts=OutboxTask.attempts + 1,
        )
        .returning(OutboxTask)
    ).first()
    db.commit()
    return task


def handle_lead_notify(db: Session, task: OutboxTask, senders: list[Sender]) -> None:
    lead = db.get(Lead, uuid.UUID(task.payload["lead_id"]))
    if lead is None:
        raise PermanentError("lead not found")
    service = db.get(Service, lead.service_id) if lead.service_id else None
    message = LeadMessage(
        public_number=lead.public_number,
        name=lead.name,
        contact=lead.contact,
        service=service.title if service else None,
        message=lead.message,
        admin_url=f"{get_settings().admin_base_url.rstrip('/')}/leads/{lead.id}",
    )
    done: list[str] = list(task.payload.get("done", []))
    errors: list[str] = []
    for sender in senders:
        if sender.channel in done:
            continue
        try:
            sender.send(message)
            done.append(sender.channel)
        except TemporaryError as exc:
            errors.append(f"{sender.channel}: {exc}")
    # Запоминаем успешные каналы, чтобы при повторе не дублировать сообщения.
    task.payload = {**task.payload, "done": done}
    if errors:
        raise TemporaryError("; ".join(errors))
    lead.notification_status = NotificationStatus.sent


def _mark_lead_failed(db: Session, task: OutboxTask) -> None:
    if task.kind == "lead.notify" and (lead_id := task.payload.get("lead_id")):
        lead = db.get(Lead, uuid.UUID(lead_id))
        if lead is not None:
            lead.notification_status = NotificationStatus.failed


Handler = Callable[[Session, OutboxTask, list[Sender]], None]
HANDLERS: dict[str, Handler] = {"lead.notify": handle_lead_notify}


def process_one(session_factory: sessionmaker, senders: list[Sender]) -> bool:
    """Обрабатывает одно задание. Возвращает False, если очередь пуста."""
    with session_factory() as db:
        task = claim_task(db)
        if task is None:
            return False
        handler = HANDLERS.get(task.kind)
        try:
            if handler is None:
                raise PermanentError(f"unknown task kind {task.kind}")
            handler(db, task, senders)
        except TemporaryError as exc:
            task.last_error = str(exc)[:2000]
            if task.attempts >= task.max_attempts:
                task.status = OutboxStatus.failed
                task.finished_at = _now()
                _mark_lead_failed(db, task)
            else:
                task.status = OutboxStatus.pending
                task.run_after = _now() + backoff(task.attempts)
            task.locked_at = None
            db.commit()
            log_event(
                log,
                "task failed",
                logging.WARNING,
                task_id=task.id,
                kind=task.kind,
                attempts=task.attempts,
                status=task.status.value,
            )
            return True
        except PermanentError as exc:
            task.status = OutboxStatus.failed
            task.last_error = str(exc)[:2000]
            task.finished_at = _now()
            task.locked_at = None
            _mark_lead_failed(db, task)
            db.commit()
            log_event(log, "task failed permanently", logging.ERROR, task_id=task.id)
            return True

        task.status = OutboxStatus.done
        task.finished_at = _now()
        task.locked_at = None
        task.last_error = None
        db.commit()
        log_event(log, "task done", task_id=task.id, kind=task.kind, attempts=task.attempts)
        return True


def purge_expired_ip_hashes(session_factory: sessionmaker) -> int:
    cutoff = _now() - timedelta(days=get_settings().ip_hash_retention_days)
    with session_factory() as db:
        result = db.execute(
            update(Lead)
            .where(Lead.ip_hash.is_not(None), Lead.created_at < cutoff)
            .values(ip_hash=None)
        )
        db.commit()
        return result.rowcount or 0


def run_forever(session_factory: sessionmaker) -> None:
    settings = get_settings()
    senders = configured_senders(settings)
    stopping = False

    def _stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    log_event(log, "worker started", channels=[s.channel for s in senders])

    heartbeat = heartbeat_path(settings.heartbeat_dir, "worker")
    last_housekeeping = 0.0
    while not stopping:
        try:
            write_heartbeat(heartbeat)
            if time.monotonic() - last_housekeeping > 3600:
                purged = purge_expired_ip_hashes(session_factory)
                log_event(log, "housekeeping", purged_ip_hashes=purged)
                last_housekeeping = time.monotonic()
            if not process_one(session_factory, senders):
                time.sleep(settings.worker_poll_seconds)
        except Exception:
            log.exception("worker loop error")
            time.sleep(5)
    log_event(log, "worker stopped")
