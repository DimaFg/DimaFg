from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Event

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import OperationalError

from app.adapter.database.base import SessionLocal
from app.adapter.database.models.leads import Lead, NotificationStatus
from app.adapter.database.models.outbox import OutboxStatus, OutboxTask
from app.adapter.database.notifications import SQLAlchemyDeliveryProgress
from app.adapter.notifications.senders import TemporaryError
from app.adapter.outbox.worker import process_one, purge_expired_ip_hashes
from app.core.config import get_settings


class FakeSender:
    def __init__(self, channel, fail_times=0):
        self.channel = channel
        self.fail_times = fail_times
        self.sent = []

    def send(self, lead):
        if self.fail_times > 0:
            self.fail_times -= 1
            raise TemporaryError(f"{self.channel} down")
        self.sent.append(lead.public_number)


def _make_ready(db):
    db.execute(update(OutboxTask).values(run_after=datetime.now(UTC) - timedelta(seconds=1)))
    db.commit()


def test_notification_sent(client, db, lead_payload):
    client.post("/api/v1/leads", json=lead_payload)
    sender = FakeSender("telegram")
    assert process_one(SessionLocal, [sender]) is True
    assert process_one(SessionLocal, [sender]) is False
    assert len(sender.sent) == 1
    db.expire_all()
    assert db.scalars(select(Lead)).one().notification_status == NotificationStatus.sent
    assert db.scalars(select(OutboxTask)).one().status == OutboxStatus.done


def test_outage_keeps_lead_and_retries(client, db, lead_payload):
    """Отказ Telegram не теряет заявку: задача повторяется, успешный канал не дублируется."""
    r = client.post("/api/v1/leads", json=lead_payload)
    assert r.status_code == 201
    tg = FakeSender("telegram", fail_times=2)
    email = FakeSender("email")

    process_one(SessionLocal, [tg, email])
    db.expire_all()
    task = db.scalars(select(OutboxTask)).one()
    assert task.status == OutboxStatus.pending and task.attempts == 1
    assert "telegram down" in task.last_error
    assert task.run_after > datetime.now(UTC)
    assert task.payload["done"] == ["email"]

    for _ in range(2):
        _make_ready(db)
        process_one(SessionLocal, [tg, email])
    db.expire_all()
    task = db.scalars(select(OutboxTask)).one()
    assert task.status == OutboxStatus.done and task.attempts == 3
    assert len(email.sent) == 1 and len(tg.sent) == 1
    assert db.scalars(select(Lead)).one().notification_status == NotificationStatus.sent


def test_task_fails_after_max_attempts(client, db, lead_payload):
    client.post("/api/v1/leads", json=lead_payload)
    db.execute(update(OutboxTask).values(max_attempts=2))
    db.commit()
    tg = FakeSender("telegram", fail_times=10)
    for _ in range(2):
        _make_ready(db)
        process_one(SessionLocal, [tg])
    db.expire_all()
    assert db.scalars(select(OutboxTask)).one().status == OutboxStatus.failed
    assert db.scalars(select(Lead)).one().notification_status == NotificationStatus.failed


def test_purge_ip_hashes(client, db, lead_payload):
    client.post("/api/v1/leads", json=lead_payload)
    db.execute(update(Lead).values(created_at=datetime.now(UTC) - timedelta(days=60)))
    db.commit()
    assert purge_expired_ip_hashes(SessionLocal) == 1
    db.expire_all()
    assert db.scalars(select(Lead)).one().ip_hash is None


def test_unexpected_sender_error_has_bounded_retries(client, db, lead_payload):
    client.post("/api/v1/leads", json=lead_payload)
    db.execute(update(OutboxTask).values(max_attempts=2))
    db.commit()

    class BrokenSender:
        channel = "telegram"

        def send(self, message):
            raise RuntimeError("private contact must not be stored")

    for _ in range(2):
        _make_ready(db)
        assert process_one(SessionLocal, [BrokenSender()])
    db.expire_all()
    task = db.scalars(select(OutboxTask)).one()
    assert task.status == OutboxStatus.failed and task.attempts == 2
    assert task.last_error == "RuntimeError"
    assert db.scalars(select(Lead)).one().notification_status == NotificationStatus.failed
    assert process_one(SessionLocal, [BrokenSender()]) is False


