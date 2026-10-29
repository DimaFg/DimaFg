import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import select

from app.adapter.database.models.leads import ContactType, Lead, LeadStatus, NotificationStatus
from app.adapter.database.models.outbox import OutboxTask
from app.domain.leads.contact import classify_contact


def test_create_lead_persists_with_outbox(client, db, lead_payload):
    r = client.post("/api/v1/leads", json=lead_payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["public_number"].endswith("-00001")
    assert body["expected_response"]

    lead = db.scalars(select(Lead)).one()
    assert lead.status == LeadStatus.new
    assert lead.contact_type == ContactType.telegram
    assert lead.contact_normalized == "@anna_photo"
    assert lead.utm_source == "telegram"
    assert lead.privacy_policy_version
    assert lead.consent_given_at is not None
    assert lead.ip_hash and len(lead.ip_hash) == 64
    assert [h.to_status for h in lead.history] == [LeadStatus.new]
    task = db.scalars(select(OutboxTask)).one()
    assert task.kind == "lead.notify" and task.payload["lead_id"] == str(lead.id)


def test_internal_fields_not_returned(client, lead_payload):
    body = client.post("/api/v1/leads", json=lead_payload).json()
    assert set(body) == {"public_number", "expected_response"}


def test_validation_errors_have_uniform_format(client, lead_payload):
    bad = {**lead_payload, "name": "", "consent": False, "unexpected": 1}
    r = client.post("/api/v1/leads", json=bad)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    assert set(err["fields"]) >= {"name", "consent", "unexpected"}
    assert err["request_id"]


def test_unknown_service_rejected(client, lead_payload):
    r = client.post("/api/v1/leads", json={**lead_payload, "service": "skydiving"})
    assert r.status_code == 422
    assert "service" in r.json()["error"]["fields"]


def test_other_service_allowed(client, db, lead_payload):
    r = client.post("/api/v1/leads", json={**lead_payload, "service": "other"})
    assert r.status_code == 201
    assert db.scalars(select(Lead)).one().service_id is None


def test_idempotency_key_prevents_duplicates(client, db, lead_payload):
    key = str(uuid.uuid4())
    r1 = client.post("/api/v1/leads", json=lead_payload, headers={"Idempotency-Key": key})
    r2 = client.post(
        "/api/v1/leads",
        json={**lead_payload, "message": "другой текст"},
        headers={"Idempotency-Key": key},
    )
    assert r1.status_code == 201 and r2.status_code == 200
    assert r1.json()["public_number"] == r2.json()["public_number"]
    assert len(db.scalars(select(Lead)).all()) == 1


def test_server_side_dedup_without_key(client, db, lead_payload):
    r1 = client.post("/api/v1/leads", json=lead_payload)
    r2 = client.post("/api/v1/leads", json=lead_payload)
    assert r2.status_code == 200
    assert r1.json()["public_number"] == r2.json()["public_number"]
    assert len(db.scalars(select(Lead)).all()) == 1


def test_honeypot_marks_spam_without_notification(client, db, lead_payload):
    r = client.post("/api/v1/leads", json={**lead_payload, "website": "http://spam"})
    assert r.status_code == 201  # бот не должен понять, что его распознали
    lead = db.scalars(select(Lead)).one()
    assert lead.status == LeadStatus.spam and lead.spam_reason == "honeypot"
    assert lead.notification_status == NotificationStatus.skipped
    assert db.scalars(select(OutboxTask)).all() == []


def test_too_fast_submission_is_spam(client, db, lead_payload):
    client.post("/api/v1/leads", json={**lead_payload, "elapsed_ms": 500})
    assert db.scalars(select(Lead)).one().spam_reason == "too_fast"


def test_rate_limit_per_ip(client, lead_payload):
    statuses = []
    for i in range(7):
        payload = {**lead_payload, "contact": f"user{i}@example.com"}
        statuses.append(client.post("/api/v1/leads", json=payload).status_code)
    assert statuses[:5] == [201] * 5
    assert statuses[5] == 429


def test_rate_limit_per_contact(client, lead_payload):
    codes = [
        client.post("/api/v1/leads", json={**lead_payload, "message": f"m{i}"}).status_code
        for i in range(4)
    ]
    assert codes == [201, 201, 201, 429]


def test_body_size_limit(client, lead_payload):
    r = client.post("/api/v1/leads", json={**lead_payload, "message": "x" * 70_000})
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "payload_too_large"


def test_classify_contact():
    assert classify_contact("Test@Mail.RU") == (ContactType.email, "test@mail.ru")
    assert classify_contact("@Dmitry_Photo") == (ContactType.telegram, "@dmitry_photo")
    assert classify_contact("https://t.me/dmitry_photo")[0] == ContactType.telegram
    assert classify_contact("8 (916) 123-45-67") == (ContactType.phone, "+79161234567")
    assert classify_contact("ВКонтакте: id1")[0] == ContactType.other


def test_same_message_for_different_services_creates_two_leads(client, db, lead_payload):
    assert client.post("/api/v1/leads", json=lead_payload).status_code == 201
    response = client.post("/api/v1/leads", json={**lead_payload, "service": "other"})
    assert response.status_code == 201
    assert len(db.scalars(select(Lead)).all()) == 2


def test_unknown_service_is_rejected_even_if_message_matches(client, lead_payload):
    client.post("/api/v1/leads", json=lead_payload)
    response = client.post("/api/v1/leads", json={**lead_payload, "service": "unknown"})
    assert response.status_code == 422


def test_duplicate_without_key_is_returned_after_contact_limit(client, lead_payload):
    for i in range(3):
        response = client.post("/api/v1/leads", json={**lead_payload, "message": f"m{i}"})
        assert response.status_code == 201
    response = client.post("/api/v1/leads", json={**lead_payload, "message": "m0"})
    assert response.status_code == 200


def test_duplicate_without_key_is_returned_after_ip_limit(client, lead_payload):
    for i in range(5):
        response = client.post("/api/v1/leads", json={**lead_payload, "contact": f"u{i}@mail.ru"})
        assert response.status_code == 201
    response = client.post("/api/v1/leads", json={**lead_payload, "contact": "u0@mail.ru"})
    assert response.status_code == 200


@pytest.mark.parametrize("with_key", [False, True])
def test_parallel_submissions_are_deduplicated(client, db, lead_payload, with_key):
    barrier = Barrier(4)
    key = str(uuid.uuid4())
    payload = {**lead_payload, "message": str(uuid.uuid4())}

    def submit(_):
        barrier.wait(timeout=10)
        return client.post(
            "/api/v1/leads",
            json=payload,
            headers={"Idempotency-Key": key} if with_key else {},
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(submit, range(4)))
    assert sorted(r.status_code for r in responses) == [200, 200, 200, 201]
    assert len({r.json()["public_number"] for r in responses}) == 1
    assert len(db.scalars(select(Lead)).all()) == 1
    assert len(db.scalars(select(OutboxTask)).all()) == 1


def test_parallel_rate_limit_is_not_exceeded(client, db, lead_payload):
    barrier = Barrier(6)

    def submit(i):
        barrier.wait(timeout=10)
        return client.post(
            "/api/v1/leads",
            json={**lead_payload, "contact": f"parallel{i}@example.com"},
        )

    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(submit, range(6)))
    assert sorted(r.status_code for r in responses) == [201] * 5 + [429]
    assert len(db.scalars(select(Lead)).all()) == 5


