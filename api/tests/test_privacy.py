import json
import logging
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.heartbeat import StaleHeartbeatError, ensure_fresh_heartbeat, write_heartbeat
from app.core.logging import JsonFormatter, log_event
from app.modules.leads.models import ContactType, Lead


def test_db_errors_do_not_contain_lead_data(client, db, lead_payload):
    """Регрессия: без hide_parameters имя и контакт попадали в traceback и логи."""
    number = client.post("/api/v1/leads", json=lead_payload).json()["public_number"]
    db.add(
        Lead(
            public_number=number,
            name="Секретное Имя",
            contact="secret@example.com",
            contact_normalized="secret@example.com",
            contact_type=ContactType.email,
            message="личный текст",
            consent_given_at=datetime.now(UTC),
            privacy_policy_version="x",
        )
    )
    with pytest.raises(IntegrityError) as exc:
        db.commit()
    db.rollback()
    text = str(exc.value)
    assert "secret@example.com" not in text and "Секретное Имя" not in text


def test_log_fields_are_redacted():
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "lead", None, None)
    record.extra_fields = {
        "contact": "@anna",
        "name": "Анна",
        "bot_token": "123:abc",
        "nested": {"message": "текст", "lead_id": "42"},
        "public_number": "2026-00001",
    }
    out = json.loads(JsonFormatter().format(record))
    assert out["contact"] == out["name"] == out["bot_token"] == "[redacted]"
    assert out["nested"] == {"message": "[redacted]", "lead_id": "42"}
    assert out["public_number"] == "2026-00001"


def test_log_event_helper_uses_redaction(caplog):
    logger = logging.getLogger("test.redaction")
    with caplog.at_level(logging.INFO, logger="test.redaction"):
        log_event(logger, "x", contact="@anna")
    formatted = JsonFormatter().format(caplog.records[-1])
    assert "@anna" not in formatted


def test_heartbeat(tmp_path):
    path = tmp_path / "worker.heartbeat"
    with pytest.raises(StaleHeartbeatError):
        ensure_fresh_heartbeat(path, 60)
    write_heartbeat(path)
    assert ensure_fresh_heartbeat(path, 60) < 5
    path.write_text("0\n")
    with pytest.raises(StaleHeartbeatError):
        ensure_fresh_heartbeat(path, 60)