def test_invalid_payload_is_failed_permanently(db):
    db.add(OutboxTask(kind="lead.notify", payload={"lead_id": "invalid"}))
    db.commit()
    assert process_one(SessionLocal, [])
    db.expire_all()
    task = db.scalars(select(OutboxTask)).one()
    assert task.status == OutboxStatus.failed
    assert task.last_error == "invalid lead_id"


@pytest.mark.parametrize("next_ready", [False, True])
def test_expired_task_is_not_reclaimed_while_sender_is_running(
    client,
    db,
    lead_payload,
    monkeypatch,
    next_ready,
):
    client.post("/api/v1/leads", json=lead_payload)
    monkeypatch.setattr(get_settings(), "outbox_lock_timeout_seconds", -1)
    started, finish = Event(), Event()

    class BlockingSender:
        channel = "email"

        def send(self, message):
            started.set()
            assert finish.wait(timeout=10)

    second_sender = FakeSender("telegram")
    first_sender = FakeSender("telegram")
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(process_one, SessionLocal, [first_sender, BlockingSender()])
        try:
            assert started.wait(timeout=10)
            db.expire_all()
            assert db.scalars(select(OutboxTask)).one().payload["done"] == ["telegram"]
            if next_ready:
                assert (
                    client.post(
                        "/api/v1/leads",
                        json={**lead_payload, "message": "Другая заявка"},
                    ).status_code
                    == 201
                )
            assert process_one(SessionLocal, [second_sender]) is next_ready
        finally:
            finish.set()
        assert first.result(timeout=10)
    assert len(second_sender.sent) == int(next_ready)
    assert len(first_sender.sent) == 1
    db.expire_all()
    task = db.scalars(select(OutboxTask).order_by(OutboxTask.id)).first()
    assert task.status == OutboxStatus.done and task.attempts == 1


def _assert_no_worker_locks(db):
    assert (
        db.scalar(
            text(
                "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' "
                "AND classid = 1145654593 AND objsubid = 2"
            )
        )
        == 0
    )


def test_crash_after_first_channel_keeps_durable_progress(client, db, lead_payload):
    client.post("/api/v1/leads", json=lead_payload)
    telegram = FakeSender("telegram")

    class WorkerCrash(BaseException):
        pass

    class CrashingEmail:
        channel = "email"

        def send(self, message):
            raise WorkerCrash

    with pytest.raises(WorkerCrash):
        process_one(SessionLocal, [telegram, CrashingEmail()])
    db.expire_all()
    task = db.scalars(select(OutboxTask)).one()
    assert task.status == OutboxStatus.processing
    assert task.payload["done"] == ["telegram"]
    _assert_no_worker_locks(db)

    task.locked_at = datetime.now(UTC) - timedelta(hours=1)
    db.commit()
    email = FakeSender("email")
    assert process_one(SessionLocal, [telegram, email])
    assert len(telegram.sent) == len(email.sent) == 1
    db.expire_all()
    task = db.scalars(select(OutboxTask)).one()
    assert task.status == OutboxStatus.done
    assert task.payload["done"] == ["telegram", "email"]
    _assert_no_worker_locks(db)


def test_checkpoint_failure_stops_sending_and_releases_lock(
    client,
    db,
    lead_payload,
    monkeypatch,
):
    client.post("/api/v1/leads", json=lead_payload)

    def fail_checkpoint(self, channel):
        raise OperationalError("checkpoint", {}, RuntimeError("database unavailable"))

    monkeypatch.setattr(SQLAlchemyDeliveryProgress, "mark_done", fail_checkpoint)
    telegram, email = FakeSender("telegram"), FakeSender("email")
    with pytest.raises(OperationalError):
        process_one(SessionLocal, [telegram, email])
    assert len(telegram.sent) == 1
    assert email.sent == []
    db.expire_all()
    task = db.scalars(select(OutboxTask)).one()
    assert task.status == OutboxStatus.processing
    assert task.payload.get("done", []) == []
    _assert_no_worker_locks(db)


def test_crashed_task_cannot_send_after_attempt_budget_is_exhausted(client, db, lead_payload):
    client.post("/api/v1/leads", json=lead_payload)
    db.execute(
        update(OutboxTask).values(
            status=OutboxStatus.processing,
            attempts=2,
            max_attempts=2,
            locked_at=datetime.now(UTC) - timedelta(hours=1),
        )
    )
    db.commit()
    sender = FakeSender("telegram")
    assert process_one(SessionLocal, [sender])
    assert sender.sent == []
    db.expire_all()
    assert db.scalars(select(OutboxTask)).one().status == OutboxStatus.failed
