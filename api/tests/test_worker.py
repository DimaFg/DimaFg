from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.core.db import SessionLocal
from app.modules.leads.models import Lead, NotificationStatus
from app.modules.notifications.models import OutboxStatus, OutboxTask
from app.modules.notifications.senders import TemporaryError
from app.modules.notifications.worker import process_one, purge_expired_ip_hashes


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