def test_legitimate_submission_is_not_deduplicated_against_spam(client, db, lead_payload):
    first = client.post("/api/v1/leads", json={**lead_payload, "elapsed_ms": 1})
    second = client.post("/api/v1/leads", json=lead_payload)
    assert first.status_code == second.status_code == 201
    assert first.json()["public_number"] != second.json()["public_number"]
    assert {lead.status for lead in db.scalars(select(Lead))} == {LeadStatus.spam, LeadStatus.new}
    assert len(db.scalars(select(OutboxTask)).all()) == 1


def test_outbox_failure_rolls_back_lead_and_history(db, monkeypatch):
    from app.adapter.database.leads import SQLAlchemyOutboxWriter
    from app.adapter.database.models.leads import LeadStatusHistory
    from app.application.leads.create import CreateLeadCommand
    from app.di.leads import get_create_lead

    def fail(*args):
        raise RuntimeError("outbox unavailable")

    monkeypatch.setattr(SQLAlchemyOutboxWriter, "enqueue", fail)
    with pytest.raises(RuntimeError, match="outbox unavailable"):
        get_create_lead(db)(CreateLeadCommand(name="Анна", contact="@anna_photo"))
    assert db.scalars(select(Lead)).all() == []
    assert db.scalars(select(LeadStatusHistory)).all() == []


def test_same_key_is_serialized_even_for_different_contacts_and_ips(db):
    from app.adapter.database.base import SessionLocal
    from app.application.leads.create import CreateLeadCommand
    from app.di.leads import get_create_lead

    barrier = Barrier(4)
    key = str(uuid.uuid4())

    def submit(i):
        with SessionLocal() as session:
            handler = get_create_lead(session)
            barrier.wait(timeout=10)
            return handler(
                CreateLeadCommand(
                    name="Анна",
                    contact=f"parallel{i}@example.com",
                    ip_hash=f"ip-{i}",
                    idempotency_key=key,
                )
            )

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(submit, range(4)))
    assert sum(result.created for result in results) == 1
    assert len({result.lead.public_number for result in results}) == 1
    assert len(db.scalars(select(Lead)).all()) == 1
    assert len(db.scalars(select(OutboxTask)).all()) == 1
