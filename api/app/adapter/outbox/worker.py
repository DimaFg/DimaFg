"""Обработчик outbox-заданий. Запускается отдельным процессом: `python -m app.cli worker`.

FOR UPDATE SKIP LOCKED защищает захват, session advisory lock — обработку между commit.
"""

import logging
import signal
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from sqlalchemy import Connection, func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.adapter.database.models.leads import Lead, NotificationStatus
from app.adapter.database.models.outbox import OutboxStatus, OutboxTask
from app.adapter.database.notifications import SQLAlchemyDeliveryProgress
from app.adapter.notifications.senders import configured_senders
from app.core.config import get_settings
from app.core.heartbeat import heartbeat_path, write_heartbeat
from app.core.logging import log_event
from app.di.notifications import get_notify_lead
from app.domain.notifications import PermanentError, TemporaryError
from app.port.notifications import Sender

log = logging.getLogger("app.worker")
_OUTBOX_LOCK_NAMESPACE = 0x44494D41


def _now() -> datetime:
    return datetime.now(UTC)


def backoff(attempts: int) -> timedelta:
    s = get_settings()
    delay = s.outbox_retry_base_seconds * 2 ** max(0, attempts - 1)
    return timedelta(seconds=min(delay, s.outbox_retry_max_seconds))


@contextmanager
def claim_task(db: Session, connection: Connection) -> Iterator[OutboxTask | None]:
    """Connection закреплён за обработкой: session lock переживает промежуточные commit."""
    locked_id = None
    skipped = []
    try:
        now = _now()
        stale_lock = timedelta(seconds=get_settings().outbox_lock_timeout_seconds)
        while True:
            task = db.scalars(
                select(OutboxTask)
                .where(
                    or_(
                        (OutboxTask.status == OutboxStatus.pending) & (OutboxTask.run_after <= now),
                        (OutboxTask.status == OutboxStatus.processing)
                        & (OutboxTask.locked_at < now - stale_lock),
                    ),
                    OutboxTask.id.not_in(skipped),
                )
                .order_by(OutboxTask.run_after, OutboxTask.id)
                .limit(1)
                .with_for_update(skip_locked=True)
            ).first()
            if task is None:
                db.rollback()
                yield None
                return
            task_id = task.id
            if not db.scalar(select(func.pg_try_advisory_lock(_OUTBOX_LOCK_NAMESPACE, task_id))):
                # Не ждём занятую задачу и не мешаем обработке остальных.
                skipped.append(task_id)
                db.rollback()
                continue
            locked_id = task_id
            task.status = OutboxStatus.processing
            task.locked_at = now
            task.attempts += 1
            db.commit()
            yield task
            return
    finally:
        if locked_id is not None:
            try:
                db.rollback()
                connection.execute(
                    select(func.pg_advisory_unlock(_OUTBOX_LOCK_NAMESPACE, locked_id))
                )
                connection.commit()
            except BaseException:
                # Соединение с возможной session lock нельзя возвращать в pool.
                connection.invalidate()
                raise


def handle_lead_notify(db: Session, task: OutboxTask, senders: list[Sender]) -> None:
    done: list[str] = list(task.payload.get("done", []))
    try:
        lead_id = uuid.UUID(task.payload["lead_id"])
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise PermanentError("invalid lead_id") from exc
    progress = SQLAlchemyDeliveryProgress(db, task)
    get_notify_lead(db, senders, progress)(lead_id, done)


def _mark_lead_failed(db: Session, task: OutboxTask) -> None:
    if task.kind == "lead.notify" and (lead_id := task.payload.get("lead_id")):
        try:
            identifier = uuid.UUID(lead_id)
        except (TypeError, ValueError, AttributeError):
            return
        lead = db.get(Lead, identifier)
        if lead is not None:
            lead.notification_status = NotificationStatus.failed


Handler = Callable[[Session, OutboxTask, list[Sender]], None]
HANDLERS: dict[str, Handler] = {"lead.notify": handle_lead_notify}


def process_one(session_factory: sessionmaker, senders: list[Sender]) -> bool:
    """Обрабатывает одно задание; сохраняет session lock между commit каналов."""
    with (
        session_factory.kw["bind"].connect() as connection,
        session_factory(bind=connection) as db,
        claim_task(db, connection) as task,
    ):
        if task is None:
            return False
        return _process_task(db, task, senders)


def _process_task(db: Session, task: OutboxTask, senders: list[Sender]) -> bool:
    handler = HANDLERS.get(task.kind)
    try:
        if task.attempts > task.max_attempts:
            raise PermanentError("maximum attempts exceeded")
        if handler is None:
            raise PermanentError(f"unknown task kind {task.kind}")
        handler(db, task, senders)
    except PermanentError as exc:
        task.status = OutboxStatus.failed
        task.last_error = str(exc)[:2000]
        task.finished_at = _now()
        task.locked_at = None
        _mark_lead_failed(db, task)
        db.commit()
        log_event(log, "task failed permanently", logging.ERROR, task_id=task.id)
        return True
    except SQLAlchemyError:
        # После ошибки checkpoint не продолжаем отправку и не используем сломанную транзакцию.
        raise
    except Exception as exc:
        # Не сохраняем произвольный текст исключения: там могут быть персональные данные.
        task.last_error = str(exc)[:2000] if isinstance(exc, TemporaryError) else type(exc).__name__
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
