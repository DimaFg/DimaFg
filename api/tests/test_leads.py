import uuid

from sqlalchemy import select

from app.modules.leads.contact import classify_contact
from app.modules.leads.models import ContactType, Lead, LeadStatus, NotificationStatus
from app.modules.notifications.models import OutboxTask


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
